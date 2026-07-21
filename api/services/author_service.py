from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from api.models.article import Article


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
