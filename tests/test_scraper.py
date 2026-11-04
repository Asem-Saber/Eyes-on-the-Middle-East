import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scraper.utils import (
    complete_links,
    deduplicate,
    extract_date,
    extract_iso_date,
    filter_by_date,
    generate_article_id,
    get_latest_scraped_date,
    parse_date,
    sort_articles_desc,
    to_display_date,
)
from src.scraper.extractor import (
    extract_body_paragraphs,
    parse_article_soup,
    parse_feed_items,
)
from src.scraper.storage import load_existing_articles, save_articles
from src.config import CONFIG, OUTPUT_FILE


# ---------------------------------------------------------------------------
# Existing behaviour (unchanged)
# ---------------------------------------------------------------------------

def test_article_id_generation():
    url1 = "https://www.ajnet.me/politics/2026/1/1/news-item"
    url2 = "https://www.ajnet.me/politics/2026/1/2/another-item"
    assert len(generate_article_id(url1)) == 12
    assert generate_article_id(url1) == generate_article_id(url1)
    assert generate_article_id(url1) != generate_article_id(url2)


def test_date_extraction_and_parsing():
    assert extract_date("نشر بتاريخ 15/03/2026 بتوقيت الدوحة") == "15/03/2026"
    assert extract_date("لا يوجد تاريخ هنا") == "No Date"
    assert extract_date("") == "No Date"

    parsed = parse_date("15/03/2026")
    assert parsed == datetime(2026, 3, 15)
    assert parse_date("No Date") is None
    assert parse_date("invalid-date") is None


def test_filter_and_sort_articles():
    articles = [
        {"id": "1", "Headline": "Article 1", "Date": "01/01/2026"},
        {"id": "2", "Headline": "Article 2", "Date": "10/02/2026"},
        {"id": "3", "Headline": "Article 3", "Date": "20/12/2025"},
        {"id": "4", "Headline": "Article 4", "Date": "No Date"},
    ]
    cutoff = datetime(2026, 1, 1)
    filtered = filter_by_date(articles, cutoff)
    assert {a["id"] for a in filtered} == {"1", "2", "4"}

    sorted_articles = sort_articles_desc(articles)
    assert sorted_articles[0]["id"] == "2"
    assert sorted_articles[1]["id"] == "1"


def test_latest_scraped_date_buffer():
    default_date = datetime(2026, 1, 1)
    articles = [{"Date": "10/03/2026"}]
    target = get_latest_scraped_date(articles, default_date)
    assert target == datetime(2026, 3, 9)


def test_latest_scraped_date_buffer_is_hour_based():
    """An hourly schedule wants a few hours of overlap, not a whole day."""
    default_date = datetime(2026, 1, 1)
    articles = [{"Published_At": "2026-03-10T18:00:00Z"}]
    assert get_latest_scraped_date(articles, default_date, 3) == datetime(2026, 3, 10, 15)
    # The configured start date is still a hard floor.
    assert get_latest_scraped_date(articles, datetime(2026, 4, 1), 3) == datetime(2026, 4, 1)


def test_atomic_storage_roundtrip(tmp_path: Path):
    test_file = tmp_path / "subfolder" / "test_articles.json"
    data = [{"id": "abc123", "Headline": "عنوان تجريبي باللغة العربية", "Date": "01/01/2026"}]

    save_articles(data, file_path=test_file)
    assert test_file.exists()
    assert not test_file.with_suffix(".tmp").exists()

    loaded = load_existing_articles(file_path=test_file)
    assert loaded == data
    assert loaded[0]["Headline"] == "عنوان تجريبي باللغة العربية"


def test_safe_url_joining():
    base = "https://www.ajnet.me"
    rel_path = "/politics/2026/test"
    abs_path = "https://www.ajnet.me/politics/2026/test"
    assert urljoin(base, rel_path) == "https://www.ajnet.me/politics/2026/test"
    assert urljoin(base, abs_path) == "https://www.ajnet.me/politics/2026/test"


def test_config_loaded():
    assert "paths" in CONFIG
    assert "scraper" in CONFIG
    assert OUTPUT_FILE.name == "articles.json"


# ---------------------------------------------------------------------------
# ISO dates — the article page's <time datetime> gives us these
# ---------------------------------------------------------------------------

def test_iso_date_parsing():
    assert parse_date("2026-11-04T10:22:36") == datetime(2026, 11, 4, 10, 22, 36)
    # A trailing Z must not break comparison, and must not make it tz-aware.
    assert parse_date("2026-11-04T10:22:36Z") == datetime(2026, 11, 4, 10, 22, 36)
    assert parse_date("2026-11-04") == datetime(2026, 11, 4)
    assert extract_iso_date("published 2026-11-04T10:22:36 GMT") == "2026-11-04T10:22:36"
    assert extract_iso_date("no date here") == "No Date"


