"""Copy legacy local Bronze data into monthly partitions without deleting it."""
import argparse

from src.scraper.storage import load_existing_articles, save_articles, upload_raw_snapshot
from src.datalake.partitions import group_articles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upload", action="store_true", help="Also merge and partition Bronze in SeaweedFS")
    args = parser.parse_args()
    records = load_existing_articles()
    if not records:
        raise SystemExit("No local Bronze records found")
    save_articles(records)
    if args.upload:
        upload_raw_snapshot(records)
    print(f"Migrated {len(records)} records into {len(group_articles(records))} partitions; legacy files retained.")


if __name__ == "__main__":
    main()
