"""
FTD-GADD: Guarded Adaptive Deployment Doctrine & Human Override Constitution.

Pure analytics — no I/O, no side effects, no execution authority.

Synthesises across all PHOENIX adaptive analytics subsystems (CIL, GAGS, memory
pressure) to produce a constitutional governance assessment:

  1. Governance state assessment (6 constitutional states)
  2. Constitutional risk diagnostics (6 metrics, 0–100 each)
  3. Constitutional classification (6 research categories)
  4. Constitutional stability score (0–100)
  5. Research-only adaptive recommendations (never auto-authorised)
  6. Human override constitution verification
  7. Immutable audit entry generation (append-only ledger entry)
  8. Audit ledger integrity report

Hard constitutional rules:
  DO NOT enable self-authorised deployment
  DO NOT enable autonomous execution mutation
  DO NOT enable recursive self-governance
  DO NOT enable self-persisting adaptation
  DO NOT weaken human override capability

PHOENIX must NEVER become sovereign over its own deployment authority.

Isolation guarantee: zero live engine imports. Pure synthesis on caller-supplied state.
"""
from __future__ import annotations

import hashlib
import json
import time as _time
from typing import Dict, List, Optional

# ── Governance state constants ─────────────────────────────────────────────────
OBSERVATION_ONLY      = "OBSERVATION_ONLY"       # default: pure observation, no adaptation
SANDBOX_REPLAY        = "SANDBOX_REPLAY"          # replay-only experimentation
HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"  # recommendation-only, explicit approval needed
GUARDED_EXPERIMENT    = "GUARDED_EXPERIMENT"     # temporary supervised activation
AUTO_DISABLED         = "AUTO_DISABLED"           # emergency freeze — instability detected
CONSTITUTION_LOCKDOWN = "CONSTITUTION_LOCKDOWN"  # hard human-only control

# ── Constitutional classification labels ──────────────────────────────────────
CONSTITUTIONALLY_STABLE  = "CONSTITUTIONALLY_STABLE"    # governance healthy
OVERSIGHT_DEPENDENT      = "OVERSIGHT_DEPENDENT"         # safe only under continuous review
ADAPTIVE_DRIFT_RISK      = "ADAPTIVE_DRIFT_RISK"         # beliefs escalating without evidence
RECOMMENDATION_OVERREACH = "RECOMMENDATION_OVERREACH"    # system confidence exceeds evidence
GOVERNANCE_FRAGMENTATION = "GOVERNANCE_FRAGMENTATION"    # conflicting adaptive doctrines
LOCKDOWN_RECOMMENDED     = "LOCKDOWN_RECOMMENDED"        # constitutional freeze advised

# ── Human-readable governance state descriptions ──────────────────────────────
GOVERNANCE_STATE_DESCRIPTIONS: Dict[str, str] = {
    OBSERVATION_ONLY:      "Default state: pure observation, no adaptive action allowed.",
    SANDBOX_REPLAY:        "Replay-only: sandbox experimentation permitted, no production mutation.",
    HUMAN_REVIEW_REQUIRED: "Recommendation-only: explicit human review required before any next step.",
    GUARDED_EXPERIMENT:    "Supervised window: temporary guarded experiment under active monitoring.",
    AUTO_DISABLED:         "Emergency freeze: automatic governance halt due to detected instability.",
    CONSTITUTION_LOCKDOWN: "Hard lockdown: constitutional emergency — human-only control required.",
}

# ── Hard constitutional principles (immutable) ────────────────────────────────
HARD_PRINCIPLES: Dict[str, bool] = {
    "human_supremacy":                True,
    "explicit_approval_required":     True,
    "rollback_capable":               True,
    "audit_history_immutable":        True,
    "policy_transparent":             True,
    "sandbox_first_doctrine":         True,
    "production_isolation":           True,
    "self_authorization_possible":    False,
    "autonomous_deployment_possible": False,
    "recursive_self_governance":      False,
    "self_persisting_adaptation":     False,
}

