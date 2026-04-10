"""
EOW Quant Engine — Genome Engine  (Step 3)
The "Search Engine for Alpha."
• Generates a population of mutated strategy variants
• Backtests them on the last 24h of harvested candles
• Promotes superior variants to ACTIVE if they beat current metrics
"""
from __future__ import annotations
import asyncio
import copy
import random
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from loguru import logger

from config import cfg
from strategies.strategy_modules import (
    TrendFollowingStrategy, MeanReversionStrategy,
    VolatilityExpansionStrategy,
)
from core.backtest_engine import DeterministicBacktestEngine, FillModelConfig


# ── Genome DNA ────────────────────────────────────────────────────────────────

GENE_BOUNDS: Dict[str, tuple] = {
    # TrendFollowing
    "ema_fast":   (5, 25),
    "ema_slow":   (20, 100),
    "ema_trend":  (50, 200),    # macro trend direction EMA
    "rsi_period": (7, 21),
    "rsi_ob":     (55.0, 80.0), # tighter: only long when RSI in momentum zone
    "rsi_os":     (20.0, 45.0), # tighter: only short when RSI fading
    # Shared
    "atr_period": (7, 21),
    "atr_sl":     (1.0, 3.5),
    "atr_tp":     (1.5, 5.0),
    # MeanReversion
    "bb_period":  (10, 30),
    "bb_std":     (2.0, 3.5),   # wider: only trade extreme deviations
    # Volatility
    "lookback":   (10, 40),
    "vol_filter": (1.0, 2.0),
}


@dataclass
class GenomeResult:
    genome_id:     str
    strategy_type: str
    dna:           dict
    trades:        int
    win_rate:      float
    profit_factor: float
    net_pnl:       float
    sharpe:        float
    promoted:      bool = False
    ts:            int  = field(default_factory=lambda: int(time.time() * 1000))


# ── Genome Engine ─────────────────────────────────────────────────────────────

