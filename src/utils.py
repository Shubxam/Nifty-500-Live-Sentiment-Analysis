from datetime import datetime, timedelta
from typing import Any

import httpx
import pandas as pd
from dateutil.relativedelta import relativedelta
from loguru import logger
from nse import NSE
from tqdm import tqdm

from config import SENTIMENT_MODEL_NAME, BATCH_SIZE

# META_FIELDS = [None] #todo

def get_webpage_content(url: str) -> str:
    """
    Fetches the content of a webpage given its URL.

    Args:
        url (str): The URL of the webpage to fetch.

    Returns:
        str: The content of the webpage.
    """
    try:
        response = httpx.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text

    except httpx.HTTPStatusError as e:
        logger.warning(f"Error {e.response.status_code}")
        return ""
    except Exception as e:
        logger.warning(f"Error: {e}")
        return ""

def fetch_metadata(ticker: str):
    """
    Fetches metadata for a given ticker.

    Args:
        ticker (str): The stock ticker symbol.

    Returns:
        list: A list containing metadata fields: [ticker, sector, industry, market_cap (in billions), company_name].
              Returns None for fields if data is unavailable.
    """
    # Fetch quote data from NSE
    logger.debug(f"Fetching metadata for {ticker}")
    with NSE("./") as nse:
        meta: dict[str, Any] = nse.quote(ticker)

    # Extract metadata fields
    try:
        sector: str = meta["industryInfo"]["macro"]
        industry: str = meta["industryInfo"]["industry"]
        previousClose: float = meta["priceInfo"]["previousClose"]
        issuedSize: int = meta["securityInfo"]["issuedSize"]
        # Calculate market capitalization in billions
        mCap: float = round(previousClose * issuedSize / 1e9, 2)
        companyName: str = meta["info"]["companyName"]

    except KeyError as e:
        logger.warning(f"KeyError: {e} for ticker {ticker}")
        return None

    return [ticker, sector, industry, mCap, companyName]

def parse_relative_date(date_string: str) -> datetime | None:
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
        now: datetime = datetime.now()
        parts: list[str] = date_string.split()

        if len(parts) != 2 and len(parts) != 3:
            return None

        value: int = int(parts[0]) if parts[0] != "a" else 1
        unit: str = parts[1]

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
        elif unit.startswith("year"):
            return now - relativedelta(years=value)
        elif unit.startswith("yesterday"):
            return now - timedelta(days=1)
        elif unit.startswith("today"):
            return now
        else:
            return None

def analyse_sentiment(headlines: list[str]):
    """
    Perform Sentiment Analysis using finBERT model. Create a dataframe from the results.

    Parameters
    ----------
    headline : list[str]
        list of article headlines

    Returns
    -------
    pd.DataFrame
        returns sentiment scores in a df with positive negative and compound columns.
    """      
        

    from transformers.models.bert import BertTokenizer, BertForSequenceClassification
    from transformers.pipelines import pipeline


    finbert_1: BertForSequenceClassification = BertForSequenceClassification.from_pretrained(
        pretrained_model_name_or_path=SENTIMENT_MODEL_NAME,
        num_labels=3,
        use_safetensors=True  # Use safe tensors
        
    )

    tokenizer_1 = BertTokenizer.from_pretrained(
        pretrained_model_name_or_path=SENTIMENT_MODEL_NAME
    )

    # set top_k=1 to get the most likely label or top_k=None to get all labels
    # device=-1 means CPU
    nlp_1 = pipeline("sentiment-analysis", model=finbert_1, tokenizer=tokenizer_1, device=-1, top_k=None, framework="pt")

    try:
        results: list[list[dict[str, str|float]]] = nlp_1(headlines, batch_size=BATCH_SIZE)
    except Exception as e:
        logger.warning(f"Error: {e}")
        return pd.DataFrame()

    # Check if the results are empty or contain only one result
    if len(results) != len(headlines):
        logger.warning(
            f"Sentiment analysis returned {len(results)} results for {len(headlines)} headlines."
        )
        return pd.DataFrame()

    logger.debug(
        f"Articles for which Sentiment Score is available: {len(results)}"
    )

    # Initialize an empty list to hold the flattened data
    # we will transform a list of list of dictionaries into a list of dictionaries
    flattened_data: list[dict[str,float]] = []

    for news_item_sentiment_list in tqdm(iterable=results, desc="Processing Sentiment"):
        news_item_sentiment_dict = {}
        for individual_label_dict in news_item_sentiment_list:
            news_item_sentiment_dict[individual_label_dict['label']] = individual_label_dict['score']
        flattened_data.append(news_item_sentiment_dict)

    # Create the DataFrame
    df = pd.DataFrame(flattened_data)
    df.fillna(0, inplace=True)  # Fill NaN values with 0
    logger.debug(f"DataFrame: {df}")

    # Calculate the compound score
    df.loc[:, "compound"] = df.loc[:, "Positive"].where(df["Positive"] > df["Negative"], -df["Negative"]).astype(float).round(4)
    df.loc[:, "compound"] = df.loc[:, "compound"].fillna(0)
    df.loc[:, "compound"] = df.loc[:, "compound"].clip(lower=-1, upper=1)
    return df
            

if __name__ == "__main__":
    # Example usage
    # url = "https://www.example.com"
    # content = get_webpage_content(url)
    # print(content)

    test_headlines = ["ADANIENT Publishes news about quarterly results", "Equity markets are down", "Market volatility increases"]
    sentiment_results = analyse_sentiment(test_headlines)
    logger.debug(f"Sentiment Results: {sentiment_results}")

# use when getting news from multiple sites for same ticker
# # ... other imports ...
# import httpx
# from bs4 import BeautifulSoup
# # ...

# # Function to be run by each process
# def worker_process_ticker(ticker_info):
#     ticker, header, news_url = ticker_info # Unpack necessary info
#     # Create a client *inside* the worker process
#     with httpx.Client(headers=header, timeout=10.0) as client:
#         _ticker: str = ticker + ":NSE"
#         url: str = f"{news_url}/{_ticker}"
#         logger.debug(f"Fetching data for {ticker} from {url}")
#         try:
#             response: Response = client.get(url) # Use the process-local client
#             response.raise_for_status()
#             soup: BeautifulSoup = BeautifulSoup(response.text, "lxml")
#             # ... rest of the processing for this ticker ...
#             # Fetch meta, articles etc. (You might need to pass more info or adjust logic)
#             # For simplicity, assuming get_url_content logic is moved/adapted here
#             # meta = fetch_meta(ticker) # Placeholder for meta fetching logic
#             # article_data, no_news = fetch_articles(ticker, soup) # Placeholder

#             # Return results
#             # return { ... }
#         except Exception as e:
#             logger.warning(f"Error processing {ticker} in worker: {e}")
#             # return { "ticker": ticker, "unavailable": True, ... } # Return error state

# # In your main run method:
# class StockDataFetcher:
#     # ... __init__ ...

#     # ... other methods ...

#     def run(self) -> None:
#         # ... fetch tickers ...
#         tickers_list = list(tickers_df["Symbol"])

#         if self.parallel_process:
#             # Prepare data to pass to workers (avoid passing self)
#             worker_args = [(ticker, self.header, self.news_url) for ticker in tickers_list]
#             with mp.Pool(processes=mp.cpu_count()) as pool:
#                 # Use the worker function
#                 ticker_data = list(
#                     tqdm(
#                         pool.imap(worker_process_ticker, worker_args),
#                         total=len(tickers_list),
#                     )
#                 )
#         else:
#              # ... serial processing ...

#         # ... process results ...