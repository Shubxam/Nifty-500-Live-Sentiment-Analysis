from abc import ABC, abstractmethod
from typing import final, override

from utils import get_webpage_content, parse_date
from bs4 import BeautifulSoup, Tag
from loguru import logger

class NewsSource(ABC):
    @abstractmethod
    def get_articles(self, ticker: str) -> list[dict[str, str]]:
        """Fetch articles for a given ticker"""
        pass

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

            for article in article_elements:
                try:
                    headline_tag: Tag | None = article.select_one(self.headline_selector)
                    date_tag: Tag | None = article.select_one(self.date_selector)
                    source_tag: Tag | None = article.select_one(self.source_selector)
                    link_tag: Tag | None = article.select_one(self.link_selector)

                    if not all([headline_tag, date_tag, source_tag, link_tag]):
                        logger.warning(f"Missing elements in Google Finance article for {ticker}")
                        continue

                    headline: str = headline_tag.text.strip().replace("\\n", "")
                    relative_date_str: str = date_tag.text
                    source: str = source_tag.text
                    article_link_raw = link_tag.get("href")
                    article_link: str = str(article_link_raw) if article_link_raw else ""

                    if not article_link:
                         logger.warning(f"Missing article link in Google Finance article for {ticker}")
                         continue

                    date_posted: str | None = parse_date(relative_date_str)

                    self.articles.append({
                        'ticker': ticker,
                        'headline': headline,
                        'date_posted': date_posted,
                        'article_link': article_link,
                        'source': source
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
            response = get_webpage_content(url)
            if not response:
                logger.warning(f"No response from Yahoo Finance for {ticker}")
                return self.articles

            soup = BeautifulSoup(response, 'html.parser')
            article_elements = soup.select(self.article_selector)

            for article in article_elements:
                try:
                    link_tag: Tag | None = article.select_one(self.link_selector)
                    headline_tag: Tag | None = article.select_one(self.headline_selector)
                    footer_tag: Tag | None = article.select_one(self.footer_selector)

                    if not link_tag or not headline_tag: # Footer is optional
                        logger.warning(f"Missing link or headline in Yahoo Finance article for {ticker}")
                        continue

                    article_link_raw = link_tag.get("href")
                    article_link: str = str(article_link_raw) if article_link_raw else ""
                    if not article_link:
                        logger.warning(f"Missing article link in Yahoo Finance article for {ticker}")
                        continue

                    # Make sure we have a full URL
                    if not article_link.startswith('http'):
                        article_link = 'https://finance.yahoo.com' + article_link

                    headline: str = headline_tag.text.strip()

                    # Get publisher and date from the footer
                    source = 'Yahoo Finance' # Default source
                    time_str = ''
                    if footer_tag:
                        footer_text = footer_tag.text.strip()
                        parts = footer_text.split("•")
                        source = parts[0].strip() if len(parts) > 0 else 'Yahoo Finance'
                        time_str = parts[1].strip() if len(parts) > 1 else ''

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

@final
class FinologySource(NewsSource):
    def __init__(self):
        self.base_url = "https://ticker.finology.in/company"
        self.articles: list[dict[str, str]] = []
        self.article_selector: str = "div#newsarticles a#btnDetails.newslink"
        self.headline_selector: str = "span"
        self.date_selector: str = "small"

    @override
    def get_articles(self, ticker: str) -> list[dict[str, str]]:
        try:
            url = f"{self.base_url}/{ticker}"
            response = get_webpage_content(url, custom_header=False)
            if not response:
                logger.warning(f"No response from Finology for {ticker}")
                return self.articles

            soup = BeautifulSoup(response, 'html.parser')
            article_elements = soup.select(self.article_selector)

            for article in article_elements:
                try:
                    headline_tag: Tag | None = article.select_one(self.headline_selector)
                    date_tag: Tag | None = article.select_one(self.date_selector)

                    if not headline_tag or not date_tag:
                        logger.warning(f"Missing elements in Finology article for {ticker}")
                        continue

                    headline: str = headline_tag.text.strip()
                    date_str: str = date_tag.text.strip()

                    date_posted = parse_date(date_str, relative=False, format="%d %b, %I:%M %p")

                    self.articles.append({
                        'ticker': ticker,
                        'headline': headline,
                        'date_posted': date_posted,
                        'article_link': url, # Finology links point back to the main page
                        'news_source': 'Finology'
                    })
                except Exception as e:
                    logger.warning(f"Error parsing Finology article for {ticker}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching from Finology for {ticker}: {str(e)}")
        return self.articles

class TickerNewsObject():
    def __init__(self, ticker: str) -> None:
        self.ticker: str = ticker
        self.news_sources: dict[str, NewsSource] = {
            "GoogleFinance": GoogleFinanceSource(),
            "YahooFinance": YahooFinanceSource(),
            "Finology": FinologySource()
        }
        self.articles: list[dict[str, str]] = []

    def collect_news(self) -> list[dict[str, str]]:
        for source_name, source_obj in self.news_sources.items():
            logger.info(f"Fetching articles from {source_name} for {self.ticker}")
            # Pass the shared client to the source object
            fetched_articles: list[dict[str, str]] = source_obj.get_articles(self.ticker)
            logger.info(f"Fetched {len(fetched_articles)} articles from {source_name} for {self.ticker}")
            if fetched_articles:
                self.articles.extend(fetched_articles)
        logger.info(f"Collected {len(self.articles)} articles in total for {self.ticker}")
        return self.articles


if __name__ == "__main__":

    ticker = "SBIN"

    ticker_news = TickerNewsObject(ticker)
    articles = ticker_news.collect_news()
    logger.info(f"Collected {len(articles)} articles for {ticker}")