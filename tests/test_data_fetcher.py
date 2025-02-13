import pytest
import pandas as pd
import datetime
from unittest.mock import MagicMock, patch
import requests

from services.data_fetcher import (
    DataFetcher, 
    NewsSource, 
    GoogleFinanceSource,
    YahooFinanceSource,
    FinologySource
)
from config import UNIVERSE_OPTIONS


class MockNewsSource(NewsSource):
    def fetch_articles(self, ticker: str) -> list:
        return [
            {
                "ticker": ticker,
                "headline": f"Test headline for {ticker}",
                "date_posted": "2024-02-07",
                "article_link": f"http://test.com/{ticker}"
            }
        ]


@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.status_code = 200
    return mock


@pytest.fixture
def google_finance_source():
    return GoogleFinanceSource()


@pytest.fixture
def yahoo_finance_source():
    return YahooFinanceSource()


@pytest.fixture
def finology_source():
    return FinologySource()


@pytest.fixture
def data_fetcher():
    fetcher = DataFetcher("nifty_50")
    fetcher.sources = {
        "test_source": MockNewsSource()
    }
    return fetcher


def test_fetch_tickers(data_fetcher):
    with patch('pandas.read_csv') as mock_read_csv:
        mock_df = pd.DataFrame({'Symbol': ['TEST1', 'TEST2']})
        mock_read_csv.return_value = mock_df
        
        result = data_fetcher.fetch_tickers()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        mock_read_csv.assert_called_with('./datasets/nifty_50.csv')


def test_fetch_articles(data_fetcher):
    result = data_fetcher.fetch_articles('TEST')
    assert len(result) == 1
    assert result[0]['ticker'] == 'TEST'
    assert 'source' in result[0]
    assert result[0]['source'] == 'test_source'


def test_fetch_articles_source_error(data_fetcher):
    def raise_error(*args):
        raise Exception("API Error")
    
    data_fetcher.sources['test_source'].fetch_articles = raise_error
    result = data_fetcher.fetch_articles('TEST')
    assert len(result) == 0


def test_invalid_universe():
    with pytest.raises(ValueError):
        DataFetcher("invalid_universe")


def test_google_finance_fetch_articles(google_finance_source, mock_response):
    mock_date = datetime.datetime(2024, 2, 9)
    with patch('requests.get', return_value=mock_response) as mock_get, \
         patch('datetime.datetime') as mock_datetime:
        # Mock current date to 2024-02-09
        mock_datetime.now.return_value = mock_date
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)
        
        mock_response.text = """
        <div class="z4rs2b">
            <div class="Yfwt5">Test Google Finance Headline</div>
            <div class="Adak">2 days ago</div>
            <div class="sfyJob">Google Finance</div>
            <a href="/article/123"></a>
        </div>
        """
        articles = google_finance_source.fetch_articles("TESTSTOCK")
        
        assert len(articles) > 0
        assert articles[0]['ticker'] == 'TESTSTOCK'
        assert articles[0]['headline'] == 'Test Google Finance Headline'
        assert articles[0]['date_posted'] == '2024-02-07'  # Should be 2 days before mock date
        assert articles[0]['article_link'] == '/article/123'
        assert articles[0]['news_source'] == 'Google Finance'


def test_yahoo_finance_fetch_articles(yahoo_finance_source, mock_response):
    mock_date = datetime.datetime(2024, 2, 9)
    with patch('requests.get', return_value=mock_response) as mock_get, \
         patch('datetime.datetime') as mock_datetime:
        # Configure mock_datetime to work with our date calculations
        mock_datetime.now.return_value = mock_date
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw) if args or kw else mock_date
        
        mock_response.text = """
        <div class="content yf-82qtw3">
            <a href="/news/test-article-123">
                <h3>Test Yahoo Finance News</h3>
            </a>
            <div class="publishing yf-1weyqlp">Reuters • 2 days ago</div>
        </div>
        """
        
        articles = yahoo_finance_source.fetch_articles("TESTSTOCK")
        
        assert len(articles) > 0
        assert articles[0]['ticker'] == 'TESTSTOCK'
        assert articles[0]['headline'] == 'Test Yahoo Finance News'
        assert articles[0]['date_posted'] == '2024-02-07'  # 2 days before mock date
        assert articles[0]['article_link'] == 'https://finance.yahoo.com/news/test-article-123'
        assert articles[0]['news_source'] == 'Reuters'


def test_finology_fetch_articles(finology_source, mock_response):
    # Create a real datetime object for mocking
    mock_date = datetime.datetime(2024, 2, 6)
    
    with patch('requests.get', return_value=mock_response) as mock_get, \
         patch('datetime.datetime') as mock_datetime:
        # Configure mock_datetime
        mock_datetime.now.return_value = mock_date
        # Make datetime constructor work normally
        mock_datetime.side_effect = datetime.datetime
        # Make mock_datetime behave like real datetime for class methods
        mock_datetime.strftime = datetime.datetime.strftime
        mock_datetime.replace = datetime.datetime.replace
        
        mock_response.text = """
        <div id="newsarticles">
            <a class="newslink">
                <span>Test Finology Headline</span>
                <small>6 Feb, 2:28 PM</small>
            </a>
        </div>
        """
        
        articles = finology_source.fetch_articles("TESTSTOCK")
        
        assert len(articles) > 0
        assert articles[0]['ticker'] == 'TESTSTOCK'
        assert articles[0]['headline'] == 'Test Finology Headline'
        assert articles[0]['date_posted'] == '2024-02-06'  # Feb 6, 2024
        assert articles[0]['article_link'] == 'https://ticker.finology.in/company/TESTSTOCK'
        assert articles[0]['news_source'] == 'Finology'


def test_news_source_error_handling():
    sources = [GoogleFinanceSource(), YahooFinanceSource(), FinologySource()]
    
    for source in sources:
        with patch('requests.get', side_effect=requests.RequestException):
            articles = source.fetch_articles("TESTSTOCK")
            assert isinstance(articles, list)
            assert len(articles) == 0  # Should return empty list on error


def test_fetch_metadata(data_fetcher):
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'info': {'companyName': 'Test Company'},
            'metadata': {
                'industry': 'Technology',
                'sector': 'Software'
            },
            'securityInfo': {'marketCap': '1000000'}
        }
        mock_get.return_value = mock_response
        
        result = data_fetcher.fetch_metadata('TEST')
        assert result is not None
        assert result['ticker'] == 'TEST'
        assert result['companyName'] == 'Test Company'
        assert result['sector'] == 'Technology'
        assert result['industry'] == 'Software'
        assert result['marketCap'] == 1000000.0
        assert 'lastUpdated' in result

def test_fetch_metadata_none_response(data_fetcher):
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = None
        mock_get.return_value = mock_response
        
        result = data_fetcher.fetch_metadata('TEST')
        assert result is None

def test_fetch_metadata_error(data_fetcher):
    with patch('requests.get', side_effect=requests.RequestException("API Error")):
        result = data_fetcher.fetch_metadata('TEST')
        assert result is None