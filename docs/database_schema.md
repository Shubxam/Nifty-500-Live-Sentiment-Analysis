# Database Schema Design
# Nifty Index Generator - Extended Database Schema

## Overview

This document outlines the comprehensive database schema for the Nifty Index Generator project, extending from the existing sentiment analysis database. The design supports:

- Daily OHLCV data storage from April 1, 2023
- Ticker/sector-based sharding for optimal query performance
- Custom index generation and tracking
- Fundamental data storage and computed metrics
- User query logging and analytics

## Database Technology

- **Primary Database**: DuckDB (with migration path to Cloudflare D1)
- **Sharding Strategy**: Ticker/sector-based for OHLCV data
- **Data Range**: Daily data from April 1, 2023 onwards
- **Storage Pattern**: Computed metrics stored in database for performance

## Sharding Architecture

### Database Structure
- `main.db` - Core tables (tickers, custom_indices, shard_mapping)
- `nifty50_prices.db` - OHLCV for Nifty 50 stocks
- `banking_prices.db` - OHLCV for banking sector stocks
- `pharma_prices.db` - OHLCV for pharma sector stocks
- `misc_prices.db` - OHLCV for remaining stocks

### Sharding Benefits
1. **Index Calculation Efficiency**: Single query per shard instead of per ticker
2. **Sector Analysis**: Sector-specific queries hit only relevant shards
3. **Parallel Processing**: Multiple shards can be queried simultaneously
4. **Storage Management**: Archive old sectors independently
5. **Performance Isolation**: Heavy queries on one sector don't affect others

## Core Database Schema

### Core Stock Data Tables

#### tickers
```sql
CREATE TABLE tickers (
    ticker VARCHAR PRIMARY KEY,
    isin_code VARCHAR UNIQUE,
    company_name VARCHAR NOT NULL,
    sector VARCHAR,
    industry VARCHAR,
    listing_date DATE,
    face_value DECIMAL(10,2),
    total_shares_outstanding BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### shard_mapping
```sql
-- Shard mapping table (stored in main database)
CREATE TABLE shard_mapping (
    ticker VARCHAR PRIMARY KEY,
    shard_id VARCHAR NOT NULL, -- e.g., 'nifty50', 'banking', 'pharma', 'misc'
    sector VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker) REFERENCES tickers(ticker)
);
```

#### price_data (replicated across shards)
```sql
CREATE TABLE price_data (
    ticker VARCHAR NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(12,4) NOT NULL,
    high_price DECIMAL(12,4) NOT NULL,
    low_price DECIMAL(12,4) NOT NULL,
    close_price DECIMAL(12,4) NOT NULL,
    volume BIGINT,
    adjusted_close DECIMAL(12,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, date)
);
```

#### market_data (sharded by ticker)
```sql
CREATE TABLE market_data (
    ticker VARCHAR NOT NULL,
    date DATE NOT NULL,
    free_float_percentage DECIMAL(5,2), -- 0.00 to 100.00
    market_cap DECIMAL(15,2),
    free_float_market_cap DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, date)
);
```

#### index_constituents
```sql
CREATE TABLE index_constituents (
    index_name VARCHAR NOT NULL,
    ticker VARCHAR NOT NULL,
    weight DECIMAL(8,4), -- percentage weight
    effective_date DATE NOT NULL,
    end_date DATE, -- NULL for current constituents
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (index_name, ticker, effective_date),
    FOREIGN KEY (ticker) REFERENCES tickers(ticker)
);
```

### Fundamental Data Tables

#### fundamental_data
```sql
CREATE TABLE fundamental_data (
    ticker VARCHAR NOT NULL,
    quarter DATE NOT NULL, -- YYYY-MM-DD format (quarter end date)
    revenue DECIMAL(15,2),
    net_income DECIMAL(15,2),
    eps DECIMAL(8,4),
    book_value_per_share DECIMAL(8,4),
    debt_to_equity DECIMAL(8,4),
    roe DECIMAL(8,4),
    roa DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, quarter),
    FOREIGN KEY (ticker) REFERENCES tickers(ticker)
);
```

#### computed_metrics (sharded by ticker)
```sql
CREATE TABLE computed_metrics (
    ticker VARCHAR NOT NULL,
    date DATE NOT NULL,
    pe_ratio DECIMAL(8,4),
    pb_ratio DECIMAL(8,4),
    dividend_yield DECIMAL(8,4),
    revenue_growth_yoy DECIMAL(8,4),
    eps_growth_yoy DECIMAL(8,4),
    beta DECIMAL(8,4),
    volatility_30d DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, date)
);
```

### Custom Index and User Data Tables

#### custom_indices
```sql
CREATE TABLE custom_indices (
    index_id VARCHAR PRIMARY KEY,
    index_name VARCHAR NOT NULL,
    user_query TEXT NOT NULL,
    generation_method ENUM('gemini_api', 'sql_query') NOT NULL,
    base_date DATE NOT NULL,
    creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'archived', 'failed') DEFAULT 'active'
);
```

#### custom_index_constituents
```sql
CREATE TABLE custom_index_constituents (
    index_id VARCHAR NOT NULL,
    ticker VARCHAR NOT NULL,
    weight DECIMAL(8,4) NOT NULL,
    rationale TEXT, -- LLM explanation for inclusion
    confidence_score DECIMAL(5,4), -- 0.0000 to 1.0000
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (index_id, ticker),
    FOREIGN KEY (index_id) REFERENCES custom_indices(index_id),
    FOREIGN KEY (ticker) REFERENCES tickers(ticker)
);
```

#### query_logs
```sql
CREATE TABLE query_logs (
    log_id VARCHAR PRIMARY KEY,
    user_query TEXT NOT NULL,
    processed_query TEXT,
    generation_method VARCHAR NOT NULL,
    result_count INTEGER,
    processing_time_ms INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    index_id VARCHAR,
    FOREIGN KEY (index_id) REFERENCES custom_indices(index_id)
);
```

### Performance and Analytics Tables

#### index_performance
```sql
CREATE TABLE index_performance (
    index_id VARCHAR NOT NULL,
    date DATE NOT NULL,
    index_value DECIMAL(12,4) NOT NULL,
    returns_1d DECIMAL(8,4),
    returns_1w DECIMAL(8,4),
    returns_1m DECIMAL(8,4),
    returns_1y DECIMAL(8,4),
    volatility DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (index_id, date),
    FOREIGN KEY (index_id) REFERENCES custom_indices(index_id)
);
```

#### corporate_actions
```sql
CREATE TABLE corporate_actions (
    ticker VARCHAR NOT NULL,
    action_date DATE NOT NULL,
    action_type ENUM('split', 'bonus', 'dividend', 'rights', 'merger') NOT NULL,
    ratio_numerator INTEGER,
    ratio_denominator INTEGER,
    amount DECIMAL(10,4), -- for dividends
    adjustment_factor DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, action_date, action_type),
    FOREIGN KEY (ticker) REFERENCES tickers(ticker)
);
```

### Sentiment Analysis Tables (Modified)

#### article_data
```sql
CREATE TABLE article_data (
    ticker VARCHAR NOT NULL,
    headline VARCHAR NOT NULL,
    date_posted DATE,
    source VARCHAR,
    article_link VARCHAR,
    neutral_sentiment DECIMAL(6,4),
    negative_sentiment DECIMAL(6,4),
    positive_sentiment DECIMAL(6,4),
    compound_sentiment DECIMAL(6,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, headline),
    FOREIGN KEY (ticker) REFERENCES tickers(ticker)
);
```

## Query Patterns

### Index Performance Calculation
```sql
-- 1. Get shard locations for index constituents
SELECT DISTINCT shard_id
FROM shard_mapping sm
JOIN custom_index_constituents cic ON sm.ticker = cic.ticker
WHERE cic.index_id = 'fintech_index_123';

