import os

from PIL import Image

from config import CONFIG, UI_MESSAGES


class ImageManager:
    @staticmethod
    def load_and_resize_image(image_path: str, width: int | None = None) -> Image.Image | None:
        """Load and resize image"""
        try:
            image = Image.open(image_path)
            if width:
                ratio = width / image.size[0]
                height = int(image.size[1] * ratio)
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            print(UI_MESSAGES["ERROR_LOAD_IMAGE"].format(str(e)))
            return None

    @staticmethod
    def optimize_image(image: Image.Image) -> Image.Image | None:
        """Optimize image"""
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
            print(UI_MESSAGES["ERROR_OPTIMIZE_IMAGE"].format(str(e)))
            return None

    @staticmethod
    def save_image(image: Image.Image, image_path: str) -> bool:
        """Save image to file"""
        try:
            if image is None:
                print("Imagem inválida ou corrompida")
                return False

            optimized_image = ImageManager.optimize_image(image)
            if optimized_image:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                optimized_image.save(image_path, "JPEG", quality=CONFIG["IMAGE_QUALITY"])
                return True
            else:
                print("Falha ao otimizar a imagem")
                return False
        except Exception as e:
            print(UI_MESSAGES["ERROR_PHOTO"].format(str(e)))
            return False

    @staticmethod
    def delete_image(image_path: str) -> bool:
        """Delete image file"""
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                return True
            return False
        except Exception as e:
            print(UI_MESSAGES["ERROR_PHOTO"].format(str(e)))
            return False
