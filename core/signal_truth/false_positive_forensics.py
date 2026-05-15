"""
PRP-001 — False Positive Forensics Engine

Identifies recurring false-positive signal structures: signals that appeared
confident but produced losing outcomes. Groups by regime, strategy, RSI zone,
confidence tier, and hour to expose systematic failure signatures.

Forensic outputs:
  02_false_positive_clusters.json
  07_noise_participation_audit.json
"""
from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional

from loguru import logger


# ── Confidence trap threshold ──────────────────────────────────────────────────
# A "confidence trap" is a signal with confidence ≥ this that still lost
CONFIDENCE_TRAP_THRESH = 0.60

# Minimum cluster size before reporting
MIN_CLUSTER_SIZE = 3


class FalsePositiveForensicsEngine:
    """
    PRP-001 false-positive cluster analyzer. Thread-safe.
    Called by SignalTruthEngine after each outcome is recorded.
    """

    def __init__(self):
        self._lock = threading.RLock()

        # Cluster keys: (regime, strategy, rsi_zone, confidence_tier, side)
        self._fp_clusters: Dict[tuple, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0, "total_pnl": 0.0, "last_ts": 0,
        })

        # Confidence trap log (high confidence but lost)
        self._confidence_traps: deque = deque(maxlen=500)

        # Hour-of-day failure map
        self._hour_fp_count: Dict[int, int] = defaultdict(int)
        self._hour_total:    Dict[int, int] = defaultdict(int)

        # Regime × side failure map
        self._regime_side_fp: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"LONG": 0, "SHORT": 0, "LONG_total": 0, "SHORT_total": 0}
        )

        self._total_false_positives: int = 0
        self._total_outcomes:        int = 0

    def record_outcome(
        self,
        signal_id:   str,
        symbol:      str,
        regime:      str,
        strategy_id: str,
        side:        str,
        confidence:  float,
        rsi_val:     float,
        utc_hour:    int,
        net_pnl:     float,
        was_win:     bool,
    ) -> None:
        """Called for every closed trade outcome. Records false positive clusters."""
        with self._lock:
            self._total_outcomes += 1
            self._hour_total[utc_hour] += 1
            self._regime_side_fp[regime][f"{side}_total"] += 1

            if was_win:
                return  # Only interested in false positives

            self._total_false_positives += 1
            self._hour_fp_count[utc_hour] += 1
            self._regime_side_fp[regime][side] += 1

            # RSI zone classification
            rsi_zone = self._rsi_zone(rsi_val)

            # Confidence tier
            conf_tier = self._conf_tier(confidence)

            # Cluster key
            key = (regime, strategy_id[:30], rsi_zone, conf_tier, side)
            cluster = self._fp_clusters[key]
            cluster["count"]     += 1
            cluster["total_pnl"] += net_pnl
            cluster["last_ts"]    = int(time.time() * 1000)
            cluster.setdefault("first_ts", cluster["last_ts"])
            cluster.setdefault("symbols", set()).add(symbol)

            # Log confidence traps
            if confidence >= CONFIDENCE_TRAP_THRESH:
                self._confidence_traps.append({
                    "signal_id":  signal_id,
                    "symbol":     symbol,
                    "regime":     regime,
                    "strategy":   strategy_id,
                    "side":       side,
                    "confidence": round(confidence, 3),
                    "rsi_val":    round(rsi_val, 2),
                    "net_pnl":    round(net_pnl, 4),
                    "ts":         int(time.time() * 1000),
                })

    # ── RSI zone classifier ────────────────────────────────────────────────────

    @staticmethod
    def _rsi_zone(rsi: float) -> str:
        if rsi < 25:     return "EXTREME_LOW"
        elif rsi < 35:   return "LOW"
        elif rsi < 45:   return "BELOW_MID"
        elif rsi < 55:   return "MID"
        elif rsi < 65:   return "ABOVE_MID"
        elif rsi < 75:   return "HIGH"
        else:            return "EXTREME_HIGH"

    @staticmethod
    def _conf_tier(conf: float) -> str:
        if conf < 0.55:  return "LOW"
        elif conf < 0.65: return "MED"
        elif conf < 0.80: return "HIGH"
        else:             return "VERY_HIGH"

    # ── Report: False Positive Clusters ───────────────────────────────────────

    def false_positive_clusters(self) -> Dict[str, Any]:
        """Report 02: Clusters of recurring false-positive signal structures."""
        with self._lock:
            clusters = []
            for key, data in self._fp_clusters.items():
                if data["count"] < MIN_CLUSTER_SIZE:
                    continue
                regime, strategy, rsi_zone, conf_tier, side = key
                avg_pnl = round(data["total_pnl"] / data["count"], 4)
                symbols = list(data.get("symbols", set()))[:10]
                clusters.append({
                    "regime":    regime,
                    "strategy":  strategy,
                    "rsi_zone":  rsi_zone,
                    "conf_tier": conf_tier,
                    "side":      side,
                    "count":     data["count"],
                    "avg_pnl":   avg_pnl,
                    "symbols":   symbols,
                    "last_ts":   data["last_ts"],
                })

            clusters.sort(key=lambda x: x["count"], reverse=True)

            fp_rate = round(self._total_false_positives / self._total_outcomes, 4) if self._total_outcomes > 0 else 0.0

            return {
                "report":               "02_false_positive_clusters",
                "prp":                  "001",
                "total_false_positives": self._total_false_positives,
                "total_outcomes":       self._total_outcomes,
                "false_positive_rate":  fp_rate,
                "clusters":             clusters[:20],
                "confidence_traps":     list(self._confidence_traps)[-20:],
                "ts":                   int(time.time() * 1000),
            }

    def noise_participation_audit(self) -> Dict[str, Any]:
        """Report 07: Hour-of-day and regime × side noise breakdown."""
        with self._lock:
            hour_breakdown = []
            for h in sorted(self._hour_total):
                total = self._hour_total[h]
                fp    = self._hour_fp_count.get(h, 0)
                hour_breakdown.append({
                    "hour":    h,
                    "total":   total,
                    "fp":      fp,
                    "fp_rate": round(fp / total, 4) if total > 0 else 0.0,
                })

            regime_side = {}
            for regime, s in self._regime_side_fp.items():
                for side in ("LONG", "SHORT"):
                    total = s.get(f"{side}_total", 0)
                    fp    = s.get(side, 0)
                    regime_side.setdefault(regime, {})[side] = {
                        "total":   total,
                        "fp":      fp,
                        "fp_rate": round(fp / total, 4) if total > 0 else 0.0,
                    }

            return {
                "report":           "07_noise_participation_audit",
                "prp":              "001",
                "by_hour":          hour_breakdown,
                "by_regime_side":   regime_side,
                "confidence_traps": len(self._confidence_traps),
                "ts":               int(time.time() * 1000),
            }

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            fp_rate = round(self._total_false_positives / self._total_outcomes, 4) if self._total_outcomes > 0 else 0.0
            active_clusters = sum(1 for d in self._fp_clusters.values() if d["count"] >= MIN_CLUSTER_SIZE)
            return {
                "module":                "FalsePositiveForensicsEngine",
                "prp":                   "001",
                "total_false_positives": self._total_false_positives,
                "total_outcomes":        self._total_outcomes,
                "false_positive_rate":   fp_rate,
                "active_clusters":       active_clusters,
                "confidence_traps":      len(self._confidence_traps),
                "ts":                    int(time.time() * 1000),
            }


# ── Singleton ──────────────────────────────────────────────────────────────────
false_positive_forensics = FalsePositiveForensicsEngine()
