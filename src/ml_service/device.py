"""Select an embedding device without requiring a working CUDA driver."""
import logging

logger = logging.getLogger(__name__)


def resolve_device(requested: str | None) -> str | None:
    if requested is None or not requested.lower().startswith("cuda"):
        return requested
    import torch

    if not torch.cuda.is_available():
        logger.warning("Requested %s but CUDA is unavailable; using CPU instead", requested)
        return "cpu"
    return requested