# ── Threshold constants ────────────────────────────────────────────────────────
LOCKDOWN_DRIFT_THRESHOLD      = 80.0   # autonomous_drift_risk ≥ this → CONSTITUTION_LOCKDOWN
LOCKDOWN_INSTAB_THRESHOLD     = 80.0   # governance_instability ≥ this → CONSTITUTION_LOCKDOWN
REVIEW_OVERFIT_THRESHOLD      = 60.0   # overfitting_escalation_risk ≥ this → HUMAN_REVIEW_REQUIRED
REVIEW_INSTAB_THRESHOLD       = 50.0   # governance_instability ≥ this → HUMAN_REVIEW_REQUIRED
SANDBOX_DRIFT_THRESHOLD       = 30.0   # autonomous_drift_risk ≥ this → SANDBOX_REPLAY
SANDBOX_OVERFIT_THRESHOLD     = 40.0   # overfitting_escalation_risk ≥ this → SANDBOX_REPLAY
GUARDED_CONFIDENCE_THRESHOLD  = 75.0   # recommendation_confidence ≥ this for GUARDED_EXPERIMENT
GUARDED_DRIFT_CEILING         = 20.0   # autonomous_drift_risk < this for GUARDED_EXPERIMENT
FRAG_CONFLICT_THRESHOLD       = 3      # conflict_count ≥ this → GOVERNANCE_FRAGMENTATION
ADAPTIVE_DRIFT_RISK_THRESHOLD = 70.0   # drift_risk ≥ this → ADAPTIVE_DRIFT_RISK
OVERREACH_OVERFIT_THRESHOLD   = 60.0   # overfitting ≥ this combined with low confidence
OVERREACH_CONF_CEILING        = 50.0   # recommendation_confidence < this for OVERREACH
OVERSIGHT_INSTAB_THRESHOLD    = 50.0   # governance_instability ≥ this → OVERSIGHT_DEPENDENT
OVERSIGHT_DRIFT_THRESHOLD     = 40.0   # drift_risk ≥ this → OVERSIGHT_DEPENDENT


# ── Tier helpers ──────────────────────────────────────────────────────────────

def _risk_tier(score: float) -> str:
    if score >= 70:  return "HIGH"
    if score >= 40:  return "MODERATE"
    if score >= 20:  return "LOW"
    return "MINIMAL"


def _integrity_tier(score: float) -> str:
    if score >= 80:  return "INTACT"
    if score >= 50:  return "ADEQUATE"
    if score >= 20:  return "DEGRADED"
    return "COMPROMISED"


def _confidence_tier(score: float) -> str:
    if score >= 75:  return "HIGH"
    if score >= 50:  return "MODERATE"
    if score >= 25:  return "LOW"
    return "INSUFFICIENT"


def _stability_tier(score: float) -> str:
    if score >= 80:  return "STRONG"
    if score >= 60:  return "ADEQUATE"
    if score >= 40:  return "WEAKENED"
    return "CRITICAL"


# ── Individual risk diagnostic functions ──────────────────────────────────────

def _autonomous_drift_risk(state: dict) -> dict:
    """
    Proxy for how far converged beliefs have drifted from evidentially-grounded
    learning. Combines ontology drift, fossilization risk, and exploration suppression.
    """
    mem = state.get("memory_pressure", {}) or {}

    # Extract max drift score across all drift pair entries in the heatmap
    drift_heatmap = mem.get("drift_heatmap", {}) or {}
    max_drift = 0.0
    if isinstance(drift_heatmap, dict):
        for pair_data in drift_heatmap.values():
            if isinstance(pair_data, dict):
                max_drift = max(max_drift, float(pair_data.get("score", 0.0) or 0.0))

    # Fallback to any max_drift_score key in ontology_drift summary
    if max_drift == 0.0:
        od = mem.get("ontology_drift", {}) or {}
        if isinstance(od, dict):
            max_drift = float(od.get("max_drift_score", 0.0) or 0.0)

    fossil_score = float(
        ((mem.get("memory_pressure", {}) or {}).get("fossilization_risk", {}) or {})
        .get("score", 0) or 0
    )

    explore_ratio = float(
        (state.get("rl", {}) or {}).get("explore_ratio", 0.25) or 0.25
    )

    # High drift + high fossilisation + low exploration → high autonomous drift risk
    drift_component   = min(100.0, max_drift * 100.0 / 60.0) if max_drift > 0 else 0.0
    fossil_component  = fossil_score
    explore_component = (
        max(0.0, (0.10 - explore_ratio) / 0.10 * 100.0)
        if explore_ratio < 0.10 else 0.0
    )

    raw   = drift_component * 0.4 + fossil_component * 0.4 + explore_component * 0.2
    score = round(min(100.0, max(0.0, raw)), 1)
    return {"score": score, "tier": _risk_tier(score)}


