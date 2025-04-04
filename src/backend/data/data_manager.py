import logging
from pathlib import Path

import pandas as pd

from config import CONFIG

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
        """
        self.data_file = Path(data_file or CONFIG["DATA_FILE"])
        self._ensure_data_file_exists()

    def _ensure_data_file_exists(self) -> None:
        """Ensure the data file exists with the correct structure.

        Raises:
            DataManagerError: If there's an error creating the data file.
        """
        try:
            if not self.data_file.exists():
                # Create empty DataFrame with the correct structure
                df = pd.DataFrame(
                    columns=[
                        "Nome",
                        "Participante",
                        "Categoria",
                        "Originalidade",
                        "Aparencia",
                        "Sabor",
                        "Data",
                    ]
                )
                df.to_csv(self.data_file, index=False)
                logger.info(f"Created new data file at {self.data_file}")
        except Exception as e:
            raise DataManagerError(f"Failed to create data file: {str(e)}") from e

    def load_data(self) -> pd.DataFrame:
        """Load voting data from CSV file.

        Returns:
            pd.DataFrame: The loaded voting data.

        Raises:
            DataManagerError: If there's an error loading the data.
        """
        try:
            df = pd.read_csv(self.data_file)
            # Convert Data column to datetime
            df["Data"] = pd.to_datetime(df["Data"])
            logger.info(f"Successfully loaded {len(df)} votes from {self.data_file}")
            return df
        except Exception as e:
            raise DataManagerError(f"Error loading data: {str(e)}") from e

    def save_data(self, data: pd.DataFrame) -> bool:
        """Save voting data to CSV file.

        Args:
            data (pd.DataFrame): The voting data to save.

        Returns:
            bool: True if save was successful, False otherwise.

        Raises:
            DataManagerError: If there's an error saving the data.
        """
        try:
            data.to_csv(self.data_file, index=False)
            logger.info(f"Successfully saved {len(data)} votes to {self.data_file}")
            return True
        except Exception as e:
            raise DataManagerError(f"Error saving data: {str(e)}") from e
