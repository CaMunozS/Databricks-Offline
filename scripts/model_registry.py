"""Public Hugging Face model review helpers for staging downloads."""
from __future__ import annotations

from dataclasses import dataclass

from huggingface_hub import HfApi

APPROVED_LICENSES = {"apache-2.0", "mit", "bsd-2-clause", "bsd-3-clause"}


@dataclass(frozen=True)
class ReviewedModel:
    revision: str
    license: str
    pipeline_tag: str | None


def review_model(model_id: str, requested_revision: str | None) -> ReviewedModel:
    """Resolve an immutable revision and reject non-public or unclear licenses."""
    info = HfApi().model_info(model_id, revision=requested_revision)
    license_name = str((info.card_data or {}).get("license") or "").lower().strip()
    if info.gated or license_name not in APPROVED_LICENSES:
        raise ValueError("SKIPPED — LICENSE REVIEW REQUIRED")
    if not info.sha:
        raise ValueError("SKIPPED — LICENSE REVIEW REQUIRED: commit SHA no disponible")
    return ReviewedModel(revision=info.sha, license=license_name, pipeline_tag=info.pipeline_tag)
