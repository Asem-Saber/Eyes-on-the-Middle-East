"""Run with python -m src.processing.main --help from the project root."""
import argparse
import json
import os
from pathlib import Path

from .pipeline import process_articles


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild Silver from a full Bronze article snapshot")
    parser.add_argument("--input", type=Path, help="Local JSON input; otherwise read SeaweedFS")
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
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        client = boto3.client(
            "s3",
            endpoint_url=os.environ["SEAWEEDFS_ENDPOINT_URL"],
            aws_access_key_id=os.environ["SEAWEEDFS_ACCESS_KEY"],
            aws_secret_access_key=os.environ["SEAWEEDFS_SECRET_KEY"],
            region_name="us-east-1",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"},
                          connect_timeout=10, read_timeout=60,
                          retries={"mode": "standard", "max_attempts": 3}),
        )
    if args.input is not None:
        records = json.loads(args.input.read_text(encoding="utf-8-sig"))
    else:
        raw_key = os.getenv("SEAWEEDFS_RAW_KEY", "aljazeera/articles.json")
        response = client.get_object(
            Bucket=os.getenv("SEAWEEDFS_RAW_BUCKET", "news-raw"), Key=raw_key
        )
        with response["Body"] as body:
            records = json.loads(body.read().decode("utf-8-sig"))
    if not isinstance(records, list):
        raise ValueError("Bronze input must be a JSON array")
    result = process_articles(records, min_words=args.min_words, min_arabic_ratio=args.min_arabic_ratio)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    names = {"articles": "processed_articles.json", "rejected": "rejected.json", "report": "report.json"}
    outputs = [(filename, json.dumps(result[name], ensure_ascii=False, indent=2).encode("utf-8"),
                "application/json; charset=utf-8") for name, filename in names.items()]
    for filename, payload, content_type in outputs:
        target = args.output_dir / filename
        temporary = target.with_suffix(".tmp")
        temporary.write_bytes(payload)
        temporary.replace(target)
        if not args.local_only:
            client.put_object(
                Bucket=os.getenv("SEAWEEDFS_PROCESSED_BUCKET", "news-processed"),
                Key=f"aljazeera/silver/{filename}", Body=payload,
                ContentType=content_type,
            )
    print(json.dumps(result["report"]))


if __name__ == "__main__":
    main()
