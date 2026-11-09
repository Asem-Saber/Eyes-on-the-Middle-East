import time
import logging
from datetime import datetime
from typing import Any, Dict, List

from src.config import (
    BASE_URL,
    DEFAULT_START_DATE,
    LOG_FILE,
    MAX_SCROLLS,
    RESCAN_BUFFER_HOURS,
    setup_logging,
)
from src.scraper.driver import get_driver, accept_cookies
from src.scraper.storage import load_existing_articles, save_articles
from src.scraper.utils import (
    complete_links,
    deduplicate,
    filter_by_date,
    get_latest_scraped_date,
    sort_articles_desc,
)
from src.scraper.crawler import scroll_and_load_more
from src.scraper.extractor import parse_page_articles


def scrape_section(target_date: datetime,
                   section_url: str = BASE_URL,
                   known_links: set = None) -> List[Dict[str, Any]]:
    """Expands and scrapes the listing page in a single browser session."""
    with get_driver() as driver:
        logging.info(f"--- Scraping section: {section_url} ---")
        driver.get(section_url)
        time.sleep(3)

        accept_cookies(driver)
        scroll_and_load_more(driver, target_date, max_scrolls=MAX_SCROLLS)
        return parse_page_articles(driver, known_links=known_links)


def run_scraper() -> None:
    """Executes the full scraping extraction pipeline."""
    setup_logging()
    logging.info("=" * 60)
    logging.info("--- Aljazeera Scraper Started ---")

    try:
        existing = load_existing_articles()
        logging.info(f"Found {len(existing)} existing articles.")

        known = complete_links(existing)
        logging.info(f"{len(known)} of them are complete and will be skipped on the feed.")

        target_date = get_latest_scraped_date(existing, DEFAULT_START_DATE, RESCAN_BUFFER_HOURS)
        logging.info(f"Target date for scraping set to: {target_date}")

        new_articles = scrape_section(target_date, known_links=known)

        unique_new_articles = [
            article for article in new_articles if article["Link"] not in known
        ]
        logging.info(
            f"Found {len(unique_new_articles)} strictly new articles "
            f"out of {len(new_articles)} fetched from the feed."
        )

        if not new_articles:
            logging.warning(
                "Scraped 0 articles. If this is unexpected, the site layout may have "
                "changed again — check the selectors in ajnet-selectors.md."
            )

        all_articles = existing + unique_new_articles

        logging.info(f"De-duplicating {len(all_articles)} total articles...")
        all_articles = deduplicate(all_articles)

        logging.info(f"Filtering {len(all_articles)} total articles...")
        all_articles = filter_by_date(all_articles, DEFAULT_START_DATE)

        logging.info("Sorting articles by date (descending)...")
        all_articles = sort_articles_desc(all_articles)

        logging.info(f"Done! Returning {len(all_articles)} articles from {DEFAULT_START_DATE.year} onwards.")

        save_articles(all_articles)
        logging.info(f"Scraping complete. Total articles saved: {len(all_articles)}")

    except Exception as e:
        logging.error(f"Scraper failed with a critical error: {e}", exc_info=True)
        print(f"Critical Error encountered. Check {LOG_FILE} for details.")

    finally:
        logging.info("--- Scraper Stopped ---\n")
        logging.info("=" * 60)


if __name__ == "__main__":
    run_scraper()