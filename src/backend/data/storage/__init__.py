"""Storage abstraction layer for data persistence.

This module provides interfaces and implementations for storing votes and images
using different backends (local files, BigQuery, Cloud Storage).
"""

from backend.data.storage.bigquery_storage import BigQueryVoteStorage
from backend.data.storage.cloud_storage import CloudStorageImageStorage
from backend.data.storage.local_storage import LocalImageStorage, LocalVoteStorage

__all__ = [
    "LocalVoteStorage",
    "LocalImageStorage",
    "BigQueryVoteStorage",
    "CloudStorageImageStorage",
]
