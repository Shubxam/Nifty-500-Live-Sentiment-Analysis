# Nifty 500 Live Sentiment Analysis Dashboard

![app-img](./res/app.png)

A live Sentiment Analysis Dashboard which shows the sentiment of the chosen index and its constituent sectors and stocks computed using news articles headlines.

## Features

- Real-time sentiment analysis of stock news headlines from multiple sources
- Interactive treemap visualization of market sentiment
- Support for multiple indices (Nifty 50, Nifty 100, Nifty 200, Nifty 500)
- Automated daily index constituent updates
- Multi-source news aggregation (Google Finance, Yahoo Finance, Finology)
- Intelligent news deduplication and relevance filtering
- Daily updates at 17:30 IST with batch processing
- Smart caching mechanism for faster dashboard loading
- Comprehensive error handling and logging
- DuckDB-based data storage with optimized indexing
- Robust testing infrastructure with pytest
- **New**: Universe Updater service for automated index tracking
- **New**: Enhanced news source parsing with improved reliability
- **New**: Optimized sentiment analysis pipeline with batching

## Architecture

The project follows a modular architecture with clear separation of concerns:

```
├── services/                # Core services
│   ├── data_fetcher.py     # Multi-source news aggregation
│   ├── sentiment_analyzer.py  # DistilRoBERTa-based analysis
│   ├── universe_updater.py   # Index constituent management
│   └── universe_scheduler.py # Scheduled updates
├── database/               # Database management
│   └── db_manager.py      # DuckDB operations
├── datasets/              # Data storage
│   ├── nifty_*.csv       # Index constituent data
│   ├── ticker_data.db    # DuckDB database
│   └── ticker_metadata.csv  # Stock metadata
├── tests/                # Comprehensive test suite
├── notebooks/            # Development notebooks
└── config.py            # Central configuration

```

## Getting Started

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   uv pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   export HF_API_TOKEN=your_huggingface_token
   ```

3. **Run Tests**
   ```bash
   pytest tests/
   ```

4. **Run Data Pipeline**
   ```bash
   python fetch-data.py
   ```

5. **Generate Dashboard**
   ```bash
   python dashboard-generation.py
   ```

Live instances of the app can be found at:
1. [Streamlit Cloud](https://nifty-sad.streamlit.app/)
2. [Github Pages](https://shubxam.github.io/NIFTY_500_live_sentiment.html)

## Data Pipeline

The project implements a robust data pipeline that includes:
- Automated constituent updates for all supported indices
- Multi-source news aggregation with intelligent deduplication
- High-performance DuckDB storage with optimized indexing
- Batched sentiment analysis using DistilRoBERTa
- Smart caching for improved dashboard performance
- Comprehensive error handling and retries
- Timezone-aware scheduling (IST)

## Database Schema

### Article Data
- News articles with sentiment scores
- Indexed for efficient querying
- Automatic deduplication
- Source attribution and metadata

### Universe Data
- Index constituents with weights
- Daily automated updates
- Historical tracking
- Multiple universe support

## Testing Infrastructure

The project includes comprehensive test coverage:
- Unit tests for all core components
- Integration tests for data pipeline
- Mocked tests for external services
- HTML structure validation for news sources
- Error handling and edge cases
- Database operation validation
- Performance benchmarking

## Project Documentation
- [Project Guidelines](./guidelines.md) - Development standards and practices
- [Project Log](./agent_project_log.md) - Technical decisions and updates
- [Companion Article](https://xumitcapital.medium.com/sentiment-analysis-dashboard-using-python-d40506e2709d)

## Technical Stack
- Python 3.10+
- DuckDB for high-performance storage
- HuggingFace Transformers (DistilRoBERTa)
- Plotly for interactive visualizations
- pytest for comprehensive testing
- UV for package management
- GitHub Actions for CI/CD
