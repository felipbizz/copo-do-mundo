"""Usage estimation utilities for GCP operations."""

import logging
from typing import Any

import pandas as pd

from config import QUOTA_LIMITS

logger = logging.getLogger(__name__)


class UsageEstimator:
    """Estimates usage/cost for GCP operations."""

    @staticmethod
    def estimate_bigquery_query(query: str, table_size_bytes: float = 0) -> float:
        """Estimate bytes scanned for a BigQuery query.

        Args:
            query: SQL query string.
            table_size_bytes: Known table size in bytes (if available).

        Returns:
            Estimated bytes to be scanned.
        """
        # Simple heuristic: if SELECT *, estimate full table scan
        if "SELECT *" in query.upper() or "SELECT *" in query:
            return table_size_bytes if table_size_bytes > 0 else 1024 * 1024  # 1MB default

        # For specific columns, estimate 50% of table size
        # This is a rough estimate - actual depends on column sizes
        if table_size_bytes > 0:
            return table_size_bytes * 0.5

        # Default conservative estimate: 100KB per query
        return 100 * 1024

    @staticmethod
    def estimate_bigquery_insert(num_rows: int, avg_row_size: int | None = None) -> float:
        """Estimate bytes for BigQuery insert operation.

        Args:
            num_rows: Number of rows to insert.
            avg_row_size: Average row size in bytes. If None, uses config default.

        Returns:
            Estimated bytes.
        """
        if avg_row_size is None:
            avg_row_size = int(QUOTA_LIMITS.get("bigquery", {}).get("avg_row_size_bytes", 200))
        return num_rows * avg_row_size

    @staticmethod
    def estimate_bigquery_load(data: pd.DataFrame) -> float:
        """Estimate bytes for BigQuery load operation.

        Args:
            data: DataFrame to load.

        Returns:
            Estimated bytes.
        """
        # Estimate based on DataFrame memory usage
        try:
            memory_usage = data.memory_usage(deep=True).sum()
            return float(memory_usage)
        except Exception:
            # Fallback: estimate based on rows and columns
            num_rows = len(data)
            num_cols = len(data.columns)
            avg_row_size = 200  # bytes
            return num_rows * num_cols * avg_row_size

    @staticmethod
    def estimate_cloud_storage_upload(file_size_bytes: int) -> float:
        """Estimate bytes for Cloud Storage upload.

        Args:
            file_size_bytes: Size of file to upload in bytes.

        Returns:
            Estimated bytes (same as input, but for consistency).
        """
        return float(file_size_bytes)

    @staticmethod
    def estimate_cloud_storage_download(file_size_bytes: int) -> float:
        """Estimate egress bytes for Cloud Storage download.

        Args:
            file_size_bytes: Size of file to download in bytes.

        Returns:
            Estimated egress bytes.
        """
        return float(file_size_bytes)

    @staticmethod
    def estimate_cloud_storage_operation(operation_type: str, **kwargs: Any) -> float:
        """Estimate usage for a Cloud Storage operation.

        Args:
            operation_type: Type of operation ("upload", "download", "delete").
            **kwargs: Operation-specific parameters.

        Returns:
            Estimated usage (bytes for upload/download, operations for delete).
        """
        if operation_type == "upload":
            file_size = kwargs.get("file_size_bytes", 0)
            return UsageEstimator.estimate_cloud_storage_upload(file_size)
        elif operation_type == "download":
            file_size = kwargs.get("file_size_bytes", 0)
            return UsageEstimator.estimate_cloud_storage_download(file_size)
        elif operation_type == "delete":
            # Delete operations count as Class A operations (1 operation)
            return 1.0
        else:
            logger.warning(f"Unknown operation type: {operation_type}")
            return 0.0

    @staticmethod
    def get_quota_limit(service: str, operation_type: str) -> float:
        """Get quota limit for a service and operation type.

        Args:
            service: Service name ("bigquery" or "cloud_storage").
            operation_type: Operation type.

        Returns:
            Quota limit.
        """
        limits = QUOTA_LIMITS.get(service, {})

        # Map operation types to quota limits
        if service == "bigquery":
            if operation_type in ["query", "load_data"]:
                # Convert TB to bytes
                return limits.get("queries_tb", 1) * 1024 * 1024 * 1024 * 1024
            elif operation_type in ["insert", "append", "streaming"]:
                # Convert GB to bytes
                return limits.get("streaming_gb", 10) * 1024 * 1024 * 1024
            elif operation_type == "storage":
                # Convert GB to bytes
                return limits.get("storage_gb", 10) * 1024 * 1024 * 1024

        elif service == "cloud_storage":
            if operation_type == "upload":
                # Storage limit
                return limits.get("storage_gb", 5) * 1024 * 1024 * 1024
            elif operation_type == "download":
                # Egress limit
                return limits.get("egress_gb", 5) * 1024 * 1024 * 1024
            elif operation_type == "class_a":
                return float(limits.get("class_a_ops", 5000))
            elif operation_type == "class_b":
                return float(limits.get("class_b_ops", 50000))

        logger.warning(f"Unknown service/operation: {service}.{operation_type}. Returning default limit of 0.")
        return 0.0
