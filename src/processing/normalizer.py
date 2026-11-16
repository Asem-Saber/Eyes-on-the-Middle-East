"""Normalization adapted from aljazeera_EDA.ipynb, cell 23."""
import re
from pathlib import Path
from string import punctuation

# Vendored NLTK Arabic corpus: no network/data downloads during processing.
STOP_WORDS = frozenset(
    Path(__file__).with_name("arabic_stopwords.txt").read_text(encoding="utf-8").splitlines()
)


def normalize_text(text: str) -> str:
    """Notebook-style NLP copy; readable article fields remain unchanged.

    Fixes the notebook's unused `txt` digit-removal assignment. After URLs,
    non-Arabic text and punctuation are removed/spaced, whitespace tokenization
    avoids NLTK's English sentence-tokenizer dependency for this Arabic stream.
    Like the notebook, this does not explicitly strip Arabic diacritics.
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\@\w+|\#", "", text)
    text = re.sub(r"\d", " ", text)
    text = re.sub(r"[،؛؟٪٫٬ـ]", " ", text)
    text = re.sub(r"[^\s\u0600-\u06FF]", " ", text)
    text = re.sub(r"([^\w\s])", r" \1 ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = text.replace("ة", "ه").replace("ى", "ي")
    return " ".join(word for word in text.split()
                    if word not in punctuation and word not in STOP_WORDS)