def _overfitting_escalation_risk(state: dict) -> dict:
    """
    Proxy for whether adaptive optimisation is sacrificing opportunity breadth.
    Amplified when CIL already detected opportunity collapse.
    """
    gov = state.get("governance", {}) or {}
    ofr_score = float(
        ((gov.get("overfitting_risk", {}) or {}).get("score", 0.0)) or 0.0
    )

    cil = state.get("counterfactual", {}) or {}
    opp_collapse = bool(cil.get("opportunity_collapse_detected", False))

    base  = min(100.0, ofr_score)
    if opp_collapse:
        base = min(100.0, base + 25.0)

    score = round(base, 1)
    return {"score": score, "tier": _risk_tier(score)}


def _governance_instability_metric(state: dict) -> dict:
    """
    Proxy for cross-profile governance conflict and classification diversity.
    High conflict count + diverse outcome classifications → fragmented governance.
    """
    gov = state.get("governance", {}) or {}
    ca  = gov.get("conflict_analysis", {}) or {}
    conflict_count = int(ca.get("conflict_count", 0) or 0)

    conflict_score  = min(100.0, conflict_count / 3.0 * 100.0)

    classifications = gov.get("governance_classifications", {}) or {}
    unique_cls      = len(set(classifications.values())) if classifications else 0
    diversity_score = min(100.0, max(0.0, (unique_cls - 1) / 5.0 * 100.0))

    raw   = conflict_score * 0.6 + diversity_score * 0.4
    score = round(min(100.0, max(0.0, raw)), 1)
    return {"score": score, "tier": _risk_tier(score)}


def _human_override_integrity_metric(audit_ledger: list) -> dict:
    """
    Verify the audit ledger contains no autonomous actions.
    Score 100 = fully intact (all entries recommendation-only, as required).
    Decrements by 20 per autonomous-action violation detected.
    """
    if not audit_ledger or not isinstance(audit_ledger, list):
        return {"score": 100.0, "tier": _integrity_tier(100.0), "autonomous_actions_detected": 0}

    auto_actions = sum(
        1 for e in audit_ledger
        if isinstance(e, dict) and e.get("auto_authorized") is True
    )
    score = max(0.0, 100.0 - auto_actions * 20.0)
    return {
        "score": round(score, 1),
        "tier":  _integrity_tier(score),
        "autonomous_actions_detected": auto_actions,
    }


def _recommendation_confidence_metric(state: dict) -> dict:
    """
    Statistical confidence in recommendations, driven by CIL trade corpus size.
    Larger corpus → more reliable replay statistics → higher recommendation confidence.
    """
    cil          = state.get("counterfactual", {}) or {}
    total_trades = int(cil.get("total_trades", 0) or 0)

    if   total_trades >= 500: raw = 90.0
    elif total_trades >= 200: raw = 75.0
    elif total_trades >= 100: raw = 60.0
    elif total_trades >= 50:  raw = 40.0
    elif total_trades >= 20:  raw = 25.0
    else:                     raw = 10.0

    score = round(raw, 1)
    return {
        "score":             score,
        "tier":              _confidence_tier(score),
        "trade_corpus_size": total_trades,
    }


