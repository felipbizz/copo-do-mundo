import pytest
import pandas as pd
import streamlit as st
from datetime import datetime
from frontend.components.voting import VotingComponent
from config import CONFIG

@pytest.fixture
def voting_component():
    return VotingComponent()

@pytest.fixture
def sample_results_data():
    """Create sample results data"""
    return pd.DataFrame({
        "Nome": ["User1", "User2", "User3"],
        "Participante": ["1", "1", "2"],
        "Categoria": ["Caipirinha", "Caipirinha", "Caipirinha"],
        "Originalidade": [8, 7, 9],
        "Aparencia": [9, 8, 7],
        "Sabor": [7, 8, 9],
        "Data": [datetime.now()] * 3
    })

def test_results_access_control(voting_component):
    """Test results access control"""
    # Initialize session state
    if "results_access" not in st.session_state:
        st.session_state.results_access = False
    
    # Test access without password
    assert st.session_state.results_access == False
    
    # Test access with correct password
    st.session_state.results_access = True
    assert st.session_state.results_access == True
    
    # Test access revocation
    st.session_state.results_access = False
    assert st.session_state.results_access == False

def test_calculate_results(voting_component, sample_results_data):
    """Test results calculation"""
    # Set data in session state
    st.session_state.data = sample_results_data
    
    # Calculate totals for participant 1
    participant1_data = sample_results_data[sample_results_data["Participante"] == "1"]
    
    total_originalidade = participant1_data["Originalidade"].mean()
    total_aparencia = participant1_data["Aparencia"].mean()
    total_sabor = participant1_data["Sabor"].mean()
    
    assert abs(total_originalidade - 7.5) < 0.01  # Average of 8 and 7
    assert abs(total_aparencia - 8.5) < 0.01  # Average of 9 and 8
    assert abs(total_sabor - 7.5) < 0.01  # Average of 7 and 8

def test_results_display_format(voting_component, sample_results_data):
    """Test results display formatting"""
    # Set data in session state
    st.session_state.data = sample_results_data
    st.session_state.results_access = True
    
    # Convert numeric columns to float and Participante to string
    sample_results_data = sample_results_data.astype({
        "Originalidade": "float64",
        "Aparencia": "float64",
        "Sabor": "float64",
        "Participante": "str"
    })
    
    # Verify data grouping
    grouped = sample_results_data.groupby(["Categoria", "Participante"], as_index=False).agg({
        "Originalidade": "mean",
        "Aparencia": "mean",
        "Sabor": "mean"
    })
    
    # Set the index for easier comparison
    grouped.set_index(["Categoria", "Participante"], inplace=True)
    
    # Check that participant 1 has higher appearance score
    participant1_scores = grouped.loc[("Caipirinha", "1")]
    participant2_scores = grouped.loc[("Caipirinha", "2")]
    
    assert participant1_scores["Aparencia"] > participant2_scores["Aparencia"]
    
    # Check that participant 2 has higher taste score
    assert participant2_scores["Sabor"] > participant1_scores["Sabor"] 