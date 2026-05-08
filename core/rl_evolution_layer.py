"""
EOW Quant Engine — RL Evolution Layer  (FTD-RL-EVOLUTION / Section E)

Standalone observability module that surfaces the RL engine's learning
evolution for runtime logs, diagnostic bundles, and future dashboard panels.

Design principles:
  • READ-ONLY  — zero mutation of any engine state
  • NON-BLOCKING — all analysis is synchronous, safe to call from any context
  • ADDITIVE   — does not change trading logic; pure analytics layer
  • LIGHTWEIGHT — no ML dependencies, no external state, fast execution

Outputs:
  - Learning speed report (context maturity distribution)
  - Adaptation rate (Q-velocity per context)
  - Context maturity scoring (0–100)
  - Intelligence evolution score (0–100 composite)
  - Confidence growth trajectory
  - Exploration pressure diagnostics
  - Strategy dominance ranking
  - Toxicity detection summary
  - Regime adaptation quality
  - Session intelligence breakdown

Integration:
  Called from diagnostics endpoints, thought logs, and build_package().
  The singleton rl_evolution_layer is available for direct use.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from loguru import logger


class RLEvolutionLayer:
    """
    Read-only analytics wrapper over RLContextualBandit.
    Provides detailed evolution observability without affecting trade logic.
    """

    MODULE  = "RL_EVOLUTION_LAYER"
    VERSION = "1.0"

    # ── Public API ────────────────────────────────────────────────────────────

    def compute_learning_snapshot(self, rl_engine_instance: Any) -> Dict[str, Any]:
        """
        Full evolution analytics snapshot.
        Returns structured dict suitable for logs, diagnostics, and dashboards.
        """
        if rl_engine_instance is None:
            return {"module": self.MODULE, "error": "rl_engine not provided"}

        try:
            # Prefer the engine's own evolution state if available (v2.0+)
            if hasattr(rl_engine_instance, "get_evolution_state"):
                evo = rl_engine_instance.get_evolution_state()
            else:
                evo = {}

            summary = {}
            try:
                summary = rl_engine_instance.summary()
            except Exception:
                pass

            table     = getattr(rl_engine_instance, "_table", {})
            n_total   = len(table)
            total_pulls = int(getattr(rl_engine_instance, "_total_pulls", 0))

            # ── Learning speed indicators ──────────────────────────────────
            speed_report = self._learning_speed_report(table)

            # ── Confidence growth trajectory ───────────────────────────────
            confidence_trajectory = self._confidence_trajectory(table)

            # ── Exploration pressure ───────────────────────────────────────
            explore_pressure = self._exploration_pressure(rl_engine_instance)

            # ── Strategy dominance ─────────────────────────────────────────
            strategy_dominance = self._strategy_dominance(table)

            # ── Regime adaptation quality ──────────────────────────────────
            regime_adaptation = self._regime_adaptation(table)

            return {
                "module":                self.MODULE,
                "version":               self.VERSION,
                "snapshot_ts":           int(time.time() * 1000),
                "total_contexts":        n_total,
                "total_trade_decisions": total_pulls,
                "learning_speed":        speed_report,
                "confidence_trajectory": confidence_trajectory,
                "exploration_pressure":  explore_pressure,
                "strategy_dominance":    strategy_dominance,
                "regime_adaptation":     regime_adaptation,
                "evolution_state":       evo,
                "summary_metrics": {
                    "total_updates":   summary.get("total_updates", 0),
                    "allow_rate":      summary.get("allow_rate", 0.0),
                    "profitable_pct":  summary.get("profitable_pct", 0.0),
                    "toxic_contexts":  summary.get("toxic_contexts", 0),
                    "boost_fires":     summary.get("boost_fires", 0),
                    "floor_lowers":    summary.get("floor_lowers", 0),
                },
            }

        except Exception as exc:
            logger.warning(f"[EVO-LAYER] compute_learning_snapshot error: {exc}")
            return {"module": self.MODULE, "error": str(exc)}

    def get_intelligence_score(self, rl_engine_instance: Any) -> float:
        """
        Returns a 0–100 composite intelligence score for the current session.

        Factors:
          - Profitable context ratio (30%)
          - Context maturity (20%)
          - Trade allow rate (20%)
          - Average Q-value quality (30%)
        """
        if rl_engine_instance is None:
            return 0.0
        try:
            if hasattr(rl_engine_instance, "get_evolution_state"):
                evo = rl_engine_instance.get_evolution_state()
                return float(evo.get("intelligence_score", 0.0))
        except Exception:
            pass
        return 0.0

    def get_learning_progress_log(self, rl_engine_instance: Any) -> str:
        """
        One-line human-readable learning progress summary for thought logs.
        """
        if rl_engine_instance is None:
            return "[EVO] No RL engine attached"
        try:
            table       = getattr(rl_engine_instance, "_table", {})
            n_total     = len(table)
            n_mature    = sum(1 for s in table.values() if s.n_visits >= 20)
            n_profit    = sum(1 for s in table.values() if getattr(s, "q_value", 0) > 0)
            n_toxic     = len(getattr(rl_engine_instance, "_toxic_contexts", set()))
            allow_rate  = (
                getattr(rl_engine_instance, "_total_allowed", 0)
                / max(getattr(rl_engine_instance, "_total_pulls", 1), 1)
            )
            score = self.get_intelligence_score(rl_engine_instance)
            return (
                f"[EVO-LAYER] ctx={n_total} mature={n_mature} "
                f"profitable={n_profit} toxic={n_toxic} "
                f"allow={allow_rate:.0%} iq={score:.0f}/100"
            )
        except Exception as exc:
            return f"[EVO-LAYER] progress_log error: {exc}"

    def log_evolution_tick(self, rl_engine_instance: Any) -> None:
        """
        Emit a single INFO log line with key evolution metrics.
        Call periodically (e.g. every 10 minutes) from a background task.
        """
        line = self.get_learning_progress_log(rl_engine_instance)
        logger.info(line)

    # ── Private analytics ─────────────────────────────────────────────────────

    def _learning_speed_report(self, table: dict) -> Dict[str, Any]:
        """Context maturity distribution and average learning velocity."""
        states = list(table.values())
        if not states:
            return {"status": "NO_CONTEXTS"}

        tiers = {"fresh": 0, "accel": 0, "standard": 0, "mature": 0}
        velocities = []
        for s in states:
            n = getattr(s, "n_visits", 0)
            if n < 5:
                tiers["fresh"] += 1
            elif n < 20:
                tiers["accel"] += 1
            elif n < 50:
                tiers["standard"] += 1
            else:
                tiers["mature"] += 1
            vel = getattr(s, "q_velocity", 0.0)
            if vel > 0:
                velocities.append(vel)

        avg_vel  = sum(velocities) / len(velocities) if velocities else 0.0
        n_total  = len(states)
        maturity_pct = round((tiers["standard"] + tiers["mature"]) / max(n_total, 1) * 100, 1)

        return {
            "total_contexts":  n_total,
            "maturity_tiers":  tiers,
            "maturity_pct":    maturity_pct,
            "avg_q_velocity":  round(avg_vel, 4),
            "status": (
                "MATURE"   if maturity_pct >= 60 else
                "LEARNING" if maturity_pct >= 20 else
                "WARMING_UP"
            ),
        }

    def _confidence_trajectory(self, table: dict) -> Dict[str, Any]:
        """
        Measure how confidence (Q-value distribution) has evolved.
        Proxied by current Q distribution since we don't store historical snapshots.
        """
        states  = list(table.values())
        visited = [s for s in states if getattr(s, "n_visits", 0) >= 3]
        if not visited:
            return {"status": "INSUFFICIENT_DATA"}

        q_values = [getattr(s, "q_value", 0.0) for s in visited]
        avg_q    = sum(q_values) / len(q_values)
        pos_q    = [q for q in q_values if q > 0]
        neg_q    = [q for q in q_values if q < 0]

        return {
            "n_visited_contexts": len(visited),
            "avg_q":              round(avg_q, 4),
            "max_q":              round(max(q_values), 4),
            "min_q":              round(min(q_values), 4),
            "positive_contexts":  len(pos_q),
            "negative_contexts":  len(neg_q),
            "avg_positive_q":     round(sum(pos_q) / len(pos_q), 4) if pos_q else 0.0,
            "avg_negative_q":     round(sum(neg_q) / len(neg_q), 4) if neg_q else 0.0,
            "confidence_direction": (
                "GROWING"   if avg_q > 0.10 else
                "NEUTRAL"   if avg_q >= -0.10 else
                "DECLINING"
            ),
        }

    def _exploration_pressure(self, rl_engine_instance: Any) -> Dict[str, Any]:
        """
        Compute exploration pressure: how often the system is forced to explore
        vs. exploit known good contexts.
        """
        explore = int(getattr(rl_engine_instance, "_explore_trades", 0))
        exploit = int(getattr(rl_engine_instance, "_exploit_trades", 0))
        blocked = int(getattr(rl_engine_instance, "_total_blocked",  0))
        total   = explore + exploit + blocked

        if total == 0:
            return {"status": "NO_DECISIONS"}

        explore_ratio  = explore / max(explore + exploit, 1)
        block_ratio    = blocked / max(total, 1)

        return {
            "explore_trades":    explore,
            "exploit_trades":    exploit,
            "blocked_trades":    blocked,
            "explore_ratio":     round(explore_ratio, 3),
            "block_ratio":       round(block_ratio, 3),
            "pressure_status": (
                "HIGH_EXPLORE"   if explore_ratio > 0.40 else
                "BALANCED"       if explore_ratio > 0.15 else
                "HIGH_EXPLOIT"
            ),
        }

    def _strategy_dominance(self, table: dict) -> List[Dict[str, Any]]:
        """
        Rank strategies by aggregate Q-value across all contexts.
        Returns top strategies sorted by dominance score.
        """
        strategy_scores: Dict[str, Dict[str, Any]] = {}

        for key, state in table.items():
            parts = key.split("|")
            if len(parts) < 3:
                continue
            strategy = parts[2]
            n  = getattr(state, "n_visits", 0)
            q  = getattr(state, "q_value",  0.0)

            if strategy not in strategy_scores:
                strategy_scores[strategy] = {
                    "strategy":  strategy,
                    "contexts":  0,
                    "total_q":   0.0,
                    "total_n":   0,
                    "profitable": 0,
                }
            entry = strategy_scores[strategy]
            entry["contexts"]  += 1
            entry["total_q"]   += q * n
            entry["total_n"]   += n
            if q > 0:
                entry["profitable"] += 1

        ranked = []
        for entry in strategy_scores.values():
            n = entry["total_n"]
            entry["avg_q"]         = round(entry["total_q"] / max(n, 1), 4)
            entry["dominance"]     = round(entry["avg_q"] * math.log(max(n, 1) + 1), 4)
            entry["profitable_pct"] = round(
                entry["profitable"] / max(entry["contexts"], 1) * 100, 1
            )
            ranked.append(entry)

        ranked.sort(key=lambda x: x["dominance"], reverse=True)
        return ranked[:10]   # top 10 strategies

    def _regime_adaptation(self, table: dict) -> Dict[str, Any]:
        """
        Per-regime Q-value summary — shows how well the system has adapted
        to each market regime.
        """
        regime_data: Dict[str, List[float]] = {}

        for key, state in table.items():
            parts = key.split("|")
            if len(parts) < 1:
                continue
            regime = parts[0]
            n = getattr(state, "n_visits", 0)
            q = getattr(state, "q_value",  0.0)
            if n >= 3:   # only include contexts with meaningful data
                if regime not in regime_data:
                    regime_data[regime] = []
                regime_data[regime].append(q)

        result = {}
        for regime, q_list in regime_data.items():
            avg_q = sum(q_list) / len(q_list)
            result[regime] = {
                "n_contexts":   len(q_list),
                "avg_q":        round(avg_q, 4),
                "profitable":   sum(1 for q in q_list if q > 0),
                "adaptation":   (
                    "STRONG"   if avg_q > 0.30 else
                    "EMERGING" if avg_q > 0.05 else
                    "WEAK"     if avg_q >= -0.10 else
                    "TOXIC"
                ),
            }

        return result


# ── math import ───────────────────────────────────────────────────────────────
import math   # noqa: E402 — kept at bottom to not conflict with module-level usage


# ── Module-level singleton ────────────────────────────────────────────────────
rl_evolution_layer = RLEvolutionLayer()
