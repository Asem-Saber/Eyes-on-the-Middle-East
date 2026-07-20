import argparse
import json
import os
import sys
import hashlib
import logging
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
from datetime import datetime, timedelta
from tqdm import tqdm
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from dotenv import load_dotenv
load_dotenv()

MAX_RETRIES = 3
BACKOFF_BASE = 2

BASE_URL = os.getenv("BASE_URL", "https://www.ajnet.me/politics")
OUTPUT_FILE = os.getenv("ARTICLES_PATH", str(ROOT_DIR / "news" / "aljazeera_articles.json"))
DATA_DIR = os.path.dirname(OUTPUT_FILE)
LOG_FILE = os.path.join(DATA_DIR, "scraper_log.txt")
DEFAULT_START_DATE = datetime(2024, 1, 1) 

# --- Setup Logging ---
os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def setup_driver():
    options = Options()

    browser_path = os.getenv("BROWSER_BINARY_PATH")
    if browser_path:
        options.binary_location = browser_path
    
    # runs in the background
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # User-Agent to prevent bot blocking
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Point to your ChromeDriver (Update path if necessary)
    # service = Service(executable_path=r"F:\Career\Web-Scraping\chromedriver.exe")
    # driver = webdriver.Chrome(service=service, options=options) 
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def accept_cookies(driver):
    """Waits for the cookie consent banner to appear and clicks the accept button."""
    print("Checking for cookie consent banner...")
    try:
        cookie_button_selector = (By.ID, "onetrust-accept-btn-handler")
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(cookie_button_selector)
        )
        driver.execute_script("arguments[0].click();", accept_btn)
        print("Cookies accepted.")
        time.sleep(1) 
    except TimeoutException:
        print("No cookie banner found within 5 seconds. Moving on.")
    except Exception as e:
        logging.warning(f"An error occurred while trying to accept cookies: {e}")

def generate_article_id(url: str) -> str:
    """Generate a unique ID from the article URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]

def load_existing_articles(): 
    """Load previously scraped articles to avoid duplicates."""
    if os.path.exists(OUTPUT_FILE): 
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f: 
            return json.load(f)
    return []

def get_latest_scraped_date(articles, default_date: datetime) -> datetime:
    """Finds the most recent date in the existing articles to use as the new target date."""
    if not articles:
        return default_date

    latest_date = default_date
    for article in articles:
        dt_str = article.get("Date", "")
        if dt_str and dt_str != "No Date":
            try:
                dt = datetime.strptime(dt_str, "%d/%m/%Y")
                if dt > latest_date:
                    latest_date = dt
            except ValueError:
                continue

    # Subtract 1 day as a buffer to catch any articles published late on that day
    buffer_date = latest_date - timedelta(days=1)
    return max(buffer_date, default_date)

def save_articles(articles): 
    """Save articles to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f: 
        json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
    logging.info(f"Saved {len(articles)} articles to {OUTPUT_FILE}")

def scroll_and_load_more(driver, target_date, max_scrolls=500): 
    """Scroll the page to load all loaded articles.
    Each time before click the "Show More Button"
    check if we reached the beginning of 2026
    if True stop the "scroll_and_load_more" function."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for i in tqdm(range(max_scrolls), desc="Scrolling & Loading"): 
        # FIRST: check the date of the last loaded article
        try: 
            articles = driver.find_elements(By.CSS_SELECTOR, "article.gc--list")
            if articles: 
                last_article = articles[-1]
                date_el = last_article.find_element(By.CSS_SELECTOR, "span.screen-reader-text")
                date_text = date_el.get_attribute("innerText").strip() 
                date_str = date_text.split(" ")[2] 

                try: 
                    article_date = datetime.strptime(date_str, "%d/%m/%Y")
                    # Break the loop if the article is older than our target
                    if article_date < target_date:
                        logging.info(f"\nReached target date: {article_date.date()}. Stopping scroll.")
                        break
                except ValueError: 
                    pass
        except Exception:
            pass

        # SECOND: click the 'show more' button if available
        try: 
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="show-more-button"]'))
            )
            show_more_btn = driver.find_element(By.CSS_SELECTOR, '[data-testid="show-more-button"]')
            driver.execute_script("arguments[0].click();", show_more_btn)
            time.sleep(2)
        except (NoSuchElementException, TimeoutException):
            pass

        # scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height: 
            logging.info("\nReached max height (bottom of available feed).")
            break
        last_height = new_height 

    logging.info("Finished scrolling.")

def _fetch_article_page(driver, url: str):
    """Load an article page with retry + exponential backoff.

    Returns the BeautifulSoup object for the page, or None after exhausting retries.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            if not soup.select('.wysiwyg p'):
                try:
                    article_link = driver.find_element(By.CSS_SELECTOR, ".article-card a")
                    driver.execute_script("arguments[0].click();", article_link)
                    time.sleep(2)
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                except NoSuchElementException:
                    pass

            return soup

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


