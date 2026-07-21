from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from api.models.article import Article
from api.models.topic_meta import TopicMeta
from api.utils.topic_labels import parse_topic_label


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

        meta = db.query(TopicMeta).filter(TopicMeta.topic_id == topic_id).first()
        if meta:
            name = meta.name
            keywords = meta.keywords or []
        else:
            name, keywords = parse_topic_label(raw_label)

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
    from api.services.article_service import _article_to_dict

    topic_meta = db.query(TopicMeta).filter(TopicMeta.topic_id == topic_id).first()
    has_articles = (
        db.query(Article.id)
        .filter(Article.topic_id == topic_id)
        .first()
    )
    if not topic_meta and not has_articles:
        return None

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
        name, keywords = parse_topic_label(raw_label)

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
