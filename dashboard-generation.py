# Imports
import pandas as pd
import datetime
import pytz

import plotly.express as px

# read csv
article_data = pd.read_csv("./datasets/NIFTY_500_Articles.csv", index_col=0)
ticker_metadata = pd.read_csv("./datasets/ticker_metadata.csv", index_col=0)

# aggregate article scores by ticker name
ticker_scores = (
    article_data.loc[:, ["Ticker", "neutral", "positive", "negative", "compound"]]
    .groupby("Ticker")
    .mean()
    .reset_index()
)

# merge dfs
final_df = pd.merge(ticker_metadata, ticker_scores, on="Ticker", how="inner")


final_df.rename(
    columns={
        "Market Cap": "Market Cap (Billion Rs)",
        "compound": "Sentiment Score",
        "neutral": "Neutral",
        "positive": "Positive",
        "negative": "Negative",
    },
    inplace=True,
)

# graphing
print("Generating Plots")
fig = px.treemap(
    final_df,
    path=[px.Constant("Nifty 500"), "Sector", "Industry", "Ticker"],
    values="Market Cap (Billion Rs)",
    color="Sentiment Score",
    hover_data=["Company Name", "Negative", "Neutral", "Positive", "Sentiment Score"],
    color_continuous_scale=["#FF0000", "#000000", "#00FF00"],
    color_continuous_midpoint=0,
)
fig.data[0].customdata = final_df[
    ["Company Name", "Negative", "Neutral", "Positive", "Sentiment Score"]
]
fig.data[0].texttemplate = "%{label}<br>%{customdata[4]}"
fig.update_traces(textposition="middle center")
fig.update_layout(margin=dict(t=30, l=10, r=10, b=10), font_size=20)


# Get current date, time and timezone to print to the html page
now = datetime.datetime.now()
ist_timezone = pytz.timezone("Asia/Kolkata")
dt_string = now.astimezone(ist_timezone).strftime("%d/%m/%Y %H:%M:%S")

# Generate HTML File with Updated Time and Treemap
print("Writing HTML")
with open("NIFTY_500_live_sentiment.html", "a") as f:
    f.truncate(0)  # clear file if something is already written on it
    title = "<h1>NIFTY 500 Stock Sentiment Dashboard</h1>"
    updated = "<h2>Last updated: " + dt_string + " (Timezone: IST" + ")</h2>"
    description = "This dashboard is updated at 17:30 IST Every Day with sentiment analysis performed on latest scraped news headlines.<br><br>"
    f.write(title + updated + description)
    f.write(
        fig.to_html(full_html=False, include_plotlyjs="cdn")
    )  # write the fig created above into the html file
