import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DATE_REGEX = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")

ISO_REGEX = re.compile(r"\b(\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?)\b")

DISPLAY_DATE_FORMAT = "%d/%m/%Y"


def generate_article_id(url: str) -> str:
    """Generate a 12-char unique MD5 hash from the article URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def extract_date(text: str) -> str:
    """Extracts a DD/MM/YYYY date substring using regex, or returns 'No Date'."""
    if not text:
        return "No Date"
    match = DATE_REGEX.search(text)
    return match.group(1) if match else "No Date"


def extract_iso_date(text: str) -> str:
    """Extracts an ISO-8601 timestamp substring, or returns 'No Date'."""
    if not text:
        return "No Date"
    match = ISO_REGEX.search(text)
    return match.group(1) if match else "No Date"


def parse_date(date_str: str) -> Optional[datetime]:
    """Safely parses a date string into datetime, returning None on failure."""
    if not date_str or date_str in ("No Date", "Error"):
        return None

    try:
        return datetime.strptime(date_str, DISPLAY_DATE_FORMAT)
    except ValueError:
        pass

    try:
        return datetime.fromisoformat(str(date_str).replace("Z", "")).replace(tzinfo=None)
    except ValueError:
        return None


def to_display_date(value: Any) -> str:
    """Normalise anything date-ish into DD/MM/YYYY (the project's stored format)."""
    if isinstance(value, datetime):
        return value.strftime(DISPLAY_DATE_FORMAT)
    parsed = parse_date(str(value or ""))
    return parsed.strftime(DISPLAY_DATE_FORMAT) if parsed else "No Date"


def article_sort_key(article: Dict[str, Any]) -> datetime:
    """Sort on the precise timestamp when we have one, else the display date."""
    return (
        parse_date(article.get("Published_At", ""))
        or parse_date(article.get("Date", ""))
        or datetime.min
    )


def complete_links(articles: List[Dict[str, Any]]) -> set:
    """Links we already hold in full.

    Error stubs are deliberately excluded, so a fetch that failed on an earlier
    run is retried on the next one instead of sticking around forever.
    """
    return {
        article["Link"] for article in articles
        if article.get("Link") and article.get("Published_At") and article.get("Full_Content")
    }


def get_latest_scraped_date(articles: List[Dict[str, Any]], default_date: datetime,
                            buffer_hours: float = 24) -> datetime:
    """Finds the latest published article date minus a safety buffer."""
    if not articles:
        return default_date

    latest_date = default_date
    for article in articles:
        dt = article_sort_key(article)
        if dt != datetime.min and dt > latest_date:
            latest_date = dt

    buffer_date = latest_date - timedelta(hours=buffer_hours)
    return max(buffer_date, default_date)


def filter_by_date(articles: List[Dict[str, Any]], target_date: datetime) -> List[Dict[str, Any]]:
    """Filter articles to only include those published from target_date onwards."""
    filtered = []
    for article in articles:
        dt = article_sort_key(article)
        if dt != datetime.min:
            if dt >= target_date:
                filtered.append(article)
        else:
            filtered.append(article)
    return filtered


def sort_articles_desc(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort articles by date in descending order (newest first)."""
    return sorted(articles, key=article_sort_key, reverse=True)


def deduplicate(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse duplicates on `id`, falling back to `Link`."""
    merged: Dict[str, Dict[str, Any]] = {}
    for article in articles:
        key = str(article.get("id") or article.get("Link") or "")
        if not key:
            continue
        merged[key] = article
    return list(merged.values())
