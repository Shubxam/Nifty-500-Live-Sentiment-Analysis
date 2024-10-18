# Nifty 500 Live Sentiment Analysis Dashboard

![app-img](./app.png)

A live Sentiment Analysis Dashboard which shows the sentiment of the chosen index and its constituent sectors and stocks computed using news articles headlines.

Ticker specific articles are sourced from the following sources everyday and stored in a persistent (duckdb) database, which are then processed for sentiment analysis using [mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis](https://huggingface.co/mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis) Language model offline using Github Actions.
- google finance
- yahoo finance
- ticker finology

Live instances of the app can be found
1. [Streamlit Cloud](https://nifty-sad.streamlit.app/)
2. [Github Pages](https://shubxam.github.io/NIFTY_500_live_sentiment.html)

Here is the link to [Companion Article](https://xumitcapital.medium.com/sentiment-analysis-dashboard-using-python-d40506e2709d).
