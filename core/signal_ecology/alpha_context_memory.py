"""
FTD-057-PHOENIX Phase 4 — Alpha Context Memory

Persists profitable RL contexts across sessions and amplifies localized
allocation when a known-profitable context recurs. Does NOT globally relax
filters — amplification is context-specific and bounded.

Context key format: "{regime}|{session_hour}|{strategy}"
(matches rl_engine make_context() format exactly)

Amplification rules:
  - Profitable context (avg_pnl > PROFIT_THRESH, n ≥ MIN_VISITS) → +BOOST_MULT
  - Toxic context (avg_pnl < TOXIC_THRESH, n ≥ MIN_VISITS) → BLOCK
  - Unknown context → pass-through (no amplification)
  - Boost is capped at MAX_BOOST_MULT regardless of confidence
"""
from __future__ import annotations

import json
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

from loguru import logger
from config import cfg


# ── Constants ──────────────────────────────────────────────────────────────────
MIN_VISITS       = 5       # minimum trade count before context is scored
PROFIT_THRESH    = 0.0     # avg_pnl > this = profitable context
TOXIC_THRESH     = -0.30   # avg_pnl < this = toxic (mirrors rl_engine)
BOOST_MULT       = 1.25    # size multiplier for known-profitable contexts
MAX_BOOST_MULT   = 1.50    # hard cap on amplification
PERSIST_PATH     = Path("data/alpha_context_memory.json")
SAVE_INTERVAL    = 60.0    # reduced 300→60: limit data loss to at most 1 min on crash
MAX_CONTEXTS     = 500     # maximum stored contexts (LRU eviction)


@dataclass
class ContextRecord:
    context_key:   str
    n_trades:      int   = 0
    total_pnl:     float = 0.0
    wins:          int   = 0
    losses:        int   = 0
    last_seen_ts:  int   = 0
    first_seen_ts: int   = field(default_factory=lambda: int(time.time() * 1000))

    @property
    def avg_pnl(self) -> float:
        return self.total_pnl / self.n_trades if self.n_trades > 0 else 0.0

    @property
    def win_rate(self) -> float:
        return self.wins / self.n_trades if self.n_trades > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "avg_pnl":  round(self.avg_pnl, 4),
            "win_rate": round(self.win_rate, 4),
        }


