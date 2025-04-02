import pytest
import streamlit as st

from backend.validation.validators import Validators
from config import CONFIG
from frontend.utils.session_manager import SessionManager


@pytest.fixture
def validators():
    return Validators()


@pytest.fixture
def mock_session_state():
    """Fixture to mock Streamlit session state"""
    if not hasattr(st, "session_state"):
        st.session_state = {}
    return st.session_state


def test_admin_password_validation(validators):
    """Test admin password validation"""
    # Test correct password
    assert validators.validate_admin_password(CONFIG["ADMIN_PASSWORD"]) is True

    # Test incorrect password
    assert validators.validate_admin_password("wrong_password") is False

    # Test empty password
    assert validators.validate_admin_password("") is False


def test_results_password_validation(mock_session_state, validators):
    """Test results password validation"""
    # Setup test data
    CONFIG["RESULTS_PASSWORD"] = "test_password"

    # Test invalid password
    assert not validators.validate_results_password("wrong_password")

    # Test valid password
    assert validators.validate_results_password("test_password")


def test_session_state_reset(mock_session_state):
    """Test session state reset"""
    # Setup test data
    CONFIG["RESULTS_PASSWORD"] = "test_password"
    SessionManager.set("is_admin", True)
    SessionManager.set("results_access", True)

    # Reset session state
    SessionManager.reset_access_state()

    # Verify state was reset
    assert not SessionManager.get("is_admin", False)
    assert not SessionManager.get("results_access", False)