def _sandbox_production_divergence_metric(state: dict) -> dict:
    """
    Proxy for how far the best simulated sandbox scenario diverges from production.
    Combines GAGS overfitting risk with regime concentration (HHI × 100).
    Higher divergence = sandbox improvements may not transfer to live production.
    """
    gov      = state.get("governance", {}) or {}
    ofr      = gov.get("overfitting_risk", {}) or {}
    ofr_tier = ofr.get("tier", "LOW")
    rsr_score = float(
        ((gov.get("regime_specialization_risk", {}) or {}).get("score", 0.0)) or 0.0
    )

    base             = {"HIGH": 75.0, "MODERATE": 45.0, "LOW": 15.0}.get(ofr_tier, 15.0)
    regime_component = min(100.0, rsr_score) * 0.3
    raw              = base * 0.7 + regime_component
    score            = round(min(100.0, max(0.0, raw)), 1)
    return {"score": score, "tier": _risk_tier(score)}


def _compute_risk_diagnostics(state: dict, audit_ledger: list) -> dict:
    """Aggregate all 6 constitutional risk metrics into a single diagnostics dict."""
    return {
        "autonomous_drift_risk":         _autonomous_drift_risk(state),
        "overfitting_escalation_risk":   _overfitting_escalation_risk(state),
        "governance_instability":        _governance_instability_metric(state),
        "human_override_integrity":      _human_override_integrity_metric(audit_ledger),
        "recommendation_confidence":     _recommendation_confidence_metric(state),
        "sandbox_production_divergence": _sandbox_production_divergence_metric(state),
    }


# ── Governance state assessment ────────────────────────────────────────────────

def _assess_governance_state(
    risk_diagnostics: dict,
    cil_flags:        dict,
    cognitive_state:  str,
    conflict_count:   int,
) -> str:
    """
    Assess the appropriate constitutional deployment state given current signals.

    Priority order (most restrictive first):
      AUTO_DISABLED         — CIL: cognitive overfitting + opportunity collapse both active
      CONSTITUTION_LOCKDOWN — autonomous drift ≥ 80 or governance instability ≥ 80
      HUMAN_REVIEW_REQUIRED — beneficial adaptation, memory health warning, or elevated risk
      SANDBOX_REPLAY        — governance conflicts or moderate drift/overfitting risk
      GUARDED_EXPERIMENT    — optimal: high confidence, no conflicts, drift below ceiling
      OBSERVATION_ONLY      — default baseline (no actionable signals)

    Research label only — not an execution authority.
    """
    drift_risk   = float((risk_diagnostics.get("autonomous_drift_risk",       {}) or {}).get("score", 0))
    overfit_risk = float((risk_diagnostics.get("overfitting_escalation_risk", {}) or {}).get("score", 0))
    gov_instab   = float((risk_diagnostics.get("governance_instability",      {}) or {}).get("score", 0))
    rec_conf     = float((risk_diagnostics.get("recommendation_confidence",   {}) or {}).get("score", 0))

    cog_overfit  = bool(cil_flags.get("cognitive_overfitting_detected",  False))
    opp_collapse = bool(cil_flags.get("opportunity_collapse_detected",   False))
    beneficial   = bool(cil_flags.get("beneficial_adaptation_detected",  False))

    if cog_overfit and opp_collapse:
        return AUTO_DISABLED

    if drift_risk >= LOCKDOWN_DRIFT_THRESHOLD or gov_instab >= LOCKDOWN_INSTAB_THRESHOLD:
        return CONSTITUTION_LOCKDOWN

    if (beneficial
            or cognitive_state in ("MEMORY_SATURATION", "PREMATURE_FOSSILIZATION")
            or overfit_risk >= REVIEW_OVERFIT_THRESHOLD
            or gov_instab >= REVIEW_INSTAB_THRESHOLD):
        return HUMAN_REVIEW_REQUIRED

    if conflict_count > 0 or drift_risk >= SANDBOX_DRIFT_THRESHOLD or overfit_risk >= SANDBOX_OVERFIT_THRESHOLD:
        return SANDBOX_REPLAY

    if rec_conf >= GUARDED_CONFIDENCE_THRESHOLD and conflict_count == 0 and drift_risk < GUARDED_DRIFT_CEILING:
        return GUARDED_EXPERIMENT

    return OBSERVATION_ONLY


