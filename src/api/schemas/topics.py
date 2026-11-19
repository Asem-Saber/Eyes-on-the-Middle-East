"""Topic response contracts.

Two differences from v1 worth knowing:

* No `keywords`. `dim_topic` stores the LLM label and summary; the c-TF-IDF
  keywords stay in the BentoML service and are never persisted to the warehouse.
* Topics are scoped by model. `topic_key` is derived from (model_version,
  topic_id), so the same `topic_id` from two training runs is two rows.
"""

from __future__ import annotations

from pydantic import BaseModel

from src.api.schemas.articles import ArticleSummary, MonthlyVolume


class Topic(BaseModel):
    topic_key: int
    topic_id: int
    model_version: str | None = None
    topic_label: str | None = None
    topic_summary: str | None = None
    is_outlier: bool = False
    article_count: int = 0


class TopicDistribution(BaseModel):
    topic_id: int
    topic_label: str | None = None
    count: int


class TopicTrendPoint(BaseModel):
    iso_year: int
    iso_week: int
    count: int


class TopicStats(BaseModel):
    article_count: int
    first_published: str | None = None
    last_published: str | None = None


class TopicDetail(Topic):
    stats: TopicStats
    trend: list[TopicTrendPoint] = []
    monthly_volume: list[MonthlyVolume] = []
    articles: list[ArticleSummary] = []
