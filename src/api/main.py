"""FastAPI application over the warehouse marts.

    uv run uvicorn src.api.main:app --reload --port 8000

Read-only by design: every query targets dbt-built tables, and the warehouse is
written by the staging loader and dbt, never by this service.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.core.config import (
    API_V1_PREFIX,
    CORS_ORIGINS,
    DESCRIPTION,
    SCHEMA,
    TITLE,
    VERSION,
)
from src.api.core.database import connect, fetch_one
from src.api.routers.v1.api import api_router
from src.config import setup_logging

logger = logging.getLogger(__name__)
setup_logging(console=True)

app = FastAPI(title=TITLE, description=DESCRIPTION, version=VERSION)

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=API_V1_PREFIX)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"service": TITLE, "version": VERSION, "docs": "/docs"}


@app.get("/health", tags=["meta"], response_model=None)
def health() -> JSONResponse | dict[str, object]:
    """Reports the warehouse connection and whether the marts are populated.

    A reachable but empty database is reported as degraded rather than healthy:
    dbt rebuilds the marts in full, so an empty `fct_articles` means a failed or
    in-flight build, not a working service.
    """
    try:
        with connect() as conn:
            row = fetch_one(conn, "select count(*) as articles from fct_articles")
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "warehouse": "unreachable", "schema": SCHEMA},
        )

    articles = int((row or {}).get("articles", 0))
    if not articles:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "warehouse": "connected", "articles": 0},
        )
    return {"status": "healthy", "warehouse": "connected", "articles": articles}
