from frontend.utils.cache_manager import CacheManager

def main():
    """Main application entry point."""
    # Initialize cache
    CacheManager.initialize_cache()
    
    # Set page config
    st.set_page_config(
        page_title="Copo do Mundo",
        page_icon="🍹",
        layout="wide"
    )
    