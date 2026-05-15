"""
PRP-001 — Asymmetry Validation Engine

Validates whether the declared Risk:Reward structure was actually achievable
in practice. Identifies systematic RR optimism bias and detects structural
asymmetry failures (declared RR ≥ 3.0 but achieved RR < 0.5).

Forensic outputs:
  06_asymmetry_validation_report.json
  04_confidence_reality_divergence.json
"""
from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Any, List

from loguru import logger


# ── Asymmetry quality thresholds ───────────────────────────────────────────────
ACHIEVABLE_RR_MIN     = 0.5    # RR actually achieved vs declared
OPTIMISM_BIAS_THRESH  = 0.40   # if achieved/declared < 40% = optimism bias
MIN_SAMPLE            = 5
CONFIDENCE_TRAP_CONF  = 0.60   # high-confidence signals that achieve poor RR


class AsymmetryValidationEngine:
    """
    PRP-001 asymmetry and RR validation tracker. Thread-safe.

    Key question: "If we said RR=3.0, did we actually get near 3.0?"
    A systematic gap indicates the TP is too ambitious or slippage/timing
    prevents achieving the declared TP before market reverses.
    """

    def __init__(self):
        self._lock = threading.RLock()

        # Per-strategy RR tracking
        self._strategy_rr: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"declared_sum": 0.0, "achieved_sum": 0.0, "count": 0, "achievable": 0}
        )

        # Per-regime RR tracking
        self._regime_rr: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"declared_sum": 0.0, "achieved_sum": 0.0, "count": 0}
        )

        # Confidence-reality divergence: high confidence + poor RR achievement
        self._divergence_log: deque = deque(maxlen=200)

        # Rolling RR achievement ratio
        self._rolling_ratios: deque = deque(maxlen=50)

        self._total_outcomes: int = 0
        self._optimism_count: int = 0

    def record_outcome(
        self,
        signal_id:    str,
        symbol:       str,
        strategy_id:  str,
        regime:       str,
        confidence:   float,
        rr_declared:  float,
        rr_achieved:  float,
        was_win:      bool,
        net_pnl:      float,
    ) -> None:
        """Record declared vs achieved RR for every closed trade."""
        with self._lock:
            if rr_declared <= 0:
                return

            self._total_outcomes += 1
            ratio = rr_achieved / rr_declared if rr_declared > 0 else 0.0
            self._rolling_ratios.append(ratio)

            # Strategy stats
            sr = self._strategy_rr[strategy_id]
            sr["declared_sum"] += rr_declared
            sr["achieved_sum"] += rr_achieved
            sr["count"]        += 1
            if rr_achieved >= ACHIEVABLE_RR_MIN:
                sr["achievable"] += 1

            # Regime stats
            rr = self._regime_rr[regime]
            rr["declared_sum"] += rr_declared
            rr["achieved_sum"] += rr_achieved
            rr["count"]        += 1

            # Optimism bias detection
            if ratio < OPTIMISM_BIAS_THRESH:
                self._optimism_count += 1

            # Confidence-reality divergence: high confidence but poor RR achievement
            if confidence >= CONFIDENCE_TRAP_CONF and ratio < OPTIMISM_BIAS_THRESH:
                self._divergence_log.append({
                    "signal_id":   signal_id,
                    "symbol":      symbol,
                    "strategy":    strategy_id,
                    "regime":      regime,
                    "confidence":  round(confidence, 3),
                    "rr_declared": round(rr_declared, 3),
                    "rr_achieved": round(rr_achieved, 3),
                    "ratio":       round(ratio, 3),
                    "net_pnl":     round(net_pnl, 4),
                    "ts":          int(time.time() * 1000),
                })

    # ── Metrics ────────────────────────────────────────────────────────────────

    def global_rr_achievement_ratio(self) -> float:
        """Average of (achieved / declared) across all outcomes."""
        with self._lock:
            if not self._rolling_ratios:
                return 0.0
            return round(sum(self._rolling_ratios) / len(self._rolling_ratios), 4)

    def optimism_bias_rate(self) -> float:
        with self._lock:
            if self._total_outcomes == 0:
                return 0.0
            return round(self._optimism_count / self._total_outcomes, 4)

    def asymmetry_health_label(self) -> str:
        ratio = self.global_rr_achievement_ratio()
        if ratio >= 0.70:   return "HEALTHY"
        elif ratio >= 0.50: return "MARGINAL"
        elif ratio >= 0.30: return "WEAK"
        else:               return "BROKEN"

    # ── Forensic reports ───────────────────────────────────────────────────────

    def asymmetry_validation_report(self) -> Dict[str, Any]:
        """Report 06: Per-strategy and per-regime RR achievement breakdown."""
        with self._lock:
            by_strategy = {}
            for strat, s in self._strategy_rr.items():
                count = s["count"]
                if count == 0:
                    continue
                avg_decl = s["declared_sum"] / count
                avg_ach  = s["achieved_sum"] / count
                by_strategy[strat] = {
                    "count":              count,
                    "avg_rr_declared":    round(avg_decl, 3),
                    "avg_rr_achieved":    round(avg_ach,  3),
                    "achievement_ratio":  round(avg_ach / avg_decl, 3) if avg_decl > 0 else 0.0,
                    "achievable_count":   s["achievable"],
                    "achievable_rate":    round(s["achievable"] / count, 4) if count > 0 else 0.0,
                }

            by_regime = {}
            for regime, r in self._regime_rr.items():
                count = r["count"]
                if count == 0:
                    continue
                avg_decl = r["declared_sum"] / count
                avg_ach  = r["achieved_sum"] / count
                by_regime[regime] = {
                    "count":             count,
                    "avg_rr_declared":   round(avg_decl, 3),
                    "avg_rr_achieved":   round(avg_ach,  3),
                    "achievement_ratio": round(avg_ach / avg_decl, 3) if avg_decl > 0 else 0.0,
                }

            return {
                "report":                  "06_asymmetry_validation_report",
                "prp":                     "001",
                "total_outcomes":          self._total_outcomes,
                "global_achievement_ratio": self.global_rr_achievement_ratio(),
                "optimism_bias_rate":       self.optimism_bias_rate(),
                "asymmetry_health":         self.asymmetry_health_label(),
                "by_strategy":             by_strategy,
                "by_regime":               by_regime,
                "ts":                      int(time.time() * 1000),
            }

    def confidence_reality_divergence(self) -> Dict[str, Any]:
        """Report 04: Cases where high confidence failed to achieve declared RR."""
        with self._lock:
            return {
                "report":           "04_confidence_reality_divergence",
                "prp":              "001",
                "total_divergences": len(self._divergence_log),
                "total_outcomes":   self._total_outcomes,
                "divergence_rate":  round(len(self._divergence_log) / self._total_outcomes, 4) if self._total_outcomes > 0 else 0.0,
                "recent":           list(self._divergence_log)[-20:],
                "ts":               int(time.time() * 1000),
            }

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "module":               "AsymmetryValidationEngine",
                "prp":                  "001",
                "total_outcomes":       self._total_outcomes,
                "achievement_ratio":    self.global_rr_achievement_ratio(),
                "optimism_bias_rate":   self.optimism_bias_rate(),
                "asymmetry_health":     self.asymmetry_health_label(),
                "divergence_count":     len(self._divergence_log),
                "ts":                   int(time.time() * 1000),
            }


# ── Singleton ──────────────────────────────────────────────────────────────────
asymmetry_validation = AsymmetryValidationEngine()
