# Adding deduplication of articles based on headline and date

## Description
Currently, the system may store duplicate articles when fetching from multiple sources or during different data collection runs. We need to implement a deduplication mechanism to ensure that articles with the same headline and date are not stored multiple times in the database.

## Problem
- Articles with identical headlines and dates may be fetched from different sources
- The current database schema doesn't enforce uniqueness on headline + date combination
- Duplicate articles affect sentiment analysis accuracy and dashboard display

## Proposed Solution
1. Modify the database schema to add a unique constraint or index on (headline, date_posted)
2. Enhance the DatabaseManager.insert_articles() method to handle potential duplicates:
   - Option 1: Use UPSERT pattern (INSERT ... ON CONFLICT DO NOTHING)
   - Option 2: Pre-filter duplicates before insertion

## Technical Implementation
- Update the _setup_database() method in db_manager.py to add unique constraint
- Modify insert_articles() to handle duplicate detection
- Add unit tests to verify deduplication works correctly

## Benefits
- Cleaner data for sentiment analysis
- More accurate dashboard visualization
- Improved performance by reducing database size and query complexity

## Priority
Medium

## Estimated Effort
2-3 hours

