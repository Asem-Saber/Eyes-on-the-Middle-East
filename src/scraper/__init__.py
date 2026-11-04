from src.scraper.driver import setup_driver, get_driver, accept_cookies
from src.scraper.crawler import scroll_and_load_more
from src.scraper.extractor import (
    parse_page_articles,
    parse_full_article,
    parse_article_soup,
    parse_feed_items,
    extract_body_paragraphs,
)
from src.scraper.storage import load_existing_articles, save_articles


def run_scraper(*args, **kwargs):
    """Lazy wrapper to execute scraping pipeline."""
    from src.scraper.main import run_scraper as _run_scraper
    return _run_scraper(*args, **kwargs)


__all__ = [
    "run_scraper",
    "setup_driver",
    "get_driver",
    "accept_cookies",
    "scroll_and_load_more",
    "parse_page_articles",
    "parse_full_article",
    "parse_article_soup",
    "parse_feed_items",
    "extract_body_paragraphs",
    "load_existing_articles",
    "save_articles",
]
