"""Retrain topics every Sunday at midnight, Africa/Cairo."""
from datetime import timedelta

import pendulum
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="news_ml_training_weekly",
    start_date=pendulum.datetime(2026, 11, 14, tz="Africa/Cairo"),
    schedule="0 0 * * 0",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=10),
    },
    tags=["news", "ml", "training"],
) as dag:
    train_topic_model = BashOperator(
        task_id="train_topic_model",
        bash_command="/opt/ml-venv/bin/python -u -m src.ml_service.training",
        cwd="/opt/news-project",
        env={
            "EMBED_DEVICE": "cpu",
            "TOPIC_MODEL_DIR": "/opt/news-project/models/news_topics_model",
        },
        append_env=True,
        do_xcom_push=False,
    )

