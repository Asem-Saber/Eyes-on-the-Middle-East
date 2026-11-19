from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, Query

from src.api.core.database import get_connection
from src.api.schemas.sources import Source
from src.api.services import source_service

router = APIRouter()


@router.get("/", response_model=list[Source])
def read_sources(
    limit: int = Query(20, ge=1, le=100),
    conn: psycopg.Connection = Depends(get_connection),
) -> list[Source]:
    """Publishing sources by article count.

    This is where v1's `/authors/top` went. The pipeline no longer keeps a
    `Publisher` field, so sources are ranked by domain instead of by byline.
    """
    return source_service.list_sources(conn, limit=limit)
