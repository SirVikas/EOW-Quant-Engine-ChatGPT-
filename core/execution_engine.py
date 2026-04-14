"""
EOW Quant Engine — Execution Engine  (FTD-REF-023 + FTD-REF-024)
Realistic trade price simulation: slippage, spread, fees.
FTD-REF-024 adds: fee-aware trade rejection gate.

Applies before recording PnL so that backtested/live metrics reflect
true costs rather than mid-price fantasy fills.

Formula:
  entry_price = mid_price + slippage + half_spread   (buying)
  exit_price  = mid_price - slippage - half_spread   (selling)
  fee         = notional × FEE_RATE  (per leg)
  net_pnl     = (exit_price - entry_price) × qty - 2 × fee

Slippage model:
  base_slippage = mid_price × SLIPPAGE_BASE_PCT
  atr_component = atr_abs   × SLIPPAGE_ATR_FACTOR   (optional, zero if not provided)
  total_slip    = base_slippage + atr_component
  Capped at SLIPPAGE_MAX_PCT × mid_price.

Spread model:
  effective_spread = max(raw_spread, SPREAD_MIN_PCT × mid_price)

Fee-aware gate (FTD-REF-024):
  should_reject_for_fees(expected_gross_profit, notional) → (reject, reason)
  Rejects when expected_gross_profit < round-trip fees (i.e. trade cannot
  even cover its own cost regardless of outcome).
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger


# ── Cost constants ─────────────────────────────────────────────────────────────
SLIPPAGE_BASE_PCT   = 0.0003   # 0.03% of price — baseline market impact
SLIPPAGE_ATR_FACTOR = 0.10     # 10% of ATR added to slippage in volatile markets
SLIPPAGE_MAX_PCT    = 0.0010   # cap at 0.10% of price
SPREAD_MIN_PCT      = 0.0002   # minimum effective spread (0.02%)
FEE_RATE            = 0.00075  # 0.075% per leg (Binance Futures taker default)


@dataclass
class ExecutionResult:
    entry_price:    float   # realistic fill price on entry
    exit_price:     float   # realistic fill price on exit
    fee_entry:      float   # fee paid at entry (USDT)
    fee_exit:       float   # fee paid at exit  (USDT)
    slippage_used:  float   # total slippage applied (price units)
    spread_used:    float   # total spread applied (price units, full round-trip)
    net_pnl:        float   # (exit - entry) × qty - fees
    qty:            float


class ExecutionEngine:
    """
    Stateless realistic execution simulator.
    Call simulate_trade() with mid prices to get adjusted PnL.
    """

    def simulate_entry(
        self,
        mid_price: float,
        raw_spread: float = 0.0,
        atr_abs:    float = 0.0,
        side:       str   = "BUY",   # "BUY" or "SELL"
    ) -> float:
        """
        Return the realistic fill price for an entry order.
        BUY pays the ask (mid + slippage + half_spread).
        SELL receives the bid (mid - slippage - half_spread).
        """
        slip         = self._slippage(mid_price, atr_abs)
        half_spread  = max(raw_spread, SPREAD_MIN_PCT * mid_price) / 2.0

        if side.upper() == "BUY":
            return mid_price + slip + half_spread
        return mid_price - slip - half_spread

    def simulate_exit(
        self,
        mid_price: float,
        raw_spread: float = 0.0,
        atr_abs:    float = 0.0,
        side:       str   = "SELL",   # opposite of entry side
    ) -> float:
        """
        Return the realistic fill price for an exit order.
        Exit BUY (close long) → SELL side.
        Exit SELL (close short) → BUY side.
        """
        slip        = self._slippage(mid_price, atr_abs)
        half_spread = max(raw_spread, SPREAD_MIN_PCT * mid_price) / 2.0

        if side.upper() == "SELL":
            return mid_price - slip - half_spread
        return mid_price + slip + half_spread

    def simulate_trade(
        self,
        entry_mid:  float,
        exit_mid:   float,
        qty:        float,
        raw_spread: float = 0.0,
        atr_abs:    float = 0.0,
        direction:  str   = "LONG",   # "LONG" or "SHORT"
    ) -> ExecutionResult:
        """
        Full round-trip simulation.
        Returns ExecutionResult with adjusted prices and net PnL.
        """
        slip_entry = self._slippage(entry_mid, atr_abs)
        slip_exit  = self._slippage(exit_mid,  atr_abs)
        hs_entry   = max(raw_spread, SPREAD_MIN_PCT * entry_mid) / 2.0
        hs_exit    = max(raw_spread, SPREAD_MIN_PCT * exit_mid)  / 2.0

        if direction.upper() == "LONG":
            entry_price = entry_mid + slip_entry + hs_entry
            exit_price  = exit_mid  - slip_exit  - hs_exit
        else:  # SHORT
            entry_price = entry_mid - slip_entry - hs_entry
            exit_price  = exit_mid  + slip_exit  + hs_exit

        notional_entry = entry_price * qty
        notional_exit  = exit_price  * qty
        fee_entry      = notional_entry * FEE_RATE
        fee_exit       = notional_exit  * FEE_RATE

        if direction.upper() == "LONG":
            gross_pnl = (exit_price - entry_price) * qty
        else:
            gross_pnl = (entry_price - exit_price) * qty

        net_pnl = gross_pnl - fee_entry - fee_exit

        result = ExecutionResult(
            entry_price   = round(entry_price,   6),
            exit_price    = round(exit_price,    6),
            fee_entry     = round(fee_entry,     6),
            fee_exit      = round(fee_exit,      6),
            slippage_used = round(slip_entry + slip_exit, 6),
            spread_used   = round(hs_entry + hs_exit,     6),
            net_pnl       = round(net_pnl,       6),
            qty           = qty,
        )

        logger.debug(
            f"[EXEC-ENG] {direction} entry={result.entry_price:.4f} "
            f"exit={result.exit_price:.4f} slip={result.slippage_used:.4f} "
            f"fees={result.fee_entry + result.fee_exit:.4f} "
            f"net_pnl={result.net_pnl:.4f}"
        )
        return result

    def fee_for_notional(self, notional: float) -> float:
        """Single-leg fee estimate (useful for pre-trade cost check)."""
        return notional * FEE_RATE

    def should_reject_for_fees(
        self,
        expected_gross_profit: float,
        notional: float,
    ) -> tuple[bool, str]:
        """
        FTD-REF-024: Fee-aware trade rejection gate.
        Returns (reject=True, reason) when the expected TP gross profit
        would not even cover the round-trip trading fees — the trade has
        no mathematical chance of a net-positive result.

        expected_gross_profit — abs(take_profit - entry) × qty  (USDT)
        notional              — entry_price × qty                (USDT)
        """
        fee_round_trip = notional * FEE_RATE * 2
        if expected_gross_profit < fee_round_trip:
            return (
                True,
                f"FEE_EXCEEDS_PROFIT("
                f"profit={expected_gross_profit:.4f}"
                f"<fees={fee_round_trip:.4f})",
            )
        return False, ""

    # ── Internals ─────────────────────────────────────────────────────────────

    @staticmethod
    def _slippage(price: float, atr_abs: float = 0.0) -> float:
        base = price * SLIPPAGE_BASE_PCT
        atr_component = atr_abs * SLIPPAGE_ATR_FACTOR
        return min(price * SLIPPAGE_MAX_PCT, base + atr_component)

    def cost_summary(self) -> dict:
        return {
            "slippage_base_pct":   SLIPPAGE_BASE_PCT,
            "slippage_atr_factor": SLIPPAGE_ATR_FACTOR,
            "slippage_max_pct":    SLIPPAGE_MAX_PCT,
            "spread_min_pct":      SPREAD_MIN_PCT,
            "fee_rate_per_leg":    FEE_RATE,
            "fee_round_trip":      FEE_RATE * 2,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
execution_engine = ExecutionEngine()
