"""
This module provides a DatabaseManager class that encapsulates the database operations
for the Nifty-500 Live Sentiment Analysis project. The class utilizes DuckDB for database
management and Pandas for DataFrame manipulation, ensuring that the database is properly
set up with the necessary schema and indexes. It also provides methods to insert articles,
update sentiment scores, and retrieve articles for dashboard data.
Classes:
    DatabaseManager:
        A singleton class responsible for managing the database connections and operations.
        It includes methods to set up the database schema, insert and update article data, and
        retrieve articles without sentiment scores as well as dashboard data.
Methods in DatabaseManager:
    __new__(cls, db_path):
        Implements the singleton pattern by ensuring only one instance of DatabaseManager exists.
    __init__(self, db_path):
        Initializes the database manager by setting up a connection pool and creating database
        tables and indexes if they do not already exist.
    _setup_database(self) -> None:
        Creates the required tables (article_data, ticker_meta) and indexes if they are not present.
        This method is automatically called during initialization to maintain schema consistency.
    get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        A context manager that yields a new connection to the DuckDB database.
        Ensures that each connection is properly closed after its usage.
    insert_articles(self, articles_df: pd.DataFrame) -> None:
        Inserts articles into the article_data table using the provided pandas DataFrame.
        Logs the number of successfully inserted records or any errors that occur during the process.
    update_sentiment_scores(self, scores_df: pd.DataFrame) -> None:
        Updates the sentiment scores (negative, positive, neutral, compound) in the article_data table
        for articles present in the provided scores DataFrame, matching on the article id.
    get_articles_without_sentiment(self, batch_size: int = 100) -> Optional[pd.DataFrame]:
        Retrieves a batch of articles from article_data that have not yet been assigned a compound sentiment score.
        Useful for selecting articles that require sentiment analysis.
    get_dashboard_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        Fetches complete datasets from both article_data and ticker_meta tables,
        returning them as a tuple of pandas DataFrames for dashboard generation.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

import duckdb
import pandas as pd

from config import DB_PATH


class DatabaseManager:
    _instance = None
    _db_path = None

    def __new__(cls, db_path=DB_PATH):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._db_path = db_path
        elif db_path != cls._db_path:
            logging.warning(f"Attempting to create DatabaseManager with different path {db_path}, but using existing instance with path {cls._db_path}")
        return cls._instance

    def __init__(self, db_path=DB_PATH):
        if not hasattr(self, 'initialized'):
            self.db_path = self._db_path
            self._setup_database()
            self.initialized = True

    def _setup_database(self) -> None:
        """Initialize database with proper schema and indexes"""
        with self.get_connection() as conn:
            # Create tables with proper indexes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS article_data (
                    id INTEGER PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    date_posted TEXT NOT NULL,
                    source TEXT NOT NULL,
                    article_link TEXT,
                    negative_sentiment FLOAT,
                    positive_sentiment FLOAT,
                    neutral_sentiment FLOAT,
                    compound_sentiment FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_ticker ON article_data(ticker);
                CREATE INDEX IF NOT EXISTS idx_date_posted ON article_data(date_posted);
                CREATE INDEX IF NOT EXISTS idx_sentiment ON article_data(compound_sentiment);
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ticker_meta (
                    ticker TEXT PRIMARY KEY,
                    sector TEXT,
                    industry TEXT,
                    marketCap FLOAT,
                    companyName TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_sector ON ticker_meta(sector);
                CREATE INDEX IF NOT EXISTS idx_industry ON ticker_meta(industry);
            """)

    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get a database connection from the pool"""
        conn = duckdb.connect(str(self.db_path))
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        """Execute a SQL query with optional parameters"""
        try:
            with self.get_connection() as conn:
                if params:
                    conn.execute(query, params)
                else:
                    conn.execute(query)
        except Exception as e:
            logging.error(f"Failed to execute query: {str(e)}")
            raise

    def insert_articles(self, articles_df: pd.DataFrame) -> None:
        """Insert article data with proper error handling"""
        try:
            with self.get_connection() as conn:
                # Register DataFrame temporarily with DuckDB
                conn.register('articles_df', articles_df)
                conn.execute("""
                    INSERT INTO article_data
                        (ticker, headline, date_posted, source, article_link)
                    SELECT ticker, headline, date_posted, source, article_link
                    FROM articles_df
                """)
                conn.unregister('articles_df')  # Cleanup after use
            logging.info(f"Successfully inserted {len(articles_df)} articles")
        except Exception as e:
            logging.error(f"Failed to insert articles: {str(e)}")
            raise

    def update_sentiment_scores(self, scores_df: pd.DataFrame) -> None:
        """Update sentiment scores for articles"""
        try:
            with self.get_connection() as conn:
                # Register DataFrame temporarily with DuckDB
                conn.register('scores_df', scores_df)
                conn.execute("""
                    UPDATE article_data
                    SET
                        negative_sentiment = s.negative,
                        positive_sentiment = s.positive,
                        neutral_sentiment = s.neutral,
                        compound_sentiment = s.compound
                    FROM scores_df s
                    WHERE article_data.id = s.id
                """)
                conn.unregister('scores_df')  # Cleanup after use
            logging.info(f"Successfully updated sentiment scores for {len(scores_df)} articles")
        except Exception as e:
            logging.error(f"Failed to update sentiment scores: {str(e)}")
            raise

    def get_articles_without_sentiment(self, batch_size: int = 100) -> Optional[pd.DataFrame]:
        """Get articles that need sentiment analysis"""
        with self.get_connection() as conn:
            return conn.execute(
                f"SELECT id, headline FROM article_data WHERE compound_sentiment IS NULL LIMIT {batch_size}"
            ).fetchdf()

    def get_dashboard_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Get data needed for dashboard generation"""
        try:
            with self.get_connection() as conn:
                article_data = conn.execute("SELECT * FROM article_data").fetchdf()
                ticker_meta = conn.execute("SELECT * FROM ticker_meta").fetchdf()
                return article_data, ticker_meta
        except Exception as e:
            logging.error(f"Failed to fetch dashboard data: {str(e)}")
            raise
