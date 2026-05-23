"""
PRP-PHASED.G.5 — Execution Discipline Memory Engine.

Builds historical memory of disciplined vs emotional execution behaviour.
Tracks revenge-trading episodes, impulsive spikes, and disciplined runs to
identify when restraint preserved survivability and when emotional overrides
accelerated degradation.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from statistics import mean, stdev
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def compute_execution_discipline_memory(trades: List[dict]) -> dict:
    """
    PRP-PHASED.G.5 — Analyse historical execution discipline patterns.

    Args:
        trades: Combined session + historical trade dicts.

    Returns EXECUTION_DISCIPLINE_MEMORY_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)

    try:
        if not trades:
            return {
                "report":                      "EXECUTION_DISCIPLINE_MEMORY_REPORT",
                "total_trades":                0,
                "discipline_score":            50,
                "discipline_tier":             "ADEQUATE",
                "revenge_episode_count":       0,
                "revenge_episodes":            [],
                "impulsive_spike_count":       0,
                "impulsive_spikes":            [],
                "discipline_periods_count":    0,
                "disciplined_trade_count":     0,
                "undisciplined_trade_count":   0,
                "discipline_effectiveness":    "MIXED_EVIDENCE",
                "conditions_discipline_helped":  [],
                "conditions_overrides_degraded": [],
                "diagnostic_only":             True,
                "auto_authorized":             False,
                "human_confirmed":             True,
                "lineage_preserved":           True,
                "generated_ts":                ts_ms,
            }

        sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))

        # ── Revenge trading episodes ──────────────────────────────────────────
        revenge_episodes: List[dict] = []
        for i in range(1, len(sorted_t)):
            prev = sorted_t[i - 1]
            curr = sorted_t[i]
            if _net(prev) < 0:
                gap_ms = (curr.get("entry_ts") or 0) - (prev.get("exit_ts") or 0)
                if 0 <= gap_ms < 300_000:
                    revenge_episodes.append({
                        "trade_id":    curr.get("trade_id", ""),
                        "gap_seconds": round(gap_ms / 1000, 1),
                        "net_pnl":     round(_net(curr), 4),
                    })

        # ── Impulsive participation spikes (non-overlapping 60-min windows) ───
        impulsive_spikes: List[dict] = []
        if sorted_t:
            window_ms  = 3_600_000
            first_ts   = sorted_t[0].get("entry_ts", 0) or 0
            last_ts    = sorted_t[-1].get("entry_ts", 0) or 0
            win_start  = first_ts
            while win_start <= last_ts:
                win_end = win_start + window_ms
                window_trades = [
                    t for t in sorted_t
                    if (t.get("entry_ts") or 0) >= win_start
                    and (t.get("entry_ts") or 0) < win_end
                ]
                if len(window_trades) >= 5:
                    avg_net = round(mean(_net(t) for t in window_trades), 4)
                    impulsive_spikes.append({
                        "window_start_ts": win_start,
                        "trade_count":     len(window_trades),
                        "avg_net":         avg_net,
                    })
                win_start += window_ms

        neg_spikes = [s for s in impulsive_spikes if s["avg_net"] < 0]

        # ── Discipline periods (5+ consecutive positive trades) ───────────────
        discipline_runs: List[int] = []
        run_len = 0
        for t in sorted_t:
            if _net(t) > 0:
                run_len += 1
            else:
                if run_len >= 5:
                    discipline_runs.append(run_len)
                run_len = 0
        if run_len >= 5:
            discipline_runs.append(run_len)

        disciplined_trade_count = sum(discipline_runs)

        # Undisciplined: trades in revenge episodes + impulsive spikes (by id)
        undisciplined_ids: set = set()
        for ep in revenge_episodes:
            undisciplined_ids.add(ep["trade_id"])
        for spike in neg_spikes:
            ws = spike["window_start_ts"]
            we = ws + 3_600_000
            for t in sorted_t:
                if (t.get("entry_ts") or 0) >= ws and (t.get("entry_ts") or 0) < we:
                    undisciplined_ids.add(t.get("trade_id", ""))
        undisciplined_trade_count = len(undisciplined_ids)

        if disciplined_trade_count > undisciplined_trade_count:
            effectiveness = "DISCIPLINE_PRESERVED_SURVIVABILITY"
        elif disciplined_trade_count == undisciplined_trade_count:
            effectiveness = "MIXED_EVIDENCE"
        else:
            effectiveness = "EMOTIONAL_OVERRIDES_DOMINATED"

        # ── Narrative conditions ──────────────────────────────────────────────
        helped: List[str] = []
        for run in discipline_runs:
            helped.append(
                f"Consecutive positive run of {run} trades — disciplined participation preserved edge"
            )

        degraded: List[str] = []
        if revenge_episodes:
            avg_gap = mean(ep["gap_seconds"] for ep in revenge_episodes)
            degraded.append(
                f"Revenge trading detected: {len(revenge_episodes)} episodes with avg gap "
                f"{avg_gap:.0f}s — rapid re-entry after losses accelerated degradation"
            )
        if neg_spikes:
            degraded.append(
                f"Impulsive spikes detected: {len(neg_spikes)} windows with negative expectancy "
                "— rushed participation degraded edge"
            )

        # ── Discipline score ──────────────────────────────────────────────────
        score = 50
        if len(discipline_runs) >= 2:
            score += 25
        if not revenge_episodes:
            score += 15
        if len(revenge_episodes) >= 3:
            score -= 20
        if len(neg_spikes) >= 2:
            score -= 15
        score = max(0, min(100, score))

        if score >= 70:
            tier = "DISCIPLINED"
        elif score >= 50:
            tier = "ADEQUATE"
        elif score >= 30:
            tier = "IMPULSIVE"
        else:
            tier = "UNCONTROLLED"

        return {
            "report":                        "EXECUTION_DISCIPLINE_MEMORY_REPORT",
            "total_trades":                  len(trades),
            "discipline_score":              score,
            "discipline_tier":               tier,
            "revenge_episode_count":         len(revenge_episodes),
            "revenge_episodes":              revenge_episodes,
            "impulsive_spike_count":         len(impulsive_spikes),
            "impulsive_spikes":              impulsive_spikes,
            "discipline_periods_count":      len(discipline_runs),
            "disciplined_trade_count":       disciplined_trade_count,
            "undisciplined_trade_count":     undisciplined_trade_count,
            "discipline_effectiveness":      effectiveness,
            "conditions_discipline_helped":  helped,
            "conditions_overrides_degraded": degraded,
            "diagnostic_only":               True,
            "auto_authorized":               False,
            "human_confirmed":               True,
            "lineage_preserved":             True,
            "generated_ts":                  ts_ms,
        }

    except Exception as exc:
        return {
            "report":                        "EXECUTION_DISCIPLINE_MEMORY_REPORT",
            "error":                         str(exc),
            "total_trades":                  len(trades) if trades else 0,
            "discipline_score":              50,
            "discipline_tier":               "ADEQUATE",
            "revenge_episode_count":         0,
            "revenge_episodes":              [],
            "impulsive_spike_count":         0,
            "impulsive_spikes":              [],
            "discipline_periods_count":      0,
            "disciplined_trade_count":       0,
            "undisciplined_trade_count":     0,
            "discipline_effectiveness":      "MIXED_EVIDENCE",
            "conditions_discipline_helped":  [],
            "conditions_overrides_degraded": [],
            "diagnostic_only":               True,
            "auto_authorized":               False,
            "human_confirmed":               True,
            "lineage_preserved":             True,
            "generated_ts":                  ts_ms,
        }
