import os
import pytest
from PIL import Image
from backend.image.image_manager import ImageManager
from config import CONFIG

@pytest.fixture
def image_manager():
    return ImageManager()

@pytest.fixture
def test_image():
    """Create a test image"""
    img = Image.new('RGB', (100, 100), color='red')
    return img

@pytest.fixture
def test_image_path(tmp_path):
    """Create a temporary path for test image"""
    return os.path.join(tmp_path, "test_image.jpg")

def test_save_image(image_manager, test_image, test_image_path):
    """Test saving an image"""
    # Test saving valid image
    assert image_manager.save_image(test_image, test_image_path) == True
    assert os.path.exists(test_image_path)
    
    # Test saving invalid image
    assert image_manager.save_image(None, test_image_path) == False

def test_delete_image(image_manager, test_image, test_image_path):
    """Test deleting an image"""
    # Save image first
    image_manager.save_image(test_image, test_image_path)
    
    # Test deleting existing image
    assert image_manager.delete_image(test_image_path) == True
    assert not os.path.exists(test_image_path)
    
    # Test deleting non-existent image
    assert image_manager.delete_image("nonexistent.jpg") == False

def test_optimize_image(image_manager, test_image):
    """Test image optimization"""
    # Test optimizing valid image
    optimized = image_manager.optimize_image(test_image)
    assert isinstance(optimized, Image.Image)
    assert optimized.size <= (CONFIG["IMAGE_MAX_SIZE"])
    
    # Test optimizing None
    assert image_manager.optimize_image(None) is None

def test_load_and_resize_image(image_manager, test_image, test_image_path):
    """Test loading and resizing image"""
    # Save test image
    image_manager.save_image(test_image, test_image_path)
    
    # Test loading and resizing
    resized = image_manager.load_and_resize_image(test_image_path, width=50)
    assert isinstance(resized, Image.Image)
    assert resized.size[0] == 50  # width should be 50
    
    # Test loading non-existent image
    assert image_manager.load_and_resize_image("nonexistent.jpg", width=50) is None 