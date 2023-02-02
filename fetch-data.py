import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import datetime
from nsepython import *
import time

# sentiment analysis libraries
import nltk
nltk.downloader.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer


#NIFTY URLS
nifty_500_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty500list.csv'
nifty_500 = pd.read_csv(nifty_500_ticker_url)
nifty_500.to_csv('./datasets/NIFTY_500.csv')
nifty_200_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty200list.csv'
nifty_200 = pd.read_csv(nifty_200_ticker_url)
nifty_200.to_csv('./datasets/NIFTY_200.csv')
nifty_100_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty100list.csv'
nifty_100 = pd.read_csv(nifty_100_ticker_url)
nifty_100.to_csv('./datasets/NIFTY_100.csv')
nifty_50_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty50list.csv'
nifty_50 = pd.read_csv(nifty_50_ticker_url)
nifty_50.to_csv('./datasets/NIFTY_50.csv')

# Set universe
universe = nifty_50

# Read CSV & create a tickers df
tickers_df = universe[['Symbol', 'Company Name']]
tickers_list = tickers_df['Symbol']

# News URL
news_url = 'https://ticker.finology.in/company/'

# list to store article data
article_data = []

# list to store tickers for which data is unavailable
unavailable_tickers = []

# length of companies
companies_len = len(tickers_list)
tickers_length = companies_len

#days_limit = datetime.datetime.now() - datetime.timedelta(days=30) #only 30 days old or newer articles

start_time = time.time()
print('Fetching Article data..')
for i,ticker in enumerate(tickers_list):
    print(i, ticker)
    url= '{}/{}'.format(news_url, ticker)
    header={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'}
    response = requests.get(url, headers=header)
    html = BeautifulSoup(response.content, 'lxml')
    news_links = html.select('#newsarticles > a')
    if len(news_links) == 0:
        print('No news found for {}'.format(tickers_list[i]))
        unavailable_tickers.append(tickers_list[i])
        continue
    # for tickers which are not recognized by finology website, it returns home-page. There's also a news section on homepage. so for unrecognized tickers, this function will scrape general financial news instead of ticker specific news
    # var to store article count
    ticker_articles_counter = 0
    for link in news_links:
        art_title = link.find('span', class_='h6').text
        #separate date and time from datetime object
        date_time_obj = datetime.datetime.strptime(link.find('small').text, '%d %b %Y, %I:%M%p')
        #if (date_time_obj <= days_limit):
        #     continue
        art_date = date_time_obj.date().strftime('%Y/%m/%d')
        art_time = date_time_obj.time().strftime('%H:%M')
        article_data.append([ticker, art_title, art_date, art_time])
        ticker_articles_counter += 1
    if(ticker_articles_counter==0):
        unavailable_tickers.append(ticker)  

print(unavailable_tickers)

articles_df = pd.DataFrame(article_data, columns=['Ticker', 'Headline', 'Date', 'Time'])

#np.setdiff1d(tickers_list, unavailable_tickers)

tickers_list = articles_df['Ticker'].unique()
print('Available', len(tickers_list))

#keep the symbols in tickers_list remove the rest from tickers_df
tickers_df = tickers_df[tickers_df['Symbol'].isin(tickers_list)].reset_index(drop=True)

# Sentiment Analysis
print('Performing Sentiment Analysis')
vader = SentimentIntensityAnalyzer()
# Perform sentiment Analysis on the Headline column of all_news_df 
# It returns a dictionary, transform it into a list
art_scores_df = pd.DataFrame(articles_df['Headline'].apply(vader.polarity_scores).to_list())

# Merge articles_df with art_scores_df
# merging on index, hence both indices should be same
art_scores_df = pd.merge(articles_df, art_scores_df, left_index=True, right_index=True)
#art_scores_df = art_scores_df.drop(['Unnamed: 0'], axis=1)
#export article data to csv file
art_scores_df.to_csv('./datasets/NIFTY_500_Articles.csv')

# Now the art_scores_df could be filtered by Date or Universe, since it has both data in it.
# Get Company,Sector,Industry,mCap Data
ticker_meta = []
new_length = len(tickers_list)
#new_length = 10
print('Fetching ticker meta data')
# whether to get only data available in tickers_list or the whole universe bc even if we take whole universe, we will later merge the dfs ticker_meta and art_scores_df
# but since we're planning on not to fetch industry and sector data that often, its better to take the universe meta

for i, ticker in enumerate(tickers_list):
    meta = nse_eq(ticker)
    print(i, ticker)
    try:
        sector = meta['industryInfo']['macro']
    except KeyError:
        print('{} sector info is not available'.format(ticker))
        sector = np.nan
        industry = np.nan
        mCap = np.nan
        companyName = np.nan
        ticker_meta.append([ticker, sector, industry, mCap, companyName])
        continue
    try:
        industry = meta['industryInfo']['industry']
    except KeyError:
        print('{} industry info is not available'.format(ticker))
        industry = np.nan
        mCap = np.nan
        companyName = np.nan
        ticker_meta.append([ticker, sector, industry, mCap, companyName])
        continue
    try:
        mCap = round((meta['priceInfo']['previousClose'] * meta['securityInfo']['issuedSize'])/1000000000, 2)
    except KeyError:
        print('{} mCap data is not available'.format(ticker))
        mCap = np.nan
        companyName = np.nan
        ticker_meta.append([ticker, sector, industry, mCap, companyName])
        continue
    try:
        companyName = meta['info']['companyName']
    except KeyError:
        print('{} company Name is not available'.format(ticker))
        companyName = np.nan
        ticker_meta.append([ticker, sector, industry, mCap, companyName])
    ticker_meta.append([ticker, sector, industry, mCap, companyName])
end_time = time.time()

print('Time Taken: {}'.format(end_time-start_time))

# create dataframe
ticker_meta_df = pd.DataFrame(ticker_meta, columns=['Ticker', 'Sector', 'Industry', 'Market Cap', 'Company Name'])

# remove null values
ticker_meta_df = ticker_meta_df.dropna()

# import XC-indices file for categorization
xc_indices = pd.read_csv('./datasets/XC-tickers.csv')
xc_indices.columns = ['Ticker', 'XC-Sector', 'XC-Industry']

# merge xc-indices and ticker_meta_df
ticker_metadata = pd.merge(ticker_meta_df, xc_indices, on='Ticker')

#export ticker data to csv file
ticker_metadata.to_csv('./datasets/ticker_metadata.csv')