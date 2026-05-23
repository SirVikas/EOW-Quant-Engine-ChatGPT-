"""
PRP-PHASEC.7 — Compression Orchestrator.

Central institutional compression governance. Runs all Phase-C compression
domains and assembles a unified OPERATIONAL_COMPRESSION_REPORT with a
deterministic lineage ID and replay-safe export structure.

Compression ID format: COMP-{ts_ms}-{sha256[:16]}

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import hashlib
import json
import time as _time
from typing import Any, Dict, List


def _score_tier(score: int) -> str:
    if score >= 80:
        return "HEALTHY"
    if score >= 60:
        return "ADEQUATE"
    if score >= 40:
        return "DEGRADED"
    return "CRITICAL"


def _make_compression_id(ts_ms: int, payload: str) -> str:
    digest = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()
    return f"COMP-{ts_ms}-{digest[:16]}"


def run_full_compression() -> dict:
    """
    PRP-PHASEC.7 — Execute all Phase-C compression domains and assemble a
    unified OPERATIONAL_COMPRESSION_REPORT.

    Domain execution order:
      1. signal_ecology_compression_layer → SIGNAL_ECOLOGY_SUMMARY_REPORT
      2. governance_compression_layer     → GOVERNANCE_EXECUTIVE_SUMMARY
      3. anomaly_clustering_engine        → ANOMALY_CLUSTER_REPORT
      4. institutional_health_score_engine→ INSTITUTIONAL_HEALTH_REPORT
      5. multi_tier_visibility_architecture→ VISIBILITY_TIER_MAP
      6. executive_compression_engine     → EXECUTIVE_COMPRESSION_REPORT

    Returns a self-contained dict; never raises.
    """
    ts_ms: int = int(_time.time() * 1000)
    domain_reports: Dict[str, Any] = {}
    domain_errors: List[str] = []
    domain_scores: Dict[str, int] = {}

    # ── Domain 1: Signal Ecology ──────────────────────────────────────────────
    try:
        from core.operational_compression.signal_ecology_compression_layer import (
            compress_signal_ecology,
        )
        result = compress_signal_ecology()
        domain_reports["signal_ecology"] = result
        domain_scores["signal_ecology"]  = result.get("ecology_score", 0)
    except Exception as exc:
        domain_errors.append(f"signal_ecology: {exc}")
        domain_reports["signal_ecology"] = {"error": str(exc), "ecology_score": 0}
        domain_scores["signal_ecology"]  = 0

    # ── Domain 2: Governance ──────────────────────────────────────────────────
    try:
        from core.operational_compression.governance_compression_layer import (
            compress_governance,
        )
        result = compress_governance()
        domain_reports["governance"] = result
        domain_scores["governance"]  = result.get("governance_health_score", 0)
    except Exception as exc:
        domain_errors.append(f"governance: {exc}")
        domain_reports["governance"] = {"error": str(exc), "governance_health_score": 0}
        domain_scores["governance"]  = 0

    # ── Domain 3: Anomaly Clustering ──────────────────────────────────────────
    try:
        from core.operational_compression.anomaly_clustering_engine import (
            cluster_anomalies,
        )
        result = cluster_anomalies()
        domain_reports["anomalies"] = result
        # Anomaly tier → score: NONE=100, LOW=80, MODERATE=60, HIGH=30, CRITICAL=0
        _anom_tier_score = {
            "NONE": 100, "LOW": 80, "MODERATE": 60,
            "HIGH": 30, "CRITICAL": 0, "UNKNOWN": 50,
        }
        domain_scores["anomalies"] = _anom_tier_score.get(
            result.get("overall_tier", "UNKNOWN"), 50
        )
    except Exception as exc:
        domain_errors.append(f"anomalies: {exc}")
        domain_reports["anomalies"] = {"error": str(exc)}
        domain_scores["anomalies"]  = 0

    # ── Domain 4: Institutional Health ───────────────────────────────────────
    try:
        from core.operational_compression.institutional_health_score_engine import (
            compute_institutional_health,
        )
        result = compute_institutional_health()
        domain_reports["health"] = result
        domain_scores["health"]  = result.get("composite_score", 0)
    except Exception as exc:
        domain_errors.append(f"health: {exc}")
        domain_reports["health"] = {"error": str(exc), "composite_score": 0}
        domain_scores["health"]  = 0

    # ── Domain 5: Visibility Tier Map ─────────────────────────────────────────
    try:
        from core.operational_compression.multi_tier_visibility_architecture import (
            build_visibility_tier_map,
        )
        result = domain_reports["visibility"] = build_visibility_tier_map()
        domain_scores["visibility"] = 100 if result.get("lineage_preserved") else 0
    except Exception as exc:
        domain_errors.append(f"visibility: {exc}")
        domain_reports["visibility"] = {"error": str(exc)}
        domain_scores["visibility"]  = 0

    # ── Domain 6: Executive Compression ──────────────────────────────────────
    try:
        from core.operational_compression.executive_compression_engine import (
            generate_executive_compression,
        )
        result = generate_executive_compression()
        domain_reports["executive"] = result
        domain_scores["executive"]  = result.get("ecosystem_health_score", 0)
    except Exception as exc:
        domain_errors.append(f"executive: {exc}")
        domain_reports["executive"] = {"error": str(exc), "ecosystem_health_score": 0}
        domain_scores["executive"]  = 0

    # ── Composite compression score ───────────────────────────────────────────
    # Weighted: health 30%, signal_ecology 25%, governance 20%,
    #           executive 15%, anomalies 10%
    _score_weights = {
        "health":        0.30,
        "signal_ecology": 0.25,
        "governance":    0.20,
        "executive":     0.15,
        "anomalies":     0.10,
    }
    composite_score = round(
        sum(domain_scores.get(k, 0) * w for k, w in _score_weights.items())
    )
    composite_score = max(0, min(100, composite_score))

    # ── Executive condition (one-word state for dashboards) ───────────────────
    exec_report = domain_reports.get("executive", {})
    executive_condition = exec_report.get("ecosystem_health_tier", _score_tier(composite_score))

    # ── Compression ID ────────────────────────────────────────────────────────
    compression_id = _make_compression_id(
        ts_ms, json.dumps(domain_scores, sort_keys=True)
    )

    # ── Visibility tier summary ───────────────────────────────────────────────
    vis_report = domain_reports.get("visibility", {})
    visibility_tier_count = len(vis_report.get("tier_distribution", {}))

    # ── Anomaly summary ───────────────────────────────────────────────────────
    anom_report = domain_reports.get("anomalies", {})
    anomaly_cluster_state = anom_report.get("overall_tier", "UNKNOWN")
    total_anomalies       = anom_report.get("total_anomalies", 0)

    return {
        "report":                   "OPERATIONAL_COMPRESSION_REPORT",
        "compression_id":           compression_id,
        "composite_score":          composite_score,
        "composite_tier":           _score_tier(composite_score),
        "executive_condition":      executive_condition,
        "domain_scores":            domain_scores,
        "domain_reports":           domain_reports,
        "domain_errors":            domain_errors,
        "visibility_tier_count":    visibility_tier_count,
        "anomaly_cluster_state":    anomaly_cluster_state,
        "total_anomalies":          total_anomalies,
        "executive_synthesis_available": "executive" in domain_reports and "error" not in domain_reports.get("executive", {}),
        "lineage_preserved":        True,
        "replay_safe":              True,
        "auto_authorized":          False,
        "assessment_only":          True,
        "generated_ts":             ts_ms,
    }


def get_compression_health() -> dict:
    """
    Lightweight compression health probe — returns scores and tier without
    full sub-report details. Suitable for boot-time logging.

    Returns a self-contained dict; never raises.
    """
    try:
        full = run_full_compression()
        return {
            "report":                "COMPRESSION_HEALTH",
            "compression_id":        full.get("compression_id", ""),
            "composite_score":       full.get("composite_score", 0),
            "composite_tier":        full.get("composite_tier", "CRITICAL"),
            "executive_condition":   full.get("executive_condition", "UNKNOWN"),
            "domain_scores":         full.get("domain_scores", {}),
            "visibility_tier_count": full.get("visibility_tier_count", 0),
            "anomaly_cluster_state": full.get("anomaly_cluster_state", "UNKNOWN"),
            "domain_errors":         full.get("domain_errors", []),
            "auto_authorized":       False,
            "generated_ts":          full.get("generated_ts", int(_time.time() * 1000)),
        }
    except Exception as exc:
        return {
            "report":                "COMPRESSION_HEALTH",
            "error":                 str(exc),
            "composite_score":       0,
            "composite_tier":        "CRITICAL",
            "executive_condition":   "UNAVAILABLE",
            "domain_scores":         {},
            "visibility_tier_count": 0,
            "anomaly_cluster_state": "UNKNOWN",
            "domain_errors":         [str(exc)],
            "auto_authorized":       False,
            "generated_ts":          int(_time.time() * 1000),
        }
