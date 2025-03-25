import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

from config import CONFIG
from backend.data.data_manager import DataManager

class SessionManager:
    """Centralized session state management"""
    
    @staticmethod
    def initialize_session_state():
        """Initialize all session state variables"""
        # Data management
        if "data" not in st.session_state:
            data_manager = DataManager()
            st.session_state.data = data_manager.load_data()
            if st.session_state.data is None:
                st.session_state.data = pd.DataFrame()
        
        # Competition settings
        if "categories" not in st.session_state:
            st.session_state.categories = CONFIG["CATEGORIES"]
        if "num_participants" not in st.session_state:
            st.session_state.num_participants = CONFIG["NUM_PARTICIPANTS"]
        if "participant_names" not in st.session_state:
            st.session_state.participant_names = CONFIG["PARTICIPANT_NAMES"]
        
        # Voting state
        if "last_votes" not in st.session_state:
            st.session_state.last_votes = {}
        if "draft_votes" not in st.session_state:
            st.session_state.draft_votes = []
        if "confirm_vote" not in st.session_state:
            st.session_state.confirm_vote = False
        
        # Selection state
        if "selected_participant" not in st.session_state:
            st.session_state.selected_participant = 1
        if "selected_category" not in st.session_state:
            st.session_state.selected_category = CONFIG["CATEGORIES"][0]
        
        # Access control
        if "is_admin" not in st.session_state:
            st.session_state.is_admin = False
        if "results_access" not in st.session_state:
            st.session_state.results_access = False
        
        # User state
        if "juror_name" not in st.session_state:
            st.session_state.juror_name = ""
        if "has_valid_juror" not in st.session_state:
            st.session_state.has_valid_juror = False
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get a session state value with a default"""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set a session state value"""
        st.session_state[key] = value
    
    @staticmethod
    def reset_voting_state() -> None:
        """Reset voting-related session states"""
        st.session_state.draft_votes = []
        st.session_state.confirm_vote = False
        st.session_state.selected_participant = 1
        st.session_state.selected_category = CONFIG["CATEGORIES"][0]
    
    @staticmethod
    def reset_access_state() -> None:
        """Reset access-related session states"""
        st.session_state.is_admin = False
        st.session_state.results_access = False
    
    @staticmethod
    def update_last_vote(name: str) -> None:
        """Update the last vote timestamp for a user"""
        st.session_state.last_votes[name] = datetime.now()
    
    @staticmethod
    def can_vote(name: str) -> bool:
        """Check if a user can vote based on rate limit"""
        if name not in st.session_state.last_votes:
            return True
        
        time_since_last_vote = datetime.now() - st.session_state.last_votes[name]
        return time_since_last_vote.total_seconds() >= CONFIG["RATE_LIMIT"]
    
    @staticmethod
    def clear_juror_name() -> None:
        """Clear juror name and related states"""
        st.session_state.juror_name = ""
        st.session_state.has_valid_juror = False
    
    @staticmethod
    def set_juror_name(name: str) -> None:
        """Set juror name and validate it"""
        st.session_state.juror_name = name.strip()
        st.session_state.has_valid_juror = bool(name.strip()) 