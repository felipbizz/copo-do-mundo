import logging

from PIL import Image

from backend.data.storage.cloud_storage import CloudStorageImageStorage
from backend.data.storage.local_storage import LocalImageStorage
from backend.utils.circuit_breaker import QuotaExceededError
from config import CONFIG, UI_MESSAGES

logger = logging.getLogger(__name__)


class ImageManager:
    """Manages image operations with storage abstraction."""

    def __init__(self):
        """Initialize ImageManager with appropriate storage backend."""
        storage_backend = CONFIG.get("STORAGE_BACKEND", "local")
        self._primary_storage = None
        self._fallback_storage = LocalImageStorage()
        self._using_fallback = False

        if storage_backend == "gcp":
            try:
                self._primary_storage = CloudStorageImageStorage(
                    project_id=CONFIG.get("GCP_PROJECT_ID"),
                    bucket_name=CONFIG.get("CLOUD_STORAGE_BUCKET"),
                )
                self.storage = self._primary_storage
                logger.info("Initialized ImageManager with Cloud Storage")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Cloud Storage: {str(e)}. "
                    "Falling back to local storage."
                )
                self.storage = self._fallback_storage
                self._using_fallback = True
        else:
            self.storage = self._fallback_storage
            self._using_fallback = True
            logger.info("Initialized ImageManager with local storage")

    def _handle_quota_exceeded(self, operation: str) -> None:
        """Handle quota exceeded by switching to fallback storage.

        Args:
            operation: Name of the operation that failed.
        """
        if self._using_fallback:
            # Already using fallback
            return

        logger.warning(
            f"Quota exceeded during {operation}. "
            "Switching to local storage fallback for images."
        )
        self.storage = self._fallback_storage
        self._using_fallback = True

    def load_and_resize_image(self, image_path: str, width: int | None = None) -> Image.Image | None:
        """Load and resize image from storage.

        Args:
            image_path: Path to the image (relative path for local, full path for Cloud Storage).
            width: Optional target width for resizing.

        Returns:
            PIL Image object or None if not found.
        """
        try:
            image = self.storage.load_image(image_path)
            if image and width:
                ratio = width / image.size[0]
                height = int(image.size[1] * ratio)
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            return image
        except QuotaExceededError:
            self._handle_quota_exceeded("load_image")
            logger.info("Retrying load_image with local storage fallback")
            # Retry with fallback storage
            image = self.storage.load_image(image_path)
            if image and width:
                ratio = width / image.size[0]
                height = int(image.size[1] * ratio)
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            logger.error(UI_MESSAGES["ERROR_LOAD_IMAGE"].format(str(e)))
            return None

    @staticmethod
    def optimize_image(image: Image.Image) -> Image.Image | None:
        """Optimize image.

        Args:
            image: PIL Image object to optimize.

        Returns:
            Optimized PIL Image object or None if error.
        """
        try:
            if not image:
                return None

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Calculate aspect ratio for resizing
            width, height = image.size
            max_width, max_height = CONFIG["IMAGE_MAX_SIZE"]

            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                new_size = (int(width * ratio), int(height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            return image
        except Exception as e:
            logger.error(UI_MESSAGES["ERROR_OPTIMIZE_IMAGE"].format(str(e)))
            return None

    def save_image(self, image: Image.Image, image_path: str) -> bool:
        """Save image to storage.

        Args:
            image: PIL Image object to save.
            image_path: Path where to save the image.

        Returns:
            bool: True if save was successful.
        """
        try:
            if image is None:
                logger.error("Imagem inválida ou corrompida")
                return False

            optimized_image = ImageManager.optimize_image(image)
            if optimized_image:
                return self.storage.save_image(optimized_image, image_path)
            else:
                logger.error("Falha ao otimizar a imagem")
                return False
        except QuotaExceededError:
            self._handle_quota_exceeded("save_image")
            logger.info("Retrying save_image with local storage fallback")
            # Retry with fallback storage
            optimized_image = ImageManager.optimize_image(image)
            if optimized_image:
                return self.storage.save_image(optimized_image, image_path)
            return False
        except Exception as e:
            logger.error(UI_MESSAGES["ERROR_PHOTO"].format(str(e)))
            return False

    def delete_image(self, image_path: str) -> bool:
        """Delete image from storage.

        Args:
            image_path: Path to the image to delete.

        Returns:
            bool: True if deletion was successful.
        """
        try:
            return self.storage.delete_image(image_path)
        except Exception as e:
            logger.error(UI_MESSAGES["ERROR_PHOTO"].format(str(e)))
            return False

    def image_exists(self, image_path: str) -> bool:
        """Check if image exists in storage.

        Args:
            image_path: Path to check.

        Returns:
            bool: True if image exists.
        """
        return self.storage.image_exists(image_path)
