"""BigQuery storage implementation for votes."""

import logging
import os
from typing import Any

import pandas as pd
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

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

    def load_data(self) -> pd.DataFrame:
        """Load voting data from BigQuery.

        Returns:
            pd.DataFrame: The loaded voting data.
        """
        try:
            query = f"SELECT * FROM `{self.table_ref}` ORDER BY Data DESC"
            df = self.client.query(query).to_dataframe()
            # Ensure Data column is datetime
            if "Data" in df.columns and len(df) > 0:
                df["Data"] = pd.to_datetime(df["Data"])
            logger.info(f"Successfully loaded {len(df)} votes from BigQuery")
            return df
        except Exception as e:
            logger.error(f"Error loading data from BigQuery: {str(e)}")
            raise

    def save_data(self, data: pd.DataFrame) -> bool:
        """Save voting data to BigQuery.

        This method replaces all data in the table. For append operations,
        use append_data instead.

        Args:
            data: The voting data to save.

        Returns:
            bool: True if save was successful.
        """
        try:
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
            # For simplicity, we'll delete all and re-insert
            # In production, you might want to use merge/upsert operations
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

    def append_data(self, data: pd.DataFrame) -> bool:
        """Append new votes to BigQuery table.

        Args:
            data: The voting data to append.

        Returns:
            bool: True if append was successful.
        """
        try:
            if data.empty:
                return True

            # Prepare data for BigQuery
            data_to_upload = data.copy()
            if "Data" in data_to_upload.columns:
                data_to_upload["Data"] = pd.to_datetime(data_to_upload["Data"])

            # Use streaming insert for better performance
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
        except Exception as e:
            logger.error(f"Error appending data to BigQuery: {str(e)}")
            raise
