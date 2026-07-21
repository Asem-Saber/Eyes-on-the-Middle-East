from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from api.schemas.articles import (
    ArticleResponse,
    ArticleDetailResponse,
    PaginatedArticleResponse,
    MonthlyVolumeResponse,
)
from api.services.article_service import (
    get_recent_articles,
    get_articles_paginated,
    get_article_by_id,
    get_monthly_volume,
)
from api.db.session import get_db

router = APIRouter()


@router.get("/", response_model=PaginatedArticleResponse)
def read_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(8, ge=1, le=100),
    topic: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get paginated articles with optional filtering by topic, search term, and date range."""
    return get_articles_paginated(
        db,
        page=page,
        limit=limit,
        topic_id=topic,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/recent", response_model=List[ArticleResponse])
def read_recent_articles(
    limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)
):
    """Get a list of the most recent articles."""
    return get_recent_articles(db, limit=limit)


@router.get("/monthly-volume", response_model=List[MonthlyVolumeResponse])
def read_monthly_volume(db: Session = Depends(get_db)):
    """Get article counts aggregated by month."""
    return get_monthly_volume(db)


@router.get("/{article_id}", response_model=ArticleDetailResponse)
def read_article_detail(article_id: str, db: Session = Depends(get_db)):
    """Get full article detail including content."""
    result = get_article_by_id(db, article_id)
    if not result:
        raise HTTPException(status_code=404, detail="Article not found")
    return result
