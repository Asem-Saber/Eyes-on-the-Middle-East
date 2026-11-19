"""Headline dashboard figures, read in one pass over the fact table."""

from __future__ import annotations

import psycopg

from src.api.core.database import fetch_one
from src.api.schemas.stats import Stats


def dashboard_stats(conn: psycopg.Connection) -> Stats:
    row = fetch_one(
        conn,
        """select
               count(*) as articles_total,
               count(distinct f.topic_key) filter (where not t.is_outlier) as topics_total,
               count(distinct f.source_key) as sources_total,
               count(*) filter (where t.is_outlier) as outlier_articles,
               min(d.full_date) as coverage_start,
               max(d.full_date) as coverage_end,
               max(f.updated_at) as last_loaded_at
           from fct_articles f
           left join dim_topic t on t.topic_key = f.topic_key
           left join dim_date d on d.date_key = f.published_date_key""",
    )
    # An empty mart returns a single row of nulls rather than no row at all.
    return Stats(**{k: v for k, v in (row or {}).items() if v is not None})