-- 2. Query each shard database directly
-- banking_prices.db:
SELECT ticker, date, close_price
FROM price_data
WHERE ticker IN ('HDFCBANK', 'ICICIBANK', 'AXISBANK')
AND date BETWEEN '2023-04-01' AND '2024-01-01';
```

### Sector Analysis
```sql
-- Get all banking sector data from single shard
SELECT p.ticker, p.date, p.close_price, m.market_cap
FROM price_data p
JOIN market_data m ON p.ticker = m.ticker AND p.date = m.date
WHERE p.date BETWEEN '2023-04-01' AND '2024-01-01';
```

## Suggested Shard Groups

```sql
-- Major indices
INSERT INTO shard_mapping VALUES
('RELIANCE', 'nifty50', 'Oil & Gas'),
('TCS', 'nifty50', 'IT Services'),
('HDFCBANK', 'nifty50', 'Private Bank'),

-- Sector-based sharding
('HDFCBANK', 'banking', 'Private Bank'),
('ICICIBANK', 'banking', 'Private Bank'),
('DRREDDY', 'pharma', 'Pharmaceuticals'),
('SUNPHARMA', 'pharma', 'Pharmaceuticals'),

-- Overflow shard for miscellaneous
('SMALLCAP1', 'misc', 'Textiles'),
('SMALLCAP2', 'misc', 'Chemicals');
```

## Migration Strategy

### Phase 1: Schema Creation
1. Create new table structures in test environment
2. Set up sharding infrastructure
3. Create migration scripts

### Phase 2: Data Migration
1. Migrate existing data:
   - `ticker_meta` → `tickers`
   - `indices_constituents` → `index_constituents`
   - Update `article_data` with foreign key constraints

### Phase 3: Historical Data Population
1. Populate OHLCV data from April 1, 2023
2. Set up shard mapping based on sectors
3. Populate fundamental and market data

### Phase 4: Application Updates
1. Update database connection logic for sharding
2. Modify existing sentiment analysis code
3. Implement new index generation features

### Phase 5: Scheduled Jobs Setup
1. Daily OHLCV data updates
2. Quarterly fundamental data updates
3. Daily computed metrics calculation
4. Corporate actions monitoring

## Data Retention and Archival

- **Price Data**: Full historical data from April 1, 2023
- **Sentiment Data**: Rolling 2-year window (configurable)
- **Query Logs**: Rolling 1-year window for analytics
- **Custom Indices**: Permanent storage with archival status

## Performance Considerations

- **Indexing**: Composite indexes on (ticker, date) for time-series queries
- **Partitioning**: Consider monthly partitions within shards for very large datasets
- **Caching**: Computed metrics cached for frequently accessed date ranges
- **Compression**: Enable compression for historical price data

## Future Scalability

- **Cloud Migration**: Schema designed for easy migration to Cloudflare D1
- **Horizontal Scaling**: Shard-based architecture supports adding more shards
- **Real-time Updates**: Schema supports streaming data ingestion
- **Multi-region**: Sharding strategy supports geographical distribution
