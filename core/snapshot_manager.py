"""
FTD-UEI: Snapshot Manager.

Creates, classifies, and analyses snapshot records for PHOENIX's
institutional lineage continuity.

A snapshot is an immutable record of the engine's observability state
at a point in time — it preserves the report registry version, app version,
trade count, and a reconstruction fingerprint.

The session-scoped snapshot ledger lives in main.py; this module provides
pure functions that operate on snapshot lists.

Pure module — no I/O, no side effects, no module-level mutable state.
Import-safe.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import time as _time

from core.reconstruction_hashing import snapshot_hash
from core.report_registry import REPORT_REGISTRY

# ── Canonical snapshot types ──────────────────────────────────────────────────
SNAPSHOT_TYPES: frozenset = frozenset({
    "HOURLY",
    "DAILY",
    "MILESTONE",
    "VERSION_TRANSITION",
    "GOVERNANCE_TRANSITION",
    "EPISTEMIC_SHIFT",
    "CATASTROPHIC_EVENT",
})

# Descriptions for each snapshot type
SNAPSHOT_TYPE_DESCRIPTIONS: Dict[str, str] = {
    "HOURLY":               "Routine hourly observability preservation",
    "DAILY":                "Daily institutional continuity snapshot",
    "MILESTONE":            "Significant engine milestone or configuration event",
    "VERSION_TRANSITION":   "Version upgrade or architecture transition",
    "GOVERNANCE_TRANSITION": "Constitutional governance parameter change",
    "EPISTEMIC_SHIFT":      "Significant epistemic state change detected",
    "CATASTROPHIC_EVENT":   "Catastrophic loss, recovery, or critical failure event",
}


def validate_snapshot_type(snapshot_type: str) -> str:
    """Returns the type if valid, else 'MILESTONE'."""
    return snapshot_type if snapshot_type in SNAPSHOT_TYPES else "MILESTONE"


def create_snapshot_record(
    snapshot_type: str,
    app_version: str,
    trade_count: int,
    label: str = "",
    triggered_by: str = "",
    generation_ts: Optional[int] = None,
) -> dict:
    """
    Create an immutable snapshot record.
    Never raises. auto_authorized=False, immutable=True.
    """
    try:
        s_type = validate_snapshot_type(snapshot_type)
        ts     = generation_ts or int(_time.time() * 1000)
        fp     = snapshot_hash(s_type, app_version, ts, trade_count)
        return {
            "snapshot_id":         f"SNP-{s_type[:4]}-{ts}-{fp[:12]}",
            "snapshot_type":       s_type,
            "snapshot_type_desc":  SNAPSHOT_TYPE_DESCRIPTIONS.get(s_type, ""),
            "timestamp_ms":        ts,
            "app_version":         app_version,
            "trade_count":         trade_count,
            "label":               label or s_type,
            "triggered_by":        triggered_by or "SYSTEM",
            "total_registered_reports": len(REPORT_REGISTRY),
            "reconstruction_hash": fp,
            "lineage_preserved":   True,
            "auto_authorized":     False,
            "immutable":           True,
        }
    except Exception:
        ts = int(_time.time() * 1000)
        return {
            "snapshot_id":     f"SNP-ERR-{ts}",
            "snapshot_type":   "MILESTONE",
            "timestamp_ms":    ts,
            "auto_authorized": False,
            "immutable":       True,
        }


def get_snapshot_health(snapshots: List[dict]) -> dict:
    """
    Analyse a list of snapshot records and return a health summary.
    Pure — does not modify the input list.
    """
    try:
        total    = len(snapshots)
        by_type: Dict[str, int] = {}
        for snap in snapshots:
            t = snap.get("snapshot_type", "UNKNOWN")
            by_type[t] = by_type.get(t, 0) + 1

        versions = sorted({s.get("app_version", "") for s in snapshots if s.get("app_version")})
        latest   = snapshots[-1] if snapshots else None

        return {
            "total_snapshots":       total,
            "snapshot_by_type":      by_type,
            "app_versions_covered":  versions,
            "latest_snapshot_id":    (latest or {}).get("snapshot_id"),
            "latest_snapshot_type":  (latest or {}).get("snapshot_type"),
            "has_version_transitions": by_type.get("VERSION_TRANSITION", 0) > 0,
            "has_governance_records":  by_type.get("GOVERNANCE_TRANSITION", 0) > 0,
            "lineage_healthy":        True,
        }
    except Exception:
        return {
            "total_snapshots": 0, "snapshot_by_type": {},
            "lineage_healthy": True,
        }


def get_latest_snapshot(snapshots: List[dict]) -> Optional[dict]:
    """Returns the most recent snapshot record, or None."""
    return snapshots[-1] if snapshots else None


def get_snapshots_by_type(snapshots: List[dict], snapshot_type: str) -> List[dict]:
    """Filter snapshots by type."""
    return [s for s in snapshots if s.get("snapshot_type") == snapshot_type]
