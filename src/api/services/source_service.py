"""Source queries — what replaced v1's author ranking.

With a single publisher scraped today this returns one row. It is kept because
the dimension exists and the shape is right for when more feeds are added.
"""

from __future__ import annotations

import psycopg

from src.api.core.database import fetch_all
from src.api.schemas.sources import Source


def list_sources(conn: psycopg.Connection, limit: int = 20) -> list[Source]:
    rows = fetch_all(
        conn,
        """select s.source_key, s.source_name, s.domain, count(f.article_key) as article_count
           from dim_source s
           left join fct_articles f on f.source_key = s.source_key
           group by s.source_key, s.source_name, s.domain
           order by article_count desc, s.source_name
           limit %(limit)s""",
        {"limit": limit},
    )
    return [Source(**row) for row in rows]
