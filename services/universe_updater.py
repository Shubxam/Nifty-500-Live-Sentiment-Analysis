import logging
import pandas as pd
from io import StringIO  # Add explicit StringIO import
import requests
from typing import Dict, List
from urllib.parse import urlparse

class UniverseUpdater:
    def __init__(self):
        self.universe_urls = {
            "nifty_50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
            "nifty_100": "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
            "nifty_200": "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv",
            "nifty_500": "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
        }
        self.required_columns = ['Company Name', 'Industry', 'Symbol', 'ISIN Code']

    def _fetch_universe_constituents(self, universe: str) -> pd.DataFrame:
        """
        Fetch constituents for a given universe directly from NSE CSV files
        
        Args:
            universe (str): The universe to fetch (nifty_50, nifty_100, etc.)
            
        Returns:
            pd.DataFrame: DataFrame containing the universe constituents
        """
        try:
            url = self.universe_urls.get(universe)
            if not url:
                logging.error(f"Invalid universe specified: {universe}")
                return pd.DataFrame()
            
            logging.debug(f"Fetching data from URL: {url}")
            
            # Add headers to simulate a browser request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # First download the CSV content
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            logging.debug(f"Successfully downloaded data for {universe}")
            
            # Use StringIO directly from io module
            df = pd.read_csv(StringIO(response.text))
            
            logging.debug(f"Successfully parsed CSV for {universe}. Columns: {df.columns.tolist()}")
            
            # Keep only required columns and add universe column
            available_columns = [col for col in self.required_columns if col in df.columns]
            if not all(col in df.columns for col in self.required_columns):
                missing_cols = set(self.required_columns) - set(df.columns)
                logging.warning(f"Missing columns in {universe} data: {missing_cols}")
            
            # Create a new DataFrame with required columns to avoid SettingWithCopyWarning
            result_df = df[available_columns].copy()
            result_df['universe'] = universe
            
            logging.info(f"Successfully fetched {len(result_df)} constituents for {universe}")
            return result_df
            
        except requests.exceptions.Timeout:
            logging.error(f"Timeout while fetching {universe} constituents")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while fetching {universe} constituents: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Failed to fetch {universe} constituents: {str(e)}")
            return pd.DataFrame()

    def update_all_universes(self) -> Dict[str, pd.DataFrame]:
        """
        Update all universe constituents and return the data as DataFrames
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping universe names to their constituent DataFrames
        """
        logging.debug("Updating all universes...")
        try:
            universe_data = {}
            for universe in self.universe_urls.keys():
                logging.info(f"Processing {universe}...")
                df = self._fetch_universe_constituents(universe)
                if not df.empty:
                    universe_data[universe] = df
                    logging.info(f"Added {len(df)} rows for {universe}")
                else:
                    logging.warning(f"No data fetched for {universe}")
            
            if universe_data:
                logging.info(f"Successfully updated data for {len(universe_data)} universes")
            else:
                logging.warning("No universe data was fetched")
            
            return universe_data
            
        except Exception as e:
            logging.error(f"Failed to update universes: {str(e)}")
            return {}

# TODO: Database functionality will be implemented later

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logging.info("Starting universe updater")
    
    updater = UniverseUpdater()
    universe_data = updater.update_all_universes()
    
    # Print summary of fetched data
    logging.info(f"Fetched data for {len(universe_data)} universes.")
    for universe, df in universe_data.items():
        print(f"\n{universe.upper()} - {len(df)} constituents")
        if not df.empty:
            print(df.head(2))