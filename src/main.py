# Note: During multiprocessing, individual processes do not share memory.
# Data is returned from each process and aggregated, not stored in a class variable directly.
# This script fetches stock news articles, adds them to a database,
# and computes sentiment scores for articles that don't have them yet.

import multiprocessing as mp
import sys

import pandas as pd
from loguru import logger
from torch import mul
from tqdm import tqdm

import utils as utils
from database import DatabaseManager
from news_fetcher import TickerNewsObject
from pprint import pprint

# Remove the default logger to prevent duplicate log entries.
logger.remove()
# Define the logging format.
fmt: str = "<white>{time:HH:mm:ss!UTC}({elapsed})</white> - <level> {level} - {message} </level>"
# Add a new logger configuration.
logger.add(sys.stderr, colorize=True, level="INFO", format=fmt, enqueue=True)


# Define the worker function outside the class for multiprocessing
def worker_collect_news(ticker_obj: TickerNewsObject) -> list[dict[str, str]]:
    """Collects news for a ticker object and closes its client."""
    try:
        news = ticker_obj.collect_news()
        return news
    except Exception as e:
        logger.error(f"Error collecting news for {ticker_obj.ticker}: {e}")
        return [] # Return empty list on error


def get_news(universe: str = "nifty_50", multiprocess:bool =False) -> None:

    dbm = DatabaseManager()

    # Fetch the tickers
    tickers_df = dbm.get_index_constituents(universe).loc[0:5, "ticker"]
    ticker_objs: list[TickerNewsObject] = [TickerNewsObject(ticker) for ticker in tickers_df]

    # Fetch and process news data for all tickers.
    logger.info(f"Start Processing {len(ticker_objs)} Tickers for {universe}")

    all_articles: list[dict[str, str]] = []  # Renamed to clarify it holds all articles

    if not multiprocess:
        # Process tickers sequentially.
        logger.info("Processing tickers sequentially.")
        for ticker_obj in tqdm(ticker_objs, desc="Processing Tickers"):
            try:
                news = ticker_obj.collect_news()
                all_articles.extend(news)
            except Exception as e:
                    logger.error(f"Error collecting news for {ticker_obj.ticker} (sequential): {e}")
    else:
        # Process tickers in parallel using multiprocessing.
        logger.info(f"Processing tickers in parallel using {mp.cpu_count()} processes.")
        # Use try-with-resources for the pool
        with mp.Pool(processes=mp.cpu_count()) as pool:
            # pool.map applies worker_collect_news to each item in ticker_objs
            # The result is a list of lists (one list of articles per ticker)
            results_list_of_lists = list(
                tqdm(
                    pool.map(worker_collect_news, ticker_objs), # Pass the worker function and the objects
                    total=len(ticker_objs), # Use the correct list length
                    desc="Processing Tickers (Parallel)",
                )
            )
            # Flatten the list of lists into a single list of articles
            all_articles = [article for sublist in results_list_of_lists for article in sublist]

    # --- Aggregation and Processing ---
    logger.success(f"Collected {len(all_articles)} articles in total for {len(ticker_objs)} tickers")
    # Check if any articles were collected
    if not all_articles:
        logger.warning("No news articles found for any ticker after processing. Exiting!")
        return
    
    # Create DataFrame directly from the flattened list
    articles_df = pd.DataFrame(all_articles)
    logger.info(f"Fetched {articles_df.shape[0]} articles from {len(ticker_objs)} tickers")

    # Drop rows where essential info might be missing (e.g., headline)
    articles_df.dropna(subset=['headline'], inplace=True)
    pprint(articles_df.head())

def SentimentAnalyzer():
    # get 200 latest articles without sentiment score from the database
    # and perform sentiment analysis on them
    # and update the database with the sentiment scores
    pass


if __name__ == "__main__":
    # Example usage: Fetch data for Nifty 50.
    # Choose the universe: "nifty_50", "nifty_100", "nifty_200", "nifty_500"
    universe: str = "nifty_50"
    multiprocess: bool = True
    # Call the function to fetch news
    get_news(universe, multiprocess)