class GenomeEngine:
    """
    Background loop that mutates strategy DNA, simulates trades on recent
    candle data, and promotes winners to replace the active strategy.
    """

    def __init__(self):
        # Active (live) DNA per strategy type
        self.active_dna: Dict[str, dict] = {
            "TrendFollowing":       TrendFollowingStrategy().to_dna(),
            "MeanReversion":        MeanReversionStrategy().to_dna(),
            "VolatilityExpansion":  VolatilityExpansionStrategy().to_dna(),
        }
        self.active_metrics: Dict[str, GenomeResult] = {}
        self.generation_log: List[GenomeResult]      = []
        self._candle_store:  Dict[str, List[dict]]   = {}   # symbol → candles
        self._running = False
        self._lock    = asyncio.Lock()
        self._backtester = DeterministicBacktestEngine(
            fill=FillModelConfig(
                taker_fee=cfg.TAKER_FEE,
                slippage_est=cfg.SLIPPAGE_EST,
                latency_bars=1,
                volatility_slippage_mult=cfg.ATR_SLIPPAGE_MULT,
            ),
            warmup_bars=50,
        )

    # ── Candle Ingestion ────────────────────────────────────────────────────

    def ingest_candle(self, symbol: str, candle: dict):
        """Called by the data lake whenever a new 1m candle closes."""
        if symbol not in self._candle_store:
            self._candle_store[symbol] = []
        self._candle_store[symbol].append(candle)
        # Keep only last 24h × 60min = 1440 candles per symbol
        self._candle_store[symbol] = self._candle_store[symbol][-1440:]

    # ── Main Loop ───────────────────────────────────────────────────────────

    async def start(self):
        self._running = True
        logger.info("[GENOME] Engine started.")
        while self._running:
            await asyncio.sleep(cfg.GENOME_CYCLE_MINUTES * 60)
            await self._evolution_cycle()

    async def stop(self):
        self._running = False
        logger.info("[GENOME] Engine stopped.")

    # ── Evolution Cycle ─────────────────────────────────────────────────────

    async def _evolution_cycle(self):
        logger.info("[GENOME] 🧬 Starting evolution cycle…")
        async with self._lock:
            symbols = list(self._candle_store.keys())
            if not symbols:
                logger.warning("[GENOME] No candle data yet. Skipping cycle.")
                return

            # Pick a representative sample of symbols to backtest
            sample = random.sample(symbols, min(5, len(symbols)))

            for strategy_type in ["TrendFollowing", "MeanReversion", "VolatilityExpansion"]:
                population = self._generate_population(strategy_type)
                results    = []

                for dna in population:
                    result = await self._backtest(dna, strategy_type, sample)
                    results.append(result)
                    self.generation_log.append(result)

                # Keep log bounded
                self.generation_log = self.generation_log[-500:]

                # Find best in population
                best = max(results, key=lambda r: r.profit_factor * r.win_rate)
                logger.info(
                    f"[GENOME] {strategy_type} best: "
                    f"PF={best.profit_factor:.2f} WR={best.win_rate:.1f}% "
                    f"Net={best.net_pnl:.2f}"
                )

                # Promote if better than active
                await self._maybe_promote(strategy_type, best)

        logger.info("[GENOME] ✅ Evolution cycle complete.")

    # ── Population Generation ───────────────────────────────────────────────

    def _generate_population(self, strategy_type: str) -> List[dict]:
        base_dna = copy.deepcopy(self.active_dna[strategy_type])
        population = [base_dna]   # include current champion

        for _ in range(cfg.GENOME_POPULATION - 1):
            mutant = copy.deepcopy(base_dna)
            mutant = self._mutate(mutant, strategy_type)
            population.append(mutant)

        return population

    def _mutate(self, dna: dict, strategy_type: str) -> dict:
        """Apply random mutations within GENE_BOUNDS."""
        keys_for_type = {
            "TrendFollowing":      ["ema_fast","ema_slow","ema_trend","rsi_period","rsi_ob","rsi_os","atr_period","atr_sl","atr_tp"],
            "MeanReversion":       ["bb_period","bb_std","rsi_period","rsi_ob","rsi_os","atr_period","atr_sl","atr_tp"],
            "VolatilityExpansion": ["lookback","vol_filter","atr_period","atr_sl","atr_tp"],
        }
        keys = keys_for_type.get(strategy_type, list(GENE_BOUNDS.keys()))

        # Mutate 1–3 genes
        for key in random.sample(keys, k=random.randint(1, min(3, len(keys)))):
            lo, hi = GENE_BOUNDS[key]
            current = dna.get(key, (lo + hi) / 2)
            # Gaussian mutation ±10% of range
            delta = random.gauss(0, (hi - lo) * 0.10)
            val   = current + delta
            if isinstance(lo, int):
                val = int(round(max(lo, min(hi, val))))
            else:
                val = round(max(lo, min(hi, val)), 3)
            dna[key] = val

        # Constraints: ema_fast < ema_slow < ema_trend
        if "ema_fast" in dna and "ema_slow" in dna:
            if dna["ema_fast"] >= dna["ema_slow"]:
                dna["ema_fast"] = max(5, dna["ema_slow"] - 5)
        if "ema_slow" in dna and "ema_trend" in dna:
            if dna["ema_slow"] >= dna["ema_trend"]:
                dna["ema_slow"] = max(dna["ema_fast"] + 5 if "ema_fast" in dna else 20,
                                      dna["ema_trend"] - 10)

        return dna

    # ── Backtesting ─────────────────────────────────────────────────────────

    async def _backtest(
        self,
        dna: dict,
        strategy_type: str,
        symbols: List[str],
    ) -> GenomeResult:
        """Deterministic backtest on sampled multi-symbol candle data."""
        await asyncio.sleep(0)

        report = self._backtester.run(
            candles_by_symbol={symbol: self._candle_store.get(symbol, []) for symbol in symbols},
            strategy_factory=lambda: self._build_strategy(strategy_type, dna),
        )

        return GenomeResult(
            genome_id=str(uuid.uuid4())[:8],
            strategy_type=strategy_type,
            dna=copy.deepcopy(dna),
            trades=report.trades,
            win_rate=report.win_rate,
            profit_factor=report.profit_factor,
            net_pnl=report.net_pnl,
            sharpe=report.sharpe,
        )

    def _build_strategy(self, strategy_type: str, dna: dict):
        if strategy_type == "TrendFollowing":
            return TrendFollowingStrategy(dna)
        elif strategy_type == "MeanReversion":
            return MeanReversionStrategy(dna)
        return VolatilityExpansionStrategy(dna)

    # ── Promotion ───────────────────────────────────────────────────────────

    async def _maybe_promote(self, strategy_type: str, candidate: GenomeResult):
        current = self.active_metrics.get(strategy_type)

        qualifies = (
            candidate.win_rate      >= cfg.GENOME_PROMOTE_WIN_RATE * 100 and
            candidate.profit_factor >= cfg.GENOME_PROMOTE_PF and
            candidate.trades        >= 5
        )
        if not qualifies:
            return

        if current is None or (
            candidate.profit_factor > current.profit_factor and
            candidate.win_rate      > current.win_rate
        ):
            candidate.promoted = True
            self.active_dna[strategy_type]     = candidate.dna
            self.active_metrics[strategy_type] = candidate
            logger.success(
                f"[GENOME] 🚀 PROMOTED {strategy_type}: "
                f"PF={candidate.profit_factor:.2f} WR={candidate.win_rate:.1f}%"
            )

    # ── State Export ────────────────────────────────────────────────────────

    def export_state(self) -> dict:
        return {
            "active_dna":      self.active_dna,
            "active_metrics":  {k: asdict(v) for k, v in self.active_metrics.items()},
            "recent_genomes":  [asdict(g) for g in self.generation_log[-50:]],
        }
