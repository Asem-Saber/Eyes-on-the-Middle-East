import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Union

from src.config import OUTPUT_FILE, DATA_DIR


def load_existing_articles(file_path: Union[Path, str] = OUTPUT_FILE) -> List[Dict[str, Any]]:
    from src.datalake.partitions import load_local, decode_records
    path = Path(file_path)
    if path == Path(OUTPUT_FILE):
        root = path.parent / "raw" / "aljazeera"
        if any(root.glob("year=*/month=*/articles.json")) or (root / "undated/articles.json").exists():
            return load_local(root)
        return decode_records(path.read_text(encoding="utf-8")) if path.exists() else []
    return decode_records(path.read_text(encoding="utf-8")) if path.exists() else []


def save_articles(articles: List[Dict[str, Any]], file_path: Union[Path, str] = OUTPUT_FILE) -> None:
    from src.datalake.partitions import load_local, group_articles, merge_articles, write_json
    path = Path(file_path)
    if path != Path(OUTPUT_FILE):
        write_json(path, articles)
        return
    root = path.parent / "raw" / "aljazeera"
    groups = group_articles(merge_articles(load_existing_articles(file_path=path), articles))
    # Empty old partitions if an article's corrected date moved it elsewhere.
    for previous in root.glob("year=*/month=*/articles.json"):
        groups.setdefault(previous.parent.relative_to(root).as_posix(), [])
    if (root / "undated/articles.json").exists():
        groups.setdefault("undated", [])
    for partition, records in groups.items():
        write_json(root / partition / "articles.json", records)
    logging.info("Saved %s monthly Bronze partitions", len(groups))


def upload_raw_snapshot(articles: List[Dict[str, Any]]) -> str:
    """Upload a full raw snapshot to SeaweedFS, without changing article fields."""
    from datetime import datetime, timezone
    from uuid import uuid4

    import boto3
    from botocore.config import Config
    from src.config import get_setting


    if not articles:
        logging.info("No articles to upload.")
        return ""


    bucket = get_setting("SEAWEEDFS_RAW_BUCKET", "news-raw")

    client = boto3.client(
        "s3",
        endpoint_url=get_setting("SEAWEEDFS_ENDPOINT_URL"),
        aws_access_key_id=get_setting("SEAWEEDFS_ACCESS_KEY"),
        aws_secret_access_key=get_setting("SEAWEEDFS_SECRET_KEY"),
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=10,
            read_timeout=60,
            retries={"mode": "standard", "max_attempts": 3},
        ),
    )

    # Verify access to the bucket prepared earlier.
    client.head_bucket(Bucket=bucket)

    now = datetime.now(timezone.utc)
    run_id = f"{now:%Y%m%dT%H%M%S}_{uuid4().hex}"

    from src.datalake.partitions import group_articles, load_remote, merge_articles
    from botocore.exceptions import ClientError

    try:
        existing = load_remote(client, bucket)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in ("NoSuchKey", "404"):
            raise
        existing = []
    groups = group_articles(merge_articles(existing, articles))
    for partition in group_articles(existing):
        groups.setdefault(partition, [])
    for partition, records in groups.items():
        key = f"aljazeera/{partition}/articles.json"
        client.put_object(
            Bucket=bucket, Key=key,
            Body=json.dumps(records, ensure_ascii=False, default=str).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
            Metadata={"run-id": run_id, "record-count": str(len(records)), "snapshot-type": "monthly"},
        )
    location = f"s3://{bucket}/aljazeera/"
    logging.info("Uploaded %s monthly Bronze partitions to %s", len(groups), location)
    return location
