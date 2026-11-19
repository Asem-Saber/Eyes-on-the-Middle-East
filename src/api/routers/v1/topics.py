from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.core.database import get_connection
from src.api.schemas.topics import Topic, TopicDetail, TopicDistribution, TopicTrendPoint
from src.api.services import topic_service

router = APIRouter()


@router.get("/", response_model=list[Topic])
def read_topics(
    include_outliers: bool = Query(True, description="Include topic -1 (غير مصنف)"),
    conn: psycopg.Connection = Depends(get_connection),
) -> list[Topic]:
    """Every topic with its article count, busiest first."""
    return topic_service.list_topics(conn, include_outliers=include_outliers)


@router.get("/distribution", response_model=list[TopicDistribution])
def read_distribution(
    limit: int = Query(20, ge=1, le=100),
    conn: psycopg.Connection = Depends(get_connection),
) -> list[TopicDistribution]:
    """Article counts per topic, outliers excluded."""
    return topic_service.topic_distribution(conn, limit=limit)


@router.get("/trends", response_model=dict[int, list[TopicTrendPoint]])
def read_trends(
    topics: int = Query(5, ge=1, le=20),
    conn: psycopg.Connection = Depends(get_connection),
) -> dict[int, list[TopicTrendPoint]]:
    """Weekly counts for the busiest topics, keyed by topic id."""
    return topic_service.topic_trends(conn, topics=topics)


@router.get("/{topic_id}", response_model=TopicDetail)
def read_topic(
    topic_id: int,
    articles: int = Query(20, ge=1, le=100),
    conn: psycopg.Connection = Depends(get_connection),
) -> TopicDetail:
    """One topic with its stats, weekly trend, monthly volume and recent articles."""
    topic = topic_service.topic_detail(conn, topic_id, articles=articles)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