class AlphaContextMemory:
    """
    Persistent profitable-context amplifier. Thread-safe.
    Survives engine restarts via JSON persistence.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._contexts: Dict[str, ContextRecord] = {}
        self._last_save_ts: float = 0.0
        self._lookup_count: int = 0
        self._boost_count:  int = 0
        self._block_count:  int = 0

        self._load()

    # ── Record a trade outcome ─────────────────────────────────────────────────

    def record_outcome(
        self,
        regime: str,
        utc_hour: int,
        strategy: str,
        net_pnl: float,
    ) -> None:
        """
        Update context memory with a completed trade result.
        Called by the engine after every closed trade.
        """
        key = self._make_key(regime, utc_hour, strategy)
        with self._lock:
            rec = self._contexts.get(key)
            if rec is None:
                rec = ContextRecord(context_key=key)
                self._contexts[key] = rec
                # LRU eviction if over capacity
                if len(self._contexts) > MAX_CONTEXTS:
                    self._evict_lru()

            rec.n_trades    += 1
            rec.total_pnl   += net_pnl
            rec.last_seen_ts = int(time.time() * 1000)
            if net_pnl > 0:
                rec.wins += 1
            else:
                rec.losses += 1

            self._maybe_save()

    # ── Query amplification for a new signal ──────────────────────────────────

    def get_amplification(
        self,
        regime: str,
        utc_hour: int,
        strategy: str,
    ) -> Dict[str, Any]:
        """
        Returns a dict with keys:
          boost_mult:   float (1.0 = no change)
          context_type: "PROFITABLE" | "TOXIC" | "UNKNOWN"
          context_key:  str
          n_trades:     int
          avg_pnl:      float
          reason:       str
        """
        key = self._make_key(regime, utc_hour, strategy)
        with self._lock:
            self._lookup_count += 1
            rec = self._contexts.get(key)

            if rec is None or rec.n_trades < MIN_VISITS:
                return {
                    "boost_mult":   1.0,
                    "context_type": "UNKNOWN",
                    "context_key":  key,
                    "n_trades":     rec.n_trades if rec else 0,
                    "avg_pnl":      0.0,
                    "reason":       "insufficient_data",
                }

            avg = rec.avg_pnl

            if avg > PROFIT_THRESH:
                # Proportional boost: more profitable = bigger boost, capped
                raw_boost = 1.0 + (avg / max(abs(avg), 1.0)) * (BOOST_MULT - 1.0)
                boost = min(raw_boost, MAX_BOOST_MULT)
                self._boost_count += 1
                return {
                    "boost_mult":   round(boost, 3),
                    "context_type": "PROFITABLE",
                    "context_key":  key,
                    "n_trades":     rec.n_trades,
                    "avg_pnl":      round(avg, 4),
                    "reason":       f"known_profitable avg={avg:+.4f} n={rec.n_trades}",
                }
            elif avg < TOXIC_THRESH:
                self._block_count += 1
                return {
                    "boost_mult":   0.0,   # 0 = blocked by context memory
                    "context_type": "TOXIC",
                    "context_key":  key,
                    "n_trades":     rec.n_trades,
                    "avg_pnl":      round(avg, 4),
                    "reason":       f"toxic_context avg={avg:+.4f} n={rec.n_trades}",
                }
            else:
                return {
                    "boost_mult":   1.0,
                    "context_type": "NEUTRAL",
                    "context_key":  key,
                    "n_trades":     rec.n_trades,
                    "avg_pnl":      round(avg, 4),
                    "reason":       f"neutral avg={avg:+.4f} n={rec.n_trades}",
                }

    # ── Persistence ────────────────────────────────────────────────────────────

    def _make_key(self, regime: str, utc_hour: int, strategy: str) -> str:
        return f"{regime}|{utc_hour}|{strategy}"

    def _evict_lru(self) -> None:
        if not self._contexts:
            return
        oldest = min(self._contexts.values(), key=lambda r: r.last_seen_ts)
        del self._contexts[oldest.context_key]

    def _maybe_save(self) -> None:
        now = time.time()
        if now - self._last_save_ts >= SAVE_INTERVAL:
            self._save()

    def _save(self) -> None:
        try:
            PERSIST_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {k: v.to_dict() for k, v in self._contexts.items()}
            PERSIST_PATH.write_text(json.dumps(data, indent=2))
            self._last_save_ts = time.time()
        except Exception as exc:
            logger.warning(f"[FTD-057][ACM] Save failed: {exc}")

    def _load(self) -> None:
        if not PERSIST_PATH.exists():
            return
        try:
            raw = json.loads(PERSIST_PATH.read_text())
            for key, d in raw.items():
                rec = ContextRecord(
                    context_key=d.get("context_key", key),
                    n_trades=d.get("n_trades", 0),
                    total_pnl=d.get("total_pnl", 0.0),
                    wins=d.get("wins", 0),
                    losses=d.get("losses", 0),
                    last_seen_ts=d.get("last_seen_ts", 0),
                    first_seen_ts=d.get("first_seen_ts", 0),
                )
                self._contexts[key] = rec
            logger.info(f"[FTD-057][ACM] Loaded {len(self._contexts)} contexts")
        except Exception as exc:
            logger.warning(f"[FTD-057][ACM] Load failed (non-fatal): {exc}")

    def save(self) -> None:
        """Force an immediate save (call on engine shutdown)."""
        with self._lock:
            self._save()

    # ── Telemetry ──────────────────────────────────────────────────────────────

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            recs = list(self._contexts.values())
            profitable = [r for r in recs if r.n_trades >= MIN_VISITS and r.avg_pnl > PROFIT_THRESH]
            toxic      = [r for r in recs if r.n_trades >= MIN_VISITS and r.avg_pnl < TOXIC_THRESH]
            top5 = sorted(profitable, key=lambda r: r.avg_pnl, reverse=True)[:5]
            return {
                "module":            "AlphaContextMemory",
                "ftd":               "057",
                "total_contexts":    len(self._contexts),
                "profitable_count":  len(profitable),
                "toxic_count":       len(toxic),
                "lookup_count":      self._lookup_count,
                "boost_count":       self._boost_count,
                "block_count":       self._block_count,
                "top_profitable":    [r.to_dict() for r in top5],
                "ts":                int(time.time() * 1000),
            }

    def context_clusters(self, n: int = 20) -> List[Dict[str, Any]]:
        """Return all contexts sorted by avg_pnl descending."""
        with self._lock:
            recs = [r for r in self._contexts.values() if r.n_trades >= MIN_VISITS]
            return [
                r.to_dict()
                for r in sorted(recs, key=lambda r: r.avg_pnl, reverse=True)[:n]
            ]


# ── Singleton ──────────────────────────────────────────────────────────────────
alpha_context_memory = AlphaContextMemory()
