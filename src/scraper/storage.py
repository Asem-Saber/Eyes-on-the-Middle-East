import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Union

from src.config import OUTPUT_FILE, DATA_DIR


def load_existing_articles(file_path: Union[Path, str] = OUTPUT_FILE) -> List[Dict[str, Any]]:
    """Loads previously saved articles from disk."""
    path = Path(file_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_articles(articles: List[Dict[str, Any]], file_path: Union[Path, str] = OUTPUT_FILE) -> None:
    """Atomically serializes article records to formatted JSON."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_file = path.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
    os.replace(temp_file, path)
    logging.info(f"Saved {len(articles)} articles to {path}")