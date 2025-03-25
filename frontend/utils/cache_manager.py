import streamlit as st
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import pandas as pd
import hashlib

class CacheManager:
    """Manages caching for expensive operations"""
    
    CACHE_DURATION = timedelta(minutes=5)
    
    @staticmethod
    def initialize_cache():
        """Initialize cache-related session states"""
        if "cache_timestamp" not in st.session_state:
            st.session_state.cache_timestamp = datetime.now()
        if "cached_data" not in st.session_state:
            st.session_state.cached_data = {}
    
    @staticmethod
    def is_cache_valid() -> bool:
        """Check if the current cache is still valid"""
        if "cache_timestamp" not in st.session_state:
            return False
        return datetime.now() - st.session_state.cache_timestamp < CacheManager.CACHE_DURATION
    
    @staticmethod
    def update_cache_timestamp():
        """Update the cache timestamp"""
        st.session_state.cache_timestamp = datetime.now()
    
    @staticmethod
    def get_cached(key: str) -> Optional[Any]:
        """Get a value from cache"""
        if not CacheManager.is_cache_valid():
            return None
        return st.session_state.cached_data.get(key)
    
    @staticmethod
    def set_cached(key: str, value: Any):
        """Set a value in cache"""
        CacheManager.update_cache_timestamp()
        st.session_state.cached_data[key] = value
    
    @staticmethod
    def clear_cache():
        """Clear all cached data"""
        st.session_state.cached_data = {}
        CacheManager.update_cache_timestamp()
    
    @staticmethod
    def _get_dataframe_hash(df: pd.DataFrame) -> str:
        """Generate a hash for a DataFrame"""
        # Convert DataFrame to string representation
        df_str = df.to_string()
        # Create hash
        return hashlib.md5(df_str.encode()).hexdigest()
    
    @staticmethod
    def calculate_results(data: pd.DataFrame) -> tuple[pd.DataFrame, Dict]:
        """Calculate competition results with caching"""
        # Generate cache key from DataFrame hash
        cache_key = f"results_{CacheManager._get_dataframe_hash(data)}"
        
        # Check if we have cached results
        cached_results = CacheManager.get_cached(cache_key)
        if cached_results is not None:
            return cached_results
        
        # Calculate results
        df_avg = data.groupby(['Categoria', 'Participante']).agg({
            'Originalidade': 'mean',
            'Aparencia': 'mean',
            'Sabor': 'mean'
        }).round(2)
        
        df_avg['Pontuação Total'] = df_avg[['Originalidade', 'Aparencia', 'Sabor']].sum(axis=1)
        
        # Calculate winners by category
        winners = {}
        for cat in df_avg.index.get_level_values('Categoria').unique():
            cat_scores = df_avg.loc[cat]
            winner_idx = cat_scores['Pontuação Total'].idxmax()
            winners[cat] = {
                'participant': winner_idx,
                'score': cat_scores.loc[winner_idx, 'Pontuação Total']
            }
        
        # Calculate overall winner
        overall_scores = df_avg.groupby('Participante')['Pontuação Total'].mean()
        overall_winner_idx = overall_scores.idxmax()
        winners['Geral'] = {
            'participant': overall_winner_idx,
            'score': overall_scores[overall_winner_idx]
        }
        
        results = (df_avg, winners)
        CacheManager.set_cached(cache_key, results)
        return results
    
    @staticmethod
    def get_participant_name(participant_id: int, participant_names: Dict) -> str:
        """Get participant name with caching"""
        cache_key = f"participant_name_{participant_id}"
        cached_name = CacheManager.get_cached(cache_key)
        if cached_name is not None:
            return cached_name
            
        name = participant_names.get(participant_id, f"Participante {participant_id}")
        CacheManager.set_cached(cache_key, name)
        return name
    
    @staticmethod
    def invalidate_results_cache():
        """Invalidate the results cache"""
        CacheManager.clear_cache() 