def test_display_date_normalisation():
    assert to_display_date("2026-11-04T10:22:36Z") == "04/11/2026"
    assert to_display_date("04/11/2026") == "04/11/2026"
    assert to_display_date(datetime(2026, 11, 4)) == "04/11/2026"
    assert to_display_date("") == "No Date"


def test_sorting_prefers_precise_timestamp():
    """Two stories on the same day must order by time, not tie on the date."""
    articles = [
        {"id": "a", "Date": "04/11/2026", "Published_At": "2026-11-04T01:00:00Z"},
        {"id": "b", "Date": "04/11/2026", "Published_At": "2026-11-04T23:00:00Z"},
    ]
    assert [a["id"] for a in sort_articles_desc(articles)] == ["b", "a"]


def test_deduplicate_keeps_latest():
    articles = [
        {"id": "1", "Headline": "old"},
        {"id": "1", "Headline": "new"},
        {"id": "2", "Headline": "other"},
    ]
    merged = deduplicate(articles)
    assert len(merged) == 2
    assert next(a for a in merged if a["id"] == "1")["Headline"] == "new"


# ---------------------------------------------------------------------------
# Incremental runs — what keeps an hourly schedule cheap and self-healing
# ---------------------------------------------------------------------------

COMPLETE = {
    "id": "1",
    "Link": "https://www.ajnet.me/politics/2026/11/4/done",
    "Full_Content": ["نص المقال"],
    "Date": "04/11/2026",
    "Published_At": "2026-11-04T10:00:00Z",
}
STUB = {
    "id": "2",
    "Link": "https://www.ajnet.me/politics/2026/11/4/failed",
    "Full_Content": [],
    "Date": "Error",
}


def test_complete_links_skips_stubs():
    """A record left behind by a failed fetch must not count as 'already have it'."""
    assert complete_links([COMPLETE, STUB]) == {COMPLETE["Link"]}
    assert complete_links([]) == set()
    assert complete_links([{"Headline": "no link at all"}]) == set()


def test_refetched_stub_replaces_the_stub():
    """The feed re-offers the failed article; `deduplicate` keeps the good one."""
    existing = [COMPLETE, STUB]
    known = complete_links(existing)

    repaired = {**STUB, "Full_Content": ["النص بعد إعادة المحاولة"],
                "Date": "04/11/2026", "Published_At": "2026-11-04T11:00:00Z"}
    fresh = [a for a in [repaired] if a["Link"] not in known]
    assert fresh, "the stub's link must not be filtered out as already-known"

    merged = deduplicate(existing + fresh)
    assert len(merged) == 2
    assert next(a for a in merged if a["id"] == "2")["Full_Content"] == ["النص بعد إعادة المحاولة"]


# ---------------------------------------------------------------------------
# Listing page parsing — mirrors the live DOM as of 2026-11-04
# ---------------------------------------------------------------------------

LISTING_HTML = """
<main>
  <article data-homepage-story-href="/politics/2026/11/4/hero-slug"
           data-card-type="large" data-media="video">
    <h3>عنوان البطاقة الرئيسية</h3>
    <p>ملخص البطاقة الرئيسية</p>
    <time data-homepage-article-date datetime="2026-11-04T13:17:06"><bdi>4/11/2026</bdi></time>
  </article>

  <div data-card-type="feed">
    <ul aria-busy="false">
      <li tabindex="-1">
        <a href="/politics/2026/11/4/row-one">
          <div><img src="/wp-content/uploads/2026/11/a.jpg?resize=170%2C113"></div>
          <div>
            <h3>عنوان الخبر الأول</h3>
            <p>ملخص الخبر الأول</p>
            <span data-homepage-article-date>4/11/2026</span>
          </div>
        </a>
      </li>
      <li tabindex="-1">
        <a href="/politics/2026/11/3/row-two">
          <div>
            <h3>عنوان الخبر الثاني</h3>
            <p>ملخص الخبر الثاني</p>
            <span data-homepage-article-date>3/11/2026</span>
          </div>
        </a>
      </li>
      <!-- the hero story also appears here; the feed row is how we pick it up -->
      <li tabindex="-1">
        <a href="/politics/2026/11/4/hero-slug">
          <div>
            <h3>عنوان البطاقة الرئيسية</h3>
            <p>ملخص مكرر</p>
            <span data-homepage-article-date>4/11/2026</span>
          </div>
        </a>
      </li>
    </ul>
  </div>
</main>
"""


