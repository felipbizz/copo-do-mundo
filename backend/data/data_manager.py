import os
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union
import pandas as pd
from pathlib import Path

from config import CONFIG, COLUMNS, UI_MESSAGES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManagerError(Exception):
    """Base exception for DataManager errors."""
    pass

class DataManager:
    """Manages the storage and retrieval of competition voting data.
    
    This class handles all data operations including loading, saving, and analyzing
    voting data for the competition. It ensures data integrity and provides methods
    for calculating results and statistics.
    """
    
    def __init__(self, data_file: Optional[str] = None):
        """Initialize the DataManager.
        
        Args:
            data_file (Optional[str]): Path to the data file. If None, uses CONFIG["DATA_FILE"].
        """
        self.data_file = Path(data_file or CONFIG["DATA_FILE"])
        self._ensure_data_file_exists()
    
    def _ensure_data_file_exists(self) -> None:
        """Ensure the data file exists with the correct structure.
        
        Raises:
            DataManagerError: If there's an error creating the data file.
        """
        try:
            if not self.data_file.exists():
                # Create empty DataFrame with the correct structure
                df = pd.DataFrame(columns=[
                    "Nome", "Participante", "Categoria", "Originalidade", 
                    "Aparencia", "Sabor", "Data"
                ])
                df.to_csv(self.data_file, index=False)
                logger.info(f"Created new data file at {self.data_file}")
        except Exception as e:
            raise DataManagerError(f"Failed to create data file: {str(e)}")
    
    def load_data(self) -> pd.DataFrame:
        """Load voting data from CSV file.
        
        Returns:
            pd.DataFrame: The loaded voting data.
            
        Raises:
            DataManagerError: If there's an error loading the data.
        """
        try:
            df = pd.read_csv(self.data_file)
            # Convert Data column to datetime
            df["Data"] = pd.to_datetime(df["Data"])
            logger.info(f"Successfully loaded {len(df)} votes from {self.data_file}")
            return df
        except Exception as e:
            raise DataManagerError(f"Error loading data: {str(e)}")
    
    def save_data(self, data: pd.DataFrame) -> bool:
        """Save voting data to CSV file.
        
        Args:
            data (pd.DataFrame): The voting data to save.
            
        Returns:
            bool: True if save was successful, False otherwise.
            
        Raises:
            DataManagerError: If there's an error saving the data.
        """
        try:
            data.to_csv(self.data_file, index=False)
            logger.info(f"Successfully saved {len(data)} votes to {self.data_file}")
            return True
        except Exception as e:
            raise DataManagerError(f"Error saving data: {str(e)}")
    
    def get_total_votes(self, data: pd.DataFrame) -> int:
        """Get total number of votes.
        
        Args:
            data (pd.DataFrame): The voting data to analyze.
            
        Returns:
            int: Total number of votes.
        """
        return len(data)
    
    def calculate_results(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Union[str, float]]]]:
        """Calculate average scores and winners for each category.
        
        Args:
            data (pd.DataFrame): The voting data to analyze.
            
        Returns:
            Tuple[pd.DataFrame, Dict]: A tuple containing:
                - DataFrame with average scores by category and participant
                - Dictionary of winners by category
                
        Raises:
            DataManagerError: If there's an error calculating results.
        """
        try:
            # Group by participant and category, calculate mean scores
            df_avg = data.groupby(["Participante", "Categoria"])[
                ["Originalidade", "Aparencia", "Sabor"]
            ].mean().round(2)

            # Calculate total score for each participant in each category
            df_avg["Total"] = df_avg[["Originalidade", "Aparencia", "Sabor"]].sum(axis=1)

            # Find winners for each category
            winners: Dict[str, Dict[str, Union[str, float]]] = {}
            for categoria in data["Categoria"].unique():
                # Get the participant with highest total score in this category
                category_data = df_avg.xs(categoria, level="Categoria")
                winner_idx = category_data["Total"].idxmax()
                winners[categoria] = {
                    "participant": winner_idx,
                    "score": category_data.loc[winner_idx, "Total"]
                }

            logger.info(f"Successfully calculated results for {len(winners)} categories")
            return df_avg, winners

        except Exception as e:
            raise DataManagerError(f"Error calculating results: {str(e)}")
    
    def get_participant_stats(self, data: pd.DataFrame, participant: int) -> Dict[str, Any]:
        """Get statistics for a specific participant.
        
        Args:
            data (pd.DataFrame): The voting data to analyze.
            participant (int): The participant ID to get stats for.
            
        Returns:
            Dict[str, Any]: Dictionary containing participant statistics including:
                - total_votes: Number of votes received
                - average_scores: Average scores for each criterion
                - categories: Statistics per category
                
        Raises:
            DataManagerError: If there's an error calculating participant stats.
        """
        try:
            participant_data = data[data["Participante"] == participant]
            if participant_data.empty:
                logger.warning(f"No data found for participant {participant}")
                return {}

            stats = {
                "total_votes": len(participant_data),
                "average_scores": {
                    "Originalidade": participant_data["Originalidade"].mean(),
                    "Aparencia": participant_data["Aparencia"].mean(),
                    "Sabor": participant_data["Sabor"].mean()
                },
                "categories": {}
            }

            # Calculate stats per category
            for categoria in data["Categoria"].unique():
                cat_data = participant_data[participant_data["Categoria"] == categoria]
                if not cat_data.empty:
                    stats["categories"][categoria] = {
                        "votes": len(cat_data),
                        "average_scores": {
                            "Originalidade": cat_data["Originalidade"].mean(),
                            "Aparencia": cat_data["Aparencia"].mean(),
                            "Sabor": cat_data["Sabor"].mean()
                        }
                    }

            logger.info(f"Successfully calculated stats for participant {participant}")
            return stats

        except Exception as e:
            raise DataManagerError(f"Error getting participant stats: {str(e)}") 