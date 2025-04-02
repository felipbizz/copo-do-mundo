from datetime import datetime

import pandas as pd
import pytest

from backend.data.vote_manager import VoteManager


@pytest.fixture
def vote_manager():
    return VoteManager()


@pytest.fixture
def sample_vote_data():
    """Create sample vote data"""
    return pd.DataFrame(
        {
            "Nome": ["Test User"],
            "Participante": ["1"],
            "Categoria": ["Caipirinha"],
            "Originalidade": [8],
            "Aparencia": [9],
            "Sabor": [7],
            "Data": [datetime.now()],
        }
    )


def test_create_vote(vote_manager):
    """Test vote creation"""
    vote = vote_manager.create_vote(
        name="Test User",
        categoria="Caipirinha",
        participant="1",
        originalidade=8,
        aparencia=9,
        sabor=7,
    )

    assert isinstance(vote, pd.DataFrame)
    assert len(vote) == 1
    assert vote.iloc[0]["Nome"] == "Test User"
    assert vote.iloc[0]["Categoria"] == "Caipirinha"
    assert vote.iloc[0]["Participante"] == "1"
    assert vote.iloc[0]["Originalidade"] == 8
    assert vote.iloc[0]["Aparencia"] == 9
    assert vote.iloc[0]["Sabor"] == 7
    assert isinstance(vote.iloc[0]["Data"], datetime)


def test_check_duplicate_vote(vote_manager, sample_vote_data):
    """Test duplicate vote checking"""
    # Test exact duplicate
    assert (
        vote_manager.check_duplicate_vote(
            sample_vote_data, name="Test User", categoria="Caipirinha", participant="1"
        )
        is True
    )

    # Test different category (should not be duplicate)
    assert (
        vote_manager.check_duplicate_vote(
            sample_vote_data, name="Test User", categoria="Livre", participant="1"
        )
        is False
    )

    # Test different participant (should not be duplicate)
    assert (
        vote_manager.check_duplicate_vote(
            sample_vote_data, name="Test User", categoria="Caipirinha", participant="2"
        )
        is False
    )

    # Test different user (should not be duplicate)
    assert (
        vote_manager.check_duplicate_vote(
            sample_vote_data, name="Other User", categoria="Caipirinha", participant="1"
        )
        is False
    )


def test_remove_duplicate_vote(vote_manager, sample_vote_data):
    """Test removing duplicate votes"""
    # Add a duplicate vote
    duplicate_data = pd.concat([sample_vote_data, sample_vote_data])
    assert len(duplicate_data) == 2

    # Remove duplicate
    cleaned_data = vote_manager.remove_duplicate_vote(
        duplicate_data, name="Test User", categoria="Caipirinha", participant="1"
    )

    # Should only have one vote now
    assert len(cleaned_data) == 1

    # Test removing non-existent vote (should not change data)
    cleaned_data = vote_manager.remove_duplicate_vote(
        sample_vote_data, name="Other User", categoria="Caipirinha", participant="1"
    )
    assert len(cleaned_data) == len(sample_vote_data)
