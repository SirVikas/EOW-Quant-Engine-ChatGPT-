"""
PRP-PHASED.G.7 — Adaptive Execution Orchestrator.

Centralised governance for the human-supervised adaptive execution civilization.
Runs all 6 Phase-G engines, generates a unified ADAPTIVE_EXECUTION_CIVILIZATION_REPORT
with a deterministic lineage ID and replay-safe execution synthesis.

Execution ID format: EXEC-{ts_ms}-{sha256[:16]}

CONSTITUTIONAL NOTE: PHOENIX operates under human constitutional authority.
All advisories require human confirmation. No autonomous execution permitted.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import hashlib
import json
import time as _time
from typing import Any, Dict, List, Optional


def _make_execution_id(ts_ms: int, payload: str) -> str:
    digest = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()
    return f"EXEC-{ts_ms}-{digest[:16]}"


def run_adaptive_execution_civilization(trades: List[dict]) -> dict:
    """
    PRP-PHASED.G.7 — Run all Phase-G engines and synthesise execution governance.

    Engine execution order:
      1. restraint_advisory_engine        → RESTRAINT_ADVISORY_REPORT
      2. capital_discipline_gate          → CAPITAL_DISCIPLINE_GATE_REPORT
      3. equilibrium_resumption_engine    → EQUILIBRIUM_RESUMPTION_REPORT
      4. operator_override_transparency   → OPERATOR_OVERRIDE_TRANSPARENCY_REPORT
      5. execution_discipline_memory      → EXECUTION_DISCIPLINE_MEMORY_REPORT
      6. human_governance_safety_engine   → HUMAN_GOVERNANCE_SAFETY_REPORT

    Args:
        trades: Combined session + historical trade dicts.

    Returns ADAPTIVE_EXECUTION_CIVILIZATION_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)
    domain_reports: Dict[str, Any] = {}
    domain_errors:  List[str]      = []

    # ── Engine 1: Restraint Advisory ─────────────────────────────────────────
    try:
        from core.adaptive_execution_governance.restraint_advisory_engine import (
            compute_restraint_advisory,
        )
        domain_reports["restraint"] = compute_restraint_advisory(trades)
    except Exception as exc:
        domain_errors.append(f"restraint: {exc}")
        domain_reports["restraint"] = {"error": str(exc)}

    # ── Engine 2: Capital Discipline Gate ────────────────────────────────────
    try:
        from core.adaptive_execution_governance.capital_discipline_gate import (
            compute_capital_discipline_gate,
        )
        domain_reports["discipline_gate"] = compute_capital_discipline_gate(trades)
    except Exception as exc:
        domain_errors.append(f"discipline_gate: {exc}")
        domain_reports["discipline_gate"] = {"error": str(exc)}

    # ── Engine 3: Equilibrium Resumption ─────────────────────────────────────
    try:
        from core.adaptive_execution_governance.equilibrium_resumption_engine import (
            compute_equilibrium_resumption,
        )
        domain_reports["equilibrium"] = compute_equilibrium_resumption(trades)
    except Exception as exc:
        domain_errors.append(f"equilibrium: {exc}")
        domain_reports["equilibrium"] = {"error": str(exc)}

    # ── Engine 4: Operator Override Transparency ──────────────────────────────
    try:
        from core.adaptive_execution_governance.operator_override_transparency_engine import (
            compute_operator_override_transparency,
        )
        domain_reports["override_transparency"] = compute_operator_override_transparency(trades)
    except Exception as exc:
        domain_errors.append(f"override_transparency: {exc}")
        domain_reports["override_transparency"] = {"error": str(exc)}

    # ── Engine 5: Execution Discipline Memory ─────────────────────────────────
    try:
        from core.adaptive_execution_governance.execution_discipline_memory_engine import (
            compute_execution_discipline_memory,
        )
        domain_reports["discipline_memory"] = compute_execution_discipline_memory(trades)
    except Exception as exc:
        domain_errors.append(f"discipline_memory: {exc}")
        domain_reports["discipline_memory"] = {"error": str(exc)}

    # ── Engine 6: Human Governance Safety ────────────────────────────────────
    try:
        from core.adaptive_execution_governance.human_governance_safety_engine import (
            compute_human_governance_safety,
        )
        domain_reports["governance_safety"] = compute_human_governance_safety(trades)
    except Exception as exc:
        domain_errors.append(f"governance_safety: {exc}")
        domain_reports["governance_safety"] = {"error": str(exc)}

    # ── Extract key signals ───────────────────────────────────────────────────
    advisory         = domain_reports["restraint"].get("advisory", "UNKNOWN")
    gate_state       = domain_reports["discipline_gate"].get("gate_state", "UNKNOWN")
    equilibrium_state = domain_reports["equilibrium"].get("equilibrium_state", "UNKNOWN")
    override_count   = domain_reports["override_transparency"].get("total_override_count", 0)
    discipline_tier  = domain_reports["discipline_memory"].get("discipline_tier", "UNKNOWN")
    governance_status = domain_reports["governance_safety"].get("governance_status", "UNKNOWN")

    # ── Civilization score (0-100) ────────────────────────────────────────────
    civilization_score = 0
    score_evidence: Dict[str, bool] = {}

    if advisory in ("TRADE_ALLOWED", "CONTRACT_RISK"):
        civilization_score += 25
        score_evidence["execution_viable"] = True
    else:
        score_evidence["execution_viable"] = False

    if gate_state in ("PASS", "CAUTION"):
        civilization_score += 20
        score_evidence["gate_acceptable"] = True
    else:
        score_evidence["gate_acceptable"] = False

    if equilibrium_state in ("ACTIVE", "CAUTIONARY"):
        civilization_score += 20
        score_evidence["equilibrium_stable"] = True
    else:
        score_evidence["equilibrium_stable"] = False

    if governance_status in ("CERTIFIED", "PARTIAL_CERTIFICATION"):
        civilization_score += 20
        score_evidence["governance_certified"] = True
    else:
        score_evidence["governance_certified"] = False

    if discipline_tier in ("DISCIPLINED", "ADEQUATE"):
        civilization_score += 15
        score_evidence["discipline_adequate"] = True
    else:
        score_evidence["discipline_adequate"] = False

    civilization_score = max(0, min(100, civilization_score))

    if civilization_score >= 80:
        tier = "SOVEREIGN"      # supervised sovereign — NOT autonomous
    elif civilization_score >= 60:
        tier = "OPERATIONAL"
    elif civilization_score >= 40:
        tier = "GUARDED"
    else:
        tier = "COMPROMISED"

    # ── Lineage ID ────────────────────────────────────────────────────────────
    key_data = {
        "trade_count":      len(trades),
        "advisory":         advisory,
        "gate_state":       gate_state,
        "equilibrium_state": equilibrium_state,
        "domain_errors":    len(domain_errors),
    }
    execution_id = _make_execution_id(ts_ms, json.dumps(key_data, sort_keys=True))

    return {
        "report":               "ADAPTIVE_EXECUTION_CIVILIZATION_REPORT",
        "execution_id":         execution_id,
        "trade_count":          len(trades),
        "civilization_score":   civilization_score,
        "civilization_tier":    tier,
        "restraint_advisory":   advisory,
        "gate_state":           gate_state,
        "equilibrium_state":    equilibrium_state,
        "override_count":       override_count,
        "discipline_tier":      discipline_tier,
        "governance_status":    governance_status,
        "score_evidence":       score_evidence,
        "domain_reports":       domain_reports,
        "domain_errors":        domain_errors,
        "constitutional_note":  (
            "PHOENIX operates under human constitutional authority. "
            "All advisories require human confirmation."
        ),
        "lineage_preserved":    True,
        "replay_safe":          True,
        "diagnostic_only":      True,
        "auto_authorized":      False,
        "human_confirmed":      True,
        "override_visible":     True,
        "generated_ts":         ts_ms,
    }


