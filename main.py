import os
import streamlit as st
from datetime import datetime

from backend.data.data_manager import DataManager
from config import CONFIG
from frontend.components.admin import AdminComponent
from frontend.components.voting import VotingComponent

def initialize_session_state():
    """Initialize session state variables"""
    if "data" not in st.session_state:
        data_manager = DataManager()
        st.session_state.data = data_manager.load_data()
    
    if "categories" not in st.session_state:
        st.session_state.categories = CONFIG["CATEGORIES"]
    
    if "num_participants" not in st.session_state:
        st.session_state.num_participants = CONFIG["NUM_PARTICIPANTS"]
    
    if "participant_names" not in st.session_state:
        st.session_state.participant_names = CONFIG["PARTICIPANT_NAMES"]
    
    if "last_votes" not in st.session_state:
        st.session_state.last_votes = {}
    
    if "results_access" not in st.session_state:
        st.session_state.results_access = False
    
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    
    if "draft_votes" not in st.session_state:
        st.session_state.draft_votes = []
    
    if "selected_participant" not in st.session_state:
        st.session_state.selected_participant = 1
    
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = CONFIG["CATEGORIES"][0]
    
    if "confirm_vote" not in st.session_state:
        st.session_state.confirm_vote = False

def main():
    """Main application flow"""
    # Page configuration
    st.set_page_config(
        page_title="Copo do Mundo",
        page_icon="🍹",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )

    # Initialize session state
    initialize_session_state()

    # Create necessary directories
    os.makedirs(CONFIG["IMAGES_DIR"], exist_ok=True)

    # Initialize components
    voting = VotingComponent()
    admin = AdminComponent()

    # Render admin in sidebar
    with st.sidebar:
        admin.render()

    # Render main voting component
    voting.render()


if __name__ == "__main__":
    main()
