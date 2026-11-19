from fastapi import APIRouter

from src.api.routers.v1 import articles, sources, stats, topics

api_router = APIRouter()

api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
