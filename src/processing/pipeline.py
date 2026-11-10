from datetime import datetime
from hashlib import sha256
from urllib.parse import urlparse

from .normalizer import normalize_text
from .quality import clean_text, clean_paragraphs, check_quality


def process_articles(records: list, *, min_words: int = 20, min_arabic_ratio: float = 0.3) -> dict:
    """Rebuild Silver from the scraper's cumulative snapshot, deterministically."""
    if min_words < 1 or not 0 <= min_arabic_ratio <= 1:
        raise ValueError("invalid quality thresholds")
    accepted, rejected = [], []
    seen_ids, seen_hashes = set(), set()
    duplicates = 0
    for index, record in enumerate(records):
        try:
            if not isinstance(record, dict):
                raise ValueError("record must be an object")
            article_id = record.get("id")
            url = record.get("Link")
            headline = record.get("Headline")
            paragraphs = record.get("Full_Content")
            published = record.get("Published_At")
            if not isinstance(article_id, str) or not article_id.strip():
                raise ValueError("missing article id")
            if not isinstance(url, str) or urlparse(url).scheme not in ("http", "https") or not urlparse(url).netloc:
                raise ValueError("invalid article URL")
            if not isinstance(headline, str) or not headline.strip() or headline == "No Headline":
                raise ValueError("missing headline")
            if not isinstance(paragraphs, list) or not paragraphs or not all(isinstance(p, str) for p in paragraphs):
                raise ValueError("missing or invalid article body")
            try:
                if isinstance(published, str) and published:
                    publication_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                else:
                    publication_date = datetime.strptime(record.get("Date", ""), "%d/%m/%Y")
            except (ValueError, TypeError):
                raise ValueError("missing or invalid publication date") from None
            summary = record.get("Summary", "No Summary")
            publisher = record.get("Publisher", "")
            topics = record.get("Topics", [])
            sources = record.get("Sources", [])
            if not isinstance(summary, str) or not isinstance(publisher, str):
                raise ValueError("Summary and Publisher must be strings")
            if not all(isinstance(values, list) and all(isinstance(v, str) for v in values)
                       for values in (topics, sources)):
                raise ValueError("Topics and Sources must be lists of strings")
            topic_id = record.get("topic_id")
            topic_label = record.get("topic_label")
            if topic_id is not None and type(topic_id) is not int:
                raise ValueError("topic_id must be an integer or null")
            if topic_label is not None and not isinstance(topic_label, str):
                raise ValueError("topic_label must be a string or null")
            paragraphs = clean_paragraphs(paragraphs, summary)
            check_quality(paragraphs, min_words, min_arabic_ratio)
            body = "\n".join(paragraphs)
            normalized = normalize_text(body)
            if not normalized:
                raise ValueError("empty normalized body")
            content_hash = sha256(normalized.encode("utf-8")).hexdigest()
            if article_id in seen_ids or content_hash in seen_hashes:
                duplicates += 1
                continue
            seen_ids.add(article_id)
            seen_hashes.add(content_hash)
            accepted.append({
                "id": article_id,
                "Link": url,
                "Headline": clean_text(headline),
                "Summary": clean_text(summary),
                "Full_Content": paragraphs,
                "Publisher": publisher,
                "Topics": list(topics),
                "Sources": list(sources),
                "Date": f"{publication_date.day}/{publication_date.month}/{publication_date.year}",
                "topic_id": topic_id,
                "topic_label": topic_label,
            })
        except ValueError as exc:
            rejected.append({"index": index, "reason": str(exc), "record": record})
    return {
        "articles": accepted,
        "rejected": rejected,
        "report": {"input": len(records), "accepted": len(accepted), "rejected": len(rejected), "duplicates": duplicates},
    }
