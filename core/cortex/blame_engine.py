"""
PHOENIX CORTEX — Blame Attribution Engine  [CX-5]

For the first time, PHOENIX will be able to answer:

  "Trade #481 lost.  Which module caused it?"

The Blame Attribution Engine traces every loss event through the module
signal chain recorded at the time of the trade, assigns blame scores to
each contributing module, and identifies the primary root cause.

Blame model
───────────
  Each trade that closes at a loss generates a BlameRecord.
  A BlameRecord lists every module that had an active signal at entry time,
  weighted by:
    - Module influence weight (higher weight = higher responsibility)
    - Signal confidence at the time
    - Whether the module's signal was the deciding factor (the "casting vote")

  Blame score per module:
    blame = influence_weight × confidence × role_factor

  Role factors:
    APPROVE signal on risk module = high blame (allowed a bad trade)
    BUY/SELL on signal module     = medium blame (generated the signal)
    regime / learning module      = low blame (supporting context)

  Primary cause = module with highest blame score.

Blame history is persisted in memory (ring buffer, MAX_RECORDS items).
Aggregated blame statistics feed:
  - Influence Matrix decay
  - CORTEX health scoring
  - OBSERVATORY-X loss investigation

Constitutional rule: blame attribution is advisory — it never automatically
alters module behaviour.  All output is informational.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional


MAX_RECORDS = 1000

_ROLE_FACTORS: Dict[str, float] = {
    "risk":        1.0,    # approved a losing trade — high responsibility
    "signal":      0.8,    # generated the entry signal
    "execution":   0.3,    # executed — lower blame (follows orders)
    "capital":     0.7,    # sized the position
    "governance":  0.5,
    "learning":    0.4,
    "intelligence": 0.3,
    "reporting":   0.0,
    "infrastructure": 0.0,
    "utilities":   0.0,
}


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class ModuleBlameEntry:
    module_key: str
    role: str
    influence_weight: float
    signal_value: Any
    signal_confidence: float
    blame_score: float
    was_deciding_factor: bool = False


@dataclass
class BlameRecord:
    trade_id: str
    loss_amount: float
    entry_time: float
    exit_time: float
    entries: List[ModuleBlameEntry]       # all modules with signals at entry
    primary_cause: str                    # module key with highest blame
    primary_cause_score: float
    root_cause_description: str
    recorded_at: float = field(default_factory=time.time)


# ── Engine ────────────────────────────────────────────────────────────────────

class BlameAttributionEngine:
    """
    Attributes blame for losing trades across all modules that participated
    in the trade's approval chain.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: Deque[BlameRecord] = deque(maxlen=MAX_RECORDS)
        # Aggregate blame totals: module_key → cumulative blame score
        self._cumulative: Dict[str, float] = {}
        self._trade_count: Dict[str, int]  = {}  # module → times appeared in blame records

    # ── Attribution ───────────────────────────────────────────────────────────

    def attribute_loss(
        self,
        trade_id: str,
        loss_amount: float,
        entry_time: float,
        exit_time: float,
        module_signals: Dict[str, Dict],
        # module_signals: {module_key: {signal_value, confidence, role}}
    ) -> BlameRecord:
        """
        Called after a losing trade closes.
        module_signals should contain all modules that had active signals at entry.
        """
        from core.cortex.module_registry import cortex_module_registry
        from core.cortex.influence_matrix import influence_matrix

        entries: List[ModuleBlameEntry] = []

        for mod_key, sig_data in module_signals.items():
            role       = sig_data.get("role", "")
            confidence = float(sig_data.get("confidence", 0.5))
            sig_val    = sig_data.get("signal_value", "")
            inf_w      = influence_matrix.weight(mod_key)
            if inf_w == 0.0:
                defn = cortex_module_registry.get(mod_key)
                inf_w = defn.influence_weight if defn else 5.0

            role_factor = _ROLE_FACTORS.get(role, 0.3)
            blame_score = inf_w * confidence * role_factor

            entries.append(ModuleBlameEntry(
                module_key=mod_key,
                role=role,
                influence_weight=inf_w,
                signal_value=sig_val,
                signal_confidence=confidence,
                blame_score=round(blame_score, 4),
            ))

        if not entries:
            # No signal data — create a minimal unknown record
            entries.append(ModuleBlameEntry(
                module_key="unknown",
                role="unknown",
                influence_weight=0,
                signal_value="UNKNOWN",
                signal_confidence=0,
                blame_score=0,
            ))

        # Identify deciding factor: module with highest blame that approved the trade
        entries.sort(key=lambda e: e.blame_score, reverse=True)
        if entries:
            entries[0].was_deciding_factor = True

        primary        = entries[0].module_key
        primary_score  = entries[0].blame_score
        primary_signal = entries[0].signal_value

        root_desc = (
            f"Primary contributor: '{primary}' (role={entries[0].role}, "
            f"signal={primary_signal}, "
            f"blame_score={primary_score:.2f}). "
            f"Loss amount: {loss_amount:.4f}."
        )

        record = BlameRecord(
            trade_id=trade_id,
            loss_amount=loss_amount,
            entry_time=entry_time,
            exit_time=exit_time,
            entries=entries,
            primary_cause=primary,
            primary_cause_score=primary_score,
            root_cause_description=root_desc,
        )

        with self._lock:
            self._records.appendleft(record)
            for entry in entries:
                self._cumulative[entry.module_key] = (
                    self._cumulative.get(entry.module_key, 0.0) + entry.blame_score
                )
                self._trade_count[entry.module_key] = (
                    self._trade_count.get(entry.module_key, 0) + 1
                )

        # Feed blame back to influence matrix (advisory decay)
        try:
            from core.cortex.influence_matrix import influence_matrix as _im
            _im.record_negative(primary,
                                 f"primary blame: trade {trade_id}, loss={loss_amount:.4f}")
        except Exception:
            pass

        return record

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_record(self, trade_id: str) -> Optional[dict]:
        with self._lock:
            for r in self._records:
                if r.trade_id == trade_id:
                    return self._serialise(r)
        return None

    def recent_losses(self, limit: int = 20) -> List[dict]:
        with self._lock:
            return [self._serialise(r) for r in list(self._records)[:limit]]

    def top_blamed_modules(self, limit: int = 10) -> List[dict]:
        """Modules ranked by cumulative blame score across all loss trades."""
        with self._lock:
            cum  = dict(self._cumulative)
            cnt  = dict(self._trade_count)
        ranked = sorted(cum.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                "module_key":       k,
                "cumulative_blame": round(v, 3),
                "loss_appearances": cnt.get(k, 0),
                "avg_blame_per_loss": round(v / cnt[k], 3) if cnt.get(k, 0) > 0 else 0,
            }
            for k, v in ranked[:limit]
        ]

    def module_blame_profile(self, module_key: str) -> dict:
        """Full blame profile for one module."""
        with self._lock:
            appearances = [
                r for r in self._records
                if any(e.module_key == module_key for e in r.entries)
            ]
            primary_times = sum(
                1 for r in self._records if r.primary_cause == module_key
            )
        total = len(self._records)
        return {
            "module_key":       module_key,
            "total_loss_trades":  total,
            "appearances":        len(appearances),
            "primary_cause_times": primary_times,
            "appearance_rate":    round(len(appearances) / total, 3) if total > 0 else 0.0,
            "primary_cause_rate": round(primary_times / total, 3)    if total > 0 else 0.0,
            "cumulative_blame":   round(self._cumulative.get(module_key, 0.0), 3),
        }

    def summary(self) -> dict:
        with self._lock:
            total   = len(self._records)
            top     = self.top_blamed_modules(5)
            cum_cnt = len(self._cumulative)
        return {
            "total_loss_trades_attributed": total,
            "modules_with_blame_data":      cum_cnt,
            "top_blamed_modules":           top,
            "buffer_capacity":              MAX_RECORDS,
        }

    # ── Serialisation ─────────────────────────────────────────────────────────

    @staticmethod
    def _serialise(r: BlameRecord) -> dict:
        return {
            "trade_id":               r.trade_id,
            "loss_amount":            r.loss_amount,
            "entry_time":             r.entry_time,
            "exit_time":              r.exit_time,
            "primary_cause":          r.primary_cause,
            "primary_cause_score":    r.primary_cause_score,
            "root_cause_description": r.root_cause_description,
            "recorded_at":            r.recorded_at,
            "entries": [
                {
                    "module_key":         e.module_key,
                    "role":               e.role,
                    "influence_weight":   e.influence_weight,
                    "signal_value":       e.signal_value,
                    "signal_confidence":  e.signal_confidence,
                    "blame_score":        e.blame_score,
                    "was_deciding_factor": e.was_deciding_factor,
                }
                for e in r.entries
            ],
        }


# Singleton
blame_engine = BlameAttributionEngine()
