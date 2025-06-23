# Product Requirements Document (PRD)

# Nifty Index Generator: Turn any idea into investible index

## Overview

This project has following aims:
- to make it easy for a user to create an index/portfolio based off their idea and test its validity.


Once user has generated the index/portfolio, this tool allows them to:
- check their index's performance against a chosen benchmark and optimize it.
- check the current media sentiment of the index/constituent-stocks.

## User's Flow of Interaction

- User visits the site.
- They have an option to either:

### Create an Index of their own

- user sees a search box to input the query; his idea of index.
- user sees a progress bar or circular loading animation as the api request is sent and processed in the background.
- 2 tabs show up: Performance Analytics and Sentiment Analytics.
- Performance Analytics:
  - config options:
    - choose a benchmark (Nifty) Index to compare against. [Default: Nifty-50]
    - choose time-period from drop-down [default: 1Y]
  - show the index-value graph for chosen index and benchmark index for chosen time period.
  - performance statistics for chosen index and benchmark index for chosen time period. Excess returns volatility etc against benchmark.
  - show the index constituents in a table along with individual performance numbers and composite score.
- Sentiment Analytics:
  - config options:
    - select the date-range. [default: 7D]
  - "Sentiment Overview": hierarchial tree-map to show the sentiment of user generated index across sectors/stocks.
  - "Stock News Analysis": drop-down to choose a stock from chosen index, and a table to show related news-articles.


### work with pre-existing Nifty Index

- user selects a Official Nifty Index from a dropdown.
- 2 tabs show up: Performance Analytics and Sentiment Analytics.
- Performance Analytics:
  - config options:
    - choose a benchmark (Nifty) Index to compare against. [Default: None]
    - choose time-period from drop-down [default: 1Y]
  - show the index-value graph for chosen index and benchmark index for chosen time period.
  - performance statistics for chosen index and benchmark index for chosen time period.
  - show the index constituents in a table along with individual performance numbers and composite score.
- Sentiment Analytics:
  - config options:
    - select the date-range. [default: 7D]
  - "Sentiment Overview": hierarchial tree-map to show the sentiment of user generated index across sectors/stocks.
  - "Stock News Analysis": drop-down to choose a stock from chosen index, and a table to show related news-articles.


## Internal Specifics

- stock universe: [Nifty 50 -> Nifty 500]
- base date: 2023-Q1
- index type: Price Index

### Data Requirements
- timeframe: for all companies in the universe since base date
- #TODO: need brainstorming on what data to get
- OHLCV data: for price performance analytics
  - frequency: daily
- fundamental data: for index generation based on fundamentals (some of the data can be computed and some has to be fetched)
  - frequency: quarterly/annually
  - EPS
  - CAGR
  - Revenue: Gross, Net, Growth Rate
- Metadata: for index generation based on metadata
  - frequency: daily
  - Market Cap
  - Sector
  - Industry
- data sources:
  - NSE Libraries
  - Yahoo Finance
  - Indian brokerage services paid API


### Index Generation
- Getting Index Constituents:
  - Nifty Indices: From Nifty website.
    - sectoral indices
    - thematic indices
  - Custom Index Generation:
    - #TODO: find an way to route the query between the following options
    - **Gemini API**:
      - for non-definitive queries where constituents are subjective and more context (currently unavailable in the local database) is needed about the stocks.
      - use search grounding/google AI overview for real time info.
      - convert user's index generation query into a structured search query using few shot prompting:
        - `<user-query: fintech companies with focus on sustainability and ESG> --> <search-query: fintech stocks on NSE with focus on sustainability and ESG>`
      - use structured outputs to get the response as list of stock tickers.
    - SQL:
      - for queries where constituents can be retrieved definitively using the data available to us in database. (price performance or fundamental data or metadata etc.)
      - convert user query into SQL query to fetch list of companies.
        - `<user-query: highest growth public sector banks> --> <sql query: SELECT * from <table-name> where industry="public sector bank" Order by revenue-growth limit 10;>`
        - `<user-query: profitable fintech startups with consistent EPS growth last 4 quarters> --> <sql-query: SELECT * FROM "nifty-eps-data" WHERE sector = 'Fintech' AND 2024_Q4_EPS > 0 AND 2024_Q4_EPS > 2024_Q3_EPS AND 2024_Q3_EPS > 2024_Q2_EPS AND 2024_Q2_EPS > 2024_Q1_EPS;>`
      - #TODO: need concrete implementation details for SQL query generation

