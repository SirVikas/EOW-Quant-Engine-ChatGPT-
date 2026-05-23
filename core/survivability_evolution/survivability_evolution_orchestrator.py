"""
PRP-PHASED.E.7 — Survivability Evolution Orchestrator
DIAGNOSTIC ONLY — no trading decisions, no I/O, no side effects.
"""
from __future__ import annotations

import hashlib
import json
import time as _time
from typing import List

from core.survivability_evolution.expectancy_stability_engine import compute_expectancy_stability
from core.survivability_evolution.ecological_self_preservation_engine import compute_ecological_self_preservation
from core.survivability_evolution.regime_adaptation_memory_engine import compute_regime_adaptation_memory
from core.survivability_evolution.alpha_persistence_tracker import track_alpha_persistence
from core.survivability_evolution.confidence_realism_engine import compute_confidence_realism
from core.survivability_evolution.entropy_resistance_engine import compute_entropy_resistance


def run_survivability_evolution(trades: List[dict]) -> dict:
    try:
        return _run(trades)
    except Exception as exc:
        return {
            "report": "SURVIVABILITY_EVOLUTION_REPORT",
            "error": str(exc),
            "trade_count": len(trades) if trades else 0,
            "evolution_score": 0,
            "evolution_tier": "COLLAPSING",
            "domain_errors": [str(exc)],
            "diagnostic_only": True,
            "auto_authorized": False,
            "generated_ts": int(_time.time() * 1000),
        }


def get_survivability_health(trades: List[dict]) -> dict:
    try:
        full = run_survivability_evolution(trades)
        return {
            "report": "SURVIVABILITY_HEALTH",
            "survivability_id": full.get("survivability_id", ""),
            "trade_count": full.get("trade_count", 0),
            "evolution_score": full.get("evolution_score", 0),
            "evolution_tier": full.get("evolution_tier", "COLLAPSING"),
            "expectancy_persistence_state": full.get("expectancy_persistence_state", "UNKNOWN"),
            "ecological_preservation_tier": full.get("ecological_preservation_tier", "UNKNOWN"),
            "alpha_persistence_state": full.get("alpha_persistence_state", "UNKNOWN"),
            "entropy_state": full.get("entropy_state", "UNKNOWN"),
            "confidence_realism_score": full.get("confidence_realism_score", 0),
            "dominant_regime": full.get("dominant_regime"),
            "domain_errors": full.get("domain_errors", []),
            "diagnostic_only": True,
            "auto_authorized": False,
            "generated_ts": int(_time.time() * 1000),
        }
    except Exception as exc:
        return {
            "report": "SURVIVABILITY_HEALTH",
            "error": str(exc),
            "trade_count": 0,
            "evolution_score": 0,
            "evolution_tier": "COLLAPSING",
            "expectancy_persistence_state": "UNAVAILABLE",
            "ecological_preservation_tier": "UNAVAILABLE",
            "alpha_persistence_state": "UNAVAILABLE",
            "entropy_state": "UNAVAILABLE",
            "confidence_realism_score": 0,
            "dominant_regime": None,
            "domain_errors": [str(exc)],
            "diagnostic_only": True,
            "auto_authorized": False,
            "generated_ts": int(_time.time() * 1000),
        }


def _run(trades: List[dict]) -> dict:
    ts = int(_time.time() * 1000)
    domain_reports: dict = {}
    domain_errors: list[str] = []

    _runners = [
        ("expectancy_stability",    lambda: compute_expectancy_stability(trades)),
        ("ecological_preservation", lambda: compute_ecological_self_preservation(trades)),
        ("regime_memory",           lambda: compute_regime_adaptation_memory(trades)),
        ("alpha_persistence",       lambda: track_alpha_persistence(trades)),
        ("confidence_realism",      lambda: compute_confidence_realism(trades)),
        ("entropy_resistance",      lambda: compute_entropy_resistance(trades)),
    ]

    for key, fn in _runners:
        try:
            domain_reports[key] = fn()
        except Exception as exc:
            domain_errors.append(f"{key}: {exc}")
            domain_reports[key] = {"error": str(exc)}

    stability_state   = domain_reports.get("expectancy_stability", {}).get("stability_state", "UNKNOWN")
    preservation_tier = domain_reports.get("ecological_preservation", {}).get("preservation_tier", "UNKNOWN")
    alpha_state       = domain_reports.get("alpha_persistence", {}).get("alpha_state", "UNKNOWN")
    realism_score     = int(domain_reports.get("confidence_realism", {}).get("realism_score", 50))
    entropy_state     = domain_reports.get("entropy_resistance", {}).get("entropy_state", "UNKNOWN")
    dominant_regime   = domain_reports.get("regime_memory", {}).get("dominant_regime")

    score_evidence: dict[str, bool] = {
        "expectancy_stable":   stability_state in ("STABILIZING", "RECOVERING"),
        "ecology_preserved":   preservation_tier in ("SAFE", "GUARDED"),
        "alpha_persisting":    alpha_state in ("PERSISTENT", "LOCALIZED"),
        "entropy_managed":     entropy_state in ("STABLE", "FRAGILE"),
        "confidence_realistic": realism_score >= 60,
    }

    evolution_score = 0
    if score_evidence["expectancy_stable"]:
        evolution_score += 25
    if score_evidence["ecology_preserved"]:
        evolution_score += 20
    if score_evidence["alpha_persisting"]:
        evolution_score += 20
    if score_evidence["entropy_managed"]:
        evolution_score += 15
    if score_evidence["confidence_realistic"]:
        evolution_score += 20
    evolution_score = max(0, min(100, evolution_score))

    if evolution_score >= 75:
        evolution_tier = "EVOLVING"
    elif evolution_score >= 50:
        evolution_tier = "ADAPTING"
    elif evolution_score >= 25:
        evolution_tier = "STRUGGLING"
    else:
        evolution_tier = "COLLAPSING"

    trade_count = len(trades) if trades else 0

    lineage_payload = json.dumps(
        {
            "domain_errors_count": len(domain_errors),
            "entropy_state": entropy_state,
            "persistence_state": stability_state,
            "trade_count": trade_count,
        },
        sort_keys=True,
    )
    sha = hashlib.sha256(lineage_payload.encode()).hexdigest()
    survivability_id = f"SURV-{ts}-{sha[:16]}"

    return {
        "report": "SURVIVABILITY_EVOLUTION_REPORT",
        "survivability_id": survivability_id,
        "trade_count": trade_count,
        "evolution_score": evolution_score,
        "evolution_tier": evolution_tier,
        "expectancy_persistence_state": stability_state,
        "ecological_preservation_tier": preservation_tier,
        "alpha_persistence_state": alpha_state,
        "entropy_state": entropy_state,
        "confidence_realism_score": realism_score,
        "dominant_regime": dominant_regime,
        "score_evidence": score_evidence,
        "domain_reports": domain_reports,
        "domain_errors": domain_errors,
        "lineage_preserved": True,
        "replay_safe": True,
        "diagnostic_only": True,
        "auto_authorized": False,
        "generated_ts": ts,
    }
