"""Enrich articles, load staging and build the mart daily at midnight, Cairo."""
from datetime import timedelta

import pendulum
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="news_ml_processing_daily",
    start_date=pendulum.datetime(2026, 11, 14, tz="Africa/Cairo"),
    schedule="0 0 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["news", "ml", "llm", "seaweedfs", "warehouse", "dbt"],
) as dag:
    enrich_and_upload = BashOperator(
        task_id="enrich_and_upload",
        bash_command="/opt/scraper-venv/bin/python -u -m src.ml_service.processing",
        cwd="/opt/news-project",
        env={"ML_SERVICE_URL": "http://host.docker.internal:3000"},
        append_env=True,
        do_xcom_push=False,
    )

    load_staging = BashOperator(
        task_id="load_staging",
        # Legacy records lack model_version; record versions take priority.
        bash_command=(
            "/opt/warehouse-venv/bin/python -u -m src.modeling.load "
            "--model-version legacy-unversioned"
        ),
        cwd="/opt/news-project",
        append_env=True,
        do_xcom_push=False,
    )

    build_and_test_mart = BashOperator(
        task_id="build_and_test_mart",
        bash_command="/opt/warehouse-venv/bin/python -u -m src.modeling.dbt build",
        cwd="/opt/news-project",
        # Source is mounted read-only; dbt outputs use writable mounts.
        env={
            "DBT_LOG_PATH": "/opt/news-project/logs/dbt",
            "DBT_TARGET_PATH": "/opt/news-project/data/dbt/target",
        },
        append_env=True,
        do_xcom_push=False,
    )

    enrich_and_upload >> load_staging >> build_and_test_mart
