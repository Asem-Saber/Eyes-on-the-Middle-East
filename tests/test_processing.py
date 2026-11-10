from src.processing.normalizer import normalize_text
from src.processing.pipeline import process_articles as run_processing


def process_articles(records):
    # Short fixtures isolate schema/deduplication behavior from length policy.
    return run_processing(records, min_words=1)


def article(**changes):
    return {"id": "one", "Link": "https://example.com/news", "Headline": "أخبار جديدة",
            "Full_Content": ["مُفاوضاتٌ في القاهرة."], "Published_At": "2026-11-08T10:00:00Z", **changes}


def test_normalization_preserves_original_and_is_idempotent():
    source = article()
    output = process_articles([source])["articles"][0]
    assert output["Full_Content"] == source["Full_Content"]
    normalized = normalize_text(output["Full_Content"][0])
    assert "في" not in normalized.split()
    assert "القاهره" in normalized
    assert normalize_text(normalized) == normalized
    assert output["Date"] == "8/11/2026"
    assert output["topic_id"] is None
    assert set(output) == {"id", "Link", "Headline", "Summary", "Full_Content",
                           "Publisher", "Topics", "Sources", "Date", "topic_id", "topic_label"}


def test_duplicate_content_and_ids_are_counted():
    result = process_articles([article(), article(id="two"), article(Full_Content=["نص مختلف"])])
    assert result["report"] == {"input": 3, "accepted": 1, "rejected": 0, "duplicates": 2}


def test_bad_records_do_not_block_valid_records():
    result = process_articles([None, article(Full_Content=[]), article(Published_At="Error"), article()])
    assert result["report"] == {"input": 4, "accepted": 1, "rejected": 3, "duplicates": 0}


def test_reprocessing_snapshot_is_deterministic():
    records = [article(), article(id="two", Full_Content=["خبر آخر"])]
    assert process_articles(records) == process_articles(records)


def test_requested_metadata_and_date_only_input():
    source = article(Published_At=None, Date="1/5/2026", Summary="ملخص",
                     Publisher="كاتب", Topics=["سياسة"], Sources=["الجزيرة"],
                     topic_id=17, topic_label="17_الصين")
    result = process_articles([source])["articles"][0]
    for field in ("Summary", "Publisher", "Topics", "Sources", "topic_id", "topic_label", "Date"):
        assert result[field] == source[field]


def test_normalized_duplicates_keep_readable_original():
    result = process_articles([article(), article(id="two", Full_Content=["مُفاوضاتٌ في القاهره"])])
    assert result["report"]["duplicates"] == 1
    assert result["articles"][0]["Full_Content"] == article()["Full_Content"]


def test_paragraph_cleanup_separates_summary_without_mutation():
    source = article(Summary="ملخص الخبر", Full_Content=[
        " ملخص  الخبر ", "", "  نص   المقال.  ", "نص المقال.", "فقرة ثانية!"])
    original = list(source["Full_Content"])
    result = process_articles([source])["articles"][0]
    assert result["Full_Content"] == ["نص المقال.", "فقرة ثانية!"]
    assert result["Summary"] == "ملخص الخبر"
    assert source["Full_Content"] == original


def test_quality_flags_short_non_arabic_and_error_pages():
    records = [article(), article(id="english", Full_Content=["English news content " * 20]),
               article(id="error", Full_Content=["403 Forbidden"]),
               article(id="valid", Full_Content=["هذا تقرير عربي عن تطورات الأحداث السياسية في المنطقة وأثرها على السكان والاقتصاد والمفاوضات الجارية بين الأطراف خلال الأيام الماضية."])]
    result = run_processing(records)
    assert [a["id"] for a in result["articles"]] == ["valid"]
    assert [r["reason"] for r in result["rejected"]] == [
        "article body below minimum word count",
        "article body below minimum Arabic letter ratio",
        "page error message in article body"]
    assert result["rejected"][0]["record"] == records[0]


def test_summary_only_body_is_quarantined():
    result = process_articles([article(Summary="ملخص فقط", Full_Content=["ملخص فقط"])])
    assert result["rejected"][0]["reason"] == "empty body after cleaning"


def test_error_phrase_inside_news_is_preserved():
    result = process_articles([article(Full_Content=["أعلنت الشركة ظهور رسالة Access denied لدى بعض المستخدمين."])])
    assert result["report"]["accepted"] == 1


def test_notebook_normalization_removes_links_mentions_digits_and_latin():
    text = "أخبار، في القاهرة https://example.com @someone #سياسة English 123 ١٢٣"
    assert normalize_text(text) == "اخبار القاهره سياسه"
    assert normalize_text(None) == ""


def test_notebook_normalization_unifies_letters_and_removes_stopwords():
    assert normalize_text("إلى على من في أخبار آفاق مدرسة فتى") == "الي علي اخبار افاق مدرسه فتي"
