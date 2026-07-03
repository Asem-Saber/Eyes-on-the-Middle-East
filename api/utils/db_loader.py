import json
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session
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

def load_data_to_db():
    if not os.path.exists(PROCESSED_PATH):
        print(f"File not found: {PROCESSED_PATH}")
        return

    db: Session = SessionLocal()
    
    print("Loading JSON data...")
    with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Found {len(data)} articles. Inserting in batches...")
    
    batch_size = 5000
    batch = []
    
    # Optional: Clear existing for fresh start
    # db.query(Article).delete()
    # db.commit()

    for idx, item in enumerate(data):
        # Parse date
        dt_str = item.get("Date", "")
        dt_obj = None
        if dt_str and dt_str != "No Date":
            try:
                dt_obj = datetime.strptime(dt_str, "%d/%m/%Y").date()
            except ValueError:
                pass

        article = Article(
            id=item.get("id"),
            link=item.get("Link"),
            headline=item.get("Headline"),
            summary=item.get("Summary"),
            full_content=item.get("Full_Content", []),
            publisher=item.get("Publisher"),
            topics=item.get("Topics", []),
            sources=item.get("Sources", []),
            date=dt_obj,
            topic_id=item.get("topic_id"),
            topic_label=item.get("topic_label")
        )
        batch.append(article)
        
        if len(batch) >= batch_size:
            # Note: For production use bulk_save_objects or merge if dealing with duplicates
            # For this simple load, we use merge to avoid primary key conflicts
            for b in batch:
                db.merge(b)
            db.commit()
            print(f"Inserted {idx + 1} records...")
            batch = []

    if batch:
        for b in batch:
            db.merge(b)
        db.commit()
        print(f"Inserted {len(data)} records... Done!")
        
    db.close()

if __name__ == "__main__":
    init_db()
    load_data_to_db()
