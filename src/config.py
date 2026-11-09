import logging
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Union

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env", override=False)

CONFIG_PATH = Path(os.getenv("CONFIG_PATH") or PROJECT_ROOT / "config" / "config.yml")


def resolve_path(path_str: Union[str, Path]) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else PROJECT_ROOT / p


def load_yaml_config(path: Path = CONFIG_PATH) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return config


def _env(name: str, default: Any = None) -> Any:
    """Non-empty environment value, else the default."""
    value = os.getenv(name)
    return value if value else default


CONFIG = load_yaml_config()

PATHS_CONFIG = CONFIG.get("paths", {})
SCRAPER_CONFIG = CONFIG.get("scraper", {})
ML_CONFIG = CONFIG.get("ml_service", {})
TRAINING_CONFIG = CONFIG.get("training", {})
LLM_CONFIG = CONFIG.get("llm", {})


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


MODEL_NAME = ML_CONFIG.get("model_name", "news_topics_model")
MODEL_DIR = resolve_path(_env("TOPIC_MODEL_DIR", ML_CONFIG.get("model_dir", "models/news_topics_model")))
EMBEDDING_MODEL = _env(
    "EMBEDDING_MODEL",
    ML_CONFIG.get("embedding_model", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"),
)

MIN_TOPIC_SIZE = int(_env("MIN_TOPIC_SIZE", ML_CONFIG.get("min_topic_size", 5)))
MIN_CLUSTER_SIZE = int(ML_CONFIG.get("min_cluster_size") or MIN_TOPIC_SIZE)
MIN_SAMPLES = int(ML_CONFIG.get("min_samples", 3))
N_NEIGHBORS = int(ML_CONFIG.get("n_neighbors", 15))
N_COMPONENTS = int(ML_CONFIG.get("n_components", 5))
TOP_N_WORDS = int(ML_CONFIG.get("top_n_words", 10))
NR_TOPICS = ML_CONFIG.get("nr_topics", "auto")
LANGUAGE = ML_CONFIG.get("language", "arabic")
CALCULATE_PROBABILITIES = bool(ML_CONFIG.get("calculate_probabilities", True))

MAX_SEQ_LENGTH = int(ML_CONFIG.get("max_seq_length", 128))
EMBED_BATCH_SIZE = int(_env("EMBED_BATCH_SIZE", ML_CONFIG.get("batch_size", 32)))
EMBED_DEVICE = _env("EMBED_DEVICE", ML_CONFIG.get("device"))
SEED = int(ML_CONFIG.get("seed", 42))
SHUFFLE_SEED = int(ML_CONFIG.get("shuffle_seed", 101))

NGRAM_RANGE = tuple(ML_CONFIG.get("ngram_range", (1, 2)))
MIN_DF = int(ML_CONFIG.get("min_df", 2))
MAX_DF = float(ML_CONFIG.get("max_df", 0.95))
MMR_DIVERSITY = float(ML_CONFIG.get("mmr_diversity", 0.3))


TRAINING_MIN_WORDS = int(TRAINING_CONFIG.get("min_words", 60))
TRAINING_SECTIONS = list(TRAINING_CONFIG.get("sections") or [])
TRAINING_LABEL_TOPICS = bool(TRAINING_CONFIG.get("label_topics", False))

LLM_MODEL = _env("LLM_MODEL", LLM_CONFIG.get("model", "gemini/gemini-2.5-flash"))
LLM_BASE_URL = _env("LLM_BASE_URL", LLM_CONFIG.get("base_url"))
LLM_TEMPERATURE = float(LLM_CONFIG.get("temperature", 0.2))
LLM_MAX_RETRIES = int(LLM_CONFIG.get("max_retries", 3))
LLM_TIMEOUT = float(LLM_CONFIG.get("timeout", 60))
LLM_MAX_HEADLINES = int(LLM_CONFIG.get("max_headlines", 8))


def setup_logging(log_file: Union[str, Path, None] = LOG_FILE, console: bool = False,
                  level: Union[int, str] = logging.INFO) -> None:

    handlers: list[logging.Handler] = []
    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(path, encoding="utf-8"))
    if console or not handlers:
        handlers.append(logging.StreamHandler(sys.stdout))

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    for handler in handlers:
        handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    for handler in handlers:
        root.addHandler(handler)