- Index Generation Methodology:
  - #DOUBT: given a user query to find top stocks in their respective sectors, If we pick the stocks based on latest values, then during historical performance backtest they most definitely will perform well due to survivalship bias. Current top stocks are known to have survived tough periods in the past and have done better since, hence they are top stocks now. It is easy to pick good stocks in hindsight, but had we been asked to predict and make our pick for best performing stocks in the past (which the user is doing now), some stocks would have failed, and ROI wouldn't be as good.
  - weighting method: free float mcap
  - capping method: <60%

- Index Value Update Methodology:
  - get the combined market cap for each day for all stocks in the index. (A: list of floats (n))
  - get the combined mcap of stocks at the base date. (B: float (1))
  - get the Base Index Value (C: float (1))
  - get the series of index values over time (D: list[floats] (n)): (A/B) * C
  - #DOUBT: How to handle price fluctuations due to corporate actions? [Example](https://economictimes.indiatimes.com/markets/stocks/news/raymond-shares-crash-66-here-are-4-things-you-need-to-know-as-realty-arm-demerger-kicks-in/articleshow/121154103.cms)

- Index Optimization/Asset Allocation Methodologies:
  - options: [note: some options will need parameter inputs from user]
    1. Mean Variance Optimization
    2. Modern Portfolio Theory
    3. Black Litterman Model
    4. Tracking Error Optimization
    5. Information Ratio Optimization
    6. Risk Parity


## Implementation thoughts

### Scheduled Jobs

- Data Fetching
  - OHLCV data [freq:daily]
  - fundamental data [freq:quarterly]
    - quarterly reports/Annual reports
  - metadata [freq:daily] -- for updated mcap data
  - nifty constituents list [freq:semi-annual]
    - scheduled rebalance/reconstitution happens at march and september end.
    - but we can fetch the list of constituents at the start of every month to ensure we have the latest data.
  - News Fetching [freq:daily]

- Data Processing
  - KPI/Performance Statistics updates [freq:daily]
    - run backtesting
      - all individual stocks in the universe.
      - for set of periods
      - for all benchmark indices.
  - Benchmark Index Value Update [freq:daily]
  - Sentiment Analysis [freq:daily]
    - run sentiment analysis on all news articles fetched for the day.
    - update sentiment scores for all stocks in the universe.


### Storing OHLCV Data:
  - evaluate storing the OHLCV data in a time-series database like InfluxDB or TimescaleDB.
  - due to storage considerations, storing the data in database could increase the size of the database significantly.
  - #TODO: look into the possibility of fetching the data from Yahoo Finance or NSE API on demand instead of storing it in the database.
  - could also consider storing the data in a separate database in cloudflare R2 storage for bulk of the processing.
  - look into data sharding


### Real Time Processing

- Custom Index Generation:
  - routing user query to either Gemini API or SQL based on the nature of the query.
  - index constituents generation
    - Gemini API
    - SQL query
- Index/Portfolio Optimization:
  - #TODO

### MCAP Computation

components in free float mcap computation:
- **Investible Weight Factor/Free Float**: public shareholding %. once declared in quarterly report, stays the same for the quarter.
- **Total Outstanding Shares**
- Free Float Market Capitalization: (Total Outstanding Shares * Investible Weight Factor * Closing Price of Stock)


## Database Tables:

### article_data

```sql
TABLE article_data{
  ticker varchar
  headline varchar
  date_posted varchar
  source varchar
  article_link varchar
  neutral_sentiment float
  negative_sentiment float
  positive_sentiment float
  compound_sentiment float
  created_at datetime
  PRIMARY KEY(ticker, headline)
}
```

### Index Constituents

```sql
TABLE indices_constituents{
  ticker VARCHAR
  ISIN_Code VARCHAR
  nifty_50 BOOLEAN
  nifty_100 BOOLEAN
  nifty_200 BOOLEAN
  nifty_500 BOOLEAN
}
```

### ticker metadata

```sql
TABLE ticker_meta{
  ticker VARCHAR
  sector VARCHAR
  industry VARCHAR
  mCap FLOAT
  companyName VARCHAR
  PRIMARY KEY(ticker)
}
```

