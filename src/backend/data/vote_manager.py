import logging
from datetime import datetime

import pandas as pd

from config import CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoteManagerError(Exception):
    """Base exception for VoteManager errors."""

    pass


class VoteManager:
    """Manages voting operations for the competition.

    This class handles all voting-related operations including creating new votes,
    checking for duplicates, removing duplicates, and tracking voting progress.
    """

    def create_vote(
        self,
        name: str,
        categoria: str,
        participant: str,
        originalidade: int,
        aparencia: int,
        sabor: int,
    ) -> pd.DataFrame:
        """Create a new vote entry.

        Args:
            name (str): Name of the juror.
            categoria (str): Category being voted on.
            participant (str): Participant ID being voted for.
            originalidade (int): Originality score (1-10).
            aparencia (int): Appearance score (1-10).
            sabor (int): Taste score (1-10).

        Returns:
            pd.DataFrame: DataFrame containing the new vote entry.

        Raises:
            VoteManagerError: If any of the scores are invalid.
        """
        try:
            # Validate scores
            for score in [originalidade, aparencia, sabor]:
                if not 0 <= score <= 10:
                    raise VoteManagerError(
                        f"Invalid score: {score}. Scores must be between 0 and 10."
                    )

            vote = pd.DataFrame(
                [
                    {
                        "Nome": name,
                        "Participante": participant,
                        "Categoria": categoria,
                        "Originalidade": originalidade,
                        "Aparencia": aparencia,
                        "Sabor": sabor,
                        "Data": datetime.now(),
                    }
                ]
            )

            logger.info(f"Created new vote for participant {participant} in category {categoria}")
            return vote

        except Exception as e:
            raise VoteManagerError(f"Error creating vote: {str(e)}") from e

    def check_duplicate_vote(
        self, data: pd.DataFrame, name: str, categoria: str, participant: str
    ) -> bool:
        """Check if a vote already exists for this participant and category.

        Args:
            data (pd.DataFrame): Current voting data.
            name (str): Name of the juror.
            categoria (str): Category being checked.
            participant (str): Participant ID being checked.

        Returns:
            bool: True if a duplicate vote exists, False otherwise.
        """
        is_duplicate = not data[
            (data["Nome"] == name)
            & (data["Categoria"] == categoria)
            & (data["Participante"] == participant)
        ].empty

        if is_duplicate:
            logger.warning(f"Duplicate vote found for {name} - {categoria} - {participant}")
        return is_duplicate

    def remove_duplicate_vote(
        self, data: pd.DataFrame, name: str, categoria: str, participant: str
    ) -> pd.DataFrame:
        """Remove all occurrences of a duplicate vote.

        Args:
            data (pd.DataFrame): Current voting data.
            name (str): Name of the juror.
            categoria (str): Category of the vote.
            participant (str): Participant ID.

        Returns:
            pd.DataFrame: Updated voting data with the vote removed.

        Raises:
            VoteManagerError: If there's an error removing the duplicate vote.
        """
        try:
            # Find all matching votes
            mask = (
                (data["Nome"] == name)
                & (data["Categoria"] == categoria)
                & (data["Participante"] == participant)
            )

            # Get all non-matching votes (effectively removing all matching votes)
            result = data[~mask].copy()

            logger.info(f"Removed all votes for {name} - {categoria} - {participant}")
            return result

        except Exception as e:
            raise VoteManagerError(f"Error removing duplicate vote: {str(e)}") from e

    def get_missing_votes(
        self, data: pd.DataFrame, name: str, categories: list[str], num_participants: int
    ) -> list[tuple[str, int]]:
        """Get list of missing votes for a juror.

        Args:
            data (pd.DataFrame): Current voting data.
            name (str): Name of the juror.
            categories (List[str]): List of all categories.
            num_participants (int): Total number of participants.

        Returns:
            List[Tuple[str, int]]: List of tuples (category, participant_id) for missing votes.
        """
        missing_votes: list[tuple[str, int]] = []

        # Get all votes for this juror
        juror_votes = data[data["Nome"] == name]

        # Check each category and participant combination
        for categoria in categories:
            for participant in range(1, num_participants + 1):
                # Check if this combination exists in juror's votes
                if juror_votes[
                    (juror_votes["Categoria"] == categoria)
                    & (juror_votes["Participante"] == str(participant))
                ].empty:
                    missing_votes.append((categoria, participant))

        if missing_votes:
            logger.info(f"Found {len(missing_votes)} missing votes for {name}")
        return missing_votes

    def clear_votes(self) -> None:
        """Clear all votes from the system.

        This method handles the entire process of clearing votes:
        1. Clears the data file
        2. Updates the session state
        3. Invalidates the cache

        Raises:
            VoteManagerError: If there's an error clearing votes.
        """
        try:
            # Get current data
            data = self.load_data()

            # Clear votes (this will save to file)
            empty_df = self.clear_all_votes(data)

            logger.info("All votes have been cleared and system state updated")
            return empty_df
        except Exception as e:
            raise VoteManagerError(f"Error clearing votes: {str(e)}") from e

    def load_data(self) -> pd.DataFrame:
        """Load voting data from the data file.

        Returns:
            pd.DataFrame: Loaded voting data.

        Raises:
            VoteManagerError: If there's an error loading the data.
        """
        try:
            # Load data from file
            data = pd.read_csv(CONFIG["DATA_FILE"])

            logger.info("Loaded voting data")
            return data

        except Exception as e:
            raise VoteManagerError(f"Error loading data: {str(e)}") from e

    def clear_all_votes(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clear all votes from the voting data.

        Args:
            data (pd.DataFrame): Current voting data.

        Returns:
            pd.DataFrame: Empty DataFrame with the same columns.

        Raises:
            VoteManagerError: If there's an error clearing votes.
        """
        try:
            # Create a new empty DataFrame with the same columns
            empty_df = pd.DataFrame(columns=data.columns)

            # Save the empty DataFrame directly to the data file
            empty_df.to_csv(CONFIG["DATA_FILE"], index=False)

            logger.info("All votes have been cleared and saved")
            return empty_df

        except Exception as e:
            raise VoteManagerError(f"Error clearing votes: {str(e)}") from e
