"""Independent Silver -> TopicService -> LLM -> news-after-llm job."""
import argparse
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

from src.config import get_setting, LLM_MAX_HEADLINES
from src.datalake.init_storage import create_client
from src.datalake.partitions import decode_records, write_json

PARTITION = re.compile(r"(year=\d{4}/month=(?:0[1-9]|1[0-2])|undated)/processed_articles\.json$")


def call_service(endpoint: str, payload):
    url = str(get_setting("ML_SERVICE_URL", "http://localhost:3000")).rstrip("/") + endpoint
    request = Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=float(get_setting("ML_SERVICE_TIMEOUT", 600))) as response:
        return json.load(response)


def enrich_articles(articles: list[dict], labels: dict) -> list[dict]:
    if not articles:
        return []
    batch_size = int(get_setting("ML_SERVICE_BATCH_SIZE", 64))
    if batch_size < 1:
        raise ValueError("ML_SERVICE_BATCH_SIZE must be positive")
    ids = [a["id"] for a in articles]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate article IDs in Silver input")
    assignments = {}
    for start in range(0, len(articles), batch_size):
        batch = articles[start:start + batch_size]
        result = call_service("/batch_infer", {"articles": batch})
        expected = {a["id"] for a in batch}
        received = set()
        if not isinstance(result, list):
            raise ValueError("Invalid inference response")
        for item in result:
            if not isinstance(item, dict) or item.get("article_id") not in expected:
                raise ValueError("Unexpected article in inference response")
            article_id = item["article_id"]
            if article_id in received or type(item.get("topic_id")) is not int:
                raise ValueError("Duplicate article or invalid topic in inference response")
            received.add(article_id)
            assignments[article_id] = item
        if received != expected:
            raise ValueError("Incomplete inference response")
    topics = {}
    for article in articles:
        topic_id = assignments[article["id"]]["topic_id"]
        if topic_id != -1:
            topics.setdefault(topic_id, []).append(article)
    for topic_id, members in topics.items():
        if topic_id not in labels:
            label = call_service("/label_topic", {"request": {
                "keywords": assignments[members[0]["id"]].get("keywords", []),
                "headlines": [a["Headline"] for a in members[:LLM_MAX_HEADLINES]],
            }})
            if not isinstance(label, dict) or not all(isinstance(label.get(k), str) and label[k].strip()
                                                     for k in ("name_ar", "summary")):
                raise ValueError("Invalid LLM label response")
            labels[topic_id] = label
    output = []
    for article in articles:
        topic_id = assignments[article["id"]]["topic_id"]
        label = labels.get(topic_id, {}) if topic_id != -1 else {}
        output.append({**article, "topic_id": topic_id, "topic_label": label.get("name_ar"),
                       "topic_summary": label.get("summary")})
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/after_llm"))
    args = parser.parse_args()
    client = create_client()
    source = get_setting("SEAWEEDFS_PROCESSED_BUCKET", "news-processed")
    target = get_setting("SEAWEEDFS_AFTER_LLM_BUCKET", "news-after-llm")
    prefix = "aljazeera/silver/"
    files = {}
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=source, Prefix=prefix):
        for item in page.get("Contents", []):
            match = PARTITION.fullmatch(item["Key"][len(prefix):])
            if match:
                files[match[1]] = item["Key"]
    if not files:
        raise ValueError("No monthly processed_articles.json files found; run processing first")
    labels, total = {}, 0
    for partition, key in sorted(files.items()):
        response = client.get_object(Bucket=source, Key=key)
        with response["Body"] as body:
            records = decode_records(body.read().decode("utf-8-sig"))
        enriched = enrich_articles(records, labels)
        payload = json.dumps(enriched, ensure_ascii=False, indent=2).encode("utf-8")
        client.put_object(Bucket=target, Key=f"aljazeera/{partition}/enriched_articles.json",
                          Body=payload, ContentType="application/json; charset=utf-8")
        write_json(args.output_dir / partition / "enriched_articles.json", enriched)
        total += len(enriched)
    print(json.dumps({"partitions": len(files), "articles": total, "bucket": target}))


if __name__ == "__main__":
    main()
