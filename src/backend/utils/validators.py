"""Data validation utilities for storage operations."""

import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

# Required columns for vote data
REQUIRED_COLUMNS = [
    "Nome",
    "Participante",
    "Categoria",
    "Originalidade",
    "Aparencia",
    "Sabor",
    "Data",
]

# Column types mapping
COLUMN_TYPES = {
    "Nome": str,
    "Participante": str,
    "Categoria": str,
    "Originalidade": int,
    "Aparencia": int,
    "Sabor": int,
    "Data": (datetime, pd.Timestamp),
}


class ValidationError(Exception):
    """Exception raised when data validation fails."""

    pass


def validate_vote_data(data: pd.DataFrame) -> None:
    """Validate vote data structure and content.

    Args:
        data: DataFrame containing vote data.

    Raises:
        ValidationError: If validation fails.
    """
    if not isinstance(data, pd.DataFrame):
        raise ValidationError("Data must be a pandas DataFrame")

    if data.empty:
        # Empty DataFrame is valid (used for clearing)
        return

    # Check required columns
    missing_columns = set(REQUIRED_COLUMNS) - set(data.columns)
    if missing_columns:
        raise ValidationError(f"Missing required columns: {missing_columns}")

    # Validate data types
    for col in REQUIRED_COLUMNS:
        if col not in data.columns:
            continue

        expected_type = COLUMN_TYPES[col]
        if col == "Data":
            # Data column should be datetime-like
            if not pd.api.types.is_datetime64_any_dtype(data[col]):
                try:
                    pd.to_datetime(data[col])
                except (ValueError, TypeError) as e:
                    raise ValidationError(f"Column '{col}' must be datetime-like") from e
        else:
            # Check if values can be converted to expected type
            try:
                if expected_type is int:
                    pd.to_numeric(data[col], errors="raise").astype(int)
                elif expected_type is str:
                    data[col].astype(str)
            except (ValueError, TypeError) as e:
                raise ValidationError(
                    f"Column '{col}' contains invalid values for type {expected_type}: {str(e)}"
                ) from e

    # Validate score ranges
    score_columns = ["Originalidade", "Aparencia", "Sabor"]
    for col in score_columns:
        if col in data.columns:
            invalid_scores = data[(data[col] < 0) | (data[col] > 10) | data[col].isna()]
            if not invalid_scores.empty:
                raise ValidationError(
                    f"Column '{col}' contains invalid scores. "
                    f"Scores must be between 0 and 10. Found {len(invalid_scores)} invalid values."
                )

    # Validate non-empty required fields
    required_string_columns = ["Nome", "Participante", "Categoria"]
    for col in required_string_columns:
        if col in data.columns:
            empty_values = data[data[col].isna() | (data[col].astype(str).str.strip() == "")]
            if not empty_values.empty:
                raise ValidationError(f"Column '{col}' contains empty values. Found {len(empty_values)} empty values.")


def validate_single_vote(
    name: str,
    participant: str,
    categoria: str,
    originalidade: int,
    aparencia: int,
    sabor: int,
) -> None:
    """Validate a single vote before insertion.

    Args:
        name: Name of the juror.
        participant: Participant ID.
        categoria: Category of the vote.
        originalidade: Originality score (0-10).
        aparencia: Appearance score (0-10).
        sabor: Taste score (0-10).

    Raises:
        ValidationError: If validation fails.
    """
    # Validate name
    if not name or not str(name).strip():
        raise ValidationError("Name cannot be empty")

    # Validate participant
    if not participant or not str(participant).strip():
        raise ValidationError("Participant cannot be empty")

    # Validate categoria
    if not categoria or not str(categoria).strip():
        raise ValidationError("Categoria cannot be empty")

    # Validate scores
    for score_name, score_value in [
        ("Originalidade", originalidade),
        ("Aparencia", aparencia),
        ("Sabor", sabor),
    ]:
        try:
            score_int = int(score_value)
            if not 0 <= score_int <= 10:
                raise ValidationError(f"{score_name} must be between 0 and 10, got {score_int}")
        except (ValueError, TypeError) as e:
            raise ValidationError(f"{score_name} must be an integer between 0 and 10") from e
