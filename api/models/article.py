from sqlalchemy import Column, String, Integer, Date, Text, JSON
from api.db.base import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, index=True)
    link = Column(String)
    headline = Column(String)
    summary = Column(Text)
    full_content = Column(JSON)
    publisher = Column(String, index=True)
    topics = Column(JSON)
    sources = Column(JSON)
    date = Column(Date, index=True)
    topic_id = Column(Integer, index=True)
    topic_label = Column(String, index=True)
