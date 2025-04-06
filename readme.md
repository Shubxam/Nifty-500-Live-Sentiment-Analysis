# Nifty-500 Live Sentiment Analysis

Real-time sentiment analysis of Nifty-500 stocks.

![app-img](./res/app.png)

## Overview

This project analyzes the sentiment of Nifty-500 stocks in real-time, providing insights into market trends and investor sentiment.

Ticker specific articles are sourced from the following sources everyday and stored in a persistent (duckdb) database, which are then processed for sentiment analysis using [mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis](https://huggingface.co/mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis) Language model offline using Github Actions.
- google finance
- yahoo finance
- ticker finology

Live instances of the app can be found
1. [Streamlit Cloud](https://nifty-sad.streamlit.app/)
2. [Github Pages](https://shubxam.github.io/NIFTY_500_live_sentiment.html)

Here is the link to [Companion Article](https://xumitcapital.medium.com/sentiment-analysis-dashboard-using-python-d40506e2709d).

## Installation

```bash
# Clone the repository
git clone https://github.com/shubxam/Nifty-500-Live-Sentiment-Analysis.git
cd Nifty-500-Live-Sentiment-Analysis

# Install dependencies
uv sync --all-extras --dev
```

## Usage

```bash
# Run the application
python -m src.main
```
