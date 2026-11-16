# Monthly Bronze to Silver processing

Publication dates determine partitions, not ingestion time. Published_At takes
priority over Date (D/M/YYYY); invalid dates go to undated/ for review.
Accepted article fields remain unchanged. Normalization and quality rules are
unchanged, including notebook-style Arabic matching and configurable thresholds.

## Storage

Local Bronze: data/raw/aljazeera/year=YYYY/month=MM/articles.json
SeaweedFS Bronze: news-raw/aljazeera/year=YYYY/month=MM/articles.json
Local Silver: data/processed/year=YYYY/month=MM/processed_articles.json
SeaweedFS Silver: news-processed/aljazeera/silver/year=YYYY/month=MM/processed_articles.json

Each Silver partition also contains rejected.json and report.json. Unknown dates
use undated/ instead of year/month. File names and article fields stay unchanged.

## Commands

Preview all local partitions without uploading:

```powershell
python -m src.processing.processing --input data/raw/aljazeera --local-only
```

Read all Bronze partitions from SeaweedFS and automatically publish Silver:

```powershell
python -m src.processing.processing
```

A local legacy JSON file can also be supplied through --input. Remote reads use
paginated S3 listings and fall back to the legacy aljazeera/articles.json only
when no monthly/undated objects exist. Local scraper state and ML training also
read monthly Bronze, falling back to the legacy local file when needed.

## Migration

Copy existing local Bronze into monthly files, retaining the legacy source:

```powershell
python -m src.datalake.migrate_partitions
```

To merge existing remote Bronze with local records and publish monthly Bronze:

```powershell
python -m src.datalake.migrate_partitions --upload
```

Raw writes merge by id (Link fallback) before partitioning, preserving existing
articles. Corrected dates leave an empty old partition, which full processing
also visits to clear stale Silver. Once monthly files exist they are authoritative;
old aggregate files are retained as backups and no longer read automatically.
Do not edit or continue writing the legacy aggregate after migration.

Processing currently performs a full rebuild, collecting raw records in memory
before grouping them. Cross-month duplicate detection shares ID/hash state;
partitions are processed in sorted order, first valid match wins. Incremental
change tracking/streaming is not implemented. Each JSON object is independently
replaced; there is no multi-object transaction or concurrent-writer locking.
Run a single writer at a time. The hourly news_scraper_hourly DAG runs process_and_upload only after scrape_and_upload succeeds. Both tasks inherit two retries with a five-minute delay. Processing rebuilds all available monthly partitions and publishes Silver automatically.

Accepted output omits Publisher, Topics and Sources, even when supplied in Bronze.
Rejected records retain the untouched original payload for review.


## Airflow

The DAG runs scrape_and_upload -> process_and_upload. Processing only cleans
and publishes Silver to news-processed; it does not invoke the ML/LLM service.
The existing BentoML service remains independently runnable as before.


## Separate ML/LLM processing

Start the unchanged service with:

```powershell
uv run bentoml serve src.ml_service.service:TopicService --port 3000
```

Then independently run:

```powershell
python -m src.ml_service.processing
```

This reads monthly processed_articles.json from news-processed (not raw articles),
calls /batch_infer and /label_topic, and publishes enriched_articles.json to
news-after-llm/aljazeera/year=YYYY/month=MM/. Local copies go to data/after_llm/.
Topic IDs and Arabic labels are populated and topic_summary is added; outliers
have topic -1 and null labels. Labels are reused across months within one run.
ML_SERVICE_URL defaults to http://localhost:3000, timeout to 600 seconds and
batch size to 64; overrides are read through config.py from config.yml.
The service must have a trained model and working LLM credentials. LLM labeling
sends keywords/headlines to the configured provider. Failures stop the job before
publishing the failed month's output; previously published months are retained.
Empty Silver partitions overwrite final output with [] without model requests.
The job does not execute preprocessing or training and is not added to Airflow.
