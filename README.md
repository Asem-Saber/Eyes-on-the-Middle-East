# Eyes on the Middle East — v2

An Arabic news analytics pipeline: scrape Al Jazeera, clean and partition articles
in SeaweedFS, enrich them with BERTopic and LLM topic labels, then build a
PostgreSQL warehouse with dbt for Power BI reporting.

## Current implementation

| Component | Implemented behavior |
|---|---|
| Ingestion | Python, Selenium and BeautifulSoup; incremental scraping and JSON persistence |
| Data lake | SeaweedFS S3 buckets for raw, processed and enriched articles |
| Processing | Arabic normalization for matching, whitespace cleanup, deduplication and quality checks |
| Topic modeling | BERTopic training, saved model artifacts and training manifest |
| Serving | Separate BentoML service: `/batch_infer` and `/label_topic` |
| Enrichment | Topic assignment, Arabic topic labels and topic summaries |
| Warehouse | Python staging upserts, PostgreSQL star schema and dbt tests |
| Orchestration | Hourly ingestion/processing, daily enrichment/warehouse, weekly training |
| Reporting | Mart tables ready for Power BI; dashboards are a separate reporting step |

Corpus sizes and topic counts depend on the current data and model, rather than
being fixed project specifications.

## Architecture

```text
Al Jazeera → Python scraper → SeaweedFS: news-raw
                                      ↓
                              Python processing
                                      ↓
                            SeaweedFS: news-processed
                                      ↓
                           ML enrichment job ↔ BentoML HTTP API
                                      │          ├─ BERTopic inference
                                      │          └─ LLM topic labeling
                                      ↓
                            SeaweedFS: news-after-llm
                                      ↓
                               Python loader
                                      ↓
                          PostgreSQL staging schema
                                      ↓
                               dbt build + tests
                                      ↓
                           PostgreSQL mart schema
                                      ↓
                             Power BI reporting

Local Bronze → weekly BERTopic training → model artifacts → BentoML startup
```

Docker Compose runs **Airflow, SeaweedFS and PostgreSQL**. BentoML runs separately
on the host; Airflow calls it through `host.docker.internal:3000`. Restart the
service to load newly trained model artifacts.

## Setup

