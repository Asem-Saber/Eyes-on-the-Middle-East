"""Topic queries.

Topics are model-scoped. `dim_topic.topic_key` is derived from
(model_version, topic_id), so a weekly retrain creates a fresh set of rows and
the same `model_topic_id` can appear under two model versions. Endpoints that
take an id therefore filter on `model_topic_id` and return every match unless a
`model_version` is supplied.
"""

from __future__ import annotations

import psycopg

from src.api.core.database import fetch_all, fetch_one
from src.api.schemas.articles import ArticleSummary, MonthlyVolume
from src.api.schemas.topics import (
    Topic,
    TopicDetail,
    TopicDistribution,
    TopicStats,
    TopicTrendPoint,
)

_TOPIC_COLUMNS = """
t.topic_key, t.model_topic_id as topic_id, t.model_version,
t.topic_label, t.topic_summary, coalesce(t.is_outlier, false) as is_outlier
"""


def list_topics(conn: psycopg.Connection, include_outliers: bool = True) -> list[Topic]:
    rows = fetch_all(
        conn,
        f"""select {_TOPIC_COLUMNS}, count(f.article_key) as article_count
            from dim_topic t
            left join fct_articles f on f.topic_key = t.topic_key
            {'' if include_outliers else 'where not t.is_outlier'}
            group by t.topic_key, t.model_topic_id, t.model_version,
                     t.topic_label, t.topic_summary, t.is_outlier
            order by article_count desc, t.model_topic_id""",
    )
    return [Topic(**row) for row in rows]


def topic_distribution(conn: psycopg.Connection, limit: int = 20) -> list[TopicDistribution]:
    rows = fetch_all(
        conn,
        """select t.model_topic_id as topic_id, t.topic_label, count(*) as count
           from fct_articles f
           join dim_topic t on t.topic_key = f.topic_key
           where not t.is_outlier
           group by 1, 2 order by count desc limit %(limit)s""",
        {"limit": limit},
    )
    return [TopicDistribution(**row) for row in rows]


def topic_trends(conn: psycopg.Connection, topics: int = 5) -> dict[int, list[TopicTrendPoint]]:
    """Weekly counts for the busiest topics, keyed by model_topic_id."""
    rows = fetch_all(
        conn,
        """with top as (
               select f.topic_key from fct_articles f
               join dim_topic t on t.topic_key = f.topic_key
               where not t.is_outlier
               group by f.topic_key order by count(*) desc limit %(topics)s
           )
           select t.model_topic_id as topic_id, d.iso_year, d.iso_week, count(*) as count
           from fct_articles f
           join top on top.topic_key = f.topic_key
           join dim_topic t on t.topic_key = f.topic_key
           join dim_date d on d.date_key = f.published_date_key
           group by 1, 2, 3 order by 1, 2, 3""",
        {"topics": topics},
    )

    trends: dict[int, list[TopicTrendPoint]] = {}
    for row in rows:
        topic_id = int(row.pop("topic_id"))
        trends.setdefault(topic_id, []).append(TopicTrendPoint(**row))
    return trends


def topic_detail(
    conn: psycopg.Connection, topic_id: int, articles: int = 20
) -> TopicDetail | None:
    row = fetch_one(
        conn,
        f"""select {_TOPIC_COLUMNS},
                   count(f.article_key) as article_count,
                   min(d.full_date)::text as first_published,
                   max(d.full_date)::text as last_published
            from dim_topic t
            left join fct_articles f on f.topic_key = t.topic_key
            left join dim_date d on d.date_key = f.published_date_key
            where t.model_topic_id = %(topic_id)s
            group by t.topic_key, t.model_topic_id, t.model_version,
                     t.topic_label, t.topic_summary, t.is_outlier
            order by article_count desc
            limit 1""",
        {"topic_id": topic_id},
    )
    if row is None:
        return None

    # Kept on the row as well as in stats: TopicDetail inherits article_count
    # from Topic, and popping it would silently leave that field at 0.
    stats = TopicStats(
        article_count=int(row["article_count"]),
        first_published=row.pop("first_published"),
        last_published=row.pop("last_published"),
    )
    topic_key = row["topic_key"]

    trend = fetch_all(
        conn,
        """select d.iso_year, d.iso_week, count(*) as count
           from fct_articles f join dim_date d on d.date_key = f.published_date_key
           where f.topic_key = %(topic_key)s group by 1, 2 order by 1, 2""",
        {"topic_key": topic_key},
    )
    volume = fetch_all(
        conn,
        """select to_char(d.full_date, 'YYYY-MM') as month, count(*) as count
           from fct_articles f join dim_date d on d.date_key = f.published_date_key
           where f.topic_key = %(topic_key)s group by 1 order by 1""",
        {"topic_key": topic_key},
    )
    rows = fetch_all(
        conn,
        """select a.article_id, a.headline, a.summary, a.url,
                  d.full_date as published_date, s.source_name,
                  t.model_topic_id as topic_id, t.topic_label, f.word_count
           from fct_articles f
           join dim_article a on a.article_key = f.article_key
           join dim_topic t on t.topic_key = f.topic_key
           left join dim_source s on s.source_key = f.source_key
           left join dim_date d on d.date_key = f.published_date_key
           where f.topic_key = %(topic_key)s
           order by d.full_date desc nulls last, a.article_id
           limit %(limit)s""",
        {"topic_key": topic_key, "limit": articles},
    )

    return TopicDetail(
        **row,
        stats=stats,
        trend=[TopicTrendPoint(**t) for t in trend],
        monthly_volume=[MonthlyVolume(**v) for v in volume],
        articles=[ArticleSummary(**a) for a in rows],
    )
