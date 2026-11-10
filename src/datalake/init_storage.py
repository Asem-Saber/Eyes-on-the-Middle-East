import os
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_client():
    return boto3.client(
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


def ensure_bucket(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        status = exc.response["ResponseMetadata"]["HTTPStatusCode"]

        if status != 404:
            raise

        client.create_bucket(Bucket=bucket)
        print(f"Created: {bucket}")
    else:
        print(f"Already exists: {bucket}")

    client.head_bucket(Bucket=bucket)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    buckets = (
        os.getenv("SEAWEEDFS_RAW_BUCKET", "news-raw"),
        os.getenv("SEAWEEDFS_PROCESSED_BUCKET", "news-processed"),
    )

    client = create_client()

    for bucket in dict.fromkeys(buckets):
        ensure_bucket(client, bucket)

    print("Storage buckets are ready.")


if __name__ == "__main__":
    main()