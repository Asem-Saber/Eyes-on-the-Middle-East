"""Load monthly news-after-llm JSON into staging, preserving latest article state."""
import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from src.config import get_setting
from src.datalake.init_storage import create_client
from src.datalake.partitions import decode_records
from .connection import settings

OBJECT = re.compile(r"aljazeera/(year=\d{4}/month=(?:0[1-9]|1[0-2])|undated)/enriched_articles\.json$")
UPSERT = """INSERT INTO staging.enriched_articles
(article_id,link,headline,summary,full_content,published_date_raw,topic_id,topic_label,
topic_summary,model_version,source_object_key,load_batch_id,payload_hash)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT(article_id) DO UPDATE SET
link=excluded.link,headline=excluded.headline,summary=excluded.summary,
full_content=excluded.full_content,published_date_raw=excluded.published_date_raw,
topic_id=excluded.topic_id,topic_label=excluded.topic_label,topic_summary=excluded.topic_summary,
model_version=excluded.model_version,source_object_key=excluded.source_object_key,
load_batch_id=excluded.load_batch_id,payload_hash=excluded.payload_hash,updated_at=now()
WHERE staging.enriched_articles.payload_hash <> excluded.payload_hash
   OR staging.enriched_articles.source_object_key <> excluded.source_object_key"""


def prepare(record, model_version=None):
    if not isinstance(record, dict):
        raise ValueError("Article must be an object")
    for key in ("id", "Link", "Headline", "Date"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f"Missing/invalid {key}")
    datetime.strptime(record["Date"], "%d/%m/%Y")
    paragraphs = record.get("Full_Content")
    if not isinstance(paragraphs, list) or not all(isinstance(p, str) for p in paragraphs):
        raise ValueError("Full_Content must be an array of strings")
    if type(record.get("topic_id")) is not int:
        raise ValueError("topic_id must be an integer")
    version = record.get("model_version") or model_version
    if not isinstance(version, str) or not version.strip():
        raise ValueError("Missing model_version: supply --model-version for legacy files")
    for key in ("topic_label", "topic_summary"):
        if record.get(key) is not None and not isinstance(record[key], str):
            raise ValueError(f"Invalid {key}")
    if not isinstance(record.get("Summary", ""), str):
        raise ValueError("Invalid Summary")
    return {"article_id": record["id"], "link": record["Link"], "headline": record["Headline"],
            "summary": record.get("Summary", ""), "full_content": paragraphs,
            "published_date_raw": record["Date"], "topic_id": record["topic_id"],
            "topic_label": record.get("topic_label"), "topic_summary": record.get("topic_summary"),
            "model_version": version.strip()}


def load_records(connection, records, key, model_version=None):
    from psycopg.types.json import Jsonb
    prepared = [prepare(record, model_version) for record in records]
    ids = [r["article_id"] for r in prepared]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate article IDs in {key}")
    batch_id = uuid4()
    with connection.transaction():
        with connection.cursor() as cursor:
            for row in prepared:
                digest = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                cursor.execute(UPSERT, (*[Jsonb(value) if name == "full_content" else value
                                         for name, value in row.items()], key, batch_id, digest))
    return len(prepared)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Local enriched JSON file or after_llm directory")
    parser.add_argument("--model-version", help="Explicit version for legacy records missing model_version")
    args = parser.parse_args()
    import psycopg
    with psycopg.connect(**settings()) as connection:
        with connection.transaction():
            connection.execute(Path(__file__).with_name("ddl.sql").read_text())
        count = 0
        if args.input:
            paths = sorted(args.input.rglob("enriched_articles.json")) if args.input.is_dir() else [args.input]
            if not paths:
                raise ValueError("No enriched input files found")
            for path in paths:
                count += load_records(connection, decode_records(path.read_text(encoding="utf-8-sig")),
                                      path.as_posix(), args.model_version)
        else:
            client = create_client()
            bucket = get_setting("SEAWEEDFS_AFTER_LLM_BUCKET", "news-after-llm")
            keys = sorted(item["Key"] for page in client.get_paginator("list_objects_v2").paginate(
                Bucket=bucket, Prefix="aljazeera/") for item in page.get("Contents", []) if OBJECT.fullmatch(item["Key"]))
            if not keys:
                raise ValueError("No enriched monthly files found")
            for key in keys:
                response = client.get_object(Bucket=bucket, Key=key)
                with response["Body"] as body:
                    records = decode_records(body.read().decode("utf-8-sig"))
                count += load_records(connection, records, key, args.model_version)
        print(f"Loaded/checked {count} articles in staging.enriched_articles")


if __name__ == "__main__":
    main()
