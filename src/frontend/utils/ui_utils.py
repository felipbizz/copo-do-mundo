import streamlit as st
from PIL import Image


class UIUtils:
    @staticmethod
    def show_error_message(message: str) -> None:
        """Show error message"""
        st.error(message)

    @staticmethod
    def show_success_message(message: str) -> None:
        """Show success message"""
        st.success(message)

    @staticmethod
    def show_info_message(message: str) -> None:
        """Show info message"""
        st.info(message)

    @staticmethod
    def show_warning_message(message: str) -> None:
        """Show warning message"""
        st.warning(message)

    @staticmethod
    def display_image(image: Image.Image | None, caption: str | None = None) -> None:
        """Display image with optional caption"""
        if image:
            st.image(image, caption=caption, use_container_width=False)
        else:
            UIUtils.show_info_message("Foto não disponível")

    @staticmethod
    def create_columns(ratios: list[int]) -> list:
        """Create columns with specified ratios"""
        return st.columns(ratios)

    @staticmethod
    def create_tabs(tab_names: list[str]) -> list:
        """Create tabs with specified names"""
        return st.tabs(tab_names)

    @staticmethod
    def create_expander(title: str):
        """Create an expander with specified title"""
        return st.expander(title)

    @staticmethod
    def create_spinner(message: str):
        """Create a spinner with specified message"""
        return st.spinner(message)
