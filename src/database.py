# implement duckdb cursor to write to same db with multiple threads

from typing import final
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
    
    def __exit__(self, exc_type, exc_val, exc_tb):
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

    def __init__(self, db_path: str = "./datasets/ticker_data.db"):
        """Initialize the database manager with the database path."""
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
                    PRIMARY KEY (ticker, headline, date_posted)
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
        with self.get_connection() as conn:
            if has_sentiment:
                logger.info(
                    f"Inserting articles with sentiment scores for {len(articles_df)} news articles"
                )
                # Using UPSERT pattern (INSERT OR REPLACE)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO article_data 
                    SELECT *, CURRENT_TIMESTAMP FROM articles_df
                    """
                )
            else:
                logger.info(
                    f"Inserting articles without sentiment scores for {len(articles_df)} news articles"
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO article_data 
                    (ticker, headline, date_posted, source, article_link, created_at) 
                    SELECT *, CURRENT_TIMESTAMP FROM articles_df
                    """
                )

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
                    meta
                )

    def get_articles(self) -> pd.DataFrame:
        """Retrieve all articles from the database."""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM article_data").fetchdf()

    def get_ticker_metadata(self) -> pd.DataFrame:
        """Retrieve all ticker metadata from the database."""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM ticker_meta").fetchdf()


if __name__ == "__main__":
    # Example usage
    db_manager = DatabaseManager()
    articles_df = db_manager.get_articles()
    logger.info(f"Retrieved {articles_df.shape[0]} articles from the database.")