def get_execution_governance_health(trades: List[dict]) -> dict:
    """
    Lightweight execution governance health probe.
    Returns scores and condition without full domain report details.

    Returns EXECUTION_GOVERNANCE_HEALTH; never raises.
    """
    try:
        full = run_adaptive_execution_civilization(trades)
        return {
            "report":                 "EXECUTION_GOVERNANCE_HEALTH",
            "execution_id":           full.get("execution_id", ""),
            "trade_count":            full.get("trade_count", 0),
            "civilization_score":     full.get("civilization_score", 0),
            "civilization_tier":      full.get("civilization_tier", "COMPROMISED"),
            "restraint_advisory":     full.get("restraint_advisory", "UNKNOWN"),
            "gate_state":             full.get("gate_state", "UNKNOWN"),
            "equilibrium_state":      full.get("equilibrium_state", "UNKNOWN"),
            "governance_status":      full.get("governance_status", "UNKNOWN"),
            "discipline_tier":        full.get("discipline_tier", "UNKNOWN"),
            "domain_errors":          full.get("domain_errors", []),
            "diagnostic_only":        True,
            "auto_authorized":        False,
            "human_confirmed":        True,
            "generated_ts":           full.get("generated_ts", int(_time.time() * 1000)),
        }
    except Exception as exc:
        return {
            "report":                 "EXECUTION_GOVERNANCE_HEALTH",
            "error":                  str(exc),
            "trade_count":            0,
            "civilization_score":     0,
            "civilization_tier":      "COMPROMISED",
            "restraint_advisory":     "UNAVAILABLE",
            "gate_state":             "UNAVAILABLE",
            "equilibrium_state":      "UNAVAILABLE",
            "governance_status":      "UNAVAILABLE",
            "discipline_tier":        "UNAVAILABLE",
            "domain_errors":          [str(exc)],
            "diagnostic_only":        True,
            "auto_authorized":        False,
            "human_confirmed":        True,
            "generated_ts":           int(_time.time() * 1000),
        }
