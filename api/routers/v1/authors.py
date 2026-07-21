from fastapi import APIRouter, Query, Depends
from typing import List
from sqlalchemy.orm import Session
from api.schemas.authors import AuthorResponse
from api.services.author_service import get_top_authors
from api.db.session import get_db

router = APIRouter()

@router.get("/top", response_model=List[AuthorResponse])
def read_top_authors(limit: int = Query(8, ge=1, le=50), db: Session = Depends(get_db)):
    """
    Get the top authors/publishers by article count.
    """
    return get_top_authors(db, limit=limit)
