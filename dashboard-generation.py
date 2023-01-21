# Imports
import pandas as pd
# import numpy as np
# from urllib.request import urlopen, Request
# from bs4 import BeautifulSoup
# from pprint import pprint
# from nsepython import *
from datetime import datetime
# import time

# import nltk
# nltk.downloader.download('vader_lexicon')
# from nltk.sentiment.vader import SentimentIntensityAnalyzer

import pandas as pd
import matplotlib.pyplot as plt
import plotly
import plotly.express as px

import streamlit as st

# # Get company tickers and create a dataframe
# ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty500list.csv'
# tickers_file = pd.read_csv(ticker_url)
# tickers_df = tickers_file[['Symbol', 'Company Name']]
# tickers = tickers_df['Symbol']

# # Get articles and put them into a df
# news_url = 'https://ticker.finology.in/company/'

# # list to store article data
# data = []
# unavailable_tickers = []
# companies_len = len(tickers)
# length = 100

# for i in range(length):
#     #print(i)
#     req = Request(url= '{}/{}'.format(news_url, tickers[i]),headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'})
#     response = urlopen(req)
#     html = BeautifulSoup(response, 'lxml') 
#     news_links = html.select('#newsarticles > a')     #select('.newslink')  
#     if len(news_links) == 0:
#         print('No news found for {}'.format(tickers[i]))
#         unavailable_tickers.append(tickers[i])
#         # delete all ticker from tickers and tickers_df together #todo
#         continue

#     for link in news_links:
#         title = link.find('span', class_='h6').text
#         #separate date and time from datetime object
#         date_time_obj = datetime.strptime(link.find('small').text, '%d %b %Y, %I:%M%p')
#         art_date = date_time_obj.date().strftime('%Y/%m/%d')
#         art_time = date_time_obj.time().strftime('%H:%M')
#         data.append([tickers[i], title, art_date, art_time])  
#     ###if (i != 0 and i%200 == 0):
#     ####print('sleeping')
#     ####time.sleep(30)
# df = pd.DataFrame(data, columns=['Ticker', 'Headline', 'Date', 'Time'])

# # removing unavailable tickers from original df
# for ticker in unavailable_tickers:
#     if ticker in tickers:
#         tickers.drop(ticker, inplace=True)

# tickers_df.drop(tickers_df[tickers_df['Symbol'].isin(unavailable_tickers)].index.values, inplace=True)

# # Sentiment Analysis
# vader = SentimentIntensityAnalyzer()
# scores = df['Headline'].apply(vader.polarity_scores).tolist()
# scores_df = pd.DataFrame(scores)
# new_df = pd.merge(left=df, right=scores_df, on=df.index.values).drop(['key_0'], axis=1)
# final_df = new_df.groupby('Ticker').mean()

# # Get Company,Sector,Industry,mCap Data
# sector = []
# industry = []
# mCap = []
# for i in range(length):
#     meta = nse_eq(tickers[i])
#     #print(tickers[i])
#     try:
#         sector.append(meta['industryInfo']['macro'])
#     except KeyError:
#         print('{} is not available'.format(tickers[i]))
#         sector.append(np.nan)
#         industry.append(np.nan)
#         mCap.append(np.nan)
#         continue
#     #pprint('Sector: {}'.format(meta['industryInfo']['macro']))
#     try:
#         industry.append(meta['industryInfo']['sector'])
#     except KeyError:
#         print('{} is not available'.format(tickers[i]))
#         industry.append(np.nan)
#         mCap.append(np.nan)
#         continue
#     #pprint('Industry: {}'.format(meta['industryInfo']['sector']))
#     try:
#         mCap.append(round((meta['priceInfo']['previousClose'] * meta['securityInfo']['issuedSize'])/1000000000, 2))
#     except KeyError:
#         print('{} is not available'.format(tickers[i]))
#         mCap.append(np.nan)
#     #print('market cap is Rs {}'.format(ticker_mcap))
#     #print('\n')

# final_df['sector'] = sector
# final_df['industry'] = industry
# final_df['mCap (Billion)'] = mCap

# final_df = final_df.reset_index()
# final_df = pd.merge(final_df, tickers_df, left_on='Ticker', right_on='Symbol').drop('Symbol', axis=1)
# final_df.columns = ['Symbol', 'Negative', 'Neutral', 'Positive', 'Sentiment Score', 'Sector', 'Industry', 'MCap (Billion)', 'Company Name']

# final_df = final_df.dropna()

xc_indices = pd.read_csv('xc-indices.csv', header=0)

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