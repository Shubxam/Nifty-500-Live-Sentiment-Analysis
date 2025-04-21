from datetime import datetime, timedelta
from typing import Any

import httpx
import pandas as pd
from dateutil.relativedelta import relativedelta
from loguru import logger
from nse import NSE
from tqdm import tqdm
from config import BATCH_SIZE, SENTIMENT_MODEL_NAME, HEADER

# META_FIELDS = [None] #todo


def get_webpage_content(url: str, custom_header:bool = True) -> str:
    """
    Fetches the content of a webpage given its URL.

    Args:
        url (str): The URL of the webpage to fetch.

    Returns:
        str: The content of the webpage.
    """
    try:
        response = httpx.get(url, headers=HEADER, follow_redirects=True) if custom_header else httpx.get(url, follow_redirects=True)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text

    except httpx.HTTPStatusError as e:
        logger.warning(f"Error {e.response.status_code} for URL: {url}")
        return ""
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
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


def parse_date(date_string: str, relative: bool = True, format: str|None = None) -> str:
    """google news contains date info in relative format. This method parses the relative date and turns into absolute dates.

    Parameters
    ----------
    date_string : str
        article date in relative terms
    relative : bool
        indicates if the date_string is in relative format

    Returns
    -------
    datetime
        datetime object
    """
    now: datetime = datetime.now()
    if relative:
        parts: list[str] = date_string.split()
        
        datetime_object: datetime

        if len(parts) != 2 and len(parts) != 3:
            return ""

        value: int = int(parts[0]) if parts[0] not in ["a", "last"] else 1
        unit: str = parts[1]

        if unit.startswith("minute"):
            datetime_object = now - timedelta(minutes=value)
        elif unit.startswith("hour"):
            datetime_object = now - timedelta(hours=value)
        elif unit.startswith("day"):
            datetime_object = now - timedelta(days=value)
        elif unit.startswith("week"):
            datetime_object = now - timedelta(weeks=value)
        elif unit.startswith("month"):
            datetime_object = now - relativedelta(months=value)
        elif unit.startswith("year"):
            datetime_object = now - relativedelta(years=value)
        elif unit.startswith("yesterday"):
            datetime_object = now - timedelta(days=1)
        elif unit.startswith("today"):
            datetime_object = now
        else:
            logger.warning(f"Unknown date format: {date_string}")
            return ""
    else:
        if not format:
            logger.error("Format string is required for absolute date parsing.")
            return ""
        try:
            datetime_object = datetime.strptime(date_string, format).replace(year=2025)
            datetime_object = datetime_object if datetime_object < now else datetime_object.replace(year=datetime_object.year - 1)
                            
        except Exception as e:
            logger.warning(f"Error parsing date '{date_string}': {e}")
            return ""

    # Format the datetime object to a string
    datetime_format: str = "%Y-%m-%d %H:%M:%S"
    formatted_date: str = datetime_object.strftime(datetime_format)
    return formatted_date


def analyse_sentiment(headlines: list[str]) -> pd.DataFrame:
    """
    Perform Sentiment Analysis using finBERT model. Create a dataframe from the results.

    Parameters
    ----------
    headline : list[str]
        list of article headlines

    Returns
    -------
    pd.DataFrame
        returns sentiment scores in a df with following columns:
        Positive, Negative, Neutral, compound
    """

    from transformers.models.bert import BertForSequenceClassification, BertTokenizer
    from transformers.pipelines import pipeline

    finbert_1: BertForSequenceClassification = BertForSequenceClassification.from_pretrained(
        pretrained_model_name_or_path=SENTIMENT_MODEL_NAME,
        num_labels=3,
        use_safetensors=True,  # Use safe tensors
    )

    tokenizer_1 = BertTokenizer.from_pretrained(pretrained_model_name_or_path=SENTIMENT_MODEL_NAME)

    # set top_k=1 to get the most likely label or top_k=None to get all labels
    # device=-1 means CPU
    nlp_1 = pipeline(
        "sentiment-analysis",
        model=finbert_1,
        tokenizer=tokenizer_1,
        device=-1,
        top_k=None,
        framework="pt",
    )

    try:
        results: list[list[dict[str, str | float]]] = nlp_1(headlines, batch_size=BATCH_SIZE)
    except Exception as e:
        logger.warning(f"Error: {e}")
        return pd.DataFrame()

    # Check if the results are empty or contain only one result
    if len(results) != len(headlines):
        logger.warning(
            f"Sentiment analysis returned {len(results)} results for {len(headlines)} headlines."
        )
        return pd.DataFrame()

    logger.debug(f"Articles for which Sentiment Score is available: {len(results)}")

    # Initialize an empty list to hold the flattened data
    # we will transform a list of list of dictionaries into a list of dictionaries
    flattened_data: list[dict[str, float]] = []

    for news_item_sentiment_list in tqdm(iterable=results, desc="Processing Sentiment"):
        news_item_sentiment_dict = {}
        for individual_label_dict in news_item_sentiment_list:
            news_item_sentiment_dict[individual_label_dict["label"]] = individual_label_dict[
                "score"
            ]
        flattened_data.append(news_item_sentiment_dict)

    # Create the DataFrame
    df = pd.DataFrame(flattened_data)
    df.fillna(0, inplace=True)  # Fill NaN values with 0
    logger.debug(f"DataFrame: {df}")

    # Calculate the compound score
    df.loc[:, "compound"] = (
        df.loc[:, "Positive"]
        .where(df["Positive"] > df["Negative"], -df["Negative"])
        .astype(float)
        .round(4)
    )
    df.loc[:, "compound"] = df.loc[:, "compound"].fillna(0)
    df.loc[:, "compound"] = df.loc[:, "compound"].clip(lower=-1, upper=1)
    return df


if __name__ == "__main__":
    # Example usage
    # url = "https://www.example.com"
    # content = get_webpage_content(url)
    # print(content)

    test_headlines = [
        "ADANIENT Publishes news about quarterly results",
        "Equity markets are down",
        "Market volatility increases",
    ]
    sentiment_results = analyse_sentiment(test_headlines)
    logger.debug(f"Sentiment Results: {sentiment_results}")