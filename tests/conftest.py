import pytest
import os
import pandas as pd
from datetime import datetime
from PIL import Image

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    """Setup test environment"""
    # Create test directories
    os.makedirs(os.path.join(tmp_path, "data"), exist_ok=True)
    os.makedirs(os.path.join(tmp_path, "data/images"), exist_ok=True)
    
    # Set environment variables for testing
    os.environ["TEST_MODE"] = "true"
    os.environ["TEST_DATA_DIR"] = str(tmp_path)
    
    yield
    
    # Cleanup
    os.environ.pop("TEST_MODE", None)
    os.environ.pop("TEST_DATA_DIR", None)

@pytest.fixture
def empty_data():
    """Create empty DataFrame with correct structure"""
    return pd.DataFrame(columns=[
        "Nome", "Participante", "Categoria", "Originalidade", 
        "Aparencia", "Sabor", "Data"
    ])

@pytest.fixture
def sample_data():
    """Create sample data for testing"""
    return pd.DataFrame({
        "Nome": ["Test User"],
        "Participante": ["1"],
        "Categoria": ["Caipirinha"],
        "Originalidade": [8],
        "Aparencia": [9],
        "Sabor": [7],
        "Data": [datetime.now()]
    })

@pytest.fixture
def test_image():
    """Create a test image"""
    return Image.new('RGB', (100, 100), color='red')

@pytest.fixture
def mock_streamlit():
    """Mock streamlit session state"""
    import streamlit as st
    
    # Initialize session state
    if not hasattr(st, "session_state"):
        setattr(st, "session_state", {})
    
    # Reset session state before each test
    st.session_state.clear()
    
    return st 