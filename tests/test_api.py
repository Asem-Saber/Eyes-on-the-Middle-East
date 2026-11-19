from __future__ import annotations

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from src.api.core.database import get_connection
from src.api.main import app
from src.api.services.article_service import _filters


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_: object) -> bool:
        return False

    def execute(self, query: str, params=None) -> None:
        # Collapse whitespace so assertions can match on SQL fragments.
        self.connection.calls.append((" ".join(query.split()), params))

    def fetchall(self) -> list[dict]:
        return self.connection.next_result()

    def fetchone(self) -> dict | None:
        rows = self.connection.next_result()
        return rows[0] if rows else None


class FakeConnection:
    """Replays queued result sets in the order the service asks for them."""

    def __init__(self, *results: list[dict]) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, object]] = []

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def next_result(self) -> list[dict]:
        return self.results.pop(0) if self.results else []


def client_for(connection: FakeConnection) -> TestClient:
    app.dependency_overrides[get_connection] = lambda: connection
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def params_for(connection: FakeConnection, fragment: str) -> dict:
    """The parameters of the first query containing `fragment`."""
    for query, params in connection.calls:
        if fragment in query:
            return params or {}
    raise AssertionError(f"No query contained {fragment!r}")


# ── stats ───────────────────────────────────────────────────────────

def test_stats_maps_the_row_onto_the_contract():
    conn = FakeConnection([{
        "articles_total": 5154, "topics_total": 85, "sources_total": 1,
        "outlier_articles": 499, "coverage_start": date(2026, 5, 23),
        "coverage_end": date(2026, 11, 9),
        "last_loaded_at": datetime(2026, 11, 19, 9, 30),
    }])
    body = client_for(conn).get("/api/v1/stats/").json()

    assert body["articles_total"] == 5154
    assert body["coverage_start"] == "2026-05-23"
    assert body["outlier_articles"] == 499


def test_stats_on_an_empty_mart_returns_zeros_not_nulls():
    """An unbuilt warehouse aggregates to a single all-null row, not no row."""
    conn = FakeConnection([{
        "articles_total": 0, "topics_total": None, "sources_total": None,
        "outlier_articles": None, "coverage_start": None,
        "coverage_end": None, "last_loaded_at": None,
    }])
    body = client_for(conn).get("/api/v1/stats/").json()

    assert body["articles_total"] == 0
    assert body["topics_total"] == 0
    assert body["coverage_start"] is None


# ── articles ────────────────────────────────────────────────────────

ARTICLE_ROW = {
    "article_id": "0ceba5fe91b1", "headline": "عنوان", "summary": "ملخص",
    "url": "https://www.ajnet.me/politics/x", "published_date": date(2026, 11, 9),
    "source_name": "Al Jazeera", "topic_id": 75, "topic_label": "الأردن",
    "word_count": 420,
}


def test_articles_pagination_arithmetic():
    conn = FakeConnection([{"total": 25}], [ARTICLE_ROW])
    body = client_for(conn).get("/api/v1/articles/?page=2&limit=8").json()

    assert body["total"] == 25
    assert body["page"] == 2
    assert body["pages"] == 4  # ceil(25 / 8)
    assert params_for(conn, "limit %(limit)s")["offset"] == 8


def test_articles_without_filters_builds_no_where_clause():
    conn = FakeConnection([{"total": 0}], [])
    client_for(conn).get("/api/v1/articles/")

    count_query = next(q for q, _ in conn.calls if "count(*)" in q)
    assert " where " not in count_query


def test_articles_filters_reach_the_query():
    conn = FakeConnection([{"total": 1}], [ARTICLE_ROW])
    client_for(conn).get(
        "/api/v1/articles/?search=غزة&date_from=2026-01-01&date_to=2026-12-31"
    )

    params = params_for(conn, "count(*)")
    assert params["search"] == "%غزة%"
    assert params["date_from"] == "2026-01-01"
    assert params["date_to"] == "2026-12-31"


