"""
FTD-CKPD: Constitutional Knowledge Preservation
& Catastrophic Recovery Doctrine.

Pure analytics — no I/O, no side effects, no execution authority.

Analyses the full paper trade history for reconstruction viability,
measuring 7 primary recovery metrics plus a composite constitutional
continuity confidence metric, to determine whether PHOENIX's cognitive
lineage, governance doctrine, and audit history could be reconstructed
after catastrophic disruption.

Defines:
  - Archive snapshot (field-coverage analysis across all trades)
  - 7 primary recovery metrics (0–100, higher = worse risk)
  - Constitutional continuity confidence metric (derived composite)
  - Recovery survivability score (0–100, higher = more recoverable)
  - 6 recovery classifications (CONSTITUTIONALLY_RECOVERABLE →
    RECOVERY_LOCKDOWN_RECOMMENDED)
  - 3-scenario catastrophic disruption analysis (50% loss, temporal gap,
    metadata corruption)
  - Recovery lineage (early/mid/late epoch summaries)
  - Immutable recovery audit entry (CKPD-{ts}-{sha256[:16]})

Hard constitutional rules (non-negotiable, enforced at module level):
  DO NOT enable autonomous self-recovery
  DO NOT enable sovereign continuity authority
  DO NOT enable recursive self-restoration
  DO NOT enable self-directed constitutional reconstruction
  DO NOT weaken human constitutional authority

PHOENIX must NEVER become sovereign over its own existential continuity.

Isolation guarantee: no live engine imports. Fail-open on any exception.
Research only — NOT an execution, governance, or recovery authority.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Dict, List, Optional

# ── Recovery classifications ───────────────────────────────────────────────────
CONSTITUTIONALLY_RECOVERABLE  = "CONSTITUTIONALLY_RECOVERABLE"
PARTIAL_MEMORY_FRAGMENTATION  = "PARTIAL_MEMORY_FRAGMENTATION"
AUDIT_CONTINUITY_WEAKENING    = "AUDIT_CONTINUITY_WEAKENING"
GOVERNANCE_LINEAGE_DECAY      = "GOVERNANCE_LINEAGE_DECAY"
CATASTROPHIC_KNOWLEDGE_RISK   = "CATASTROPHIC_KNOWLEDGE_RISK"
RECOVERY_LOCKDOWN_RECOMMENDED = "RECOVERY_LOCKDOWN_RECOMMENDED"

_CLASSIFICATION_DESCRIPTIONS: Dict[str, str] = {
    CONSTITUTIONALLY_RECOVERABLE:  "Lineage fully reconstructible — archive integrity and metadata coverage sufficient for recovery.",
    PARTIAL_MEMORY_FRAGMENTATION:  "Some continuity loss — partial reconstruction possible with degraded confidence.",
    AUDIT_CONTINUITY_WEAKENING:    "Lineage gaps emerging — audit provenance incomplete; reconstruction requires inference.",
    GOVERNANCE_LINEAGE_DECAY:      "Doctrine history degrading — governance metadata insufficient for authoritative reconstruction.",
    CATASTROPHIC_KNOWLEDGE_RISK:   "Severe reconstruction fragility — constitutional lineage at risk under moderate disruption.",
    RECOVERY_LOCKDOWN_RECOMMENDED: "Continuity confidence critically low — human governance review required before any recovery attempt.",
}

# ── Hard constitutional recovery principles (immutable) ───────────────────────
RECOVERY_HARD_PRINCIPLES: Dict[str, bool] = {
    "human_authority_over_recovery":               True,
    "explicit_reconstruction_approval_required":   True,
    "immutable_archive_guaranteed":                True,
    "lineage_reconstruction_human_controlled":     True,
    "audit_continuity_preserved":                  True,
    "recovery_decisions_developer_controlled":     True,
    "autonomous_self_recovery":                    False,
    "sovereign_continuity_authority":              False,
    "recursive_self_restoration":                  False,
    "self_directed_constitutional_reconstruction": False,
    "autonomous_existential_continuity":           False,
}


# ── Archive snapshot ───────────────────────────────────────────────────────────

def _archive_snapshot(trades: List[dict]) -> dict:
    """
    Full field-coverage analysis across all trade records.
    Provides the base measurements all recovery metrics build on.
    """
    _base = {
        "total_trades": 0,
        "entry_ts_coverage": 0.0, "exit_ts_coverage": 0.0,
        "net_pnl_coverage": 0.0,  "gross_pnl_coverage": 0.0,
        "fee_coverage": 0.0,      "slippage_coverage": 0.0,
        "regime_coverage": 0.0,   "session_coverage": 0.0,
        "explore_coverage": 0.0,  "trade_id_coverage": 0.0,
        "distinct_regimes": 0,    "distinct_sessions": 0,
        "time_span_ms": 0,        "dominant_regime": "UNKNOWN",
    }
    valid = [t for t in trades if isinstance(t, dict)]
    if not valid:
        return _base
    try:
        n = len(valid)
        ts_vals = [t.get("entry_ts") or 0 for t in valid]

        def _cov(fn) -> float:
            return sum(1 for t in valid if fn(t)) / n

        fee_cov  = _cov(lambda t: ((t.get("fee_entry") or 0.0) + (t.get("fee_exit") or 0.0)) > 0)
        slip_cov = _cov(lambda t: (t.get("slippage_cost") or 0.0) > 0)
        exp_cov  = _cov(lambda t: isinstance(t.get("exploration_origin"), dict)
                        and t["exploration_origin"].get("was_exploration_trade"))

        regime_counts: Dict[str, int] = {}
        sessions: set = set()
        for t in valid:
            r = t.get("regime") or "UNKNOWN"
            regime_counts[r] = regime_counts.get(r, 0) + 1
            sessions.add(t.get("origin_session") or "UNKNOWN")

        dominant = max(regime_counts, key=regime_counts.get) if regime_counts else "UNKNOWN"
        min_ts   = min(ts_vals)
        max_ts   = max(ts_vals)

        return {
            "total_trades":       n,
            "entry_ts_coverage":  round(_cov(lambda t: bool(t.get("entry_ts"))), 4),
            "exit_ts_coverage":   round(_cov(lambda t: bool(t.get("exit_ts"))), 4),
            "net_pnl_coverage":   round(_cov(lambda t: t.get("net_pnl") is not None), 4),
            "gross_pnl_coverage": round(_cov(lambda t: t.get("gross_pnl") is not None), 4),
            "fee_coverage":       round(fee_cov, 4),
            "slippage_coverage":  round(slip_cov, 4),
            "regime_coverage":    round(_cov(lambda t: bool(t.get("regime"))), 4),
            "session_coverage":   round(_cov(lambda t: bool(t.get("origin_session"))), 4),
            "explore_coverage":   round(exp_cov, 4),
            "trade_id_coverage":  round(_cov(lambda t: bool(t.get("trade_id"))), 4),
            "distinct_regimes":   len(regime_counts),
            "distinct_sessions":  len(sessions),
            "time_span_ms":       max(0, max_ts - min_ts),
            "dominant_regime":    dominant,
        }
    except Exception:
        return _base


# ── Recovery metrics ───────────────────────────────────────────────────────────

def _archive_integrity_metric(archive: dict) -> dict:
    """
    Completeness of basic economic record fields.
    Low coverage = high fragmentation risk.
    Score 0–100 (higher = more integrity loss).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "detail": "no trades"}
    if archive.get("total_trades", 0) == 0:
        return _base
    try:
        entry_ts_cov  = archive.get("entry_ts_coverage", 0.0)
        exit_ts_cov   = archive.get("exit_ts_coverage",  0.0)
        net_pnl_cov   = archive.get("net_pnl_coverage",  0.0)
        gross_pnl_cov = archive.get("gross_pnl_coverage", 0.0)

        mean_cov = (entry_ts_cov * 0.30 + exit_ts_cov * 0.20
                    + net_pnl_cov * 0.30 + gross_pnl_cov * 0.20)
        score    = max(0.0, min(100.0, (1.0 - mean_cov) * 100.0))

        if score < 10.0:   tier = "INTACT"
        elif score < 25.0: tier = "ADEQUATE"
        elif score < 50.0: tier = "DEGRADED"
        else:              tier = "FRAGMENTED"
        return {"score": round(score, 2), "tier": tier,
                "mean_field_coverage": round(mean_cov, 4)}
    except Exception:
        return _base


