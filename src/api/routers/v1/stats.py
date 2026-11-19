from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends

from src.api.core.database import get_connection
from src.api.schemas.stats import Stats
from src.api.services import stats_service

router = APIRouter()


@router.get("/", response_model=Stats)
def read_stats(conn: psycopg.Connection = Depends(get_connection)) -> Stats:
    """Headline figures: article and topic counts, coverage window, last load."""
    return stats_service.dashboard_stats(conn)
