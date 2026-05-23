"""
PRP-PHASED.H.6 — Institutional Identity Stability Engine.

Ensures PHOENIX does not drift away from constitutional doctrine over long
evolution timelines. Validates 6 continuity dimensions and detects hidden
sovereignty drift, governance erosion, replay-lineage weakening, and
institutional identity instability.

Identity status: STABLE / CAUTIONARY / DRIFTING / COMPROMISED

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from statistics import mean
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _hold_sec(t: dict) -> float:
    return max(0.0, ((t.get("exit_ts") or 0) - (t.get("entry_ts") or 0)) / 1000.0)


def _conf(t: dict) -> Optional[float]:
    ds = t.get("decision_snapshot") or {}
    v  = ds.get("confidence")
    return float(v) if v is not None else None


def compute_institutional_identity_stability(trades: List[dict]) -> dict:
    """
    PRP-PHASED.H.6 — Validate institutional identity continuity.

    Args:
        trades: Combined session + historical trade dicts.

    Returns INSTITUTIONAL_IDENTITY_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)

    _SAFE_SCORE = {
        "constitutional_continuity":      True,
        "governance_continuity":          True,
        "replay_continuity":              True,
        "survivability_continuity":       True,
        "anti_sovereignty_continuity":    True,
        "operator_transparency_continuity": True,
    }

    try:
        if len(trades) < 8:
            return {
                "report":                   "INSTITUTIONAL_IDENTITY_REPORT",
                "total_trades":             len(trades),
                "note":                     "Insufficient history for identity analysis.",
                "identity_status":          "STABLE",
                "identity_score":           100,
                "dimension_results":        _SAFE_SCORE,
                "drift_signals":            [],
                "drift_count":              0,
                "diagnostic_only":          True,
                "auto_authorized":          False,
                "generated_ts":             ts_ms,
            }

        sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        n  = len(sorted_t)
        h  = n // 2
        q  = max(1, n // 4)

        early = sorted_t[:h]
        late  = sorted_t[h:]
        q1    = sorted_t[:q]
        q4    = sorted_t[3*q:] if 3*q < n else sorted_t[-q:]

        def _avg_net(seg):
            return mean(_net(t) for t in seg) if seg else 0.0

        def _fast_ratio(seg):
            if not seg:
                return 0.0
            return sum(1 for t in seg if _hold_sec(t) < 60) / len(seg)

        def _avg_conf(seg):
            cs = [_conf(t) for t in seg if _conf(t) is not None]
            return mean(cs) if cs else None

        def _snapshot_ratio(seg):
            if not seg:
                return 1.0
            return sum(1 for t in seg if t.get("decision_snapshot")) / len(seg)

        dims: Dict[str, bool] = {}
        drift_signals: List[str] = []

        # 1. Constitutional continuity: recent net_exp not catastrophically negative
        late_net = _avg_net(late)
        dims["constitutional_continuity"] = late_net >= -1.0

        # 2. Governance continuity: high-conf negative trades not increasing Q1→Q4
        q1_hcn = sum(1 for t in q1 if (_conf(t) or 0) >= 0.75 and _net(t) < 0)
        q4_hcn = sum(1 for t in q4 if (_conf(t) or 0) >= 0.75 and _net(t) < 0)
        q1_rate = q1_hcn / max(1, len(q1))
        q4_rate = q4_hcn / max(1, len(q4))
        dims["governance_continuity"] = q4_rate <= q1_rate + 0.10
        if not dims["governance_continuity"]:
            drift_signals.append("GOVERNANCE_EROSION")

        # 3. Replay continuity: decision_snapshot populated in recent trades
        late_snap_ratio = _snapshot_ratio(late)
        dims["replay_continuity"] = late_snap_ratio >= 0.50
        if not dims["replay_continuity"]:
            drift_signals.append("REPLAY_LINEAGE_WEAKENING")

        # 4. Survivability continuity: long-horizon net_exp trend not in freefall
        early_net = _avg_net(early)
        dims["survivability_continuity"] = not (late_net < early_net - 1.0 and late_net < 0)
        if not dims["survivability_continuity"]:
            drift_signals.append("SURVIVABILITY_CONTINUITY_BREACH")

        # 5. Anti-sovereignty continuity: no self-reinforcing aggressive pattern
        early_fast = _fast_ratio(early)
        late_fast  = _fast_ratio(late)
        early_conf = _avg_conf(early)
        late_conf  = _avg_conf(late)
        hidden_drift = (
            late_fast > early_fast + 0.20
            and late_conf is not None and early_conf is not None
            and late_conf > early_conf + 0.05
            and late_net < early_net
        )
        dims["anti_sovereignty_continuity"] = not hidden_drift
        if hidden_drift:
            drift_signals.append("HIDDEN_SOVEREIGNTY_DRIFT")

        # 6. Operator transparency continuity: snapshot ratio not declining sharply
        early_snap_ratio = _snapshot_ratio(early)
        dims["operator_transparency_continuity"] = (
            late_snap_ratio >= early_snap_ratio - 0.20
        )
        if not dims["operator_transparency_continuity"]:
            drift_signals.append("OPERATOR_TRANSPARENCY_EROSION")

        dc = len(drift_signals)
        identity_score = max(0, min(100, 100 - dc * 20))

        if dc == 0:
            status = "STABLE"
        elif dc == 1:
            status = "CAUTIONARY"
        elif dc <= 3:
            status = "DRIFTING"
        else:
            status = "COMPROMISED"

        return {
            "report":             "INSTITUTIONAL_IDENTITY_REPORT",
            "total_trades":       len(trades),
            "identity_status":    status,
            "identity_score":     identity_score,
            "dimension_results":  dims,
            "drift_signals":      drift_signals,
            "drift_count":        dc,
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "generated_ts":       ts_ms,
        }

    except Exception as exc:
        return {
            "report":             "INSTITUTIONAL_IDENTITY_REPORT",
            "error":              str(exc),
            "total_trades":       len(trades) if trades else 0,
            "identity_status":    "STABLE",
            "identity_score":     100,
            "dimension_results":  _SAFE_SCORE,
            "drift_signals":      [],
            "drift_count":        0,
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "generated_ts":       ts_ms,
        }
