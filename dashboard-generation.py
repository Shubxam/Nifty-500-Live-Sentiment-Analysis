import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit import cache_data
from whenever import Instant
from src.database import DatabaseManager
from src.config import UNIVERSE_NAMES_DICT, DatePickerOptions, IndexType, TREEMAP_COLOR_SCALE
from src.utils import get_relative_date

st.set_page_config(
        page_title=f"Nifty Indices Sentiment Analyzer", layout="wide"
    )

# initialize session state
# session state variables persist across reruns
if "date_filter" not in st.session_state:
    st.session_state["date_filter"] = "Past 1 Month"
if "universe_filter" not in st.session_state:
    st.session_state["universe_filter"] = "nifty_50"
if "newsbox" not in st.session_state:
    st.session_state["newsbox"] = "SBIN"


@cache_data # Cache data loading
def load_data(universe: IndexType, cut_off_date: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Loads data from the database."""
    dbm = DatabaseManager()
    articles_data = dbm.get_articles(has_sentiment=True, index=universe, after_date=cut_off_date)
    ticker_metadata = dbm.get_ticker_metadata(index=universe)
    return articles_data, ticker_metadata


@cache_data # Cache data processing
def calculate_sentiment(articles_data: pd.DataFrame, ticker_metadata: pd.DataFrame) -> pd.DataFrame:
    """Calculates aggregate sentiment scores and merges data."""
    if articles_data.empty or ticker_metadata.empty:
        return pd.DataFrame()

    ticker_aggregate_sentiment: pd.DataFrame = (
        articles_data.loc[
            :, ["ticker", "positive_sentiment", "negative_sentiment", "compound_sentiment"]
        ]
        .groupby("ticker")
        .mean()
        .reset_index()
    )

    # merge dfs
    final_df: pd.DataFrame = pd.merge(
        left=ticker_metadata, right=ticker_aggregate_sentiment, on="ticker", how="inner"
    )

    final_df.rename(
        columns={
            "mCap": "Market Cap (Billion Rs)",
            "compound_sentiment": "Sentiment Score",
        },
        inplace=True,
    )
    return final_df


@cache_data # Cache plot creation
def create_treemap(df: pd.DataFrame, universe_string: str) -> go.Figure | None:
    """Creates the Plotly treemap figure."""
    if df.empty:
        return None

    fig: go.Figure = px.treemap(
        df,
        path=[px.Constant(universe_string), "sector", "industry", "ticker"],
        values="Market Cap (Billion Rs)",
        color="Sentiment Score",
        hover_data=[
            "companyName",
            "negative_sentiment",
            "positive_sentiment",
            "Sentiment Score",
        ],
        color_continuous_scale=TREEMAP_COLOR_SCALE,
        color_continuous_midpoint=0,
    )

    fig.data[0].texttemplate = "%{label}<br>%{customdata[3]:.2f}"
    fig = fig.update_traces(textposition="middle center")
    fig = fig.update_layout(height=800)
    fig = fig.update_layout(margin=dict(t=30, l=10, r=10, b=10), font_size=20)
    return fig


def display_news(articles_data: pd.DataFrame, ticker: str):
    """Filters and displays news for a selected ticker."""
    if articles_data.empty:
        st.warning("No articles data available to display news.")
        return

    # Filter news for the selected ticker
    news_df_filtered = articles_data[articles_data["ticker"] == ticker]

    if news_df_filtered.empty:
        st.info(f"No news found for ticker {ticker}.")
        return

    news_df: pd.DataFrame = news_df_filtered[
        [
            "ticker",
            "headline",
            "date_posted",
            "source",
            "article_link",
            "compound_sentiment",
        ]
    ].reset_index(drop=True)
    news_df.rename(columns={"compound_sentiment": "Sentiment Score"}, inplace=True)

    st.dataframe(
        news_df.loc[
            :, ["Sentiment Score", "headline", "date_posted", "source", "article_link"]
        ],
        column_config={
            "Sentiment Score": st.column_config.NumberColumn(format="%.2f"),
            "article_link": st.column_config.LinkColumn("Link"),
        },
        hide_index=True
    )


def main():
    """Main function to run the Streamlit app."""
    # Get current date, time and timezone to print to the App
    now = Instant.now().to_tz("Asia/Kolkata")
    datetime_now = now.py_datetime().strftime("%d/%m/%Y %H:%M:%S")

    # --- Sidebar / Filters ---
    st.sidebar.header("Filters")
    st.sidebar.selectbox(
        "Pick the Date Range",
        DatePickerOptions.__args__,
        key="date_filter",
    )
    st.sidebar.selectbox(
        "Select Universe of Stocks",
        IndexType.__args__,
        key="universe_filter",
    )

    # --- Data Loading and Processing ---
    universe: IndexType = st.session_state["universe_filter"]
    universe_string: str = UNIVERSE_NAMES_DICT[universe]
    date_filter: DatePickerOptions = st.session_state["date_filter"]
    cut_off_date: str = get_relative_date(date_filter)

    # Load data using cached function
    articles_data, ticker_metadata = load_data(universe, cut_off_date)

    # Calculate sentiment using cached function
    final_df: pd.DataFrame = calculate_sentiment(articles_data, ticker_metadata)

    # --- App Layout ---
    st.header(f"{universe_string} stocks Sentiment Analyzer")

    st.markdown(
        f"This dashboard gives users an almost real-time comprehensive visual overview on the sentiments of various NIFTY indices. It analyses the ticker specific news from the **{date_filter}** from the internet."
    )

    # --- Treemap Chart ---
    if not final_df.empty:
        fig = create_treemap(final_df, universe_string)
        if fig:
            st.plotly_chart(fig, height=800, use_container_width=True, theme="streamlit")
            
        else:
            st.warning("Could not generate treemap.")
    else:
        st.warning(f"No data available for the selected filters ({universe_string}, {date_filter}). Please try different filters.")


    # --- Stock Specific News Section ---
    st.subheader("Stock Specific News")
    if not final_df.empty:
        selected_ticker: str | None = st.selectbox(
            "Type or select the Symbol name to get associated news:",
            options=sorted(list(final_df["ticker"].unique())),
            key="newsbox",
        )
        if selected_ticker:
            display_news(articles_data, selected_ticker)
        else:
            st.info("Select a ticker to view news.")
    else:
         st.info("Select filters with data to enable news section.")


    # --- Footer ---
    st.markdown("---") # Add a separator
    st.markdown(
        """
    - [GitHub Repo](https://github.com/Shubxam/Nifty-500-Live-Sentiment-Analysis)
    - [Companion Article](https://xumitcapital.medium.com/sentiment-analysis-dashboard-using-python-d40506e2709d)
    """
    )
    st.info(
        f"""This dashboard is updated everyday at 17:30 IST. Last Refreshed: {datetime_now} ({now.tz})"""
    )


if __name__ == "__main__":
    main()
