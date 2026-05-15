"""
PRP-001 — Signal Truth Engine

Core observational layer. Records each signal's context at generation time
and its outcome after trade close. Computes truth scores across all signals.

This is a NON-BLOCKING measurement system for Phase 1.
It collects data; later phases (PRP-002+) act on it.

Forensic outputs:
  01_signal_truth_matrix.json
  08_predictive_integrity_monitor.json
  10_truth_density_summary.json
"""
from __future__ import annotations

import time
import threading
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List

from loguru import logger


# ── Constants ──────────────────────────────────────────────────────────────────
MAX_RECORDS        = 2000   # rolling window of signal records
MIN_SAMPLE         = 5      # minimum records before computing scores
CONFIDENCE_BUCKETS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.80, 0.90, 1.0]


@dataclass
class SignalRecord:
    """Full context snapshot at signal generation + outcome after close."""
    signal_id:       str
    symbol:          str
    strategy_id:     str
    regime:          str
    side:            str          # "LONG" | "SHORT"
    confidence:      float
    entry_price:     float
    stop_loss:       float
    take_profit:     float
    rr_declared:     float        # declared RR = |TP-entry| / |SL-entry|
    utc_hour:        int
    gen_ts:          int          # signal generation timestamp ms

    # Context at generation time
    rsi_val:         float = 0.0
    above_sma:       bool  = False
    atr_pct:         float = 0.0
    context_score:   float = 0.0  # from context_quality_engine

    # Outcome (filled after close)
    outcome_recorded: bool  = False
    net_pnl:         float = 0.0
    gross_pnl:       float = 0.0
    exit_price:      float = 0.0
    rr_achieved:     float = 0.0  # actual |exit-entry| / |SL-entry|
    was_win:         bool  = False
    directionally_correct: bool = False
    close_ts:        int   = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SignalTruthEngine:
    """
    PRP-001 central observational registry. Thread-safe.

    Integration points in main.py:
      1. signal_truth_engine.record_signal(...)  — at trade open
      2. signal_truth_engine.record_outcome(...) — at trade close (with trade_id)
    """

    def __init__(self):
        self._lock    = threading.RLock()
        self._records: deque = deque(maxlen=MAX_RECORDS)
        self._index:   Dict[str, SignalRecord] = {}  # signal_id → record

        # Running counters for fast metrics
        self._total_signals:   int   = 0
        self._total_outcomes:  int   = 0
        self._total_wins:      int   = 0
        self._total_correct:   int   = 0  # directionally correct
        self._total_net_pnl:   float = 0.0

        # Per-regime, per-strategy truth stats
        self._regime_stats:    Dict[str, Dict[str, int]]   = defaultdict(lambda: {"signals": 0, "wins": 0, "outcomes": 0})
        self._strategy_stats:  Dict[str, Dict[str, int]]   = defaultdict(lambda: {"signals": 0, "wins": 0, "outcomes": 0})

        logger.info("[PRP-001] SignalTruthEngine initialized")

    # ── Record at signal generation (trade open) ───────────────────────────────

    def record_signal(
        self,
        signal_id:    str,
        symbol:       str,
        strategy_id:  str,
        regime:       str,
        side:         str,
        confidence:   float,
        entry_price:  float,
        stop_loss:    float,
        take_profit:  float,
        utc_hour:     int,
        rsi_val:      float = 0.0,
        above_sma:    bool  = False,
        atr_pct:      float = 0.0,
        context_score: float = 0.0,
    ) -> None:
        """Call when a trade is opened. signal_id == position_id == trade_id."""
        with self._lock:
            sl_dist = abs(entry_price - stop_loss)
            tp_dist = abs(take_profit - entry_price)
            rr_declared = round(tp_dist / sl_dist, 3) if sl_dist > 0 else 0.0

            rec = SignalRecord(
                signal_id     = signal_id,
                symbol        = symbol,
                strategy_id   = strategy_id,
                regime        = regime,
                side          = side,
                confidence    = confidence,
                entry_price   = entry_price,
                stop_loss     = stop_loss,
                take_profit   = take_profit,
                rr_declared   = rr_declared,
                utc_hour      = utc_hour,
                gen_ts        = int(time.time() * 1000),
                rsi_val       = rsi_val,
                above_sma     = above_sma,
                atr_pct       = atr_pct,
                context_score = context_score,
            )
            self._records.append(rec)
            self._index[signal_id] = rec

            self._total_signals += 1
            self._regime_stats[regime]["signals"]   += 1
            self._strategy_stats[strategy_id]["signals"] += 1

    # ── Record outcome at trade close ──────────────────────────────────────────

    def record_outcome(
        self,
        signal_id:   str,
        net_pnl:     float,
        gross_pnl:   float,
        exit_price:  float,
    ) -> None:
        """Call when the position identified by signal_id closes."""
        with self._lock:
            rec = self._index.get(signal_id)
            if rec is None:
                # Signal was generated before this session started — skip
                return

            sl_dist = abs(rec.entry_price - rec.stop_loss)
            exit_dist = abs(exit_price - rec.entry_price)
            rr_achieved = round(exit_dist / sl_dist, 3) if sl_dist > 0 else 0.0

            # Directional correctness: did price move toward TP?
            if rec.side == "LONG":
                dir_correct = exit_price > rec.entry_price
            else:
                dir_correct = exit_price < rec.entry_price

            rec.outcome_recorded     = True
            rec.net_pnl              = net_pnl
            rec.gross_pnl            = gross_pnl
            rec.exit_price           = exit_price
            rec.rr_achieved          = rr_achieved
            rec.was_win              = net_pnl > 0
            rec.directionally_correct = dir_correct
            rec.close_ts             = int(time.time() * 1000)

            self._total_outcomes += 1
            self._total_net_pnl  += net_pnl
            if rec.was_win:
                self._total_wins += 1
                self._regime_stats[rec.regime]["wins"]       += 1
                self._strategy_stats[rec.strategy_id]["wins"] += 1
            if dir_correct:
                self._total_correct += 1

            self._regime_stats[rec.regime]["outcomes"]       += 1
            self._strategy_stats[rec.strategy_id]["outcomes"] += 1

    # ── Truth metrics ──────────────────────────────────────────────────────────

    def truth_density(self) -> float:
        """Fraction of outcomes that were wins (truth-density signal metric)."""
        with self._lock:
            if self._total_outcomes == 0:
                return 0.0
            return round(self._total_wins / self._total_outcomes, 4)

    def directional_legitimacy(self) -> float:
        """Fraction of outcomes that were directionally correct (regardless of fees)."""
        with self._lock:
            if self._total_outcomes == 0:
                return 0.0
            return round(self._total_correct / self._total_outcomes, 4)

    def confidence_calibration(self) -> List[Dict[str, Any]]:
        """
        Bin signals by confidence tier and compute win rate per tier.
        High calibration = higher confidence → higher win rate.
        """
        with self._lock:
            buckets: Dict[float, Dict[str, int]] = {b: {"signals": 0, "wins": 0} for b in CONFIDENCE_BUCKETS}
            for rec in self._records:
                if not rec.outcome_recorded:
                    continue
                for thresh in CONFIDENCE_BUCKETS:
                    if rec.confidence <= thresh:
                        buckets[thresh]["signals"] += 1
                        if rec.was_win:
                            buckets[thresh]["wins"] += 1
                        break
            result = []
            for thresh, v in buckets.items():
                if v["signals"] > 0:
                    result.append({
                        "confidence_up_to": thresh,
                        "signals":          v["signals"],
                        "wins":             v["wins"],
                        "win_rate":         round(v["wins"] / v["signals"], 4),
                    })
            return result

    def noise_participation_ratio(self) -> float:
        """Fraction of signals that were directionally WRONG — pure noise."""
        with self._lock:
            if self._total_outcomes == 0:
                return 0.0
            wrong = self._total_outcomes - self._total_correct
            return round(wrong / self._total_outcomes, 4)

    # ── Forensic reports ───────────────────────────────────────────────────────

    def signal_truth_matrix(self) -> Dict[str, Any]:
        """Report 01: Per-regime, per-strategy truth breakdown."""
        with self._lock:
            regime_truth = {}
            for regime, s in self._regime_stats.items():
                outs = s["outcomes"]
                regime_truth[regime] = {
                    "signals":   s["signals"],
                    "outcomes":  outs,
                    "wins":      s["wins"],
                    "win_rate":  round(s["wins"] / outs, 4) if outs > 0 else 0.0,
                }
            strategy_truth = {}
            for strat, s in self._strategy_stats.items():
                outs = s["outcomes"]
                strategy_truth[strat] = {
                    "signals":   s["signals"],
                    "outcomes":  outs,
                    "wins":      s["wins"],
                    "win_rate":  round(s["wins"] / outs, 4) if outs > 0 else 0.0,
                }
            return {
                "report":              "01_signal_truth_matrix",
                "prp":                 "001",
                "total_signals":       self._total_signals,
                "total_outcomes":      self._total_outcomes,
                "truth_density":       self.truth_density(),
                "directional_legit":   self.directional_legitimacy(),
                "noise_ratio":         self.noise_participation_ratio(),
                "total_net_pnl":       round(self._total_net_pnl, 4),
                "by_regime":           regime_truth,
                "by_strategy":         strategy_truth,
                "ts":                  int(time.time() * 1000),
            }

    def predictive_integrity_monitor(self) -> Dict[str, Any]:
        """Report 08: Calibration + rolling predictive stability."""
        with self._lock:
            recent = [r for r in self._records if r.outcome_recorded][-50:]
            recent_wins = sum(1 for r in recent if r.was_win)
            recent_wr = round(recent_wins / len(recent), 4) if recent else 0.0
            rolling_drift = abs(recent_wr - self.truth_density()) if self._total_outcomes > 0 else 0.0
            return {
                "report":                "08_predictive_integrity_monitor",
                "prp":                   "001",
                "global_truth_density":  self.truth_density(),
                "recent_win_rate":       recent_wr,
                "rolling_drift":         round(rolling_drift, 4),
                "confidence_calibration": self.confidence_calibration(),
                "ts":                    int(time.time() * 1000),
            }

    def truth_density_summary(self) -> Dict[str, Any]:
        """Report 10: Top-level survivability summary."""
        with self._lock:
            avg_pnl = self._total_net_pnl / self._total_outcomes if self._total_outcomes > 0 else 0.0
            return {
                "report":            "10_truth_density_summary",
                "prp":               "001",
                "total_signals":     self._total_signals,
                "total_outcomes":    self._total_outcomes,
                "truth_density":     self.truth_density(),
                "directional_legit": self.directional_legitimacy(),
                "noise_ratio":       self.noise_participation_ratio(),
                "avg_net_pnl":       round(avg_pnl, 4),
                "total_net_pnl":     round(self._total_net_pnl, 4),
                "data_sufficient":   self._total_outcomes >= MIN_SAMPLE,
                "ts":                int(time.time() * 1000),
            }

    def get_telemetry(self) -> Dict[str, Any]:
        """Full telemetry for dashboard / export bundle."""
        with self._lock:
            return {
                "module":              "SignalTruthEngine",
                "prp":                 "001",
                "total_signals":       self._total_signals,
                "total_outcomes":      self._total_outcomes,
                "pending_outcomes":    self._total_signals - self._total_outcomes,
                "truth_density":       self.truth_density(),
                "directional_legit":   self.directional_legitimacy(),
                "noise_ratio":         self.noise_participation_ratio(),
                "total_net_pnl":       round(self._total_net_pnl, 4),
                "ts":                  int(time.time() * 1000),
            }

    def recent_signals(self, n: int = 30) -> List[Dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in list(self._records)[-n:]]


# ── Singleton ──────────────────────────────────────────────────────────────────
signal_truth_engine = SignalTruthEngine()
