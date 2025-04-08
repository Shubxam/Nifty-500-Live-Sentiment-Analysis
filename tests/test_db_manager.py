import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path

from database.db_manager import DatabaseManager
from config import DB_PATH


@pytest.fixture
def mock_duckdb():
    with patch('duckdb.connect') as mock:
        yield mock


@pytest.fixture
def db_manager(mock_duckdb):
    return DatabaseManager(DB_PATH)


def test_singleton_pattern():
    """Test that DatabaseManager follows singleton pattern"""
    db1 = DatabaseManager()  # Should use default DB_PATH
    db2 = DatabaseManager(DB_PATH)  # Explicit path
    assert db1 is db2
    assert db1.db_path == DB_PATH


def test_setup_database(db_manager, mock_duckdb):
    """Test database initialization"""
    mock_conn = MagicMock()
    mock_duckdb.return_value = mock_conn

    db_manager._setup_database()

    # Verify tables and indexes were created
    mock_conn.execute.assert_called()
    calls = mock_conn.execute.call_args_list
    assert any('CREATE TABLE IF NOT EXISTS article_data' in str(call) for call in calls)
    assert any('CREATE TABLE IF NOT EXISTS ticker_meta' in str(call) for call in calls)


def test_insert_articles(db_manager, mock_duckdb):
    """Test article insertion with DataFrame registration"""
    mock_conn = MagicMock()
    mock_duckdb.return_value = mock_conn

    test_df = pd.DataFrame({
        'ticker': ['TEST'],
        'headline': ['Test headline'],
        'date_posted': ['2024-01-01'],
        'source': ['test_source'],
        'article_link': ['http://test.com']
    })

    db_manager.insert_articles(test_df)

    # Verify DataFrame registration and insertion
    mock_conn.register.assert_called_once_with('articles_df', test_df)
    assert any('INSERT INTO article_data' in str(call) for call in mock_conn.execute.call_args_list)


def test_update_sentiment_scores(db_manager, mock_duckdb):
    """Test sentiment score updates"""
    mock_conn = MagicMock()
    mock_duckdb.return_value = mock_conn

    test_df = pd.DataFrame({
        'id': [1],
        'positive': [0.9],
        'negative': [0.05],
        'neutral': [0.05],
        'compound': [0.85]
    })

    db_manager.update_sentiment_scores(test_df)
    mock_conn.execute.assert_called()
    assert 'UPDATE article_data' in str(mock_conn.execute.call_args[0][0])


def test_get_articles_without_sentiment(db_manager, mock_duckdb):
    """Test fetching articles without sentiment scores"""
    mock_conn = MagicMock()
    mock_duckdb.return_value = mock_conn
    test_df = pd.DataFrame({'id': [1], 'headline': ['Test']})
    mock_conn.execute().fetchdf.return_value = test_df

    result = db_manager.get_articles_without_sentiment(100)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    mock_conn.execute.assert_called_with(
"SELECT id, headline FROM article_data WHERE compound_sentiment IS NULL LIMIT 100"
    )
