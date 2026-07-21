from api.models.article import Article


def article_to_dict(r: Article) -> dict:
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
