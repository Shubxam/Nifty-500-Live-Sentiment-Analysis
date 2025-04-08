# Agent Project Log

## Decision Log

### 2025-02-11: Major Codebase Refactoring

**Context**: Performed a comprehensive refactoring of the codebase to improve maintainability, performance, and adherence to best practices.

**Key Decisions**:

1. **Project Structure Reorganization**
   - Created separate service modules for data fetching and sentiment analysis
   - Implemented a dedicated database management layer
   - Reason: Better separation of concerns and improved maintainability

2. **Database Management**
   - Implemented singleton pattern for DatabaseManager to prevent multiple database connections
   - Added proper indexing for frequently queried columns
   - Added connection pooling with context managers
   - Reason: Improved performance and resource management

3. **Error Handling & Logging**
   - Implemented comprehensive error handling throughout the codebase
   - Added detailed logging for better debugging and monitoring
   - Reason: Better reliability and easier troubleshooting

4. **Performance Optimizations**
   - Implemented batch processing for sentiment analysis
   - Added data caching for dashboard generation
   - Added retry mechanism with exponential backoff for API calls
   - Reason: Better resource utilization and improved reliability

5. **Configuration Management**
   - Centralized configuration in config.py
   - Added type hints and literals for better type safety
   - Reason: Easier maintenance and better type safety

## Future Improvements
   - Implementing the missing methods in news source classes (GoogleFinanceSource, YahooFinanceSource, FinologySource)
   - Adding unit tests for the new modules
   - Setting up CI/CD pipeline for automated testing
   - Creating a proper logging configuration file

### 2025-02-11: Test Infrastructure Implementation

**Context**: Implemented comprehensive test infrastructure to ensure code quality and reliability.

**Key Decisions**:

1. **Test Framework Selection**
   - Chose pytest as the primary testing framework
   - Added pytest-cov for coverage reporting
   - Added pytest-mock for mocking functionality
   - Reason: Pytest provides better fixtures and cleaner syntax for testing Python code

2. **Test Structure**
   - Created separate test files for each core component
   - Implemented mock classes and fixtures for external dependencies
   - Added comprehensive test cases for error handling and edge cases
   - Reason: Better test organization and maintenance

3. **Test Coverage Areas**
   - Database operations (connection pooling, CRUD operations)
   - API interactions (retries, error handling)
   - Data processing and validation
   - Sentiment analysis accuracy
   - Reason: Critical functionality requires thorough testing

## Implementation Details

### Database Schema
```sql
article_data:
  - id (PRIMARY KEY)
  - ticker (TEXT, INDEXED)
  - headline (TEXT)
  - date_posted (TEXT, INDEXED)
  - source (TEXT)
  - article_link (TEXT)
  - sentiment fields (FLOAT)
  - created_at (TIMESTAMP)

ticker_meta:
  - ticker (TEXT, PRIMARY KEY)
  - sector (TEXT, INDEXED)
  - industry (TEXT, INDEXED)
  - marketCap (FLOAT)
  - companyName (TEXT)
```

### Performance Considerations
- Batch size set to 100 for optimal performance
- Cache duration set to 1 hour for dashboard data
- API timeout set to 30 seconds with 3 retries
- Database indexes on frequently queried columns

## Learning Log

1. **DuckDB Optimization**
   - DuckDB performs better with proper indexing on frequently queried columns
   - Connection pooling helps prevent resource leaks

2. **Sentiment Analysis API**
   - HuggingFace API has rate limits, implemented retry mechanism
   - Batch processing significantly improves throughput

3. **Data Visualization**
   - Plotly treemap performance improves with proper data preparation
   - Caching dashboard data reduces load times

4. **Testing Best Practices**
   - Mock external dependencies (API calls, database connections)
   - Use fixtures for common test setup
   - Test both success and failure scenarios
   - Validate error handling and edge cases

## Gotchas & Reminders

1. **Timezone Handling**
   - All timestamps are in IST (Asia/Kolkata)
   - Dashboard updates at 17:30 IST daily

2. **Database Operations**
   - Always use context managers for database connections
   - Verify indexes are created after schema changes

3. **API Calls**
   - Handle rate limits with exponential backoff
   - Always validate API responses

4. **Data Processing**
   - Process data in batches for better performance
   - Validate data types before database operations

## Future Improvements

1. **Monitoring & Alerting**
   - Add monitoring for API failures
   - Implement alerting for data processing errors

