import pytest
import datetime
from unittest.mock import MagicMock, patch
import requests

from services.universe_updater import UniverseUpdater

@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.status_code = 200
    return mock

@pytest.fixture
def universe_updater():
    return UniverseUpdater()

def test_setup_database(universe_updater):
    with patch.object(universe_updater.db_manager, 'execute') as mock_execute:
        universe_updater._setup_database()
        
        # Verify the table creation SQL was executed
        mock_execute.assert_any_call(
            """
                CREATE TABLE IF NOT EXISTS universe_constituents (
                    ticker TEXT,
                    universe TEXT,
                    weight FLOAT,
                    entry_date DATE,
                    last_updated TIMESTAMP,
                    PRIMARY KEY (ticker, universe)
                )
            """
        )

def test_get_nse_cookies(universe_updater, mock_response):
    with patch('requests.get', return_value=mock_response) as mock_get:
        mock_response.cookies = {'mock_cookie': 'value'}
        
        universe_updater._get_nse_cookies()
        
        assert universe_updater.nse_cookie == {'mock_cookie': 'value'}
        mock_get.assert_called_with(
            "https://www.nseindia.com/market-data/live-market-indices",
            headers=universe_updater.headers
        )

def test_fetch_universe_constituents(universe_updater, mock_response):
    mock_date = datetime.datetime(2025, 2, 12, 15, 36, 10)
    with patch('requests.get', return_value=mock_response) as mock_get, \
         patch('datetime.datetime') as mock_datetime:
        # Configure datetime mock
        mock_datetime.now.return_value = mock_date
        
        # Mock NSE API response
        mock_response.json.return_value = {
            'data': [
                {'symbol': 'SBIN', 'isinCode': 'INE062A01020', 'weightage': '3.5'},
                {'symbol': 'HDFC', 'isinCode': 'INE001A01036', 'weightage': '4.2'}
            ]
        }
        
        constituents = universe_updater._fetch_universe_constituents('nifty_50')
        
        assert len(constituents) == 2
        assert constituents[0]['ticker'] == 'INE062A01020'  # ISIN code
        assert constituents[0]['universe'] == 'nifty_50'
        assert constituents[0]['weight'] == 3.5
        assert constituents[0]['entry_date'] == '2025-02-12'
        assert constituents[0]['last_updated'] == '2025-02-12 15:36:10'

def test_update_universe_table(universe_updater):
    test_constituents = [
        {
            'ticker': 'INE062A01020',
            'universe': 'nifty_50',
            'weight': 3.5,
            'entry_date': '2025-02-12',
            'last_updated': '2025-02-12 15:36:10'
        }
    ]
    
    with patch.object(universe_updater.db_manager, 'execute') as mock_execute:
        universe_updater._update_universe_table(test_constituents)
        
        # Verify temp table creation and data insertion
        assert mock_execute.called
        calls = mock_execute.call_args_list
        assert any('CREATE TEMP TABLE' in str(call) for call in calls)
        assert any('MERGE INTO' in str(call) for call in calls)

def test_error_handling(universe_updater):
    with patch('requests.get', side_effect=requests.RequestException("API Error")) as mock_get:
        constituents = universe_updater._fetch_universe_constituents('nifty_50')
        assert constituents == []  # Should return empty list on error
        mock_get.assert_called()

def test_update_all_universes(universe_updater):
    with patch.object(universe_updater, '_setup_database') as mock_setup, \
         patch.object(universe_updater, '_fetch_universe_constituents') as mock_fetch, \
         patch.object(universe_updater, '_update_universe_table') as mock_update:
        
        mock_fetch.return_value = [{'ticker': 'INE062A01020', 'universe': 'nifty_50'}]
        
        universe_updater.update_all_universes()
        
        assert mock_setup.called
        assert mock_fetch.call_count == 4  # Called for all universes
        assert mock_update.called