## Minimum Viable Product

- Index Generation:
  - Gemini Integration for stocks suggestion.
  - Stock Weights: Free-Floating MCap.
- Pre-Existing Indices
  - all nifty indices.
- Performance Analytics
  - Index Value Chart.
  - Benchmark Comparison
  - Index KPIs: Returns, Beta
  - set time periods for KPIs and Chart
  - Basic Details of Index Constituents and KPIs
- Sentiment Analytics
  - Set of time periods
  - tree-map similar to current implementation
  - table showing news article details for a stock.



## Features for Future releases
- ability to view fundamental data for stock. [Note: not the main goal of the project, but since we have the data available]
- selecting companies for index generation for definitive queries using SQL and LLMs.
- adding stocks to index manually
- overview of company by summarising last quarter fundamental data and price performance in last 3 months using LLM.
- FAQ page: which will explain common pitfalls and educate users.
- add a column "confidence" in the index constituents table: % confidence shows how confident LLM is that company fits the query
- add tooltips wherever necessary
- add a third tab "optimize portfolio/index"
  - ability to optimize user-generated portfolio / existing nifty index using popular optimization/asset allocation methods
  - [doubt]: wonder how much useful it'll be since optimization has been done based on historical data and on that data itself we will backtest.
  - user has an option to choose optimization method.
  - backtest results will be shown
    - index/portfolio chart of optimized portfolio against free-float mcap weighted portfolio.
    - KPIs of optimized and un-optimized portfolio (before/after)
    - stocks with updated weights in a table.
- add another tab called stress-testing
  - where you run simulation methods to visualise the breadth of future performance of a portfolio/index for a chosen weight allocation method.
  - config:
    - simulation method:
      - Monte-Carlo
    - asset allocation method:
      - all portfolio optimization methods from optimization tab.
- Index Turnover:
  - ability to see the turnover of the index constituents over time.
  - config:
    - time period
    - benchmark index
  - show the turnover in a line chart.

### App State/UI

- Need data persistence. Refreshing the page or clicking the home-screen should not reset the generated index or weights generated by optimizing it.
- there should be a reset button up-top with confirmation to reset the app to default state.
- remove Home button and make app icon clickable to go to home.

## Inbox

- present the commentary of the index constituents by the LLM in a section above the index constituents table. why each stock is included in the index, and how it relates to the user query.

- various **agents** perform individual tasks and communicate with each other to complete the user query.
  - search grounding agent: to get real-time stock data and news.

- you can also leverage the search to get the latest news articles about the stocks in the index and generate a sentiment score of the index with a summary. This can be compared with the native sentiment score of index based on the news articles and see which fares better.

- add a note to allow the system some time to process the user query and generate the index. This is to avoid confusion if the user clicks on the button multiple times thinking it is not working.

- Add hints to guide the user in formulating their queries effectively. e.g., "Try asking for 'top fintech companies in India' or 'sustainable energy stocks in the Nifty 500'. or "What are the top 10 stocks in the Nifty 500 based on revenue growth?" or "be specific about the sector or industry you are interested in, or how many stocks you want in the index." or "if you want to create an index based on fundamentals, try asking for 'top 10 public sector banks with highest EPS growth in last 4 quarters' or 'top 5 fintech companies with consistent revenue growth'."

- user queries and fetched results should be logged for future reference and debugging purposes. This will help in improving the system and understanding user behavior.

### Components

LLM Integration:
- routing user query to either Gemini API or SQL
- Gemini API:
  - **Query Cleanup Agent**: reasons about the user query and generate a structured search query.
  - **Google Search Agent**: performs real time search to fetch stocks based on user query. {Company Name, Ticker, NSE_Listed, Rationale, Analyst Ratings}
  - **Structured Outputs Agent**: converts Google Search Agent response into structured search query. {Company Name, Ticker, NSE_Listed, Rationale, Analyst Ratings}
- **Query to SQL Agent**: #TODO
    - Has access to database schema. Analyzes the user query and generates SQL query to fetch stocks based on user query.


## References
- https://www.fe.training/free-resources/portfolio-management/portfolio-optimization/
- https://www.fe.training/free-resources/portfolio-management/black-litterman-model/
- https://www.wrightresearch.in/blog/risk-parity-portfolio-optimization/#5._Continuous_Improvement (details and implementation of optimization methods)
