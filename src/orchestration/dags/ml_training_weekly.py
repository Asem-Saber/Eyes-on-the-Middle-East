import os
from datetime import timedelta

import pendulum
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import DAG
from docker.types import DeviceRequest, Mount

HOST_PROJECT_DIR = os.environ.get("HOST_PROJECT_DIR", "")
TRAINER_IMAGE = os.environ.get("ML_TRAINER_IMAGE", "ajnet-ml:latest")
HF_CACHE_DIR = os.environ.get("HF_CACHE_DIR", "")


def _mount(name: str, read_only: bool) -> Mount:
    return Mount(
        source=f"{HOST_PROJECT_DIR}/{name}",
        target=f"/opt/news-project/{name}",
        type="bind",
        read_only=read_only,
    )


def _mounts() -> list[Mount]:
    mounts = [
        _mount("src", read_only=True),
        _mount("config", read_only=True),
        _mount("data", read_only=False),
        _mount("models", read_only=False),
    ]
    if HF_CACHE_DIR:
        mounts.append(
            Mount(source=HF_CACHE_DIR, target="/root/.cache/huggingface", type="bind")
        )
    return mounts


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
    tags=["news", "ml", "training", "gpu"],
) as dag:
    train_topic_model = DockerOperator(
        task_id="train_topic_model",
        image=TRAINER_IMAGE,
        command="python -u -m src.ml_service.training",
        working_dir="/opt/news-project",
        docker_url="unix://var/run/docker.sock",
        mounts=_mounts(),
        environment={
            "PYTHONPATH": "/opt/news-project",
            "EMBED_DEVICE": "cuda",
            "TOPIC_MODEL_DIR": "/opt/news-project/models/news_topics_model",
        },
        device_requests=[DeviceRequest(count=-1, capabilities=[["gpu"]])],

        auto_remove="success",
        mount_tmp_dir=False,
        do_xcom_push=False,
    )