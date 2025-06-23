import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sentiment Analysis Configuration
SENTIMENT_MODEL_NAME = 'yiyanghkust/finbert-tone'
BATCH_SIZE = 8

# Web Scraping Configuration
HEADER: dict[str, str] = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# Database Configuration
DB_PATH = os.path.join(BASE_DIR, 'database')
DB_NAME = 'ticker_data.db'

# SQL Queries
CREATE_TABLE = {
    'article_data': """
        CREATE TABLE IF NOT EXISTS article_data (
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
        )
    """,
    'ticker_meta': """
        CREATE TABLE IF NOT EXISTS ticker_meta (
            ticker TEXT PRIMARY KEY NOT NULL,
            sector TEXT NOT NULL,
            industry TEXT NOT NULL,
            mCap REAL,
            companyName TEXT NOT NULL
        )
    """,
}

CREATE_INDEX = {}

INSERT_DATA = {
    'article_data_with_sentiment': """
        INSERT OR REPLACE INTO article_data (
            ticker, headline, date_posted, source, article_link,
            neutral_sentiment, negative_sentiment, positive_sentiment, compound_sentiment, created_at

        )
        SELECT
            ticker, headline, date_posted, source, article_link,
            Neutral, Negative, Positive, compound, CURRENT_TIMESTAMP
        FROM articles_df;
    """,
    'article_data_without_sentiment': """
        INSERT OR REPLACE INTO article_data
        (ticker, headline, date_posted, source, article_link, created_at)
        SELECT
            ticker, headline, date_posted, source, article_link, CURRENT_TIMESTAMP
        FROM articles_df;
    """,
    'ticker_meta': """
        INSERT OR REPLACE INTO ticker_meta
        VALUES (?, ?, ?, ?, ?)
    """,
}

GET_DATA = {
    'ticker_meta': """
        SELECT * FROM ticker_meta
    """,
    'index_constituents': """
        SELECT ticker FROM indices_constituents WHERE {} = true
    """,
    'articles_base': """
        SELECT * FROM article_data WHERE 1=1
    """,
}

# Query building utilities


def build_articles_query(
    has_sentiment: bool = True,
    after_date: str | None = None,
    latest: bool = True,
    limit: int = 20,
) -> tuple[str, list]:
    """
    Build dynamic query for articles with filters and parameters.

    Returns:
        tuple: (query_string, parameters_list)
    """
    query_parts = [GET_DATA['articles_base']]
    params = []

    # Apply sentiment filter
    if not has_sentiment:
        query_parts.append('AND compound_sentiment IS NULL')

    # Apply date filter
    if after_date is not None:
        query_parts.append('AND date_posted >= ?')
        params.append(after_date)

    # Apply ordering
    order_direction = 'DESC' if latest else 'ASC'
    query_parts.append(f'ORDER BY date_posted {order_direction}')

    # Apply limit
    query_parts.append('LIMIT ?')
    params.append(limit)

    return ' '.join(query_parts), params


if __name__ == '__main__':
    # This block is for testing purposes only
    pass
