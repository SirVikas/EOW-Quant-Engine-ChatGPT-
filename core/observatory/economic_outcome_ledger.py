"""
PHOENIX OBSERVATORY-X — Economic Outcome Ledger  [OX-MATURITY-02]

The single most important question in any advisory system:
  "Which recommendation actually made us more money?"

The Economic Outcome Ledger links each applied Observatory recommendation
to measurable economic outcomes:
  - PnL delta (actual profit/loss change in USDT)
  - Win Rate delta
  - Profit Factor delta
  - Trade count delta (did we take more/fewer good trades?)
  - Fee drag delta (did costs improve?)

Ledger entry lifecycle:
  PENDING     — recommendation applied, monitoring has not started
  MEASURING   — within the measurement window (30–100 trades)
  CONFIRMED   — economic outcome measured and confirmed
  INCONCLUSIVE — window passed, no clear signal

This answers the governance question:
  "Which Observatory intelligence layer actually improved our economics?"
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EconomicSnapshot:
    """Point-in-time economic metrics."""
    trade_count: int
    total_pnl_usdt: float
    win_rate: float
    profit_factor: float
    avg_fee_usdt: float
    equity_usdt: float
    captured_at: float = field(default_factory=time.time)


@dataclass
class LedgerEntry:
    entry_id: str
    rec_id: str
    rec_type: str
    rec_title: str
    investigation_id: str
    applied_at: float
    snapshot_before: EconomicSnapshot
    snapshot_after: Optional[EconomicSnapshot] = None
    measurement_trade_target: int = 100    # confirm after this many new trades
    status: str = "PENDING"               # PENDING | MEASURING | CONFIRMED | INCONCLUSIVE
    economic_verdict: str = "unknown"     # profitable | neutral | harmful | unknown
    pnl_delta: float = 0.0
    wr_delta: float = 0.0
    pf_delta: float = 0.0
    narrative: str = ""


class EconomicOutcomeLedger:
    """
    Tracks the economic impact of every applied Observatory recommendation.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: Dict[str, LedgerEntry] = {}

    # ── Registration ──────────────────────────────────────────────────────────

    def open_entry(
        self,
        rec_id: str,
        rec_type: str,
        rec_title: str,
        investigation_id: str,
        current_trade_count: int,
        current_pnl_usdt: float,
        current_wr: float,
        current_pf: float,
        current_avg_fee_usdt: float = 0.0,
        current_equity_usdt: float = 0.0,
    ) -> LedgerEntry:
        entry_id = f"EOL_{rec_id}_{int(time.time())}"
        snapshot = EconomicSnapshot(
            trade_count=current_trade_count,
            total_pnl_usdt=current_pnl_usdt,
            win_rate=current_wr,
            profit_factor=current_pf,
            avg_fee_usdt=current_avg_fee_usdt,
            equity_usdt=current_equity_usdt,
        )
        entry = LedgerEntry(
            entry_id=entry_id,
            rec_id=rec_id,
            rec_type=rec_type,
            rec_title=rec_title,
            investigation_id=investigation_id,
            applied_at=time.time(),
            snapshot_before=snapshot,
            status="MEASURING",
        )
        with self._lock:
            self._entries[rec_id] = entry
        return entry

    # ── Measurement ───────────────────────────────────────────────────────────

    def record_outcome(
        self,
        rec_id: str,
        current_trade_count: int,
        current_pnl_usdt: float,
        current_wr: float,
        current_pf: float,
        current_avg_fee_usdt: float = 0.0,
        current_equity_usdt: float = 0.0,
    ) -> Optional[LedgerEntry]:
        with self._lock:
            entry = self._entries.get(rec_id)
            if not entry or entry.status == "CONFIRMED":
                return None

            new_trades = current_trade_count - entry.snapshot_before.trade_count
            if new_trades < entry.measurement_trade_target:
                return None  # still accumulating

            snapshot_after = EconomicSnapshot(
                trade_count=current_trade_count,
                total_pnl_usdt=current_pnl_usdt,
                win_rate=current_wr,
                profit_factor=current_pf,
                avg_fee_usdt=current_avg_fee_usdt,
                equity_usdt=current_equity_usdt,
            )
            entry.snapshot_after = snapshot_after
            entry.pnl_delta = current_pnl_usdt - entry.snapshot_before.total_pnl_usdt
            entry.wr_delta  = current_wr - entry.snapshot_before.win_rate
            entry.pf_delta  = current_pf - entry.snapshot_before.profit_factor
            entry.status    = "CONFIRMED"
            entry.economic_verdict = self._verdict(entry.pnl_delta, entry.wr_delta, entry.pf_delta)
            entry.narrative = self._build_narrative(entry)

        return entry

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, rec_id: str) -> Optional[dict]:
        with self._lock:
            e = self._entries.get(rec_id)
        return self._serialise(e) if e else None

    def all_entries(self, status_filter: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = list(self._entries.values())
        if status_filter:
            items = [e for e in items if e.status == status_filter]
        return [self._serialise(e) for e in sorted(items, key=lambda x: x.applied_at, reverse=True)]

    def top_performers(self, n: int = 5) -> List[dict]:
        """Top N recommendations by PnL delta (confirmed only)."""
        with self._lock:
            items = [e for e in self._entries.values() if e.status == "CONFIRMED"]
        items.sort(key=lambda e: e.pnl_delta, reverse=True)
        return [self._serialise(e) for e in items[:n]]

    def worst_performers(self, n: int = 5) -> List[dict]:
        with self._lock:
            items = [e for e in self._entries.values() if e.status == "CONFIRMED"]
        items.sort(key=lambda e: e.pnl_delta)
        return [self._serialise(e) for e in items[:n]]

    def summary(self) -> dict:
        with self._lock:
            items = list(self._entries.values())
        confirmed = [e for e in items if e.status == "CONFIRMED"]
        profitable = [e for e in confirmed if e.economic_verdict == "profitable"]
        harmful    = [e for e in confirmed if e.economic_verdict == "harmful"]
        total_pnl_impact = sum(e.pnl_delta for e in confirmed)
        return {
            "total_entries":        len(items),
            "confirmed":            len(confirmed),
            "profitable_count":     len(profitable),
            "harmful_count":        len(harmful),
            "neutral_count":        len(confirmed) - len(profitable) - len(harmful),
            "total_pnl_impact_usdt": round(total_pnl_impact, 4),
            "avg_wr_delta":         round(sum(e.wr_delta for e in confirmed) / max(1, len(confirmed)), 4),
            "avg_pf_delta":         round(sum(e.pf_delta for e in confirmed) / max(1, len(confirmed)), 4),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _verdict(pnl_delta: float, wr_delta: float, pf_delta: float) -> str:
        if pnl_delta > 0 and (wr_delta > 0.01 or pf_delta > 0.02):
            return "profitable"
        if pnl_delta < -0.5 or wr_delta < -0.03 or pf_delta < -0.05:
            return "harmful"
        return "neutral"

    @staticmethod
    def _build_narrative(e: LedgerEntry) -> str:
        direction = "improved" if e.pnl_delta >= 0 else "worsened"
        return (
            f"After {e.measurement_trade_target} trades following '{e.rec_title}': "
            f"PnL {direction} by {e.pnl_delta:+.2f} USDT, "
            f"WR {e.wr_delta:+.3f}, PF {e.pf_delta:+.3f}. "
            f"Verdict: {e.economic_verdict.upper()}."
        )

    @staticmethod
    def _serialise(e: LedgerEntry) -> dict:
        def _snap(s: Optional[EconomicSnapshot]) -> Optional[dict]:
            if not s:
                return None
            return {
                "trade_count":    s.trade_count,
                "total_pnl_usdt": s.total_pnl_usdt,
                "win_rate":       s.win_rate,
                "profit_factor":  s.profit_factor,
                "avg_fee_usdt":   s.avg_fee_usdt,
                "equity_usdt":    s.equity_usdt,
                "captured_at":    s.captured_at,
            }
        return {
            "entry_id":           e.entry_id,
            "rec_id":             e.rec_id,
            "rec_type":           e.rec_type,
            "rec_title":          e.rec_title,
            "investigation_id":   e.investigation_id,
            "applied_at":         e.applied_at,
            "status":             e.status,
            "economic_verdict":   e.economic_verdict,
            "pnl_delta":          e.pnl_delta,
            "wr_delta":           e.wr_delta,
            "pf_delta":           e.pf_delta,
            "narrative":          e.narrative,
            "snapshot_before":    _snap(e.snapshot_before),
            "snapshot_after":     _snap(e.snapshot_after),
        }


# Singleton
economic_outcome_ledger = EconomicOutcomeLedger()
