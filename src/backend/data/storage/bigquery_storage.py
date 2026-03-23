"""BigQuery storage implementation for votes."""

import logging
import os
from datetime import datetime

import pandas as pd
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery

from backend.utils.circuit_breaker import QuotaExceededError, get_circuit_breaker
from backend.utils.quota_manager import get_quota_manager
from backend.utils.rate_limiter import RateLimitExceededError, rate_limit
from backend.utils.retry import retry_with_backoff
from backend.utils.usage_estimator import UsageEstimator
from backend.utils.validators import validate_single_vote, validate_vote_data
from config import CONFIG, RATE_LIMITS

logger = logging.getLogger(__name__)


class BigQueryVoteStorage:
    """BigQuery storage for votes."""

    def __init__(
        self,
        project_id: str | None = None,
        dataset_id: str | None = None,
        table_id: str | None = None,
    ):
        """Initialize BigQuery vote storage.

        Args:
            project_id: GCP project ID. If None, uses GCP_PROJECT_ID env var.
            dataset_id: BigQuery dataset ID. If None, uses BIGQUERY_DATASET env var.
            table_id: BigQuery table ID. If None, uses BIGQUERY_TABLE env var.
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.dataset_id = dataset_id or os.getenv("BIGQUERY_DATASET", "copo_do_mundo")
        self.table_id = table_id or os.getenv("BIGQUERY_TABLE", "votes")

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be set")

        try:
            self.client = bigquery.Client(project=self.project_id)
            self.table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            self._ensure_table_exists()
        except DefaultCredentialsError as e:
            logger.error(f"GCP credentials not found: {str(e)}")
            raise ValueError(
                "GCP credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS "
                "or use Workload Identity Federation."
            ) from e

    def _ensure_table_exists(self) -> None:
        """Ensure the BigQuery table exists with correct schema."""
        try:
            dataset_ref = self.client.dataset(self.dataset_id)
            # Create dataset if it doesn't exist
            try:
                self.client.get_dataset(dataset_ref)
            except Exception:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"  # Default location
                self.client.create_dataset(dataset, exists_ok=True)
                logger.info(f"Created dataset {self.dataset_id}")

            # Create table if it doesn't exist
            table_ref = dataset_ref.table(self.table_id)
            try:
                self.client.get_table(table_ref)
                logger.info(f"Table {self.table_id} already exists")
            except Exception:
                schema = [
                    bigquery.SchemaField("Nome", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("Participante", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("Categoria", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("Originalidade", "INTEGER", mode="REQUIRED"),
                    bigquery.SchemaField("Aparencia", "INTEGER", mode="REQUIRED"),
                    bigquery.SchemaField("Sabor", "INTEGER", mode="REQUIRED"),
                    bigquery.SchemaField("Data", "TIMESTAMP", mode="REQUIRED"),
                ]
                table = bigquery.Table(table_ref, schema=schema)
                self.client.create_table(table)
                logger.info(f"Created table {self.table_id} with schema")
        except Exception as e:
            logger.error(f"Error ensuring table exists: {str(e)}")
            raise

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    @rate_limit(
        service="bigquery",
        operation_type="query",
        max_ops=RATE_LIMITS["bigquery"]["query"]["max_ops"],
        window_seconds=RATE_LIMITS["bigquery"]["query"]["window"],
    )
    def load_data(self) -> pd.DataFrame:
        """Load voting data from BigQuery.

        Returns:
            pd.DataFrame: The loaded voting data.
        """
        if not CONFIG.get("QUOTA_PROTECTION_ENABLED", True):
            return self._load_data_internal()

        try:
            # Estimate usage
            estimated_bytes = UsageEstimator.estimate_bigquery_query(
                f"SELECT * FROM `{self.table_ref}`"
            )
            limit = UsageEstimator.get_quota_limit("bigquery", "query")

            # Check quota and circuit breaker
            quota_manager = get_quota_manager()
            circuit_breaker = get_circuit_breaker("bigquery")

            can_proceed, status, reason = circuit_breaker.can_proceed(
                "query", estimated_bytes, limit
            )

            if not can_proceed:
                raise QuotaExceededError(reason)

            # Execute operation
            df = self._load_data_internal()

            # Track actual usage (estimate bytes scanned from result)
            actual_bytes = len(df) * 200 if not df.empty else estimated_bytes
            quota_manager.track_operation("bigquery", "query", actual_bytes, "bytes")

            if status.value == "warning":
                logger.warning(f"Quota warning for BigQuery query: {reason}")

            return df

        except (QuotaExceededError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error loading data from BigQuery: {str(e)}")
            raise

    def _load_data_internal(self) -> pd.DataFrame:
        """Internal method to load data without quota checks."""
        query = f"SELECT * FROM `{self.table_ref}` ORDER BY Data DESC"
        df = self.client.query(query).to_dataframe()
        # Ensure Data column is datetime
        if "Data" in df.columns and len(df) > 0:
            df["Data"] = pd.to_datetime(df["Data"])
        logger.info(f"Successfully loaded {len(df)} votes from BigQuery")
        return df

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def load_data_since(self, since_timestamp: datetime) -> pd.DataFrame:
        """Load voting data from BigQuery since a specific timestamp.

        This is more efficient than loading all data when you only need recent votes.

        Args:
            since_timestamp: Only load votes after this timestamp.

        Returns:
            pd.DataFrame: The loaded voting data.
        """
        try:
            # Format timestamp for BigQuery
            timestamp_str = since_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            query = (
                f"SELECT * FROM `{self.table_ref}` "
                f"WHERE Data > TIMESTAMP('{timestamp_str}') "
                f"ORDER BY Data DESC"
            )
            df = self.client.query(query).to_dataframe()
            # Ensure Data column is datetime
            if "Data" in df.columns and len(df) > 0:
                df["Data"] = pd.to_datetime(df["Data"])
            logger.info(
                f"Successfully loaded {len(df)} votes from BigQuery since {since_timestamp}"
            )
            return df
        except Exception as e:
            logger.error(f"Error loading incremental data from BigQuery: {str(e)}")
            raise

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def save_data(self, data: pd.DataFrame) -> bool:
        """Save voting data to BigQuery.

        This method replaces all data in the table. For append operations,
        use append_data instead. This is typically used for admin operations
        like clearing all votes.

        Args:
            data: The voting data to save.

        Returns:
            bool: True if save was successful.
        """
        try:
            # Validate data before saving
            validate_vote_data(data)

            if data.empty:
                # Clear table by deleting all rows
                query = f"DELETE FROM `{self.table_ref}` WHERE TRUE"
                self.client.query(query).result()
                logger.info("Cleared all votes from BigQuery table")
                return True

            # Prepare data for BigQuery
            # Convert datetime to string format BigQuery expects
            data_to_upload = data.copy()
            if "Data" in data_to_upload.columns:
                data_to_upload["Data"] = pd.to_datetime(data_to_upload["Data"])

            # Delete existing data and insert new data
            # This is a full replacement operation (admin use case)
            delete_query = f"DELETE FROM `{self.table_ref}` WHERE TRUE"
            self.client.query(delete_query).result()

            # Insert new data
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                source_format=bigquery.SourceFormat.CSV,
            )

            # Convert DataFrame to CSV string
            csv_string = data_to_upload.to_csv(index=False)
            job = self.client.load_table_from_string(
                csv_string, self.table_ref, job_config=job_config
            )
            job.result()  # Wait for job to complete

            logger.info(f"Successfully saved {len(data)} votes to BigQuery")
            return True
        except Exception as e:
            logger.error(f"Error saving data to BigQuery: {str(e)}")
            raise

    @retry_with_backoff(max_retries=3, initial_delay=0.5)
    @rate_limit(
        service="bigquery",
        operation_type="insert",
        max_ops=RATE_LIMITS["bigquery"]["insert"]["max_ops"],
        window_seconds=RATE_LIMITS["bigquery"]["insert"]["window"],
    )
    def insert_vote(
        self,
        name: str,
        participant: str,
        categoria: str,
        originalidade: int,
        aparencia: int,
        sabor: int,
        data_timestamp: datetime | None = None,
    ) -> bool:
        """Insert a single vote using BigQuery streaming insert.

        This is the most efficient method for inserting individual votes.
        Uses streaming insert API for low latency.

        Args:
            name: Name of the juror.
            participant: Participant ID.
            categoria: Category of the vote.
            originalidade: Originality score (0-10).
            aparencia: Appearance score (0-10).
            sabor: Taste score (0-10).
            data_timestamp: Timestamp for the vote. If None, uses current time.

        Returns:
            bool: True if insert was successful.
        """
        if not CONFIG.get("QUOTA_PROTECTION_ENABLED", True):
            return self._insert_vote_internal(
                name, participant, categoria, originalidade, aparencia, sabor, data_timestamp
            )

        try:
            # Validate vote data before insertion
            validate_single_vote(
                name=name,
                participant=participant,
                categoria=categoria,
                originalidade=originalidade,
                aparencia=aparencia,
                sabor=sabor,
            )

            # Estimate usage
            estimated_bytes = UsageEstimator.estimate_bigquery_insert(1)
            limit = UsageEstimator.get_quota_limit("bigquery", "streaming")

            # Check quota and circuit breaker
            quota_manager = get_quota_manager()
            circuit_breaker = get_circuit_breaker("bigquery")

            can_proceed, status, reason = circuit_breaker.can_proceed(
                "streaming", estimated_bytes, limit
            )

            if not can_proceed:
                raise QuotaExceededError(reason)

            # Execute operation
            result = self._insert_vote_internal(
                name, participant, categoria, originalidade, aparencia, sabor, data_timestamp
            )

            # Track actual usage
            quota_manager.track_operation("bigquery", "streaming", estimated_bytes, "bytes")

            if status.value == "warning":
                logger.warning(f"Quota warning for BigQuery insert: {reason}")

            return result

        except (QuotaExceededError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error inserting vote to BigQuery: {str(e)}")
            raise

    def _insert_vote_internal(
        self,
        name: str,
        participant: str,
        categoria: str,
        originalidade: int,
        aparencia: int,
        sabor: int,
        data_timestamp: datetime | None = None,
    ) -> bool:
        """Internal method to insert vote without quota checks."""
        if data_timestamp is None:
            data_timestamp = datetime.now()

        # Prepare row data matching BigQuery schema
        row = {
            "Nome": name,
            "Participante": str(participant),
            "Categoria": categoria,
            "Originalidade": int(originalidade),
            "Aparencia": int(aparencia),
            "Sabor": int(sabor),
            "Data": data_timestamp,
        }

        # Use streaming insert API for single row
        errors = self.client.insert_rows_json(self.table_ref, [row])
        if errors:
            logger.error(f"Error inserting vote: {errors}")
            raise ValueError(f"Failed to insert vote: {errors}")

        logger.info(f"Successfully inserted vote for {name} - {categoria} - {participant}")
        return True

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    @rate_limit(
        service="bigquery",
        operation_type="insert",
        max_ops=RATE_LIMITS["bigquery"]["insert"]["max_ops"],
        window_seconds=RATE_LIMITS["bigquery"]["insert"]["window"],
    )
    def batch_insert_votes(self, votes: list[dict]) -> bool:
        """Insert multiple votes using BigQuery streaming insert.

        Args:
            votes: List of vote dictionaries, each containing:
                - Nome: str
                - Participante: str
                - Categoria: str
                - Originalidade: int
                - Aparencia: int
                - Sabor: int
                - Data: datetime

        Returns:
            bool: True if all inserts were successful.
        """
        if not CONFIG.get("QUOTA_PROTECTION_ENABLED", True):
            return self._batch_insert_votes_internal(votes)

        try:
            if not votes:
                return True

            # Estimate usage
            estimated_bytes = UsageEstimator.estimate_bigquery_insert(len(votes))
            limit = UsageEstimator.get_quota_limit("bigquery", "streaming")

            # Check quota and circuit breaker
            quota_manager = get_quota_manager()
            circuit_breaker = get_circuit_breaker("bigquery")

            can_proceed, status, reason = circuit_breaker.can_proceed(
                "streaming", estimated_bytes, limit
            )

            if not can_proceed:
                raise QuotaExceededError(reason)

            # Execute operation
            result = self._batch_insert_votes_internal(votes)

            # Track actual usage
            quota_manager.track_operation("bigquery", "streaming", estimated_bytes, "bytes")

            if status.value == "warning":
                logger.warning(f"Quota warning for BigQuery batch insert: {reason}")

            return result

        except (QuotaExceededError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error batch inserting votes to BigQuery: {str(e)}")
            raise

    def _batch_insert_votes_internal(self, votes: list[dict]) -> bool:
        """Internal method to batch insert votes without quota checks."""
        if not votes:
            return True

        # Prepare rows for BigQuery
        rows = []
        for vote in votes:
            row = {
                "Nome": str(vote["Nome"]),
                "Participante": str(vote["Participante"]),
                "Categoria": str(vote["Categoria"]),
                "Originalidade": int(vote["Originalidade"]),
                "Aparencia": int(vote["Aparencia"]),
                "Sabor": int(vote["Sabor"]),
                "Data": vote.get("Data", datetime.now()),
            }
            rows.append(row)

        # Use streaming insert API for batch
        errors = self.client.insert_rows_json(self.table_ref, rows)
        if errors:
            logger.error(f"Error inserting votes: {errors}")
            raise ValueError(f"Failed to insert votes: {errors}")

        logger.info(f"Successfully inserted {len(votes)} votes to BigQuery")
        return True

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def append_data(self, data: pd.DataFrame) -> bool:
        """Append new votes to BigQuery table.

        For single or small batches, consider using insert_vote() or batch_insert_votes()
        for better performance. This method is better for large batches.

        Args:
            data: The voting data to append.

        Returns:
            bool: True if append was successful.
        """
        if not CONFIG.get("QUOTA_PROTECTION_ENABLED", True):
            return self._append_data_internal(data)

        try:
            # Validate data before appending
            validate_vote_data(data)

            if data.empty:
                return True

            # Estimate usage
            estimated_bytes = UsageEstimator.estimate_bigquery_insert(len(data))
            limit = UsageEstimator.get_quota_limit("bigquery", "streaming")

            # Check quota and circuit breaker
            quota_manager = get_quota_manager()
            circuit_breaker = get_circuit_breaker("bigquery")

            can_proceed, status, reason = circuit_breaker.can_proceed(
                "streaming", estimated_bytes, limit
            )

            if not can_proceed:
                raise QuotaExceededError(reason)

            # Execute operation
            result = self._append_data_internal(data)

            # Track actual usage
            quota_manager.track_operation("bigquery", "streaming", estimated_bytes, "bytes")

            if status.value == "warning":
                logger.warning(f"Quota warning for BigQuery append: {reason}")

            return result

        except (QuotaExceededError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error appending data to BigQuery: {str(e)}")
            raise

    def _append_data_internal(self, data: pd.DataFrame) -> bool:
        """Internal method to append data without quota checks."""
        if data.empty:
            return True

        # For small batches, use streaming insert for better performance
        if len(data) <= 100:
            votes = data.to_dict("records")
            return self.batch_insert_votes(votes)

        # For larger batches, use load job
        # Prepare data for BigQuery
        data_to_upload = data.copy()
        if "Data" in data_to_upload.columns:
            data_to_upload["Data"] = pd.to_datetime(data_to_upload["Data"])

        # Use load job for larger datasets
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            source_format=bigquery.SourceFormat.CSV,
        )

        csv_string = data_to_upload.to_csv(index=False)
        job = self.client.load_table_from_string(
            csv_string, self.table_ref, job_config=job_config
        )
        job.result()

        logger.info(f"Successfully appended {len(data)} votes to BigQuery")
        return True
