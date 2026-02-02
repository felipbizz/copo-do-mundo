"""Cloud Storage implementation for images."""

import logging
import os
from io import BytesIO
from pathlib import Path

from PIL import Image
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError

from backend.utils.retry import retry_with_backoff
from config import CONFIG

logger = logging.getLogger(__name__)


class CloudStorageImageStorage:
    """Cloud Storage for images."""

    def __init__(
        self,
        project_id: str | None = None,
        bucket_name: str | None = None,
    ):
        """Initialize Cloud Storage image storage.

        Args:
            project_id: GCP project ID. If None, uses GCP_PROJECT_ID env var.
            bucket_name: Cloud Storage bucket name. If None, uses CLOUD_STORAGE_BUCKET env var.
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.bucket_name = bucket_name or os.getenv("CLOUD_STORAGE_BUCKET")

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be set")
        if not self.bucket_name:
            raise ValueError("CLOUD_STORAGE_BUCKET must be set")

        try:
            self.client = storage.Client(project=self.project_id)
            self.bucket = self.client.bucket(self.bucket_name)
            self._ensure_bucket_exists()
        except DefaultCredentialsError as e:
            logger.error(f"GCP credentials not found: {str(e)}")
            raise ValueError(
                "GCP credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS "
                "or use Workload Identity Federation."
            ) from e

    def _ensure_bucket_exists(self) -> None:
        """Ensure the Cloud Storage bucket exists."""
        try:
            self.bucket.reload()
            logger.info(f"Bucket {self.bucket_name} exists")
        except Exception:
            # Bucket doesn't exist, create it
            self.bucket = self.client.create_bucket(
                self.bucket_name, location="US"
            )
            logger.info(f"Created bucket {self.bucket_name}")

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def save_image(self, image: Image.Image, image_path: str) -> bool:
        """Save image to Cloud Storage.

        Args:
            image: PIL Image object to save.
            image_path: Path/name for the image in the bucket.

        Returns:
            bool: True if save was successful.
        """
        try:
            if image is None:
                logger.error("Invalid image provided")
                return False

            # Optimize image
            if image.mode != "RGB":
                image = image.convert("RGB")

            width, height = image.size
            max_width, max_height = CONFIG["IMAGE_MAX_SIZE"]
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                new_size = (int(width * ratio), int(height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Convert image to bytes
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=CONFIG["IMAGE_QUALITY"])
            buffer.seek(0)

            # Upload to Cloud Storage
            blob = self.bucket.blob(image_path)
            blob.upload_from_file(buffer, content_type="image/jpeg")
            blob.make_public()  # Make images publicly accessible

            logger.info(f"Saved image to Cloud Storage: {image_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving image to Cloud Storage: {str(e)}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def load_image(self, image_path: str) -> Image.Image | None:
        """Load image from Cloud Storage.

        Args:
            image_path: Path/name of the image in the bucket.

        Returns:
            PIL Image object or None if not found.
        """
        try:
            blob = self.bucket.blob(image_path)
            if not blob.exists():
                logger.warning(f"Image not found in Cloud Storage: {image_path}")
                return None

            # Download image to bytes
            image_bytes = blob.download_as_bytes()
            image = Image.open(BytesIO(image_bytes))

            logger.info(f"Loaded image from Cloud Storage: {image_path}")
            return image
        except Exception as e:
            logger.error(f"Error loading image from Cloud Storage: {str(e)}")
            return None

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def delete_image(self, image_path: str) -> bool:
        """Delete image from Cloud Storage.

        Args:
            image_path: Path/name of the image in the bucket.

        Returns:
            bool: True if deletion was successful.
        """
        try:
            blob = self.bucket.blob(image_path)
            if blob.exists():
                blob.delete()
                logger.info(f"Deleted image from Cloud Storage: {image_path}")
                return True
            logger.warning(f"Image not found for deletion: {image_path}")
            return False
        except Exception as e:
            logger.error(f"Error deleting image from Cloud Storage: {str(e)}")
            return False

    def image_exists(self, image_path: str) -> bool:
        """Check if image exists in Cloud Storage.

        Args:
            image_path: Path/name of the image in the bucket.

        Returns:
            bool: True if image exists.
        """
        try:
            blob = self.bucket.blob(image_path)
            return blob.exists()
        except Exception as e:
            logger.error(f"Error checking image existence: {str(e)}")
            return False

    def get_image_url(self, image_path: str) -> str | None:
        """Get public URL for an image.

        Args:
            image_path: Path/name of the image in the bucket.

        Returns:
            Public URL string or None if image doesn't exist.
        """
        try:
            blob = self.bucket.blob(image_path)
            if blob.exists():
                return blob.public_url
            return None
        except Exception as e:
            logger.error(f"Error getting image URL: {str(e)}")
            return None
