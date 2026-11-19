# syntax=docker/dockerfile:1.7

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN install -d /opt/news-project /opt/uv-build

ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/ml-venv \
    PATH=/opt/ml-venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    UV_HTTP_TIMEOUT=300

COPY pyproject.toml uv.lock /opt/uv-build/

RUN --mount=type=cache,target=/root/.cache/uv \
    pip install --no-cache-dir uv \
    && uv sync \
    --project /opt/uv-build \
    --frozen --no-dev --group ml --no-install-project \
    && rm -rf /opt/uv-build

WORKDIR /opt/news-project
