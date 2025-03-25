import pytest
import os
import pandas as pd
from datetime import datetime
from PIL import Image
import streamlit as st
from frontend.utils.session_manager import SessionManager
from config import CONFIG

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Initialize session state
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    # Reset session state
    st.session_state.clear()
    
    # Initialize required session state variables
    SessionManager.initialize_session_state()
    
    # Initialize anonymizer state
    if 'drink_codes' not in st.session_state:
        st.session_state.drink_codes = {}
    if 'drink_names' not in st.session_state:
        st.session_state.drink_names = {}
    if 'code_to_participant' not in st.session_state:
        st.session_state.code_to_participant = {}
    if 'participant_to_code' not in st.session_state:
        st.session_state.participant_to_code = {}
    
    # Initialize tracking lists
    if 'rendered_elements' not in st.session_state:
        st.session_state.rendered_elements = []
    if 'form_elements' not in st.session_state:
        st.session_state.form_elements = []
    
    # Add test-specific config values
    CONFIG["RESULTS_PASSWORD"] = "test_password"
    CONFIG["ADMIN_PASSWORD"] = "admin_password"
    
    yield
    
    # Cleanup after test
    st.session_state.clear()
    CONFIG.pop("RESULTS_PASSWORD", None)
    CONFIG.pop("ADMIN_PASSWORD", None)

@pytest.fixture
def mock_session_state():
    """Fixture to mock Streamlit session state"""
    return st.session_state

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
    """Mock Streamlit functions to capture rendered elements"""
    # Store original functions
    original_markdown = st.markdown
    original_subheader = st.subheader
    original_write = st.write
    original_error = st.error
    original_warning = st.warning
    original_success = st.success
    original_info = st.info
    
    def mock_markdown(text, **kwargs):
        # Extract text from markdown if it's a string
        if isinstance(text, str):
            # Preserve markdown formatting
            st.session_state.rendered_elements.append(text)
        return original_markdown(text, **kwargs)
    
    def mock_subheader(text, **kwargs):
        if isinstance(text, str):
            st.session_state.rendered_elements.append(text)
        return original_subheader(text, **kwargs)
    
    def mock_write(text, **kwargs):
        if isinstance(text, str):
            st.session_state.rendered_elements.append(text)
        return original_write(text, **kwargs)
    
    def mock_error(text, **kwargs):
        if isinstance(text, str):
            st.session_state.rendered_elements.append(text)
        return original_error(text, **kwargs)
    
    def mock_warning(text, **kwargs):
        if isinstance(text, str):
            st.session_state.rendered_elements.append(text)
        return original_warning(text, **kwargs)
    
    def mock_success(text, **kwargs):
        if isinstance(text, str):
            st.session_state.rendered_elements.append(text)
        return original_success(text, **kwargs)
    
    def mock_info(text, **kwargs):
        if isinstance(text, str):
            st.session_state.rendered_elements.append(text)
        return original_info(text, **kwargs)
    
    # Replace functions with mocks
    st.markdown = mock_markdown
    st.subheader = mock_subheader
    st.write = mock_write
    st.error = mock_error
    st.warning = mock_warning
    st.success = mock_success
    st.info = mock_info
    
    yield
    
    # Restore original functions
    st.markdown = original_markdown
    st.subheader = original_subheader
    st.write = original_write
    st.error = original_error
    st.warning = original_warning
    st.success = original_success
    st.info = original_info 