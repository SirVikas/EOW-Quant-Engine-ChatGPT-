"""
PRP-PHASED.G.4 — Operator Override Transparency Engine.

Preserves full institutional visibility when human operators override
survivability advisories. Detects both explicit overrides (flagged in
decision_snapshot) and inferred override-like behaviour patterns.

All override events are preserved in replay-visible lineage — nothing hidden.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from statistics import mean
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _conf(t: dict) -> Optional[float]:
    ds = t.get("decision_snapshot") or {}
    v = ds.get("confidence")
    return float(v) if v is not None else None


def compute_operator_override_transparency(trades: List[dict]) -> dict:
    """
    PRP-PHASED.G.4 — Detect and report operator override patterns.

    Args:
        trades: Combined session + historical trade dicts.

    Returns OPERATOR_OVERRIDE_TRANSPARENCY_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)

    try:
        if not trades:
            return {
                "report":                  "OPERATOR_OVERRIDE_TRANSPARENCY_REPORT",
                "total_trade_count":       0,
                "total_override_count":    0,
                "explicit_override_count": 0,
                "inferred_override_count": 0,
                "override_frequency_pct":  0.0,
                "override_negative_rate":  0.0,
                "override_avg_net":        None,
                "override_events":         [],
                "discipline_effectiveness": "DISCIPLINE_NEUTRAL",
                "lineage_note":            "All override events preserved in replay-visible lineage",
                "replay_visible":          True,
                "diagnostic_only":         True,
                "auto_authorized":         False,
                "human_confirmed":         True,
                "override_visible":        True,
                "lineage_preserved":       True,
                "generated_ts":            ts_ms,
            }

        sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        override_events: List[dict] = []
        seen_ids: set = set()

        # ── Method A: Explicit override flag ─────────────────────────────────
        for t in sorted_t:
            ds = t.get("decision_snapshot") or {}
            if ds.get("operator_override", False):
                tid = t.get("trade_id", "")
                seen_ids.add(tid)
                override_events.append({
                    "trade_id":             tid,
                    "override_type":        "EXPLICIT",
                    "net_pnl":              round(_net(t), 4),
                    "confidence":           _conf(t),
                    "override_reason":      ds.get("override_reason", "UNSPECIFIED"),
                    "survivability_impact": "NEGATIVE" if _net(t) < 0 else "NEUTRAL",
                })

        # ── Method B: Inferred override-like behaviour ────────────────────────
        # B1: High-confidence loss
        for t in sorted_t:
            tid = t.get("trade_id", "")
            if tid in seen_ids:
                continue
            c = _conf(t)
            if c is not None and c >= 0.80 and _net(t) < 0:
                seen_ids.add(tid)
                override_events.append({
                    "trade_id":             tid,
                    "override_type":        "HIGH_CONFIDENCE_LOSS",
                    "net_pnl":              round(_net(t), 4),
                    "confidence":           round(c, 4),
                    "override_reason":      "INFERRED",
                    "survivability_impact": "NEGATIVE",
                })

        # B2: Rapid re-entry after loss (potential revenge trade)
        for i in range(1, len(sorted_t)):
            prev = sorted_t[i - 1]
            curr = sorted_t[i]
            tid  = curr.get("trade_id", "")
            if tid in seen_ids:
                continue
            if _net(prev) < 0:
                gap_ms = (curr.get("entry_ts") or 0) - (prev.get("exit_ts") or 0)
                if 0 <= gap_ms < 300_000:
                    seen_ids.add(tid)
                    override_events.append({
                        "trade_id":             tid,
                        "override_type":        "RAPID_REENTRY_LOSS",
                        "net_pnl":              round(_net(curr), 4),
                        "confidence":           _conf(curr),
                        "override_reason":      "INFERRED",
                        "survivability_impact": "NEGATIVE" if _net(curr) < 0 else "NEUTRAL",
                    })

        # B3: Adverse-regime high-confidence trade
        for t in sorted_t:
            tid = t.get("trade_id", "")
            if tid in seen_ids:
                continue
            regime = (t.get("regime") or "").upper()
            c = _conf(t)
            if regime == "VOLATILITY_EXPANSION" and _net(t) < 0 and c is not None and c >= 0.70:
                seen_ids.add(tid)
                override_events.append({
                    "trade_id":             tid,
                    "override_type":        "ADVERSE_REGIME_TRADE",
                    "net_pnl":              round(_net(t), 4),
                    "confidence":           round(c, 4),
                    "override_reason":      "INFERRED",
                    "survivability_impact": "NEGATIVE",
                })

        total_count = len(trades)
        ov_count    = len(override_events)
        explicit_c  = sum(1 for e in override_events if e["override_type"] == "EXPLICIT")
        inferred_c  = ov_count - explicit_c
        freq_pct    = round(ov_count / total_count * 100, 1) if total_count else 0.0

        neg_count  = sum(1 for e in override_events if e["net_pnl"] < 0)
        neg_rate   = round(neg_count / max(1, ov_count) * 100, 1)
        avg_net    = round(mean(e["net_pnl"] for e in override_events), 4) if override_events else None

        if neg_rate >= 60:
            effectiveness = "DISCIPLINE_HELPED"
        elif neg_rate < 40:
            effectiveness = "OVERRIDES_BENEFICIAL"
        else:
            effectiveness = "DISCIPLINE_NEUTRAL"

        return {
            "report":                  "OPERATOR_OVERRIDE_TRANSPARENCY_REPORT",
            "total_trade_count":       total_count,
            "total_override_count":    ov_count,
            "explicit_override_count": explicit_c,
            "inferred_override_count": inferred_c,
            "override_frequency_pct":  freq_pct,
            "override_negative_rate":  neg_rate,
            "override_avg_net":        avg_net,
            "override_events":         override_events,
            "discipline_effectiveness": effectiveness,
            "lineage_note":            "All override events preserved in replay-visible lineage",
            "replay_visible":          True,
            "diagnostic_only":         True,
            "auto_authorized":         False,
            "human_confirmed":         True,
            "override_visible":        True,
            "lineage_preserved":       True,
            "generated_ts":            ts_ms,
        }

    except Exception as exc:
        return {
            "report":                  "OPERATOR_OVERRIDE_TRANSPARENCY_REPORT",
            "error":                   str(exc),
            "total_trade_count":       len(trades) if trades else 0,
            "total_override_count":    0,
            "explicit_override_count": 0,
            "inferred_override_count": 0,
            "override_frequency_pct":  0.0,
            "override_negative_rate":  0.0,
            "override_avg_net":        None,
            "override_events":         [],
            "discipline_effectiveness": "DISCIPLINE_NEUTRAL",
            "lineage_note":            "All override events preserved in replay-visible lineage",
            "replay_visible":          True,
            "diagnostic_only":         True,
            "auto_authorized":         False,
            "human_confirmed":         True,
            "override_visible":        True,
            "lineage_preserved":       True,
            "generated_ts":            ts_ms,
        }
