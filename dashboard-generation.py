# Imports
import pandas as pd
import numpy as np
from urllib.request import urlopen, Request
import requests
from bs4 import BeautifulSoup
from pprint import pprint
from nsepython import *
import datetime
import pytz
#import time

import nltk
nltk.downloader.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import pandas as pd
import matplotlib.pyplot as plt
import plotly
import plotly.express as px

# Get company tickers and create a dataframe
nifty_500_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty500list.csv'
nifty_200_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty200list.csv'
nifty_100_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty100list.csv'
nifty_50_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty50list.csv'
tickers_file = pd.read_csv(nifty_500_ticker_url)
tickers_df = tickers_file[['Symbol', 'Company Name']]
tickers = tickers_df['Symbol']

# Get articles and put them into a df
news_url = 'https://ticker.finology.in/company/'

#import XC indices
xc_indices = pd.read_csv('XC-tickers.csv', header=0)

# list to store article data
data = []
unavailable_tickers = []
companies_len = len(tickers)
length = companies_len
days_limit = datetime.datetime.now() - datetime.timedelta(days=30) #only 30 days old or newer articles
print('Fetching Article data..')
for i in range(length):
    print(i, tickers[i])
    url= '{}/{}'.format(news_url, tickers[i])
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'}
    response = requests.get(url, headers=headers)
    html = BeautifulSoup(response.content, 'lxml')
    news_links = html.select('#newsarticles > a')
    if len(news_links) == 0:
        print('No news found for {}'.format(tickers[i]))
        unavailable_tickers.append(tickers[i])
        continue
    new_articles_counter = 0
    for link in news_links:
        title = link.find('span', class_='h6').text
        #separate date and time from datetime object
        date_time_obj = datetime.datetime.strptime(link.find('small').text, '%d %b %Y, %I:%M%p')
        if (date_time_obj <= days_limit):
             continue
        art_date = date_time_obj.date().strftime('%Y/%m/%d')
        art_time = date_time_obj.time().strftime('%H:%M')
        data.append([tickers[i], title, art_date, art_time])
        new_articles_counter += 1
    if(new_articles_counter==0):
        unavailable_tickers.append(tickers[i])  

df = pd.DataFrame(data, columns=['Ticker', 'Headline', 'Date', 'Time'])

print(unavailable_tickers)

# removing unavailable tickers from original df
tickers = np.setdiff1d(tickers, unavailable_tickers)
tickers_df.drop(tickers_df[tickers_df['Symbol'].isin(unavailable_tickers)].index.values, inplace=True)

# Sentiment Analysis
print('Performing Sentiment Analysis')
vader = SentimentIntensityAnalyzer()
scores = df['Headline'].apply(vader.polarity_scores).tolist()
scores_df = pd.DataFrame(scores)
new_df = pd.merge(left=df, right=scores_df, on=df.index.values).drop(['key_0'], axis=1)
final_df = new_df.groupby('Ticker').mean()

# Get Company,Sector,Industry,mCap Data
sector = []
industry = []
mCap = []
companyName = []
new_length = len(tickers)
#new_length = 10
print('Fetching industry data')
for i in range(new_length):
    meta = nse_eq(tickers[i])
    print(i, tickers[i])
    try:
        sector.append(meta['industryInfo']['macro'])
    except KeyError:
        print('{} is not available'.format(tickers[i]))
        sector.append(np.nan)
        industry.append(np.nan)
        mCap.append(np.nan)
        companyName.append(np.nan)
        continue
    #pprint('Sector: {}'.format(meta['industryInfo']['macro']))
    try:
        industry.append(meta['industryInfo']['sector'])
    except KeyError:
        print('{} is not available'.format(tickers[i]))
        industry.append(np.nan)
        mCap.append(np.nan)
        companyName.append(np.nan)
        continue
    #pprint('Industry: {}'.format(meta['industryInfo']['sector']))
    try:
        mCap.append(round((meta['priceInfo']['previousClose'] * meta['securityInfo']['issuedSize'])/1000000000, 2))
    except KeyError:
        print('{} is not available'.format(tickers[i]))
        mCap.append(np.nan)
        companyName.append(np.nan)
        continue
    try:
        companyName.append(meta['info']['companyName'])
    except KeyError:
        print('{} is not available'.format(tickers[i]))
        companyName.append(np.nan)
    
    #print('market cap is Rs {}'.format(ticker_mcap))
    #print('\n')

#final_df['sector'] = sector
#final_df['industry'] = industry
final_df['mCap (Billion)'] = mCap
final_df['Company Name'] = companyName

final_df = final_df.reset_index()
final_df = pd.merge(final_df, xc_indices, left_on='Ticker', right_on='Ticker', how='inner')
final_df.columns = ['Symbol', 'Negative', 'Neutral', 'Positive', 'Sentiment Score','MCap (Billion)', 'Company Name', 'Sector', 'Industry']

final_df = final_df.dropna()
final_df = final_df.round(3)

final_df.to_csv('sentiment_data.csv')

# Plotting
print('Generating Plots')
fig = px.treemap(
    final_df, path=[px.Constant('Nifty 500'), 'Sector', 'Industry', 'Symbol'], values='MCap (Billion)', color='Sentiment Score',
    hover_data=['Company Name', 'Negative', 'Neutral', 'Positive', 'Sentiment Score'], color_continuous_scale=['#FF0000', "#000000", '#00FF00'], color_continuous_midpoint=0
    )
fig.data[0].customdata = final_df[['Company Name', 'Negative', 'Neutral', 'Positive', 'Sentiment Score']]
fig.data[0].texttemplate = "%{label}<br>%{customdata[4]}"
fig.update_traces(textposition="middle center")
fig.update_layout(margin = dict(t=30, l=10, r=10, b=10), font_size=20)


# Get current date, time and timezone to print to the html page
now = datetime.datetime.now()
ist_timezone = pytz.timezone('Asia/Kolkata')
dt_string = now.astimezone(ist_timezone).strftime("%d/%m/%Y %H:%M:%S")

# Generate HTML File with Updated Time and Treemap
print('Writing HTML')
with open('NIFTY_500_live_sentiment.html', 'a') as f:
    f.truncate(0) # clear file if something is already written on it
    title = "<h1>NIFTY 500 Stock Sentiment Dashboard</h1>"
    updated = "<h2>Last updated: " + dt_string + " (Timezone: IST" + ")</h2>"
    description = "This dashboard is updated at 17:30 IST Every Day with sentiment analysis performed on latest scraped news headlines.<br><br>"
    f.write(title + updated + description)
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn')) # write the fig created above into the html file