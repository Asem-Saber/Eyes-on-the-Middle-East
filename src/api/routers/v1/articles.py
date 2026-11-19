from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.core.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from src.api.core.database import get_connection
from src.api.schemas.articles import (
    ArticleDetail,
    ArticleSummary,
    MonthlyVolume,
    PaginatedArticles,
)
from src.api.services import article_service

router = APIRouter()


@router.get("/", response_model=PaginatedArticles)
def read_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    topic: int | None = Query(None, description="Filter by dim_topic.model_topic_id"),
    search: str | None = Query(None, description="Case-insensitive match on headline or summary"),
    date_from: str | None = Query(None, description="YYYY-MM-DD, inclusive"),
    date_to: str | None = Query(None, description="YYYY-MM-DD, inclusive"),
    conn: psycopg.Connection = Depends(get_connection),
) -> PaginatedArticles:
    """Paginated articles, newest first, with optional topic/search/date filters."""
    return article_service.list_articles(
        conn, page=page, limit=limit, topic_id=topic,
        search=search, date_from=date_from, date_to=date_to,
    )


@router.get("/recent", response_model=list[ArticleSummary])
def read_recent(
    limit: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    conn: psycopg.Connection = Depends(get_connection),
) -> list[ArticleSummary]:
    """The most recently published articles."""
    return article_service.recent_articles(conn, limit=limit)


@router.get("/monthly-volume", response_model=list[MonthlyVolume])
def read_monthly_volume(
    conn: psycopg.Connection = Depends(get_connection),
) -> list[MonthlyVolume]:
    """Article counts per calendar month across the whole corpus."""
    return article_service.monthly_volume(conn)


@router.get("/{article_id}", response_model=ArticleDetail)
def read_article(
    article_id: str, conn: psycopg.Connection = Depends(get_connection)
) -> ArticleDetail:
    """One article with its full paragraph list and topic metadata."""
    article = article_service.article_detail(conn, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
