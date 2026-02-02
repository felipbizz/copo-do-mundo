import logging

import pandas as pd

from config import CONFIG
from backend.data.storage.local_storage import LocalVoteStorage
from backend.data.storage.bigquery_storage import BigQueryVoteStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataManagerError(Exception):
    """Base exception for DataManager errors."""

    pass


class DataManager:
    """Manages the storage and retrieval of competition voting data.

    This class handles all data operations including loading, saving, and analyzing
    voting data for the competition. It ensures data integrity and provides methods
    for calculating results and statistics.
    """

    def __init__(self, data_file: str | None = None):
        """Initialize the DataManager.

        Args:
            data_file (Optional[str]): Path to the data file. If None, uses CONFIG["DATA_FILE"].
                Only used for local storage backend.
        """
        storage_backend = CONFIG.get("STORAGE_BACKEND", "local")

        if storage_backend == "gcp":
            try:
                self.storage = BigQueryVoteStorage(
                    project_id=CONFIG.get("GCP_PROJECT_ID"),
                    dataset_id=CONFIG.get("BIGQUERY_DATASET"),
                    table_id=CONFIG.get("BIGQUERY_TABLE"),
                )
                logger.info("Initialized DataManager with BigQuery storage")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize BigQuery storage: {str(e)}. "
                    "Falling back to local storage."
                )
                self.storage = LocalVoteStorage(data_file)
        else:
            self.storage = LocalVoteStorage(data_file)
            logger.info("Initialized DataManager with local storage")

    def load_data(self) -> pd.DataFrame:
        """Load voting data from storage.

        Returns:
            pd.DataFrame: The loaded voting data.

        Raises:
            DataManagerError: If there's an error loading the data.
        """
        try:
            return self.storage.load_data()
        except Exception as e:
            raise DataManagerError(f"Error loading data: {str(e)}") from e

    def save_data(self, data: pd.DataFrame) -> bool:
        """Save voting data to storage.

        Args:
            data (pd.DataFrame): The voting data to save.

        Returns:
            bool: True if save was successful, False otherwise.

        Raises:
            DataManagerError: If there's an error saving the data.
        """
        try:
            return self.storage.save_data(data)
        except Exception as e:
            raise DataManagerError(f"Error saving data: {str(e)}") from e
