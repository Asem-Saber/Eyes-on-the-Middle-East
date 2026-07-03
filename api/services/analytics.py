from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, String, or_
from api.models.article import Article
from api.models.topic_meta import TopicMeta
from datetime import datetime, date
from collections import defaultdict
import math


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def get_dashboard_stats(db: Session):
    articles_scraped = db.query(func.count(Article.id)).scalar()
    topics_discovered = (
        db.query(func.count(func.distinct(Article.topic_id)))
        .filter(Article.topic_id != -1)
        .scalar()
    )

    min_date = db.query(func.min(Article.date)).scalar()
    max_date = db.query(func.max(Article.date)).scalar()

    if min_date and max_date:
        coverage_period = f"{min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"
        last_scraped = max_date.strftime("%m/%d/%Y")
    else:
        coverage_period = "N/A"
        last_scraped = "N/A"

    return {
        "articles_scraped": articles_scraped or 0,
        "topics_discovered": topics_discovered or 0,
        "coverage_period": coverage_period,
        "last_scraped": last_scraped,
    }


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

def get_topic_distribution(db: Session):
    results = (
        db.query(Article.topic_label, func.count(Article.id).label("count"))
        .filter(Article.topic_label != "Unknown", Article.topic_label.isnot(None))
        .group_by(Article.topic_label)
        .order_by(desc("count"))
        .all()
    )
    return [{"topic": r[0], "count": r[1]} for r in results]


def get_topics_list(db: Session):
    """Return all topics with id, display name, keywords, and article count."""
    results = (
        db.query(
            Article.topic_id,
            Article.topic_label,
            func.count(Article.id).label("count"),
        )
        .filter(
            Article.topic_id != -1,
            Article.topic_id.isnot(None),
            Article.topic_label.isnot(None),
            Article.topic_label != "Unknown",
        )
        .group_by(Article.topic_id, Article.topic_label)
        .order_by(desc("count"))
        .all()
    )

    topics = []
    for r in results:
        topic_id = r[0]
        raw_label = r[1] or ""
        count = r[2]

        # Try to get keywords from topic_meta table first
        meta = db.query(TopicMeta).filter(TopicMeta.topic_id == topic_id).first()
        if meta:
            name = meta.name
            keywords = meta.keywords or []
        else:
            # Fallback: parse from topic_label  e.g. "0_ceasefire_Hamas_negotiations"
            parts = raw_label.split("_")
            # Drop leading numeric id if present
            if parts and parts[0].lstrip("-").isdigit():
                parts = parts[1:]
            name = " ".join(w.capitalize() for w in parts) if parts else raw_label
            keywords = parts[:10]

        topics.append(
            {
                "topic_id": topic_id,
                "name": name,
                "keywords": keywords,
                "count": count,
            }
        )

    return topics


