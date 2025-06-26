"""
Provides classes for managing and interacting with the DuckDB database
containing stock ticker news articles and metadata.

This module includes:
- DatabaseConnection: A context manager for handling DuckDB connections.
- DatabaseManager: A class for initializing the database schema, inserting
  article data and ticker metadata, and retrieving data.

It uses DuckDB for storage and Pandas DataFrames for data manipulation.
"""

# TODO: evaluate the need to implement duckdb cursor to write to same db with multiple threads
# TODO: make all sql queries consistent and use parameterized queries to prevent SQL injection

import os
from types import TracebackType
from typing import final

import duckdb
import pandas as pd
from loguru import logger

from nifty_analyzer.config import (
    BASE_DIR,
    CREATE_TABLE,
    DB_NAME,
    GET_DATA,
    INSERT_DATA,
)
from nifty_analyzer.core.utils import build_articles_query, setup_logger

DB_PATH = os.path.join(BASE_DIR, 'database')


class DatabaseConnection:
    """
    A context manager class for DuckDB database connections.
    """

    def __init__(self, db_path: str) -> None:
        """
        Initialize the database connection context manager.

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path: str = db_path
        self.conn: duckdb.DuckDBPyConnection | None = None

    def __enter__(self):
        """
        Enter the context manager, establishing a connection to the database.

        Returns:
            The DuckDB connection object
        """
        self.conn = duckdb.connect(self.db_path)
        return self.conn

    def __exit__(
        self,
        exc_type: BaseException | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Exit the context manager, closing the database connection.
        """
        if self.conn:
            self.conn.close()


@final
class DatabaseManager:
    """
    A class to handle database operations.
    """

    def __init__(self, db_path: str = ''):
        """Initialize the database manager with the database path."""
        if not db_path:
            # Construct path relative to this file's directory
            self.db_path = os.path.join(DB_PATH, DB_NAME)
        else:
            self.db_path = db_path
        self._initialize_db()

    def get_connection(self) -> DatabaseConnection:
        """
        Get a database connection context manager.

        Returns:
            A DatabaseConnection context manager

        Example:
            ```python
            db_manager = DatabaseManager()
            with db_manager.get_connection() as conn:
                result = conn.execute("SELECT * FROM article_data").fetchdf()
            ```
        """
        return DatabaseConnection(self.db_path)

    def _initialize_db(self) -> None:
        """Initialize the database tables if they don't exist."""
        with self.get_connection() as conn:
            # Create article data table with composite primary key
            conn.execute(CREATE_TABLE['article_data'])

            # Create ticker metadata table with ticker as primary key
            conn.execute(CREATE_TABLE['ticker_meta'])

    def insert_articles(
        self, articles_df: pd.DataFrame, has_sentiment: bool = False
    ) -> None:
        """
        Insert articles into the database with conflict resolution to avoid duplicates.

        Args:
            articles_df: DataFrame with article data
            has_sentiment: Whether the DataFrame includes sentiment columns
        """
        logger.info(
            f'Inserting {articles_df.shape[0]} articles {"with" if has_sentiment else "without"} sentiment into the database'
        )
        with self.get_connection() as conn:
            if has_sentiment:
                conn.execute(INSERT_DATA['article_data_with_sentiment'])
            else:
                conn.execute(INSERT_DATA['article_data_without_sentiment'])
        logger.success(f'Inserted {articles_df.shape[0]} articles into the database')

    def insert_ticker_metadata(
        self, ticker_meta: list[list[str | float | None]]
    ) -> None:
        """
        Insert or replace ticker metadata.

        Args:
            ticker_meta: List of ticker metadata [ticker, sector, industry, mCap, companyName]
        """
        with self.get_connection() as conn:
            logger.info(f'Inserting metadata for {len(ticker_meta)} tickers')
            # Using UPSERT pattern for each row
            for meta in ticker_meta:
                conn.execute(INSERT_DATA['ticker_meta'], meta)

    def get_articles(
        self,
        n: int = 20,
        latest: bool = True,
        has_sentiment: bool = True,
        after_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Retrieve articles from the database with filtering options.

        Args:
            n: Number of articles to return
            latest: If True, returns the n latest articles; if False, returns the n oldest
            has_sentiment: If False, returns only articles without sentiment scores
            after_date: Filter for articles after this date in 'yyyy-MM-dd' format (None for no date filtering)

        Returns:
            DataFrame containing the filtered articles
        """
        with self.get_connection() as conn:
            query, params = build_articles_query(
                has_sentiment=has_sentiment,
                after_date=after_date,
                latest=latest,
                limit=n,
            )
            return conn.execute(query, params).fetchdf()

    def get_ticker_metadata(self) -> pd.DataFrame:
        """Retrieve all ticker metadata from the database."""
        with self.get_connection() as conn:
            return conn.execute(GET_DATA['ticker_meta']).fetchdf()

    def get_index_constituents(self, index: str = 'nifty_50') -> pd.DataFrame:
        """get index constituents from the database"""
        # TODO: validate index input against known indices
        with self.get_connection() as conn:
            return conn.execute(
                GET_DATA['index_constituents'].format(index)  # nosec B608
            ).fetchdf()


if __name__ == '__main__':
    setup_logger()
    # Example usage
    db_manager = DatabaseManager()
    articles_df = db_manager.get_articles(has_sentiment=True, n=100)
    logger.info(f'Retrieved {articles_df.shape[0]} articles from the database.')
