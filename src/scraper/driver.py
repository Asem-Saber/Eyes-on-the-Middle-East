import time
import logging
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from src.config import HEADLESS, PAGE_LOAD_TIMEOUT, USER_AGENT


def setup_driver() -> webdriver.Chrome:
    """Configures and initializes Chrome webdriver using Selenium Manager."""
    options = Options()

    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument(f"user-agent={USER_AGENT}")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


@contextmanager
def get_driver():
    """Context manager ensuring driver terminates cleanly on normal exit or error."""
    driver = setup_driver()
    try:
        yield driver
    finally:
        driver.quit()


def accept_cookies(driver: webdriver.Chrome) -> None:
    logging.info("Checking for cookie consent banner...")
    try:
        cookie_button_selector = (By.ID, "onetrust-accept-btn-handler")
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(cookie_button_selector)
        )
        driver.execute_script("arguments[0].click();", accept_btn)
        logging.info("Cookies accepted.")
        time.sleep(1)
    except TimeoutException:
        logging.info("No cookie banner found within 5 seconds. Moving on.")
    except Exception as e:
        logging.warning(f"An error occurred while trying to accept cookies: {e}")