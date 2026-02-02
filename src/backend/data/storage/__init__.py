"""Storage abstraction layer for data persistence.

This module provides interfaces and implementations for storing votes and images
using different backends (local files, BigQuery, Cloud Storage).
"""

from backend.data.storage.local_storage import LocalVoteStorage, LocalImageStorage
from backend.data.storage.bigquery_storage import BigQueryVoteStorage
from backend.data.storage.cloud_storage import CloudStorageImageStorage

__all__ = [
    "LocalVoteStorage",
    "LocalImageStorage",
    "BigQueryVoteStorage",
    "CloudStorageImageStorage",
]