2. **Testing**
   - Add unit tests for core functionality
   - Implement integration tests for data pipeline

3. **Documentation**
   - Add API documentation
   - Create user guide for dashboard

4. **Testing Enhancements**
   - Add integration tests for the full data pipeline
   - Implement performance benchmarks
   - Add load testing for database operations
   - Add mocked tests for news sources

## 2025-02-11: Implementation of News Source Classes and Metadata Fetching

### Decision Log
1. **News Source Implementation**
   - Implemented three news sources: Google Finance, Yahoo Finance, and Finology
   - Each source has specific parsing logic for its respective website structure
   - Added error handling and logging for robustness
   - Limited to 10 most recent articles per source to manage data volume

2. **Metadata Fetching Strategy**
   - Initially planned to use nsepython library but switched to direct NSE web API
   - Reason: nsepython library lacked required functionality
   - Implemented custom NSE API client with proper headers and error handling
   - Added data validation and type conversion for market cap values

### Bug/Issue Log
1. **nsepython Integration**
   - Issue: nsepython library didn't have the expected get_quote method
   - Solution: Implemented direct NSE web API calls with proper headers
   - See: services/data_fetcher.py

2. **Universe Validation**
   - Issue: DataFetcher wasn't validating universe values properly
   - Fix: Added explicit validation in __init__ method
   - Impact: Prevents invalid universe values from being used

### Learning Log
1. NSE API requires specific headers for successful requests
2. Google Finance news parsing requires handling of relative dates
3. Yahoo Finance provides timestamps that need conversion to dates
4. Finology uses relative date strings that need parsing

### Gotchas & Reminders
1. Always include User-Agent header for news source requests to avoid blocks
2. NSE API responses need careful error handling due to rate limits
3. Market cap values should be converted to float for consistency
4. Date formats vary between sources - standardized to YYYY-MM-DD

## 2025-02-12: News Source HTML Parsing Improvements

### Decision Log
1. **HTML Structure Updates**
   - Updated Google Finance parsing to use new selectors:
     - Article container: `div.z4rs2b`
     - Headline: `div.Yfwt5`
     - Date: `div.Adak`
     - Source: `div.sfyJob`
     - Link: `a` tag within container
   - Reason: More reliable and maintainable selector structure

2. **Yahoo Finance News Endpoint Change**
   - Switched from search endpoint to ticker-specific news page
   - New URL pattern: `https://finance.yahoo.com/quote/{ticker}/news`
   - New selectors:
     - Article container: `div.content.yf-82qtw3`
     - Headline: `a h3`
     - Footer: `div.publishing.yf-1weyqlp`
   - Reason: More relevant and ticker-specific news results

3. **Finology Source Structure**
   - Updated to use company-specific page: `https://ticker.finology.in/company/{ticker}`
   - Using direct article link selector: `a.newslink`
   - Headline: `span` within link
   - Date: `small` within link
   - Source: Fixed as 'Finology'
   - Reason: Better structure for news aggregation

### Bug/Issue Log
1. **Date Parsing Inconsistencies**
   - Issue: Date parsing failing with recursive mocking in tests
   - Fix: Simplified date parsing logic and improved mock handling
   - Impact: More reliable date conversion across news sources

2. **HTML Structure Changes**
   - Issue: News sources occasionally changing their HTML structure
   - Fix: Updated selectors to match current HTML structure
   - Added more robust error handling for parsing failures

### Learning Log
1. Yahoo Finance news endpoint provides more relevant results when using the ticker-specific URL
2. Google Finance date parsing needs to handle relative dates like "2 days ago"
3. Finology date format includes both date and time (e.g., "6 Feb, 2:28 PM")
4. HTML structure changes require regular monitoring and updates

### Gotchas & Reminders
1. Always check for empty lists when parsing news items
2. Handle relative URLs by prepending base URL
3. Date parsing should account for timezone differences
4. Different news sources have different date formats
5. Regular validation of HTML selectors needed

### Testing Improvements (2025-02-12)
1. **Enhanced Date Mocking**
   - Added proper datetime mocking in all news source tests
   - Fixed recursion issues in date parsing tests
   - Standardized mock date to 2024-02-09 for consistent testing
   - Reason: More reliable and predictable test behavior

2. **HTML Structure Testing**
   - Updated test fixtures with actual HTML structure from each source
   - Added validation for news source attributes:
     - Headlines
     - Publication dates
     - Article links
     - Source attribution
   - Reason: Better coverage of real-world scenarios

