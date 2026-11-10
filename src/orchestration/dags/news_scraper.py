from datetime import timedelta

import pendulum
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="news_scraper_hourly",
    start_date=pendulum.datetime(2026, 11, 5, tz="Africa/Cairo"),
    schedule="0 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["news", "scraping", "seaweedfs"],
) as dag:

    scrape_and_upload = BashOperator(
        task_id="scrape_and_upload",
        bash_command=(
            "/opt/scraper-venv/bin/python -u -m src.scraper.main"
        ),
        cwd="/opt/news-project",
        append_env=True,
        do_xcom_push=False,
    )
