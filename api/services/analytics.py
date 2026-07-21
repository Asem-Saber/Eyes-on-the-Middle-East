"""Backwards-compatible re-exports.

All logic has moved to dedicated service modules. Import from those directly.
"""

from api.services.stats_service import get_dashboard_stats
from api.services.topic_service import (
    get_topic_distribution,
    get_topic_trends,
    get_topics_list,
    get_topic_detail,
)
from api.services.author_service import get_top_authors
from api.services.article_service import (
    get_recent_articles,
    get_articles_paginated,
    get_article_by_id,
    get_monthly_volume,
)

__all__ = [
    "get_dashboard_stats",
    "get_topic_distribution",
    "get_topic_trends",
    "get_topics_list",
    "get_topic_detail",
    "get_top_authors",
    "get_recent_articles",
    "get_articles_paginated",
    "get_article_by_id",
    "get_monthly_volume",
]
