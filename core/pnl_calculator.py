"""
EOW Quant Engine — Pure PnL Calculator  (Step 2)
Formula: NetPnL = GrossProfit − BinanceFees − SlippageCosts − BorrowingInterest
Everything is in USDT.  Truth over vanity.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import List, Optional
from loguru import logger

from config import cfg


# ── Trade Record ─────────────────────────────────────────────────────────────

@dataclass
class TradeRecord:
    trade_id:       str
    symbol:         str
    side:           str          # "BUY" | "SELL"
    entry_price:    float
    exit_price:     float
    qty:            float        # base asset qty
    entry_ts:       int          # epoch ms
    exit_ts:        int
    is_short:       bool = False
    margin_rate:    float = 0.0  # annual borrow rate (fraction)
    strategy_id:    str = "default"
    regime:         str = "UNKNOWN"
    mode:           str = "PAPER"

    order_type:     str   = "MARKET"  # "MARKET" | "LIMIT" — affects fees & slippage

    # Computed fields (filled by calculator)
    gross_pnl:      float = 0.0
    fee_entry:      float = 0.0
    fee_exit:       float = 0.0
    slippage_cost:  float = 0.0
    borrow_cost:    float = 0.0
    net_pnl:        float = 0.0
    net_pnl_pct:    float = 0.0
    r_multiple:     float = 0.0   # net_pnl / initial_risk


# ── PnL Calculator ────────────────────────────────────────────────────────────

class PurePnLCalculator:
    """
    Calculates the true bankable profit for every trade by deducting:
      • Binance maker/taker fees (configurable, defaults to 0.04% taker)
      • Slippage costs (entry + exit, estimated from config)
      • Borrowing/margin interest (for short positions)
    Also maintains running session metrics: equity curve, MDD, Sharpe, etc.
    """

    def __init__(self, starting_capital: float = None):
        self.capital       = starting_capital or cfg.INITIAL_CAPITAL
        self.peak_equity   = self.capital
        self.trades:       List[TradeRecord] = []
        self._equity_curve: List[dict]       = []
        self._log_equity(label="START")

    # ── Core Calculation ────────────────────────────────────────────────────

    def calculate(
        self,
        trade: TradeRecord,
        entry_fee_type: str = "taker",
        exit_fee_type:  str = "taker",
        initial_risk_usdt: float = 0.0,
    ) -> TradeRecord:
        """
        Fill all cost/profit fields on the TradeRecord and return it.
        """
        notional_entry = trade.entry_price * trade.qty
        notional_exit  = trade.exit_price  * trade.qty

        # ── Gross PnL ──────────────────────────────────────────────────────
        if trade.is_short:
            trade.gross_pnl = (trade.entry_price - trade.exit_price) * trade.qty
        else:
            trade.gross_pnl = (trade.exit_price - trade.entry_price) * trade.qty

        # ── Binance Fees ───────────────────────────────────────────────────
        # Limit orders (maker) pay half the fee vs market orders (taker)
        if trade.order_type == "LIMIT":
            entry_rate = cfg.MAKER_FEE
            exit_rate  = cfg.MAKER_FEE
        else:
            entry_rate = cfg.MAKER_FEE if entry_fee_type == "maker" else cfg.TAKER_FEE
            exit_rate  = cfg.MAKER_FEE if exit_fee_type  == "maker" else cfg.TAKER_FEE
        trade.fee_entry = notional_entry * entry_rate
        trade.fee_exit  = notional_exit  * exit_rate

        # ── Slippage ───────────────────────────────────────────────────────
        # Limit orders post at a known price — no market impact slippage
        if trade.order_type == "LIMIT":
            trade.slippage_cost = 0.0
        else:
            trade.slippage_cost = (notional_entry + notional_exit) * cfg.SLIPPAGE_EST

        # ── Borrowing Interest (short margin) ──────────────────────────────
        if trade.is_short and trade.margin_rate > 0:
            hold_hours = (trade.exit_ts - trade.entry_ts) / 3_600_000
            daily_rate = trade.margin_rate / 365
            trade.borrow_cost = notional_entry * daily_rate * (hold_hours / 24)
        else:
            trade.borrow_cost = 0.0

        # ── Net PnL ────────────────────────────────────────────────────────
        total_costs = (
            trade.fee_entry
            + trade.fee_exit
            + trade.slippage_cost
            + trade.borrow_cost
        )
        trade.net_pnl = trade.gross_pnl - total_costs
        trade.net_pnl_pct = (trade.net_pnl / notional_entry) * 100 if notional_entry else 0.0
        trade.r_multiple  = (trade.net_pnl / initial_risk_usdt) if initial_risk_usdt else 0.0

        # ── Update Engine State ────────────────────────────────────────────
        self.capital += trade.net_pnl
        self.trades.append(trade)
        self._log_equity(label=f"TRADE:{trade.trade_id}")

        logger.info(
            f"[PNL] {trade.symbol} {trade.side} | "
            f"Gross={trade.gross_pnl:+.4f} Fees={total_costs:.4f} "
            f"Net={trade.net_pnl:+.4f} USDT ({trade.net_pnl_pct:+.2f}%)"
        )
        return trade

    # ── Session Metrics ─────────────────────────────────────────────────────

    @property
    def session_stats(self) -> dict:
        if not self.trades:
            return self._empty_stats()

        nets  = [t.net_pnl for t in self.trades]
        wins  = [p for p in nets if p > 0]
        losses= [p for p in nets if p <= 0]

        win_rate      = len(wins) / len(nets) if nets else 0
        avg_win       = sum(wins)  / len(wins)   if wins   else 0
        avg_loss      = sum(losses)/ len(losses)  if losses else 0
        profit_factor = (sum(wins) / abs(sum(losses))) if losses else 99.99
        total_net     = sum(nets)
        total_fees    = sum(t.fee_entry + t.fee_exit for t in self.trades)
        total_slippage= sum(t.slippage_cost for t in self.trades)

        # Max Drawdown
        mdd           = self._max_drawdown()
        sharpe        = self._sharpe_ratio(nets)

        return {
            "capital":        round(self.capital, 4),
            "total_net_pnl":  round(total_net, 4),
            "total_trades":   len(self.trades),
            "win_rate":       round(win_rate * 100, 2),
            "profit_factor":  round(profit_factor, 3),
            "avg_win_usdt":   round(avg_win, 4),
            "avg_loss_usdt":  round(avg_loss, 4),
            "max_drawdown_pct": round(mdd * 100, 2),
            "sharpe_ratio":   round(sharpe, 3),
            "total_fees_paid": round(total_fees, 4),
            "total_slippage":  round(total_slippage, 4),
            "equity_curve":    self._equity_curve,
        }

    def _max_drawdown(self) -> float:
        if not self._equity_curve:
            return 0.0
        peak = 0.0
        mdd  = 0.0
        for pt in self._equity_curve:
            eq   = pt["equity"]
            peak = max(peak, eq)
            dd   = (peak - eq) / peak if peak else 0
            mdd  = max(mdd, dd)
        return mdd

    def _sharpe_ratio(self, pnl_list: list, risk_free: float = 0.0) -> float:
        if len(pnl_list) < 2:
            return 0.0
        import statistics
        mean = statistics.mean(pnl_list) - risk_free
        std  = statistics.stdev(pnl_list)
        result = (mean / std * (252 ** 0.5)) if std else 0.0
        return 0.0 if (result != result or result == float('inf') or result == float('-inf')) else round(result, 3)

    def _log_equity(self, label: str = ""):
        self._equity_curve.append({
            "ts":     int(time.time() * 1000),
            "equity": round(self.capital, 4),
            "label":  label,
        })
        # Update peak
        if self.capital > self.peak_equity:
            self.peak_equity = self.capital

    def _empty_stats(self) -> dict:
        return {
            "capital": round(self.capital, 4),
            "total_net_pnl": 0.0, "total_trades": 0,
            "win_rate": 0.0, "profit_factor": 0.0,
            "avg_win_usdt": 0.0, "avg_loss_usdt": 0.0,
            "max_drawdown_pct": 0.0, "sharpe_ratio": 0.0,
            "total_fees_paid": 0.0, "total_slippage": 0.0,
            "equity_curve": self._equity_curve,
        }

    # ── Alpha / Beta vs Benchmark ───────────────────────────────────────────

    def alpha_beta(self, benchmark_returns: List[float]) -> dict:
        """Compare engine returns vs a buy-and-hold benchmark."""
        if not self.trades or not benchmark_returns:
            return {"alpha": 0.0, "beta": 0.0}

        nets = [t.net_pnl / cfg.INITIAL_CAPITAL for t in self.trades]
        n    = min(len(nets), len(benchmark_returns))
        if n < 2:
            return {"alpha": 0.0, "beta": 0.0}

        import statistics
        e_ret  = nets[:n]
        b_ret  = benchmark_returns[:n]
        cov    = statistics.covariance(e_ret, b_ret)
        var_b  = statistics.variance(b_ret)
        beta   = cov / var_b if var_b else 0.0
        alpha  = statistics.mean(e_ret) - beta * statistics.mean(b_ret)
        return {"alpha": round(alpha * 100, 4), "beta": round(beta, 4)}
