import multiprocessing as mp
import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

# sentiment analysis libraries
import nltk
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nsepython as nse



# list to store article data
article_data = []

# list to store meta data
ticker_meta = []

# list to store tickers for which data is unavailable
unavailable_tickers = []


def fetching_data(universe):

    tickers_url_dict = {
        'nifty_500': 'https://archives.nseindia.com/content/indices/ind_nifty500list.csv',
        'nifty_200': 'https://archives.nseindia.com/content/indices/ind_nifty200list.csv',
        'nifty_100': 'https://archives.nseindia.com/content/indices/ind_nifty100list.csv',
        'nifty_50': 'https://archives.nseindia.com/content/indices/ind_nifty50list.csv'
    }

    # NIFTY URLS
    print(f"Downloading {universe} Tickers")

    tickers_url = tickers_url_dict[universe]


    universe_tickers = pd.read_csv(tickers_url)
    universe_tickers.to_csv(f"./datasets/{universe}.csv")

    # Read CSV & create a tickers df
    tickers_df = universe_tickers[["Symbol", "Company Name"]]
    
    return tickers_df


# function to fetch news and meta concurrently
def get_url_content(ticker):

    _ticker = special_symbols[ticker] if ticker in special_symbols.keys() else ticker
    url = f"{news_url}/{_ticker}"
    print(f"Fetching data for {ticker} from {url}")
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.content, "lxml")
    meta = nse.nse_eq(ticker)
    return ticker, soup, meta


# function to parse news data and create a df
def ticker_article_fetch(ticker, soup):
    news_articles = soup.select("div.z4rs2b")
    if len(news_articles) == 0:
        print("No news found for {}".format(ticker))
        return True
    ticker_articles_counter = 0
    for link in news_articles:
        art_title = link.select_one("div.Yfwt5").text.replace("\n", "")
        date_posted = link.select_one("div.Adak").text
        source = link.select_one("div.sfyJob").text
        article_link = link.select_one("a").get("href")
        article_data.append([ticker, art_title, date_posted, source, article_link])
        ticker_articles_counter += 1
    print("No of articles: {} for {}".format(ticker_articles_counter, ticker))


# function to parse meta data and create a df
def ticker_meta_fetch(i, ticker, meta):
    try:
        sector = meta["industryInfo"]["macro"]
    except KeyError:
        print("{} sector info is not available".format(ticker))
        sector = np.nan
        industry = np.nan
        mCap = np.nan
        companyName = np.nan
        ticker_meta.append([ticker, sector, industry, mCap, companyName])
        return True
    try:
        industry = meta["industryInfo"]["industry"]
    except KeyError:
        print("{} industry info is not available".format(ticker))
        industry = np.nan
        mCap = np.nan
        companyName = np.nan
        ticker_meta.append([ticker, sector, industry, mCap, companyName])
        return True
    try:
        mCap = round(
            (meta["priceInfo"]["previousClose"] * meta["securityInfo"]["issuedSize"])
            / 1000000000,
            2,
        )  # Rounding MCap off to Billion
    except KeyError:
        print("{} mCap data is not available".format(ticker))
        mCap = np.nan
        companyName = np.nan
        ticker_meta.append([ticker, sector, industry, mCap, companyName])
        return True
    try:
        companyName = meta["info"]["companyName"]
    except KeyError:
        print("{} company Name is not available".format(ticker))
        companyName = np.nan
        ticker_meta.append([ticker, sector, industry, mCap, companyName])
        return True
    ticker_meta.append([ticker, sector, industry, mCap, companyName])


def process_tickers(ticker):
    ticker, soup, meta = get_url_content(ticker)
    ticker_article_response = ticker_article_fetch(ticker, soup)
    if ticker_article_response:
        unavailable_tickers.append(ticker)
        print("skipping meta check for {}".format(ticker))
        return
    ticker_meta_response = ticker_meta_fetch(ticker, meta)
    if ticker_meta_response:
        unavailable_tickers.append(ticker)


if __name__ == "__main__":
    
    nltk.downloader.download("vader_lexicon")

    # News URL
    news_urls = {
        "ticker_finology": "https://ticker.finology.in/company",
        "google_finance": "https://www.google.com/finance/quote",
        "yahoo_finance": "https://finance.yahoo.com/quote",
    }

    special_symbols = {
        "L&TFH": "SCRIP-220350",
        "M&M": "SCRIP-100520",
        "M&MFIN": "SCRIP-132720",
    }

    news_url = news_urls["google_finance"]

    # Header for sending requests
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0"
    }

    # Set universe
    universe = 'nifty_50'
    
    # fetch tickers
    tickers_df = fetching_data(universe)
    tickers_list = list(tickers_df["Symbol"])
    
    # fetch news and meta data concurrently
    with mp.Pool(processes=mp.cpu_count()) as p:
        p.map(process_tickers, tqdm(tickers_list))

    print(f"No news data available for: {unavailable_tickers}")

    # create df from article_data
    articles_df = pd.DataFrame(
        article_data, columns=["Ticker", "Headline", "Date", "Source", "Link"]
    )

    # create df from metadata
    ticker_meta_df = pd.DataFrame(
        ticker_meta,
        columns=["Ticker", "Sector", "Industry", "Market Cap", "Company Name"],
    )

    # Sentiment Analysis
    print("Performing Sentiment Analysis")
    vader = SentimentIntensityAnalyzer()

    # import custom lexicon dictionary
    lex_fin = pd.read_csv("./datasets/lexicon_dictionary.csv")
    # create a dictionary from df columns
    lex_dict = dict(zip(lex_fin.word, lex_fin.sentiment_score))
    # set custom lexicon dictionary as default to calculate sentiment analysis scores
    vader.lexicon = lex_dict

    # Perform sentiment Analysis on the Headline column of all_news_df
    # It returns a dictionary, transform it into a list
    art_scores_df = pd.DataFrame(
        articles_df["Headline"].apply(vader.polarity_scores).to_list()
    )

    # Merge articles_df with art_scores_df
    # merging on index, hence both indices should be same
    art_scores_df = pd.merge(
        articles_df, art_scores_df, left_index=True, right_index=True
    )

    # export article data to csv file
    art_scores_df.to_csv("./datasets/NIFTY_500_Articles.csv")

    # remove null values
    ticker_metadata = ticker_meta_df.dropna()

    # export ticker data to csv file
    ticker_metadata.to_csv("./datasets/ticker_metadata.csv")
