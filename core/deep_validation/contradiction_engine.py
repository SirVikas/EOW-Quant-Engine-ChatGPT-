"""
FTD-028 Part 1 — Contradiction Engine

Detects logical conflicts across system state.
Blocks report generation if critical contradictions are found.
"""
from __future__ import annotations
import time
from enum import Enum
from typing import Any, Dict, List


class Severity(str, Enum):
    ERROR = "ERROR"
    FLAG  = "FLAG"
    WARN  = "WARN"


class ContradictionEngine:
    """
    Scans system state for logical impossibilities.

    Rules:
        trades > 0  AND signals == 0  → ERROR  (trades without signals)
        pnl < 0     AND win_rate > 0.7 → FLAG   (losing money with high win rate → fee leak / bad sizing)
        risk_halted AND trades_active  → ERROR  (trading while risk says stop)
        drawdown > max_dd AND no halt  → ERROR  (DD breach without halt)
        equity < 0                     → ERROR  (impossible equity)
    """

    MODULE = "CONTRADICTION_ENGINE"
    PHASE  = "028"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        contradictions: List[Dict[str, Any]] = []
        block = False

        trades      = state.get("total_trades", 0) or 0
        signals     = state.get("total_signals", 0) or 0
        pnl         = state.get("total_pnl", 0.0) or 0.0
        win_rate    = state.get("win_rate", 0.0) or 0.0
        risk_halted = state.get("risk_halted", False)
        trades_active = state.get("trades_active", False)
        drawdown    = state.get("current_drawdown_pct", 0.0) or 0.0
        max_dd      = state.get("max_drawdown_pct", 0.15) or 0.15
        equity      = state.get("equity", 1.0)
        halted      = state.get("halted", False)

        # Rule 1: trades without signals
        if trades > 0 and signals == 0:
            contradictions.append(self._mk(
                "TRADES_WITHOUT_SIGNALS",
                Severity.ERROR,
                f"trades={trades} but signals={signals}; execution without signal source is impossible",
            ))
            block = True

        # Rule 2: negative PnL with suspiciously high win rate
        if pnl < 0 and win_rate > 0.70:
            contradictions.append(self._mk(
                "LOSING_WITH_HIGH_WIN_RATE",
                Severity.FLAG,
                f"total_pnl={pnl:.4f} but win_rate={win_rate:.2%}; likely fee/sizing issue",
            ))

        # Rule 3: risk halted but trades still active
        if risk_halted and trades_active:
            contradictions.append(self._mk(
                "TRADING_WHILE_RISK_HALTED",
                Severity.ERROR,
                "risk controller says HALT but active trades are being placed",
            ))
            block = True

        # Rule 4: drawdown breach without halt
        if drawdown > max_dd and not halted:
            contradictions.append(self._mk(
                "DD_BREACH_WITHOUT_HALT",
                Severity.ERROR,
                f"drawdown={drawdown:.2%} exceeds max_dd={max_dd:.2%} but engine is not halted",
            ))
            block = True

        # Rule 5: impossible equity
        if equity is not None and equity < 0:
            contradictions.append(self._mk(
                "NEGATIVE_EQUITY",
                Severity.ERROR,
                f"equity={equity:.4f} is negative — impossible state",
            ))
            block = True

        return {
            "module":          self.MODULE,
            "phase":           self.PHASE,
            "contradictions":  contradictions,
            "contradiction_count": len(contradictions),
            "block_report":    block,
            "passed":          len(contradictions) == 0,
            "snapshot_ts":     int(time.time() * 1000),
        }

    @staticmethod
    def _mk(code: str, severity: Severity, message: str) -> Dict[str, Any]:
        return {"code": code, "severity": severity.value, "message": message}
