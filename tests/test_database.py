import atexit
import os
import shutil
import sys
import tempfile

import pandas as pd
import pytest

# This adds the 'src' directory to the Python path.
src_rel_path = '../src'
src_abs_path = os.path.abspath(src_rel_path)

if src_abs_path not in sys.path:
    sys.path.append(src_abs_path)
    print(f"Added '{src_abs_path}' to sys.path")
else:
    print(f"'{src_abs_path}' is already in sys.path")

from database import DatabaseManager

tempdir_path = tempfile.mkdtemp()
print(f'Temporary directory created at: {tempdir_path}')


def cleanup_dir():
    print(f'Cleaning up temporary directory: {tempdir_path}')
    shutil.rmtree(tempdir_path)


atexit.register(cleanup_dir)


# Fixture to create a temporary database for testing
@pytest.fixture(scope='module')
def db_manager():
    """Provides a DatabaseManager instance with an in-memory database for tests."""
    test_db_path = f'{tempdir_path}/test.db'  # Use in-memory database
    manager = DatabaseManager(db_path=test_db_path)
    yield manager


# Test data
mock_articles_no_sentiment = pd.DataFrame(
    {
        'ticker': ['AAPL', 'GOOG'],
        'headline': ['Apple News', 'Google News'],
        'date_posted': ['2023-01-01', '2023-01-02'],
        'source': ['SourceA', 'SourceB'],
        'article_link': ['link1', 'link2'],
    }
)

mock_articles_with_sentiment = pd.DataFrame(
    {
        'ticker': ['MSFT', 'AMZN'],
        'headline': ['Microsoft News', 'Amazon News'],
        'date_posted': ['2023-01-03', '2023-01-04'],
        'source': ['SourceC', 'SourceD'],
        'article_link': ['link3', 'link4'],
        'negative_sentiment': [0.1, 0.2],
        'positive_sentiment': [0.7, 0.6],
        'neutral_sentiment': [0.2, 0.2],
        'compound_sentiment': [0.6, 0.4],
    }
)

mock_ticker_meta = [
    ['AAPL', 'Tech', 'Electronics', 2.5e12, 'Apple Inc.'],
    ['GOOG', 'Tech', 'Internet', 1.8e12, 'Alphabet Inc.'],
]


def test_db_initialization(db_manager):
    """Test if the database and tables are created."""
    with db_manager.get_connection() as conn:
        # Use DuckDB's way to list tables
        tables_df = conn.execute('SHOW TABLES;').fetchdf()
        table_names = tables_df['name'].tolist() if not tables_df.empty else []
        assert 'article_data' in table_names
        assert 'ticker_meta' in table_names


def test_insert_articles_no_sentiment(db_manager):
    """Test inserting articles without sentiment scores."""
    db_manager.insert_articles(mock_articles_no_sentiment, has_sentiment=False)
    with db_manager.get_connection() as conn:
        df = conn.execute(
            'SELECT * FROM article_data WHERE compound_sentiment IS NULL'
        ).fetchdf()
        assert len(df) == 2
        assert 'AAPL' in df['ticker'].values
        assert (
            df['negative_sentiment'].isnull().all()
        )  # Check sentiment columns are NULL


def test_insert_duplicate_articles(db_manager):
    """Test inserting duplicate articles."""
    # Insert the same articles twice
    db_manager.insert_articles(mock_articles_no_sentiment, has_sentiment=False)
    db_manager.insert_articles(mock_articles_no_sentiment, has_sentiment=False)

    with db_manager.get_connection() as conn:
        df = conn.execute('SELECT * FROM article_data').fetchdf()
        assert len(df) == 2  # Should still be 2 due to primary key constraint
        assert df['ticker'].nunique() == 2  # Ensure unique tickers


def test_insert_articles_with_sentiment(db_manager):
    """Test inserting articles with sentiment scores."""
    db_manager.insert_articles(mock_articles_with_sentiment, has_sentiment=True)
    with db_manager.get_connection() as conn:
        # Fetch only the newly inserted articles with sentiment
        df = conn.execute(
            'SELECT * FROM article_data WHERE compound_sentiment IS NOT NULL'
        ).fetchdf()
        assert len(df) == 2
        assert 'MSFT' in df['ticker'].values
        assert (
            not df['compound_sentiment'].isnull().any()
        )  # Check sentiment columns are NOT NULL


def test_insert_ticker_metadata(db_manager):
    """Test inserting ticker metadata."""
    db_manager.insert_ticker_metadata(mock_ticker_meta)
    with db_manager.get_connection() as conn:
        df = conn.execute('SELECT * FROM ticker_meta').fetchdf()
        assert len(df) == 2
        assert 'AAPL' in df['ticker'].values
        assert df[df['ticker'] == 'GOOG']['industry'].iloc[0] == 'Internet'


def test_get_articles(db_manager):
    """Test retrieving articles with various filters."""
    # Insert all test articles first
    db_manager.insert_articles(mock_articles_no_sentiment, has_sentiment=False)
    db_manager.insert_articles(mock_articles_with_sentiment, has_sentiment=True)

    # Test get latest n=1 with sentiment (should be AMZN)
    latest_with_sentiment = db_manager.get_articles(
        n=1, latest=True, has_sentiment=True
    )
    assert len(latest_with_sentiment) == 1
    assert latest_with_sentiment['ticker'].iloc[0] == 'AMZN'
    assert latest_with_sentiment['compound_sentiment'].iloc[0] is not None

    # Test get oldest n=1 without sentiment (should be AAPL)
    oldest_no_sentiment = db_manager.get_articles(
        n=1, latest=False, has_sentiment=False
    )
    assert len(oldest_no_sentiment) == 1
    assert oldest_no_sentiment['ticker'].iloc[0] == 'AAPL'
    # Use pd.isnull() to check for NaN
    assert pd.isnull(oldest_no_sentiment['compound_sentiment'].iloc[0])

    # Test get all (n=4) latest
    all_latest = db_manager.get_articles(n=4, latest=True)
    assert len(all_latest) == 4
    assert all_latest[
        'date_posted'
    ].is_monotonic_decreasing  # Dates should be descending

    # Test get articles after a specific date
    after_date_articles = db_manager.get_articles(after_date='2023-01-02', n=10)
    assert len(after_date_articles) == 3  # GOOG, MSFT and AMZN
    assert 'AAPL' not in after_date_articles['ticker'].values


def test_get_ticker_metadata(db_manager):
    """Test retrieving all ticker metadata."""
    # Ensure metadata is inserted first
    db_manager.insert_ticker_metadata(mock_ticker_meta)

    metadata_df = db_manager.get_ticker_metadata()
    assert isinstance(metadata_df, pd.DataFrame)
    assert len(metadata_df) == 2
    assert 'ticker' in metadata_df.columns
    assert 'companyName' in metadata_df.columns
    assert 'AAPL' in metadata_df['ticker'].values
