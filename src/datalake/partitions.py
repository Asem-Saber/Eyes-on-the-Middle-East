"""Monthly publication-date partitions shared by Bronze and Silver."""
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PARTITION = re.compile(r"(?:year=\d{4}/month=(?:0[1-9]|1[0-2])|undated)/articles\.json$")


def partition_for(record) -> str:
    if isinstance(record, dict):
        published = record.get("Published_At")
        try:
            date = (datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if isinstance(published, str) and published
                    else datetime.strptime(record.get("Date", ""), "%d/%m/%Y"))
            return f"year={date.year:04d}/month={date.month:02d}"
        except (ValueError, TypeError):
            pass
    return "undated"


def group_articles(records: list) -> dict[str, list]:
    groups = defaultdict(list)
    for record in records:
        groups[partition_for(record)].append(record)
    return dict(sorted(groups.items()))


def merge_articles(*batches) -> list:
    """Later versions of an article replace earlier versions, preserving stubs."""
    indexed, anonymous = {}, []
    for batch in batches:
        for record in batch:
            key = (record.get("id") or record.get("Link")) if isinstance(record, dict) else None
            if key:
                indexed[str(key)] = record
            else:
                anonymous.append(record)
    return list(indexed.values()) + anonymous


def decode_records(payload: str) -> list:
    records = json.loads(payload)
    if not isinstance(records, list):
        raise ValueError("Article input must be a JSON array")
    return records


def write_json(path: Path, value) -> bytes:
    payload = json.dumps(value, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return payload


def load_local(root: Path) -> list:
    paths = sorted(root.glob("year=*/month=*/articles.json"))
    unknown = root / "undated/articles.json"
    if unknown.exists():
        paths.append(unknown)
    if not paths:
        legacy = root / "articles.json"
        paths = [legacy] if legacy.exists() else []
    return merge_articles(*(decode_records(p.read_text(encoding="utf-8-sig")) for p in paths))


def load_remote(client, bucket: str, prefix: str = "aljazeera/", legacy_key: str = "aljazeera/articles.json") -> list:
    keys = []
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        keys.extend(item["Key"] for item in page.get("Contents", [])
                    if PARTITION.fullmatch(item["Key"][len(prefix):]))
    if not keys:
        keys = [legacy_key]
    batches = []
    for key in sorted(keys):
        response = client.get_object(Bucket=bucket, Key=key)
        with response["Body"] as body:
            batches.append(decode_records(body.read().decode("utf-8-sig")))
    return merge_articles(*batches)
