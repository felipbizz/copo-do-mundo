import logging
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from backend.data.data_manager import DataManager
from config import CONFIG

logger = logging.getLogger(__name__)


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

        # Data refresh tracking
        if "last_data_load" not in st.session_state:
            st.session_state.last_data_load = datetime.now()

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
    def get_last_data_load() -> datetime:
        """Get the timestamp of the last data load."""
        return st.session_state.get("last_data_load", datetime.now())

    @staticmethod
    def update_last_data_load() -> None:
        """Update the timestamp of the last data load."""
        st.session_state.last_data_load = datetime.now()

    @staticmethod
    def refresh_data_incremental(data_manager: DataManager) -> pd.DataFrame:
        """Refresh data by loading only new votes since last load.

        Args:
            data_manager: DataManager instance to use for loading.

        Returns:
            pd.DataFrame: New votes loaded since last refresh.
        """
        last_load = SessionManager.get_last_data_load()
        try:
            new_data = data_manager.load_data_since(last_load)
            if not new_data.empty:
                # Merge with existing data
                current_data = SessionManager.get("data", pd.DataFrame())
                if current_data.empty:
                    SessionManager.set("data", new_data)
                else:
                    # Combine and remove duplicates
                    combined = pd.concat([current_data, new_data], ignore_index=True)
                    # Remove duplicates based on all columns except Data (in case of re-votes)
                    combined = combined.drop_duplicates(
                        subset=["Nome", "Participante", "Categoria"], keep="last"
                    )
                    SessionManager.set("data", combined)
                SessionManager.update_last_data_load()
                return new_data
            return pd.DataFrame()
        except Exception as e:
            # If incremental load fails, fall back to full load
            logger.warning(f"Incremental load failed, falling back to full load: {str(e)}")
            full_data = data_manager.load_data()
            SessionManager.set("data", full_data)
            SessionManager.update_last_data_load()
            return full_data
