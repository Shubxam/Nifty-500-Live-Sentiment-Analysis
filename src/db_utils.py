# implement duckdb cursor to write to same db with multiple threads
import pandas as pd
from loguru import logger

from database import DatabaseManager

INDEX_CONSTITUENTS_URL: dict[str, str] = {
    "nifty_500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "nifty_200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
    "nifty_100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "nifty_50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
}

query_duplicates_cmd = """
with duplicates_cte as (
select 
  ROW_NUMBER() OVER (
    partition by ticker, headline order by created_at asc
  ) as rn, 
  ticker, 
  headline, 
  date_posted, 
  article_link, 
  created_at 
from article_data
) select * from duplicates_cte where rn > 1;
"""

delete_duplicates_cmd = """
with duplicates_cte as (
  -- cte table with duplicates
  select
    rowid, rn
  from (
    -- filter duplicates and get their rowid
    select 
    rowid,
    ROW_NUMBER() OVER (
      partition by ticker, headline order by created_at asc
    ) as rn 
    from article_data
  ) sub
  where rn > 1
)
-- delete statement
delete from article_data
where rowid in (select rowid from duplicates_cte);
"""

def query_duplicates(return_df: bool = False) -> pd.DataFrame | None:
    with DatabaseManager().get_connection() as conn:
        # Select duplicates
        duplicates_df: pd.DataFrame = conn.execute(query_duplicates_cmd).fetchdf()
        duplicate_rows_count: int = duplicates_df.shape[0]

        if duplicate_rows_count == 0:
            logger.info("No duplicates found in database")
            return None

        logger.info(f"{duplicate_rows_count} duplicates found in database")

        if return_df:
            return duplicates_df


def deduplicate_db() -> None:
    duplicates_count: int = query_duplicates(return_df=True).shape[0]

    if duplicates_count == 0:
        logger.info("No duplicates found to delete.")
        return

    with DatabaseManager().get_connection() as conn:
        conn.execute(delete_duplicates_cmd)
        logger.success(f"Deleted {duplicates_count} duplicate rows from database.")


# todo: add function to update ticker_meta everyday
# todo: add function to update indices_constituents 

if __name__ == "__main__":
    query_duplicates()
    # deduplicate_db()
