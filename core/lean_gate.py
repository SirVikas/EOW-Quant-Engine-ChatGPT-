"""
EOW Quant Engine — core/lean_gate.py
Lean Gate: 5 essential checks that replace the 38-gate legacy pipeline.

Design principle: let trades flow; block only what is truly dangerous.

Gate 1  SL distance    — SL must be ≥ MIN_SL_DIST_PCT from entry (sub-tick noise filter)
Gate 2  RR ratio       — TP/SL distance ≥ MIN_RR (avoid fee-uneconomic setups)
Gate 3  Fee economy    — round-trip fees < MAX_FEE_RATIO of expected TP profit
Gate 4  Loss streak    — pause after MAX_CONSEC_LOSSES consecutive session losses
Gate 5  Daily drawdown — hard stop when session equity drops > MAX_DAILY_DD_PCT

All thresholds are tunable via config. No bootstrap dependency, no external
singleton state — LeanGate is stateless per call; the caller supplies live values.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


# ── Thresholds ────────────────────────────────────────────────────────────────

MIN_SL_DIST_PCT   = 0.15    # SL must be ≥ 0.15% from entry (raised from 0.05 — ultra-tight SLs are fee-eaten at any notional)
MIN_RR            = 1.8     # minimum risk-reward ratio (raised from 1.5)
MAX_FEE_RATIO     = 0.25    # fees must be < 25% of expected TP profit
MAX_CONSEC_LOSSES = 6       # pause after this many consecutive session losses
MAX_DAILY_DD_PCT  = 12.0    # hard stop: session equity down > 12%


@dataclass
class LeanResult:
    execute:  bool
    reason:   str
    rr:       float = 0.0
    sl_dist_pct: float = 0.0


class LeanGate:
    """
    Stateless per-call gate.  Caller supplies all live values; no singleton
    queries, no historical data lookups, no bootstrap wait.

    Usage:
        result = lean_gate.check(
            entry=sig.entry_price,
            stop_loss=sig.stop_loss,
            take_profit=sig.take_profit,
            notional=qty * sig.entry_price,
            consecutive_losses=session_consecutive_losses,
            session_dd_pct=session_drawdown_pct,
        )
        if not result.execute:
            return  # skip this trade
    """

    def __init__(self):
        logger.info(
            f"[LEAN-GATE] activated | "
            f"min_sl={MIN_SL_DIST_PCT}% min_rr={MIN_RR} "
            f"max_fee_ratio={MAX_FEE_RATIO} gate3=ALWAYS_ON "
            f"max_consec_loss={MAX_CONSEC_LOSSES} "
            f"max_daily_dd={MAX_DAILY_DD_PCT}%"
        )

    def check(
        self,
        entry:               float,
        stop_loss:           float,
        take_profit:         float,
        notional:            float,
        consecutive_losses:  int,
        session_dd_pct:      float,
        side:                str = "",
    ) -> LeanResult:
        """
        Run all five gates in order.  Returns on first failure.

        Args:
            entry:               signal entry price
            stop_loss:           signal stop-loss price
            take_profit:         signal take-profit price
            notional:            qty × entry price (for fee calculation)
            consecutive_losses:  number of consecutive losing trades this session
            session_dd_pct:      current session equity drawdown as a percentage
            side:                "LONG" or "SHORT" (optional, for logging)
        """
        if entry <= 0:
            return LeanResult(execute=False, reason="ZERO_ENTRY")

        # ── Gate 1: SL distance ───────────────────────────────────────────────
        sl_dist      = abs(entry - stop_loss)
        sl_dist_pct  = sl_dist / entry * 100 if entry > 0 else 0.0
        if sl_dist_pct < MIN_SL_DIST_PCT:
            return LeanResult(
                execute=False,
                reason=f"SL_TOO_TIGHT({sl_dist_pct:.4f}%<{MIN_SL_DIST_PCT}%)",
                sl_dist_pct=sl_dist_pct,
            )

        # ── Gate 2: RR ratio ──────────────────────────────────────────────────
        tp_dist = abs(take_profit - entry)
        rr      = tp_dist / sl_dist if sl_dist > 0 else 0.0
        if rr < MIN_RR:
            return LeanResult(
                execute=False,
                reason=f"RR_LOW({rr:.2f}<{MIN_RR})",
                rr=rr, sl_dist_pct=sl_dist_pct,
            )

        # ── Gate 3: Fee economy ───────────────────────────────────────────────
        # Always active. PAPER_SPEED SL widened to 2× ATR floor (0.2%+) so
        # notional is large enough that fee_ratio ≈ 20% < 25% threshold.
        round_trip_fee = notional * (cfg.TAKER_FEE * 2)
        gross_tp       = tp_dist * (notional / entry) if entry > 0 else 0.0
        if gross_tp > 0:
            fee_ratio = round_trip_fee / gross_tp
            if fee_ratio > MAX_FEE_RATIO:
                return LeanResult(
                    execute=False,
                    reason=f"FEE_HEAVY({fee_ratio*100:.1f}%>{MAX_FEE_RATIO*100:.0f}%)",
                    rr=rr, sl_dist_pct=sl_dist_pct,
                )

        # ── Gate 4: Loss streak ───────────────────────────────────────────────
        if consecutive_losses >= MAX_CONSEC_LOSSES:
            return LeanResult(
                execute=False,
                reason=f"LOSS_STREAK({consecutive_losses}>={MAX_CONSEC_LOSSES})",
                rr=rr, sl_dist_pct=sl_dist_pct,
            )

        # ── Gate 5: Daily drawdown ────────────────────────────────────────────
        if session_dd_pct >= MAX_DAILY_DD_PCT:
            return LeanResult(
                execute=False,
                reason=f"DAILY_DD({session_dd_pct:.1f}%>={MAX_DAILY_DD_PCT}%)",
                rr=rr, sl_dist_pct=sl_dist_pct,
            )

        logger.debug(
            f"[LEAN-GATE] PASS {side} entry={entry:.4f} "
            f"sl_dist={sl_dist_pct:.3f}% rr={rr:.2f} "
            f"consec_loss={consecutive_losses} dd={session_dd_pct:.1f}%"
        )
        return LeanResult(
            execute=True, reason="OK",
            rr=round(rr, 3), sl_dist_pct=round(sl_dist_pct, 4),
        )

    def summary(self) -> dict:
        return {
            "module":           "LEAN_GATE",
            "min_sl_dist_pct":  MIN_SL_DIST_PCT,
            "min_rr":           MIN_RR,
            "max_fee_ratio":    MAX_FEE_RATIO,
            "max_consec_losses": MAX_CONSEC_LOSSES,
            "max_daily_dd_pct": MAX_DAILY_DD_PCT,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
lean_gate = LeanGate()