Requirements: Python 3.11+, [uv](https://docs.astral.sh/uv/), Docker Desktop with
Compose, and Chrome/Chromium for local scraping. The Airflow image includes
Chromium and its driver. GPU execution is optional; CPU execution is supported.

Run commands from the repository root:

```powershell
uv sync --locked --group ml --group warehouse --group dev
```

Application settings and credentials live in `config/config.yml` and are read
through `src/config.py`. Configure scraping, model/training options, LLM access,
SeaweedFS credentials and the `warehouse` connection there. Deployment environment
variables can override YAML values. Application code does not load `.env`.

Keep populated configuration private. A fresh checkout needs a valid local YAML
configuration before running; a redacted `config.example.yml` is not currently
included in the repository.

Use the Compose wrapper to pass YAML settings to Docker:

```powershell
uv run python scripts/compose.py up -d --build
uv run python -m src.datalake.init_storage
```

The second command creates or verifies all three storage buckets. Rebuild Airflow
when its Dockerfile or dependencies change. Source files and DAGs are mounted
from the working tree.

| Service | Host address |
|---|---|
| Airflow UI | http://localhost:8081 |
| SeaweedFS S3 API | http://localhost:8333 |
| SeaweedFS filer | http://localhost:8888 |
| SeaweedFS master | http://localhost:9333 |
| PostgreSQL | `localhost:5433`, database `news_dwh` |
| BentoML, started separately | http://localhost:3000 |

Database credentials in the warehouse configuration must match PostgreSQL.
Changing Compose credentials does not reset an account in an existing volume.

## Run manually

### Scrape and clean

```powershell
uv run python -m src.scraper.scrape
uv run python -m src.processing.processing
```

Scraping merges existing records and writes monthly Bronze partitions. Processing
reads Bronze from SeaweedFS by default and automatically publishes Silver. To
preview local input without uploading:

```powershell
uv run python -m src.processing.processing --input data/raw/aljazeera --local-only
```

Processing removes blank/duplicate paragraphs, cleans whitespace, deduplicates
articles and applies quality checks. Notebook-derived Arabic normalization is
used internally for matching; accepted text remains readable. Accepted output
omits `Publisher`, `Topics` and `Sources`. Rejected records retain their original
payloads for review.

### Train and serve

```powershell
uv run python -m src.ml_service.training
uv run bentoml serve src.ml_service.service:TopicService --host 0.0.0.0 --port 3000
```

Training writes `models/news_topics_model/` and a manifest. Leave BentoML running
in a separate terminal. LLM labeling requires provider credentials and sends
keywords/selected headlines to the configured provider.

The ML group uses the configured PyTorch CUDA 12.4 index. CUDA requires compatible
hardware and drivers; requested CUDA falls back to CPU when PyTorch reports it
unavailable. Check availability without assuming a GPU exists:

```powershell
uv run python -c "import torch; print(torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```

BentoML requests use parameter names as outer JSON keys:

```jsonc
// POST /batch_infer
{"articles": [{"id": "article-id", "Headline": "عنوان الخبر", "Full_Content": ["نص الخبر"], "Link": "https://www.ajnet.me/..."}]}

// POST /label_topic
{"request": {"keywords": ["غزة", "هدنة"], "headlines": ["عنوان الخبر"]}}
```

### Enrich

```powershell
uv run python -m src.ml_service.processing
```

This independent job reads `news-processed`, calls BentoML and writes enriched
articles to `news-after-llm`, with local copies under `data/after_llm/`. It fills
`topic_id` and `topic_label`, and adds `topic_summary`. Outliers use topic `-1`
and null labels/summaries. It does not run preprocessing or training.

### Load and build the warehouse

```powershell
uv run python -m src.modeling.load --model-version legacy-unversioned
uv run python -m src.modeling.dbt debug
uv run python -m src.modeling.dbt build
```

To load local enriched files instead of SeaweedFS:

```powershell
uv run python -m src.modeling.load --input data/after_llm --model-version legacy-unversioned
```

The Python loader upserts `staging.enriched_articles` by article ID. Unchanged
payloads retain their timestamps. The config-aware dbt wrapper builds:

| Relation | Purpose |
|---|---|
| `staging.stg_enriched_articles` | Prepare dates, keys, sources and measures |
| `mart.fct_articles` | One row per article, current classification, word/paragraph counts and provenance |
| `mart.dim_article` | Article ID, URL, headline, summary and paragraphs |
| `mart.dim_date` | Calendar attributes |
| `mart.dim_source` | Source name and domain |
| `mart.dim_topic` | Model-scoped topics, labels, summaries and outlier flag |

The mart tables are fully rebuilt by dbt. Relationships are checked with data
tests rather than physical foreign-key constraints. See the
[warehouse guide](src/modeling/README.md) for loading rules and dbt editor setup.

## Airflow workflows

All schedules use **Africa/Cairo**. Catchup is disabled and each DAG permits one
active run. Tasks retry twice. New DAGs are paused by default; enable them in
Airflow after configuring services, buckets and the model service.

| DAG | Schedule | Tasks |
|---|---|---|
| `news_scraper_hourly` | Every hour | `scrape_and_upload → process_and_upload` |
| `news_ml_processing_daily` | Daily at 00:00 | `enrich_and_upload → load_staging → build_and_test_mart` |
| `news_ml_training_weekly` | Sunday at 00:00 | `train_topic_model` |

The standalone `news_dwh_twice_daily` DAG has been removed. Modeling follows
successful daily enrichment. dbt writes logs and targets to the writable
`logs/dbt` and `data/dbt/target` mounts because `src` is mounted read-only.

Weekly training and daily enrichment are independent and can overlap on Sunday;
there is no automatic cross-DAG model handoff or service restart.

## Storage

Publication dates determine partitions. New month/year prefixes are created
automatically; missing or invalid dates use `undated/`.

| Layer | SeaweedFS object path | Local root |
|---|---|---|
| Raw | `news-raw/aljazeera/year=YYYY/month=MM/articles.json` | `data/raw/aljazeera/` |
| Processed | `news-processed/aljazeera/silver/year=YYYY/month=MM/processed_articles.json` | `data/processed/` |
| Enriched | `news-after-llm/aljazeera/year=YYYY/month=MM/enriched_articles.json` | `data/after_llm/` |

Silver also includes `rejected.json` and `report.json`. Monthly partitions take
precedence over legacy aggregate files. See the
[processing guide](src/processing/README.md) for migration commands and details.

## Power BI

In Power BI Desktop select **Get Data → PostgreSQL database**, server
`localhost:5433`, database `news_dwh`, and the configured database credentials.
Import the five `mart` tables. Join dimension keys to their fact keys;
`dim_date.date_key` joins to `fct_articles.published_date_key`.

The mart supports publishing volume, topic coverage/trends, period comparisons,
article length and unclassified-article reporting. It measures news coverage,
not audience engagement. Only Al Jazeera is currently ingested. Power BI Service
refresh against the local database requires an on-premises data gateway.

## Project layout

```text
config/config.yml              Application settings and credentials
scripts/                       Compose wrapper and dbt editor setup
src/
  config.py                    YAML loader and deployment overrides
  schemas.py                   Shared article/topic contracts
  scraper/                     Crawling, extraction and persistence
  datalake/                    Bucket initialization, partitions and migration
  processing/                  Cleaning, Arabic matching and quality checks
  ml_service/                  Training, BentoML serving and enrichment
  modeling/
    load.py                    SeaweedFS/local JSON → staging
    dbt.py                     Config-aware dbt launcher
    models/staging/            Source declarations and staging view
    models/marts/              Fact and dimension models
    macros/                    Schema naming and stable keys
    tests/                     Warehouse SQL tests
  orchestration/dags/           Three Airflow workflows
  infrastructure/docker/       Airflow image and isolated Python environments
tests/                         Python tests
data/                          Local snapshots and generated dbt artifacts
models/                        Trained model artifacts
logs/                          Application and dbt logs
```

## Validation and limitations

```powershell
uv run pytest -q
uv run python -m src.modeling.dbt build
```

Python tests cover available scraper/loader behavior. dbt tests cover keys,
relationships, topic identity, row counts and measures; they require a reachable
database and loaded staging data.

- Processing rebuilds the available corpus in memory. JSON writes are atomic per
  object, without multi-object transactions or concurrent-writer locking.
- The warehouse stores the latest article state rather than classification history.
- Enriched outputs currently lack a verified `model_version`. The explicit
  `legacy-unversioned` fallback is not an actual training version. Topic IDs from
  different model training runs cannot be safely equated.
- Training does not automatically reload the running BentoML service.
- Scheduled execution depends on running infrastructure and valid configuration;
  workflow definitions alone do not guarantee successful runs.
