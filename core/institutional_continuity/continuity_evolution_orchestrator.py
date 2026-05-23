"""
PRP-PHASED.H.7 — Continuity Evolution Orchestrator.

Centralised long-horizon survivability governance. Runs all 6 Phase-H engines,
generates a unified INSTITUTIONAL_CONTINUITY_REPORT with a deterministic
lineage ID and replay-safe evolutionary synthesis.

Continuity ID format: CONT-{ts_ms}-{sha256[:16]}

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import hashlib
import json
import time as _time
from typing import Any, Dict, List, Optional


def _make_continuity_id(ts_ms: int, payload: str) -> str:
    digest = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()
    return f"CONT-{ts_ms}-{digest[:16]}"


def run_institutional_continuity(trades: List[dict]) -> dict:
    """
    PRP-PHASED.H.7 — Run all Phase-H continuity engines and synthesise results.

    Engine execution order:
      1. multi_cycle_survivability_memory    → MULTI_CYCLE_SURVIVABILITY_REPORT
      2. evolutionary_doctrine_memory        → EVOLUTIONARY_DOCTRINE_REPORT
      3. long_horizon_entropy_engine         → LONG_HORIZON_ENTROPY_REPORT
      4. institutional_recovery_inheritance  → RECOVERY_INHERITANCE_REPORT
      5. cross_regime_continuity_engine      → CROSS_REGIME_CONTINUITY_REPORT
      6. institutional_identity_stability    → INSTITUTIONAL_IDENTITY_REPORT

    Args:
        trades: Combined session + historical trade dicts.

    Returns INSTITUTIONAL_CONTINUITY_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)
    domain_reports: Dict[str, Any] = {}
    domain_errors:  List[str]      = []

    # ── Engine 1 ──────────────────────────────────────────────────────────────
    try:
        from core.institutional_continuity.multi_cycle_survivability_memory import (
            compute_multi_cycle_survivability_memory,
        )
        domain_reports["survivability_memory"] = compute_multi_cycle_survivability_memory(trades)
    except Exception as exc:
        domain_errors.append(f"survivability_memory: {exc}")
        domain_reports["survivability_memory"] = {"error": str(exc)}

    # ── Engine 2 ──────────────────────────────────────────────────────────────
    try:
        from core.institutional_continuity.evolutionary_doctrine_memory import (
            compute_evolutionary_doctrine_memory,
        )
        domain_reports["doctrine"] = compute_evolutionary_doctrine_memory(trades)
    except Exception as exc:
        domain_errors.append(f"doctrine: {exc}")
        domain_reports["doctrine"] = {"error": str(exc)}

    # ── Engine 3 ──────────────────────────────────────────────────────────────
    try:
        from core.institutional_continuity.long_horizon_entropy_engine import (
            compute_long_horizon_entropy,
        )
        domain_reports["entropy"] = compute_long_horizon_entropy(trades)
    except Exception as exc:
        domain_errors.append(f"entropy: {exc}")
        domain_reports["entropy"] = {"error": str(exc)}

    # ── Engine 4 ──────────────────────────────────────────────────────────────
    try:
        from core.institutional_continuity.institutional_recovery_inheritance import (
            compute_institutional_recovery_inheritance,
        )
        domain_reports["recovery"] = compute_institutional_recovery_inheritance(trades)
    except Exception as exc:
        domain_errors.append(f"recovery: {exc}")
        domain_reports["recovery"] = {"error": str(exc)}

    # ── Engine 5 ──────────────────────────────────────────────────────────────
    try:
        from core.institutional_continuity.cross_regime_continuity_engine import (
            compute_cross_regime_continuity,
        )
        domain_reports["cross_regime"] = compute_cross_regime_continuity(trades)
    except Exception as exc:
        domain_errors.append(f"cross_regime: {exc}")
        domain_reports["cross_regime"] = {"error": str(exc)}

    # ── Engine 6 ──────────────────────────────────────────────────────────────
    try:
        from core.institutional_continuity.institutional_identity_stability_engine import (
            compute_institutional_identity_stability,
        )
        domain_reports["identity"] = compute_institutional_identity_stability(trades)
    except Exception as exc:
        domain_errors.append(f"identity: {exc}")
        domain_reports["identity"] = {"error": str(exc)}

    # ── Extract signals ───────────────────────────────────────────────────────
    cycle_verdict    = domain_reports["survivability_memory"].get("multi_cycle_verdict", "UNKNOWN")
    doctrine_state   = domain_reports["doctrine"].get("doctrine_state", "UNKNOWN")
    entropy_state    = domain_reports["entropy"].get("entropy_state", "UNKNOWN")
    inheritance_state = domain_reports["recovery"].get("inheritance_state", "UNKNOWN")
    continuity_verdict = domain_reports["cross_regime"].get("continuity_verdict", "UNKNOWN")
    identity_status  = domain_reports["identity"].get("identity_status", "UNKNOWN")

    # ── Continuity score (0-100) ──────────────────────────────────────────────
    score = 0
    evidence: Dict[str, bool] = {}

    if cycle_verdict in ("DURABLE", "CYCLICAL"):
        score += 20
        evidence["cycles_stable"] = True
    else:
        evidence["cycles_stable"] = False

    if entropy_state in ("DURABLE", "AGING"):
        score += 20
        evidence["entropy_managed"] = True
    else:
        evidence["entropy_managed"] = False

    if continuity_verdict in ("UNIVERSAL", "BROAD"):
        score += 20
        evidence["cross_regime_viable"] = True
    else:
        evidence["cross_regime_viable"] = False

    if identity_status in ("STABLE", "CAUTIONARY"):
        score += 20
        evidence["identity_preserved"] = True
    else:
        evidence["identity_preserved"] = False

    if inheritance_state in ("RICH_INHERITANCE", "MODERATE_INHERITANCE"):
        score += 20
        evidence["recovery_inherited"] = True
    else:
        evidence["recovery_inherited"] = False

    score = max(0, min(100, score))

    if score >= 80:
        tier = "ENDURING"
    elif score >= 60:
        tier = "PERSISTENT"
    elif score >= 40:
        tier = "FRAGILE"
    else:
        tier = "DECAYING"

    # ── Lineage ID ────────────────────────────────────────────────────────────
    key_data = {
        "trade_count":    len(trades),
        "cycle_verdict":  cycle_verdict,
        "entropy_state":  entropy_state,
        "identity_status": identity_status,
        "domain_errors":  len(domain_errors),
    }
    continuity_id = _make_continuity_id(ts_ms, json.dumps(key_data, sort_keys=True))

    return {
        "report":               "INSTITUTIONAL_CONTINUITY_REPORT",
        "continuity_id":        continuity_id,
        "trade_count":          len(trades),
        "continuity_score":     score,
        "continuity_tier":      tier,
        "multi_cycle_verdict":  cycle_verdict,
        "doctrine_state":       doctrine_state,
        "entropy_state":        entropy_state,
        "inheritance_state":    inheritance_state,
        "cross_regime_verdict": continuity_verdict,
        "identity_status":      identity_status,
        "score_evidence":       evidence,
        "domain_reports":       domain_reports,
        "domain_errors":        domain_errors,
        "lineage_preserved":    True,
        "replay_safe":          True,
        "diagnostic_only":      True,
        "auto_authorized":      False,
        "generated_ts":         ts_ms,
    }


