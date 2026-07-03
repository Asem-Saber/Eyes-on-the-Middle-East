from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.schemas.stats import StatsResponse
from api.services.analytics import get_dashboard_stats
from api.db.session import get_db

router = APIRouter()

@router.get("/", response_model=StatsResponse)
def read_stats(db: Session = Depends(get_db)):
    """
    Get high-level statistics for the dashboard.
    """
    return get_dashboard_stats(db)
