import os
from datetime import datetime
import pandas as pd
from typing import Any, Optional

from config import CONFIG, COLUMNS, UI_MESSAGES

class DataManager:
    def __init__(self):
        self.data_file = CONFIG["DATA_FILE"]
        self._ensure_data_file_exists()

    def _ensure_data_file_exists(self):
        """Ensure the data file exists with the correct structure"""
        if not os.path.exists(self.data_file):
            # Create empty DataFrame with the correct structure
            df = pd.DataFrame(columns=[
                "Nome", "Participante", "Categoria", "Originalidade", 
                "Aparencia", "Sabor", "Data"
            ])
            df.to_csv(self.data_file, index=False)

    def load_data(self) -> pd.DataFrame:
        """Load voting data from CSV file"""
        try:
            df = pd.read_csv(self.data_file)
            # Convert Data column to datetime
            df["Data"] = pd.to_datetime(df["Data"])
            return df
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return pd.DataFrame()

    def save_data(self, data: pd.DataFrame) -> bool:
        """Save voting data to CSV file"""
        try:
            data.to_csv(self.data_file, index=False)
            return True
        except Exception as e:
            print(f"Error saving data: {str(e)}")
            return False

    def get_total_votes(self, data: pd.DataFrame) -> int:
        """Get total number of votes"""
        return len(data)

    def calculate_results(self, data: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        """Calculate average scores and winners for each category"""
        try:
            # Group by participant and category, calculate mean scores
            df_avg = data.groupby(["Participante", "Categoria"])[
                ["Originalidade", "Aparencia", "Sabor"]
            ].mean().round(2)

            # Calculate total score for each participant in each category
            df_avg["Total"] = df_avg[["Originalidade", "Aparencia", "Sabor"]].sum(axis=1)

            # Find winners for each category
            winners = {}
            for categoria in data["Categoria"].unique():
                # Get the participant with highest total score in this category
                category_data = df_avg.xs(categoria, level="Categoria")
                winner_idx = category_data["Total"].idxmax()
                winners[categoria] = {
                    "participant": winner_idx,
                    "score": category_data.loc[winner_idx, "Total"]
                }

            return df_avg, winners

        except Exception as e:
            print(f"Error calculating results: {str(e)}")
            return pd.DataFrame(), {}

    def get_participant_stats(self, data: pd.DataFrame, participant: int) -> dict:
        """Get statistics for a specific participant"""
        try:
            participant_data = data[data["Participante"] == participant]
            if participant_data.empty:
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

            return stats

        except Exception as e:
            print(f"Error getting participant stats: {str(e)}")
            return {} 