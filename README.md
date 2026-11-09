# Eyes on the Middle East — v2

Arabic news intelligence over Al Jazeera (`ajnet.me`): scrape the politics feed,
cluster the articles into topics with BERTopic, and turn each cluster's keyword
soup into an editorial Arabic title with an LLM.

This is the v2 rebuild of a script-based prototype.

---

## Status

| Stage | State |
|---|---|
| **Scraper** — Selenium ingestion into `data/articles.json` | working |
| **Topic modeling** — BERTopic training, model artifacts + manifest | working |
| **LLM labeling** — litellm structured output, Arabic titles | working |
| **Serving** — BentoML `/batch_infer`, `/label_topic` | working |
| Bronze/Silver lakehouse (SeaweedFS) | In Progress |
| Airflow DAGs | In Progress |
| dbt warehouse, FastAPI, React dashboard | not started |

Current corpus: **5157 articles**, 2026-05-23 → 2026-11-09.
Current model: **85 topics** over 5,047 documents, 1,400 outliers, fitted in ~100s.

---

## Pipeline

```
ajnet.me/politics
      │  Selenium + BeautifulSoup
      ▼
data/articles.json          ← id, Link, Headline, Summary, Date, Full_Content, Published_At
      │  src/ml_service/training.py
      ▼
models/news_topics_model/   ← BERTopic weights (safetensors) + manifest.json
      │  src/ml_service/service.py
      ▼
BentoML  /batch_infer  →  topic_id, probability, keywords
         /label_topic  →  name_ar, summary
```

---

## Setup

Requires **Python ≥ 3.11**, [uv](https://docs.astral.sh/uv/), Chrome (for the
scraper), and an NVIDIA GPU for comfortable training (CPU works, slower).

```bash
uv sync --group ml
```

`torch` is pinned to PyTorch's own CUDA index in `pyproject.toml`
(`[tool.uv.sources]`), because the PyPI wheel is **CPU-only on Windows**. The
pin lives in the project rather than an install command on purpose: `uv run`
re-syncs to the lockfile before every command, so a hand-installed CUDA build
would be replaced before each training run.

Verify the GPU is actually being used:

```bash
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Expected: `2.6.0+cu124 True NVIDIA GeForce RTX 3060 Ti`. If `is_available()` is
`False`, the CPU wheel won — re-run `uv sync --group ml`.

### Credentials

Only the LLM labeler needs any. Create a gitignored `.env` in the project root:

```bash
OPENAI_API_KEY=sk-...
LLM_BASE_URL=https://openrouter.ai/api/v1   # only for OpenAI-compatible gateways
```

---

## Usage

### Scrape

```bash
uv run python -m src.scraper.scrape
```

Incremental and safe to re-run. It reads what is already stored, scrolls the
feed back only `rescan_buffer_hours`, and skips any article it already holds in
full — so an hourly run opens almost no article pages. A fetch that fails is
left incomplete on purpose, so the next run retries it rather than keeping a
stub forever.

### Train

```bash
uv run python -m src.ml_service.training
```

No arguments by design: everything comes from `config.yml`, so a scheduled
retrain and a manual one cannot diverge. It prints the topic table and writes
`models/news_topics_model/` plus a `manifest.json` recording the corpus size,
hyperparameters and timings that produced those weights.

Set `training.label_topics: true` to also generate Arabic titles into the
manifest.

### Serve

```bash
uv run bentoml serve src.ml_service.service:TopicService --port 3000
```

Ready in roughly 6 seconds. Open <http://localhost:3000> for the Swagger UI.

BentoML keys request bodies by **parameter name**:

```jsonc
// POST /batch_infer
{ "articles": [ { "id": "…", "Headline": "…", "Full_Content": ["…"], "Link": "…" } ] }

// POST /label_topic
{ "request": { "keywords": ["غزة", "هدنة"], "headlines": ["…"] } }
```

Responses:

```jsonc
// /batch_infer
[ { "article_id": "…", "topic_id": 30, "probability": 0.61,
    "keywords": ["الصحفيين", "غزة", "…"], "is_outlier": false } ]

// /label_topic
{ "name_ar": "تجدد الاشتباكات في اليمن",
  "summary": "تغطية للاشتباكات المتجددة بين القوات الحكومية والحوثيين في اليمن." }
```

Status codes worth knowing: **400** for an empty `label_topic` request, **424**
when a dependency is unconfigured — no trained model, or missing LLM
credentials. A 424 is a configuration problem, not a crash.

---

## Configuration

All of it lives in [`config/config.yml`](config/config.yml) and is exposed as
flat constants by `src/config.py`. There is no second settings system.

| Section | Covers |
|---|---|
| `paths` | where articles and logs are written |
| `scraper` | base URL, retries, scroll limits, politeness delays, rescan buffer |
| `ml_service` | embedding model, UMAP/HDBSCAN/vectorizer hyperparameters, device |
| `training` | corpus filters (`min_words`, `sections`) and whether to label |
| `llm` | litellm model string, temperature, retries, timeout |

A few values accept environment overrides for deployment: `CONFIG_PATH`,
`TOPIC_MODEL_DIR`, `EMBEDDING_MODEL`, `MIN_TOPIC_SIZE`, `EMBED_BATCH_SIZE`,
`EMBED_DEVICE`, `LLM_MODEL`, `LLM_BASE_URL`.

---

## Layout

```
config/config.yml          all configuration
src/
  config.py                the single config loader + setup_logging
  schemas.py               shared contracts (ArticleRecord, CorpusItem, Topic*)
  scraper/
    scrape.py              entry point; orchestrates a run
    driver.py              Chrome lifecycle as a context manager
    crawler.py             feed expansion via the "عرض المزيد" button
    extractor.py           listing and article-page parsing
    storage.py             atomic JSON writes
    utils.py               dates, ids, dedup, incremental helpers
  ml_service/
    bertopic_engine.py     build / fit / transform / save / load
    training.py            the weekly retrain entry point
    llm.py                 one litellm call with structured output
    artifacts.py           manifest beside the weights
    service.py             BentoML endpoints
    bentofile.yaml         image build (run from the repo root)
tests/                     21 tests, no browser or network needed
```