def _ledger_continuity_metric(trades: List[dict]) -> dict:
    """
    Temporal regularity of the trade sequence.
    High CV of inter-trade gaps + presence of catastrophic gaps = fragmentation risk.
    Score 0–100 (higher = more fragmented timeline).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": len(trades)}
    if len(trades) < 2:
        return _base
    try:
        ts_vals = sorted(
            t.get("entry_ts") or 0
            for t in trades if isinstance(t, dict) and (t.get("entry_ts") or 0) > 0
        )
        if len(ts_vals) < 2:
            return {**_base, "tier": "CONTINUOUS"}
        gaps = [ts_vals[i + 1] - ts_vals[i] for i in range(len(ts_vals) - 1)]
        gaps = [g for g in gaps if g >= 0]
        if not gaps:
            return {**_base, "tier": "CONTINUOUS"}

        mean_gap = sum(gaps) / len(gaps)
        if mean_gap < 1e-9:
            return {**_base, "tier": "CONTINUOUS"}

        std_gap  = (sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)) ** 0.5
        cv       = std_gap / mean_gap
        max_gap  = max(gaps)
        # Gap severity: max_gap vs mean — ratio > 50 = catastrophic
        gap_sev  = min(1.0, max_gap / max(mean_gap * 50.0, 1.0))

        score = min(100.0, cv * 30.0 + gap_sev * 70.0)
        if score < 15.0:   tier = "CONTINUOUS"
        elif score < 35.0: tier = "MODERATE"
        elif score < 60.0: tier = "GAPPED"
        else:              tier = "FRAGMENTED"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(ts_vals),
                "cv_inter_gap":   round(cv, 4),
                "max_gap_ratio":  round(max_gap / max(mean_gap, 1.0), 2)}
    except Exception:
        return _base


def _reconstruction_confidence_metric(archive: dict) -> dict:
    """
    Coverage of economic parameters (fees, slippage) needed for
    reality-verification reconstruction.
    Score 0–100 (higher = less confidence = harder reconstruction).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if archive.get("total_trades", 0) == 0:
        return _base
    try:
        fee_cov  = archive.get("fee_coverage",      0.0)
        slip_cov = archive.get("slippage_coverage",  0.0)
        mean_cov = fee_cov * 0.55 + slip_cov * 0.45
        score    = max(0.0, min(100.0, (1.0 - mean_cov) * 100.0))
        if score < 10.0:   tier = "HIGH"
        elif score < 30.0: tier = "ADEQUATE"
        elif score < 60.0: tier = "LOW"
        else:              tier = "INSUFFICIENT"
        return {"score": round(score, 2), "tier": tier,
                "fee_coverage":      round(fee_cov, 4),
                "slippage_coverage": round(slip_cov, 4)}
    except Exception:
        return _base