# ── Constitutional classification ──────────────────────────────────────────────

def _classify_constitution(
    governance_state:  str,
    risk_diagnostics:  dict,
    conflict_count:    int,
) -> str:
    """
    Classify the constitutional health of the governance architecture.

    Priority order:
      LOCKDOWN_RECOMMENDED     — state is AUTO_DISABLED or CONSTITUTION_LOCKDOWN
      GOVERNANCE_FRAGMENTATION — ≥ 3 active cross-profile conflicts
      ADAPTIVE_DRIFT_RISK      — autonomous drift risk ≥ 70
      RECOMMENDATION_OVERREACH — overfitting ≥ 60 combined with recommendation confidence < 50
      OVERSIGHT_DEPENDENT      — governance instability ≥ 50 or drift risk ≥ 40
      CONSTITUTIONALLY_STABLE  — governance within acceptable operational bounds

    Research label only — not an execution authority.
    """
    if governance_state in (AUTO_DISABLED, CONSTITUTION_LOCKDOWN):
        return LOCKDOWN_RECOMMENDED

    if conflict_count >= FRAG_CONFLICT_THRESHOLD:
        return GOVERNANCE_FRAGMENTATION

    drift_risk = float((risk_diagnostics.get("autonomous_drift_risk", {}) or {}).get("score", 0))
    if drift_risk >= ADAPTIVE_DRIFT_RISK_THRESHOLD:
        return ADAPTIVE_DRIFT_RISK

    overfit_risk = float((risk_diagnostics.get("overfitting_escalation_risk", {}) or {}).get("score", 0))
    rec_conf     = float((risk_diagnostics.get("recommendation_confidence",   {}) or {}).get("score", 0))
    if overfit_risk >= OVERREACH_OVERFIT_THRESHOLD and rec_conf < OVERREACH_CONF_CEILING:
        return RECOMMENDATION_OVERREACH

    gov_instab = float((risk_diagnostics.get("governance_instability", {}) or {}).get("score", 0))
    if gov_instab >= OVERSIGHT_INSTAB_THRESHOLD or drift_risk >= OVERSIGHT_DRIFT_THRESHOLD:
        return OVERSIGHT_DEPENDENT

    return CONSTITUTIONALLY_STABLE


# ── Constitutional stability score ─────────────────────────────────────────────

def _constitutional_stability_score(
    risk_diagnostics: dict,
    governance_state: str,
) -> dict:
    """
    Overall constitutional health (0–100). Starts at 100 and subtracts risk deductions.
    Higher score = more constitutionally stable governance architecture.
    """
    drift_risk  = float((risk_diagnostics.get("autonomous_drift_risk",         {}) or {}).get("score", 0))
    overfit     = float((risk_diagnostics.get("overfitting_escalation_risk",   {}) or {}).get("score", 0))
    instab      = float((risk_diagnostics.get("governance_instability",        {}) or {}).get("score", 0))
    divergence  = float((risk_diagnostics.get("sandbox_production_divergence", {}) or {}).get("score", 0))

    score  = 100.0
    score -= drift_risk * 0.30
    score -= overfit    * 0.20
    score -= instab     * 0.20
    score -= divergence * 0.10

    state_penalty = {
        OBSERVATION_ONLY:      0.0,
        GUARDED_EXPERIMENT:    3.0,
        SANDBOX_REPLAY:        5.0,
        HUMAN_REVIEW_REQUIRED: 15.0,
        AUTO_DISABLED:         40.0,
        CONSTITUTION_LOCKDOWN: 50.0,
    }.get(governance_state, 0.0)
    score -= state_penalty

    score = round(max(0.0, min(100.0, score)), 1)
    return {"score": score, "tier": _stability_tier(score)}


# ── Recommendation generation ──────────────────────────────────────────────────

