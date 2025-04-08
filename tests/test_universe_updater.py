import pytest
import pandas as pd
from io import StringIO
from unittest.mock import patch
from services.universe_updater import UniverseUpdater

@pytest.fixture
def universe_updater():
    return UniverseUpdater()

@pytest.fixture
def sample_csv_data():
    return """Company Name,Industry,Symbol,ISIN Code,Series,Security Code
TCS,IT,TCS,INE467B01029,EQ,532540
HDFC Bank,FINANCIAL SERVICES,HDFCBANK,INE040A01034,EQ,500180"""

def test_fetch_universe_constituents(universe_updater, sample_csv_data):
    # Mock pandas read_csv to return our sample data
    mock_df = pd.read_csv(StringIO(sample_csv_data))
    
    with patch('pandas.read_csv', return_value=mock_df):
        df = universe_updater._fetch_universe_constituents('nifty_50')
        
        # Verify DataFrame structure and content
        assert not df.empty
        assert len(df) == 2
        assert all(col in df.columns for col in universe_updater.required_columns)
        assert 'universe' in df.columns
        assert df['universe'].iloc[0] == 'nifty_50'
        assert df['Symbol'].iloc[0] == 'TCS'
        assert df['ISIN Code'].iloc[0] == 'INE467B01029'

def test_fetch_universe_constituents_error_handling(universe_updater):
    with patch('pandas.read_csv', side_effect=Exception("Network error")):
        df = universe_updater._fetch_universe_constituents('nifty_50')
        assert df.empty

def test_fetch_universe_constituents_invalid_universe(universe_updater):
    df = universe_updater._fetch_universe_constituents('invalid_universe')
    assert df.empty

def test_update_all_universes(universe_updater, sample_csv_data):
    # Mock pandas read_csv to return our sample data for all universes
    mock_df = pd.read_csv(StringIO(sample_csv_data))
    
    with patch('pandas.read_csv', return_value=mock_df):
        universe_data = universe_updater.update_all_universes()
        
        # Verify we got data for all universes
        assert len(universe_data) == 4  # All 4 universes should be present
        
        # Check each universe's data
        for universe, df in universe_data.items():
            assert not df.empty
            assert len(df) == 2  # Our sample data has 2 rows
            assert all(col in df.columns for col in universe_updater.required_columns)
            assert 'universe' in df.columns
            assert df['universe'].iloc[0] == universe

def test_update_all_universes_partial_failure(universe_updater, sample_csv_data):
    mock_df = pd.read_csv(StringIO(sample_csv_data))
    
    def mock_read_csv(url):
        # Simulate failure for nifty_100 only
        if 'nifty100list' in url:
            raise Exception("Network error")
        return mock_df
    
    with patch('pandas.read_csv', side_effect=mock_read_csv):
        universe_data = universe_updater.update_all_universes()
        
        # Should still have data for other universes
        assert len(universe_data) == 3  # One universe failed
        assert 'nifty_100' not in universe_data  # Failed universe
        
        # Check remaining universes have valid data
        for universe, df in universe_data.items():
            assert not df.empty
            assert all(col in df.columns for col in universe_updater.required_columns)