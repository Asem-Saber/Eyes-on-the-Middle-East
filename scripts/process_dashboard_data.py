import os
import sys
import json
from pathlib import Path
from bertopic import BERTopic
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

ARTICLES_PATH = os.getenv("ARTICLES_PATH", str(ROOT_DIR / "news" / "aljazeera_articles.json"))
PROCESSED_PATH = os.getenv("PROCESSED_PATH", str(ROOT_DIR / "news" / "processed_articles.json"))
MODEL_PATH = os.getenv("MODEL_PATH", str(ROOT_DIR / "Aljazeera_topics_model"))


def load_data():
    if not os.path.exists(ARTICLES_PATH):
        print(f"No articles found at {ARTICLES_PATH}")
        return []
    with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_processed_data():
    if not os.path.exists(PROCESSED_PATH):
        return {}
    with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return {item["id"]: item for item in data}


def save_processed_data(processed_dict):
    with open(PROCESSED_PATH, "w", encoding="utf-8") as f:
        json.dump(list(processed_dict.values()), f, ensure_ascii=False, indent=2)


def save_topic_metadata(topic_model):
    """Extract topic keywords from BERTopic and upsert into topic_meta table.

    This runs after inference so the API can serve pre-computed keywords.
    Ready for Airflow integration — just call this function in the DAG.
    """
    from api.db.session import SessionLocal, engine
    from api.db.base import Base
    from api.models.topic_meta import TopicMeta

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        topic_info = topic_model.get_topic_info()
        for _, row in topic_info.iterrows():
            tid = int(row["Topic"])
            if tid == -1:
                continue 
            raw_name = row["Name"]
            parts = raw_name.split("_")
            if parts and parts[0].lstrip("-").isdigit():
                parts = parts[1:]
            display_name = " ".join(w.capitalize() for w in parts)
            topic_words = topic_model.get_topic(tid)
            if topic_words:
                keywords = [word for word, _score in topic_words[:10]]
            else:
                keywords = parts[:10]

            existing = db.query(TopicMeta).filter(TopicMeta.topic_id == tid).first()
            if existing:
                existing.name = display_name
                existing.keywords = keywords
            else:
                db.add(TopicMeta(topic_id=tid, name=display_name, keywords=keywords))

        db.commit()
        print(f"Saved metadata for {len(topic_info) - 1} topics to topic_meta table.")
    finally:
        db.close()


def main():
    articles = load_data()
    processed = load_processed_data()

    new_articles = [a for a in articles if a["id"] not in processed]
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
        processed[a["id"]] = a

    save_processed_data(processed)
    print("Articles processed successfully")

    save_topic_metadata(topic_model)


if __name__ == "__main__":
    main()
