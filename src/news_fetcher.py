from abc import ABC, abstractmethod
from typing import final, override

from utils import get_webpage_content, parse_date
from bs4 import BeautifulSoup
from loguru import logger

class NewsSource(ABC):
    @abstractmethod
    def get_articles(self, ticker: str) -> list[dict[str, str]]:
        """Fetch articles for a given ticker"""
        pass

GOOGLE_FINANCE = {
    "base_url": "https://www.google.com/finance/quote",
    "article_selector": "div.z4rs2b",
    "headline_selector": "div.Yfwt5",
    "date_selector": "div.Adak",
    "source_selector": "div.sfyJob",
    "link_selector": "a"
}

@final
class GoogleFinanceSource(NewsSource):
    def __init__(self):
        self.base_url: str = "https://www.google.com/finance/quote"
        self.articles: list[dict[str, str]] = []
        self.article_selector: str = "div.z4rs2b"
        self.headline_selector: str = "div.Yfwt5"
        self.date_selector: str = "div.Adak"
        self.source_selector: str = "div.sfyJob"
        self.link_selector: str = "a"

    @override
    def get_articles(self, ticker: str) -> list[dict[str, str]]:   
        try:
            url = f"{self.base_url}/{ticker}:NSE"
            response = get_webpage_content(url)
            if not response:
                logger.warning(f"No response from Google Finance for {ticker}")
                return self.articles
            soup = BeautifulSoup(response, 'html.parser')
            article_elements = soup.select(self.article_selector)

            for article in article_elements:  # Limit to 10 most recent articles
                try:
                    headline: str = article.select_one(self.headline_selector).text.strip().replace("\n", "")
                    relative_date_str: str = article.select_one(self.date_selector).text
                    source: str = article.select_one(self.source_selector).text
                    article_link: str = article.select_one(self.link_selector).get("href")

                    # Convert relative date to actual date
                    date_posted: str | None = parse_date(relative_date_str)

                    self.articles.append({
                        'ticker': ticker,
                        'headline': headline,
                        'date_posted': date_posted,
                        'article_link': article_link,
                        'source': source  # Changed from news_source to source
                    })
                except Exception as e:
                    logger.warning(f"Error parsing Google Finance article for {ticker}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching from Google Finance for {ticker}: {str(e)}")
        return self.articles

@final
class YahooFinanceSource(NewsSource):
    def __init__(self):
        self.base_url = "https://finance.yahoo.com/quote"
        self.articles: list[dict[str, str]] = []
        self.article_selector: str = "div.content.yf-1y7058a"
        self.headline_selector: str = "a h3"
        self.footer_selector: str = "div.publishing.yf-1weyqlp"
        self.link_selector: str = "a"
        
    @override
    def get_articles(self, ticker: str) -> list[dict[str, str]]:
        try:
            url = f"{self.base_url}/{ticker}.NS/news/"
            logger.info(f"Fetching Yahoo Finance articles for {ticker} from {url}")
            response = get_webpage_content(url)
            if not response:
                logger.warning(f"No response from Yahoo Finance for {ticker}")
                return self.articles

            soup = BeautifulSoup(response, 'html.parser')
            article_elements = soup.select(self.article_selector)

            for article in article_elements:
                try:
                    article_link: str = article.select_one(self.link_selector).get("href")
                    # Make sure we have a full URL
                    if not article_link.startswith('http'):
                        article_link = 'https://finance.yahoo.com' + article_link

                    headline = article.select_one(self.headline_selector).text.strip()

                    # Get publisher and date from the footer
                    footer = article.select_one(self.footer_selector)
                    if footer:
                        footer_text = footer.text.strip()
                        parts = footer_text.split("•")
                        source = parts[0].strip() if len(parts) > 0 else 'Yahoo Finance'
                        time_str = parts[1].strip() if len(parts) > 1 else ''
                    else:
                        source = 'Yahoo Finance'
                        time_str = ''

                    # Convert relative time to date
                    date_posted: str = parse_date(time_str)

                    data_dict = {
                        'ticker': ticker,
                        'headline': headline,
                        'date_posted': date_posted,
                        'article_link': article_link,
                        'news_source': source
                    }
                    self.articles.append(data_dict)
                except Exception as e:
                    logger.warning(f"Error parsing Yahoo Finance article for {ticker}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching from Yahoo Finance for {ticker}: {str(e)}")
        return self.articles

if __name__ == "__main__":
    # Example usage
    ticker = "DIXON"
    google_finance_source = GoogleFinanceSource()
    articles = google_finance_source.get_articles(ticker)
    for article in articles:
        print(article)
    # Example usage for Yahoo Finance
    yahoo_finance_source = YahooFinanceSource()
    articles = yahoo_finance_source.get_articles(ticker)
    for article in articles:
        print(article)