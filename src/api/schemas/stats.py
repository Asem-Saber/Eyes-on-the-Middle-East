"""Dashboard headline figures."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class Stats(BaseModel):
    articles_total: int = 0
    topics_total: int = 0
    sources_total: int = 0
    outlier_articles: int = 0
    coverage_start: date | None = None
    coverage_end: date | None = None
    # When the staging loader last wrote, not when the scraper last ran.
    last_loaded_at: datetime | None = None
