"""Local file storage implementation for votes and images."""

import logging
import os
from pathlib import Path

import pandas as pd
from PIL import Image

from backend.utils.validators import validate_vote_data
from config import CONFIG

logger = logging.getLogger(__name__)


class LocalVoteStorage:
    """Local CSV file storage for votes."""

    def __init__(self, data_file: str | None = None):
        """Initialize local vote storage.

        Args:
            data_file: Path to CSV file. If None, uses CONFIG["DATA_FILE"].
        """
        self.data_file = Path(data_file or CONFIG["DATA_FILE"])
        self._ensure_data_file_exists()

    def _ensure_data_file_exists(self) -> None:
        """Ensure the data file exists with the correct structure."""
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
            logger.error(f"Failed to create data file: {str(e)}")
            raise

    def load_data(self) -> pd.DataFrame:
        """Load voting data from CSV file.

        Returns:
            pd.DataFrame: The loaded voting data.
        """
        try:
            df = pd.read_csv(self.data_file)
            # Convert Data column to datetime
            if "Data" in df.columns and len(df) > 0:
                df["Data"] = pd.to_datetime(df["Data"])
            logger.info(f"Successfully loaded {len(df)} votes from {self.data_file}")
            return df
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def save_data(self, data: pd.DataFrame) -> bool:
        """Save voting data to CSV file.

        This method replaces all data in the file. For append operations,
        use append_data instead.

        Args:
            data: The voting data to save.

        Returns:
            bool: True if save was successful.
        """
        try:
            # Validate data before saving
            validate_vote_data(data)

            data.to_csv(self.data_file, index=False)
            logger.info(f"Successfully saved {len(data)} votes to {self.data_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            raise

    def append_data(self, data: pd.DataFrame) -> bool:
        """Append voting data to CSV file.

        Args:
            data: The voting data to append.

        Returns:
            bool: True if append was successful.
        """
        try:
            # Validate data before appending
            validate_vote_data(data)

            if data.empty:
                return True

            # Load existing data
            existing_data = self.load_data()

            # Append new data
            if existing_data.empty:
                updated_data = data
            else:
                updated_data = pd.concat([existing_data, data], ignore_index=True)

            # Save combined data
            updated_data.to_csv(self.data_file, index=False)
            logger.info(f"Successfully appended {len(data)} votes to {self.data_file}")
            return True
        except Exception as e:
            logger.error(f"Error appending data: {str(e)}")
            raise


class LocalImageStorage:
    """Local file system storage for images."""

    def __init__(self, images_dir: str | None = None):
        """Initialize local image storage.

        Args:
            images_dir: Directory path for images. If None, uses CONFIG["IMAGES_DIR"].
        """
        self.images_dir = Path(images_dir or CONFIG["IMAGES_DIR"])
        os.makedirs(self.images_dir, exist_ok=True)

    def save_image(self, image: Image.Image, image_path: str) -> bool:
        """Save image to local file system.

        Args:
            image: PIL Image object to save.
            image_path: Relative path within images directory.

        Returns:
            bool: True if save was successful.
        """
        try:
            if image is None:
                logger.error("Invalid image provided")
                return False

            full_path = self.images_dir / image_path
            # Ensure the directory exists
            os.makedirs(full_path.parent, exist_ok=True)
            image.save(full_path, "JPEG", quality=CONFIG["IMAGE_QUALITY"])
            logger.info(f"Saved image to {full_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return False

    def load_image(self, image_path: str) -> Image.Image | None:
        """Load image from local file system.

        Args:
            image_path: Relative path within images directory.

        Returns:
            PIL Image object or None if not found.
        """
        try:
            full_path = self.images_dir / image_path
            if not full_path.exists():
                logger.warning(f"Image not found: {full_path}")
                return None
            image = Image.open(full_path)
            logger.info(f"Loaded image from {full_path}")
            return image
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            return None

    def delete_image(self, image_path: str) -> bool:
        """Delete image from local file system.

        Args:
            image_path: Relative path within images directory.

        Returns:
            bool: True if deletion was successful.
        """
        try:
            full_path = self.images_dir / image_path
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted image at {full_path}")
                return True
            logger.warning(f"Image not found for deletion: {full_path}")
            return False
        except Exception as e:
            logger.error(f"Error deleting image: {str(e)}")
            return False

    def image_exists(self, image_path: str) -> bool:
        """Check if image exists.

        Args:
            image_path: Relative path within images directory.

        Returns:
            bool: True if image exists.
        """
        full_path = self.images_dir / image_path
        return full_path.exists()
