from __future__ import annotations

import json
import logging
import random
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Iterable, Sequence

from src.config import (
    EMBEDDING_MODEL,
    MIN_TOPIC_SIZE,
    MODEL_DIR,
    OUTPUT_FILE,
    SHUFFLE_SEED,
    TRAINING_LABEL_TOPICS,
    TRAINING_MIN_WORDS,
    TRAINING_SECTIONS,
    setup_logging,
)
from src.ml_service.artifacts import write_manifest
from src.ml_service.bertopic_engine import TopicEngine
from src.ml_service.llm import label_topics
from src.schemas import CorpusItem, TopicSummary, TrainingReport

logger = logging.getLogger(__name__)


def format_topics(topics: Iterable[TopicSummary], limit: int = 20) -> str:
    rows = sorted(topics, key=lambda t: -t.count)[:limit]
    lines = [f"{'id':>4}  {'n':>5}  keywords"]
    for topic in rows:
        lines.append(f"{topic.topic_id:>4}  {topic.count:>5}  {', '.join(topic.keywords[:8])}")
    return "\n".join(lines)


class TopicTrainer:
    def __init__(self) -> None:
        self.engine = TopicEngine()

    def load_corpus(self) -> list[CorpusItem]:
        records = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        random.Random(SHUFFLE_SEED).shuffle(records)
        logger.info("Loaded %d articles from %s", len(records), OUTPUT_FILE)

        return self.select([CorpusItem.from_mapping(record) for record in records])

    def select(self, items: Sequence[CorpusItem]) -> list[CorpusItem]:
        dropped: Counter = Counter()
        allowed = {s.lower() for s in TRAINING_SECTIONS}
        kept: list[CorpusItem] = []

        for item in items:
            if not item.document.strip():
                dropped["empty_document"] += 1
            elif TRAINING_MIN_WORDS and item.word_count < TRAINING_MIN_WORDS:
                dropped["below_min_words"] += 1
            elif allowed and item.section.lower() not in allowed:
                dropped[f"section:{item.section}"] += 1
            else:
                kept.append(item)

        for reason, count in dropped.most_common():
            logger.info("  dropped %5d  %s", count, reason)
        logger.info("Training corpus: %d documents", len(kept))

        if not kept:
            raise ValueError(
                "Corpus is empty after filtering — lower training.min_words or widen "
                "training.sections in config.yml"
            )
        return kept

    def run(self) -> TrainingReport:
        started = time.perf_counter()
        items = self.load_corpus()

        assignments = self.engine.fit(
            [i.document for i in items], [i.article_id for i in items]
        )
        topics = self.engine.topic_table()

        report = TrainingReport(
            documents=len(items),
            topics=len(topics),
            outliers=sum(a.is_outlier for a in assignments),
            sections=list(TRAINING_SECTIONS),
            min_words=TRAINING_MIN_WORDS,
            embedding_model=EMBEDDING_MODEL,
            min_topic_size=MIN_TOPIC_SIZE,
            trained_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            duration_seconds=time.perf_counter() - started,
            topic_sizes={str(t.topic_id): t.count for t in topics},
        )

        logger.info("Fit complete: %s", report.summary())
        print()
        print(format_topics(topics))
        print()

        self.engine.save()
        write_manifest(report, MODEL_DIR, self.labels(topics))
        return report

    def labels(self, topics: Sequence[TopicSummary]) -> dict:
        if not TRAINING_LABEL_TOPICS:
            return {}

        labels = label_topics(topics)
        logger.info("Labeled %d/%d topics", len(labels), len(topics))
        return {"labels": {str(k): v.model_dump() for k, v in labels.items()}}


def main() -> None:
    setup_logging(console=True)
    report = TopicTrainer().run()
    print(report.summary())
    print(f"Model saved to {MODEL_DIR}")


if __name__ == "__main__":
    main()