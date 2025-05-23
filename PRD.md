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
  
### work with pre-existing Nifty Index

- user selects a Official Nifty Index from a dropdown.
- 2 tabs show up: Performance Analytics and Sentiment Analytics.
- Performance Analytics:
  - choose another Nifty Index to compare against. [optional]
  - show the index-value graph for both indices.
  - performance statistics for both indices for pre-determined periods choosable from a dropdown.
  - show the index constituents in a table along with individual performance numbers and composite score.
- Sentiment Analytics:
  - select the date-range.
  - hierarchial tree-map to show the sentiment of user generated index/sectors/stocks.
  - drop-down to choose a stock, and a table shows related news-articles.


### Create an Index of their own

- user sees a search box to input the query; his idea of index.
- user sees a progress bar or loading banner as the api request is sent and processed in the background.
- 2 tabs show up: Performance Analytics and Sentiment Analytics.
- Performance Analytics:
  - user selects a Nifty Index as benchmark.
  - sees the index-value graph for his generated index and benchmark.
  - performance statistics for both indices for pre-determined periods choosable from a dropdown.
  - show the index constituents in a table along with individual performance numbers and composite score.
- Sentiment Analytics:
  - select the date-range.
  - hierarchial tree-map to show the sentiment of user generated index/sectors/stocks.
  - drop-down to choose a stock, and a table shows related news-articles.


## Internal Specifics


## Minimum Viable Product