3. **Error Handling Tests**
   - Added test cases for common failure scenarios:
     - Network errors
     - Invalid HTML responses
     - Missing elements
     - Malformed dates
   - Reason: Improved robustness and error recovery

### Code Quality Improvements
1. **Date Parsing Standardization**
   - Implemented consistent date parsing across all news sources
   - Added validation for future dates
   - Standardized error handling and logging
   - Reason: Better maintainability and reliability

2. **News Source Architecture**
   - Maintained consistent interface across all sources
   - Added proper type hints and docstrings
   - Standardized response format
   - Reason: Better code organization and maintainability

### Validation Results
- All 11 test cases passing successfully
- Coverage maintained for critical paths
- Error handling verified for edge cases
- Date parsing working correctly across sources

## Implementation Notes (2025-02-12 15:36:10)

### News Source Observations
1. **Google Finance**
   - Headlines sometimes contain HTML entities - need to be decoded
   - Relative dates like "2 hours ago" are more common than absolute dates
   - Article links sometimes require base URL prefixing
   - Most relevant news appears in first 10 items

2. **Yahoo Finance**
   - Ticker-specific news page `/{ticker}.NS/news` provides better results than search
   - Publishing time is more accurate with new HTML selectors
   - Source attribution is consistently available in footer element
   - Article links always need https://finance.yahoo.com prefix

3. **Finology**
   - Company pages load faster than search endpoints
   - Date format is consistent: "DD MMM, HH:MM AM/PM"
   - Duplicate news items sometimes appear - need deduplication
   - Article links should use source URL since individual links aren't available

### Performance Insights
1. **Response Times**
   - Google Finance: ~0.8-1.2s per request
   - Yahoo Finance: ~0.6-0.9s per request
   - Finology: ~0.4-0.7s per request
   - Testing shows consistent response times across multiple runs

2. **Data Quality**
   - Yahoo Finance provides most consistent financial news
   - Google Finance offers broader news coverage
   - Finology focuses on company-specific announcements
   - Combined sources provide good coverage of market events

### Next Steps
1. **Monitoring**
   - Add monitoring for HTML structure changes
   - Track response times and success rates
   - Monitor date parsing accuracy
   - Set up alerts for parsing failures

2. **Improvements**
   - Implement article deduplication
   - Add caching for frequently accessed tickers
   - Consider parallel fetching from multiple sources
   - Add rate limiting for production use
   - add a new service to periodically fetch the universe tickers from nse and update in duckdb ticker_meta table

## 2025-02-12 15:36:10: Universe Updater Implementation

### Decision Log
1. **Universe Data Management**
   - Created new UniverseUpdater service for managing NSE index constituents
   - Implemented DuckDB table with schema: ticker, universe, weight, entry_date, last_updated
   - Added daily scheduled updates at market open (09:15 IST)
   - Reason: Automated tracking of index composition changes

2. **NSE Data Fetching Strategy**
   - Direct NSE API integration instead of third-party libraries
   - Cookie-based authentication for API access
   - Implemented NSE index code mapping (NIFTY 50, 100, 200, 500)
   - Reason: More reliable and direct data access

3. **Database Operations**
   - Used MERGE operation for upsert functionality
   - Implemented temporary tables for atomic updates
   - Added PRIMARY KEY constraint on (ticker, universe)
   - Reason: Ensures data consistency and handles updates efficiently

### Implementation Details
1. **Services Created**
   - universe_updater.py: Core constituent update logic
   - universe_scheduler.py: Scheduled execution service
   - Added configuration in config.py

2. **Data Structure**
```sql
universe_constituents:
  - ticker (TEXT)
  - universe (TEXT)
  - weight (FLOAT)
  - entry_date (DATE)
  - last_updated (TIMESTAMP)
  PRIMARY KEY (ticker, universe)
```

### Learning Log
1. NSE API requires session cookies for authentication
2. Index constituent weights can change daily
3. Need to handle timezone properly for scheduling (IST)
4. DuckDB MERGE operation is more efficient than delete-insert

### Gotchas & Reminders
1. Always refresh NSE cookies before API calls
2. Handle API rate limits with proper delays
3. Keep backup of previous day's constituents
4. Monitor for failed updates at market open

### Next Steps
- write github action workflows for periodic service runs.
1. Add monitoring for successful updates
2. Implement constituent change notifications
3. Add historical constituent tracking
4. Set up backup and recovery procedures

