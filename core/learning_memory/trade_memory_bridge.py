"""
Trade Memory Bridge — connects trade-close events to LearningMemoryOrchestrator.

The LMO was designed for FTD-029 parameter-optimisation cycles. This bridge
translates closed TradeRecord outcomes into the same record format so trade
patterns crystallise using the existing PatternEngine, NegativeMemory, and
ForgettingEngine — no new storage infrastructure required.

Pattern key produced:
  (REGIME, VOLATILITY, SYMBOL, STRATEGY_ID, UP|DOWN)
  e.g. (MEAN_REVERTING, MEDIUM, BTCUSDT, MR_PAPER_SPEED, UP)

Pattern formation threshold (inherited from PatternEngine):
  20+ records + confidence ≥ 70 + trades in 3+ distinct UTC hours
  → utc_hour is passed as "timeframe" to generate context diversity

Call record_trade() at every trade close alongside signal_truth_engine.record_outcome().
"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict

from loguru import logger

from core.learning_memory import learning_memory_orchestrator

# ATR → volatility tier mapping
_ATR_LOW_THRESH  = 1.0   # atr_pct < 1.0% = LOW
_ATR_HIGH_THRESH = 3.0   # atr_pct > 3.0% = HIGH

# Net PnL below this triggers an extra negative-memory hit (catastrophic loss)
_CATASTROPHIC_PNL = -2.0


def _volatility_tier(atr_pct: float) -> str:
    if atr_pct < _ATR_LOW_THRESH:
        return "LOW"
    if atr_pct < _ATR_HIGH_THRESH:
        return "MEDIUM"
    return "HIGH"


class TradeMemoryBridge:
    """
    Thin adapter: trade outcome → LMO after_resolve_cycle() format.

    Thread-safe — LMO sub-modules carry their own locks; this class only
    guards its own counters.
    """

    def __init__(self) -> None:
        self._lock            = threading.RLock()
        self._total_recorded  = 0
        self._total_wins      = 0
        self._total_losses    = 0
        logger.info("[TRADE_MEMORY_BRIDGE] Initialized — trade→memory pipeline active")

    # ── Primary API ────────────────────────────────────────────────────────────

    def record_trade(
        self,
        trade_id:    str,
        symbol:      str,
        regime:      str,
        strategy_id: str,
        side:        str,       # "LONG" | "SHORT" (or "BUY" | "SELL")
        net_pnl:     float,
        confidence:  float = 0.51,
        atr_pct:     float = 1.5,
        utc_hour:    int   = 0,
    ) -> None:
        """
        Feed one closed trade into the learning memory pipeline.

        Maps to LMO format:
          cycle_id  = trade_id
          parameter = strategy_id   ("what decision was made")
          direction = UP (LONG) | DOWN (SHORT)
          rollback  = net_pnl < 0  ("did this decision fail?")
          timeframe = str(utc_hour) ("when" → drives context diversity for pattern formation)
        """
        if not learning_memory_orchestrator._enabled:
            return

        is_win   = net_pnl > 0
        direction = "UP" if side.upper() in ("LONG", "BUY") else "DOWN"
        volatility = _volatility_tier(atr_pct)

        with self._lock:
            self._total_recorded += 1
            if is_win:
                self._total_wins += 1
            else:
                self._total_losses += 1

        context = {
            "regime":     (regime or "UNKNOWN").upper(),
            "volatility": volatility,
            "instrument": symbol or "UNKNOWN",
            # utc_hour as timeframe → each hour produces a distinct context bucket,
            # allowing PatternEngine to accumulate the 3 required distinct contexts.
            "timeframe":  str(utc_hour),
        }

        # before/after encode trade direction (not PnL magnitude) so LMO's
        # "UP if after > before" produces the correct pattern key direction.
        # PnL outcome is captured via rollback=did_rollback and score_delta.
        _before = 0.0 if direction == "UP" else 1.0
        _after  = 1.0 if direction == "UP" else 0.0

        applied_changes = [{
            "parameter": strategy_id or "UNKNOWN",
            "before":    _before,
            "after":     _after,
            "rationale": (
                f"{side} {symbol} net_pnl={net_pnl:+.4f} "
                f"conf={confidence:.3f} regime={regime}"
            ),
        }]

        # LMO maps rollback=True → pattern failure → negative memory
        rollbacks = [{"parameter": strategy_id or "UNKNOWN"}] if not is_win else []

        pre_score  = round(min(confidence * 100, 100.0), 2)
        post_score = pre_score + (10.0 if is_win else -10.0)

        try:
            learning_memory_orchestrator.after_resolve_cycle(
                cycle_id        = trade_id,
                applied_changes = applied_changes,
                rollbacks       = rollbacks,
                context         = context,
                pre_meta_score  = pre_score,
                post_meta_score = post_score,
                ai_mode         = "TRADE",
                contradiction   = False,
            )

            # Extra negative-memory hit for catastrophic losses (net_pnl < -$2)
            # This accelerates the permanent-ban threshold for toxic contexts.
            if net_pnl < _CATASTROPHIC_PNL:
                _key = learning_memory_orchestrator._engine.make_key_from_context(
                    regime     = context["regime"],
                    volatility = volatility,
                    instrument = symbol or "UNKNOWN",
                    parameter  = strategy_id or "UNKNOWN",
                    direction  = direction,
                )
                _pat = learning_memory_orchestrator._engine.get_pattern(_key)
                _samples = _pat.samples if _pat else 0
                learning_memory_orchestrator._neg_memory.record_rollback(_key, current_samples=_samples)
                logger.warning(
                    f"[TRADE_MEMORY_BRIDGE] Catastrophic loss → extra negative-memory entry: "
                    f"{symbol} {strategy_id} pnl={net_pnl:+.4f}"
                )

        except Exception as exc:
            # Non-fatal — memory pipeline must never crash the trading engine
            logger.warning(f"[TRADE_MEMORY_BRIDGE] record_trade failed (non-fatal): {exc}")

    # ── Telemetry ──────────────────────────────────────────────────────────────

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            total = self._total_recorded
            return {
                "module":          "TradeMemoryBridge",
                "total_recorded":  total,
                "total_wins":      self._total_wins,
                "total_losses":    self._total_losses,
                "win_rate":        round(self._total_wins / total, 4) if total > 0 else 0.0,
                "lmo_enabled":     learning_memory_orchestrator._enabled,
                "lmo_cycle_count": learning_memory_orchestrator._cycle_count,
                "lmo_records":     learning_memory_orchestrator._store.count(),
                "lmo_patterns_formed": learning_memory_orchestrator._indexer.formed_count(),
                "lmo_negative_memory": learning_memory_orchestrator._neg_memory.count(),
                "ts":              int(time.time() * 1000),
            }


# ── Singleton ──────────────────────────────────────────────────────────────────
trade_memory_bridge = TradeMemoryBridge()
