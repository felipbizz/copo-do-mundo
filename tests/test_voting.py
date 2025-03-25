import pytest
import streamlit as st
import pandas as pd
from frontend.components.voting import VotingComponent
from frontend.utils.anonymizer import Anonymizer
from frontend.utils.session_manager import SessionManager
import os
from PIL import Image
from config import CONFIG

@pytest.fixture
def mock_session_state():
    """Fixture to mock Streamlit session state"""
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    return st.session_state

@pytest.fixture
def voting_component(mock_session_state):
    """Fixture to create a VotingComponent instance"""
    return VotingComponent()

def test_drink_selection(voting_component, mock_session_state):
    """Test drink selection with anonymization"""
    # Setup test data
    SessionManager.set("num_participants", 2)
    SessionManager.set("categories", ["Categoria1"])
    SessionManager.set("data", pd.DataFrame(columns=[
        "Nome", "Participante", "Categoria", "Originalidade", 
        "Aparencia", "Sabor", "Data"
    ]))
    
    # Initialize Anonymizer state
    Anonymizer.initialize_anonymization()
    
    # Create test images directory
    os.makedirs(CONFIG["IMAGES_DIR"], exist_ok=True)
    
    # Create test images
    for participant in range(1, 3):
        image_path = os.path.join(CONFIG["IMAGES_DIR"], f"participant_{participant}_categoria1.jpg")
        Image.new('RGB', (100, 100), color='red').save(image_path)
    
    # Create codes for drinks
    code1 = Anonymizer.get_or_create_code(1, "Categoria1")
    code2 = Anonymizer.get_or_create_code(2, "Categoria1")
    
    # Set custom names
    Anonymizer.set_drink_name(code1, "Gin Tônica")
    Anonymizer.set_drink_name(code2, "Mojito")
    
    # Get available codes
    available_codes = voting_component._get_available_codes()
    assert len(available_codes) == 2
    assert code1 in available_codes
    assert code2 in available_codes
    
    # Test code to name mapping
    code_options = {Anonymizer.get_drink_name(code): code for code in available_codes}
    assert "Gin Tônica" in code_options
    assert "Mojito" in code_options
    assert code_options["Gin Tônica"] == code1
    assert code_options["Mojito"] == code2
    
    # Cleanup test images
    for participant in range(1, 3):
        image_path = os.path.join(CONFIG["IMAGES_DIR"], f"participant_{participant}_categoria1.jpg")
        if os.path.exists(image_path):
            os.remove(image_path)

def test_vote_submission(voting_component, mock_session_state):
    """Test vote submission with anonymization"""
    # Setup test data
    SessionManager.set("data", pd.DataFrame())
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    Anonymizer.set_drink_name(code, "Gin Tônica")
    
    # Test vote validation
    assert voting_component._validate_vote("Teste", code)
    assert not voting_component._validate_vote("Teste", "")
    
    # Test vote saving
    voting_component._save_vote("Teste", code, 8, 9, 10)
    
    # Verify vote was saved correctly
    data = SessionManager.get("data")
    assert not data.empty
    assert data.iloc[0]["Nome"] == "Teste"
    assert data.iloc[0]["Participante"] == "1"
    assert data.iloc[0]["Categoria"] == "Categoria1"
    assert data.iloc[0]["Originalidade"] == 8
    assert data.iloc[0]["Aparencia"] == 9
    assert data.iloc[0]["Sabor"] == 10

def test_voting_form(voting_component, mock_session_state, mock_streamlit):
    """Test voting form rendering with anonymization"""
    # Setup test data
    SessionManager.set("num_participants", 2)
    SessionManager.set("categories", ["Categoria1"])
    SessionManager.set("data", pd.DataFrame(columns=[
        "Nome", "Participante", "Categoria", "Originalidade", 
        "Aparencia", "Sabor", "Data"
    ]))
    
    # Initialize Anonymizer state
    Anonymizer.initialize_anonymization()
    
    # Create test images directory
    os.makedirs(CONFIG["IMAGES_DIR"], exist_ok=True)
    
    # Create test image
    image_path = os.path.join(CONFIG["IMAGES_DIR"], "participant_1_categoria1.jpg")
    Image.new('RGB', (100, 100), color='red').save(image_path)
    
    # Create code and set name
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    Anonymizer.set_drink_name(code, "Gin Tônica")
    
    # Initialize rendered elements list
    st.session_state.rendered_elements = []
    
    # Test form rendering
    voting_component._render_voting_form("Teste", code)
    
    # Verify form elements are present
    assert "Drink: Gin Tônica" in st.session_state.rendered_elements
    assert "Avaliação" in st.session_state.rendered_elements
    assert "**Originalidade**: Avalie a criatividade e inovação do drink" in st.session_state.rendered_elements
    assert "**Aparência**: Avalie a apresentação visual do drink" in st.session_state.rendered_elements
    assert "**Sabor**: Avalie o sabor e equilíbrio do drink" in st.session_state.rendered_elements
    
    # Cleanup test image
    if os.path.exists(image_path):
        os.remove(image_path)