def get_topic_detail(db: Session, topic_id: int):
    """Detailed stats for a single topic."""
    topic_meta = db.query(TopicMeta).filter(TopicMeta.topic_id == topic_id).first()
    has_articles = (
        db.query(Article.id)
        .filter(Article.topic_id == topic_id)
        .first()
    )
    if not topic_meta and not has_articles:
        return None

    # Basic stats
    article_count = (
        db.query(func.count(Article.id))
        .filter(Article.topic_id == topic_id)
        .scalar()
        or 0
    )
    contributors_count = (
        db.query(func.count(func.distinct(Article.publisher)))
        .filter(
            Article.topic_id == topic_id,
            Article.publisher.isnot(None),
            Article.publisher.notin_(["Unknown", "Error"]),
        )
        .scalar()
        or 0
    )
    min_date = (
        db.query(func.min(Article.date))
        .filter(Article.topic_id == topic_id)
        .scalar()
    )
    max_date = (
        db.query(func.max(Article.date))
        .filter(Article.topic_id == topic_id)
        .scalar()
    )
    if min_date and max_date:
        date_range = f"{min_date.strftime('%b %d')} - {max_date.strftime('%b %d, %Y')}"
    else:
        date_range = "N/A"

    # Top contributors for this topic
    contributors = (
        db.query(Article.publisher, func.count(Article.id).label("count"))
        .filter(
            Article.topic_id == topic_id,
            Article.publisher.isnot(None),
            Article.publisher.notin_(["Unknown", "Al Jazeera Staff", "Error"]),
        )
        .group_by(Article.publisher)
        .order_by(desc("count"))
        .limit(8)
        .all()
    )

    # Weekly trend for this topic
    trend_results = (
        db.query(
            func.to_char(Article.date, 'IYYY-"W"IW').label("week_key"),
            func.count(Article.id),
        )
        .filter(Article.topic_id == topic_id, Article.date.isnot(None))
        .group_by("week_key")
        .order_by("week_key")
        .all()
    )

    # Monthly volume for this topic
    monthly_results = (
        db.query(
            func.to_char(Article.date, "YYYY-MM").label("month"),
            func.count(Article.id).label("count"),
        )
        .filter(Article.topic_id == topic_id, Article.date.isnot(None))
        .group_by("month")
        .order_by("month")
        .all()
    )

    topic_articles = (
        db.query(Article)
        .filter(
            Article.topic_id == topic_id,
            Article.headline.isnot(None),
            Article.headline != "No Headline",
        )
        .order_by(desc(Article.date))
        .limit(20)
        .all()
    )

    # Topic metadata (name + keywords)
    label_row = (
        db.query(Article.topic_label)
        .filter(Article.topic_id == topic_id)
        .first()
    )
    raw_label = label_row[0] if label_row else ""

    if topic_meta:
        name = topic_meta.name
        keywords = topic_meta.keywords or []
    else:
        parts = raw_label.split("_")
        if parts and parts[0].lstrip("-").isdigit():
            parts = parts[1:]
        name = " ".join(w.capitalize() for w in parts) if parts else raw_label
        keywords = parts[:10]

    return {
        "topic_id": topic_id,
        "name": name,
        "keywords": keywords,
        "stats": {
            "article_count": article_count,
            "contributors_count": contributors_count,
            "date_range": date_range,
        },
        "contributors": [{"author": c[0], "count": c[1]} for c in contributors],
        "trend": [{"week": t[0], "count": t[1]} for t in trend_results],
        "monthly_volume": [{"month": m[0], "count": m[1]} for m in monthly_results],
        "articles": [_article_to_dict(article) for article in topic_articles],
    }


def get_topic_trends(db: Session):
    # 1. Get Top 5 topics
    top_5_results = (
        db.query(Article.topic_label)
        .filter(Article.topic_label != "Unknown", Article.topic_label.isnot(None))
        .group_by(Article.topic_label)
        .order_by(desc(func.count(Article.id)))
        .limit(5)
        .all()
    )
    top_5 = [r[0] for r in top_5_results]

    if not top_5:
        return []

    # 2. Get trends for top 5
    results = (
        db.query(
            func.to_char(Article.date, 'IYYY-"W"IW').label("week_key"),
            Article.topic_label,
            func.count(Article.id),
        )
        .filter(Article.topic_label.in_(top_5), Article.date.isnot(None))
        .group_by("week_key", Article.topic_label)
        .all()
    )

    weekly = defaultdict(lambda: {t: 0 for t in top_5})
    for row in results:
        week_key = row[0]
        topic = row[1]
        count = row[2]
        if week_key:
            weekly[week_key][topic] = count

    trends = []
    for week in sorted(weekly.keys()):
        entry = {"week": week}
        entry.update(weekly[week])
        trends.append(entry)

    return trends


# ---------------------------------------------------------------------------
# Authors
# ---------------------------------------------------------------------------

def get_top_authors(db: Session, limit: int = 8):
    results = (
        db.query(Article.publisher, func.count(Article.id).label("count"))
        .filter(
            Article.publisher.isnot(None),
            Article.publisher.notin_(["Unknown", "Al Jazeera Staff", "Error"]),
        )
        .group_by(Article.publisher)
        .order_by(desc("count"))
        .limit(limit)
        .all()
    )
    return [{"author": r[0], "count": r[1]} for r in results]


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Monthly volume (global)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
