import time
import logging
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)

from src.config import FEED_LOAD_TIMEOUT
from src.scraper.utils import extract_date, parse_date


def _feed_is_loading(driver: webdriver.Chrome) -> bool:
    try:
        feed = driver.find_element(By.CSS_SELECTOR, "ul[aria-busy]")
        return feed.get_attribute("aria-busy") == "true"
    except (NoSuchElementException, StaleElementReferenceException):
        return False


def _wait_until_loaded(driver: webdriver.Chrome, timeout: float = FEED_LOAD_TIMEOUT) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _feed_is_loading(driver):
            return
        time.sleep(0.25)


def _oldest_loaded_date(driver: webdriver.Chrome):
    """Date of the last row currently in the DOM, or None."""
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "ul[aria-busy] > li")
        if not rows:
            return None
        date_el = rows[-1].find_element(By.CSS_SELECTOR, "span[data-homepage-article-date]")
        date_text = date_el.get_attribute("innerText").strip()
        return parse_date(extract_date(date_text))
    except (NoSuchElementException, StaleElementReferenceException):
        return None


def scroll_and_load_more(driver: webdriver.Chrome, target_date: datetime, max_scrolls: int = 500) -> None:
    last_count = len(driver.find_elements(By.CSS_SELECTOR, "ul[aria-busy] > li"))

    for i in range(max_scrolls):
        article_date = _oldest_loaded_date(driver)
        if article_date and article_date < target_date:
            logging.info(f"Reached target date: {article_date.date()}. Stopping.")
            break

        try:
            show_more_btn = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(., 'اعرض المزيد')]"))
            )
            if show_more_btn.get_attribute("aria-disabled") == "true":
                logging.info("'Show more' is disabled (bottom of available feed).")
                break

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", show_more_btn)
            driver.execute_script("arguments[0].click();", show_more_btn)
            _wait_until_loaded(driver)
        except (NoSuchElementException, TimeoutException):
            logging.info("No 'show more' button found (bottom of available feed).")
            break
        except Exception as e:
            logging.warning(
                f"Browser connection lost while expanding feed (iteration {i}): {e}. Stopping early."
            )
            break

        new_count = len(driver.find_elements(By.CSS_SELECTOR, "ul[aria-busy] > li"))
        if new_count == last_count:
            logging.info("Row count did not grow (bottom of available feed).")
            break
        last_count = new_count
    else:
        logging.warning(f"Hit the max_scrolls={max_scrolls} safety limit.")

    logging.info(f"Finished expanding feed. {last_count} rows loaded.")
