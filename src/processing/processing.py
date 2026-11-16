"""Run with python -m src.processing.processing --help from the project root."""
import argparse
import json
from pathlib import Path

from .pipeline import process_articles
from src.datalake.partitions import decode_records, group_articles, load_local, load_remote, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild Silver from a full Bronze article snapshot")
    parser.add_argument("--input", type=Path, help="Local JSON file or partition directory; otherwise read SeaweedFS")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--upload", action="store_true", help="Compatibility flag; upload is now the default")
    parser.add_argument("--local-only", action="store_true", help="Skip upload for an offline preview")
    parser.add_argument("--min-words", type=int, default=20)
    parser.add_argument("--min-arabic-ratio", type=float, default=0.3)
    args = parser.parse_args()
    if args.min_words < 1 or not 0 <= args.min_arabic_ratio <= 1:
        parser.error("min-words must be positive; min-arabic-ratio must be between 0 and 1")
    client = None
    if args.input is None or not args.local_only:
        import boto3
        from botocore.config import Config
        from src.config import get_setting

        client = boto3.client(
            "s3",
            endpoint_url=get_setting("SEAWEEDFS_ENDPOINT_URL"),
            aws_access_key_id=get_setting("SEAWEEDFS_ACCESS_KEY"),
            aws_secret_access_key=get_setting("SEAWEEDFS_SECRET_KEY"),
            region_name="us-east-1",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"},
                          connect_timeout=10, read_timeout=60,
                          retries={"mode": "standard", "max_attempts": 3}),
        )
    if args.input is not None:
        records = (load_local(args.input) if args.input.is_dir()
                   else decode_records(args.input.read_text(encoding="utf-8-sig")))
    else:
        records = load_remote(client, get_setting("SEAWEEDFS_RAW_BUCKET", "news-raw"),
                              legacy_key=get_setting("SEAWEEDFS_RAW_KEY", "aljazeera/articles.json"))
    totals = {"input": 0, "accepted": 0, "rejected": 0, "duplicates": 0}
    names = {"articles": "processed_articles.json", "rejected": "rejected.json", "report": "report.json"}
    groups = group_articles(records)
    # Retain empty Bronze partitions too, clearing stale Silver outputs on full rebuilds.
    if args.input is None:
        bucket = get_setting("SEAWEEDFS_RAW_BUCKET", "news-raw")
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix="aljazeera/"):
            from src.datalake.partitions import PARTITION
            for item in page.get("Contents", []):
                relative = item["Key"][len("aljazeera/"):]
                if PARTITION.fullmatch(relative):
                    groups.setdefault(relative.rsplit("/", 1)[0], [])
    elif args.input.is_dir():
        for path in args.input.glob("year=*/month=*/articles.json"):
            groups.setdefault(path.parent.relative_to(args.input).as_posix(), [])
        if (args.input / "undated/articles.json").exists():
            groups.setdefault("undated", [])
    seen = (set(), set())
    for partition, batch in sorted(groups.items()):
        result = process_articles(batch, min_words=args.min_words, min_arabic_ratio=args.min_arabic_ratio, seen=seen)
        for name in totals:
            totals[name] += result["report"][name]
        for name, filename in names.items():
            payload = write_json(args.output_dir / partition / filename, result[name])
            if not args.local_only:
                client.put_object(
                    Bucket=get_setting("SEAWEEDFS_PROCESSED_BUCKET", "news-processed"),
                    Key=f"aljazeera/silver/{partition}/{filename}", Body=payload,
                    ContentType="application/json; charset=utf-8",
                )
    print(json.dumps(totals))


if __name__ == "__main__":
    main()
