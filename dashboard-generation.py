# Imports
import pandas as pd
# import numpy as np
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

import streamlit as st


# read csv files
#XC indices list for reference
xc_indices = pd.read_csv('xc-indices.csv', header=0)

article_data = pd.read_csv('./datasets/NIFTY_500_Articles.csv')


## Filter Articles by date

## Filter articles by UNIVERSE

sentiment_data = pd.read_csv('sentiment_data.csv')

# Plotting
fig = px.treemap(
    sentiment_data, path=[px.Constant('Nifty 500'), 'Sector', 'Industry', 'Symbol'], values='MCap (Billion)', color='Sentiment Score',
    hover_data=['Company Name', 'Negative', 'Neutral', 'Positive', 'Sentiment Score'], color_continuous_scale=['#FF0000', "#000000", '#00FF00'], color_continuous_midpoint=0
    )
fig.data[0].customdata = sentiment_data[['Company Name', 'Negative', 'Neutral', 'Positive', 'Sentiment Score']]
fig.data[0].texttemplate = "%{label}<br>%{customdata[4]}"
fig.update_traces(textposition="middle center")
fig.update_layout(height=800)
fig.update_layout(margin = dict(t=30, l=10, r=10, b=10), font_size=20)


# Get current date, time and timezone to print to the html page
now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
timezone_string = datetime.now().astimezone().tzname()

# Generate HTML File with Updated Time and Treemap
#with open('NIFTY_500_live_sentiment.html', 'a') as f:
#    f.truncate(0) # clear file if something is already written on it
#    title = "<h1>NIFTY 500 Stock Sentiment Dashboard</h1>"
#    updated = "<h2>Last updated: " + dt_string + " (Timezone: " + timezone_string + ")</h2>"
#    description = "This dashboard is updated every half an hour with sentiment analysis performed on latest scraped news headlines from the FinViz website.<br><br>"
#    f.write(title + updated + description)
#    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn')) # write the fig created above into the html file


# Streamlit App
st.set_page_config(page_title = "Nifty 500 Sentiment Analyzer", layout = "wide")
st.header("Nifty 500 stocks Sentiment Analyzer")
st.plotly_chart(fig,height=800,use_container_width=True)

st.write('''The chart above depicts the real time sentiment of Stocks and Industries in the Nifty 500 Universe.\n
The following table could be used as reference to identify sector and industry names.''') 
st.dataframe(xc_indices)
st.write('''
- [github repo](https://github.com/Shubxam/Nifty-500-Live-Sentiment-Analysis)
- [Companion Article](https://xumitcapital.medium.com/sentiment-analysis-dashboard-using-python-d40506e2709d)
''')
st.write('''This dashboard is updated everyday at 17:30 IST with sentiment analysis performed on latest scraped news headlines from the Ticker-Finology website.''')