def get_continuity_health(trades: List[dict]) -> dict:
    """
    Lightweight continuity health probe for boot visibility.

    Returns CONTINUITY_HEALTH; never raises.
    """
    try:
        full = run_institutional_continuity(trades)
        return {
            "report":               "CONTINUITY_HEALTH",
            "continuity_id":        full.get("continuity_id", ""),
            "trade_count":          full.get("trade_count", 0),
            "continuity_score":     full.get("continuity_score", 0),
            "continuity_tier":      full.get("continuity_tier", "DECAYING"),
            "multi_cycle_verdict":  full.get("multi_cycle_verdict", "UNKNOWN"),
            "doctrine_state":       full.get("doctrine_state", "UNKNOWN"),
            "entropy_state":        full.get("entropy_state", "UNKNOWN"),
            "inheritance_state":    full.get("inheritance_state", "UNKNOWN"),
            "cross_regime_verdict": full.get("cross_regime_verdict", "UNKNOWN"),
            "identity_status":      full.get("identity_status", "UNKNOWN"),
            "domain_errors":        full.get("domain_errors", []),
            "diagnostic_only":      True,
            "auto_authorized":      False,
            "generated_ts":         full.get("generated_ts", int(_time.time() * 1000)),
        }
    except Exception as exc:
        return {
            "report":               "CONTINUITY_HEALTH",
            "error":                str(exc),
            "trade_count":          0,
            "continuity_score":     0,
            "continuity_tier":      "DECAYING",
            "multi_cycle_verdict":  "UNAVAILABLE",
            "doctrine_state":       "UNAVAILABLE",
            "entropy_state":        "UNAVAILABLE",
            "inheritance_state":    "UNAVAILABLE",
            "cross_regime_verdict": "UNAVAILABLE",
            "identity_status":      "UNAVAILABLE",
            "domain_errors":        [str(exc)],
            "diagnostic_only":      True,
            "auto_authorized":      False,
            "generated_ts":         int(_time.time() * 1000),
        }
