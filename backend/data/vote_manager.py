from datetime import datetime
import pandas as pd
from typing import List, Tuple

from config import CONFIG

class VoteManager:
    def create_vote(
        self, name: str, categoria: str, participant: str, 
        originalidade: int, aparencia: int, sabor: int
    ) -> pd.DataFrame:
        """Create a new vote entry"""
        return pd.DataFrame([{
            "Nome": name,
            "Participante": participant,
            "Categoria": categoria,
            "Originalidade": originalidade,
            "Aparencia": aparencia,
            "Sabor": sabor,
            "Data": datetime.now()
        }])

    def check_duplicate_vote(
        self, data: pd.DataFrame, name: str, 
        categoria: str, participant: str
    ) -> bool:
        """Check if a vote already exists for this participant and category"""
        return not data[
            (data["Nome"] == name) & 
            (data["Categoria"] == categoria) & 
            (data["Participante"] == participant)
        ].empty

    def remove_duplicate_vote(
        self, data: pd.DataFrame, name: str, 
        categoria: str, participant: str
    ) -> pd.DataFrame:
        """Remove a duplicate vote"""
        # Find all matching votes
        mask = (
            (data["Nome"] == name) & 
            (data["Categoria"] == categoria) & 
            (data["Participante"] == participant)
        )
        
        # Get the first occurrence
        first_occurrence = data[mask].iloc[0:1]
        
        # Get all non-matching votes
        non_matching = data[~mask]
        
        # Combine first occurrence with non-matching votes
        return pd.concat([first_occurrence, non_matching], ignore_index=True)

    def get_missing_votes(
        self, data: pd.DataFrame, name: str, 
        categories: list, num_participants: int
    ) -> list:
        """Get list of missing votes for a juror"""
        missing_votes = []
        
        # Get all votes for this juror
        juror_votes = data[data["Nome"] == name]
        
        # Check each category and participant combination
        for categoria in categories:
            for participant in range(1, num_participants + 1):
                # Check if this combination exists in juror's votes
                if juror_votes[
                    (juror_votes["Categoria"] == categoria) & 
                    (juror_votes["Participante"] == str(participant))
                ].empty:
                    missing_votes.append((categoria, participant))
        
        return missing_votes 