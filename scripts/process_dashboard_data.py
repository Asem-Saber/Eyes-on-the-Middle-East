import os
import sys
import json
from pathlib import Path
from datetime import datetime

from bertopic import BERTopic
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

ARTICLES_PATH = os.getenv("ARTICLES_PATH", str(ROOT_DIR / "news" / "aljazeera_articles.json"))
MODEL_PATH = os.getenv("MODEL_PATH", str(ROOT_DIR / "Aljazeera_topics_model"))


def load_raw_articles():
    if not os.path.exists(ARTICLES_PATH):
        print(f"No articles found at {ARTICLES_PATH}")
        return []
    with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_processed_ids(db):
    from api.models.article import Article

    rows = db.query(Article.id).all()
    return {r[0] for r in rows}


def parse_date(dt_str: str):
    if dt_str and dt_str not in ("No Date", "Error"):
        try:
            return datetime.strptime(dt_str, "%d/%m/%Y").date()
        except ValueError:
            return None
    return None


def upsert_articles(db, articles_with_topics):
    from api.models.article import Article

    batch_size = 500
    total = 0

    for i in range(0, len(articles_with_topics), batch_size):
        batch = articles_with_topics[i : i + batch_size]
        rows = [
            {
                "id": a["id"],
                "link": a.get("Link"),
                "headline": a.get("Headline"),
                "summary": a.get("Summary"),
                "full_content": a.get("Full_Content", []),
                "publisher": a.get("Publisher"),
                "topics": a.get("Topics", []),
                "sources": a.get("Sources", []),
                "date": parse_date(a.get("Date", "")),
                "topic_id": a.get("topic_id"),
                "topic_label": a.get("topic_label"),
            }
            for a in batch
        ]

        stmt = insert(Article).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "headline": stmt.excluded.headline,
                "summary": stmt.excluded.summary,
                "full_content": stmt.excluded.full_content,
                "publisher": stmt.excluded.publisher,
                "topics": stmt.excluded.topics,
                "sources": stmt.excluded.sources,
                "date": stmt.excluded.date,
                "topic_id": stmt.excluded.topic_id,
                "topic_label": stmt.excluded.topic_label,
            },
        )
        db.execute(stmt)
        db.commit()

        total += len(rows)
        print(f"  Upserted {total} / {len(articles_with_topics)} articles...")

    return total


def save_topic_metadata(db, topic_model):
    from api.models.topic_meta import TopicMeta
    from api.utils.topic_labels import parse_topic_label

    topic_info = topic_model.get_topic_info()
    for _, row in topic_info.iterrows():
        tid = int(row["Topic"])
        if tid == -1:
            continue

        display_name, fallback_keywords = parse_topic_label(row["Name"])
        topic_words = topic_model.get_topic(tid)
        keywords = [word for word, _score in topic_words[:10]] if topic_words else fallback_keywords

        existing = db.query(TopicMeta).filter(TopicMeta.topic_id == tid).first()
        if existing:
            existing.name = display_name
            existing.keywords = keywords
        else:
            db.add(TopicMeta(topic_id=tid, name=display_name, keywords=keywords))

    db.commit()
    print(f"Saved metadata for {len(topic_info) - 1} topics to topic_meta table.")


def main():
    from api.db.session import SessionLocal, engine
    from api.db.base import Base

    Base.metadata.create_all(bind=engine)

    articles = load_raw_articles()
    if not articles:
        return

    db = SessionLocal()
    try:
        processed_ids = get_processed_ids(db)
        new_articles = [a for a in articles if a["id"] not in processed_ids]
        print(f"Found {len(new_articles)} new articles out of {len(articles)} total.")

        if not new_articles:
            print("No new articles to process.")
            return

        try:
            topic_model = BERTopic.load(MODEL_PATH)
        except Exception as e:
            print(f"Failed to load BERTopic model: {e}")
            return

        docs = []
        for a in new_articles:
            headline = a.get("Headline", "")
            summary = a.get("Summary", "")
            text = f"{headline}. {summary}".strip()
            docs.append(text)

        topics, probs = topic_model.transform(docs)

        topic_info = topic_model.get_topic_info()
        topic_mapping = dict(zip(topic_info["Topic"], topic_info["Name"]))

        for i, a in enumerate(new_articles):
            topic_id = int(topics[i])
            a["topic_id"] = topic_id
            a["topic_label"] = topic_mapping.get(topic_id, "Unknown")

        total = upsert_articles(db, new_articles)
        print(f"Articles processed and loaded: {total}")

        save_topic_metadata(db, topic_model)
    finally:
        db.close()


if __name__ == "__main__":
    main()