def parse_full_article(driver, url: str):
    """Visit an individual article page and extract full content."""
    soup = _fetch_article_page(driver, url)
    if not soup:
        return None

    page_content = soup.find('main')
    if not page_content:
        return None

    page_topics = [topic.text for topic in page_content.select('.breadcrumbs a')]

    publisher_el = page_content.select_one('.contributors-list--byline a')
    publisher = publisher_el.get_text(strip=True) if publisher_el else "Al Jazeera Staff"

    summary_el = page_content.select_one('.container--video-page .article-excerpt, .article-excerpt')
    summary = summary_el.get_text(strip=True) if summary_el else None

    page_articles = [article.text for article in page_content.select('.wysiwyg p')[:6]]

    if summary:
        page_articles.insert(0, summary)

    article_date_el = page_content.select_one('.date-simple > span')
    article_date = article_date_el.get_text(strip=True).split(" ")[2] if article_date_el else "No Date"

    article_sources_el = page_content.find('div', class_='article-source')
    if article_sources_el:
        raw_source = article_sources_el.get_text(strip=True)
        article_sources = raw_source.replace('المصدر:', '').split('+')
    else:
        article_sources = []

    return {
        "Full_Content": page_articles,
        "Publisher": publisher,
        "Topics": page_topics,
        "Sources": article_sources,
        "Date": article_date
    }

def parse_page_articles(driver, dry_run=False):
    """Extract basic info from the section page, then visit each article link.

    In dry-run mode, only the feed-level metadata is collected (no individual
    article pages are visited).
    """
    news = []
    soup = BeautifulSoup(driver.page_source, "html.parser")

    thumbnail_articles = soup.select('ul.themed-featured-posts-list li')
    articles_section = soup.find_all("article", class_="gc--list")
    all_article_elements = thumbnail_articles + articles_section

    for idx, item in enumerate(all_article_elements):
        link_tag = item.find("a", href=True)
        if not link_tag:
            continue

        article_link = link_tag['href']
        full_article_link = f"https://www.ajnet.me{article_link}"

        article_header_el = item.find("h2")
        article_header = article_header_el.get_text(strip=True) if article_header_el else "No Headline"

        article_summary_el = item.find("p", class_="article-card__excerpt")
        article_summary = article_summary_el.get_text(strip=True) if article_summary_el else "No Summary"

        article_data = {
            "id": generate_article_id(full_article_link),
            "Link": full_article_link,
            "Headline": article_header,
            "Summary": article_summary,
        }

        if dry_run:
            print(f"[dry-run] {idx + 1}/{len(all_article_elements)}: {article_header}")
            news.append(article_data)
            continue

        print(f"Scraping {idx + 1}/{len(all_article_elements)}: {full_article_link}")
        detailed_data = parse_full_article(driver, full_article_link)

        if detailed_data:
            article_data.update(detailed_data)
        else:
            article_data.update({
                "Full_Content": [], "Publisher": "Error", "Topics": [], "Sources": [], "Date": "Error"
            })

        news.append(article_data)

    return news

def filter_by_date(articles: list, target_date: datetime) -> list:
    """Filter articles to only include those from target_date onwards."""
    filtered = []
    for article in articles:
        dt_str = article.get("Date", "")
        if dt_str and dt_str != "No Date":
            try:
                dt = datetime.strptime(dt_str, "%d/%m/%Y")
                if dt >= target_date:
                    filtered.append(article)
            except ValueError:
                filtered.append(article)
        else:
            filtered.append(article)
            
    return filtered

def sort_articles_desc(articles):
    """Sort articles by date in descending order (newest first)."""
    def get_date_key(article):
        dt_str = article.get("Date", "")
        try:
            return datetime.strptime(dt_str, "%d/%m/%Y")
        except ValueError:
            # Push invalid/missing dates to the bottom
            return datetime.min 
            
    return sorted(articles, key=get_date_key, reverse=True)

def run_scraper(dry_run=False):
    """Main scraper entry point."""
    logging.info("=" * 60)
    logging.info("--- Aljazeera Scraper Started ---")
    if dry_run:
        logging.info("DRY-RUN mode — no data will be saved.")
        print("=== DRY-RUN MODE ===")

    driver = None
    try:
        existing = load_existing_articles()
        logging.info(f"Found {len(existing)} existing articles.")

        target_date = get_latest_scraped_date(existing, DEFAULT_START_DATE)
        logging.info(f"Target date for scraping set to: {target_date.date()}")

        driver = setup_driver()

        driver.get(BASE_URL)
        time.sleep(3)

        accept_cookies(driver)

        scroll_and_load_more(driver, target_date)
        new_articles = parse_page_articles(driver, dry_run=dry_run)

        existing_urls = {article["Link"] for article in existing}
        unique_new_articles = [
            article for article in new_articles
            if article["Link"] not in existing_urls
        ]
        logging.info(f"Found {len(unique_new_articles)} strictly new articles out of {len(new_articles)} scraped on the feed.")

        if dry_run:
            print(f"\n--- Dry-run summary ---")
            print(f"  Existing articles: {len(existing)}")
            print(f"  Articles on feed:  {len(new_articles)}")
            print(f"  New (unique):      {len(unique_new_articles)}")
            print(f"  Target date:       {target_date.date()}")
            print(f"  Nothing was saved.")
            return

        all_articles = existing + unique_new_articles

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
        if driver:
            driver.quit()
        logging.info("--- Scraper Stopped ---\n")
        logging.info("=" * 60)


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Al Jazeera politics articles.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be scraped without saving any data or visiting article pages.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_scraper(dry_run=args.dry_run)