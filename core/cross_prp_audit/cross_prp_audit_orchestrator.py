"""
PRP-PHASEB Master Orchestrator — Cross-PRP Wiring Audit.

Runs all 6 Phase-B auditors and computes a composite wiring health score.
Each auditor is individually wrapped so one failure does not abort the rest.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import hashlib
import json
import time as _time
from typing import Any, Dict, List


# ── Scoring weights (must sum to 1.0) ────────────────────────────────────────
_WEIGHTS: Dict[str, float] = {
    "constitution_score":          0.20,
    "propagation_score":           0.25,
    "dependency_score":            0.20,
    "archive_score":               0.15,
    "rendering_score":             0.10,
    "compression_readiness_score": 0.10,
}


def _score_tier(score: int) -> str:
    if score >= 80:
        return "HEALTHY"
    if score >= 60:
        return "ADEQUATE"
    if score >= 40:
        return "WEAK"
    return "CRITICAL"


def _make_audit_id(ts_ms: int, payload: str) -> str:
    digest = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()
    return f"AUDIT-{ts_ms}-{digest[:16]}"


def run_full_wiring_audit() -> dict:
    """
    Execute all 6 Phase-B auditors and aggregate results into a single
    composite wiring health report.

    Weighting:
      constitution 20%, propagation 25%, dependency 20%,
      archive 15%, rendering 10%, compression 10%.

    Returns a self-contained dict; never raises.
    """
    ts_ms: int = int(_time.time() * 1000)
    domain_reports: Dict[str, Any] = {}
    scores: Dict[str, int] = {k: 0 for k in _WEIGHTS}
    auditor_errors: List[str] = []

    # ── Auditor 1: Endpoint Constitution ─────────────────────────────────────
    try:
        from core.cross_prp_audit.endpoint_constitution_auditor import (  # lazy
            audit_endpoint_constitution,
        )
        result = audit_endpoint_constitution()
        domain_reports["constitution"] = result
        scores["constitution_score"] = result.get("constitution_score", 0)
    except Exception as exc:
        auditor_errors.append(f"constitution: {exc}")
        domain_reports["constitution"] = {"error": str(exc), "constitution_score": 0}

    # ── Auditor 2: Report Propagation ─────────────────────────────────────────
    try:
        from core.cross_prp_audit.report_propagation_auditor import (  # lazy
            audit_report_propagation,
        )
        result = audit_report_propagation()
        domain_reports["propagation"] = result
        scores["propagation_score"] = result.get("propagation_score", 0)
    except Exception as exc:
        auditor_errors.append(f"propagation: {exc}")
        domain_reports["propagation"] = {"error": str(exc), "propagation_score": 0}

    # ── Auditor 3: Dependency Survivability ───────────────────────────────────
    try:
        from core.cross_prp_audit.dependency_survivability_auditor import (  # lazy
            audit_dependency_survivability,
        )
        result = audit_dependency_survivability()
        domain_reports["dependency"] = result
        scores["dependency_score"] = result.get("dependency_score", 0)
    except Exception as exc:
        auditor_errors.append(f"dependency: {exc}")
        domain_reports["dependency"] = {"error": str(exc), "dependency_score": 0}

    # ── Auditor 4: Archive Continuity ─────────────────────────────────────────
    try:
        from core.cross_prp_audit.archive_continuity_auditor import (  # lazy
            audit_archive_continuity,
        )
        result = audit_archive_continuity()
        domain_reports["archive"] = result
        scores["archive_score"] = result.get("archive_score", 0)
    except Exception as exc:
        auditor_errors.append(f"archive: {exc}")
        domain_reports["archive"] = {"error": str(exc), "archive_score": 0}

    # ── Auditor 5: Rendering Consistency ─────────────────────────────────────
    try:
        from core.cross_prp_audit.rendering_consistency_auditor import (  # lazy
            audit_rendering_consistency,
        )
        result = audit_rendering_consistency()
        domain_reports["rendering"] = result
        scores["rendering_score"] = result.get("rendering_score", 0)
    except Exception as exc:
        auditor_errors.append(f"rendering: {exc}")
        domain_reports["rendering"] = {"error": str(exc), "rendering_score": 0}

    # ── Auditor 6: Compression Readiness ─────────────────────────────────────
    try:
        from core.cross_prp_audit.compression_readiness_mapper import (  # lazy
            map_compression_readiness,
        )
        result = map_compression_readiness()
        domain_reports["compression"] = result
        scores["compression_readiness_score"] = result.get("compression_readiness_score", 0)
    except Exception as exc:
        auditor_errors.append(f"compression: {exc}")
        domain_reports["compression"] = {"error": str(exc), "compression_readiness_score": 0}

    # ── Composite score ────────────────────────────────────────────────────────
    wiring_health_score: int = round(
        sum(scores[k] * w for k, w in _WEIGHTS.items())
    )
    wiring_health_score = max(0, min(100, wiring_health_score))

    # ── Audit ID: deterministic hash of scores dict ───────────────────────────
    audit_id = _make_audit_id(ts_ms, json.dumps(scores, sort_keys=True))

    return {
        "report":               "CROSS_PRP_WIRING_AUDIT",
        "audit_id":             audit_id,
        "wiring_health_score":  wiring_health_score,
        "wiring_health_tier":   _score_tier(wiring_health_score),
        "domain_scores":        scores,
        "domain_reports":       domain_reports,
        "auditor_errors":       auditor_errors,
        "auto_authorized":      False,
        "generated_ts":         ts_ms,
    }


def get_wiring_audit_health() -> dict:
    """
    Lightweight health probe — returns only scores and tier without the full
    sub-report details.  Suitable for boot-time logging.

    Returns a self-contained dict; never raises.
    """
    try:
        full = run_full_wiring_audit()
        return {
            "report":              "WIRING_AUDIT_HEALTH",
            "audit_id":            full.get("audit_id", ""),
            "wiring_health_score": full.get("wiring_health_score", 0),
            "wiring_health_tier":  full.get("wiring_health_tier", "CRITICAL"),
            "domain_scores":       full.get("domain_scores", {}),
            "auditor_errors":      full.get("auditor_errors", []),
            "auto_authorized":     False,
            "generated_ts":        full.get("generated_ts", int(_time.time() * 1000)),
        }
    except Exception as exc:
        return {
            "report":              "WIRING_AUDIT_HEALTH",
            "error":               str(exc),
            "wiring_health_score": 0,
            "wiring_health_tier":  "CRITICAL",
            "domain_scores":       {},
            "auditor_errors":      [str(exc)],
            "auto_authorized":     False,
            "generated_ts":        int(_time.time() * 1000),
        }