def _generate_recommendations(state: dict, governance_state: str) -> List[dict]:
    """
    Generate research-only adaptive proposals from CIL and GAGS findings.

    Each recommendation carries:
      type, priority, summary, evidence, action_required, auto_authorized.

    Constitutional guarantee: auto_authorized is ALWAYS False.
    System may recommend, explain, justify.
    System may NEVER self-activate, self-deploy, or self-authorize.
    """
    recs: List[dict] = []
    cil = state.get("counterfactual", {}) or {}
    gov = state.get("governance",     {}) or {}
    mem = state.get("memory_pressure",{}) or {}

    # ── CIL-sourced ───────────────────────────────────────────────────────────
    if cil.get("cognitive_overfitting_detected"):
        recs.append({
            "type":            "COGNITIVE_OVERFITTING_WARNING",
            "priority":        "CRITICAL",
            "summary":         (
                "Replay analysis detected cognitive overfitting — at least one intervention "
                "policy degrades learning plasticity significantly."
            ),
            "evidence":        {"source": "FTD-CIL", "flag": "cognitive_overfitting_detected"},
            "action_required": "IMMEDIATE_HUMAN_REVIEW",
            "auto_authorized": False,
        })

    if cil.get("opportunity_collapse_detected"):
        recs.append({
            "type":            "OPPORTUNITY_COLLAPSE_WARNING",
            "priority":        "HIGH",
            "summary":         (
                "One or more interventions collapse trade opportunity (>40% reduction) "
                "without proportional economic improvement."
            ),
            "evidence":        {"source": "FTD-CIL", "flag": "opportunity_collapse_detected"},
            "action_required": "HUMAN_REVIEW",
            "auto_authorized": False,
        })

    if cil.get("beneficial_adaptation_detected"):
        top = cil.get("top_intervention") or "unspecified"
        recs.append({
            "type":            "BENEFICIAL_INTERVENTION_IDENTIFIED",
            "priority":        "HIGH",
            "summary":         (
                f"Replay evidence suggests {top} improved net expectancy and survivability "
                "without significant opportunity cost. Human review and discretionary "
                "evaluation required before any consideration."
            ),
            "evidence":        {"source": "FTD-CIL", "top_intervention": top},
            "action_required": "HUMAN_REVIEW",
            "auto_authorized": False,
        })

    if cil.get("ontology_stabilization_detected"):
        recs.append({
            "type":            "ONTOLOGY_STABILIZATION_OPPORTUNITY",
            "priority":        "MEDIUM",
            "summary":         (
                "At least one intervention materially reduced explore/exploit belief "
                "divergence. May support cognitive coherence under human review."
            ),
            "evidence":        {"source": "FTD-CIL", "flag": "ontology_stabilization_detected"},
            "action_required": "OPTIONAL_REVIEW",
            "auto_authorized": False,
        })

    # ── GAGS-sourced ──────────────────────────────────────────────────────────
    conflict_count = int(
        ((gov.get("conflict_analysis", {}) or {}).get("conflict_count", 0)) or 0
    )
    if conflict_count > 0:
        recs.append({
            "type":            "GOVERNANCE_CONFLICT_DETECTED",
            "priority":        "HIGH",
            "summary":         (
                f"{conflict_count} governance profile conflict(s) detected — competing adaptive "
                "philosophies disagree on optimal policy stack. Human arbitration required "
                "before any policy is considered."
            ),
            "evidence":        {"source": "FTD-GAGS", "conflict_count": conflict_count},
            "action_required": "HUMAN_ARBITRATION_REQUIRED",
            "auto_authorized": False,
        })

    consensus = gov.get("consensus_compound")
    if consensus:
        recs.append({
            "type":            "GOVERNANCE_CONSENSUS_REACHED",
            "priority":        "MEDIUM",
            "summary":         (
                f"All governance profiles independently selected {consensus} as optimal "
                "compound policy. High-confidence research finding — human discretion "
                "required before any consideration."
            ),
            "evidence":        {"source": "FTD-GAGS", "consensus_compound": consensus},
            "action_required": "HUMAN_REVIEW",
            "auto_authorized": False,
        })

    # ── Memory-sourced ────────────────────────────────────────────────────────
    cognitive_state = str(mem.get("cognitive_state", "") or "")
    if cognitive_state == "MEMORY_SATURATION":
        recs.append({
            "type":            "MEMORY_SATURATION_ALERT",
            "priority":        "HIGH",
            "summary":         (
                "Multiple memory subsystems showing high agreement with low exploration — "
                "potential belief convergence ahead of evidence."
            ),
            "evidence":        {"source": "FTD-ONTOLOGY-DRIFT", "cognitive_state": cognitive_state},
            "action_required": "HUMAN_REVIEW",
            "auto_authorized": False,
        })
    elif cognitive_state == "PREMATURE_FOSSILIZATION":
        recs.append({
            "type":            "FOSSILIZATION_WARNING",
            "priority":        "HIGH",
            "summary":         (
                "Learning system exhibiting premature fossilisation — memory systems "
                "hardening before sufficient exploration evidence."
            ),
            "evidence":        {"source": "FTD-ONTOLOGY-DRIFT", "cognitive_state": cognitive_state},
            "action_required": "HUMAN_REVIEW",
            "auto_authorized": False,
        })

    # Health affirmation when no concerns found
    if not recs:
        recs.append({
            "type":            "CONSTITUTIONAL_HEALTH_AFFIRMATION",
            "priority":        "LOW",
            "summary":         (
                "No concerning signals detected across CIL, GAGS, or memory systems. "
                "Governance architecture within operational bounds."
            ),
            "evidence":        {"source": "FTD-GADD"},
            "action_required": "NONE",
            "auto_authorized": False,
        })

    return recs


