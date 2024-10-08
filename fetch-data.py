# during multiprocessing, the individual processes do not share memory, hence we return the data from each process and store it in a list and not in a class variable.
# add articles to database and compute sentiment scores for all articles without sentiment scores

import os
import multiprocessing as mp
from typing import Any, Literal, Dict
import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import nsepython as nse
import logging
import duckdb
from huggingface_hub.inference_api import InferenceApi
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class StockDataFetcher:

    def __init__(self, universe) -> None:
        self.universe = universe
        self.news_url = "https://www.google.com/finance/quote"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0"
        }
        self.token = os.getenv("hf_api_key")
        self.sentiment_model = InferenceApi(
            "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
            token=self.token,
        )

    def fetch_tickers(self) -> None:
        """
        Fetches the tickers for the specified Nifty index and saves as csv in .datasets directory.
        """

        # check if a directory datasets exists in root folder if not then create it
        if not os.path.exists("./datasets"):
            os.makedirs("./datasets")

        # Dictionary to store the URLs for the different Nifty indices
        tickers_url_dict: dict = {
            "nifty_500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
            "nifty_200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
            "nifty_100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
            "nifty_50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
        }

        logging.info(f"Downloading Tickers List for {list(tickers_url_dict.keys())}")

        for index_name in tickers_url_dict.keys():
            try:
                ticker_list_url = tickers_url_dict[index_name]
                ticker_list_df = pd.read_csv(ticker_list_url)
                ticker_list_df.to_csv(f"./datasets/{index_name}.csv")
            except Exception as e:
                logging.warning(f"Error fetching tickers for {index_name}: {e}")

    def get_url_content(
        self, ticker: str
    ) -> tuple[None, None, None] | tuple[str, BeautifulSoup, dict]:
        """fetch the news articles for a ticker symbol using request library and parse using bs4. also fetches metadata for a ticker using nse_eq library

        Parameters
        ----------
        ticker : str
            ticker symbol for the stock

        Returns
        -------
        tuple[None, None, None] | tuple[str, BeautifulSoup, dict]
            if news data is found then returns a tuple of ticker, bs4 object and ticker metadata else tuple of none objects.
        """
        _ticker: str = ticker + ":NSE"
        url = f"{self.news_url}/{_ticker}"
        logging.debug(f"Fetching data for {ticker} from {url}")
        try:
            response: requests.Response = requests.get(url, headers=self.header)
            soup: BeautifulSoup = BeautifulSoup(response.content, "lxml")
        except Exception as e:
            logging.warning(f"Error fetching data for {ticker}: {e}")
            return None, None, None
        meta: dict = nse.nse_eq(ticker)
        
        return ticker, soup, meta

    def parse_relative_date(self, date_string):
        """google news contains date info in relative format. This method parses the relative date and turns into absolute dates.

        Parameters
        ----------
        date_string : str
            article date in relative terms

        Returns
        -------
        datetime
            datetime object
        """        
        now = datetime.now()
        parts = date_string.split()

        if len(parts) != 2 and len(parts) != 3:
            return None

        value = int(parts[0]) if parts[0] != "a" else 1
        unit = parts[1]

        if unit.startswith("minute"):
            return now - timedelta(minutes=value)
        elif unit.startswith("hour"):
            return now - timedelta(hours=value)
        elif unit.startswith("day"):
            return now - timedelta(days=value)
        elif unit.startswith("week"):
            return now - timedelta(weeks=value)
        elif unit.startswith("month"):
            return now - relativedelta(months=value)
        else:
            return None

    def ticker_article_fetch(
        self, ticker: str, soup: BeautifulSoup
    ) -> tuple[list, Literal[True]] | tuple[list, Literal[False]]:
        """parse bs4 object to get article metadata for each ticker
        - title
        - date_posted
        - source name
        - article link

        Parameters
        ----------
        ticker : str
            ticker symbol
        soup : BeautifulSoup
            bs4 object containing links

        Returns
        -------
        tuple[list, Literal[True]] | tuple[list, Literal[False]]
            tuple containing list of article meta and bool value indicating whether news articles were found.
        """        
        article_data = []
        news_articles: list = soup.select("div.z4rs2b")

        if not news_articles:
            logging.warning(f"No news found for {ticker}")
            return article_data, True

        ticker_articles_counter = 0

        for link in news_articles:
            art_title: str = link.select_one("div.Yfwt5").text.strip().replace("\n", "")
            date_posted_str: str = link.select_one("div.Adak").text
            date_posted: str = self.parse_relative_date(date_posted_str).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            source: str = link.select_one("div.sfyJob").text
            article_link: str = link.select_one("a").get("href")

            article_data.append([ticker, art_title, date_posted, source, article_link])
            ticker_articles_counter += 1

        logging.debug(f"No of articles: {ticker_articles_counter} for {ticker}")
        return article_data, False

    def ticker_meta_fetch(self, ticker: str, meta: dict) -> list[str]:
        """parse ticker metadata obtained from nse_eq library

        Parameters
        ----------
        ticker : str
            ticker symbol
        meta : dict
            dictionary containing ticker meta

        Returns
        -------
        list
            list containing ticker metadata
        """        
        try:
            sector: str = meta["industryInfo"]["macro"]
            industry: str = meta["industryInfo"]["industry"]
            mCap: float = round(
                (
                    meta["priceInfo"]["previousClose"]
                    * meta["securityInfo"]["issuedSize"]
                )
                / 1e9,
                2,
            )
            companyName: str = meta["info"]["companyName"]
        except KeyError as e:
            logging.warning(f"Error fetching metadata for {ticker}: {e}")
            sector = industry = mCap = companyName = np.nan
        return [ticker, sector, industry, mCap, companyName]

    def process_ticker(self, ticker: str) -> dict[str, Any]:
        """fetch and parse ticker specific news articles and metadata

        Parameters
        ----------
        ticker : str
            ticker symbol

        Returns
        -------
        dict[str, Any]
            dictionary containing ticker news and meta
        """
        try:
            ticker, soup, meta = self.get_url_content(ticker)
            article_data, no_news = self.ticker_article_fetch(ticker, soup)
            if no_news:
                logging.info(f"Skipping meta check for {ticker}")
                return {
                    "ticker": ticker,
                    "article_data": [],
                    "ticker_meta": None,
                    "unavailable": True,
                }
            ticker_meta = self.ticker_meta_fetch(ticker, meta)
            return {
                "ticker": ticker,
                "article_data": article_data,
                "ticker_meta": ticker_meta,
                "unavailable": False,
            }
        except Exception as e:
            logging.warning(f"Error processing {ticker}: {e}")
            return {
                "ticker": ticker,
                "article_data": [],
                "ticker_meta": None,
                "unavailable": True,
            }

    def perform_sentiment_analysis(self, headline: list[str]) -> pd.DataFrame:
        """Perform Sentiment Analysis using HF Inference API. Create a dataframe from the results.

        Parameters
        ----------
        headline : list[str]
            list of article headlines

        Returns
        -------
        pd.DataFrame
            returns sentiment scores in a df with positive negative and compound columns.
        """

        # perform sentiment analysis using the model saved in self.sentiment_model
        results: list[str] = self.sentiment_model(headline)

        # will encounter when HF rate limit is hit.
        if len(results) == 1:
            logging.warning("No sentiment scores available")
            logging.warning(f"results: {results}")
            return pd.DataFrame()

        logging.debug(
            f"Articles for which Sentiment Score is available: {len(results)}"
        )

        # Initialize an empty list to hold the flattened data
        # we will transform a list of list of dictionaries into a list of dictionaries
        flattened_data: list[Dict[str:float]] = []

        for list_item in tqdm(results, desc="Processing Sentiment Analysis"):
            logging.debug(f"List Item: {list_item}")
            score_dict: Dict[str:float] = dict()
            for dict_item in list_item:
                logging.debug(f"Dict Item: {dict_item}")
                sentiment = dict_item["label"]
                sentiment_score = dict_item["score"]
                score_dict[sentiment] = sentiment_score
            flattened_data.append(score_dict)

        # Create the DataFrame
        df = pd.DataFrame(flattened_data)

        # Calculate the compound score
        df.loc[:, "compound"] = df.loc[:, "positive"] - df.loc[:, "negative"]
        return df

    def run(self) -> None:

        # Fetch the tickers
        self.fetch_tickers()
        tickers_df = pd.read_csv(f"./datasets/{self.universe}.csv")
        tickers_list = list(tickers_df["Symbol"])

        # Fetch the news data for the tickers concurrently
        logging.info("Fetching News Data for the tickers")
        with mp.Pool(processes=mp.cpu_count()) as pool:
            ticker_data = list(
                tqdm(
                    pool.imap(self.process_ticker, tickers_list),
                    total=len(tickers_list),
                )
            )


        article_data = []
        ticker_meta = []
        unavailable_tickers = []

        for result in ticker_data:
            if result["unavailable"]:
                unavailable_tickers.append(result["ticker"])
            else:
                article_data.extend(result["article_data"])
                ticker_meta.append(result["ticker_meta"])

        logging.info(f"No news data available for: {unavailable_tickers}")

        articles_df = pd.DataFrame(
            article_data,
            columns=["ticker", "headline", "date_posted", "source", "article_link"],
        )
        # ticker_meta_df = pd.DataFrame(
        #     ticker_meta,
        #     columns=["ticker", "sector", "industry", "marketCap", "companyName"],
        # )

        logging.info("Performing Sentiment Analysis")

        scores_df = self.perform_sentiment_analysis(
            articles_df.headline.astype(str).to_list()
        )

        if not scores_df.empty:
            # if sentiment scores are available, merge the scores with the articles_df and write to database
            articles_df = pd.merge(
                articles_df, scores_df, left_index=True, right_index=True
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

            if not scores_df.empty:
                # insert all data into the table
                logging.info(
                    f"Inserting Sentiment Scores for {len(articles_df)} news articles into the database."
                )
                conn.execute(
                    "INSERT INTO article_data SELECT *, CURRENT_TIMESTAMP FROM articles_df"
                )
            else:
                # insert only article data without sentiment scores
                logging.info(
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
            logging.info(
                f"Inserting Ticker Metadata for {len(ticker_meta)} tickers into the database."
            )
            conn.executemany(
                "INSERT into ticker_meta VALUES (?, ?, ?, ?, ?)", ticker_meta
            )

        # articles_df.to_csv("./datasets/NIFTY_500_Articles.csv")
        # ticker_meta_df.dropna().to_csv("./datasets/ticker_metadata.csv")


if __name__ == "__main__":
    fetcher = StockDataFetcher(universe="nifty_50")
    fetcher.run()