def test_topic_zero_is_a_real_filter_not_a_missing_one():
    """Topic 0 is the largest cluster; a falsy check would silently drop it."""
    conn = FakeConnection([{"total": 1}], [ARTICLE_ROW])
    client_for(conn).get("/api/v1/articles/?topic=0")

    assert params_for(conn, "count(*)")["topic_id"] == 0


def test_article_detail_returns_404_when_absent():
    conn = FakeConnection([])
    assert client_for(conn).get("/api/v1/articles/nope").status_code == 404


def test_article_detail_tolerates_a_null_body():
    row = {**ARTICLE_ROW, "full_content": None, "paragraph_count": 0,
           "topic_summary": None, "model_version": "v1", "is_outlier": False}
    conn = FakeConnection([row])
    body = client_for(conn).get("/api/v1/articles/0ceba5fe91b1").json()

    assert body["full_content"] == []


@pytest.mark.parametrize("query", ["?page=0", "?limit=0", "?limit=5000"])
def test_out_of_range_paging_is_rejected(query: str):
    conn = FakeConnection([{"total": 0}], [])
    assert client_for(conn).get(f"/api/v1/articles/{query}").status_code == 422


# ── topics ──────────────────────────────────────────────────────────

TOPIC_ROW = {
    "topic_key": 1, "topic_id": 0, "model_version": "legacy-unversioned",
    "topic_label": "تطورات الحرب في غزة", "topic_summary": None,
    "is_outlier": False, "article_count": 1077,
}


def test_topics_include_outliers_toggles_the_where_clause():
    with_outliers = FakeConnection([TOPIC_ROW])
    client_for(with_outliers).get("/api/v1/topics/?include_outliers=true")
    assert not any("not t.is_outlier" in q for q, _ in with_outliers.calls)

    app.dependency_overrides.clear()
    without = FakeConnection([TOPIC_ROW])
    client_for(without).get("/api/v1/topics/?include_outliers=false")
    assert any("not t.is_outlier" in q for q, _ in without.calls)


def test_trends_are_keyed_by_topic_id():
    """The dashboard pivots this object; an array would break the chart."""
    conn = FakeConnection([
        {"topic_id": 0, "iso_year": 2026, "iso_week": 7, "count": 12},
        {"topic_id": 0, "iso_year": 2026, "iso_week": 8, "count": 15},
        {"topic_id": 7, "iso_year": 2026, "iso_week": 8, "count": 3},
    ])
    body = client_for(conn).get("/api/v1/topics/trends?topics=2").json()

    assert isinstance(body, dict)
    assert set(body) == {"0", "7"}
    assert [p["iso_week"] for p in body["0"]] == [7, 8]


# ── cross-cutting ───────────────────────────────────────────────────

@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:8080", "http://127.0.0.1:8080",
        "http://localhost:5173", "http://127.0.0.1:5173",
    ],
)
def test_both_spellings_of_each_dev_origin_are_allowed(origin: str):
    """A browser treats localhost and 127.0.0.1 as different origins; the
    dashboard silently failed every fetch when only one spelling was listed."""
    conn = FakeConnection([{"articles_total": 0}])
    response = client_for(conn).get("/api/v1/stats/", headers={"Origin": origin})

    assert response.headers.get("access-control-allow-origin") == origin


def test_health_reports_503_when_the_warehouse_is_unreachable(monkeypatch):
    def boom():
        raise RuntimeError('relation "fct_articles" does not exist')

    monkeypatch.setattr("src.api.main.connect", boom)
    response = TestClient(app).get("/health")

    assert response.status_code == 503
    assert response.json()["warehouse"] == "unreachable"


# ── filter assembly, directly ───────────────────────────────────────

def test_filters_emit_no_clause_when_everything_is_none():
    where, params = _filters(None, None, None, None)
    assert where == "" and params == {}


def test_filters_wrap_search_for_ilike():
    _, params = _filters(None, "gaza", None, None)
    assert params["search"] == "%gaza%"


def test_filters_and_clauses_together():
    where, params = _filters(3, "x", "2026-01-01", None)
    assert where.count(" and ") == 2
    assert set(params) == {"topic_id", "search", "date_from"}
