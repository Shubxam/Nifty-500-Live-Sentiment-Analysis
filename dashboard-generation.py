import logging
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import pytz

from config import TIMEZONE, CACHE_DURATION
from database.db_manager import DatabaseManager


class DashboardGenerator:
    def __init__(self):
        self.db = DatabaseManager()
        self.cache_file = Path("./cache/dashboard_data.json")
        self.cache_file.parent.mkdir(exist_ok=True)
    
    def _get_cached_data(self) -> Optional[Dict]:
        """Get cached data if it's still valid"""
        if not self.cache_file.exists():
            return None
            
        try:
            with open(self.cache_file) as f:
                cache = json.load(f)
            
            cache_time = datetime.fromtimestamp(cache["timestamp"])
            if (datetime.now() - cache_time).total_seconds() < CACHE_DURATION:
                return cache["data"]
        except Exception as e:
            logging.error(f"Error reading cache: {str(e)}")
        return None
    
    def _cache_data(self, data: Dict) -> None:
        """Cache dashboard data"""
        try:
            cache = {
                "timestamp": datetime.now().timestamp(),
                "data": data
            }
            with open(self.cache_file, "w") as f:
                json.dump(cache, f)
        except Exception as e:
            logging.error(f"Error caching data: {str(e)}")
    
    def prepare_data(self) -> pd.DataFrame:
        """Prepare data for visualization with caching"""
        cached_data = self._get_cached_data()
        if cached_data:
            return pd.DataFrame(cached_data)
            
        try:
            article_data, ticker_metadata = self.db.get_dashboard_data()
            
            # Aggregate article scores by ticker
            ticker_scores = (
                article_data.loc[
                    :,
                    [
                        "ticker",
                        "neutral_sentiment",
                        "positive_sentiment",
                        "negative_sentiment",
                        "compound_sentiment",
                    ],
                ]
                .groupby("ticker")
                .mean()
                .reset_index()
            )
            
            # Merge with metadata
            final_df = pd.merge(ticker_metadata, ticker_scores, on="ticker", how="inner")
            
            # Rename columns for display
            final_df.rename(
                columns={
                    "marketCap": "Market Cap (Billion Rs)",
                    "compound_sentiment": "Sentiment Score",
                    "neutral_sentiment": "Neutral",
                    "positive_sentiment": "Positive",
                    "negative_sentiment": "Negative",
                },
                inplace=True,
            )
            
            # Cache the prepared data
            self._cache_data(final_df.to_dict())
            
            return final_df
        except Exception as e:
            logging.error(f"Error preparing dashboard data: {str(e)}")
            raise
    
    def generate_treemap(self, data: pd.DataFrame):
        """Generate treemap visualization"""
        try:
            fig = px.treemap(
                data,
                path=[px.Constant("Nifty 500"), "sector", "industry", "ticker"],
                values="Market Cap (Billion Rs)",
                color="Sentiment Score",
                hover_data=["companyName", "Negative", "Neutral", "Positive", "Sentiment Score"],
                color_continuous_scale=["#FF0000", "#000000", "#00FF00"],
                color_continuous_midpoint=0,
            )
            
            fig.data[0].customdata = data[
                ["companyName", "Negative", "Neutral", "Positive", "Sentiment Score"]
            ]
            fig.data[0].texttemplate = "%{label}<br>%{customdata[4]}"
            fig.update_traces(textposition="middle center")
            fig.update_layout(margin=dict(t=30, l=10, r=10, b=10), font_size=20)
            
            return fig
        except Exception as e:
            logging.error(f"Error generating treemap: {str(e)}")
            raise
    
    def generate_html(self, fig) -> None:
        """Generate HTML dashboard"""
        try:
            ist_timezone = pytz.timezone(TIMEZONE)
            dt_string = datetime.now().astimezone(ist_timezone).strftime("%d/%m/%Y %H:%M:%S")
            
            with open("NIFTY_500_live_sentiment.html", "w") as f:
                title = "<h1>NIFTY 500 Stock Sentiment Dashboard</h1>"
                updated = f"<h2>Last updated: {dt_string} (Timezone: IST)</h2>"
                description = "This dashboard is updated at 17:30 IST Every Day with sentiment analysis performed on latest scraped news headlines.<br><br>"
                f.write(title + updated + description)
                f.write(fig.to_html(full_html=False, include_plotlyjs="cdn"))
                
            logging.info("Successfully generated dashboard HTML")
        except Exception as e:
            logging.error(f"Error generating HTML: {str(e)}")
            raise
    
    def update_dashboard(self) -> None:
        """Main method to update the dashboard"""
        try:
            data = self.prepare_data()
            fig = self.generate_treemap(data)
            self.generate_html(fig)
        except Exception as e:
            logging.error(f"Failed to update dashboard: {str(e)}")
            raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    try:
        dashboard = DashboardGenerator()
        dashboard.update_dashboard()
    except Exception as e:
        logging.error(f"Dashboard generation failed: {str(e)}")
        raise
