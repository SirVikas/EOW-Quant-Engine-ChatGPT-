"""
Deterministic backtest engine with explicit fill and cost modeling.

This module is designed for genome evaluation where reproducibility matters
more than microstructure-perfect simulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Callable, Dict, List, Optional

from strategies.strategy_modules import Signal


@dataclass(frozen=True)
class FillModelConfig:
    """Execution assumptions used consistently across all backtests."""

    taker_fee: float
    slippage_est: float
    latency_bars: int = 1
    volatility_slippage_mult: float = 0.0


@dataclass
class ClosedTrade:
    symbol: str
    direction: Signal
    entry_price: float
    exit_price: float
    gross_pnl: float
    fees: float
    slippage_cost: float
    net_pnl: float
    bars_held: int


@dataclass
class BacktestReport:
    trades: int
    wins: int
    losses: int
    win_rate: float
    profit_factor: float
    net_pnl: float
    expectancy: float
    sharpe: float


class DeterministicBacktestEngine:
    """
    Stable event-replay simulator:
    - Deterministic symbol ordering.
    - Deterministic candle ordering.
    - Explicit entry/exit execution costs.
    - Deterministic same-candle SL/TP tie break (stop-loss first).
    """

    def __init__(self, fill: FillModelConfig, warmup_bars: int = 50):
        self.fill = fill
        self.warmup_bars = warmup_bars

    def run(
        self,
        candles_by_symbol: Dict[str, List[dict]],
        strategy_factory: Callable[[], object],
    ) -> BacktestReport:
        trades: List[ClosedTrade] = []

        for symbol in sorted(candles_by_symbol.keys()):
            candles = sorted(candles_by_symbol[symbol], key=lambda c: c.get("ts", 0))
            if len(candles) <= self.warmup_bars + self.fill.latency_bars:
                continue

            closes = [float(c["close"]) for c in candles]
            highs = [float(c["high"]) for c in candles]
            lows = [float(c["low"]) for c in candles]
            opens = [float(c.get("open", c["close"])) for c in candles]

            strategy = strategy_factory()
            position: Optional[dict] = None

            for i in range(self.warmup_bars, len(candles)):
                if position is None:
                    signal = strategy.generate_signal(
                        symbol,
                        closes[:i],
                        highs[:i],
                        lows[:i],
                    )
                    if signal and signal.signal in (Signal.LONG, Signal.SHORT):
                        entry_i = i + self.fill.latency_bars
                        if entry_i >= len(candles):
                            break
                        entry_price = self._apply_slippage(
                            side=signal.signal,
                            base_price=opens[entry_i],
                            candle_high=highs[entry_i],
                            candle_low=lows[entry_i],
                        )
                        position = {
                            "symbol": symbol,
                            "side": signal.signal,
                            "entry": entry_price,
                            "sl": float(signal.stop_loss),
                            "tp": float(signal.take_profit),
                            "entry_i": entry_i,
                        }
                    continue

                # If entry happened in future bar, wait until we reach it.
                if i < position["entry_i"]:
                    continue

                bar_high = highs[i]
                bar_low = lows[i]
                exit_price = None

                if position["side"] == Signal.LONG:
                    stop_hit = bar_low <= position["sl"]
                    target_hit = bar_high >= position["tp"]
                    if stop_hit:
                        exit_price = position["sl"]
                    elif target_hit:
                        exit_price = position["tp"]
                else:
                    stop_hit = bar_high >= position["sl"]
                    target_hit = bar_low <= position["tp"]
                    if stop_hit:
                        exit_price = position["sl"]
                    elif target_hit:
                        exit_price = position["tp"]

                if exit_price is None:
                    continue

                executed_exit = self._apply_slippage(
                    side=Signal.SHORT if position["side"] == Signal.LONG else Signal.LONG,
                    base_price=exit_price,
                    candle_high=bar_high,
                    candle_low=bar_low,
                )
                trades.append(
                    self._close_trade(
                        symbol=symbol,
                        side=position["side"],
                        entry=position["entry"],
                        exit_price=executed_exit,
                        bars_held=i - position["entry_i"] + 1,
                    )
                )
                position = None

        return self._summarize(trades)

    def _apply_slippage(self, side: Signal, base_price: float, candle_high: float, candle_low: float) -> float:
        volatility = max(0.0, (candle_high - candle_low) / base_price) if base_price > 0 else 0.0
        slip_rate = self.fill.slippage_est + (volatility * self.fill.volatility_slippage_mult)
        if side == Signal.LONG:
            return base_price * (1 + slip_rate)
        return base_price * (1 - slip_rate)

    def _close_trade(self, symbol: str, side: Signal, entry: float, exit_price: float, bars_held: int) -> ClosedTrade:
        if side == Signal.LONG:
            gross = exit_price - entry
        else:
            gross = entry - exit_price

        fees = (entry + exit_price) * self.fill.taker_fee
        slippage_cost = 0.0
        net = gross - fees

        return ClosedTrade(
            symbol=symbol,
            direction=side,
            entry_price=entry,
            exit_price=exit_price,
            gross_pnl=gross,
            fees=fees,
            slippage_cost=slippage_cost,
            net_pnl=net,
            bars_held=bars_held,
        )

    def _summarize(self, trades: List[ClosedTrade]) -> BacktestReport:
        if not trades:
            return BacktestReport(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

        net_results = [t.net_pnl for t in trades]
        wins = [x for x in net_results if x > 0]
        losses = [x for x in net_results if x < 0]

        total = len(trades)
        win_rate = len(wins) / total * 100
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (999.0 if gross_win > 0 else 0.0)
        net_pnl = sum(net_results)
        expectancy = net_pnl / total

        mean = expectancy
        variance = sum((x - mean) ** 2 for x in net_results) / total
        std = sqrt(variance)
        sharpe = (mean / std * sqrt(total)) if std > 0 else 0.0

        return BacktestReport(
            trades=total,
            wins=len(wins),
            losses=len(losses),
            win_rate=round(win_rate, 2),
            profit_factor=round(profit_factor, 3),
            net_pnl=round(net_pnl, 4),
            expectancy=round(expectancy, 6),
            sharpe=round(sharpe, 4),
        )
