"""
Provides classes for managing and interacting with the DuckDB database
containing stock ticker news articles and metadata.

This module includes:
- DatabaseConnection: A context manager for handling DuckDB connections.
- DatabaseManager: A class for initializing the database schema, inserting
  article data and ticker metadata, and retrieving data.

It uses DuckDB for storage and Pandas DataFrames for data manipulation.
"""

# implement duckdb cursor to write to same db with multiple threads

import os
from types import TracebackType
from typing import Literal, final

import duckdb
import pandas as pd
from loguru import logger


class DatabaseConnection:
    """
    A context manager for DuckDB database connections.
    Allows for simplified database access with automatic resource cleanup.
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
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit the context manager, closing the database connection.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        if self.conn:
            self.conn.close()


@final
class DatabaseManager:
    """
    A class to handle database operations.
    """

    def __init__(self, db_path: str | None = None):
        """Initialize the database manager with the database path."""
        if db_path is None:
            # Construct path relative to this file's directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(script_dir, "..", "datasets", "ticker_data.db")
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
            conn.execute(
                """CREATE TABLE IF NOT EXISTS article_data (
                    ticker TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    date_posted TEXT NOT NULL,
                    source TEXT,
                    article_link TEXT,
                    negative_sentiment FLOAT DEFAULT NULL,
                    positive_sentiment FLOAT DEFAULT NULL,
                    neutral_sentiment FLOAT DEFAULT NULL,
                    compound_sentiment FLOAT DEFAULT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (ticker, headline)
                )"""
            )

            # Create ticker metadata table with ticker as primary key
            conn.execute(
                """CREATE TABLE IF NOT EXISTS ticker_meta (
                    ticker TEXT PRIMARY KEY NOT NULL,
                    sector TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    mCap REAL,
                    companyName TEXT NOT NULL
                )"""
            )

    def insert_articles(self, articles_df: pd.DataFrame, has_sentiment: bool = False) -> None:
        """
        Insert articles into the database with conflict resolution to avoid duplicates.

        Args:
            articles_df: DataFrame with article data
            has_sentiment: Whether the DataFrame includes sentiment columns
        """
        logger.info(f"Inserting {articles_df.shape[0]} articles {'with' if has_sentiment else 'without'} sentiment into the database")
        with self.get_connection() as conn:
            if has_sentiment:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO article_data (
                        ticker, headline, date_posted, source, article_link,
                        neutral_sentiment, negative_sentiment, positive_sentiment, compound_sentiment, created_at
            
                    )
                    SELECT 
                        ticker, headline, date_posted, source, article_link,
                        Neutral, Negative, Positive, compound, CURRENT_TIMESTAMP
                    FROM articles_df;
                    """
                )
            else:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO article_data 
                    (ticker, headline, date_posted, source, article_link, created_at) 
                    SELECT 
                        ticker, headline, date_posted, source, article_link, CURRENT_TIMESTAMP 
                    FROM articles_df;
                    """
                )
        logger.success(f"Inserted {articles_df.shape[0]} articles into the database")

    def insert_ticker_metadata(self, ticker_meta: list[list[str | float | None]]) -> None:
        """
        Insert or replace ticker metadata.

        Args:
            ticker_meta: List of ticker metadata [ticker, sector, industry, mCap, companyName]
        """
        with self.get_connection() as conn:
            logger.info(f"Inserting metadata for {len(ticker_meta)} tickers")
            # Using UPSERT pattern for each row
            for meta in ticker_meta:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO ticker_meta 
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    meta,
                )

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
            query_parts = ["SELECT * FROM article_data WHERE 1=1"]
            params = []

            # Apply sentiment filter
            if not has_sentiment:
                query_parts.append("AND compound_sentiment IS NULL")

            # Apply date filter
            if after_date is not None:
                query_parts.append("AND date_posted >= ?")
                params.append(after_date)

            # Apply ordering
            order_direction: Literal["DESC", "ASC"] = "DESC" if latest else "ASC"
            query_parts.append(f"ORDER BY date_posted {order_direction}")

            # Apply limit
            query_parts.append("LIMIT ?")
            params.append(n)

            # Build and execute query
            query = " ".join(query_parts)
            return conn.execute(query, params).fetchdf()

    def get_ticker_metadata(self) -> pd.DataFrame:
        """Retrieve all ticker metadata from the database."""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM ticker_meta").fetchdf()


    def get_index_constituents(self, index: str = "nifty_50") -> pd.DataFrame:
        """get index constituents from the database"""
        with self.get_connection() as conn:
            return conn.execute(f"select ticker from indices_constituents where {index} = true;").fetchdf()


if __name__ == "__main__":
    # Example usage
    db_manager = DatabaseManager()
    articles_df = db_manager.get_articles(has_sentiment=False, n=100)
    logger.info(f"Retrieved {articles_df.shape[0]} articles from the database.")
