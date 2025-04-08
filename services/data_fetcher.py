"""This module provides functionality to fetch financial news articles from various sources.""" 

from abc import ABC, abstractmethod
import logging
from typing import Dict, List, Optional
import datetime
from functools import wraps
from typing import Callable

import nsepython as nse
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

from config import DATA_SOURCES, UNIVERSE_OPTIONS


class NewsSource(ABC):
    @abstractmethod
    def fetch_articles(self, ticker: str) -> List[Dict]:
        """Fetch articles for a given ticker"""
        pass


class GoogleFinanceSource(NewsSource):
    def __init__(self):
        self.base_url = "https://www.google.com/finance/quote"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_articles(self, ticker: str) -> List[Dict]:
        articles = []
        try:
            url = f"{self.base_url}/{ticker}:NSE"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            article_elements = soup.select('div.z4rs2b')

            for article in article_elements[:10]:  # Limit to 10 most recent articles
                try:
                    headline = article.select_one("div.Yfwt5").text.strip().replace("\n", "")
                    date_posted_str = article.select_one("div.Adak").text
                    source = article.select_one("div.sfyJob").text
                    article_link = article.select_one("a").get("href")

                    # Convert relative date to actual date
                    date_posted = self._parse_date(date_posted_str)

                    articles.append({
                        'ticker': ticker,
                        'headline': headline,
                        'date_posted': date_posted,
                        'article_link': article_link,
                        'source': source  # Changed from news_source to source
                    })
                except Exception as e:
                    logging.warning(f"Error parsing Google Finance article for {ticker}: {str(e)}")
                    continue

        except Exception as e:
            logging.error(f"Error fetching from Google Finance for {ticker}: {str(e)}")
        return articles

    def _parse_date(self, date_text: str) -> str:
        """Convert relative date text to actual date"""
        try:
            today = datetime.datetime.now()
            date_text = date_text.lower()

            if 'hour' in date_text or 'minute' in date_text or 'just now' in date_text:
                return today.strftime('%Y-%m-%d')
            elif 'yesterday' in date_text:
                return (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'day' in date_text:
                days = int(''.join(filter(str.isdigit, date_text)))
                return (today - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
            else:
                return today.strftime('%Y-%m-%d')
        except Exception:
            return datetime.datetime.now().strftime('%Y-%m-%d')


class YahooFinanceSource(NewsSource):
    def __init__(self):
        self.base_url = "https://finance.yahoo.com/quote"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_articles(self, ticker: str) -> List[Dict]:
        articles = []
        try:
            yahoo_ticker = f"{ticker}.NS"
            url = f"{self.base_url}/{yahoo_ticker}/news"

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            # Find news items with div.content.yf-82qtw3 selector
            news_items = soup.select("div.content.yf-82qtw3")

            for item in news_items[:10]:  # Limit to 10 most recent articles
                try:
                    # Get link and headline
                    article_link = item.select_one("a").get("href")
                    # Make sure we have a full URL
                    if not article_link.startswith('http'):
                        article_link = 'https://finance.yahoo.com' + article_link

                    headline = item.select_one("a h3").text.strip()

                    # Get publisher and date from the footer
                    footer = item.select_one("div.publishing.yf-1weyqlp")
                    if footer:
                        footer_text = footer.text.strip()
                        parts = footer_text.split("•")
                        source = parts[0].strip() if len(parts) > 0 else 'Yahoo Finance'
                        time_str = parts[1].strip() if len(parts) > 1 else ''
                    else:
                        source = 'Yahoo Finance'
                        time_str = ''

                    # Convert relative time to date
                    date_posted = self._parse_date(time_str)

                    articles.append({
                        'ticker': ticker,
                        'headline': headline,
                        'date_posted': date_posted,
                        'article_link': article_link,
                        'news_source': source
                    })
                except Exception as e:
                    logging.warning(f"Error parsing Yahoo Finance article for {ticker}: {str(e)}")
                    continue

        except Exception as e:
            logging.error(f"Error fetching from Yahoo Finance for {ticker}: {str(e)}")
        return articles

    def _parse_date(self, time_str: str) -> str:
        """Convert Yahoo Finance relative time to actual date"""
        try:
            today = datetime.datetime.now()
            time_str = time_str.lower().strip()

            if not time_str:
                return today.strftime('%Y-%m-%d')

            if 'minute' in time_str or 'hour' in time_str:
                return today.strftime('%Y-%m-%d')
            elif 'yesterday' in time_str:
                return (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'day' in time_str:
                days = int(''.join(filter(str.isdigit, time_str)))
                return (today - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
            elif 'week' in time_str:
                weeks = int(''.join(filter(str.isdigit, time_str))) if any(c.isdigit() for c in time_str) else 1
                return (today - datetime.timedelta(weeks=weeks)).strftime('%Y-%m-%d')
            elif 'month' in time_str:
                # For "last month" or "X months ago"
                months = int(''.join(filter(str.isdigit, time_str))) if any(c.isdigit() for c in time_str) else 1
                # Approximate a month as 30 days
                return (today - datetime.timedelta(days=30*months)).strftime('%Y-%m-%d')
            else:
                return today.strftime('%Y-%m-%d')
        except Exception as e:
            logging.warning(f"Error parsing date '{time_str}': {str(e)}")
            return today.strftime('%Y-%m-%d')


class FinologySource(NewsSource):
    def __init__(self):
        self.base_url = "https://ticker.finology.in/company"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_articles(self, ticker: str) -> List[Dict]:
        articles = []
        try:
            url = f"{self.base_url}/{ticker}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.select("a.newslink")

            for item in news_items[:10]:  # Limit to 10 most recent articles
                try:
                    headline = item.select_one("span").text.strip()
                    date_str = item.select_one("small").text.strip()

                    # Convert Finology date format to YYYY-MM-DD
                    date_posted = self._parse_date(date_str)

                    articles.append({
                        'ticker': ticker,
                        'headline': headline,
                        'date_posted': date_posted,
                        'article_link': url,
                        'news_source': 'Finology'
                    })
                except Exception as e:
                    logging.warning(f"Error parsing Finology article for {ticker}: {str(e)}")
                    continue

        except Exception as e:
            logging.error(f"Error fetching from Finology for {ticker}: {str(e)}")
        return articles

    def _parse_date(self, date_text: str) -> str:
        """Convert Finology date format (e.g., '6 Feb, 2:28 PM') to YYYY-MM-DD"""
        try:
            today = datetime.datetime.now()

            # Extract the date part (e.g., "6 Feb" from "6 Feb, 2:28 PM")
            date_part = date_text.split(',')[0].strip()
            day, month = date_part.split()

            # Convert month abbreviations to numbers
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }

            # Handle months as strings directly
            month_num = month_map.get(month, None)
            if month_num is None:
                raise ValueError(f"Invalid month: {month}")

            day_num = int(day)
            year = today.year

            # Create the date
            date = datetime.datetime(year, month_num, day_num)

            # If the date would be in the future, it must be from last year
            if date > today:
                date = date.replace(year=year - 1)

            return date.strftime('%Y-%m-%d')

        except Exception as e:
            logging.warning(f"Error parsing date '{date_text}': {str(e)}")
            return today.strftime('%Y-%m-%d')

class DataFetcher:
    def __init__(self, universe: UNIVERSE_OPTIONS):
        if universe not in ["nifty_50", "nifty_100", "nifty_200", "nifty_500"]:
            raise ValueError(f"Invalid universe: {universe}. Must be one of: nifty_50, nifty_100, nifty_200, nifty_500")
        self.universe = universe
        self.sources = {
            "google_finance": GoogleFinanceSource(),
            "yahoo_finance": YahooFinanceSource(),
            "ticker_finology": FinologySource()
        }

    def fetch_tickers(self) -> pd.DataFrame:
        """Fetch tickers list from NSE"""
        # todo: instead of reading from csv, fetch from database
        try:
            logging.info(f"Fetching {self.universe} tickers")
            df = pd.read_csv(f"./datasets/{self.universe}.csv")
            return df
        except Exception as e:
            logging.error(f"Failed to fetch tickers: {str(e)}")
            raise

    def fetch_articles(self, ticker: str) -> List[Dict]:
        """Fetch articles from all sources for a given ticker"""
        all_articles = []
        for source_name, source in self.sources.items():
            try:
                logging.info(f"Fetching articles from {source_name} for {ticker}")
                articles = source.fetch_articles(ticker)
                # no need for this as sources are already defined during article fetching
                # for article in articles:
                #     article["source"] = source_name
                all_articles.extend(articles)
            except Exception as e:
                logging.error(f"Error in {source_name} for {ticker}: {str(e)}")
        return all_articles


    def fetch_metadata(self, ticker: str) -> Optional[Dict]:
        """Fetch metadata for a ticker with retries"""
        try:
            #todo: use NSE library to fetch metadata

            metadata = {
                'ticker': ticker,
                'companyName': stock_info.get('info', {}).get('companyName', ''),
                'sector': stock_info.get('metadata', {}).get('industry', ''),
                'industry': stock_info.get('metadata', {}).get('sector', ''),
                'marketCap': float(stock_info.get('securityInfo', {}).get('marketCap', 0) or 0),
                'lastUpdated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            return metadata
        
        except Exception as e:
            logging.error(f"Error fetching metadata for {ticker}: {str(e)}")
            return None