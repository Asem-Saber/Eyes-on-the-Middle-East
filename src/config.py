import logging
from pathlib import Path
from datetime import datetime, date
from typing import Any, Dict, List, Union
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yml"


def resolve_path(path_str: Union[str, Path]) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else PROJECT_ROOT / p


def load_yaml_config(path: Path = CONFIG_PATH) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return config


CONFIG = load_yaml_config()

PATHS_CONFIG = CONFIG.get("paths", {})
SCRAPER_CONFIG = CONFIG.get("scraper", {})

OUTPUT_FILE = resolve_path(PATHS_CONFIG.get("articles_file", "data/articles.json"))
DATA_DIR = OUTPUT_FILE.parent
LOG_FILE = resolve_path(PATHS_CONFIG.get("scraper_log", "logs/scraper_log.txt"))

BASE_URL = SCRAPER_CONFIG.get("base_url", "https://www.ajnet.me/politics")
BASE_DOMAIN = SCRAPER_CONFIG.get("base_domain", "https://www.ajnet.me")


MAX_RETRIES = int(SCRAPER_CONFIG.get("max_retries", 3))
BACKOFF_BASE = int(SCRAPER_CONFIG.get("backoff_base", 2))
MAX_SCROLLS = int(SCRAPER_CONFIG.get("max_scrolls", 500))
RESCAN_BUFFER_HOURS = float(SCRAPER_CONFIG.get("rescan_buffer_hours", 24))
HEADLESS = bool(SCRAPER_CONFIG.get("headless", True))
PAGE_LOAD_TIMEOUT = int(SCRAPER_CONFIG.get("page_load_timeout", 30))

ARTICLE_DELAY = float(SCRAPER_CONFIG.get("article_delay", 1.0))

FEED_LOAD_TIMEOUT = float(SCRAPER_CONFIG.get("feed_load_timeout", 10))

MAX_PARAGRAPHS = int(SCRAPER_CONFIG.get("max_paragraphs", 6))

USER_AGENT = SCRAPER_CONFIG.get(
    "user_agent",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)

_raw_start_date = SCRAPER_CONFIG.get("default_start_date", "2026-01-01")
if isinstance(_raw_start_date, datetime):
    DEFAULT_START_DATE = _raw_start_date
elif isinstance(_raw_start_date, date):
    DEFAULT_START_DATE = datetime(_raw_start_date.year, _raw_start_date.month, _raw_start_date.day)
elif isinstance(_raw_start_date, str):
    DEFAULT_START_DATE = datetime.strptime(_raw_start_date, "%Y-%m-%d")
else:
    DEFAULT_START_DATE = datetime(2026, 1, 1)


def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
