# Imports
import pandas as pd
# import numpy as np
import datetime

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

import streamlit as st


#initialize session state
if 'date_filter' not in st.session_state:
    st.session_state['date_filter'] = 'Past 1 Month'
if 'universe_filter' not in st.session_state:
    st.session_state['universe_filter'] = 'NIFTY_100'


# Get current date, time and timezone to print to the App
now = datetime.datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
timezone_string = datetime.datetime.now().astimezone().tzname()

# read must csv files
articles_data = pd.read_csv('./datasets/NIFTY_500_Articles.csv', index_col=0)
ticker_metadata = pd.read_csv('./datasets/ticker_metadata.csv', index_col=0)
xc_indices = pd.read_csv('./datasets/XC-Indices.csv')

## Filter articles by UNIVERSE
universe = st.session_state['universe_filter']

# universe string will be used at places where we need to show the universe name (without underscores)
if universe == 'NIFTY_50':
    universe_string = 'NIFTY 50'
if universe == 'NIFTY_100':
    universe_string = 'NIFTY 100'
if universe == 'NIFTY_200':
    universe_string = 'NIFTY 200'
if universe == 'NIFTY_500':
    universe_string = 'NIFTY 500'


universe_tickers = pd.read_csv('./datasets/{}.csv'.format(universe), index_col=0)['Symbol']

## Filter Articles by date
date_interval_st = st.session_state['date_filter']

if date_interval_st == 'Past 7 days':
    date_interval = 7
if date_interval_st == 'Past 1 Month':
    date_interval = 30
if date_interval_st == 'Past 2 Months':
    date_interval = 60
if date_interval_st == 'Full':
    date_interval = 1000



cutoff_date = datetime.datetime.now().date() - datetime.timedelta(date_interval)

#filter articles based on date filter
date_filter_article = articles_data[pd.to_datetime(articles_data['Date']).dt.date > cutoff_date]
#calculate mean sentiment score for each ticker
filter_article_sent_score = round(date_filter_article.groupby('Ticker').mean().reset_index(),2)

#filter companies based on universe
universe_filtered_df = filter_article_sent_score[filter_article_sent_score['Ticker'].isin(universe_tickers)]

#merge dfs
final_df = pd.merge(ticker_metadata, universe_filtered_df, on='Ticker', how='inner')
final_df.columns = ['Symbol','Macro-Sector','Industry', 'Market Cap (Billion Rs)','Company Name','XC-Sector', 'XC-Industry', 'Negative', 'Neutral', 'Positive', 'Sentiment Score']

# Plotting
fig = px.treemap(
    final_df, path=[px.Constant(universe_string), 'XC-Sector', 'XC-Industry', 'Symbol'], values= 'Market Cap (Billion Rs)', color='Sentiment Score',
    hover_data=['Company Name', 'Negative', 'Neutral', 'Positive', 'Sentiment Score'], color_continuous_scale=['#FF0000', "#000000", '#00FF00'], color_continuous_midpoint=0
    )
#fig.data[0].customdata = final_df[['Company Name', 'Negative', 'Neutral', 'Positive', 'Sentiment Score']]
fig.data[0].texttemplate = "%{label}<br>%{customdata[4]}"
fig.update_traces(textposition="middle center")
fig.update_layout(height=800)
fig.update_layout(margin = dict(t=30, l=10, r=10, b=10), font_size=20)
    




# Streamlit App
st.set_page_config(page_title = "{} Sentiment Analyzer".format(universe_string), layout = "wide")
st.header("{} stocks Sentiment Analyzer".format(universe_string))
#st.subheader()

st.markdown('This dashboard gives users a almost real-time comprehensive visual overview on the sentiments regarding various NIFTY indices.')

# Update filters

col1, col2 = st.columns(2)
with col1:
    date_interval = st.selectbox('Pick the Date Range', ('Past 7 days', 'Past 1 Month', 'Past 2 Months', 'Full'), key='date_filter')
with col2:
    universe_var = st.selectbox('Select Universe of Stocks', ('NIFTY_50', 'NIFTY_100', 'NIFTY_200', 'NIFTY_500'), key='universe_filter')

chart_area = st.empty()

chart_area.plotly_chart(fig,height=800,use_container_width=True)

st.markdown('The chart above depicts the real time sentiment of Stocks and Industries in the Nifty 500 Universe.')
st.markdown('The following table could be used as reference to identify sector and industry names.') 
st.dataframe(xc_indices)
st.markdown('''
- [github repo](https://github.com/Shubxam/Nifty-500-Live-Sentiment-Analysis)
- [Companion Article](https://xumitcapital.medium.com/sentiment-analysis-dashboard-using-python-d40506e2709d)
''')
st.markdown('This is a treemap generated using python, plotly and streamlit.')
st.info('''This dashboard is updated everyday at 17:30 IST with sentiment analysis performed on latest scraped news headlines from the Ticker-Finology website.''')