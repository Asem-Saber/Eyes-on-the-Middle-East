from __future__ import annotations

import logging
import re
from typing import Iterable, Sequence

import litellm

from src.config import (
    LLM_BASE_URL,
    LLM_MAX_HEADLINES,
    LLM_MAX_RETRIES,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
)
from src.schemas import TopicLabel, TopicSummary

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a professional Arabic news editor who classifies news topics.

You receive the keywords and the most representative headlines from a single
topic cluster. Write the editorial title describing what these stories share.

Rules:
- name_ar: a title in formal Modern Standard Arabic, 3 to 8 words, phrased as a
  noun phrase, with no trailing punctuation.
- summary: one Arabic sentence describing what the topic covers.
- Do not repeat the keywords verbatim — express the theme that unites them.
- If the headlines are unrelated, describe their broadest common thread.
- Never name a news outlet or wire agency in the title.

Return a JSON object with exactly these keys: name_ar, summary.

Example input:
    Keywords: غزة, هدنة, مفاوضات, القاهرة, وفد
    Headlines:
      1. وفد المفاوضات يصل إلى القاهرة لمناقشة بنود التهدئة
      2. محادثات مكثفة حول وقف إطلاق النار وتبادل الأسرى

Example output:
    {"name_ar": "مفاوضات التهدئة وتبادل الأسرى في غزة",
     "summary": "تغطية للمحادثات الدبلوماسية ومفاوضات التهدئة الجارية في القاهرة."}
"""

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class LLMError(RuntimeError):
    """The model could not be reached, or never returned a usable label."""


def _user_prompt(keywords: Sequence[str], headlines: Sequence[str]) -> str:
    listed = "\n".join(
        f"{i}. {h.strip()}" for i, h in enumerate(headlines[:LLM_MAX_HEADLINES], start=1)
    )
    return (
        f"Keywords: {', '.join(k.strip() for k in keywords if k.strip()) or '—'}\n\n"
        f"Headlines:\n{listed or '—'}"
    )


def _unfence(content: str) -> str:
    match = _JSON_FENCE.search(content or "")
    return match.group(1).strip() if match else (content or "").strip()


def label_topic(keywords: Sequence[str], headlines: Sequence[str]) -> TopicLabel:
    try:
        response = litellm.completion(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(keywords, headlines)},
            ],
            response_format=TopicLabel,
            temperature=LLM_TEMPERATURE,
            num_retries=LLM_MAX_RETRIES,
            timeout=LLM_TIMEOUT,
            api_base=LLM_BASE_URL,
        )
        return TopicLabel.model_validate_json(_unfence(response.choices[0].message.content))
    except Exception as exc:
        raise LLMError(f"Labeling failed via {LLM_MODEL}: {exc}") from exc


def label_topics(
    topics: Iterable[TopicSummary], *, skip_failures: bool = True
) -> dict[int, TopicLabel]:
    labels: dict[int, TopicLabel] = {}
    for topic in topics:
        try:
            labels[topic.topic_id] = label_topic(topic.keywords, topic.representative_docs)
        except LLMError as exc:
            if not skip_failures:
                raise
            logger.error("Skipping topic %d — %s", topic.topic_id, exc)
    return labels