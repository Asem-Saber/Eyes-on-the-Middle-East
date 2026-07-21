from datetime import date
from unittest.mock import MagicMock

from api.utils.topic_labels import parse_topic_label
from api.utils.serializers import article_to_dict


class TestParseTopicLabel:
    def test_standard_label(self):
        name, kws = parse_topic_label("0_ceasefire_Hamas_negotiations")
        assert name == "Ceasefire Hamas Negotiations"
        assert kws == ["ceasefire", "Hamas", "negotiations"]

    def test_negative_id_prefix(self):
        name, kws = parse_topic_label("-1_outlier_topic")
        assert name == "Outlier Topic"
        assert kws == ["outlier", "topic"]

    def test_no_numeric_prefix(self):
        name, kws = parse_topic_label("economy_trade")
        assert name == "Economy Trade"
        assert kws == ["economy", "trade"]

    def test_single_keyword(self):
        name, kws = parse_topic_label("3_politics")
        assert name == "Politics"
        assert kws == ["politics"]

    def test_empty_string(self):
        name, kws = parse_topic_label("")
        assert name == ""
        assert kws == [""]

    def test_many_keywords_capped_at_10(self):
        parts = "_".join(f"w{i}" for i in range(15))
        label = f"5_{parts}"
        _, kws = parse_topic_label(label)
        assert len(kws) == 10


class TestArticleToDict:
    def _make_article(self, **overrides):
        defaults = dict(
            id="x1",
            headline="Test Headline",
            summary="Test Summary",
            topic_label="0_test",
            topic_id=0,
            publisher="Author Name",
            date=date(2024, 3, 15),
            link="https://example.com",
        )
        defaults.update(overrides)
        article = MagicMock()
        for k, v in defaults.items():
            setattr(article, k, v)
        return article

    def test_full_fields(self):
        article = self._make_article()
        d = article_to_dict(article)
        assert d["id"] == "x1"
        assert d["headline"] == "Test Headline"
        assert d["summary"] == "Test Summary"
        assert d["topic_label"] == "0_test"
        assert d["topic_id"] == 0
        assert d["author"] == "Author Name"
        assert d["date"] == "2024-03-15"
        assert d["link"] == "https://example.com"

    def test_null_summary_defaults_to_empty(self):
        d = article_to_dict(self._make_article(summary=None))
        assert d["summary"] == ""

    def test_null_topic_label_defaults_to_uncategorized(self):
        d = article_to_dict(self._make_article(topic_label=None))
        assert d["topic_label"] == "Uncategorized"

    def test_null_publisher_defaults_to_unknown(self):
        d = article_to_dict(self._make_article(publisher=None))
        assert d["author"] == "Unknown"

    def test_null_date_defaults_to_no_date(self):
        d = article_to_dict(self._make_article(date=None))
        assert d["date"] == "No Date"

    def test_null_link_defaults_to_hash(self):
        d = article_to_dict(self._make_article(link=None))
        assert d["link"] == "#"
