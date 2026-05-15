"""
PRP-001 — Directional Legitimacy Analyzer

Tracks directional consistency: how often LONG/SHORT calls are directionally
correct across regimes, strategies, and hours. Identifies systematic directional
bias or regime × direction mismatches.

Forensic outputs:
  03_directional_legitimacy_report.json
  09_regime_signal_validity.json
"""
from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Any, List

from loguru import logger


# ── Legitimacy score thresholds ────────────────────────────────────────────────
STRONG_LEGIT_THRESH = 0.60   # directional correctness rate above this = strong
WEAK_LEGIT_THRESH   = 0.45   # below this = worse than random
MIN_SAMPLE          = 5


class DirectionalLegitimacyAnalyzer:
    """
    PRP-001 directional correctness tracker. Thread-safe.

    "Directionally correct" = price moved in the predicted direction,
    regardless of whether the net PnL was positive after fees.
    """

    def __init__(self):
        self._lock = threading.RLock()

        # Per-regime directional stats
        self._regime_dir: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"correct": 0, "total": 0, "LONG_ok": 0, "LONG_total": 0, "SHORT_ok": 0, "SHORT_total": 0}
        )

        # Per-strategy directional stats
        self._strategy_dir: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"correct": 0, "total": 0}
        )

        # Per-hour directional stats
        self._hour_dir: Dict[int, Dict[str, int]] = defaultdict(
            lambda: {"correct": 0, "total": 0}
        )

        # Rolling 50-outcome window for stability tracking
        self._rolling: deque = deque(maxlen=50)

        self._total_correct: int = 0
        self._total_outcomes: int = 0

    def record_outcome(
        self,
        regime:      str,
        strategy_id: str,
        side:        str,
        utc_hour:    int,
        directionally_correct: bool,
        net_pnl:     float,
    ) -> None:
        with self._lock:
            self._total_outcomes += 1
            self._rolling.append(1 if directionally_correct else 0)

            rd = self._regime_dir[regime]
            rd["total"] += 1
            rd[f"{side}_total"] += 1
            if directionally_correct:
                self._total_correct += 1
                rd["correct"] += 1
                rd[f"{side}_ok"] += 1

            sd = self._strategy_dir[strategy_id]
            sd["total"] += 1
            if directionally_correct:
                sd["correct"] += 1

            hd = self._hour_dir[utc_hour]
            hd["total"] += 1
            if directionally_correct:
                hd["correct"] += 1

    # ── Metrics ────────────────────────────────────────────────────────────────

    def global_legit_score(self) -> float:
        with self._lock:
            if self._total_outcomes == 0:
                return 0.0
            return round(self._total_correct / self._total_outcomes, 4)

    def rolling_legit_score(self) -> float:
        """Legitimacy over last 50 outcomes — stability indicator."""
        with self._lock:
            if not self._rolling:
                return 0.0
            return round(sum(self._rolling) / len(self._rolling), 4)

    def legitimacy_label(self) -> str:
        score = self.global_legit_score()
        if score >= STRONG_LEGIT_THRESH:
            return "STRONG"
        elif score >= 0.50:
            return "NEUTRAL"
        elif score >= WEAK_LEGIT_THRESH:
            return "WEAK"
        else:
            return "DIRECTIONAL_BIAS"

    # ── Forensic reports ───────────────────────────────────────────────────────

    def directional_legitimacy_report(self) -> Dict[str, Any]:
        """Report 03: Full directional breakdown by regime, strategy, hour."""
        with self._lock:
            by_regime = {}
            for regime, d in self._regime_dir.items():
                total = d["total"]
                by_regime[regime] = {
                    "total":        total,
                    "correct":      d["correct"],
                    "legit_rate":   round(d["correct"] / total, 4) if total > 0 else 0.0,
                    "LONG_rate":    round(d["LONG_ok"]  / d["LONG_total"],  4) if d["LONG_total"]  > 0 else 0.0,
                    "SHORT_rate":   round(d["SHORT_ok"] / d["SHORT_total"], 4) if d["SHORT_total"] > 0 else 0.0,
                    "label":        self._label(d["correct"], total),
                }

            by_strategy = {}
            for strat, d in self._strategy_dir.items():
                total = d["total"]
                by_strategy[strat] = {
                    "total":      total,
                    "correct":    d["correct"],
                    "legit_rate": round(d["correct"] / total, 4) if total > 0 else 0.0,
                }

            by_hour = {}
            for h, d in self._hour_dir.items():
                total = d["total"]
                by_hour[str(h)] = {
                    "total":    total,
                    "legit_rate": round(d["correct"] / total, 4) if total > 0 else 0.0,
                }

            return {
                "report":           "03_directional_legitimacy_report",
                "prp":              "001",
                "global_score":     self.global_legit_score(),
                "rolling_score":    self.rolling_legit_score(),
                "label":            self.legitimacy_label(),
                "by_regime":        by_regime,
                "by_strategy":      by_strategy,
                "by_hour":          by_hour,
                "ts":               int(time.time() * 1000),
            }

    def regime_signal_validity(self) -> Dict[str, Any]:
        """Report 09: Regime-specific signal validity assessment."""
        with self._lock:
            validity = {}
            for regime, d in self._regime_dir.items():
                total = d["total"]
                if total < MIN_SAMPLE:
                    validity[regime] = {"status": "INSUFFICIENT_DATA", "total": total}
                    continue
                legit = d["correct"] / total
                validity[regime] = {
                    "total":       total,
                    "legit_rate":  round(legit, 4),
                    "status":      "VALID" if legit >= 0.50 else "INVALID",
                    "LONG_valid":  d["LONG_ok"] / d["LONG_total"] >= 0.50 if d["LONG_total"] > 0 else None,
                    "SHORT_valid": d["SHORT_ok"] / d["SHORT_total"] >= 0.50 if d["SHORT_total"] > 0 else None,
                }
            return {
                "report":              "09_regime_signal_validity",
                "prp":                 "001",
                "global_legit_score":  self.global_legit_score(),
                "by_regime":           validity,
                "ts":                  int(time.time() * 1000),
            }

    @staticmethod
    def _label(correct: int, total: int) -> str:
        if total < MIN_SAMPLE:
            return "INSUFFICIENT_DATA"
        rate = correct / total
        if rate >= STRONG_LEGIT_THRESH: return "STRONG"
        elif rate >= 0.50:              return "NEUTRAL"
        elif rate >= WEAK_LEGIT_THRESH: return "WEAK"
        else:                           return "DIRECTIONAL_BIAS"

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "module":         "DirectionalLegitimacyAnalyzer",
                "prp":            "001",
                "global_score":   self.global_legit_score(),
                "rolling_score":  self.rolling_legit_score(),
                "label":          self.legitimacy_label(),
                "total_outcomes": self._total_outcomes,
                "ts":             int(time.time() * 1000),
            }


# ── Singleton ──────────────────────────────────────────────────────────────────
directional_legitimacy = DirectionalLegitimacyAnalyzer()
