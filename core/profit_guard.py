"""
EOW Quant Engine — Profit Guard  (FTD-REF-026)
Self-protecting profitability guardrails.

Gate 1 — Profit Factor Frequency Gate:
  If profit_factor < 1.0 after MIN_TRADES_FOR_PF trades, the system is losing
  money on net.  The engine applies a frequency multiplier of FREQ_REDUCE_MULT
  (0.50) to the adjusted confidence, halving the effective rate of passing the
  confidence threshold — reducing trade frequency without hard-blocking.

Gate 2 — Fee Ratio Gate:
  If fee_cost / gross_tp_profit > FEE_RATIO_MAX (20%), the trade is blocked.
  This prevents small-notional trades where fees eat >20% of the expected gain.

Singleton: profit_guard
"""
from __future__ import annotations

from loguru import logger


# ── Thresholds ────────────────────────────────────────────────────────────────
PROFIT_FACTOR_MIN  = 1.0     # below this PF → reduce frequency
FEE_RATIO_MAX      = 0.50    # raised to 50% — signals already RR-filtered upstream
FREQ_REDUCE_MULT   = 0.80    # gentle 20% reduction instead of 50% halving
MIN_TRADES_FOR_PF  = 30      # need 30 trades before PF gate activates (not 10)
MAX_CONSEC_LOSSES  = 8       # hard-stop only after 8 consecutive losses (not 4)


class ProfitGuard:
    """
    Applies two profitability-aware gates before a new trade is opened.

    Usage:
      # Gate 1: scale confidence down when PF < 1
      mult = profit_guard.frequency_multiplier(profit_factor, n_trades)
      adjusted_conf = base_conf * mult

      # Gate 2: block if fees consume too much of the expected profit
      blocked, reason = profit_guard.check_fee_ratio(gross_tp_profit, fee_cost)
    """

    # ── Public ────────────────────────────────────────────────────────────────

    def frequency_multiplier(self, profit_factor: float, n_trades: int) -> float:
        """
        Returns a multiplier (0.0–1.0) to scale adjusted_confidence.

        Returns FREQ_REDUCE_MULT (0.50) when:
          • n_trades ≥ MIN_TRADES_FOR_PF, AND
          • profit_factor < PROFIT_FACTOR_MIN (1.0)

        Returns 1.0 in all other cases.
        """
        if n_trades >= MIN_TRADES_FOR_PF and profit_factor < PROFIT_FACTOR_MIN:
            logger.debug(
                f"[PROFIT-GUARD] PF={profit_factor:.3f}<1 after {n_trades} trades "
                f"— frequency multiplier={FREQ_REDUCE_MULT}"
            )
            return FREQ_REDUCE_MULT
        return 1.0

    def check_fee_ratio(
        self,
        gross_tp_profit: float,
        fee_cost: float,
    ) -> tuple[bool, str]:
        """
        Returns (blocked, reason).

        Blocks when fee_cost / gross_tp_profit > FEE_RATIO_MAX.
        Passes through if gross_tp_profit ≤ 0 (cannot compute ratio).
        """
        if gross_tp_profit <= 0:
            return False, ""
        ratio = fee_cost / gross_tp_profit
        if ratio > FEE_RATIO_MAX:
            reason = (
                f"HIGH_FEE_RATIO(fees={fee_cost:.4f} "
                f"= {ratio * 100:.1f}% of gross={gross_tp_profit:.4f}, "
                f"max={FEE_RATIO_MAX * 100:.0f}%)"
            )
            logger.debug(f"[PROFIT-GUARD] {reason}")
            return True, reason
        return False, ""

    def summary(self, profit_factor: float, n_trades: int) -> dict:
        """Human-readable guard state for /api/profit-guard."""
        mult = self.frequency_multiplier(profit_factor, n_trades)
        return {
            "profit_factor":        round(profit_factor, 4),
            "n_trades":             n_trades,
            "frequency_multiplier": mult,
            "pf_guard_active":      mult < 1.0,
            "fee_ratio_max":        FEE_RATIO_MAX,
            "min_trades_for_pf":    MIN_TRADES_FOR_PF,
            "max_consecutive_losses": MAX_CONSEC_LOSSES,
        }

    def hard_stop_required(
        self,
        *,
        profit_factor: float,
        n_trades: int,
        consecutive_losses: int,
    ) -> tuple[bool, str]:
        """
        Returns (blocked, reason) for full stop conditions.

        Hard-stop when both are true:
          • enough trade sample exists, and
          • strategy remains net-losing (PF < 1), and
          • consecutive losses exceed threshold.
        """
        if (
            n_trades >= MIN_TRADES_FOR_PF
            and profit_factor < PROFIT_FACTOR_MIN
            and consecutive_losses >= MAX_CONSEC_LOSSES
        ):
            reason = (
                f"PROFIT_GUARD_HARD_STOP("
                f"pf={profit_factor:.2f}<1.0,"
                f"consecutive_losses={consecutive_losses}>={MAX_CONSEC_LOSSES})"
            )
            logger.warning(f"[PROFIT-GUARD] {reason}")
            return True, reason
        return False, ""


# ── Module-level singleton ────────────────────────────────────────────────────
profit_guard = ProfitGuard()
