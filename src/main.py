import os

import streamlit as st

from config import CONFIG
from frontend.components.admin import AdminComponent
from frontend.components.voting import VotingComponent
from frontend.utils.session_manager import SessionManager


def main():
    """Main application flow"""
    # Page configuration
    st.set_page_config(
        page_title="Copo do Mundo",
        page_icon="🍹",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={"Get Help": None, "Report a bug": None, "About": None},
    )

    # Initialize session state
    SessionManager.initialize_session_state()

    # Create necessary directories (only for local storage)
    if CONFIG.get("STORAGE_BACKEND", "local") == "local":
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
