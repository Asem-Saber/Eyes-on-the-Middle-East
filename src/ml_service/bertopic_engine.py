from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import numpy as np
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

from src.config import (
    CALCULATE_PROBABILITIES,
    EMBED_BATCH_SIZE,
    EMBED_DEVICE,
    EMBEDDING_MODEL,
    LANGUAGE,
    MAX_DF,
    MAX_SEQ_LENGTH,
    MIN_CLUSTER_SIZE,
    MIN_DF,
    MIN_SAMPLES,
    MIN_TOPIC_SIZE,
    MMR_DIVERSITY,
    MODEL_DIR,
    N_COMPONENTS,
    N_NEIGHBORS,
    NGRAM_RANGE,
    NR_TOPICS,
    SEED,
    TOP_N_WORDS,
)
from src.schemas import OUTLIER_TOPIC, TopicAssignment, TopicSummary

logger = logging.getLogger(__name__)


def _as_list(value: object) -> list[str]:
    return [str(v) for v in value] if isinstance(value, (list, tuple)) else []


class TopicEngine:
    def __init__(self, model_dir: Path | str | None = None) -> None:
        self.model_dir = Path(model_dir or MODEL_DIR)
        self.model: BERTopic | None = None

        logger.info("Loading embedding model %s", EMBEDDING_MODEL)
        self.embedder = SentenceTransformer(EMBEDDING_MODEL, device=EMBED_DEVICE)

        self.embedder.max_seq_length = MAX_SEQ_LENGTH
        logger.info(
            "Embedder ready on %s, max_seq_length=%s", self.embedder.device, MAX_SEQ_LENGTH
        )

    def build(self) -> BERTopic:
        umap_model = UMAP(
            n_neighbors=N_NEIGHBORS,
            n_components=N_COMPONENTS,
            min_dist=0.0,
            metric="cosine",
            random_state=SEED,
        )

        hdbscan_model = HDBSCAN(
            min_cluster_size=MIN_CLUSTER_SIZE,
            min_samples=MIN_SAMPLES,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )

        vectorizer_model = CountVectorizer(
            min_df=MIN_DF,
            max_df=MAX_DF,
            ngram_range=NGRAM_RANGE,
        )

        return BERTopic(
            embedding_model=self.embedder,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            representation_model={
                "KeyBERT": KeyBERTInspired(),
                "MMR": MaximalMarginalRelevance(diversity=MMR_DIVERSITY),
            },
            top_n_words=TOP_N_WORDS,
            min_topic_size=MIN_TOPIC_SIZE,
            nr_topics=NR_TOPICS,
            language=LANGUAGE,
            calculate_probabilities=CALCULATE_PROBABILITIES,
            verbose=True,
        )


    def encode(self, documents: Sequence[str], show_progress: bool = False) -> np.ndarray:
        return self.embedder.encode(
            list(documents),
            batch_size=EMBED_BATCH_SIZE,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

    def fit(
        self, documents: Sequence[str], document_ids: Sequence[str] | None = None
    ) -> list[TopicAssignment]:
        if not documents:
            raise ValueError("fit() needs at least one document")
        if len(documents) < MIN_CLUSTER_SIZE:
            raise ValueError(
                f"{len(documents)} documents is below min_cluster_size={MIN_CLUSTER_SIZE}; "
                "every one would be an outlier"
            )

        ids = self._resolve_ids(documents, document_ids)

        logger.info("Encoding %d documents", len(documents))
        embeddings = self.encode(documents, show_progress=True)
        logger.info("Embeddings shape: %s", embeddings.shape)

        self.model = self.build()
        logger.info("Fitting BERTopic")
        topics, probabilities = self.model.fit_transform(list(documents), embeddings)
        return self._to_assignments(ids, topics, probabilities)

    def transform(
        self, documents: Sequence[str], document_ids: Sequence[str] | None = None
    ) -> list[TopicAssignment]:
        """Assign already-trained topics to new documents."""
        if not documents:
            return []

        ids = self._resolve_ids(documents, document_ids)
        topics, probabilities = self._require_model().transform(
            list(documents), self.encode(documents)
        )
        return self._to_assignments(ids, topics, probabilities)

    def _require_model(self) -> BERTopic:
        if self.model is None:
            raise RuntimeError(f"No topic model loaded. Call fit(), or load() from {self.model_dir}.")
        return self.model

    @staticmethod
    def _resolve_ids(documents: Sequence[str], document_ids: Sequence[str] | None) -> list[str]:
        ids = (
            list(document_ids)
            if document_ids is not None
            else [str(i) for i in range(len(documents))]
        )
        if len(ids) != len(documents):
            raise ValueError("document_ids must be the same length as documents")
        return ids

    @staticmethod
    def _to_assignments(ids, topics, probabilities) -> list[TopicAssignment]:
        out: list[TopicAssignment] = []
        for i, (doc_id, topic) in enumerate(zip(ids, topics)):
            prob = 0.0
            if probabilities is not None:
                value = probabilities[i]
                prob = float(max(value)) if hasattr(value, "__len__") else float(value)
            out.append(
                TopicAssignment(document_id=str(doc_id), topic_id=int(topic), probability=prob)
            )
        return out

    def topic_table(self, include_outliers: bool = False) -> list[TopicSummary]:
        """Every topic with its keywords and representative documents."""
        summaries: list[TopicSummary] = []
        for row in self._require_model().get_topic_info().to_dict("records"):
            topic_id = int(row["Topic"])
            if topic_id == OUTLIER_TOPIC and not include_outliers:
                continue
            summaries.append(
                TopicSummary(
                    topic_id=topic_id,
                    count=int(row.get("Count", 0)),
                    keywords=self.topic_keywords(topic_id),
                    representative_docs=_as_list(row.get("Representative_Docs")),
                )
            )
        return summaries

    def topic_keywords(self, topic_id: int, top_n: int = TOP_N_WORDS) -> list[str]:
        return [word for word, _score in (self._require_model().get_topic(topic_id) or [])[:top_n]]

    def save(self, path: Path | str | None = None) -> Path:
        """Persist with safetensors; the embedding model is stored by name only."""
        target = Path(path or self.model_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._require_model().save(
            str(target),
            serialization="safetensors",
            save_embedding_model=EMBEDDING_MODEL,
            save_ctfidf=True,
        )
        logger.info("Saved topic model to %s", target)
        return target

    @classmethod
    def load(cls, path: Path | str | None = None) -> "TopicEngine":
        engine = cls(model_dir=path)
        if not engine.model_dir.exists():
            raise FileNotFoundError(f"No topic model at {engine.model_dir}; train one first")

        logger.info("Loading topic model from %s", engine.model_dir)
        engine.model = BERTopic.load(str(engine.model_dir), embedding_model=engine.embedder)
        return engine
