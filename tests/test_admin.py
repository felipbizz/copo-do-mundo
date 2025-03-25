import pytest
import streamlit as st
from frontend.components.admin import AdminComponent
from frontend.utils.anonymizer import Anonymizer
from frontend.utils.session_manager import SessionManager

@pytest.fixture
def mock_session_state():
    """Fixture to mock Streamlit session state"""
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    return st.session_state

@pytest.fixture
def admin_component(mock_session_state):
    """Fixture to create an AdminComponent instance"""
    return AdminComponent()

def test_photo_management(admin_component, mock_session_state):
    """Test photo management with anonymization"""
    # Setup test data
    SessionManager.set("num_participants", 2)
    SessionManager.set("categories", ["Categoria1", "Categoria2"])
    
    # Create codes for drinks
    code1 = Anonymizer.get_or_create_code(1, "Categoria1")
    code2 = Anonymizer.get_or_create_code(2, "Categoria1")
    
    # Test drink codes display
    codes = Anonymizer.get_all_codes()
    assert len(codes) == 2
    assert code1 in codes
    assert code2 in codes
    
    # Test custom name setting
    Anonymizer.set_drink_name(code1, "Gin Tônica")
    Anonymizer.set_drink_name(code2, "Mojito")
    
    # Verify names are displayed correctly
    assert Anonymizer.get_drink_name(code1) == "Gin Tônica"
    assert Anonymizer.get_drink_name(code2) == "Mojito"

def test_code_regeneration(admin_component, mock_session_state):
    """Test code regeneration"""
    # Setup initial codes
    SessionManager.set("num_participants", 2)
    SessionManager.set("categories", ["Categoria1", "Categoria2"])
    
    # Create initial codes
    code1 = Anonymizer.get_or_create_code(1, "Categoria1")
    code2 = Anonymizer.get_or_create_code(2, "Categoria1")
    code3 = Anonymizer.get_or_create_code(1, "Categoria2")
    code4 = Anonymizer.get_or_create_code(2, "Categoria2")
    
    # Set custom names
    Anonymizer.set_drink_name(code1, "Gin Tônica")
    Anonymizer.set_drink_name(code2, "Mojito")
    Anonymizer.set_drink_name(code3, "Caipirinha")
    Anonymizer.set_drink_name(code4, "Margarita")
    
    # Clear and regenerate codes
    Anonymizer.clear_anonymization()
    for participant in range(1, SessionManager.get("num_participants") + 1):
        for categoria in SessionManager.get("categories"):
            Anonymizer.get_or_create_code(participant, categoria)
    
    # Verify new codes were generated
    new_codes = Anonymizer.get_all_codes()
    assert len(new_codes) == 4  # 2 participants * 2 categories
    assert code1 not in new_codes  # Old codes should be gone
    assert code2 not in new_codes
    assert code3 not in new_codes
    assert code4 not in new_codes

def test_admin_access_control(admin_component, mock_session_state):
    """Test admin access control with anonymization"""
    # Test admin login
    assert not SessionManager.get("is_admin", False)
    
    # Simulate successful login
    SessionManager.set("is_admin", True)
    
    # Verify admin can see all codes and mappings
    codes = Anonymizer.get_all_codes()
    assert isinstance(codes, dict)
    
    # Test code to participant mapping
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    participant, categoria = Anonymizer.get_participant_from_code(code)
    assert participant == 1
    assert categoria == "Categoria1"

def test_drink_name_management(admin_component, mock_session_state):
    """Test drink name management in admin interface"""
    # Setup test data
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    
    # Test setting name
    Anonymizer.set_drink_name(code, "Gin Tônica")
    assert Anonymizer.get_drink_name(code) == "Gin Tônica"
    
    # Test updating name
    Anonymizer.set_drink_name(code, "Gin Tônica Especial")
    assert Anonymizer.get_drink_name(code) == "Gin Tônica Especial"
    
    # Test name persistence
    new_code = Anonymizer.get_or_create_code(1, "Categoria1")
    assert Anonymizer.get_drink_name(new_code) == "Gin Tônica Especial"

def test_results_access_control(admin_component, mock_session_state):
    """Test results access control"""
    # Initially results should be blocked
    assert not SessionManager.get("results_access", False)
    
    # Simulate admin login
    SessionManager.set("is_admin", True)
    
    # Simulate clicking the toggle button
    st.session_state.toggle_results = True
    
    # Admin should be able to toggle results access
    admin_component._render_results_access()
    
    # Verify results access was toggled
    assert SessionManager.get("results_access", False)
    
    # Simulate clicking the toggle button again
    st.session_state.toggle_results = True
    
    # Admin should be able to toggle results access back
    admin_component._render_results_access()
    
    # Verify results access was toggled back
    assert not SessionManager.get("results_access", False)
    
    # Test that non-admin cannot toggle
    SessionManager.set("is_admin", False)
    st.session_state.toggle_results = True
    admin_component._render_results_access()
    assert not SessionManager.get("results_access", False) 