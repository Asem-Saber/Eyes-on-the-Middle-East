from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import (
    EMBEDDING_MODEL,
    MAX_SEQ_LENGTH,
    MIN_SAMPLES,
    MODEL_DIR,
    MODEL_NAME,
    N_COMPONENTS,
    N_NEIGHBORS,
    NR_TOPICS,
    SEED,
)
from src.schemas import TrainingReport

logger = logging.getLogger(__name__)

MANIFEST_NAME = "manifest.json"


def write_manifest(
    report: TrainingReport,
    model_dir: Path | str = MODEL_DIR,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Everything needed to decide whether this model is still the right one."""
    manifest: dict[str, Any] = {
        "model_name": MODEL_NAME,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "embedding_model": EMBEDDING_MODEL,
        "max_seq_length": MAX_SEQ_LENGTH,
        "n_neighbors": N_NEIGHBORS,
        "n_components": N_COMPONENTS,
        "min_samples": MIN_SAMPLES,
        "nr_topics": NR_TOPICS,
        "seed": SEED,
        "report": report.model_dump(),
    }
    if extra:
        manifest.update(extra)

    directory = Path(model_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / MANIFEST_NAME
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote manifest to %s", path)
    return path


def read_manifest(model_dir: Path | str = MODEL_DIR) -> dict[str, Any] | None:
    path = Path(model_dir) / MANIFEST_NAME
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.error("Manifest at %s is corrupt", path)
        return None