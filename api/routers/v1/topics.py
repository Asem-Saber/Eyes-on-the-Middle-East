from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from api.schemas.topics import (
    TopicDistributionResponse,
    TopicTrendResponse,
    TopicResponse,
    TopicDetailResponse,
)
from api.services.analytics import (
    get_topic_distribution,
    get_topic_trends,
    get_topics_list,
    get_topic_detail,
)
from api.db.session import get_db

router = APIRouter()


@router.get("/", response_model=List[TopicResponse])
def read_topics(db: Session = Depends(get_db)):
    """Get all topics with id, name, keywords, and article count."""
    return get_topics_list(db)


@router.get("/distribution", response_model=List[TopicDistributionResponse])
def read_topic_distribution(db: Session = Depends(get_db)):
    """Get the overall distribution of articles across different topics."""
    return get_topic_distribution(db)


@router.get("/trends", response_model=List[TopicTrendResponse])
def read_topic_trends(db: Session = Depends(get_db)):
    """Get the weekly trend for the top 5 topics."""
    return get_topic_trends(db)


@router.get("/{topic_id}", response_model=TopicDetailResponse)
def read_topic_detail(topic_id: int, db: Session = Depends(get_db)):
    """Get detailed stats, trend, contributors, and articles for a single topic."""
    result = get_topic_detail(db, topic_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return result