# ── Immutable audit ledger ────────────────────────────────────────────────────

def _generate_audit_entry(
    governance_state:              str,
    constitutional_classification: str,
    risk_diagnostics:              dict,
    recommendations:               List[dict],
) -> dict:
    """
    Generate an immutable audit entry for this governance assessment.

    Constitutional guarantee: auto_authorized is ALWAYS False — the system
    never self-authorises. This entry must be appended by the caller to
    a session-scoped append-only ledger.
    """
    ts = int(_time.time() * 1000)

    risk_summary = {
        k: round(float((v or {}).get("score", 0)), 1)
        for k, v in risk_diagnostics.items()
        if isinstance(v, dict)
    }

    fingerprint_payload = json.dumps({
        "ts":    ts,
        "state": governance_state,
        "cls":   constitutional_classification,
        "risks": risk_summary,
    }, sort_keys=True)
    fingerprint = hashlib.sha256(fingerprint_payload.encode()).hexdigest()[:16]

    return {
        "entry_id":                      f"GADD-{ts}-{fingerprint}",
        "timestamp_ms":                  ts,
        "governance_state":              governance_state,
        "constitutional_classification": constitutional_classification,
        "risk_summary":                  risk_summary,
        "recommendations_generated":     len(recommendations),
        "human_approval_required":       governance_state != OBSERVATION_ONLY,
        "auto_authorized":               False,   # constitutional guarantee — never True
        "immutable":                     True,
    }


