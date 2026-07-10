import json
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert
from api.db.session import SessionLocal, engine
from api.db.base import Base
from api.models.article import Article
from api.models.topic_meta import TopicMeta  # ensures topic_meta table is created

load_dotenv()
PROCESSED_PATH = os.getenv("PROCESSED_PATH", "news/processed_articles.json")


def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


def _parse_date(dt_str: str):
    if dt_str and dt_str not in ("No Date", "Error"):
        try:
            return datetime.strptime(dt_str, "%d/%m/%Y").date()
        except ValueError:
            return None
    return None


def load_data_to_db():
    if not os.path.exists(PROCESSED_PATH):
        print(f"File not found: {PROCESSED_PATH}")
        return

    print("Loading JSON data...")
    with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Found {len(data)} articles. Upserting in batches...")

    batch_size = 1000
    total_upserted = 0

    with SessionLocal() as db:
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            rows = [
                {
                    "id": item.get("id"),
                    "link": item.get("Link"),
                    "headline": item.get("Headline"),
                    "summary": item.get("Summary"),
                    "full_content": item.get("Full_Content", []),
                    "publisher": item.get("Publisher"),
                    "topics": item.get("Topics", []),
                    "sources": item.get("Sources", []),
                    "date": _parse_date(item.get("Date", "")),
                    "topic_id": item.get("topic_id"),
                    "topic_label": item.get("topic_label"),
                }
                for item in batch
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

            total_upserted += len(rows)
            print(f"  Upserted {total_upserted} / {len(data)} records...")

    print(f"Done! {total_upserted} articles loaded.")


if __name__ == "__main__":
    init_db()
    load_data_to_db()
