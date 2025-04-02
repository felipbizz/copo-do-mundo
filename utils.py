import os
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
from PIL import Image

from config import COLUMNS, CONFIG, UI_MESSAGES


@st.cache_data(ttl=CONFIG["CACHE_TTL"])
def safe_load_data() -> pd.DataFrame:
    """Safely load data with error handling and caching"""
    try:
        if os.path.exists(CONFIG["DATA_FILE"]):
            return pd.read_csv(CONFIG["DATA_FILE"])
    except Exception as e:
        show_error_message(UI_MESSAGES["ERROR_LOAD_DATA"].format(str(e)))
    return pd.DataFrame(columns=COLUMNS)


def save_data(df: pd.DataFrame) -> bool:
    """Safely save data with error handling"""
    try:
        df.to_csv(CONFIG["DATA_FILE"], index=False)
        return True
    except Exception:
        show_error_message(UI_MESSAGES["ERROR_SAVE_VOTE"])
        return False


@st.cache_data(ttl=CONFIG["IMAGE_CACHE_TTL"])
def load_and_resize_image(image_path: str, width: int | None = None) -> Image.Image | None:
    """Load and resize image with caching"""
    try:
        image = Image.open(image_path)
        if width:
            ratio = width / image.size[0]
            height = int(image.size[1] * ratio)
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        return image
    except Exception as e:
        show_error_message(UI_MESSAGES["ERROR_LOAD_IMAGE"].format(str(e)))
        return None


def optimize_image(image: Image.Image) -> Image.Image | None:
    """Optimize image with better error handling and validation"""
    try:
        if not image:
            return None

        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Calculate aspect ratio for resizing
        width, height = image.size
        max_width, max_height = CONFIG["IMAGE_MAX_SIZE"]

        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image
    except Exception as e:
        show_error_message(UI_MESSAGES["ERROR_OPTIMIZE_IMAGE"].format(str(e)))
        return None


def validate_vote_data(name: str, categoria: str, drink_number: str) -> tuple[bool, str]:
    """Validate vote data"""
    if not name.strip():
        return False, UI_MESSAGES["ERROR_NAME_EMPTY"]
    if not categoria:
        return False, UI_MESSAGES["ERROR_CATEGORY_EMPTY"]
    if not drink_number:
        return False, UI_MESSAGES["ERROR_DRINK_EMPTY"]
    try:
        drink_num = int(drink_number)
        if drink_num < 1 or drink_num > st.session_state.num_drinks:
            return False, UI_MESSAGES["ERROR_DRINK_INVALID"]
    except ValueError:
        return False, UI_MESSAGES["ERROR_DRINK_INVALID"]
    return True, ""


def check_rate_limit(user_name: str) -> bool:
    """Prevent too many votes in short time"""
    now = datetime.now()
    if "last_votes" not in st.session_state:
        st.session_state.last_votes = {}

    if user_name in st.session_state.last_votes:
        last_vote_time = st.session_state.last_votes[user_name]
        if now - last_vote_time < CONFIG["RATE_LIMIT"]:
            return False

    st.session_state.last_votes[user_name] = now
    return True


@st.cache_data(ttl=CONFIG["CACHE_TTL"])
def calculate_results(data: pd.DataFrame) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    """Calculate and cache competition results"""
    if data.empty:
        return None, {}

    try:
        df_avg = data.groupby(["Categoria", "Drink"])[
            ["Originalidade", "Aparencia", "Sabor"]
        ].mean()
        df_avg["Pontuação Total"] = df_avg.sum(axis=1)
        df_avg = df_avg.round(2)

        # Calculate winners
        winners = {}
        for cat in df_avg.index.get_level_values("Categoria").unique():
            cat_scores = df_avg.xs(cat, level="Categoria")
            winner = cat_scores["Pontuação Total"].idxmax()
            score = cat_scores.loc[winner, "Pontuação Total"]
            winners[cat] = {"drink": winner, "score": score}

        return df_avg, winners
    except Exception as e:
        show_error_message(f"Erro ao calcular resultados: {str(e)}")
        return None, {}


def initialize_session_state():
    """Initialize all session state variables in one place"""
    if "data" not in st.session_state:
        st.session_state.data = safe_load_data()
    if "num_drinks" not in st.session_state:
        st.session_state.num_drinks = CONFIG["DEFAULT_NUM_DRINKS"]
    if "categories" not in st.session_state:
        st.session_state.categories = CONFIG["DEFAULT_CATEGORIES"]
    if "last_upload_status" not in st.session_state:
        st.session_state.last_upload_status = None
    if "cache_timestamp" not in st.session_state:
        st.session_state.cache_timestamp = datetime.now()
    if "last_votes" not in st.session_state:
        st.session_state.last_votes = {}


# UI Helper functions
def show_loading_message():
    """Show loading message while processing"""
    return st.spinner("Processando...")


def show_error_message(message: str):
    """Standardized error message display"""
    st.error(f"❌ {message}")


def show_success_message(message: str):
    """Standardized success message display"""
    st.success(f"✅ {message}")


def show_info_message(message: str):
    """Standardized info message display"""
    st.info(f"ℹ️ {message}")


def check_duplicate_vote(name: str, categoria: str, drink_number: str) -> bool:
    """Check if a vote already exists for the given name, category and drink"""
    if st.session_state.data.empty:
        return False
    return not st.session_state.data[
        (st.session_state.data["Nome"] == name)
        & (st.session_state.data["Categoria"] == categoria)
        & (st.session_state.data["Drink"] == int(drink_number))
    ].empty


def get_missing_votes(name: str) -> list:
    """Get list of drinks with photos that haven't been voted by the given name"""
    missing_votes = []
    for categoria in st.session_state.categories:
        for drink in range(1, st.session_state.num_drinks + 1):
            image_path = os.path.join(CONFIG["IMAGES_DIR"], f"drink_{drink}.jpg")
            if os.path.exists(image_path):
                if (
                    st.session_state.data.empty
                    or st.session_state.data[
                        (st.session_state.data["Nome"] == name)
                        & (st.session_state.data["Categoria"] == categoria)
                        & (st.session_state.data["Drink"] == drink)
                    ].empty
                ):
                    missing_votes.append((categoria, drink))
    return missing_votes


def remove_duplicate_vote(name: str, categoria: str, drink_number: str) -> None:
    """Remove a duplicate vote"""
    st.session_state.data = st.session_state.data[
        ~(
            (st.session_state.data["Nome"] == name)
            & (st.session_state.data["Categoria"] == categoria)
            & (st.session_state.data["Drink"] == int(drink_number))
        )
    ]
    # Save the updated data to CSV file
    save_data(st.session_state.data)
