from __future__ import annotations

from src.config import (
    API_CORS_ORIGINS,
    API_DEFAULT_PAGE_SIZE,
    API_MAX_PAGE_SIZE,
    API_TITLE,
    API_VERSION,
    MART_SCHEMA,
)

TITLE = API_TITLE
VERSION = API_VERSION
DESCRIPTION = (
    "Read-only API over the Eyes on the Middle East warehouse marts "
    "(fct_articles, dim_article, dim_topic, dim_source, dim_date)."
)

API_V1_PREFIX = "/api/v1"
SCHEMA = MART_SCHEMA

DEFAULT_PAGE_SIZE = API_DEFAULT_PAGE_SIZE
MAX_PAGE_SIZE = API_MAX_PAGE_SIZE

# Empty means no browser origin is allowed, which is the right default for a
# service fronted by something else.
CORS_ORIGINS = API_CORS_ORIGINS
