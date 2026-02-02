import logging
from datetime import datetime

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

    def load_data_since(self, since_timestamp: datetime) -> pd.DataFrame:
        """Load voting data from storage since a specific timestamp.

        This is more efficient than loading all data when you only need recent votes.
        Falls back to full load if storage doesn't support incremental loading.

        Args:
            since_timestamp: Only load votes after this timestamp.

        Returns:
            pd.DataFrame: The loaded voting data.

        Raises:
            DataManagerError: If there's an error loading the data.
        """
        try:
            from datetime import datetime

            if hasattr(self.storage, "load_data_since"):
                return self.storage.load_data_since(since_timestamp)
            else:
                # Fallback: load all data and filter
                all_data = self.load_data()
                if all_data.empty or "Data" not in all_data.columns:
                    return all_data

                # Filter by timestamp
                all_data["Data"] = pd.to_datetime(all_data["Data"])
                filtered_data = all_data[all_data["Data"] > since_timestamp]
                logger.info(
                    f"Loaded {len(filtered_data)} votes since {since_timestamp} "
                    f"(filtered from {len(all_data)} total)"
                )
                return filtered_data
        except Exception as e:
            raise DataManagerError(f"Error loading incremental data: {str(e)}") from e

    def save_data(self, data: pd.DataFrame) -> bool:
        """Save voting data to storage.

        This method replaces all data in storage. For appending new votes,
        use append_vote() or append_data() instead.

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

    def append_vote(
        self,
        name: str,
        participant: str,
        categoria: str,
        originalidade: int,
        aparencia: int,
        sabor: int,
    ) -> bool:
        """Append a single vote to storage.

        This is the preferred method for adding new votes as it's more efficient
        than saving the entire dataset.

        Args:
            name: Name of the juror.
            participant: Participant ID.
            categoria: Category of the vote.
            originalidade: Originality score (0-10).
            aparencia: Appearance score (0-10).
            sabor: Taste score (0-10).

        Returns:
            bool: True if append was successful.

        Raises:
            DataManagerError: If there's an error appending the vote.
        """
        try:
            # Check if storage supports direct insert (BigQuery)
            if hasattr(self.storage, "insert_vote"):
                from datetime import datetime

                return self.storage.insert_vote(
                    name=name,
                    participant=participant,
                    categoria=categoria,
                    originalidade=originalidade,
                    aparencia=aparencia,
                    sabor=sabor,
                    data_timestamp=datetime.now(),
                )
            else:
                # Fallback to append_data for local storage
                from datetime import datetime

                vote_df = pd.DataFrame(
                    [
                        {
                            "Nome": name,
                            "Participante": participant,
                            "Categoria": categoria,
                            "Originalidade": originalidade,
                            "Aparencia": aparencia,
                            "Sabor": sabor,
                            "Data": datetime.now(),
                        }
                    ]
                )
                if hasattr(self.storage, "append_data"):
                    return self.storage.append_data(vote_df)
                else:
                    # For storage backends without append, load, append, and save
                    current_data = self.load_data()
                    updated_data = pd.concat([current_data, vote_df], ignore_index=True)
                    return self.save_data(updated_data)
        except Exception as e:
            raise DataManagerError(f"Error appending vote: {str(e)}") from e

    def append_data(self, data: pd.DataFrame) -> bool:
        """Append multiple votes to storage.

        Args:
            data (pd.DataFrame): The voting data to append.

        Returns:
            bool: True if append was successful.

        Raises:
            DataManagerError: If there's an error appending the data.
        """
        try:
            if hasattr(self.storage, "append_data"):
                return self.storage.append_data(data)
            else:
                # Fallback: load, append, and save
                current_data = self.load_data()
                updated_data = pd.concat([current_data, data], ignore_index=True)
                return self.save_data(updated_data)
        except Exception as e:
            raise DataManagerError(f"Error appending data: {str(e)}") from e
