"""
PHOENIX AEG — Damage Accounting  [GAP-007]

Tracks economic impact per recommendation class:
  - PnL delta attributed to each rec_type
  - Win rate delta attributed to each rec_type
  - Net economic value generated vs destroyed

Answers: "Recommendation class REDUCE_POSITION_SIZE generated +2.3% or -1.8%?"

Data sources:
  - RecommendationRealityEngine (verified outcomes with pnl_delta)
  - EconomicOutcomeLedger (if available)
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DamageRecord:
    rec_id: str
    rec_type: str
    entity_id: str
    pnl_delta: float
    win_rate_delta: float
    correct: bool
    recorded_at: float = field(default_factory=time.time)


class AEGDamageAccounting:
    """
    Economic impact ledger per AEG recommendation class.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[DamageRecord] = []

    def record(
        self,
        rec_id: str,
        rec_type: str,
        entity_id: str,
        pnl_delta: float,
        win_rate_delta: float,
        correct: bool,
    ) -> DamageRecord:
        dr = DamageRecord(
            rec_id=rec_id,
            rec_type=rec_type,
            entity_id=entity_id,
            pnl_delta=pnl_delta,
            win_rate_delta=win_rate_delta,
            correct=correct,
        )
        with self._lock:
            self._records.append(dr)
            if len(self._records) > 50_000:
                self._records = self._records[-50_000:]
        return dr

    def account_for(self, rec_type: str, days: Optional[int] = None) -> dict:
        cutoff = time.time() - days * 86400 if days else 0.0
        with self._lock:
            items = [r for r in self._records if r.rec_type == rec_type and r.recorded_at >= cutoff]
        if not items:
            return {"rec_type": rec_type, "count": 0, "net_pnl": 0.0, "note": "No records"}
        net_pnl = sum(r.pnl_delta for r in items)
        net_wr = sum(r.win_rate_delta for r in items)
        correct = sum(1 for r in items if r.correct)
        return {
            "rec_type":         rec_type,
            "count":            len(items),
            "correct":          correct,
            "accuracy":         round(correct / len(items), 3),
            "net_pnl_delta":    round(net_pnl, 4),
            "avg_pnl_delta":    round(net_pnl / len(items), 4),
            "net_wr_delta":     round(net_wr, 4),
            "avg_wr_delta":     round(net_wr / len(items), 4),
            "economic_verdict": "POSITIVE" if net_pnl > 0 else ("NEUTRAL" if net_pnl == 0 else "NEGATIVE"),
            "days_window":      days,
        }

    def all_rec_types(self, days: Optional[int] = None) -> List[dict]:
        with self._lock:
            rec_types = list(set(r.rec_type for r in self._records))
        return sorted(
            [self.account_for(rt, days=days) for rt in rec_types],
            key=lambda x: x.get("net_pnl_delta", 0),
            reverse=True,
        )

    def top_performers(self, days: Optional[int] = None, limit: int = 10) -> List[dict]:
        return self.all_rec_types(days=days)[:limit]

    def worst_performers(self, days: Optional[int] = None, limit: int = 10) -> List[dict]:
        return list(reversed(self.all_rec_types(days=days)))[:limit]

    def portfolio_summary(self, days: Optional[int] = None) -> dict:
        cutoff = time.time() - days * 86400 if days else 0.0
        with self._lock:
            items = [r for r in self._records if r.recorded_at >= cutoff]
        if not items:
            return {"total": 0, "net_pnl": 0.0, "note": "No data"}
        net_pnl = sum(r.pnl_delta for r in items)
        correct = sum(1 for r in items if r.correct)
        return {
            "total_recommendations": len(items),
            "correct":               correct,
            "overall_accuracy":      round(correct / len(items), 3),
            "net_pnl_delta":         round(net_pnl, 4),
            "avg_pnl_delta":         round(net_pnl / len(items), 4),
            "positive_classes":      sum(1 for a in self.all_rec_types(days=days) if a.get("net_pnl_delta", 0) > 0),
            "negative_classes":      sum(1 for a in self.all_rec_types(days=days) if a.get("net_pnl_delta", 0) < 0),
            "days_window":           days,
        }


# Singleton
aeg_damage_accounting = AEGDamageAccounting()
