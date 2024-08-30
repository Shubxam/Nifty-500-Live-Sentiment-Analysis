# Imports
import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import plotly.express as px
import streamlit as st
import duckdb

# initialize session state
if "date_filter" not in st.session_state:
    st.session_state["date_filter"] = "Past 1 Month"
if "universe_filter" not in st.session_state:
    st.session_state["universe_filter"] = "nifty_50"
if "newsbox" not in st.session_state:
    st.session_state["newsbox"] = "SBIN"

# Get current date, time and timezone to print to the App
now = datetime.datetime.now()
datetime_now = now.strftime("%d/%m/%Y %H:%M:%S")
timezone_string = datetime.datetime.now().astimezone().tzname()

# read csv files
# articles_data = pd.read_csv("./datasets/NIFTY_500_Articles.csv", index_col=0)
# ticker_metadata = pd.read_csv("./datasets/ticker_metadata.csv", index_col=0)

# read duckdb file
conn = duckdb.connect("./datasets/ticker_data.db")
articles_data = conn.execute(
    "SELECT * FROM article_data where compound_sentiment is not null"
).fetchdf()
ticker_metadata = conn.execute("SELECT * FROM ticker_meta").fetchdf()

## Filter articles by UNIVERSE
universe = st.session_state["universe_filter"]

# universe string will be used at places where we need to show the universe name (without underscores)
if universe == "nifty_50":
    universe_string = "NIFTY 50"
if universe == "nifty_100":
    universe_string = "NIFTY 100"
if universe == "nifty_200":
    universe_string = "NIFTY 200"
if universe == "nifty_500":
    universe_string = "NIFTY 500"


universe_tickers = pd.read_csv("./datasets/{}.csv".format(universe), index_col=0)[
    "Symbol"
]

## Filter Articles by date
date_interval_st = st.session_state["date_filter"]

if date_interval_st == "Past 7 days":
    date_interval = 7
if date_interval_st == "Past 1 Month":
    date_interval = 30
if date_interval_st == "Past 2 Months":
    date_interval = 60
if date_interval_st == "Full":
    date_interval = 1000


cutoff_date = pd.to_datetime(
    datetime.datetime.now() - relativedelta(days=date_interval)
)

# filter articles based on date filter
filterd_articles = articles_data.loc[
    articles_data.date_posted.astype("datetime64[ns]") > cutoff_date
]

# calculate mean sentiment score for each ticker
ticker_scores = (
    filterd_articles.loc[
        :, ["ticker", "positive_sentiment", "negative_sentiment", "compound_sentiment"]
    ]
    .groupby("Ticker")
    .mean()
    .reset_index()
)

# filter companies based on universe
filtered_tickers = ticker_scores.loc[ticker_scores.ticker.isin(universe_tickers)]

# merge dfs
final_df = pd.merge(
    left=ticker_metadata, right=filtered_tickers, on="ticker", how="inner"
)

final_df.rename(
    columns={
        "marketCap": "Market Cap (Billion Rs)",
        "compound_score": "Sentiment Score",
    },
    inplace=True,
)

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

fig.data[0].texttemplate = "%{label}<br>%{customdata[4]}"
fig.update_traces(textposition="middle center")
fig.update_layout(height=800)
fig.update_layout(margin=dict(t=30, l=10, r=10, b=10), font_size=20)


###################### Streamlit App ######################

# stock specific news section
news_ticker_name = st.session_state.newsbox
news_df = filterd_articles[filterd_articles["ticker"] == news_ticker_name][
    [
        "ticker",
        "headline",
        "date_posted",
        "source",
        "article_link",
        "compound_sentiment",
    ]
].reset_index(drop=True)
news_df.rename(columns={"compound": "Sentiment Score"}, inplace=True)


# Streamlit App
st.set_page_config(
    page_title="{} Sentiment Analyzer".format(universe_string), layout="wide"
)
st.header("{} stocks Sentiment Analyzer".format(universe_string))
# st.subheader()

st.markdown(
    "This dashboard gives users a almost real-time comprehensive visual overview on the sentiments regarding various NIFTY indices."
)


# Update filters
col1, col2, col3 = st.columns(3)
with col1:
    date_interval = st.selectbox(
        "Pick the Date Range",
        ("Past 7 days", "Past 1 Month", "Past 2 Months", "Full"),
        key="date_filter",
    )
with col2:
    universe_var = st.selectbox(
        "Select Universe of Stocks",
        ("nifty_50", "nifty_100", "nifty_200", "nifty_500"),
        key="universe_filter",
    )
with col3:
    st.empty()

chart_area = st.empty()

chart_area.plotly_chart(fig, height=800, use_container_width=True)

st.markdown(
    "The chart above depicts the real time sentiment of Stocks and Industries in the Nifty 500 Universe."
)


col_1, col_2 = st.columns(2)
with col_1:
    st.selectbox(
        "Type the Symbol name to get associated news: ",
        final_df["Ticker"],
        key="newsbox",
    )
    st.dataframe(
        news_df.loc[
            :, ["Sentiment Score", "headline", "date_posted", "source", "article_link"]
        ]
    )

with col_2:
    st.markdown(" ")

st.markdown(
    """
- [github repo](https://github.com/Shubxam/Nifty-500-Live-Sentiment-Analysis)
- [Companion Article](https://xumitcapital.medium.com/sentiment-analysis-dashboard-using-python-d40506e2709d)
"""
)
st.markdown("This is a treemap generated using python, plotly and streamlit.")
st.info(
    """This dashboard is updated everyday at 17:30 IST with sentiment analysis performed on latest scraped news headlines from the Ticker-Finology website."""
)
