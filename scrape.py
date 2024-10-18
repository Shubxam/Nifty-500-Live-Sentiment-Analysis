# fetch the articles from the news providers for tickers and store them in the database.
# only working with nifty50 tickers for now.

import requests
from bs4 import BeautifulSoup
import duckdb as db
import logging
import concurrent.futures
import itertools

news_providers = {
    "google_finance": {
        "base_url": "https://www.google.com/finance/quote/{}:NSE",
        "schema": {
            "base_selector": "div.yY3Lee",
            "title": "div.Yfwt5",
            "content": None,
            "date_posted": "div.Adak",
            "source": "div.sfyJob",
            "link": "a",
        }
    },
    "yahoo_finance": {
        "base_url": "https://finance.yahoo.com/quote/{}.NS",
        "schema": {
            "base_selector": "div.stream-item.yf-ovk92u",
            "title": "h1",
            "content": "p",
            "date_posted": "time",
            "source": "span",
            "link": "a",
        }
    },
    "finology_ticker": {
        "base_url": "https://ticker.finology.in/company/{}",
        "schema": {
            "base_selector": "div",
            "title": "h1",
            "content": "p",
            "date_posted": "time",
            "source": "span",
            "link": "a",
        }
    },
    # "screener": {
    #     "base_url": "https://www.screener.in/company/",
    #     "schema": {
    #         "base_selector": "div",
    #         "title": "h1",
    #         "content": "p",
    #         "date_posted": "time",
    #         "source": "span",
    #         "link": "a",
    #     }
    # },
}

def fetch_soup(url: str):
    header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0"
    }
    response = requests.get(url, headers=header)
    soup: BeautifulSoup = BeautifulSoup(response.content, "lxml")
    return soup

def process_ticker(ticker: str):

    urls = [provider['base_url'].format(ticker) for provider in news_providers.values()]
    header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0"
    }
    response = requests.get(url, headers=header)
    soup: BeautifulSoup = BeautifulSoup(response.content, "lxml")

if __name__ == '__main__':
    
    # fetch the tickers from the database
    with db.connect('./datasets/ticker_data.db', read_only=True) as conn:
        tickers_meta = conn.execute("SELECT * FROM ticker_meta;").df()
    
    tickers_list = tickers_meta['ticker'].tolist()
    
    
    # fetch the articles for each ticker from the news providers concurrently, where each thread will process 1 ticker across all sources
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_ticker, tickers_list)
        
        
        # for ticker in tickers_list:
        #     for provider in news_providers:
        #         url = news_providers[provider]["base_url"].format(ticker)
        #         response = requests.get(url)
        #         soup = BeautifulSoup(response.content, 'html.parser')
        #         schema = news_providers[provider]["schema"]
        #         base_selector = schema["base_selector"]
        #         title = soup.find(base_selector, schema["title"]).text
        #         content = soup.find(base_selector, schema["content"]).text
        #         date_posted = soup.find(base_selector, schema["date_posted"]).text
        #         source = soup.find(base_selector, schema["source"]).text
        #         link = soup.find(base_selector, schema["link"]).text
        #         print(title, content, date_posted, source, link)
        #         # store the articles in the database
        #         with db.connect('./datasets/ticker_data.db') as conn:
        #             conn.execute("INSERT INTO news_data VALUES (?, ?, ?, ?, ?, ?);", (ticker, title, content, date_posted, source, link))