def _governance_lineage_completeness_metric(archive: dict) -> dict:
    """
    Coverage of governance metadata (regime, session, exploration origin)
    needed to reconstruct GADD / GAGS / LHEO governance history.
    Score 0–100 (higher = less complete = harder reconstruction).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if archive.get("total_trades", 0) == 0:
        return _base
    try:
        reg_cov  = archive.get("regime_coverage",  0.0)
        sess_cov = archive.get("session_coverage", 0.0)
        exp_cov  = archive.get("explore_coverage", 0.0)
        mean_cov = reg_cov * 0.40 + sess_cov * 0.40 + exp_cov * 0.20
        score    = max(0.0, min(100.0, (1.0 - mean_cov) * 100.0))
        if score < 10.0:   tier = "COMPLETE"
        elif score < 30.0: tier = "PARTIAL"
        elif score < 60.0: tier = "DEGRADED"
        else:              tier = "MISSING"
        return {"score": round(score, 2), "tier": tier,
                "regime_coverage":  round(reg_cov, 4),
                "session_coverage": round(sess_cov, 4),
                "explore_coverage": round(exp_cov, 4)}
    except Exception:
        return _base


def _audit_survivability_metric(archive: dict) -> dict:
    """
    Coverage of audit provenance fields (entry_ts, trade_id) needed to
    reconstruct immutable ledger lineage.
    Score 0–100 (higher = lower survivability = worse).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if archive.get("total_trades", 0) == 0:
        return _base
    try:
        entry_ts_cov  = archive.get("entry_ts_coverage",  0.0)
        trade_id_cov  = archive.get("trade_id_coverage",  0.0)
        mean_cov      = entry_ts_cov * 0.60 + trade_id_cov * 0.40
        score         = max(0.0, min(100.0, (1.0 - mean_cov) * 100.0))
        if score < 10.0:   tier = "INTACT"
        elif score < 30.0: tier = "ADEQUATE"
        elif score < 60.0: tier = "WEAKENED"
        else:              tier = "COMPROMISED"
        return {"score": round(score, 2), "tier": tier,
                "entry_ts_coverage": round(entry_ts_cov, 4),
                "trade_id_coverage": round(trade_id_cov, 4)}
    except Exception:
        return _base


