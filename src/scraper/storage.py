import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Union

from src.config import OUTPUT_FILE, DATA_DIR


def load_existing_articles(file_path: Union[Path, str] = OUTPUT_FILE) -> List[Dict[str, Any]]:
    """Loads previously saved articles from disk."""
    path = Path(file_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_articles(articles: List[Dict[str, Any]], file_path: Union[Path, str] = OUTPUT_FILE) -> None:
    """Atomically serializes article records to formatted JSON."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_file = path.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
    os.replace(temp_file, path)
    logging.info(f"Saved {len(articles)} articles to {path}")

def upload_raw_snapshot(articles: List[Dict[str, Any]]) -> str:
    """Upload a full raw snapshot to SeaweedFS, without changing article fields."""
    from datetime import datetime, timezone
    from uuid import uuid4

    import boto3
    from botocore.config import Config
    from dotenv import load_dotenv

    from src.config import PROJECT_ROOT

    if not articles:
        logging.info("No articles to upload.")
        return ""

    load_dotenv(PROJECT_ROOT / ".env")

    bucket = os.getenv("SEAWEEDFS_RAW_BUCKET", "news-raw")

    client = boto3.client(
        "s3",
        endpoint_url=os.environ["SEAWEEDFS_ENDPOINT_URL"],
        aws_access_key_id=os.environ["SEAWEEDFS_ACCESS_KEY"],
        aws_secret_access_key=os.environ["SEAWEEDFS_SECRET_KEY"],
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

    key = "aljazeera/articles.json"

    body = json.dumps(
        articles,
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json; charset=utf-8",
        Metadata={
            "run-id": run_id,
            "record-count": str(len(articles)),
            "snapshot-type": "full",
        },
    )

    location = f"s3://{bucket}/{key}"
    logging.info("Uploaded %s articles to %s", len(articles), location)
    print(f"Uploaded {len(articles)} articles to {location}")

    return location