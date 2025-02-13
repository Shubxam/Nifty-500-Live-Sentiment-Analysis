from pathlib import Path
from typing import Literal

# Database
DB_PATH = Path("./datasets/ticker_data.db")
BATCH_SIZE = 100  # For batch processing

# Database Tables
UNIVERSE_TABLE = "universe_constituents"
UNIVERSE_TABLE_SCHEMA = """
    ticker TEXT,
    universe TEXT,
    weight FLOAT,
    entry_date DATE,
    last_updated TIMESTAMP,
    PRIMARY KEY (ticker, universe)
"""

# API Settings
HF_MODEL_NAME = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Data Sources
UNIVERSE_OPTIONS = Literal["nifty_50", "nifty_100", "nifty_200", "nifty_500"]
DATA_SOURCES = ["google_finance", "yahoo_finance", "ticker_finology"]

# Dashboard Settings
UPDATE_INTERVAL = "17:30"  # IST
TIMEZONE = "Asia/Kolkata"
CACHE_DURATION = 3600  # 1 hour in seconds

# Update Settings
UNIVERSE_UPDATE_INTERVAL = "09:15"  # IST - Update at market open