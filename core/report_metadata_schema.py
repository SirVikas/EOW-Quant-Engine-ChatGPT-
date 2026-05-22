"""
FTD-RTAG: Unified Report Metadata Schema.

Defines the canonical metadata standard that EVERY PHOENIX report export
must include — enabling forensic reconstruction, archive continuity, and
AI-assisted long-horizon analysis.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Dict, List, Tuple

SCHEMA_VERSION = "1.0"

# Every export MUST carry these fields.
REQUIRED_METADATA_FIELDS: Tuple[str, ...] = (
    "report_id",
    "report_family",
    "app_version",
    "doctrine_version",
    "generation_ts",
    "evidence_window",
    "lineage_epoch",
    "constitutional_flags",
    "reconstruction_hash",
    "replay_lineage_id",
    "export_bundle_type",
)

# Recommended additional fields for full institutional archivability.
RECOMMENDED_METADATA_FIELDS: Tuple[str, ...] = (
    "schema_version",
    "export_format",
    "archive_priority",
    "human_review_required",
)


def generate_metadata(
    report_id: str,
    report_family: str,
    app_version: str,
    doctrine_version: str,
    trade_count: int,
    export_bundle_type: str = "STANDALONE",
    lineage_epoch: str = "CURRENT",
    replay_lineage_id: str = "",
    constitutional_flags: Dict | None = None,
    human_review_required: bool = True,
) -> dict:
    """
    Generate a canonical metadata block for any report export.
    reconstruction_hash is derived from (report_id, family, ts, trade_count)
    so it uniquely fingerprints the export event.
    """
    ts = int(_time.time() * 1000)
    payload = f"{report_id}|{report_family}|{ts}|{trade_count}"
    reconstruction_hash = hashlib.sha256(payload.encode()).hexdigest()
    return {
        "report_id":            report_id,
        "report_family":        report_family,
        "app_version":          app_version,
        "doctrine_version":     doctrine_version,
        "generation_ts":        ts,
        "evidence_window":      trade_count,
        "lineage_epoch":        lineage_epoch,
        "constitutional_flags": constitutional_flags or {},
        "reconstruction_hash":  reconstruction_hash,
        "replay_lineage_id":    replay_lineage_id or f"RPL-{ts}",
        "export_bundle_type":   export_bundle_type,
        "schema_version":       SCHEMA_VERSION,
        "human_review_required": human_review_required,
    }


def validate_metadata(meta: dict) -> Tuple[bool, List[str]]:
    """
    Validate that a metadata dict satisfies the required schema.
    Returns (is_valid, list_of_missing_fields).
    """
    if not isinstance(meta, dict):
        return False, list(REQUIRED_METADATA_FIELDS)
    missing = [f for f in REQUIRED_METADATA_FIELDS if f not in meta]
    return (len(missing) == 0, missing)


def compliance_score(meta: dict) -> float:
    """
    0.0–100.0 compliance score: fraction of required fields present × 100.
    """
    if not isinstance(meta, dict) or not meta:
        return 0.0
    present = sum(1 for f in REQUIRED_METADATA_FIELDS if f in meta)
    return round(present / len(REQUIRED_METADATA_FIELDS) * 100.0, 2)
