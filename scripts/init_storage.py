import os
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Read .env from the project root.
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# دلوقتي هنعمل كونيكت علي ال seaweedfs من خلال ال s3
s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["SEAWEEDFS_ENDPOINT_URL"],
    aws_access_key_id=os.environ["SEAWEEDFS_ACCESS_KEY"],
    aws_secret_access_key=os.environ["SEAWEEDFS_SECRET_KEY"],
    region_name="us-east-1",
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
    ),
)

# Create the buckets.
for bucket in ("news-raw", "news-processed"):
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"Already exists: {bucket}")

    except ClientError as exc:
        status = exc.response["ResponseMetadata"]["HTTPStatusCode"]

        if status != 404:
            raise

        s3.create_bucket(Bucket=bucket)
        print(f"Created: {bucket}")

# Verify that both buckets are accessible.
for bucket in ("news-raw", "news-processed"):
    s3.head_bucket(Bucket=bucket)

print("Storage buckets are ready.")