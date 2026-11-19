from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlparse

from pydantic import BaseModel, Field

OUTLIER_TOPIC = -1

PLACEHOLDERS = {"Error", "No Summary", "No Headline", "No Date", ""}


def clean_field(value: Any) -> str | None:
    text = str(value or "").strip()
    return None if text in PLACEHOLDERS else text


def section_of(url: str) -> str:
    parts = urlparse(url or "").path.strip("/").split("/")
    return parts[0] if parts and parts[0] else "unknown"


class ArticleRecord(BaseModel):
    """A scraped article exactly as stored. Extra keys are tolerated."""

    model_config = {"extra": "allow"}

    id: str
    Link: str = ""
    Headline: str = ""
    Summary: str = ""
    Date: str = ""
    Full_Content: list[str] = Field(default_factory=list)
    Published_At: str | None = None

    def to_corpus_item(self) -> "CorpusItem":
        parts = [self.Headline, *self.Full_Content]
        document = " ".join(str(p).strip() for p in parts if str(p).strip())
        return CorpusItem(
            article_id=self.id,
            document=document,
            headline=clean_field(self.Headline),
            section=section_of(self.Link),
            published_at=clean_field(self.Published_At),
            word_count=len(document.split()),
        )


class CorpusItem(BaseModel):
    """One training or inference unit."""

    article_id: str
    document: str
    headline: str | None = None
    section: str = "unknown"
    published_at: str | None = None
    word_count: int = 0

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CorpusItem":
        return ArticleRecord.model_validate(raw).to_corpus_item()


class TopicAssignment(BaseModel):
    """One document's topic, as returned by inference."""

    document_id: str
    topic_id: int
    probability: float = 0.0

    @property
    def is_outlier(self) -> bool:
        return self.topic_id == OUTLIER_TOPIC


class TopicSummary(BaseModel):
    """A cluster: its size, keywords and most representative documents."""

    topic_id: int
    count: int = 0
    keywords: list[str] = Field(default_factory=list)
    representative_docs: list[str] = Field(default_factory=list)


class TopicLabel(BaseModel):
    """The structured output the LLM must return."""

    name_ar: str = Field(description="Formal Arabic topic title, 3-8 words, no trailing punctuation")
    summary: str = Field(description="One-sentence Arabic description of what the topic covers")


class InferenceResult(BaseModel):
    """Per-article inference output."""

    article_id: str
    topic_id: int
    probability: float = 0.0
    keywords: list[str] = Field(default_factory=list)
    is_outlier: bool = False


class TrainingReport(BaseModel):
    """Everything worth knowing about a fit, persisted beside the weights."""

    documents: int = 0
    topics: int = 0
    outliers: int = 0
    sections: list[str] = Field(default_factory=list)
    min_words: int = 0
    embedding_model: str = ""
    min_topic_size: int = 0
    trained_at: str = ""
    duration_seconds: float = 0.0
    topic_sizes: dict[str, int] = Field(default_factory=dict)

    @property
    def outlier_rate(self) -> float:
        return self.outliers / self.documents if self.documents else 0.0

    def summary(self) -> str:
        return (
            f"{self.topics} topics over {self.documents} documents, "
            f"{self.outliers} outliers ({self.outlier_rate:.1%}) "
            f"in {self.duration_seconds:.1f}s"
        )