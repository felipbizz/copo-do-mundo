"""Cloud Storage implementation for images."""

import logging
import os
from io import BytesIO
from pathlib import Path

from PIL import Image
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError

from backend.utils.circuit_breaker import QuotaExceededError, get_circuit_breaker
from backend.utils.quota_manager import get_quota_manager
from backend.utils.rate_limiter import RateLimitExceededError, rate_limit
from backend.utils.retry import retry_with_backoff
from backend.utils.usage_estimator import UsageEstimator
from config import CONFIG, RATE_LIMITS

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
    @rate_limit(
        service="cloud_storage",
        operation_type="upload",
        max_ops=RATE_LIMITS["cloud_storage"]["upload"]["max_ops"],
        window_seconds=RATE_LIMITS["cloud_storage"]["upload"]["window"],
    )
    def save_image(self, image: Image.Image, image_path: str) -> bool:
        """Save image to Cloud Storage.

        Args:
            image: PIL Image object to save.
            image_path: Path/name for the image in the bucket.

        Returns:
            bool: True if save was successful.
        """
        if not CONFIG.get("QUOTA_PROTECTION_ENABLED", True):
            return self._save_image_internal(image, image_path)

        try:
            if image is None:
                logger.error("Invalid image provided")
                return False

            # Optimize image first to get actual size
            if image.mode != "RGB":
                image = image.convert("RGB")

            width, height = image.size
            max_width, max_height = CONFIG["IMAGE_MAX_SIZE"]
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                new_size = (int(width * ratio), int(height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Convert image to bytes to get actual size
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=CONFIG["IMAGE_QUALITY"])
            file_size = buffer.tell()
            buffer.seek(0)

            # Estimate usage
            estimated_bytes = UsageEstimator.estimate_cloud_storage_upload(file_size)
            limit = UsageEstimator.get_quota_limit("cloud_storage", "upload")

            # Check quota and circuit breaker
            quota_manager = get_quota_manager()
            circuit_breaker = get_circuit_breaker("cloud_storage")

            can_proceed, status, reason = circuit_breaker.can_proceed(
                "upload", estimated_bytes, limit
            )

            if not can_proceed:
                raise QuotaExceededError(reason)

            # Execute operation
            result = self._save_image_internal(image, image_path, buffer)

            # Track actual usage (storage and Class A operation)
            quota_manager.track_operation("cloud_storage", "upload", file_size, "bytes")
            quota_manager.track_operation("cloud_storage", "class_a", 1, "operations")

            if status.value == "warning":
                logger.warning(f"Quota warning for Cloud Storage upload: {reason}")

            return result

        except (QuotaExceededError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error saving image to Cloud Storage: {str(e)}")
            return False

    def _save_image_internal(
        self, image: Image.Image, image_path: str, buffer: BytesIO | None = None
    ) -> bool:
        """Internal method to save image without quota checks."""
        if buffer is None:
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

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    @rate_limit(
        service="cloud_storage",
        operation_type="download",
        max_ops=RATE_LIMITS["cloud_storage"]["download"]["max_ops"],
        window_seconds=RATE_LIMITS["cloud_storage"]["download"]["window"],
    )
    def load_image(self, image_path: str) -> Image.Image | None:
        """Load image from Cloud Storage.

        Args:
            image_path: Path/name of the image in the bucket.

        Returns:
            PIL Image object or None if not found.
        """
        if not CONFIG.get("QUOTA_PROTECTION_ENABLED", True):
            return self._load_image_internal(image_path)

        try:
            blob = self.bucket.blob(image_path)
            if not blob.exists():
                logger.warning(f"Image not found in Cloud Storage: {image_path}")
                return None

            # Get blob size for estimation
            blob.reload()
            file_size = blob.size

            # Estimate usage (egress)
            estimated_bytes = UsageEstimator.estimate_cloud_storage_download(file_size)
            limit = UsageEstimator.get_quota_limit("cloud_storage", "download")

            # Check quota and circuit breaker
            quota_manager = get_quota_manager()
            circuit_breaker = get_circuit_breaker("cloud_storage")

            can_proceed, status, reason = circuit_breaker.can_proceed(
                "download", estimated_bytes, limit
            )

            if not can_proceed:
                raise QuotaExceededError(reason)

            # Execute operation
            image = self._load_image_internal(image_path)

            # Track actual usage (egress and Class B operation)
            if image:
                quota_manager.track_operation(
                    "cloud_storage", "download", file_size, "bytes"
                )
                quota_manager.track_operation("cloud_storage", "class_b", 1, "operations")

            if status.value == "warning":
                logger.warning(f"Quota warning for Cloud Storage download: {reason}")

            return image

        except (QuotaExceededError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error loading image from Cloud Storage: {str(e)}")
            return None

    def _load_image_internal(self, image_path: str) -> Image.Image | None:
        """Internal method to load image without quota checks."""
        blob = self.bucket.blob(image_path)
        if not blob.exists():
            logger.warning(f"Image not found in Cloud Storage: {image_path}")
            return None

        # Download image to bytes
        image_bytes = blob.download_as_bytes()
        image = Image.open(BytesIO(image_bytes))

        logger.info(f"Loaded image from Cloud Storage: {image_path}")
        return image

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    @rate_limit(
        service="cloud_storage",
        operation_type="delete",
        max_ops=RATE_LIMITS["cloud_storage"]["delete"]["max_ops"],
        window_seconds=RATE_LIMITS["cloud_storage"]["delete"]["window"],
    )
    def delete_image(self, image_path: str) -> bool:
        """Delete image from Cloud Storage.

        Args:
            image_path: Path/name of the image in the bucket.

        Returns:
            bool: True if deletion was successful.
        """
        if not CONFIG.get("QUOTA_PROTECTION_ENABLED", True):
            return self._delete_image_internal(image_path)

        try:
            # Delete operations count as Class A operations
            estimated_ops = 1.0
            limit = UsageEstimator.get_quota_limit("cloud_storage", "class_a")

            # Check quota and circuit breaker
            quota_manager = get_quota_manager()
            circuit_breaker = get_circuit_breaker("cloud_storage")

            can_proceed, status, reason = circuit_breaker.can_proceed(
                "class_a", estimated_ops, limit
            )

            if not can_proceed:
                raise QuotaExceededError(reason)

            # Execute operation
            result = self._delete_image_internal(image_path)

            # Track actual usage
            if result:
                quota_manager.track_operation("cloud_storage", "class_a", 1, "operations")

            if status.value == "warning":
                logger.warning(f"Quota warning for Cloud Storage delete: {reason}")

            return result

        except (QuotaExceededError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error deleting image from Cloud Storage: {str(e)}")
            return False

    def _delete_image_internal(self, image_path: str) -> bool:
        """Internal method to delete image without quota checks."""
        blob = self.bucket.blob(image_path)
        if blob.exists():
            blob.delete()
            logger.info(f"Deleted image from Cloud Storage: {image_path}")
            return True
        logger.warning(f"Image not found for deletion: {image_path}")
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
