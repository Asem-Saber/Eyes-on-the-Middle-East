"""Article queries over the star schema.

Every read starts at `fct_articles` and joins outward. The dimension joins are
LEFT joins on purpose: dbt verifies the relationships with tests rather than
foreign keys, so a mart rebuilt mid-request should degrade to nulls instead of
dropping the row entirely.
"""

from __future__ import annotations

import math
from typing import Any

import psycopg

from src.api.core.database import fetch_all, fetch_one
from src.api.schemas.articles import (
    ArticleDetail,
    ArticleSummary,
    MonthlyVolume,
    PaginatedArticles,
)

_BASE = """
from fct_articles f
join dim_article a on a.article_key = f.article_key
left join dim_topic t on t.topic_key = f.topic_key
left join dim_source s on s.source_key = f.source_key
left join dim_date d on d.date_key = f.published_date_key
"""

_SUMMARY_COLUMNS = """
a.article_id, a.headline, a.summary, a.url,
d.full_date as published_date, s.source_name,
t.model_topic_id as topic_id, t.topic_label, f.word_count
"""


def _filters(
    topic_id: int | None, search: str | None, date_from: str | None, date_to: str | None
) -> tuple[str, dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if topic_id is not None:
        clauses.append("t.model_topic_id = %(topic_id)s")
        params["topic_id"] = topic_id
    if search:
        clauses.append("(a.headline ilike %(search)s or a.summary ilike %(search)s)")
        params["search"] = f"%{search}%"
    if date_from:
        clauses.append("d.full_date >= %(date_from)s")
        params["date_from"] = date_from
    if date_to:
        clauses.append("d.full_date <= %(date_to)s")
        params["date_to"] = date_to

    return (" where " + " and ".join(clauses) if clauses else ""), params


def list_articles(
    conn: psycopg.Connection,
    page: int = 1,
    limit: int = 8,
    topic_id: int | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> PaginatedArticles:
    where, params = _filters(topic_id, search, date_from, date_to)

    total_row = fetch_one(conn, f"select count(*) as total {_BASE} {where}", params)
    total = int(total_row["total"]) if total_row else 0

    rows = fetch_all(
        conn,
        f"""select {_SUMMARY_COLUMNS} {_BASE} {where}
            order by d.full_date desc nulls last, a.article_id
            limit %(limit)s offset %(offset)s""",
        {**params, "limit": limit, "offset": (page - 1) * limit},
    )

    return PaginatedArticles(
        articles=[ArticleSummary(**row) for row in rows],
        total=total,
        page=page,
        pages=math.ceil(total / limit) if limit else 0,
    )


def recent_articles(conn: psycopg.Connection, limit: int = 10) -> list[ArticleSummary]:
    rows = fetch_all(
        conn,
        f"""select {_SUMMARY_COLUMNS} {_BASE}
            order by d.full_date desc nulls last, a.article_id
            limit %(limit)s""",
        {"limit": limit},
    )
    return [ArticleSummary(**row) for row in rows]


def article_detail(conn: psycopg.Connection, article_id: str) -> ArticleDetail | None:
    row = fetch_one(
        conn,
        f"""select {_SUMMARY_COLUMNS},
                   a.full_content, f.paragraph_count,
                   t.topic_summary, t.model_version, coalesce(t.is_outlier, false) as is_outlier
            {_BASE}
            where a.article_id = %(article_id)s""",
        {"article_id": article_id},
    )
    if row is None:
        return None

    # full_content is jsonb in dim_article; psycopg returns it already decoded.
    row["full_content"] = list(row.get("full_content") or [])
    return ArticleDetail(**row)


def monthly_volume(conn: psycopg.Connection) -> list[MonthlyVolume]:
    rows = fetch_all(
        conn,
        f"""select to_char(d.full_date, 'YYYY-MM') as month, count(*) as count
            {_BASE}
            where d.full_date is not null
            group by 1 order by 1""",
    )
    return [MonthlyVolume(**row) for row in rows]
