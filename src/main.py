# Note: During multiprocessing, individual processes do not share memory.
# Data is returned from each process and aggregated, not stored in a class variable directly.
# This script fetches stock news articles, adds them to a database,
# and computes sentiment scores for articles that don't have them yet.

import multiprocessing as mp
import os
import sys
from datetime import datetime
from typing import Any, final

import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from loguru import logger
from tqdm import tqdm

import utils as utils
from database import DatabaseManager

# Remove the default logger to prevent duplicate log entries.
logger.remove()
# Define the logging format.
fmt: str = "<white>{time:HH:mm:ss!UTC}({elapsed})</white> - <level> {level} - {message} </level>"
# Add a new logger configuration.
logger.add(sys.stderr, colorize=True, level="INFO", format=fmt, enqueue=True)

@final
class StockDataFetcher:
    """
    Fetches, processes, and stores stock news data and metadata for a given market universe.

    Attributes:
        universe (str): The market universe (e.g., 'nifty_500') to fetch data for.
        news_url (str): The base URL for fetching news from Google Finance.
        parallel_process (bool): Flag to enable/disable multiprocessing.
    """
    def __init__(self, universe: str = "nifty_50") -> None:
        """
        Initializes the StockDataFetcher.

        Args:
            universe (str): The market universe (e.g., 'nifty_500').
        """
        self.universe = universe
        self.news_url = "https://www.google.com/finance/quote"
        self.parallel_process = True # Set to False to disable multiprocessing for debugging.

    def fetch_tickers(self) -> None:
        """
        Fetches the list of tickers for the specified Nifty index from the NSE website
        and saves it as a CSV file in the './datasets' directory. Creates the directory
        if it doesn't exist.
        """

        # Check if the 'datasets' directory exists in the root folder; create it if not.
        if not os.path.exists("./datasets"):
            os.makedirs("./datasets")

        # Dictionary mapping universe names to their corresponding NSE ticker list URLs.
        tickers_url_dict: dict[str, str] = {
            "nifty_500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
            "nifty_200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
            "nifty_100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
            "nifty_50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
        }

        logger.info(f"Downloading Tickers List for {self.universe} from {tickers_url_dict.get(self.universe, 'N/A')}")

        ticker_list_url = tickers_url_dict.get(self.universe)
        if not ticker_list_url:
            logger.error(f"Invalid universe specified: {self.universe}")
            return # Exit if the universe is not found in the dictionary

        try:
            ticker_list_df: pd.DataFrame = pd.read_csv(ticker_list_url)
            # Save the fetched tickers to a CSV file.
            ticker_list_df.to_csv(f"./datasets/{self.universe}.csv", index=False) # Avoid saving pandas index
            logger.info(f"Successfully saved tickers to ./datasets/{self.universe}.csv")
        except Exception as e:
            logger.warning(f"Error fetching tickers for {self.universe}: {e}")

    def parse_articles_from_html(
        self, ticker: str, html_content: str
    ) -> tuple[list[list[str]], bool]:
        """
        Parses the HTML content of a Google Finance page to extract news article metadata.

        Extracts:
        - Title
        - Date Posted (parsed into standard format)
        - Source Name
        - Article Link

        Args:
            ticker (str): The stock ticker symbol.
            html_content (str): The raw HTML content of the news page.

        Returns:
            tuple[list[list[str]], bool]: A tuple containing:
                - A list of lists, where each inner list represents an article's metadata
                  [ticker, title, date_posted_str, source, article_link].
                - A boolean indicating if no news articles were found (True if no news, False otherwise).
        """
        logger.debug(f"Parsing articles for {ticker}")
        article_data: list[list[str]] = []
        soup_obj: BeautifulSoup = BeautifulSoup(html_content, 'html.parser')

        # Select all news article container divs.
        news_articles: ResultSet[Tag] = soup_obj.select("div.z4rs2b")

        logger.debug(f"Number of news articles found for {ticker}: {len(news_articles)}")

        if not news_articles:
            logger.warning(f"No news articles found for {ticker} on the page.")
            return article_data, True

        ticker_articles_counter = 0

        for link in news_articles:
            # Extract article details using CSS selectors.
            art_title: str = link.select_one("div.Yfwt5").text.strip().replace("\n", "")
            date_posted_str: str = link.select_one("div.Adak").text
            # Parse the relative date string (e.g., "2 hours ago") into a datetime object.
            date_posted: datetime | None = utils.parse_relative_date(date_posted_str)
            # Format the datetime object or use current time if parsing fails.
            date_posted_str_formatted: str = date_posted.strftime(
                "%Y-%m-%d %H:%M:%S"
            ) if date_posted is not None else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            source: str = link.select_one("div.sfyJob").text
            article_link: str = link.select_one("a").get("href") # type: ignore[reportAssignmentType]

            # Append the extracted data for the article.
            article_data.append([ticker, art_title, date_posted_str_formatted, source, article_link])
            ticker_articles_counter += 1

        logger.debug(f"{ticker_articles_counter} articles processed for {ticker}")
        return article_data, False

    def process_ticker(self, ticker: str) -> dict[str, str | list[list[str]] | list[str | float] | bool | None]:
        """
        Fetches news page HTML, parses articles, and retrieves metadata for a single ticker.

        Args:
            ticker (str): The stock ticker symbol.

        Returns:
            dict: A dictionary containing:
                - 'ticker': The ticker symbol processed.
                - 'article_data': List of parsed article metadata.
                - 'ticker_meta': List containing ticker metadata [ticker, sector, industry, mCap, companyName] or None.
                - 'unavailable': Boolean indicating if data fetching failed or no news was found.
        """

        logger.info(f"Processing {ticker}")

        url: str = f"{self.news_url}/{ticker+':NSE'}"
        logger.debug(f"Fetching web page for {ticker} from {url}")
        # Get the HTML content of the page.
        content: str = utils.get_webpage_content(url)
        if not content: # Check if content fetching failed
            logger.warning(f"No content retrieved for {ticker} from {url}. Skipping!")
            return {
                "ticker": ticker,
                "article_data": [],
                "ticker_meta": None,
                "unavailable": True,
            }

        # Parse the HTML content to extract articles.
        article_data, no_news = self.parse_articles_from_html(ticker, content)
        if no_news:
            logger.warning(f"No news articles found for {ticker}. Skipping metadata fetch.")
            return {
                "ticker": ticker,
                "article_data": [], # Return empty list as no articles were found
                "ticker_meta": None,
                "unavailable": True,
            }

        # Fetch additional metadata for the ticker (e.g., sector, industry).
        ticker_meta: list[str | float] | None = utils.fetch_metadata(ticker)
        if ticker_meta is None:
            logger.warning(f"Metadata not found for ticker {ticker}.")


        return {
            "ticker": ticker,
            "article_data": article_data,
            "ticker_meta": ticker_meta,
            "unavailable": False,
        }

    def run(self) -> None:
        # Fetch the tickers
        self.fetch_tickers()
        try:
            tickers_df: pd.DataFrame = pd.read_csv(f"./datasets/{self.universe}.csv")
        except FileNotFoundError:
            logger.error(f"Ticker file ./datasets/{self.universe}.csv not found. Run fetch_tickers first or check path.")
            return
        tickers_list: list[str] = list(tickers_df["Symbol"])

        # Fetch and process news data for all tickers.
        logger.info(f"Start Processing {len(tickers_list)} Tickers for {self.universe}")

        ticker_data: list[dict[str, Any]] # Type hint for the list of results

        if not self.parallel_process:
            # Process tickers sequentially.
            logger.info("Processing tickers sequentially.")
            ticker_data = []
            for ticker in tqdm(tickers_list, desc="Processing Tickers"):
                ticker_data.append(self.process_ticker(ticker))
        else:
            # Process tickers in parallel using multiprocessing.
            logger.info(f"Processing tickers in parallel using {mp.cpu_count()} processes.")
            with mp.Pool(processes=mp.cpu_count()) as pool:
                ticker_data = list(
                    tqdm(
                        pool.imap(self.process_ticker, tickers_list),
                        total=len(tickers_list),
                        desc="Processing Tickers (Parallel)"
                    )
                )

        # Aggregate results from processing.
        article_data: list[list[str]] = []
        ticker_meta: list[list[str | float]] = []
        unavailable_tickers: list[str] = []

        # Check if any ticker yielded article data.
        if not any(result.get("article_data") for result in ticker_data if not result.get("unavailable")):
            logger.warning("No news articles found for any ticker after processing. Exiting!")
            return

        # Separate successful results from unavailable ones.
        for result in ticker_data:
            if result["unavailable"]:
                unavailable_tickers.append(result["ticker"])
            else:
                # Ensure article_data and ticker_meta exist before extending/appending
                if result.get("article_data"):
                    article_data.extend(result["article_data"])
                if result.get("ticker_meta"):
                    ticker_meta.append(result["ticker_meta"])


        if unavailable_tickers:
            logger.info(f"Data unavailable or no news found for: {', '.join(unavailable_tickers)}")

        # Create DataFrame for articles if data exists.
        if not article_data:
            logger.warning("No article data collected. Skipping sentiment analysis and database insertion.")
            return

        articles_df = pd.DataFrame(
            article_data,
            columns=["ticker", "headline", "date_posted", "source", "article_link"],
        )

        logger.info("Performing Sentiment Analysis on collected headlines.")
        # Perform sentiment analysis on the headlines.
        sentiment_scores_df = utils.analyse_sentiment(
            articles_df["headline"].astype(str).to_list()
        )

        if not sentiment_scores_df.empty:
            logger.info("Merging sentiment scores with article data.")
            articles_df = pd.merge(
                articles_df, sentiment_scores_df, left_index=True, right_index=True
            )

        # Use DatabaseManager to handle database operations
        db_manager = DatabaseManager("./datasets/ticker_data.db")
        
        if not sentiment_scores_df.empty:
            # Insert articles with sentiment scores
            db_manager.insert_articles(articles_df, has_sentiment=True)
        else:
            # Insert articles without sentiment scores
            db_manager.insert_articles(articles_df, has_sentiment=False)
        
        # Insert ticker metadata
        db_manager.insert_ticker_metadata(ticker_meta)


if __name__ == "__main__":
    # Example usage: Fetch data for Nifty 50.
    # Choose the universe: "nifty_50", "nifty_100", "nifty_200", "nifty_500"
    fetcher = StockDataFetcher(universe="nifty_50")
    fetcher.run()
