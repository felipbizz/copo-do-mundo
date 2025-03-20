import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Tuple

from config import CONFIG, UI_MESSAGES

class Validators:
    def validate_vote_data(
        self, name: str, categoria: str, participant: str, num_participants: int
    ) -> tuple[bool, str]:
        """Validate vote data"""
        if not name.strip():
            return False, "Nome do jurado é obrigatório"
        
        if not categoria:
            return False, "Categoria é obrigatória"
        
        try:
            participant_num = int(participant)
            if participant_num < 1 or participant_num > num_participants:
                return False, f"Participante deve estar entre 1 e {num_participants}"
        except ValueError:
            return False, "Participante deve ser um número válido"
        
        return True, ""

    def validate_results_password(self, password: str) -> bool:
        """Validate results password"""
        is_valid = password == CONFIG["RESULTS_PASSWORD"]
        if not is_valid and "results_access" in st.session_state:
            st.session_state.results_access = False
        return is_valid

    def check_rate_limit(self, last_votes: dict, name: str) -> tuple[bool, str]:
        """Check if user is within rate limit"""
        if name not in last_votes:
            last_votes[name] = datetime.now()
            return True, ""

        time_since_last_vote = datetime.now() - last_votes[name]
        if time_since_last_vote < timedelta(seconds=CONFIG["RATE_LIMIT"]):
            return False, f"Aguarde {CONFIG['RATE_LIMIT']} segundos entre os votos"

        last_votes[name] = datetime.now()
        return True, ""

    @staticmethod
    def validate_admin_password(password: str) -> bool:
        """Validate admin password"""
        is_valid = password == CONFIG["ADMIN_PASSWORD"]
        if not is_valid and "is_admin" in st.session_state:
            st.session_state.is_admin = False
        return is_valid 