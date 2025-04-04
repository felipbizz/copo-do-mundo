from config import CONFIG
from frontend.utils.session_manager import SessionManager


class Validators:
    @staticmethod
    def validate_admin_password(password: str) -> bool:
        """Validate admin password"""
        is_valid = password == CONFIG["ADMIN_PASSWORD"]
        if not is_valid:
            SessionManager.reset_access_state()
        return is_valid
