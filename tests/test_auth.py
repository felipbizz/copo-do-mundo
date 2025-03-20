import pytest
import streamlit as st
from backend.validation.validators import Validators
from config import CONFIG

@pytest.fixture
def validators():
    return Validators()

def test_admin_password_validation(validators):
    """Test admin password validation"""
    # Test correct password
    assert validators.validate_admin_password(CONFIG["ADMIN_PASSWORD"]) == True
    
    # Test incorrect password
    assert validators.validate_admin_password("wrong_password") == False
    
    # Test empty password
    assert validators.validate_admin_password("") == False

def test_results_password_validation(validators):
    """Test results password validation"""
    # Test correct password
    assert validators.validate_results_password(CONFIG["RESULTS_PASSWORD"]) == True
    
    # Test incorrect password
    assert validators.validate_results_password("wrong_password") == False
    
    # Test empty password
    assert validators.validate_results_password("") == False

def test_session_state_reset():
    """Test that session state is properly reset when password is removed"""
    # Initialize session state
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "results_access" not in st.session_state:
        st.session_state.results_access = False
        
    # Set access
    st.session_state.is_admin = True
    st.session_state.results_access = True
    
    # Simulate password removal
    validators = Validators()
    assert validators.validate_admin_password("") == False
    assert validators.validate_results_password("") == False
    
    # Check that access is revoked
    assert st.session_state.is_admin == False
    assert st.session_state.results_access == False 