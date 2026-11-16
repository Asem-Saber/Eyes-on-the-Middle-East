import pytest

from src.modeling.load import prepare


def article(**changes):
    return {"id": "a1", "Link": "https://www.ajnet.me/politics/news", "Headline": "عنوان",
            "Summary": "ملخص المقال", "Full_Content": ["الفقرة الأولى", "الفقرة الثانية"],
            "Date": "1/5/2026", "topic_id": 17, "topic_label": "عنوان الموضوع",
            "topic_summary": "ملخص الموضوع", **changes}


def test_loader_requires_explicit_version_for_legacy_articles():
    with pytest.raises(ValueError, match="model_version"):
        prepare(article())
    result = prepare(article(), "legacy-unversioned")
    assert result["model_version"] == "legacy-unversioned"
    assert result["summary"] != result["topic_summary"]
    assert result["full_content"] == article()["Full_Content"]


def test_record_model_version_takes_priority():
    assert prepare(article(model_version="model-v2"), "legacy")["model_version"] == "model-v2"


def test_bad_dates_and_body_types_fail_before_database_load():
    with pytest.raises(ValueError):
        prepare(article(Date="31/2/2026"), "v1")
    with pytest.raises(ValueError, match="Full_Content"):
        prepare(article(Full_Content="not an array"), "v1")


def test_outlier_keeps_null_topic_metadata():
    result = prepare(article(topic_id=-1, topic_label=None, topic_summary=None), "v1")
    assert result["topic_id"] == -1
    assert result["topic_label"] is None
