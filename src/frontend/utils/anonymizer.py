import random
import string

import streamlit as st


class Anonymizer:
    """
    Manages drink anonymization for voting.

    This class handles the mapping between drink codes and participants,
    ensuring that jurors only see drink codes or custom names during voting,
    while maintaining the connection to actual participants for results calculation.

    Attributes:
        None (all methods are static)

    Usage:
        ```python
        # Initialize the anonymization system
        Anonymizer.initialize_anonymization()

        # Get or create a code for a drink
        code = Anonymizer.get_or_create_code(participant=1, categoria="Categoria1")

        # Set a custom name for the drink
        Anonymizer.set_drink_name(code, "Gin Tônica")

        # Get the custom name (or code if no name is set)
        drink_name = Anonymizer.get_drink_name(code)

        # Get participant info from code (admin only)
        participant, categoria = Anonymizer.get_participant_from_code(code)
        ```
    """

    @staticmethod
    def initialize_anonymization() -> None:
        """
        Initialize anonymization data in session state.

        This method must be called at the start of the application to ensure
        all necessary session state variables are properly initialized.

        Creates three dictionaries in session state:
        - drink_codes: Maps participant-category pairs to codes
        - code_to_participant: Maps codes to participant-category pairs
        - drink_names: Maps codes to custom drink names
        """
        if "drink_codes" not in st.session_state:
            st.session_state.drink_codes = {}
        if "code_to_participant" not in st.session_state:
            st.session_state.code_to_participant = {}
        if "drink_names" not in st.session_state:
            st.session_state.drink_names = {}

    @staticmethod
    def generate_code() -> str:
        """
        Generate a random code for a drink.

        Returns:
            str: A 6-character code using uppercase letters and numbers.
        """
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    @staticmethod
    def get_or_create_code(participant: int, categoria: str) -> str:
        """
        Get existing code or create new one for a drink.

        Args:
            participant (int): The participant number
            categoria (str): The drink category

        Returns:
            str: The drink code (existing or newly created)
        """
        key = f"{participant}_{categoria}"
        if key not in st.session_state.drink_codes:
            code = Anonymizer.generate_code()
            st.session_state.drink_codes[key] = code
            st.session_state.code_to_participant[code] = (participant, categoria)
        return st.session_state.drink_codes[key]

    @staticmethod
    def get_participant_from_code(code: str) -> tuple[int, str] | None:
        """
        Get participant and category from code (admin only).

        Args:
            code (str): The drink code

        Returns:
            Optional[Tuple[int, str]]: Tuple of (participant, category) if code exists,
                                     None otherwise
        """
        return st.session_state.code_to_participant.get(code)

    @staticmethod
    def get_code_from_participant(participant: int, categoria: str) -> str | None:
        """
        Get code from participant and category (admin only).

        Args:
            participant (int): The participant number
            categoria (str): The drink category

        Returns:
            Optional[str]: The drink code if exists, None otherwise
        """
        key = f"{participant}_{categoria}"
        return st.session_state.drink_codes.get(key)

    @staticmethod
    def get_all_codes() -> dict[str, tuple[int, str]]:
        """
        Get all code mappings (admin only).

        Returns:
            Dict[str, Tuple[int, str]]: Dictionary mapping codes to (participant, category) tuples
        """
        return st.session_state.code_to_participant.copy()

    @staticmethod
    def get_drink_name(code: str) -> str:
        """
        Get custom name for a drink, or return the code if no name is set.

        Args:
            code (str): The drink code

        Returns:
            str: The custom name if set, otherwise the code itself
        """
        return st.session_state.drink_names.get(code, code)

    @staticmethod
    def set_drink_name(code: str, name: str) -> None:
        """
        Set custom name for a drink.

        Args:
            code (str): The drink code
            name (str): The custom name to set
        """
        st.session_state.drink_names[code] = name

    @staticmethod
    def clear_anonymization() -> None:
        """
        Clear all anonymization data.

        This method resets all session state variables related to anonymization.
        Use with caution as it will remove all code mappings and custom names.
        """
        st.session_state.drink_codes = {}
        st.session_state.code_to_participant = {}
        st.session_state.drink_names = {}
