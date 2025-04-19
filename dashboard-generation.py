import pandas as pd
import plotly.express as px
import streamlit as st
from whenever import Instant
from database import DatabaseManager
from config import UNIVERSE_NAMES_DICT, DatePickerOptions, IndexType
from utils import get_relative_date

# initialize session state
if "date_filter" not in st.session_state:
    st.session_state["date_filter"] = "Past 1 Month"
if "universe_filter" not in st.session_state:
    st.session_state["universe_filter"] = "nifty_50"
if "newsbox" not in st.session_state:
    st.session_state["newsbox"] = "SBIN"

# Get current date, time and timezone to print to the App
now = Instant.now().to_tz("Asia/Kolkata")
datetime_now = now.py_datetime().strftime("%d/%m/%Y %H:%M:%S")
timezone_string = now.tz

# Filter articles by UNIVERSE
universe: IndexType = st.session_state["universe_filter"]

# universe string will be used at places where we need to show the universe name (without underscores)
universe_string: str = UNIVERSE_NAMES_DICT[universe]

# Get the date filter from session state and convert it to a date string  
date_filter: DatePickerOptions = st.session_state["date_filter"]
cut_off_date: str = get_relative_date(date_filter)

# Get the data from database
dbm: DatabaseManager = DatabaseManager()
articles_data: pd.DataFrame = dbm.get_articles(has_sentiment=True, index=universe, after_date=cut_off_date)
ticker_metadata = dbm.get_ticker_metadata(index=universe)
universe_tickers = dbm.get_index_constituents(index=universe)

# calculate mean sentiment scores
ticker_aggregate_sentiment = (
    articles_data.loc[
        :, ["ticker", "positive_sentiment", "negative_sentiment", "compound_sentiment"]
    ]
    .groupby("ticker")
    .mean()
    .reset_index()
)

# merge dfs
final_df = pd.merge(
    left=ticker_metadata, right=ticker_aggregate_sentiment, on="ticker", how="inner"
)

final_df.rename(
    columns={
        "mCap": "Market Cap (Billion Rs)",
        "compound_sentiment": "Sentiment Score",
    },
    inplace=True,
)

print(final_df.columns)
print(final_df.head())

# Plotting
fig = px.treemap(
    final_df,
    path=[px.Constant(universe_string), "sector", "industry", "ticker"],
    values="Market Cap (Billion Rs)",
    color="Sentiment Score",
    hover_data=[
        "companyName",
        "negative_sentiment",
        "positive_sentiment",
        "Sentiment Score",
    ],
    color_continuous_scale=["#FF0000", "#000000", "#00FF00"],
    color_continuous_midpoint=0,
)

fig.data[0].texttemplate = "%{label}<br>%{customdata[3]}"
fig.update_traces(textposition="middle center")
fig.update_layout(height=800)
fig.update_layout(margin=dict(t=30, l=10, r=10, b=10), font_size=20)


###################### Streamlit App ######################

# stock specific news section
news_ticker_name = st.session_state.newsbox
news_df = articles_data[articles_data["ticker"] == news_ticker_name][
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


# Streamlit App
st.set_page_config(
    page_title="{} Sentiment Analyzer".format(universe_string), layout="wide"
)
st.header("{} stocks Sentiment Analyzer".format(universe_string))
# st.subheader()

st.markdown(
    "This dashboard gives users a almost real-time comprehensive visual overview on the sentiments regarding various NIFTY indices."
)

st.markdown(
    "The chart shows the latest sentiment of Stocks and Industries in the Nifty 500 Universe."
)

# Update filters
col1, col2, col3 = st.columns(3)
with col1:
    date_interval = st.selectbox(
        "Pick the Date Range",
        DatePickerOptions.__args__,
        key="date_filter",
    )
with col2:
    universe_var = st.selectbox(
        "Select Universe of Stocks",
        IndexType.__args__,
        key="universe_filter",
    )
with col3:
    st.empty()

chart_area = st.empty()

chart_area.plotly_chart(fig, height=800, use_container_width=True)



col_1, col_2 = st.columns(2)
with col_1:
    st.selectbox(
        "Type the Symbol name to get associated news: ",
        final_df["ticker"],
        key="newsbox",
    )

with col_2:
    st.markdown(" ")

st.dataframe(
        news_df.loc[
            :, ["Sentiment Score", "headline", "date_posted", "source", "article_link"]
        ],
        hide_index=True
    )

st.markdown(
    """
- [github repo](https://github.com/Shubxam/Nifty-500-Live-Sentiment-Analysis)
- [Companion Article](https://xumitcapital.medium.com/sentiment-analysis-dashboard-using-python-d40506e2709d)
"""
)
st.markdown("This is a treemap generated using python, plotly and streamlit.")
st.info(
    """This dashboard is updated everyday at 17:30 IST with sentiment analysis performed on latest scraped news headlines from the internet."""
)
