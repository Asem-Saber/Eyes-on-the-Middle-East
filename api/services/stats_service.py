from sqlalchemy.orm import Session
from sqlalchemy import func
from api.models.article import Article


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
