from fastapi import APIRouter

from api.routers.v1 import stats, topics, authors, articles

api_router = APIRouter()

api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(authors.router, prefix="/authors", tags=["authors"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
