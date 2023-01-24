import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# sentiment analysis libraries
import nltk
nltk.downloader.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer


#NIFTY URLS
nifty_500_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty500list.csv'
nifty_200_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty200list.csv'
nifty_100_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty100list.csv'
nifty_50_ticker_url = 'https://www1.nseindia.com/content/indices/ind_nifty50list.csv'

# Set universe
universe = nifty_50_ticker_url

# Read CSV & create a tickers df
tickers_file = pd.read_csv(universe)
tickers_df = tickers_file[['Symbol', 'Company Name']]
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
        date_time_obj = datetime.strptime(link.find('small').text, '%d %b %Y, %I:%M%p')
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

# Now the art_scores_df could be filtered by Date or Universe, since it has both data in it.