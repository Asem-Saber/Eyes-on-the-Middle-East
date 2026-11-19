"""Readable-text cleanup and configurable Arabic news quality checks."""
import re
import unicodedata


def clean_text(text: str) -> str:
    return " ".join(text.split())


def clean_paragraphs(paragraphs: list[str], summary: str) -> list[str]:
    # Compare readable copies: do not merge distinct Arabic spellings.
    summary = clean_text(summary)
    seen, result = set(), []
    for paragraph in paragraphs:
        paragraph = clean_text(paragraph)
        if not paragraph or paragraph in seen:
            continue
        if summary and summary != "No Summary" and paragraph == summary:
            continue
        seen.add(paragraph)
        result.append(paragraph)
    return result


def check_quality(paragraphs: list[str], min_words: int, min_arabic_ratio: float) -> None:
    text = " ".join(paragraphs)
    if not text:
        raise ValueError("empty body after cleaning")
    # Match standalone error messages, not phrases quoted inside news articles.
    error_messages = {
        "access denied", "forbidden", "403 forbidden", "404 not found",
        "internal server error", "service unavailable", "just a moment",
        "حدث خطأ", "الصفحة غير موجودة", "تعذر تحميل الصفحة",
    }
    if any(p.casefold().strip(" .!…") in error_messages for p in paragraphs):
        raise ValueError("page error message in article body")
    words = re.findall(r"[^\W_]+", text, flags=re.UNICODE)
    if len(words) < min_words:
        raise ValueError("article body below minimum word count")
    letters = [char for char in text if char.isalpha()]
    arabic_letters = sum("ARABIC" in unicodedata.name(char, "") for char in letters)
    if not letters or arabic_letters / len(letters) < min_arabic_ratio:
        raise ValueError("article body below minimum Arabic letter ratio")
