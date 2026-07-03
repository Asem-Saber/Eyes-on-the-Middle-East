from pydantic import BaseModel
from typing import List, Optional


class ArticleResponse(BaseModel):
    id: str
    headline: str
    summary: Optional[str] = None
    topic_label: str
    topic_id: Optional[int] = None
    author: str
    date: str
    link: str


class ArticleDetailResponse(ArticleResponse):
    full_content: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    sources: Optional[List[str]] = None


class PaginatedArticleResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    page: int
    pages: int


class MonthlyVolumeResponse(BaseModel):
    month: str
    count: int