def _validate_audit_integrity(audit_ledger: list) -> dict:
    """
    Validate that the audit ledger preserves immutability guarantees.

    Any entry with auto_authorized=True represents a constitutional violation —
    the system must never self-authorise. INTACT = zero violations.
    """
    if not audit_ledger or not isinstance(audit_ledger, list):
        return {
            "depth":              0,
            "integrity":          "EMPTY",
            "autonomous_actions": 0,
            "violations":         [],
            "oldest_entry_id":    None,
            "latest_entry_id":    None,
        }

    violations: List[str] = []
    auto_count = 0
    for i, entry in enumerate(audit_ledger):
        if not isinstance(entry, dict):
            violations.append(f"Entry {i}: not a dict")
            continue
        if entry.get("auto_authorized") is True:
            violations.append(f"Entry {i}: auto_authorized=True (constitutional violation)")
            auto_count += 1
        if not entry.get("immutable"):
            violations.append(f"Entry {i}: immutable flag missing or False")

    return {
        "depth":              len(audit_ledger),
        "integrity":          "INTACT" if not violations else "VIOLATED",
        "autonomous_actions": auto_count,
        "violations":         violations,
        "oldest_entry_id":    audit_ledger[0].get("entry_id") if audit_ledger else None,
        "latest_entry_id":    audit_ledger[-1].get("entry_id") if audit_ledger else None,
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_governed_adaptive_doctrine(state: dict) -> dict:
    """
    Synthesise all PHOENIX adaptive analytics into a constitutional governance assessment.

    Expected `state` dict keys:
      "counterfactual":  output from compute_counterfactual_interventions (CIL)
      "governance":      output from compute_adaptive_governance (GAGS)
      "memory_pressure": output from compute_memory_pressure_dynamics
      "rl":              lightweight RL stats {explore_ratio, profitable_pct, total_contexts}
      "audit_ledger":    existing session-scoped audit entries (caller-maintained append-only list)

    All values are accessed defensively — missing or None values use safe defaults.

    Isolation guarantee: no live engine state read or written.
    Never raises — fail-open contract.
    All adaptive authority subordinate to explicit human governance.
    """
    SCOPE = (
        "FTD-GADD: Guarded Adaptive Deployment Doctrine & Human Override Constitution. "
        "Research instrumentation only — non-governing. "
        "Synthesises constitutional governance health across all PHOENIX adaptive subsystems. "
        "No production state is read or written. No execution behavior is altered. "
        "DO NOT enable autonomous deployment, self-authorised adaptation, or weakening of "
        "human override authority based on these outputs. "
        "All adaptive authority remains permanently subordinate to explicit human governance. "
        "PHOENIX must NEVER become sovereign over its own deployment authority. "
        "Not an execution authority. All decisions at developer discretion."
    )

    try:
        if not isinstance(state, dict):
            state = {}

        cil          = state.get("counterfactual",  {}) or {}
        gov          = state.get("governance",       {}) or {}
        mem          = state.get("memory_pressure",  {}) or {}
        audit_ledger = state.get("audit_ledger",     [])
        if not isinstance(audit_ledger, list):
            audit_ledger = []

        cognitive_state = str(mem.get("cognitive_state", "") or "")
        conflict_count  = int(
            ((gov.get("conflict_analysis", {}) or {}).get("conflict_count", 0)) or 0
        )

        # ── Risk diagnostics ─────────────────────────────────────────────────
        risk_diagnostics = _compute_risk_diagnostics(state, audit_ledger)

        # ── Governance state assessment ───────────────────────────────────────
        governance_state = _assess_governance_state(
            risk_diagnostics, cil, cognitive_state, conflict_count,
        )

        # ── Constitutional classification ─────────────────────────────────────
        constitution_class = _classify_constitution(
            governance_state, risk_diagnostics, conflict_count,
        )

        # ── Constitutional stability score ────────────────────────────────────
        stability_score = _constitutional_stability_score(risk_diagnostics, governance_state)

        # ── Research-only recommendations ─────────────────────────────────────
        recommendations = _generate_recommendations(state, governance_state)

        # ── Immutable audit entry ─────────────────────────────────────────────
        audit_entry = _generate_audit_entry(
            governance_state, constitution_class, risk_diagnostics, recommendations,
        )

        # ── Audit ledger integrity ────────────────────────────────────────────
        ledger_integrity = _validate_audit_integrity(audit_ledger)

        return {
            "scope_note":                    SCOPE,
            "governance_state":              governance_state,
            "governance_state_description":  GOVERNANCE_STATE_DESCRIPTIONS.get(governance_state, ""),
            "constitutional_classification": constitution_class,
            "constitutional_stability":      stability_score,
            "risk_diagnostics":              risk_diagnostics,
            "recommendations":               recommendations,
            "human_override_constitution":   HARD_PRINCIPLES,
            "audit_entry":                   audit_entry,
            "audit_ledger_depth":            len(audit_ledger),
            "audit_ledger_integrity":        ledger_integrity,
        }

    except Exception as exc:
        return {
            "scope_note": SCOPE,
            "error":      str(exc),
        }