def test_duplicate_vote_handling(voting_component, mock_session_state, mock_streamlit):
    """Test handling of duplicate votes"""
    # Setup test data
    SessionManager.set("num_participants", 2)
    SessionManager.set("categories", ["Categoria1"])
    SessionManager.set("data", pd.DataFrame(columns=[
        "Nome", "Participante", "Categoria", "Originalidade", 
        "Aparencia", "Sabor", "Data"
    ]))
    
    # Initialize Anonymizer state
    Anonymizer.initialize_anonymization()
    
    # Create test images directory
    os.makedirs(CONFIG["IMAGES_DIR"], exist_ok=True)
    
    # Create test image
    image_path = os.path.join(CONFIG["IMAGES_DIR"], "participant_1_categoria1.jpg")
    Image.new('RGB', (100, 100), color='red').save(image_path)
    
    # Create code and set name
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    Anonymizer.set_drink_name(code, "Gin Tônica")
    
    # Initialize rendered elements list
    st.session_state.rendered_elements = []
    
    # Submit first vote
    voting_component._save_vote("Teste", code, 8, 9, 10)
    
    # Try to submit duplicate vote
    voting_component._save_vote("Teste", code, 8, 9, 10)
    
    # Verify warning message is shown
    assert "Você já votou para o Participante #1 na categoria Categoria1!" in st.session_state.rendered_elements
    
    # Cleanup test image
    if os.path.exists(image_path):
        os.remove(image_path)

def test_results_display(voting_component, mock_session_state, mock_streamlit):
    """Test results display with anonymization"""
    # Setup test data
    SessionManager.set("data", pd.DataFrame(columns=[
        "Nome", "Participante", "Categoria", "Originalidade", 
        "Aparencia", "Sabor", "Data"
    ]))
    
    # Initialize Anonymizer state
    Anonymizer.initialize_anonymization()
    
    # Create test images directory
    os.makedirs(CONFIG["IMAGES_DIR"], exist_ok=True)
    
    # Create test image
    image_path = os.path.join(CONFIG["IMAGES_DIR"], "participant_1_categoria1.jpg")
    Image.new('RGB', (100, 100), color='red').save(image_path)
    
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    Anonymizer.set_drink_name(code, "Gin Tônica")
    
    # Submit some votes
    voting_component._save_vote("Teste1", code, 8, 9, 10)
    voting_component._save_vote("Teste2", code, 7, 8, 9)
    
    # Initialize rendered elements list
    st.session_state.rendered_elements = []
    
    # Test results rendering
    SessionManager.set("results_access", True)
    voting_component._render_results()
    
    # Verify results are displayed correctly
    assert "Resultados por Categoria" in st.session_state.rendered_elements
    assert "Gin Tônica" in st.session_state.rendered_elements
    
    # Cleanup test image
    if os.path.exists(image_path):
        os.remove(image_path)

def test_voting_progress(voting_component, mock_session_state, mock_streamlit):
    """Test voting progress calculation"""
    # Setup test data
    SessionManager.set("num_participants", 2)
    SessionManager.set("categories", ["Categoria1"])
    SessionManager.set("data", pd.DataFrame(columns=[
        "Nome", "Participante", "Categoria", "Originalidade", 
        "Aparencia", "Sabor", "Data"
    ]))
    
    # Initialize Anonymizer state
    Anonymizer.initialize_anonymization()
    
    # Create test images directory
    os.makedirs(CONFIG["IMAGES_DIR"], exist_ok=True)
    
    # Create test image
    image_path = os.path.join(CONFIG["IMAGES_DIR"], "participant_1_categoria1.jpg")
    Image.new('RGB', (100, 100), color='red').save(image_path)
    
    # Create code and set name
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    Anonymizer.set_drink_name(code, "Gin Tônica")
    
    # Initialize rendered elements list
    st.session_state.rendered_elements = []
    
    # Submit a vote
    voting_component._save_vote("Teste", code, 8, 9, 10)
    
    # Calculate expected progress
    total_votes = len(SessionManager.get("data"))
    total_possible_votes = SessionManager.get("num_participants") * len(SessionManager.get("categories"))
    expected_progress = (total_votes / total_possible_votes) * 100
    
    # Verify progress is calculated correctly
    assert voting_component.vote_manager.calculate_progress(
        SessionManager.get("data"),
        "Teste",
        SessionManager.get("categories"),
        SessionManager.get("num_participants")
    ) == expected_progress
    
    # Cleanup test image
    if os.path.exists(image_path):
        os.remove(image_path)

def test_draft_votes(voting_component, mock_session_state, mock_streamlit):
    """Test draft vote functionality"""
    # Setup test data
    SessionManager.set("num_participants", 2)
    SessionManager.set("categories", ["Categoria1"])
    SessionManager.set("data", pd.DataFrame(columns=[
        "Nome", "Participante", "Categoria", "Originalidade", 
        "Aparencia", "Sabor", "Data"
    ]))
    
    # Initialize Anonymizer state
    Anonymizer.initialize_anonymization()
    
    # Create test images directory
    os.makedirs(CONFIG["IMAGES_DIR"], exist_ok=True)
    
    # Create test image
    image_path = os.path.join(CONFIG["IMAGES_DIR"], "participant_1_categoria1.jpg")
    Image.new('RGB', (100, 100), color='red').save(image_path)
    
    # Create code and set name
    code = Anonymizer.get_or_create_code(1, "Categoria1")
    Anonymizer.set_drink_name(code, "Gin Tônica")
    
    # Initialize rendered elements list
    st.session_state.rendered_elements = []
    
    # Test form rendering
    voting_component._render_voting_form("Teste", code)
    
    # Verify form elements are present
    assert "Drink: Gin Tônica" in st.session_state.rendered_elements
    assert "Avaliação" in st.session_state.rendered_elements
    assert "**Originalidade**: Avalie a criatividade e inovação do drink" in st.session_state.rendered_elements
    assert "**Aparência**: Avalie a apresentação visual do drink" in st.session_state.rendered_elements
    assert "**Sabor**: Avalie o sabor e equilíbrio do drink" in st.session_state.rendered_elements
    
    # Cleanup test image
    if os.path.exists(image_path):
        os.remove(image_path) 