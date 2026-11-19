"""Article response contracts.

Shapes follow the marts, not v1's `articles` table. `publisher`, `topics` and
`sources` are gone because the v2 processing step omits them; `source_name`
from `dim_source` is the nearest equivalent that still has data behind it.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ArticleSummary(BaseModel):
    article_id: str
    headline: str
    summary: str | None = None
    url: str
    published_date: date | None = None
    source_name: str | None = None
    topic_id: int | None = None
    topic_label: str | None = None
    word_count: int = 0


class ArticleDetail(ArticleSummary):
    full_content: list[str] = []
    paragraph_count: int = 0
    topic_summary: str | None = None
    model_version: str | None = None
    is_outlier: bool = False


class PaginatedArticles(BaseModel):
    articles: list[ArticleSummary]
    total: int
    page: int
    pages: int


class MonthlyVolume(BaseModel):
    month: str
    count: int
