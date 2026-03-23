import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for expensive operations in the application.

    This class provides a centralized caching mechanism using Streamlit's session state.
    It handles caching of competition results, participant names, and other expensive operations.
    The cache has a configurable duration and can be invalidated when needed.
    """

    CACHE_DURATION: timedelta = timedelta(minutes=5)

    @staticmethod
    def initialize_cache() -> None:
        """Initialize cache-related session states.

        Sets up the initial cache timestamp and cached data dictionary in Streamlit's session state.
        This should be called at the start of the application.
        """
        if "cache_timestamp" not in st.session_state:
            st.session_state.cache_timestamp = datetime.now()
        if "cached_data" not in st.session_state:
            st.session_state.cached_data = {}

    @staticmethod
    def is_cache_valid() -> bool:
        """Check if the current cache is still valid.

        Returns:
            bool: True if the cache exists and hasn't expired, False otherwise.
        """
        if "cache_timestamp" not in st.session_state:
            return False
        return datetime.now() - st.session_state.cache_timestamp < CacheManager.CACHE_DURATION

    @staticmethod
    def update_cache_timestamp() -> None:
        """Update the cache timestamp to the current time."""
        st.session_state.cache_timestamp = datetime.now()

    @staticmethod
    def get_cached(key: str) -> Any | None:
        """Get a value from cache.

        Args:
            key (str): The cache key to look up.

        Returns:
            Optional[Any]: The cached value if it exists and is valid, None otherwise.
        """
        if not CacheManager.is_cache_valid():
            return None
        return st.session_state.cached_data.get(key)

    @staticmethod
    def set_cached(key: str, value: Any) -> None:
        """Set a value in cache.

        Args:
            key (str): The cache key to store the value under.
            value (Any): The value to cache.
        """
        CacheManager.update_cache_timestamp()
        st.session_state.cached_data[key] = value

    @staticmethod
    def clear_cache() -> None:
        """Clear all cached data and update the cache timestamp."""
        st.session_state.cached_data = {}
        CacheManager.update_cache_timestamp()

    @staticmethod
    def _get_dataframe_hash(df: pd.DataFrame) -> str:
        """Generate a hash for a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to generate a hash for.

        Returns:
            str: MD5 hash of the DataFrame's string representation.
        """
        df_str = df.to_string()
        return hashlib.md5(df_str.encode()).hexdigest()

    @staticmethod
    def calculate_results(
        data: pd.DataFrame,
    ) -> tuple[pd.DataFrame, dict[str, dict[str, str | float]]]:
        """Calculate competition results with caching.

        Args:
            data (pd.DataFrame): DataFrame containing competition data with columns:
                ['Categoria', 'Participante', 'Originalidade', 'Aparencia', 'Sabor']

        Returns:
            Tuple[pd.DataFrame, Dict]: A tuple containing:
                - DataFrame with average scores by category and participant
                - Dictionary of winners by category and overall
        """
        # Generate cache key from DataFrame hash
        cache_key = f"results_{CacheManager._get_dataframe_hash(data)}"

        # Check if we have cached results
        cached_results = CacheManager.get_cached(cache_key)
        if cached_results is not None:
            return cached_results

        # Calculate results
        df_avg = (
            data.groupby(["Categoria", "Participante"])
            .agg({"Originalidade": "mean", "Aparencia": "mean", "Sabor": "mean"})
            .round(2)
        )

        df_avg["Pontuação Total"] = df_avg[["Originalidade", "Aparencia", "Sabor"]].sum(axis=1)

        # Calculate winners by category
        winners: dict[str, dict[str, str | float]] = {}
        for cat in df_avg.index.get_level_values("Categoria").unique():
            cat_scores = df_avg.loc[cat]
            winner_idx = cat_scores["Pontuação Total"].idxmax()
            winners[cat] = {
                "participant": winner_idx,
                "score": cat_scores.loc[winner_idx, "Pontuação Total"],
            }

        # Calculate overall winner
        overall_scores = df_avg.groupby("Participante")["Pontuação Total"].mean()
        overall_winner_idx = overall_scores.idxmax()
        winners["Geral"] = {
            "participant": overall_winner_idx,
            "score": overall_scores[overall_winner_idx],
        }

        results = (df_avg, winners)
        CacheManager.set_cached(cache_key, results)
        return results

    @staticmethod
    def get_participant_name(participant_id: int, participant_names: dict[int, str]) -> str:
        """Get participant name with caching.

        Args:
            participant_id (int): The ID of the participant.
            participant_names (Dict[int, str]): Dictionary mapping participant IDs to names.

        Returns:
            str: The participant's name, or a default name if not found.
        """
        cache_key = f"participant_name_{participant_id}"
        cached_name = CacheManager.get_cached(cache_key)
        if cached_name is not None:
            return cached_name

        name = participant_names.get(participant_id, f"Participante {participant_id}")
        CacheManager.set_cached(cache_key, name)
        return name

    @staticmethod
    def invalidate_results_cache() -> None:
        """Invalidate only the results cache, keeping other cached data."""
        if "cached_data" not in st.session_state:
            return

        # Remove only results-related cache entries
        keys_to_remove = [
            key for key in st.session_state.cached_data if key.startswith("results_")
        ]
        for key in keys_to_remove:
            del st.session_state.cached_data[key]

        if keys_to_remove:
            logger.info(f"Invalidated {len(keys_to_remove)} results cache entries")

    @staticmethod
    def invalidate_category_cache(categoria: str) -> None:
        """Invalidate cache entries for a specific category.

        Args:
            categoria: The category to invalidate cache for.
        """
        if "cached_data" not in st.session_state:
            return

        # Remove cache entries related to this category
        keys_to_remove = [
            key
            for key in st.session_state.cached_data
            if f"_cat_{categoria}_" in key or key.endswith(f"_{categoria}")
        ]
        for key in keys_to_remove:
            del st.session_state.cached_data[key]

    @staticmethod
    def invalidate_participant_cache(participant: str | int) -> None:
        """Invalidate cache entries for a specific participant.

        Args:
            participant: The participant ID to invalidate cache for.
        """
        if "cached_data" not in st.session_state:
            return

        participant_str = str(participant)
        # Remove cache entries related to this participant
        keys_to_remove = [
            key
            for key in st.session_state.cached_data
            if f"_participant_{participant_str}_" in key
            or key.endswith(f"_{participant_str}")
            or key == f"participant_name_{participant_str}"
        ]
        for key in keys_to_remove:
            del st.session_state.cached_data[key]
