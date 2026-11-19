"""Read-only access to the dbt marts.

psycopg directly rather than an ORM: the marts are tables dbt owns and fully
rebuilds on every run, so declaring SQLAlchemy models for them would duplicate a
schema that already lives in `src/modeling/models/` and silently drift from it.

Connection settings come from `src.modeling.connection`, the same warehouse
config the staging loader and the dbt wrapper use.
"""

from __future__ import annotations

import re
from typing import Any, Iterator, Sequence

import psycopg
from psycopg.rows import dict_row

from src.config import MART_SCHEMA
from src.modeling.connection import settings

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _search_path() -> str:
    """Put the mart schema first so queries can name tables bare.

    Validated because it is interpolated into a connection option rather than
    passed as a bound parameter.
    """
    if not _IDENTIFIER.match(MART_SCHEMA):
        raise ValueError(f"Invalid mart schema name: {MART_SCHEMA!r}")
    return f"-c search_path={MART_SCHEMA},public"


def connect() -> psycopg.Connection:
    """One connection, rows as dicts, autocommit so nothing idles in a transaction."""
    return psycopg.connect(
        **settings(), row_factory=dict_row, autocommit=True, options=_search_path()
    )


def get_connection() -> Iterator[psycopg.Connection]:
    """FastAPI dependency yielding a short-lived read-only connection."""
    with connect() as conn:
        yield conn


def fetch_all(
    conn: psycopg.Connection, query: str, params: Sequence[Any] | dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fetch_one(
    conn: psycopg.Connection, query: str, params: Sequence[Any] | dict[str, Any] | None = None
) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()
