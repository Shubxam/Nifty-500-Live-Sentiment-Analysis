# during multiprocessing, the individual processes do not share memory, hence we return the data from each process and store it in a list and not in a class variable.


import multiprocessing as mp
import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import nsepython as nse
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

from huggingface_hub.inference_api import InferenceApi
import os


class StockDataFetcher:

    def __init__(self, universe) -> None:
        self.universe = universe
        self.news_url = "https://www.google.com/finance/quote"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0"
        }
        self.special_symbols = {
            "L&TFH": "SCRIP-220350",
            "M&M": "SCRIP-100520",
            "M&MFIN": "SCRIP-132720",
        }

        token = os.getenv("hf_api_key")

        self.sentiment_model = InferenceApi("ProsusAI/finbert", token=token)

    def fetch_tickers(self):
        tickers_url_dict = {
            "nifty_500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
            "nifty_200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
            "nifty_100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
            "nifty_50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
        }
        logging.info(f"Downloading {self.universe} Tickers")
        tickers_url = tickers_url_dict[self.universe]
        universe_tickers = pd.read_csv(tickers_url)
        universe_tickers.to_csv(f"./datasets/{self.universe}.csv")
        return universe_tickers[["Symbol", "Company Name"]]

    def get_url_content(self, ticker):
        _ticker = ticker + ":NSE"
        url = f"{self.news_url}/{_ticker}"
        logging.info(f"Fetching data for {ticker} from {url}")
        response = requests.get(url, headers=self.header)
        soup = BeautifulSoup(response.content, "lxml")
        meta = nse.nse_eq(ticker)
        return ticker, soup, meta

    def ticker_article_fetch(self, ticker, soup):
        article_data = []
        news_articles = soup.select("div.z4rs2b")
        if not news_articles:
            logging.info(f"No news found for {ticker}")
            return article_data, True
        ticker_articles_counter = 0
        for link in news_articles:
            art_title = link.select_one("div.Yfwt5").text.strip().replace("\n", "")
            date_posted = link.select_one("div.Adak").text
            source = link.select_one("div.sfyJob").text
            article_link = link.select_one("a").get("href")

            article_data.append([ticker, art_title, date_posted, source, article_link])
            ticker_articles_counter += 1
        logging.info(f"No of articles: {ticker_articles_counter} for {ticker}")
        return article_data, False

    def ticker_meta_fetch(self, ticker, meta):
        try:
            sector = meta["industryInfo"]["macro"]
            industry = meta["industryInfo"]["industry"]
            mCap = round(
                (
                    meta["priceInfo"]["previousClose"]
                    * meta["securityInfo"]["issuedSize"]
                )
                / 1e9,
                2,
            )
            companyName = meta["info"]["companyName"]
        except KeyError as e:
            logging.warning(f"Error fetching metadata for {ticker}: {e}")
            sector = industry = mCap = companyName = np.nan
        return [ticker, sector, industry, mCap, companyName]

    def process_ticker(self, ticker):
        try:
            ticker, soup, meta = self.get_url_content(ticker)
            article_data, no_news = self.ticker_article_fetch(ticker, soup)
            if no_news:
                print(f"Skipping meta check for {ticker}")
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

    def perform_sentiment_analysis(self, headline: list[str]):
        results: list[list[dict[str:float]]] = self.sentiment_model(headline)

        # Initialize an empty list to hold the flattened data
        flattened_data: list = []

        # Loop through each entry in the data
        for entry in results:
            # Create a dictionary for each entry with labels as keys and scores as values
            score_dict = {item["label"]: item["score"] for item in entry}
            flattened_data.append(score_dict)

        # Create the DataFrame
        df = pd.DataFrame(flattened_data)

        # Calculate the compound score
        df.loc[:, "compound"] = df.loc[:, "positive"] - df.loc[:, "negative"]
        return df

    def run(self):
        tickers_df = self.fetch_tickers()
        tickers_list = list(tickers_df["Symbol"])

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
            article_data, columns=["Ticker", "Headline", "Date", "Source", "Link"]
        )
        ticker_meta_df = pd.DataFrame(
            ticker_meta,
            columns=["Ticker", "Sector", "Industry", "Market Cap", "Company Name"],
        )

        logging.info("Performing Sentiment Analysis")
        scores_df = self.perform_sentiment_analysis(
            articles_df.Headline.astype(str).to_list()
        )
        articles_df = pd.merge(
            articles_df, scores_df, left_index=True, right_index=True
        )

        articles_df.to_csv("./datasets/NIFTY_500_Articles.csv")
        ticker_meta_df.dropna().to_csv("./datasets/ticker_metadata.csv")


if __name__ == "__main__":
    fetcher = StockDataFetcher(universe="nifty_50")
    fetcher.run()