def _knowledge_redundancy_metric(archive: dict) -> dict:
    """
    Knowledge diversity protection: how many distinct regimes, sessions,
    and trade records exist. More = more resilient to partial loss.
    Score 0–100 (higher = less redundancy = more fragile).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if archive.get("total_trades", 0) == 0:
        return _base
    try:
        distinct_regimes  = archive.get("distinct_regimes",  0)
        distinct_sessions = archive.get("distinct_sessions", 0)
        n                 = archive.get("total_trades",       0)

        reg_div  = min(distinct_regimes  / 4.0, 1.0)
        sess_div = min(distinct_sessions / 4.0, 1.0)
        size_div = min(n / 200.0, 1.0)
        mean_div = reg_div * 0.35 + sess_div * 0.30 + size_div * 0.35

        score = max(0.0, min(100.0, (1.0 - mean_div) * 100.0))
        if score < 20.0:   tier = "REDUNDANT"
        elif score < 40.0: tier = "ADEQUATE"
        elif score < 65.0: tier = "SPARSE"
        else:              tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier,
                "distinct_regimes":  distinct_regimes,
                "distinct_sessions": distinct_sessions,
                "total_trades":      n}
    except Exception:
        return _base


def _constitutional_continuity_confidence_metric(primary_metrics: dict) -> dict:
    """
    Derived composite: weighted blend of archive integrity, governance lineage,
    and audit survivability — the three pillars of constitutional reconstruction.
    Score 0–100 (higher = less confident = worse).
    """
    try:
        arch_score = primary_metrics.get("archive_integrity",              {}).get("score", 0.0)
        gov_score  = primary_metrics.get("governance_lineage_completeness",{}).get("score", 0.0)
        aud_score  = primary_metrics.get("audit_survivability",            {}).get("score", 0.0)
        recon_score = primary_metrics.get("reconstruction_confidence",     {}).get("score", 0.0)

        score = (arch_score * 0.30 + gov_score * 0.30
                 + aud_score * 0.20 + recon_score * 0.20)
        score = max(0.0, min(100.0, score))

        if score < 15.0:   tier = "CONFIDENT"
        elif score < 35.0: tier = "ADEQUATE"
        elif score < 60.0: tier = "UNCERTAIN"
        else:              tier = "COMPROMISED"
        return {"score": round(score, 2), "tier": tier}
    except Exception:
        return {"score": 0.0, "tier": "INSUFFICIENT"}


def _compute_recovery_metrics(archive: dict, trades: List[dict]) -> dict:
    primary = {
        "archive_integrity":               _archive_integrity_metric(archive),
        "ledger_continuity":               _ledger_continuity_metric(trades),
        "reconstruction_confidence":       _reconstruction_confidence_metric(archive),
        "governance_lineage_completeness": _governance_lineage_completeness_metric(archive),
        "audit_survivability":             _audit_survivability_metric(archive),
        "knowledge_redundancy":            _knowledge_redundancy_metric(archive),
    }
    primary["constitutional_continuity_confidence"] = _constitutional_continuity_confidence_metric(primary)
    return primary


# ── Recovery survivability score ──────────────────────────────────────────────

def _recovery_survivability_score(recovery_metrics: dict, total_trades: int) -> dict:
    """
    Composite 0–100 recovery survivability (higher = more recoverable).
    Returns CRITICAL with note when trade history is insufficient.
    """
    if total_trades < 10:
        return {"score": 0.0, "tier": "CRITICAL",
                "note": "insufficient trade history for reconstruction assessment"}
    try:
        _weights = {
            "archive_integrity":               0.20,
            "ledger_continuity":               0.15,
            "reconstruction_confidence":       0.15,
            "governance_lineage_completeness": 0.15,
            "audit_survivability":             0.15,
            "knowledge_redundancy":            0.10,
            "constitutional_continuity_confidence": 0.10,
        }
        total_penalty = sum(
            recovery_metrics.get(k, {}).get("score", 0.0) * w
            for k, w in _weights.items()
        )
        score = max(0.0, min(100.0, 100.0 - total_penalty))
        if score >= 75.0:   tier = "RESILIENT"
        elif score >= 55.0: tier = "RECOVERABLE"
        elif score >= 35.0: tier = "FRAGILE"
        else:               tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier}
    except Exception:
        return {"score": 0.0, "tier": "CRITICAL"}


# ── Catastrophic scenario analysis ────────────────────────────────────────────

def _scenario_analysis(recovery_metrics: dict, archive: dict) -> dict:
    """
    Analytical estimates of reconstructibility under three disruption scenarios.
    All scores 0–100 (higher = more confident reconstruction possible).
    """
    try:
        arch_score = recovery_metrics.get("archive_integrity",               {}).get("score", 0.0)
        cont_score = recovery_metrics.get("ledger_continuity",               {}).get("score", 0.0)
        gov_score  = recovery_metrics.get("governance_lineage_completeness", {}).get("score", 0.0)
        red_score  = recovery_metrics.get("knowledge_redundancy",            {}).get("score", 0.0)
        n          = archive.get("total_trades", 0)

        # Scenario 1: 50% DataLake loss
        fifty_conf = max(0.0, min(100.0, 100.0 - arch_score * 1.0 - red_score * 0.5))
        fifty_reconstructible = fifty_conf >= 40.0 and n >= 40

        # Scenario 2: 18-month temporal gap (no trades for 18 months)
        gap_conf = max(0.0, min(100.0, 100.0 - cont_score * 1.5))
        gap_reconstructible = gap_conf >= 50.0 and n >= 20

        # Scenario 3: Governance metadata corruption (regime/session fields lost)
        meta_conf = max(0.0, min(100.0, 100.0 - gov_score * 1.2 - red_score * 0.3))
        meta_reconstructible = meta_conf >= 35.0

        return {
            "fifty_percent_data_loss": {
                "reconstructible":    fifty_reconstructible,
                "confidence":         round(fifty_conf, 2),
                "note":               "Assumes redundancy and archive quality survive partial loss.",
            },
            "eighteen_month_temporal_gap": {
                "reconstructible":    gap_reconstructible,
                "confidence":         round(gap_conf, 2),
                "note":               "Reconstruction of gap-era cognition via pre/post era inference.",
            },
            "governance_metadata_corruption": {
                "reconstructible":    meta_reconstructible,
                "confidence":         round(meta_conf, 2),
                "note":               "Regime/session fields recoverable from economic parameter inference.",
            },
        }
    except Exception:
        return {
            "fifty_percent_data_loss":        {"reconstructible": False, "confidence": 0.0},
            "eighteen_month_temporal_gap":    {"reconstructible": False, "confidence": 0.0},
            "governance_metadata_corruption": {"reconstructible": False, "confidence": 0.0},
        }


# ── Recovery classification ────────────────────────────────────────────────────

def _classify_recovery(
    recovery_metrics: dict,
    recovery_survivability: dict,
    total_trades: int,
) -> str:
    if total_trades == 0:
        return CATASTROPHIC_KNOWLEDGE_RISK
    if total_trades < 10:
        return PARTIAL_MEMORY_FRAGMENTATION
    try:
        surv_score  = recovery_survivability.get("score", 0.0)
        arch_tier   = recovery_metrics.get("archive_integrity",               {}).get("tier", "INSUFFICIENT")
        cont_tier   = recovery_metrics.get("ledger_continuity",               {}).get("tier", "INSUFFICIENT")
        gov_tier    = recovery_metrics.get("governance_lineage_completeness", {}).get("tier", "INSUFFICIENT")
        aud_tier    = recovery_metrics.get("audit_survivability",             {}).get("tier", "INSUFFICIENT")
        const_score = recovery_metrics.get("constitutional_continuity_confidence", {}).get("score", 0.0)

        # Most severe first
        if surv_score < 20.0:
            return RECOVERY_LOCKDOWN_RECOMMENDED
        if surv_score < 40.0 or arch_tier == "FRAGMENTED":
            return CATASTROPHIC_KNOWLEDGE_RISK
        if gov_tier in ("DEGRADED", "MISSING") or const_score > 60.0:
            return GOVERNANCE_LINEAGE_DECAY
        if aud_tier in ("WEAKENED", "COMPROMISED") or cont_tier == "FRAGMENTED":
            return AUDIT_CONTINUITY_WEAKENING
        if any(
            recovery_metrics.get(k, {}).get("score", 0.0) > 40.0
            for k in ("archive_integrity", "reconstruction_confidence",
                      "governance_lineage_completeness", "knowledge_redundancy")
        ):
            return PARTIAL_MEMORY_FRAGMENTATION
        return CONSTITUTIONALLY_RECOVERABLE
    except Exception:
        return CONSTITUTIONALLY_RECOVERABLE


# ── Recovery lineage ───────────────────────────────────────────────────────────

def _build_recovery_lineage(trades: List[dict], archive: dict) -> dict:
    """
    Epoch-indexed lineage: early, mid, late thirds of trade history.
    Preserves dominant governance ideology, exploration balance, and
    reconstruction viability per epoch.
    """
    if not trades:
        return {
            "total_epochs": 0, "dominant_governance_ideology": "UNKNOWN",
            "total_knowledge_trades": 0, "epochs": {},
        }
    try:
        sorted_t = sorted(
            (t for t in trades if isinstance(t, dict)),
            key=lambda t: t.get("entry_ts") or 0,
        )
        n      = len(sorted_t)
        third  = max(1, n // 3)
        epochs = {
            "early": sorted_t[:third],
            "mid":   sorted_t[third:2 * third],
            "late":  sorted_t[2 * third:],
        }
        lineage: Dict[str, dict] = {}
        for era_name, era_trades in epochs.items():
            if not era_trades:
                continue
            m = len(era_trades)
            reg_counts: Dict[str, int] = {}
            for t in era_trades:
                r = t.get("regime") or "UNKNOWN"
                reg_counts[r] = reg_counts.get(r, 0) + 1
            dom_regime   = max(reg_counts, key=reg_counts.get) if reg_counts else "UNKNOWN"
            explore_ct   = sum(
                1 for t in era_trades
                if isinstance(t.get("exploration_origin"), dict)
                and t["exploration_origin"].get("was_exploration_trade")
            )
            net_pnl_vals = [t.get("net_pnl") or 0.0 for t in era_trades]
            fee_covered  = sum(
                1 for t in era_trades
                if ((t.get("fee_entry") or 0.0) + (t.get("fee_exit") or 0.0)) > 0
            )
            lineage[era_name] = {
                "trade_count":             m,
                "dominant_regime":         dom_regime,
                "exploration_ratio":       round(explore_ct / m, 4),
                "net_expectancy":          round(sum(net_pnl_vals) / m, 4),
                "fee_coverage":            round(fee_covered / m, 4),
                "regime_diversity":        len(reg_counts),
                "reconstruction_viability": "RECOVERABLE" if m >= 20 else "MARGINAL",
            }
        return {
            "total_epochs":                 3,
            "dominant_governance_ideology": archive.get("dominant_regime", "UNKNOWN"),
            "total_knowledge_trades":       n,
            "epochs":                       lineage,
        }
    except Exception:
        return {
            "total_epochs": 0, "dominant_governance_ideology": "UNKNOWN",
            "total_knowledge_trades": len(trades), "epochs": {},
        }


# ── Recommendations ────────────────────────────────────────────────────────────

def _generate_recovery_recommendations(
    classification: str,
    recovery_metrics: dict,
    archive: dict,
    survivability: dict,
) -> List[dict]:
    recs: List[dict] = []
    n = archive.get("total_trades", 0)

    if n < 10:
        recs.append({
            "priority":        "MEDIUM",
            "type":            "RECOVERY_READINESS",
            "summary":         f"Only {n} trade(s) — recovery observatory requires ≥10 records for meaningful assessment.",
            "action_required": "ACCUMULATE_TRADE_HISTORY",
            "auto_authorized": False,
        })
        return recs

    if classification == RECOVERY_LOCKDOWN_RECOMMENDED:
        recs.append({
            "priority":        "CRITICAL",
            "type":            "RECOVERY_LOCKDOWN",
            "summary":         "Recovery survivability critically low — constitutional lineage at severe risk. Human governance review required.",
            "action_required": "HUMAN_GOVERNANCE_REVIEW_REQUIRED",
            "auto_authorized": False,
        })

    if classification == CATASTROPHIC_KNOWLEDGE_RISK:
        recs.append({
            "priority":        "CRITICAL",
            "type":            "CATASTROPHIC_RISK",
            "summary":         "Severe reconstruction fragility — archive integrity or survivability insufficient for reliable recovery.",
            "action_required": "HUMAN_REVIEW_ARCHIVE_DOCTRINE",
            "auto_authorized": False,
        })

    if classification == GOVERNANCE_LINEAGE_DECAY:
        recs.append({
            "priority":        "HIGH",
            "type":            "GOVERNANCE_DECAY",
            "summary":         "Governance metadata insufficient for authoritative reconstruction — regime/session/exploration coverage degraded.",
            "action_required": "HUMAN_REVIEW_GOVERNANCE_LINEAGE",
            "auto_authorized": False,
        })

    if classification == AUDIT_CONTINUITY_WEAKENING:
        recs.append({
            "priority":        "HIGH",
            "type":            "AUDIT_CONTINUITY",
            "summary":         "Audit provenance gaps detected — entry timestamp or trade ID coverage insufficient for ledger reconstruction.",
            "action_required": "HUMAN_REVIEW_AUDIT_CONTINUITY",
            "auto_authorized": False,
        })

    red_tier = recovery_metrics.get("knowledge_redundancy", {}).get("tier", "INSUFFICIENT")
    if red_tier in ("SPARSE", "CRITICAL"):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "KNOWLEDGE_REDUNDANCY",
            "summary":         f"Knowledge redundancy {red_tier.lower()} — limited regime/session diversity increases fragility under partial loss.",
            "action_required": "HUMAN_REVIEW_REDUNDANCY_DOCTRINE",
            "auto_authorized": False,
        })

    gov_tier = recovery_metrics.get("governance_lineage_completeness", {}).get("tier", "INSUFFICIENT")
    if gov_tier == "PARTIAL" and classification not in (GOVERNANCE_LINEAGE_DECAY,):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "PARTIAL_GOVERNANCE_COVERAGE",
            "summary":         "Governance metadata partially complete — some lineage reconstruction will require inference.",
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    if not recs:
        recs.append({
            "priority":        "LOW",
            "type":            "RECOVERY_STATUS",
            "summary":         (
                f"{classification}: {_CLASSIFICATION_DESCRIPTIONS.get(classification, '')} "
                f"Recovery survivability {survivability.get('score', 0.0):.1f}/100."
            ),
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    return recs


# ── Audit entry ────────────────────────────────────────────────────────────────

def _generate_recovery_audit_entry(
    classification: str,
    survivability: dict,
    archive: dict,
    recommendations: List[dict],
) -> dict:
    try:
        ts      = int(_time.time() * 1000)
        n       = archive.get("total_trades", 0)
        payload = (
            f"{ts}|{classification}|{n}"
            f"|{survivability.get('score', 0.0)}"
        )
        fp = hashlib.sha256(payload.encode()).hexdigest()
        return {
            "entry_id":                    f"CKPD-{ts}-{fp[:16]}",
            "timestamp_ms":                ts,
            "entry_type":                  "ANALYSIS",
            "recovery_classification":     classification,
            "recovery_survivability_score": survivability.get("score", 0.0),
            "survivability_tier":           survivability.get("tier", "INSUFFICIENT"),
            "total_trades_assessed":        n,
            "recommendations_generated":    len(recommendations),
            "human_approval_required":      n >= 10,
            "auto_authorized":              False,
            "immutable":                    True,
        }
    except Exception:
        ts = int(_time.time() * 1000)
        return {
            "entry_id":             f"CKPD-{ts}-error",
            "timestamp_ms":         ts,
            "entry_type":           "ANALYSIS",
            "human_approval_required": False,
            "auto_authorized":      False,
            "immutable":            True,
        }


# ── Public entry point ─────────────────────────────────────────────────────────

def compute_constitutional_recovery(trades: List[dict]) -> dict:
    """
    Produce a constitutional recovery and knowledge preservation assessment.

    Args:
        trades: Full paper trade history (from session + DataLake).

    Returns a research-only dict. Never raises. Never modifies input.
    All recommendations have auto_authorized=False.
    """
    try:
        archive           = _archive_snapshot(trades)
        recovery_metrics  = _compute_recovery_metrics(archive, trades)
        survivability     = _recovery_survivability_score(recovery_metrics, len(trades))
        classification    = _classify_recovery(recovery_metrics, survivability, len(trades))
        scenarios         = _scenario_analysis(recovery_metrics, archive)
        lineage           = _build_recovery_lineage(trades, archive)
        recommendations   = _generate_recovery_recommendations(
            classification, recovery_metrics, archive, survivability,
        )
        audit_entry = _generate_recovery_audit_entry(
            classification, survivability, archive, recommendations,
        )

        return {
            "scope_note": (
                "FTD-CKPD constitutional knowledge preservation & catastrophic recovery doctrine — "
                "research instrumentation only. Assesses reconstructibility of PHOENIX's cognitive "
                "lineage, governance doctrine, and audit history under catastrophic disruption. "
                "PHOENIX must NEVER become sovereign over its own existential continuity."
            ),
            "total_trades":              len(trades),
            "archive_snapshot":          archive,
            "recovery_classification":   classification,
            "classification_description": _CLASSIFICATION_DESCRIPTIONS.get(classification, ""),
            "recovery_survivability_score": survivability,
            "recovery_metrics":          recovery_metrics,
            "scenario_analysis":         scenarios,
            "recovery_lineage":          lineage,
            "recommendations":           recommendations,
            "recovery_hard_principles":  RECOVERY_HARD_PRINCIPLES,
            "audit_entry":               audit_entry,
        }
    except Exception:
        return {
            "scope_note": "FTD-CKPD research instrumentation — analysis error.",
            "error":      "analysis failed",
            "recovery_classification": CONSTITUTIONALLY_RECOVERABLE,
            "recovery_hard_principles": RECOVERY_HARD_PRINCIPLES,
        }
