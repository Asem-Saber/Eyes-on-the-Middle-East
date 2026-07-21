import math
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from api.models.article import Article


def get_recent_articles(db: Session, limit: int = 10):
    results = (
        db.query(Article)
        .filter(Article.headline.isnot(None), Article.headline != "No Headline", Article.date.isnot(None))
        .order_by(desc(Article.date))
        .limit(limit)
        .all()
    )
    return [_article_to_dict(r) for r in results]


def get_articles_paginated(
    db: Session,
    page: int = 1,
    limit: int = 8,
    topic_id: int | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    query = db.query(Article).filter(
        Article.headline.isnot(None), Article.headline != "No Headline", Article.date.isnot(None)
    )

    if topic_id is not None:
        query = query.filter(Article.topic_id == topic_id)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Article.headline.ilike(pattern),
                Article.publisher.ilike(pattern),
                Article.summary.ilike(pattern),
            )
        )

    if date_from:
        try:
            df = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(Article.date >= df)
        except ValueError:
            pass

    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(Article.date <= dt)
        except ValueError:
            pass

    total = query.count()
    pages = math.ceil(total / limit) if limit else 1
    offset = (page - 1) * limit

    results = query.order_by(desc(Article.date)).offset(offset).limit(limit).all()

    return {
        "articles": [_article_to_dict(r) for r in results],
        "total": total,
        "page": page,
        "pages": pages,
    }


def get_article_by_id(db: Session, article_id: str):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        return None

    d = _article_to_dict(article)
    d["full_content"] = article.full_content or []
    d["topics"] = article.topics or []
    d["sources"] = article.sources or []
    return d


def get_monthly_volume(db: Session):
    results = (
        db.query(
            func.to_char(Article.date, "YYYY-MM").label("month"),
            func.count(Article.id).label("count"),
        )
        .filter(Article.date.isnot(None))
        .group_by("month")
        .order_by("month")
        .all()
    )
    return [{"month": r[0], "count": r[1]} for r in results]


def _article_to_dict(r: Article) -> dict:
    return {
        "id": r.id,
        "headline": r.headline,
        "summary": r.summary or "",
        "topic_label": r.topic_label or "Uncategorized",
        "topic_id": r.topic_id,
        "author": r.publisher or "Unknown",
        "date": r.date.strftime("%Y-%m-%d") if r.date else "No Date",
        "link": r.link or "#",
    }