def test_parse_feed_items():
    items = parse_feed_items(BeautifulSoup(LISTING_HTML, "html.parser"))

    # Only the main feed is scraped — the 3 rows, in DOM order.
    assert len(items) == 3
    assert [i["Link"] for i in items] == [
        "https://www.ajnet.me/politics/2026/11/4/row-one",
        "https://www.ajnet.me/politics/2026/11/3/row-two",
        "https://www.ajnet.me/politics/2026/11/4/hero-slug",
    ]

    row_one, row_two, hero_row = items
    assert row_one["Headline"] == "عنوان الخبر الأول"
    assert row_one["Summary"] == "ملخص الخبر الأول"
    assert row_one["Date"] == "04/11/2026"           # from the day-first span
    assert row_two["Date"] == "03/11/2026"
    assert hero_row["Headline"] == "عنوان البطاقة الرئيسية"
    assert len(row_one["id"]) == 12


def test_hero_card_is_not_scraped():
    """The hero/carousel strip is out of scope — only the feed container is read."""
    html = """
    <main>
      <article data-homepage-story-href="/politics/2026/11/4/hero-slug"
               data-card-type="large" data-media="video">
        <h3>عنوان البطاقة الرئيسية</h3>
        <p>ملخص البطاقة الرئيسية</p>
        <time data-homepage-article-date datetime="2026-11-04T13:17:06"><bdi>4/11/2026</bdi></time>
      </article>
    </main>
    """
    assert parse_feed_items(BeautifulSoup(html, "html.parser")) == []


def test_parse_feed_items_handles_missing_pieces():
    html = """
    <div data-card-type="feed">
      <ul aria-busy="false">
        <li><a href="/politics/2026/11/4/bare"></a></li>
      </ul>
    </div>
    """
    items = parse_feed_items(BeautifulSoup(html, "html.parser"))
    assert items[0]["Headline"] == "No Headline"
    assert items[0]["Summary"] == "No Summary"
    assert items[0]["Date"] == "No Date"


# ---------------------------------------------------------------------------
# Article page parsing
# ---------------------------------------------------------------------------

ARTICLE_HTML = """
<main>
  <div data-testid="article-featured-area">
    <header>
      <div><div>
        <ul><li><a href="/politics">سياسة</a></li><li><a href="/where/palestine/">فلسطين</a></li></ul>
      </div>
      <h1>عنوان المقال</h1></div>
    </header>
    <div><span><time datetime="2026-11-04T10:22:36Z">4 نوفمبر 2026</time></span></div>
    <figure><figcaption><p><span>تعليق الصورة</span></p></figcaption></figure>
  </div>

  <article>
    <div class="wysiwyg wysiwyg--all-content">
      <p>الفقرة الأولى</p>
      <blockquote class="twitter-tweet"><p>نص تغريدة مضمّنة</p></blockquote>
      <h2>عنوان فرعي</h2>
      <p>الفقرة الثانية</p>
      <div class="suggested"><h3>أخبار مقترحة</h3><p>عنوان خبر مقترح</p></div>
      <aside><p>تابع تطورات هذا الموضوع</p></aside>
      <p>الفقرة الثالثة</p>
    </div>
    <div><div class="text-body-lg text-text-primary">المصدر: الجزيرة</div></div>
  </article>
</main>
"""


def test_parse_article_soup():
    result = parse_article_soup(BeautifulSoup(ARTICLE_HTML, "html.parser"))

    assert result["Published_At"] == "2026-11-04T10:22:36Z"
    assert result["Date"] == "04/11/2026"


def test_dropped_fields_are_not_collected():
    """Topics, Sources and Publisher are all still in the DOM — we skip all three."""
    result = parse_article_soup(BeautifulSoup(ARTICLE_HTML, "html.parser"))
    assert set(result) == {"Full_Content", "Date", "Published_At"}


def test_article_body_excludes_injected_widgets():
    """The suggested-news block, tweet embeds and the promo aside all carry
    their own <p> tags — none of them belong in the article text."""
    result = parse_article_soup(BeautifulSoup(ARTICLE_HTML, "html.parser"))
    assert result["Full_Content"] == ["الفقرة الأولى", "الفقرة الثانية", "الفقرة الثالثة"]


def test_extract_body_paragraphs_on_empty_body():
    assert extract_body_paragraphs(None) == []
    assert extract_body_paragraphs(BeautifulSoup("<div></div>", "html.parser").div) == []
