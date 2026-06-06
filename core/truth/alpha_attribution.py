"""
Alpha Attribution Platform (AAP) — FTD-PHOENIX-ENTRY-EXIT-TRUTH-ENGINE-001
Records per-trade attribution snapshots and aggregates alpha discovery matrix.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from collections import defaultdict
import threading
import time

from loguru import logger


@dataclass
class AttributionSnapshot:
    trade_id:             str
    symbol:               str
    session:              str
    strategy:             str
    regime:               str
    entry_truth_score:    float
    exit_truth_score:     float
    structure_score:      float
    regime_score:         float
    momentum_score:       float
    volatility_score:     float
    liquidity_score:      float
    cost_score:           float
    net_pnl:              float
    r_multiple:           float
    genome_id:            Optional[str]
    rl_context:           Optional[str]
    ts_entry:             float
    ts_exit:              float
    alpha_sources:        List[str] = field(default_factory=list)
    destruction_sources:  List[str] = field(default_factory=list)

    def __post_init__(self):
        # Populate alpha/destruction sources from component scores
        components = {
            "structure":  self.structure_score,
            "regime":     self.regime_score,
            "momentum":   self.momentum_score,
            "volatility": self.volatility_score,
            "liquidity":  self.liquidity_score,
            "cost":       self.cost_score,
        }
        if not self.alpha_sources:
            self.alpha_sources = [c for c, s in components.items() if s >= 70]
        if not self.destruction_sources:
            self.destruction_sources = [c for c, s in components.items() if s < 40]


class AlphaAttributionPlatform:
    def __init__(self):
        logger.info("[BOOT] ALPHA_ATTRIBUTION_PLATFORM=ACTIVE")
        self._lock = threading.Lock()
        self._snapshots: List[AttributionSnapshot] = []

    def record(self, snapshot: AttributionSnapshot) -> None:
        with self._lock:
            self._snapshots.append(snapshot)

    def alpha_discovery_matrix(self) -> dict:
        with self._lock:
            snaps = list(self._snapshots)

        components = ["structure", "regime", "momentum", "volatility", "liquidity", "cost"]

        # Win/loss counts per component
        win_component_counts: Dict[str, int] = defaultdict(int)
        win_component_scores: Dict[str, List[float]] = defaultdict(list)
        loss_component_counts: Dict[str, int] = defaultdict(int)
        loss_component_scores: Dict[str, List[float]] = defaultdict(list)

        score_buckets: Dict[str, List[float]] = {
            "0-20": [], "20-40": [], "40-60": [], "60-80": [], "80-100": []
        }

        for snap in snaps:
            comp_scores = {
                "structure":  snap.structure_score,
                "regime":     snap.regime_score,
                "momentum":   snap.momentum_score,
                "volatility": snap.volatility_score,
                "liquidity":  snap.liquidity_score,
                "cost":       snap.cost_score,
            }
            if snap.net_pnl > 0:
                for c in components:
                    if comp_scores[c] >= 70:
                        win_component_counts[c] += 1
                        win_component_scores[c].append(comp_scores[c])
            elif snap.net_pnl < 0:
                for c in components:
                    if comp_scores[c] < 40:
                        loss_component_counts[c] += 1
                        loss_component_scores[c].append(comp_scores[c])

            # Score bucket
            ete = snap.entry_truth_score
            if ete < 20:
                score_buckets["0-20"].append(snap.net_pnl)
            elif ete < 40:
                score_buckets["20-40"].append(snap.net_pnl)
            elif ete < 60:
                score_buckets["40-60"].append(snap.net_pnl)
            elif ete < 80:
                score_buckets["60-80"].append(snap.net_pnl)
            else:
                score_buckets["80-100"].append(snap.net_pnl)

        top_alpha = sorted([
            {
                "component": c,
                "win_count": win_component_counts[c],
                "avg_score": round(sum(win_component_scores[c]) / len(win_component_scores[c]), 1)
                    if win_component_scores[c] else 0.0,
            }
            for c in components
        ], key=lambda x: x["win_count"], reverse=True)

        top_destroyers = sorted([
            {
                "component": c,
                "loss_count": loss_component_counts[c],
                "avg_score": round(sum(loss_component_scores[c]) / len(loss_component_scores[c]), 1)
                    if loss_component_scores[c] else 0.0,
            }
            for c in components
        ], key=lambda x: x["loss_count"], reverse=True)

        score_vs_expectancy = [
            {
                "score_bucket": bucket,
                "avg_pnl": round(sum(pnls) / len(pnls), 4) if pnls else 0.0,
                "trade_count": len(pnls),
            }
            for bucket, pnls in score_buckets.items()
        ]

        return {
            "top_alpha_sources": top_alpha,
            "top_destroyers": top_destroyers,
            "score_vs_expectancy": score_vs_expectancy,
            "total_snapshots": len(snaps),
        }

    def truth_calibration_report(self) -> dict:
        with self._lock:
            snaps = list(self._snapshots)

        # Decile breakdown: 0-10, 10-20, ..., 90-100
        deciles: Dict[str, List[float]] = {f"{i*10}-{(i+1)*10}": [] for i in range(10)}

        for snap in snaps:
            ete = snap.entry_truth_score
            bucket_idx = min(int(ete / 10), 9)
            bucket_key = f"{bucket_idx*10}-{(bucket_idx+1)*10}"
            deciles[bucket_key].append(snap.net_pnl)

        calibration = []
        for decile, pnls in deciles.items():
            if not pnls:
                calibration.append({
                    "decile": decile,
                    "avg_pnl": 0.0,
                    "win_rate": 0.0,
                    "trade_count": 0,
                })
            else:
                calibration.append({
                    "decile": decile,
                    "avg_pnl": round(sum(pnls) / len(pnls), 4),
                    "win_rate": round(sum(1 for p in pnls if p > 0) / len(pnls), 3),
                    "trade_count": len(pnls),
                })

        return {
            "calibration": calibration,
            "total_trades": len(snaps),
        }

    def summary(self) -> dict:
        with self._lock:
            n = len(self._snapshots)
        return {
            "total_snapshots": n,
        }


# Module-level singleton
alpha_attribution_platform = AlphaAttributionPlatform()
