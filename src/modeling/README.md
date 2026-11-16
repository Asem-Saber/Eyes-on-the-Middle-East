# News DWH: PostgreSQL staging -> dbt mart

All dbt models are under src/modeling/models/. The existing news-postgres
Compose service exposes PostgreSQL 16 on localhost:5433 (container port 5432).
Connection values live in config/config.yml under warehouse, read through
src/config.py. Optional DWH_HOST/PORT/DATABASE/USER/PASSWORD overrides are resolved
there too. The password must match the existing PostgreSQL volume's credentials;
changing a Compose password does not reset an existing database account.

## Setup and run

```powershell
uv sync --locked --group warehouse --group dev --inexact
python scripts/compose.py up -d news-postgres
```

Load from news-after-llm in SeaweedFS:

```powershell
python -m src.modeling.load --model-version legacy-unversioned
```

Or load the existing local enriched files:

```powershell
python -m src.modeling.load --input data/after_llm --model-version legacy-unversioned
```

Then build and test the warehouse:

```powershell
python -m src.modeling.dbt debug
python -m src.modeling.dbt build
```

The wrapper uses the dbt executable in the active Python environment, reads
credentials from config.py, and passes them to the child process without writing
secrets to profiles.yml. Direct dbt commands require the corresponding DBT_*
variables; the wrapper supplies them. To inspect schema lineage:

```powershell
python -m src.modeling.dbt docs generate
```

## Relations

- staging.enriched_articles: Python-owned ingestion table, one row per article_id.
- staging.stg_enriched_articles: dbt view, parses date, prepares source/keys/measures.
- mart.dim_article: article ID, URL, headline, article summary, JSONB paragraphs.
- mart.dim_date: continuous calendar spanning the publication dates.
- mart.dim_source: source name and normalized domain.
- mart.dim_topic: model-scoped topics, topic label/summary, outlier flag.
- mart.fct_articles: one row per article with the latest classification and measures.

Exact staging and mart schema names are configured by generate_schema_name.
This single-user project intentionally omits dbt's usual target-schema prefix;
use separate databases or customize the macro before sharing development targets.
Stable BIGINT keys are derived from 60 bits of MD5; unique tests detect collisions.
There are no fact-to-fact relationships. Relationships are verified by dbt tests,
not physical foreign-key constraints in dbt-generated tables.

## Loading rules and limits

Each object is validated before writing, then loaded in a transaction. Repeated
article IDs across files upsert the current state; duplicate IDs within one file
are rejected. Invalid dates, invalid paragraph arrays, missing IDs, or missing
model versions fail that file without partial writes. Previous objects already
committed remain loaded. Empty input files never delete warehouse articles.

Unchanged payloads do not update timestamps; first loaded_at is retained and
updated_at changes for modified content/source paths. The batch UUID and source
object path provide row provenance. This is a latest-state store, not change
history. dbt tables are fully rebuilt initially; incremental marts are not needed
yet. Reclassification changes historic article counts by topic.

Current enriched files do not contain model_version. --model-version is a required
explicit fallback for them; legacy-unversioned identifies an unknown legacy
namespace, not a verified training version. It cannot distinguish different old
models. New outputs must carry the actual model version before weekly models can
be safely combined. Do not infer the model version from article publication dates.
The service/training files are unchanged in this implementation.

Topic titles can vary across LLM runs. dim_topic picks the most recently updated
staging row per model/topic, breaking ties by article_id. This gives deterministic
results; editorial approval/history is not implemented. Topic -1 is retained as
غير مصنف. day_of_week uses ISO Monday=1; iso_week is paired with iso_year.

## Tests

`dbt build` tests unique and non-null keys, source article IDs, all four fact
relationships, topic version/ID uniqueness, row-count reconciliation and measures.
Python tests validate loader field/date/version handling. Airflow runs
news_ml_processing_daily at 00:00 Africa/Cairo:
enrich_and_upload -> load_staging -> build_and_test_mart. Tasks inherit two
retries five minutes apart; each task requires its upstream task to succeed.
Catchup is disabled and only one run may be active. The warehouse loader consumes
the news-after-llm objects after enrichment completes. Weekly training remains a
separate DAG; the former news_dwh_twice_daily DAG has been removed.

Rebuild Airflow after adding the isolated warehouse environment:

```powershell
python scripts/compose.py up -d --build airflow
```

Enable news_ml_processing_daily in Airflow. It uses /opt/warehouse-venv for dbt and
psycopg, and DWH_HOST=news-postgres/DWH_PORT=5432 inside the Compose network.
The explicit legacy-unversioned fallback matches the initial data load; it must
not be mistaken for a verified model identity. Source model_version takes priority.
The daily schedule is based on local wall time; DST changes may change elapsed
hours between scheduled runs.


## VS Code / dbt Power User

Open the repository normally after the one-time project-venv setup:

```powershell
.\.venv\Scripts\python.exe scripts/setup_dbt_editor.py
```

This installs news_dwh_editor.pth in this .venv only. New Python processes in the
venv load src.modeling.editor_env, which resolves dbt connection variables via
config.py without copying credentials to disk or changing Windows user variables.
It also works for the pythonw interpreter used by dbt Power User. Existing DBT_*
process overrides are preserved; DBT_CONFIG_AUTOLOAD=0 opts out.

Select dbt Power User with Core integration and disable the dbt Labs extension
for this workspace, since its separate engine does not use this Python startup.
Reload VS Code once after setup; subsequent normal folder opens work without a
launcher. Repeat setup only if .venv is deleted/recreated. Connection edits are
picked up by new Python processes; reload the editor to refresh persistent ones.
scripts/vscode.py remains optional for launching an explicitly configured session.
