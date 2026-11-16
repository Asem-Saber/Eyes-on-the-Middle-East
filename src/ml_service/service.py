from __future__ import annotations

import logging
from http import HTTPStatus

import bentoml
from bentoml.exceptions import BentoMLException, InvalidArgument
from pydantic import BaseModel, Field

from src.config import MODEL_DIR, setup_logging
from src.ml_service.bertopic_engine import TopicEngine
from src.ml_service.llm import LLMError, label_topic as generate_label
from src.schemas import CorpusItem, InferenceResult, TopicLabel

logger = logging.getLogger(__name__)


class DependencyNotReady(BentoMLException):
    error_code = HTTPStatus.FAILED_DEPENDENCY


class ArticleIn(BaseModel):
    id: str
    Headline: str = ""
    Full_Content: list[str] = Field(default_factory=list)
    Link: str = ""


class LabelRequest(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    headlines: list[str] = Field(default_factory=list)


@bentoml.service(
    name="ajnet_topic_service",
    resources={"cpu": "4", "memory": "8Gi"},
    traffic={"timeout": 600, "concurrency": 8},
)
class TopicService:
    def __init__(self) -> None:
        setup_logging(console=True)
        try:
            self.engine: TopicEngine | None = TopicEngine.load()
            logger.info("Topic model ready from %s", MODEL_DIR)
        except FileNotFoundError:
            self.engine = None
            logger.warning(
                "No topic model at %s — /batch_infer returns 424 until one is trained", MODEL_DIR
            )

    @bentoml.api
    def batch_infer(self, articles: list[ArticleIn]) -> list[InferenceResult]:
        if self.engine is None:
            raise DependencyNotReady(f"No topic model at {MODEL_DIR}. Train one first.")
        if not articles:
            return []

        items = [CorpusItem.from_mapping(a.model_dump()) for a in articles]
        assignments = self.engine.transform(
            [i.document for i in items], [i.article_id for i in items]
        )

        keywords: dict[int, list[str]] = {}
        results: list[InferenceResult] = []
        for assignment in assignments:
            topic_id = assignment.topic_id
            if topic_id not in keywords:
                keywords[topic_id] = self.engine.topic_keywords(topic_id)
            results.append(
                InferenceResult(
                    article_id=assignment.document_id,
                    topic_id=topic_id,
                    probability=assignment.probability,
                    keywords=keywords[topic_id],
                    is_outlier=assignment.is_outlier,
                )
            )
        return results

    @bentoml.api
    def label_topic(self, request: LabelRequest) -> TopicLabel:
        if not request.keywords and not request.headlines:
            raise InvalidArgument("label_topic needs at least one of keywords or headlines")
        try:
            return generate_label(request.keywords, request.headlines)
        except LLMError as exc:
            raise DependencyNotReady(str(exc).splitlines()[0]) from exc
