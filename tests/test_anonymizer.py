import pytest
import streamlit as st
from frontend.utils.anonymizer import Anonymizer

@pytest.fixture
def mock_session_state():
    """Fixture to mock Streamlit session state"""
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    return st.session_state

def test_initialize_anonymization(mock_session_state):
    """Test initialization of anonymization data"""
    Anonymizer.initialize_anonymization()
    assert "drink_codes" in st.session_state
    assert "code_to_participant" in st.session_state
    assert "drink_names" in st.session_state
    assert isinstance(st.session_state.drink_codes, dict)
    assert isinstance(st.session_state.code_to_participant, dict)
    assert isinstance(st.session_state.drink_names, dict)

def test_generate_code():
    """Test code generation"""
    code = Anonymizer.generate_code()
    assert len(code) == 6
    assert all(c.isalnum() for c in code)
    assert all(c.isupper() or c.isdigit() for c in code)

def test_get_or_create_code(mock_session_state):
    """Test code creation and retrieval"""
    # Test new code creation
    code1 = Anonymizer.get_or_create_code(1, "Categoria1")
    assert code1 in st.session_state.drink_codes.values()
    assert code1 in st.session_state.code_to_participant
    
    # Test existing code retrieval
    code2 = Anonymizer.get_or_create_code(1, "Categoria1")
    assert code1 == code2

def test_get_participant_from_code(mock_session_state):
    """Test participant retrieval from code"""
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    participant, categoria = Anonymizer.get_participant_from_code(code)
    assert participant == 1
    assert categoria == "Categoria1"

def test_get_code_from_participant(mock_session_state):
    """Test code retrieval from participant"""
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    retrieved_code = Anonymizer.get_code_from_participant(1, "Categoria1")
    assert code == retrieved_code

def test_drink_name_management(mock_session_state):
    """Test drink name management"""
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    
    # Test setting name
    Anonymizer.set_drink_name(code, "Gin Tônica")
    assert Anonymizer.get_drink_name(code) == "Gin Tônica"
    
    # Test fallback to code when no name is set
    new_code = Anonymizer.get_or_create_code(2, "Categoria2")
    assert Anonymizer.get_drink_name(new_code) == new_code

def test_clear_anonymization(mock_session_state):
    """Test clearing anonymization data"""
    # Setup test data
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    Anonymizer.set_drink_name(code, "Gin Tônica")
    
    # Clear data
    Anonymizer.clear_anonymization()
    
    # Verify clearing
    assert not st.session_state.drink_codes
    assert not st.session_state.code_to_participant
    assert not st.session_state.drink_names 