"""
PRP-PHASEC.2 — Institutional Health Score Engine.

Generates consolidated ecosystem health scoring across 9 mandatory domains.
Scores are ASSESSMENT ONLY — they carry no deployment authority, no scaling
authority, and no capital decision authority.

Health domains (weighted):
  economic_survivability:  20%
  governance_integrity:    20%
  archive_continuity:      15%
  signal_ecology:          15%
  alpha_density:           10%
  propagation_integrity:   10%
  replay_survivability:     5%
  rendering_integrity:      5%
  operational_coherence:    0%  (informational — does not affect score)

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Any, Dict


_WEIGHTS: Dict[str, float] = {
    "economic_survivability": 0.20,
    "governance_integrity":   0.20,
    "archive_continuity":     0.15,
    "signal_ecology":         0.15,
    "alpha_density":          0.10,
    "propagation_integrity":  0.10,
    "replay_survivability":   0.05,
    "rendering_integrity":    0.05,
}


def _score_tier(score: int) -> str:
    if score >= 80:
        return "HEALTHY"
    if score >= 60:
        return "ADEQUATE"
    if score >= 40:
        return "DEGRADED"
    return "CRITICAL"


def compute_institutional_health() -> dict:
    """
    PRP-PHASEC.2 — Compute weighted institutional health score.

    Each domain score is derived from available runtime data; domains that
    cannot be probed fall back to 0 with an error note.

    Returns a self-contained dict with assessment_only=True; never raises.
    """
    domain_scores: Dict[str, int] = {}
    domain_notes:  Dict[str, str] = {}

    # ── Domain 1: Economic Survivability (20%) ────────────────────────────────
    try:
        from core.signal_ecology.signal_density_engine import signal_density_engine
        t = signal_density_engine.get_telemetry()
        sr = t.get("survival_rate", 0.0)
        if t.get("is_starvation"):
            eco_s = 10
        elif t.get("is_drought"):
            eco_s = 40
        else:
            eco_s = min(100, round(sr * 100))
        domain_scores["economic_survivability"] = eco_s
        domain_notes["economic_survivability"]  = (
            f"survival_rate={sr:.2%}, drought={t.get('is_drought')}, "
            f"starvation={t.get('is_starvation')}"
        )
    except Exception as exc:
        domain_scores["economic_survivability"] = 0
        domain_notes["economic_survivability"]  = f"Unavailable: {exc}"

    # ── Domain 2: Governance Integrity (20%) ──────────────────────────────────
    try:
        from core.cross_prp_audit.cross_prp_audit_orchestrator import run_full_wiring_audit
        audit = run_full_wiring_audit()
        domain_audit_scores = audit.get("domain_scores", {})
        const_s = domain_audit_scores.get("constitution_score", 0)
        prop_s  = domain_audit_scores.get("propagation_score", 0)
        dep_s   = domain_audit_scores.get("dependency_score", 0)
        gov_s   = round((const_s * 0.40 + prop_s * 0.35 + dep_s * 0.25))
        domain_scores["governance_integrity"] = gov_s
        domain_notes["governance_integrity"]  = (
            f"constitution={const_s}, propagation={prop_s}, dependency={dep_s}"
        )
    except Exception as exc:
        domain_scores["governance_integrity"] = 0
        domain_notes["governance_integrity"]  = f"Unavailable: {exc}"

    # ── Domain 3: Archive Continuity (15%) ────────────────────────────────────
    try:
        from core.cross_prp_audit.cross_prp_audit_orchestrator import run_full_wiring_audit
        audit = run_full_wiring_audit()
        arch_s = audit.get("domain_scores", {}).get("archive_score", 0)
        domain_scores["archive_continuity"] = arch_s
        domain_notes["archive_continuity"]  = f"archive_score={arch_s}/100"
    except Exception as exc:
        domain_scores["archive_continuity"] = 0
        domain_notes["archive_continuity"]  = f"Unavailable: {exc}"

    # ── Domain 4: Signal Ecology (15%) ────────────────────────────────────────
    try:
        from core.signal_ecology.opportunity_ecology import opportunity_ecology
        t = opportunity_ecology.get_telemetry()
        approval = t.get("approval_rate", 0.0)
        density  = t.get("density_snapshot", {})
        if density.get("is_starvation"):
            sig_s = 15
        elif density.get("is_drought"):
            sig_s = 45
        elif approval >= 0.30:
            sig_s = 90
        elif approval >= 0.10:
            sig_s = 65
        elif t.get("total_evaluated", 0) == 0:
            sig_s = 50
        else:
            sig_s = 30
        domain_scores["signal_ecology"] = sig_s
        domain_notes["signal_ecology"]  = f"approval_rate={approval:.2%}"
    except Exception as exc:
        domain_scores["signal_ecology"] = 0
        domain_notes["signal_ecology"]  = f"Unavailable: {exc}"

    # ── Domain 5: Alpha Density (10%) ─────────────────────────────────────────
    try:
        from core.signal_ecology.alpha_context_memory import alpha_context_memory
        t = alpha_context_memory.get_telemetry()
        total    = t.get("total_contexts", 0)
        profit   = t.get("profitable_count", 0)
        toxic    = t.get("toxic_count", 0)
        if total == 0:
            alpha_s = 50
            note    = "no data"
        else:
            p_ratio = profit / total
            t_ratio = toxic  / total
            if p_ratio >= 0.40:
                alpha_s = 95
            elif p_ratio >= 0.20:
                alpha_s = 70
            elif t_ratio >= 0.50:
                alpha_s = 15
            elif t_ratio >= 0.30:
                alpha_s = 35
            else:
                alpha_s = 50
            note = f"profitable={profit}/{total}, toxic={toxic}/{total}"
        domain_scores["alpha_density"] = alpha_s
        domain_notes["alpha_density"]  = note
    except Exception as exc:
        domain_scores["alpha_density"] = 0
        domain_notes["alpha_density"]  = f"Unavailable: {exc}"

    # ── Domain 6: Propagation Integrity (10%) ─────────────────────────────────
    try:
        from core.cross_prp_audit.cross_prp_audit_orchestrator import run_full_wiring_audit
        audit = run_full_wiring_audit()
        prop_s = audit.get("domain_scores", {}).get("propagation_score", 0)
        domain_scores["propagation_integrity"] = prop_s
        domain_notes["propagation_integrity"]  = f"propagation_score={prop_s}/100"
    except Exception as exc:
        domain_scores["propagation_integrity"] = 0
        domain_notes["propagation_integrity"]  = f"Unavailable: {exc}"

    # ── Domain 7: Replay Survivability (5%) ───────────────────────────────────
    try:
        from core.signal_ecology.exploration_recovery import exploration_recovery_governor
        t = exploration_recovery_governor.get_telemetry()
        consec_blocks = t.get("consecutive_blocks", 0)
        active_cycle  = t.get("active_cycle_id")
        if consec_blocks >= 200:
            rep_s = 10
        elif consec_blocks >= 100:
            rep_s = 30
        elif consec_blocks >= 50:
            rep_s = 55
        elif active_cycle:
            rep_s = 70
        else:
            rep_s = 90
        domain_scores["replay_survivability"] = rep_s
        domain_notes["replay_survivability"]  = (
            f"consecutive_blocks={consec_blocks}, recovery_active={bool(active_cycle)}"
        )
    except Exception as exc:
        domain_scores["replay_survivability"] = 0
        domain_notes["replay_survivability"]  = f"Unavailable: {exc}"

    # ── Domain 8: Rendering Integrity (5%) ────────────────────────────────────
    try:
        from core.cross_prp_audit.cross_prp_audit_orchestrator import run_full_wiring_audit
        audit = run_full_wiring_audit()
        rend_s = audit.get("domain_scores", {}).get("rendering_score", 0)
        domain_scores["rendering_integrity"] = rend_s
        domain_notes["rendering_integrity"]  = f"rendering_score={rend_s}/100"
    except Exception as exc:
        domain_scores["rendering_integrity"] = 0
        domain_notes["rendering_integrity"]  = f"Unavailable: {exc}"

    # ── Weighted composite ────────────────────────────────────────────────────
    composite = round(
        sum(domain_scores.get(k, 0) * w for k, w in _WEIGHTS.items())
    )
    composite = max(0, min(100, composite))

    # ── Operational coherence (informational, not scored) ─────────────────────
    try:
        from core.dashboard_orchestrator import build_dashboard_structure
        dash = build_dashboard_structure({})
        op_coherence_pct = dash.get("coverage_pct", 0.0)
        op_coherence_note = f"dashboard coverage={op_coherence_pct:.1f}%"
    except Exception as exc:
        op_coherence_pct  = 0.0
        op_coherence_note = f"Unavailable: {exc}"

    return {
        "report":              "INSTITUTIONAL_HEALTH_REPORT",
        "composite_score":     composite,
        "composite_tier":      _score_tier(composite),
        "domain_scores":       domain_scores,
        "domain_notes":        domain_notes,
        "weights":             _WEIGHTS,
        "operational_coherence_pct": round(op_coherence_pct, 1),
        "operational_coherence_note": op_coherence_note,
        "assessment_only":     True,
        "auto_authorized":     False,
        "generated_ts":        int(_time.time() * 1000),
    }
