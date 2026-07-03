from pydantic import BaseModel
from typing import List
from api.schemas.articles import ArticleResponse


class TopicResponse(BaseModel):
    topic_id: int
    name: str
    keywords: List[str]
    count: int


class TopicDetailStats(BaseModel):
    article_count: int
    contributors_count: int
    date_range: str


class TopicContributor(BaseModel):
    author: str
    count: int


class TopicTrendPoint(BaseModel):
    week: str
    count: int


class TopicMonthlyVolumePoint(BaseModel):
    month: str
    count: int


class TopicDetailResponse(BaseModel):
    topic_id: int
    name: str
    keywords: List[str]
    stats: TopicDetailStats
    contributors: List[TopicContributor]
    trend: List[TopicTrendPoint]
    monthly_volume: List[TopicMonthlyVolumePoint]
    articles: List[ArticleResponse]


class TopicDistributionResponse(BaseModel):
    topic: str
    count: int


# Dynamic dict for trends (keys are topic names)
from typing import Dict, Any
TopicTrendResponse = Dict[str, Any]
