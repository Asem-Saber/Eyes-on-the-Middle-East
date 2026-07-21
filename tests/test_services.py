import pytest

from api.services.stats_service import get_dashboard_stats
from api.services.article_service import (
    get_recent_articles,
    get_articles_paginated,
    get_article_by_id,
    get_monthly_volume,
)
from api.services.author_service import get_top_authors
from api.services.topic_service import (
    get_topic_distribution,
    get_topics_list,
    get_topic_detail,
    get_topic_trends,
)


class TestStatsService:
    def test_empty_db(self, db):
        stats = get_dashboard_stats(db)
        assert stats["articles_scraped"] == 0
        assert stats["topics_discovered"] == 0
        assert stats["coverage_period"] == "N/A"
        assert stats["last_scraped"] == "N/A"

    def test_with_data(self, db, seed_data):
        stats = get_dashboard_stats(db)
        assert stats["articles_scraped"] == 4
        assert stats["topics_discovered"] == 3
        assert "2024" in stats["coverage_period"]
        assert stats["last_scraped"] != "N/A"


class TestArticleService:
    def test_recent_articles_ordered_by_date(self, db, seed_data):
        results = get_recent_articles(db, limit=10)
        assert len(results) == 3  # "No Headline" filtered out
        assert results[0]["date"] >= results[1]["date"]

    def test_recent_articles_filters_bad_headlines(self, db, seed_data):
        results = get_recent_articles(db)
        headlines = [r["headline"] for r in results]
        assert "No Headline" not in headlines

    def test_recent_articles_respects_limit(self, db, seed_data):
        results = get_recent_articles(db, limit=2)
        assert len(results) == 2

    def test_paginated_basic(self, db, seed_data):
        result = get_articles_paginated(db, page=1, limit=2)
        assert result["total"] == 3  # 3 valid articles (No Headline excluded)
        assert result["page"] == 1
        assert result["pages"] == 2
        assert len(result["articles"]) == 2

    def test_paginated_second_page(self, db, seed_data):
        result = get_articles_paginated(db, page=2, limit=2)
        assert len(result["articles"]) == 1

    def test_paginated_topic_filter(self, db, seed_data):
        result = get_articles_paginated(db, topic_id=0)
        assert result["total"] == 1  # Only abc123 (ghi789 has "No Headline")
        for a in result["articles"]:
            assert a["topic_id"] == 0

    def test_paginated_search(self, db, seed_data):
        result = get_articles_paginated(db, search="Summit")
        assert result["total"] == 1
        assert result["articles"][0]["headline"] == "Economic Summit in Riyadh"

    def test_paginated_date_range(self, db, seed_data):
        result = get_articles_paginated(db, date_from="2024-07-01", date_to="2024-07-31")
        assert result["total"] == 2
        for a in result["articles"]:
            assert a["date"] >= "2024-07-01"

    def test_get_by_id_found(self, db, seed_data):
        result = get_article_by_id(db, "abc123")
        assert result is not None
        assert result["headline"] == "Gaza Ceasefire Talks Resume"
        assert "full_content" in result
        assert result["full_content"] == ["Paragraph 1", "Paragraph 2"]

    def test_get_by_id_not_found(self, db, seed_data):
        result = get_article_by_id(db, "nonexistent")
        assert result is None

    def test_monthly_volume(self, db, seed_data):
        result = get_monthly_volume(db)
        assert len(result) > 0
        months = [r["month"] for r in result]
        assert "2024-07" in months


class TestAuthorService:
    def test_top_authors(self, db, seed_data):
        results = get_top_authors(db, limit=5)
        assert len(results) > 0
        assert results[0]["count"] >= results[-1]["count"]

    def test_excludes_unknown_publishers(self, db, seed_data):
        results = get_top_authors(db, limit=10)
        authors = [r["author"] for r in results]
        assert "Unknown" not in authors

    def test_ahmed_ali_has_highest_count(self, db, seed_data):
        results = get_top_authors(db)
        assert results[0]["author"] == "Ahmed Ali"
        assert results[0]["count"] == 2


class TestTopicService:
    def test_distribution(self, db, seed_data):
        results = get_topic_distribution(db)
        assert len(results) > 0
        topics = [r["topic"] for r in results]
        assert "Unknown" not in topics

    def test_topics_list_with_meta(self, db, seed_data):
        results = get_topics_list(db)
        topic_0 = next((t for t in results if t["topic_id"] == 0), None)
        assert topic_0 is not None
        assert topic_0["name"] == "Ceasefire Negotiations"
        assert "ceasefire" in topic_0["keywords"]

    def test_topics_list_fallback_without_meta(self, db, seed_data):
        results = get_topics_list(db)
        topic_2 = next((t for t in results if t["topic_id"] == 2), None)
        assert topic_2 is not None
        assert topic_2["name"] == "Un Resolution Palestine"

    def test_topic_detail_found(self, db, seed_data):
        result = get_topic_detail(db, topic_id=0)
        assert result is not None
        assert result["name"] == "Ceasefire Negotiations"
        assert result["stats"]["article_count"] >= 1
        assert "trend" in result
        assert "monthly_volume" in result
        assert "contributors" in result
        assert "articles" in result

    def test_topic_detail_not_found(self, db, seed_data):
        result = get_topic_detail(db, topic_id=9999)
        assert result is None

    def test_topic_trends(self, db, seed_data):
        results = get_topic_trends(db)
        if results:
            assert "week" in results[0]
