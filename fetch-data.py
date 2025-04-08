import logging
import os
from typing import List

import pandas as pd
from tqdm import tqdm

from database.db_manager import DatabaseManager
from services.data_fetcher import DataFetcher
from services.sentiment_analyzer import SentimentAnalyzer
from config import UNIVERSE_OPTIONS, BATCH_SIZE


def main(universe: UNIVERSE_OPTIONS = "nifty_500"):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    try:
        # Initialize services
        db = DatabaseManager()
        fetcher = DataFetcher(universe)
        analyzer = SentimentAnalyzer(os.getenv("HF_API_TOKEN"))
        
        # Fetch tickers
        tickers_df = fetcher.fetch_tickers()
        logging.info(f"Processing {len(tickers_df)} tickers")
        
        # Fetch and store articles
        for ticker in tqdm(tickers_df["Symbol"], desc="Fetching articles"):
            articles = fetcher.fetch_articles(ticker)
            if articles:
                articles_df = pd.DataFrame(articles)
                db.insert_articles(articles_df)
                
            metadata = fetcher.fetch_metadata(ticker)
            if metadata:
                db.update_ticker_metadata(metadata)
        
        # Process sentiment for articles without scores
        while True:
            articles_df = db.get_articles_without_sentiment(BATCH_SIZE)
            if articles_df.empty:
                break
                
            scores_df = analyzer.analyze_headlines(articles_df)
            if not scores_df.empty:
                db.update_sentiment_scores(scores_df)
        
        logging.info("Data fetch and sentiment analysis completed successfully")
        
    except Exception as e:
        logging.error(f"Process failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
