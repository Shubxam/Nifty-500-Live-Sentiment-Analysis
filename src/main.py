# during multiprocessing, the individual processes do not share memory, hence we return the data from each process and store it in a list and not in a class variable.
# add articles to database and compute sentiment scores for all articles without sentiment scores

from bs4.element import ResultSet, Tag
from loguru import logger
import multiprocessing as mp
import os
from datetime import datetime
from typing import Literal, final
import sys

import duckdb
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import utils as utils

# remove default logger, else will get duplicate logs
logger.remove()
fmt:str = "<white>{time:HH:mm:ss!UTC}({elapsed})</white> - <level> {level} - {message} </level>"
logger.add(sys.stderr, colorize=True, level="INFO", format=fmt, enqueue=True)

@final
class StockDataFetcher:
    def __init__(self, universe: str) -> None:
        self.universe = universe
        self.news_url = "https://www.google.com/finance/quote"        
        self.parallel_process = True

    def fetch_tickers(self) -> None:
        """
        Fetches the tickers for the specified Nifty index and saves as csv in .datasets directory.
        """

        # check if a directory datasets exists in root folder if not then create it
        if not os.path.exists("./datasets"):
            os.makedirs("./datasets")

        # Dictionary to store the URLs for the different Nifty indices
        tickers_url_dict: dict[str, str] = {
            "nifty_500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
            "nifty_200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
            "nifty_100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
            "nifty_50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
        }

        logger.info(f"Downloading Tickers List for {tickers_url_dict[self.universe]}")

        ticker_list_url = tickers_url_dict[self.universe]
        try:
            ticker_list_df: pd.DataFrame = pd.read_csv(ticker_list_url)
            ticker_list_df.to_csv(f"./datasets/{self.universe}.csv")
        except Exception as e:
            logger.warning(f"Error fetching tickers for {self.universe}: {e}")

    def parse_articles_from_html(
        self, ticker: str, html_content: str
    ) -> tuple[list[list[str]], Literal[True] | Literal[False]]:
        """parse bs4 object to get article metadata for each ticker
        - title
        - date_posted
        - source name
        - article link

        Parameters
        ----------
        ticker : str
            ticker symbol
        soup : str
            HTML content containing links

        Returns
        -------
        tuple[list, Literal[True]] | tuple[list, Literal[False]]
            tuple containing list of article meta and bool value indicating whether news articles were found.
        """
        logger.debug(f"Fetching articles for {ticker}")
        article_data: list[list[str]] = []
        soup_obj: BeautifulSoup = BeautifulSoup(html_content, 'html.parser')
        news_articles: ResultSet[Tag] = soup_obj.select("div.z4rs2b")

        logger.debug(f"Number of news-articles found: {len(news_articles)}")

        if not news_articles:
            logger.warning(f"No news found for {ticker}")
            return article_data, True

        ticker_articles_counter = 0

        for link in news_articles:
            art_title: str = link.select_one("div.Yfwt5").text.strip().replace("\n", "")
            date_posted_str: str = link.select_one("div.Adak").text
            date_posted: datetime | None = utils.parse_relative_date(date_posted_str)
            date_posted_str_formatted: str = date_posted.strftime(
                "%Y-%m-%d %H:%M:%S"
            ) if date_posted is not None else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            source: str = link.select_one("div.sfyJob").text
            article_link: str = link.select_one("a").get("href")

            article_data.append([ticker, art_title, date_posted_str_formatted, source, article_link])
            ticker_articles_counter += 1

        logger.debug(f"{ticker_articles_counter} articles processed for {ticker}")
        return article_data, False

    def process_ticker(self, ticker: str) -> dict[str, str | list[list[str]] | list[str | float | None] | bool | None]:
        """fetch and parse ticker specific news articles and metadata

        Parameters
        ----------
        ticker : str
            ticker symbol

        Returns
        -------
        dict[str, str | list[str] | None]
            dictionary containing ticker news and meta
        """
        
        logger.info(f"Processing {ticker}")

        url: str = f"{self.news_url}/{ticker+':NSE'}"
        logger.debug(f"Fetching web page for {ticker} from {url}")
        content: str = utils.get_webpage_content(url)
        if len(content) == 0:
            logger.warning(f"No content found for {ticker}. Skipping!")
            return {
                "ticker": ticker,
                "article_data": [],
                "ticker_meta": None,
                "unavailable": True,
            }
            
        # parse the content using bs4
        article_data, no_news = self.parse_articles_from_html(ticker, content)
        if no_news:
            logger.warning(f"No news articles found for {ticker}. Skipping meta check!")
            return {
                "ticker": ticker,
                "article_data": [],
                "ticker_meta": None,
                "unavailable": True,
            }

        ticker_meta: list[str | float | None] = utils.fetch_metadata(ticker)
        

        return {
            "ticker": ticker,
            "article_data": article_data,
            "ticker_meta": ticker_meta,
            "unavailable": False,
        }

    def run(self) -> None:
        # Fetch the tickers
        self.fetch_tickers()
        tickers_df: pd.DataFrame = pd.read_csv(f"./datasets/{self.universe}.csv")
        tickers_list: list[str] = list(tickers_df["Symbol"])

        # Fetch the news data for the tickers concurrently
        logger.info("Start Processing Tickers")

        if not self.parallel_process:
            ticker_data = []
            for ticker in tickers_list:
                ticker_data.append(self.process_ticker(ticker))
        else:
            with mp.Pool(processes=mp.cpu_count()) as pool:
                ticker_data = list(
                    tqdm(
                        pool.imap(self.process_ticker, tickers_list),
                        total=len(tickers_list),
                    )
                )

        article_data: list[list[str]] = []
        ticker_meta: list[list[str | float | None]] = []
        unavailable_tickers: list[str] = []

        # check if article data is available for atleast one ticker
        if not any(result["article_data"] for result in ticker_data):
            logger.warning("No news articles found for any ticker. Exiting!")
            return

        for result in ticker_data:
            if result["unavailable"]:
                unavailable_tickers.append(result["ticker"])
            else:
                article_data.extend(result["article_data"])
                ticker_meta.append(result["ticker_meta"])

        logger.info(f"No news data available for: {unavailable_tickers}")

        articles_df = pd.DataFrame(
            article_data,
            columns=["ticker", "headline", "date_posted", "source", "article_link"],
        )

        logger.info("Performing Sentiment Analysis")

        sentiment_scores_df = utils.analyse_sentiment(
            articles_df.headline.astype(str).to_list()
        )

        if not sentiment_scores_df.empty:
            # if sentiment scores are available, merge the scores with the articles_df and write to database
            articles_df = pd.merge(
                articles_df, sentiment_scores_df, left_index=True, right_index=True
            )

        with duckdb.connect("./datasets/ticker_data.db") as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS article_data (
                            ticker TEXT,
                            headline TEXT,
                            date_posted TEXT,
                            source TEXT,
                            article_link TEXT,
                            negative_sentiment FLOAT DEFAULT NULL,
                            positive_sentiment FLOAT DEFAULT NULL,
                            neutral_sentiment FLOAT DEFAULT NULL,
                            compound_sentiment FLOAT DEFAULT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )"""
            )

            if not sentiment_scores_df.empty:
                # insert all data into the table
                logger.info(
                    f"Inserting Sentiment Scores for {len(articles_df)} news articles into the database."
                )
                conn.execute(
                    "INSERT INTO article_data SELECT *, CURRENT_TIMESTAMP FROM articles_df"
                )
            else:
                # insert only article data without sentiment scores
                logger.info(
                    f"Inserting Article Data for {len(articles_df)} news articles into the database. No Sentiment Scores available."
                )
                conn.execute(
                    "INSERT INTO article_data (ticker, headline, date_posted, source, article_link, created_at) SELECT *, CURRENT_TIMESTAMP FROM articles_df"
                )

            # create a new table for storing ticker metadata
            conn.execute(
                "CREATE or REPLACE TABLE ticker_meta (ticker TEXT, sector TEXT, industry TEXT, mCap REAL, companyName TEXT)"
            )

            # insert ticker metadata into the table, this table will be replaced on every run.
            logger.info(
                f"Inserting Ticker Metadata for {len(ticker_meta)} tickers into the database."
            )
            conn.executemany(
                "INSERT into ticker_meta VALUES (?, ?, ?, ?, ?)", ticker_meta
            )

if __name__ == "__main__":
    fetcher = StockDataFetcher(universe="nifty_50")
    fetcher.run()
