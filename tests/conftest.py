from datetime import date

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from api.db.base import Base
from api.db.session import get_db
from api.main import app
from api.models.article import Article
from api.models.topic_meta import TopicMeta


def _sqlite_to_char(value, fmt):
    if value is None:
        return None
    s = str(value)
    if "YYYY-MM" in fmt and "W" not in fmt:
        return s[:7]
    if "IW" in fmt:
        from datetime import datetime

        try:
            d = datetime.strptime(s, "%Y-%m-%d")
            iso = d.isocalendar()
            return f"{iso[0]}-W{iso[1]:02d}"
        except (ValueError, TypeError):
            return s
    return s


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _register_functions(dbapi_conn, _record):
        dbapi_conn.create_function("to_char", 2, _sqlite_to_char)

    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def client(engine):
    Session = sessionmaker(bind=engine)

    def _override():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


SAMPLE_ARTICLES = [
    dict(
        id="abc123",
        headline="Gaza Ceasefire Talks Resume",
        summary="Negotiations continue in Cairo",
        publisher="Ahmed Ali",
        date=date(2024, 6, 15),
        topic_id=0,
        topic_label="0_ceasefire_negotiations_Hamas",
        link="https://aljazeera.net/article1",
        full_content=["Paragraph 1", "Paragraph 2"],
        topics=["politics", "conflict"],
        sources=["Reuters"],
    ),
    dict(
        id="def456",
        headline="Economic Summit in Riyadh",
        summary="Leaders discuss regional trade",
        publisher="Sarah Hassan",
        date=date(2024, 7, 1),
        topic_id=1,
        topic_label="1_economy_trade_summit",
        link="https://aljazeera.net/article2",
        full_content=["Content here"],
        topics=["economics"],
        sources=[],
    ),
    dict(
        id="ghi789",
        headline="No Headline",
        summary="Should be filtered out",
        publisher="Unknown",
        date=date(2024, 5, 10),
        topic_id=0,
        topic_label="0_ceasefire_negotiations_Hamas",
        link="https://aljazeera.net/article3",
        full_content=[],
        topics=[],
        sources=[],
    ),
    dict(
        id="jkl012",
        headline="UN Resolution on Palestine",
        summary="General Assembly votes on new resolution",
        publisher="Ahmed Ali",
        date=date(2024, 7, 10),
        topic_id=2,
        topic_label="2_UN_resolution_Palestine",
        link="https://aljazeera.net/article4",
        full_content=["Para 1"],
        topics=["diplomacy"],
        sources=["AP"],
    ),
]

SAMPLE_TOPIC_META = [
    dict(topic_id=0, name="Ceasefire Negotiations", keywords=["ceasefire", "negotiations", "Hamas"]),
    dict(topic_id=1, name="Regional Economy", keywords=["economy", "trade", "summit"]),
]


@pytest.fixture()
def seed_data(db):
    for a in SAMPLE_ARTICLES:
        db.add(Article(**a))
    for m in SAMPLE_TOPIC_META:
        db.add(TopicMeta(**m))
    db.commit()
