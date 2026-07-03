from pydantic import BaseModel

class StatsResponse(BaseModel):
    articles_scraped: int
    topics_discovered: int
    coverage_period: str
    last_scraped: str
