import logging
from datetime import datetime

import pandas as pd

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

    def calculate_progress(
        self, data: pd.DataFrame, name: str, categories: list[str], num_participants: int
    ) -> float:
        """Calculate voting progress as a percentage.

        Args:
            data (pd.DataFrame): Current voting data.
            name (str): Name of the juror.
            categories (List[str]): List of all categories.
            num_participants (int): Total number of participants.

        Returns:
            float: Percentage of votes completed (0-100).
        """
        # Get total possible votes
        total_possible_votes = len(categories) * num_participants

        # Get current votes for this juror
        current_votes = len(data[data["Nome"] == name])

        # Calculate progress percentage
        progress = (current_votes / total_possible_votes) * 100
        logger.info(f"Voting progress for {name}: {progress:.1f}%")
        return progress
