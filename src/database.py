# will only do read operations on the database
# todo:  add error handling to get functions

import os
import duckdb as db
import sys
from loguru import logger
from typing import final
from contextlib import contextmanager
from .config import IndexType
import pandas as pd

# remove default logger and add a new one
logger.remove()
fmt: str = "<white>{time:HH:mm:ss!UTC}({elapsed})</white> - <level> {level} - {message} </level>"
logger.add(sys.stderr, colorize=True, level="INFO", format=fmt, enqueue=True)

@final
class DatabaseManager():
    def __init__(self, db_path: str | None = None):
        """Initialize the database manager with the database path."""
        if db_path is None:
            logger.debug("Database path not provided.")
            # Construct path relative to this file's directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, "..", "datasets", "ticker_data.db")

            logger.debug(f"Database path set to: {db_path}")
            self.db_path = db_path
        else:
            self.db_path = db_path
        self.conn: db.DuckDBPyConnection | None = None

    @contextmanager
    def _get_connection(self):
        """Connect to the DuckDB database."""
        logger.debug(f"creating a connection to database.")
        self.conn = db.connect(self.db_path)

        yield self.conn

        self.conn.close()
        logger.debug("Database connection closed.")

    def check_query_result(self, result: pd.DataFrame):
        pass

    def get_articles(self, has_sentiment: bool = True, after_date: str | None = None, index: IndexType | None = None) -> pd.DataFrame:
        """
        Get articles from the database with optional filtering.
        
        Args:
            has_sentiment: If True, only returns articles with sentiment data
            after_date: Filter articles after this date (format: 'YYYY-MM-DD')  
            index: Filter by specific index ('nifty_50', 'nifty_100', 'nifty_200', 'nifty_500')
        """

        with self._get_connection() as conn:
            query = 'Select * from article_data where 1=1'
            sentiment_filter = " AND compound_sentiment IS NOT NULL" if has_sentiment else " AND compound_sentiment IS NULL"
            query += sentiment_filter
            if after_date:
                date_filter = f" AND date_posted > '{after_date}'"
                query += date_filter
            
            if index:
                index_filter = f" AND ticker IN (SELECT ticker FROM indices_constituents WHERE {index}=True)"
                query += index_filter
        
            order_filter = " ORDER BY date_posted DESC"
            query += order_filter

            logger.debug(f"Executing query: {query}")
            result = conn.execute(query).fetchdf()

            if result.empty:
                logger.warning("No articles found with the given filters.")
            return result  

    def get_ticker_metadata(self, index: IndexType | None = None, ticker: str | None = None) -> pd.DataFrame:

        # todo: wrong ticker name and the function will crash

        with self._get_connection() as conn:
            query = "SELECT * FROM ticker_meta where 1=1"
            if index:
                index_filter = f" AND ticker IN (SELECT ticker FROM indices_constituents WHERE {index}=True)"
                query += index_filter
            elif ticker:
                # todo: validate ticker
                ticker_filter = f" AND ticker = '{ticker}'"
                query += ticker_filter
            query += " ORDER BY ticker"
            logger.debug(f"Executing query: {query}")
            try:
                result = conn.execute(query).fetchdf()
            except db.BinderException as e:
                logger.error(f"Error executing query: {e}")
                result = pd.DataFrame()
            return result

    def get_index_constituents(self, index: IndexType) -> pd.Series:

        with self._get_connection() as conn:
            query = f"SELECT ticker FROM indices_constituents WHERE {index}=True"
            logger.debug(f"Executing query: {query}")
            try:
                result: pd.Series = conn.execute(query).fetchdf().loc[:, "ticker"]
            except db.BinderException as e:
                logger.error(f"Error executing query: {e}")
                result = pd.Series()
            return result


if __name__ == "__main__":
    dbm = DatabaseManager()
    articles = dbm.get_articles(after_date="2025-01-01", has_sentiment=True, index="nifty_50")
    print(articles)