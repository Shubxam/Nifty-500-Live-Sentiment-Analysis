from dataclasses import dataclass


@dataclass
class Article:
    """Represents a single news article."""

    ticker: str
    headline: str
    date_posted: str | None
    article_link: str
    source: str