## 2025-02-13

### Documentation
- Created comprehensive architecture.md to document system design and component interactions
- Documented key architectural decisions:
  - Use of DuckDB for efficient data storage and querying
  - Implementation of singleton pattern for database connections
  - Data flow patterns between components
  - Security and performance considerations

### Decisions
- Organized architecture documentation by layers (Data Collection, Storage, Visualization) for clarity
- Included detailed component interactions to aid in future development
- Added comprehensive security and performance considerations sections to guide implementation

## 2024-03-19: Universe Update Schedule Change

### Decision Log
1. **Removed Daily Universe Updates**
   - Removed universe_scheduler.py and its associated configuration
   - Keeping only GitHub Actions workflow for monthly updates
   - Reason: Index constituent changes happen monthly, making daily updates unnecessary
   - Impact: Reduced system overhead and simplified update mechanism

### Learning Log
1. NSE indices (NIFTY 50, 100, 200, 500) typically rebalance monthly
2. GitHub Actions provides reliable scheduling for monthly maintenance tasks

### Gotchas & Reminders
1. Monthly updates occur at 00:00 UTC on the first of each month
2. Manual updates can still be triggered via GitHub Actions workflow_dispatch

## 2024-03-19: Package Management Update

### Decision Log
1. **Switched to uv for Package Management**
   - Changed GitHub Actions workflow to use uv instead of pip
   - Added explicit uv installation step in workflow
   - Used --system flag with uv to ensure global package availability
   - Reason: Better performance and reliability in package management

### Learning Log
1. uv provides faster package installation than pip
2. GitHub Actions requires explicit installation of uv using install script
3. --system flag needed for proper package visibility in GitHub Actions environment

### Gotchas & Reminders
1. uv installation requires curl and shell script execution
2. uv pip install needs --system flag in CI environments

## 2024-03-19: Universe Updater Timezone Clarification

### Decision Log
1. **Removed TZ Environment Variable from GitHub Actions**
   - Removed unnecessary TZ environment variable from universe update workflow
   - Reason: UniverseUpdater module is timezone-independent
   - Impact: Simplified workflow configuration

### Learning Log
1. Universe updates are timezone-agnostic because:
   - NSE CSV files don't contain time-sensitive data
   - No timestamp conversions are performed in the universe update process
   - Monthly index rebalancing is a point-in-time event

### Gotchas & Reminders
1. While other parts of the project use IST timezone (dashboard, data fetching), the universe update process does not need timezone information
2. Keep universe updater timezone-independent for simplicity

## 2024-03-20: UniverseUpdater Architecture Change

### Decision Log
1. **Simplified UniverseUpdater Implementation**
   - Removed NSE API integration and cookie-based authentication
   - Switched to direct file-based constituent updates
   - Reason: Simpler and more reliable implementation without external API dependencies

### Learning Log
1. File-based constituent updates are more reliable and easier to maintain
2. Removing API dependency reduces potential points of failure

### Gotchas & Reminders
1. Ensure constituent files are up-to-date before monthly updates
2. Validate file contents before database updates

## 2025-02-24 20:29:06: News Scraper Connection Issue Fix

### Bug Fix
- **Issue:** Connection errors when trying to access iinvest.cogencis.com
- **Root Cause:** Missing proper session management and cookie handling
- **Solution:** Enhanced NewsScraper class with:
  - Improved session initialization
  - Better cookie management
  - More robust retry mechanism
  - Proper SSL verification
  - Random delays between retries

### Testing Results
- Successfully connected to iinvest.cogencis.com
- Received valid response (Status 200)
- Cookie persistence confirmed
- Session management working correctly

### Learning Log
- NSE API requires proper session cookies for authentication
- Adding random delays (jitter) between retries helps avoid rate limiting
- Maintaining cookie state between requests is crucial for stable connections

### Gotchas & Reminders
- Always refresh session on retry attempts
- Keep cookies updated throughout the session
- Use proper SSL verification
- Implement exponential backoff with jitter for retries

# TODOs

- [ ] GitHub Actions workflows need to be created for periodic service runs
- [ ] implement article deduplication system
- [ ] Caching system needed for frequently accessed tickers
- [ ] Parallel fetching from multiple sources for news articles
- [ ] how to monitor for HTML structure changes in news sources
- [ ] whether to implement Historical constituent tracking
