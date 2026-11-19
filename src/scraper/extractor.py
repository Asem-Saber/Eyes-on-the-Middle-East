import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from src.config import (
    BASE_DOMAIN,
    BACKOFF_BASE,
    MAX_PARAGRAPHS,
    MAX_RETRIES,
    ARTICLE_DELAY
)
from src.scraper.utils import extract_date, generate_article_id, to_display_date


def _text(node) -> str:
    return node.get_text(strip=True) if node else ""


def extract_body_paragraphs(body) -> List[str]:
    if not body:
        return []

    paragraphs = [
        _text(p) for p in body.find_all("p", recursive=False)
    ]
    paragraphs = [p for p in paragraphs if p]

    if MAX_PARAGRAPHS and MAX_PARAGRAPHS > 0:
        return paragraphs[:MAX_PARAGRAPHS]
    return paragraphs


def fetch_article_page(driver: webdriver.Chrome, url: str) -> Optional[BeautifulSoup]:
    """Loads an article URL with retry and exponential backoff."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver.get(url)
            time.sleep(2)
            return BeautifulSoup(driver.page_source, "html.parser")

        except TimeoutException:
            wait = BACKOFF_BASE ** attempt
            logging.warning(f"  Timeout loading {url} (attempt {attempt}/{MAX_RETRIES}). Retrying in {wait}s...")
            time.sleep(wait)
        except Exception as e:
            wait = BACKOFF_BASE ** attempt
            logging.warning(f"  Error loading {url} (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying in {wait}s...")
            time.sleep(wait)

    logging.error(f"  Failed to load {url} after {MAX_RETRIES} attempts.")
    return None


def parse_article_soup(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    page_content = soup.find("main") or soup

    body = page_content.select_one("div.wysiwyg")
    page_articles = extract_body_paragraphs(body)

    time_el = page_content.select_one("time[datetime]")
    published_iso = time_el.get("datetime", "") if time_el else ""
    article_date = to_display_date(published_iso) if published_iso else "No Date"

    return {
        "Full_Content": page_articles,
        "Date": article_date,
        "Published_At": published_iso or None,
    }


def parse_full_article(driver: webdriver.Chrome, url: str) -> Optional[Dict[str, Any]]:
    """Extracts article body, metadata, date, topics, and publisher."""
    soup = fetch_article_page(driver, url)
    if not soup:
        return None
    return parse_article_soup(soup)



def parse_feed_items(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    feed= soup.select('div[data-card-type="feed"] > ul > li> a[href]')
    for element in feed:
        href= element.get('href')
        if not href:
            link_tag = element.find("a", href=True)
            href = link_tag["href"] if link_tag else None
        if not href:
            continue

        article_url= urljoin(BASE_DOMAIN, href)

        date_el = element.select_one("span[data-homepage-article-date]")
        feed_date = to_display_date(extract_date(_text(date_el)))

        items.append({
            "id": generate_article_id(article_url),
            "Link": article_url,
            "Headline": _text(element.find("h3")) or "No Headline",
            "Summary": _text(element.find("p")) or "No Summary",
            "Date": feed_date,
        })

    return items


def parse_page_articles(driver: webdriver.Chrome,
                        known_links: Optional[set] = None) -> List[Dict[str, Any]]:
    known_links = known_links or set()

    soup = BeautifulSoup(driver.page_source, "html.parser")
    feed_items = parse_feed_items(soup)
    fresh = [item for item in feed_items if item["Link"] not in known_links]
    logging.info(
        f"{len(feed_items)} article cards on the listing page: "
        f"{len(feed_items) - len(fresh)} already stored, {len(fresh)} to fetch."
    )

    news = []
    for idx, article_data in enumerate(fresh, start=1):
        print(f"Scraping {idx}/{len(fresh)}: {article_data['Link']}")
        detailed_data = parse_full_article(driver, article_data["Link"])

        if detailed_data:
            feed_summary = article_data.get("Summary")
            if feed_summary and feed_summary != "No Summary":
                detailed_data["Full_Content"].insert(0, feed_summary)

            if detailed_data.get("Date") in (None, "", "No Date"):
                detailed_data.pop("Date", None)

            article_data.update(detailed_data)
        else:
            article_data.update({
                "Full_Content": [],
                "Date": "Error",
            })

        news.append(article_data)
        time.sleep(ARTICLE_DELAY)

    return news