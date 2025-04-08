# Nifty 500 Live Sentiment Analysis - System Architecture

## Overview

This document outlines the architecture of the Nifty 500 Live Sentiment Analysis system, which provides real-time sentiment analysis of news articles for Nifty 500 stocks through a web-based dashboard.

## System Components

### 1. Data Collection Layer (`services/`)

#### a. Universe Management (`universe_updater.py`)
- **UniverseUpdater**: Maintains up-to-date lists of stock constituents for different Nifty indices.
- Performs monthly updates of universe constituents via GitHub Actions.
- Direct file-based constituent updates.
- Make updates to indices table 

#### b. News Collection (`data_fetcher.py`)
- **DataFetcher**: Orchestrates news collection from multiple sources
- News Sources:
  - GoogleFinanceSource (`div.z4rs2b` containers)
  - YahooFinanceSource (ticker-specific `/{ticker}.NS/news` endpoints)
  - FinologySource (company-specific pages)
- Standardized date parsing across sources
- Handles relative dates and timezone conversions
- TODO: Use parallelism to fetch articles
- TODO: Deduplication of articles based on headline and date before inserting into DB

#### c. Sentiment Analysis (`sentiment_analyzer.py`)
- Uses DistilRoBERTa model fine-tuned for financial news
- Processes news headlines in batches for better performance
- Provides sentiment scores (positive, negative, neutral, compound)
- Implements caching and retry mechanisms

### 2. Data Storage Layer (`database/`)

#### Database Manager (`db_manager.py`)
- Singleton pattern implementation for database connections
- Uses DuckDB for efficient data storage and querying
- Schema:
  ```sql
  article_data:
    - id (PRIMARY KEY)
    - ticker (TEXT, INDEXED)
    - headline (TEXT)
    - date_posted (TEXT, INDEXED)
    - source (TEXT)
    - article_link (TEXT)
    - sentiment scores (negative, positive, neutral, compound)
    - created_at (TIMESTAMP)

  ticker_meta:
    - ticker (TEXT, PRIMARY KEY)
    - sector (TEXT, INDEXED)
    - industry (TEXT, INDEXED)
    - marketCap (FLOAT)
    - companyName (TEXT)

  universe_constituents:
    - ticker (TEXT)
    - universe (TEXT)
    - weight (FLOAT)
    - entry_date (DATE)
    - last_updated (TIMESTAMP)
    PRIMARY KEY (ticker, universe)
  ```
- Implements connection pooling and transaction management

### 3. Visualization Layer

#### Dashboard Generator (`dashboard-generation.py`)
- **DashboardGenerator**: Creates interactive visualizations
- Features:
  - Treemap visualization by sector/industry
  - Market cap weighted sentiment analysis
  - Real-time data updates
- Implements data caching for performance
- Generates static HTML for deployment

## Data Flow

1. **Universe Update Flow**:
   ```
   GitHub Actions (Monthly) → UniverseUpdater → Database
   ```

2. **News Collection Flow**:
   ```
   DataFetcher → Multiple News Sources → Raw Articles → Database
   ```

3. **Sentiment Analysis Flow**:
   ```
   Articles without sentiment → SentimentAnalyzer → Updated sentiment scores → Database
   ```

4. **Dashboard Update Flow**:
   ```
   DatabaseManager → DashboardGenerator → HTML Generation (17:30 IST)
   ```

## Configuration Management

- **config.py**: Central configuration for:
  - Database settings
  - API configurations
  - Update intervals
  - Timezone settings (standardized to IST)
  - Model parameters
  - HTML selectors for news sources

## Testing Strategy

- Comprehensive pytest-based test suite
- Unit tests with pytest-mock for external dependencies
- Integration tests for data pipeline
- HTML structure validation for news sources
- Test coverage reporting with pytest-cov
- Mock responses for external APIs
- Date parsing and timezone conversion tests
- Performance benchmarking

## Performance Considerations

1. **Database Optimization**:
   - Indexed queries for frequent operations
   - Connection pooling with context managers
   - Batch processing for bulk operations
   - MERGE operations for atomic updates

2. **API Handling**:
   - Retry mechanisms with exponential backoff
   - Rate limiting per news source
   - Request caching for frequently accessed data

3. **Dashboard Performance**:
   - Data caching with configurable duration
   - Efficient data aggregation
   - Optimized visualization rendering
   - Standardized date formats for better performance

## Security Considerations

1. **API Security**:
   - Environment variables for sensitive data
   - Rate limiting per source
   - User-Agent header management

2. **Data Security**:
   - Input validation for all data sources
   - SQL injection prevention via parameterized queries
   - Secure data storage with proper indexing
   - Regular backups of constituent data

## Monitoring and Logging

- Comprehensive logging throughout the system
- Error tracking for HTML parsing failures
- Performance monitoring for API calls
- Data quality validation
- News source HTML structure monitoring

## Dependencies

- **Core**:
  - Python 3.11+
  - DuckDB
  - Pandas
  - Plotly
  - Requests
  - BeautifulSoup4

- **Machine Learning**:
  - Hugging Face Transformers
  - DistilRoBERTa (Financial News fine-tuned)

- **Development**:
  - pytest (with pytest-mock and pytest-cov)
  - uv (Python package installer)

## Deployment

- Static HTML generation for dashboard
- Monthly universe updates via GitHub Actions
- Environmental configuration for different deployments
- Timezone-aware scheduling