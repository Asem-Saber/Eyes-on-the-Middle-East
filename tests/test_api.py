import pytest
from tests.conftest import SAMPLE_ARTICLES, SAMPLE_TOPIC_META
from api.models.article import Article
from api.models.topic_meta import TopicMeta


@pytest.fixture()
def seeded_client(client, engine):
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()
    for a in SAMPLE_ARTICLES:
        session.add(Article(**a))
    for m in SAMPLE_TOPIC_META:
        session.add(TopicMeta(**m))
    session.commit()
    session.close()
    return client


class TestRootAndHealth:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "Eyes on the Middle East" in r.json()["message"]

    def test_health_responds(self, client):
        r = client.get("/health")
        assert r.status_code in (200, 503)
        assert "status" in r.json()


class TestStatsEndpoint:
    def test_stats_empty(self, client):
        r = client.get("/api/v1/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["articles_scraped"] == 0

    def test_stats_with_data(self, seeded_client):
        r = seeded_client.get("/api/v1/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["articles_scraped"] == 4
        assert data["topics_discovered"] == 3


class TestTopicsEndpoints:
    def test_list(self, seeded_client):
        r = seeded_client.get("/api/v1/topics")
        assert r.status_code == 200
        topics = r.json()
        assert len(topics) > 0
        assert all("topic_id" in t and "name" in t and "keywords" in t for t in topics)

    def test_distribution(self, seeded_client):
        r = seeded_client.get("/api/v1/topics/distribution")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        assert all("topic" in d and "count" in d for d in data)

    def test_trends(self, seeded_client):
        r = seeded_client.get("/api/v1/topics/trends")
        assert r.status_code == 200

    def test_detail_found(self, seeded_client):
        r = seeded_client.get("/api/v1/topics/0")
        assert r.status_code == 200
        data = r.json()
        assert data["topic_id"] == 0
        assert data["name"] == "Ceasefire Negotiations"
        assert "stats" in data
        assert "contributors" in data
        assert "trend" in data

    def test_detail_not_found(self, seeded_client):
        r = seeded_client.get("/api/v1/topics/9999")
        assert r.status_code == 404


class TestArticlesEndpoints:
    def test_paginated_default(self, seeded_client):
        r = seeded_client.get("/api/v1/articles")
        assert r.status_code == 200
        data = r.json()
        assert "articles" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert data["total"] == 3  # "No Headline" excluded

    def test_paginated_with_limit(self, seeded_client):
        r = seeded_client.get("/api/v1/articles?limit=1&page=1")
        assert r.status_code == 200
        data = r.json()
        assert len(data["articles"]) == 1
        assert data["pages"] == 3

    def test_paginated_topic_filter(self, seeded_client):
        r = seeded_client.get("/api/v1/articles?topic=1")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["articles"][0]["topic_id"] == 1

    def test_paginated_search(self, seeded_client):
        r = seeded_client.get("/api/v1/articles?search=Summit")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1

    def test_paginated_date_range(self, seeded_client):
        r = seeded_client.get("/api/v1/articles?date_from=2024-07-01&date_to=2024-07-31")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2

    def test_recent(self, seeded_client):
        r = seeded_client.get("/api/v1/articles/recent")
        assert r.status_code == 200
        articles = r.json()
        assert len(articles) <= 10
        assert all(a["headline"] != "No Headline" for a in articles)

    def test_recent_limit(self, seeded_client):
        r = seeded_client.get("/api/v1/articles/recent?limit=1")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_monthly_volume(self, seeded_client):
        r = seeded_client.get("/api/v1/articles/monthly-volume")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        assert all("month" in d and "count" in d for d in data)

    def test_detail_found(self, seeded_client):
        r = seeded_client.get("/api/v1/articles/abc123")
        assert r.status_code == 200
        data = r.json()
        assert data["headline"] == "Gaza Ceasefire Talks Resume"
        assert data["full_content"] == ["Paragraph 1", "Paragraph 2"]

    def test_detail_not_found(self, seeded_client):
        r = seeded_client.get("/api/v1/articles/nonexistent")
        assert r.status_code == 404


class TestAuthorsEndpoint:
    def test_top_authors(self, seeded_client):
        r = seeded_client.get("/api/v1/authors/top")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        assert data[0]["author"] == "Ahmed Ali"
        assert data[0]["count"] == 2

    def test_top_authors_excludes_unknown(self, seeded_client):
        r = seeded_client.get("/api/v1/authors/top")
        authors = [d["author"] for d in r.json()]
        assert "Unknown" not in authors

    def test_top_authors_limit(self, seeded_client):
        r = seeded_client.get("/api/v1/authors/top?limit=1")
        assert r.status_code == 200
        assert len(r.json()) == 1


class TestValidation:
    def test_articles_page_must_be_positive(self, seeded_client):
        r = seeded_client.get("/api/v1/articles?page=0")
        assert r.status_code == 422

    def test_articles_limit_max_100(self, seeded_client):
        r = seeded_client.get("/api/v1/articles?limit=200")
        assert r.status_code == 422

    def test_authors_limit_max_50(self, seeded_client):
        r = seeded_client.get("/api/v1/authors/top?limit=100")
        assert r.status_code == 422
