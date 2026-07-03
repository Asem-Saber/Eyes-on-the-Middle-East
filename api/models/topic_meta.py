from sqlalchemy import Column, Integer, String, JSON
from api.db.base import Base


class TopicMeta(Base):
    __tablename__ = "topic_meta"

    topic_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    keywords = Column(JSON, default=list)
