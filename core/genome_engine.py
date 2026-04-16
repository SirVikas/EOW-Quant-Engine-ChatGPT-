"""
EOW Quant Engine — Genome Engine  (Phase 3 — Calibration & Promotion Hardening)

Phase 3 additions on top of the original "search engine for alpha":

1. Regime-aware calibration
   Each strategy type is evolved using candles from symbols whose recent market
   regime matches the strategy's domain (TRENDING → TrendFollowing, etc.).
   A lightweight inline ADX/slope classifier buckets the sample symbols so the
   mutation pressure is applied to regime-appropriate data.

2. Out-of-sample (OOS) validation gate
   Candles are split 70 % / 30 % into a training window and a held-out OOS
   window.  A candidate must achieve PF ≥ 1.0 on the unseen OOS slice before it
   can be promoted.  An overfitting-ratio check (train_pf / oos_pf ≤ 2.0)
   further rejects candidates that look great on training data but degrade badly
   on fresh data.

3. Execution-adjusted promotion gates
   GenomeResult now carries avg_r_multiple, total_fees, and cost_drag_pct from
   the deterministic backtest.  Promotion requires avg_r_multiple ≥ 0.50 — only
   strategies that return positive net R (after fees and slippage) advance.

4. Immutable promotion audit trail
   Every promotion decision (PROMOTED or REJECTED) is appended to
   GenomeEngine.promotion_log as a PromotionEvent.  The log is bounded to 500
   entries and exported via export_state().
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
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
from core.backtest_engine import DeterministicBacktestEngine, FillModelConfig, BacktestReport


# ── Gene search space ────────────────────────────────────────────────────────

GENE_BOUNDS: Dict[str, tuple] = {
    # TrendFollowing
    "ema_fast":   (5, 25),
    "ema_slow":   (20, 100),
    "ema_trend":  (50, 200),
    "rsi_period": (7, 21),
    "rsi_ob":     (55.0, 80.0),
    "rsi_os":     (20.0, 45.0),
    # Shared
    "atr_period": (7, 21),
    "atr_sl":     (1.0, 3.5),
    "atr_tp":     (1.5, 5.0),
    # MeanReversion
    "bb_period":  (10, 30),
    "bb_std":     (2.0, 3.5),
    # Volatility
    "lookback":   (10, 40),
    "vol_filter": (1.0, 2.0),
}

# Path for automatic DNA persistence across restarts (Fix A)
_DNA_PERSIST_PATH = os.path.join("data", "exports", "optimized_dna.json")


# Each strategy type targets a specific market regime for calibration.
_STRATEGY_TARGET_REGIME: Dict[str, str] = {
    "TrendFollowing":      "TRENDING",
    "MeanReversion":       "MEAN_REVERTING",
    "VolatilityExpansion": "VOLATILE",
}


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class GenomeResult:
    genome_id:      str
    strategy_type:  str
    dna:            dict
    trades:         int
    win_rate:       float
    profit_factor:  float
    net_pnl:        float
    sharpe:         float
    # Execution-cost metrics (Phase 3)
    avg_r_multiple: float = 0.0
    total_fees:     float = 0.0
    cost_drag_pct:  float = 0.0
    # OOS validation (Phase 3)
    oos_pf:         float = 0.0
    oos_win_rate:   float = 0.0
    oos_trades:     int   = 0
    oos_valid:      bool  = False
    # Regime context used during calibration (Phase 3)
    regime:         str   = "ALL"
    promoted:       bool  = False
    ts:             int   = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class PromotionEvent:
    """Immutable record of every promotion decision for the audit trail."""
    ts:             int
    strategy_type:  str
    decision:       str    # "PROMOTED" | "REJECTED"
    reason:         str
    genome_id:      str
    train_pf:       float
    oos_pf:         float
    avg_r_multiple: float
    cost_drag_pct:  float
    dna:            dict


# ── Genome Engine ─────────────────────────────────────────────────────────────

class GenomeEngine:
    """
    Background loop that mutates strategy DNA, simulates trades on recent
    candle data, and promotes winners to replace the active strategy.

    Phase 3 enhancements:
      • Regime-aware symbol bucketing per evolution cycle.
      • Train / OOS split with PF gate on unseen data.
      • Execution-cost R-multiple gate.
      • Overfitting ratio guard.
      • Full promotion audit log.
    """

    def __init__(self):
        # ── Active (live) DNA per strategy type ──────────────────────────────
        self.active_dna: Dict[str, dict] = {
            "TrendFollowing":      TrendFollowingStrategy().to_dna(),
            "MeanReversion":       MeanReversionStrategy().to_dna(),
            "VolatilityExpansion": VolatilityExpansionStrategy().to_dna(),
        }
        # Per-regime best DNA: regime → {strategy_type → dna}
        # Populated as regime-bucketed cycles run; ready for Phase 4 routing.
        self.per_regime_dna: Dict[str, Dict[str, dict]] = {}

        self.active_metrics: Dict[str, GenomeResult]  = {}
        self.generation_log: List[GenomeResult]        = []
        self.promotion_log:  List[PromotionEvent]      = []  # audit trail
        self._candle_store:  Dict[str, List[dict]]     = {}  # symbol → candles
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

    # ── Candle Ingestion ──────────────────────────────────────────────────────

    def ingest_candle(self, symbol: str, candle: dict):
        """Called by the data lake whenever a new 1-minute candle closes."""
        if symbol not in self._candle_store:
            self._candle_store[symbol] = []
        self._candle_store[symbol].append(candle)
        # Keep last 24 h × 60 min = 1 440 candles per symbol.
        self._candle_store[symbol] = self._candle_store[symbol][-1440:]

    # ── Main Loop ─────────────────────────────────────────────────────────────

    async def start(self):
        self._running = True
        logger.info("[GENOME] Engine started.")
        while self._running:
            await asyncio.sleep(cfg.GENOME_CYCLE_MINUTES * 60)
            await self._evolution_cycle()

    async def stop(self):
        self._running = False
        logger.info("[GENOME] Engine stopped.")

    # ── Evolution Cycle ───────────────────────────────────────────────────────

    async def _evolution_cycle(self):
        logger.info("[GENOME] Starting evolution cycle…")
        async with self._lock:
            symbols = list(self._candle_store.keys())
            if not symbols:
                logger.warning("[GENOME] No candle data yet — skipping cycle.")
                return

            # Sample up to 5 symbols and bucket them by recent market regime.
            sample = random.sample(symbols, min(5, len(symbols)))
            regime_buckets = self._classify_symbol_regimes(sample)

            for strategy_type in ["TrendFollowing", "MeanReversion", "VolatilityExpansion"]:
                target_regime = _STRATEGY_TARGET_REGIME[strategy_type]

                # Use regime-matched symbols when available; fall back to full sample.
                regime_symbols = regime_buckets.get(target_regime) or sample

                population = self._generate_population(strategy_type)
                results: List[GenomeResult] = []

                for dna in population:
                    result = await self._backtest_with_oos(dna, strategy_type, regime_symbols)
                    result.regime = target_regime
                    results.append(result)
                    self.generation_log.append(result)

                self.generation_log = self.generation_log[-500:]

                # Select the best candidate by training-window fitness.
                best = max(results, key=lambda r: r.profit_factor * r.win_rate)
                logger.info(
                    f"[GENOME] {strategy_type} ({target_regime}) best: "
                    f"Train PF={best.profit_factor:.2f}  "
                    f"OOS PF={best.oos_pf:.2f}  "
                    f"avg_R={best.avg_r_multiple:.2f}  "
                    f"cost_drag={best.cost_drag_pct:.1f}%"
                )

                await self._maybe_promote(strategy_type, best)

        logger.info("[GENOME] Evolution cycle complete.")

    # ── Regime Classification ─────────────────────────────────────────────────

    def _classify_symbol_regimes(self, symbols: List[str]) -> Dict[str, List[str]]:
        """
        Lightweight inline regime classifier using recent candle data.
        Returns a dict mapping regime label → list of symbols.
        No external dependencies; intentionally simple for intra-engine use.
        """
        result: Dict[str, List[str]] = {
            "TRENDING": [], "MEAN_REVERTING": [], "VOLATILE": [],
        }
        for symbol in symbols:
            candles = self._candle_store.get(symbol, [])
            if len(candles) < 20:
                result["TRENDING"].append(symbol)
                continue

            recent = candles[-50:]
            closes = [float(c["close"]) for c in recent]
            highs  = [float(c["high"])  for c in recent]
            lows   = [float(c["low"])   for c in recent]

            # ATR proxy (14-bar average true range as % of close)
            trs = [
                max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i]  - closes[i - 1]),
                )
                for i in range(1, len(closes))
            ]
            atr14    = sum(trs[-14:]) / 14 if len(trs) >= 14 else (sum(trs) / len(trs) if trs else 0.0)
            mid      = closes[-1] if closes[-1] > 0 else 1.0
            atr_pct  = atr14 / mid * 100

            # Price slope proxy: % move over last 20 bars
            slope_pct = abs((closes[-1] - closes[-20]) / closes[-20] * 100) if len(closes) >= 20 else 0.0

            if atr_pct > 2.5:
                result["VOLATILE"].append(symbol)
            elif slope_pct > 3.0:
                result["TRENDING"].append(symbol)
            else:
                result["MEAN_REVERTING"].append(symbol)

        return result

    # ── Population Generation ─────────────────────────────────────────────────

    def _generate_population(self, strategy_type: str) -> List[dict]:
        base_dna   = copy.deepcopy(self.active_dna[strategy_type])
        population = [base_dna]  # champion always included

        for _ in range(cfg.GENOME_POPULATION - 1):
            mutant = copy.deepcopy(base_dna)
            mutant = self._mutate(mutant, strategy_type)
            population.append(mutant)

        return population

    def _mutate(self, dna: dict, strategy_type: str) -> dict:
        """Apply random Gaussian mutations within GENE_BOUNDS."""
        keys_for_type = {
            "TrendFollowing":      ["ema_fast", "ema_slow", "ema_trend", "rsi_period", "rsi_ob", "rsi_os", "atr_period", "atr_sl", "atr_tp"],
            "MeanReversion":       ["bb_period", "bb_std", "rsi_period", "rsi_ob", "rsi_os", "atr_period", "atr_sl", "atr_tp"],
            "VolatilityExpansion": ["lookback", "vol_filter", "atr_period", "atr_sl", "atr_tp"],
        }
        keys = keys_for_type.get(strategy_type, list(GENE_BOUNDS.keys()))

        for key in random.sample(keys, k=random.randint(1, min(3, len(keys)))):
            lo, hi  = GENE_BOUNDS[key]
            current = dna.get(key, (lo + hi) / 2)
            delta   = random.gauss(0, (hi - lo) * 0.10)
            val     = current + delta
            if isinstance(lo, int):
                val = int(round(max(lo, min(hi, val))))
            else:
                val = round(max(lo, min(hi, val)), 3)
            dna[key] = val

        # Structural constraint: ema_fast < ema_slow < ema_trend
        if "ema_fast" in dna and "ema_slow" in dna:
            if dna["ema_fast"] >= dna["ema_slow"]:
                dna["ema_fast"] = max(5, dna["ema_slow"] - 5)
        if "ema_slow" in dna and "ema_trend" in dna:
            if dna["ema_slow"] >= dna["ema_trend"]:
                dna["ema_slow"] = max(
                    dna["ema_fast"] + 5 if "ema_fast" in dna else 20,
                    dna["ema_trend"] - 10,
                )
        return dna

    # ── Backtesting with OOS split ────────────────────────────────────────────

    async def _backtest_with_oos(
        self,
        dna: dict,
        strategy_type: str,
        symbols: List[str],
    ) -> GenomeResult:
        """
        Run a deterministic backtest split into training and OOS windows.

        Candles are split at GENOME_OOS_SPLIT_RATIO (default 70/30).
        When total candle history is shorter than 3× warmup_bars (early session),
        the OOS gate is skipped (pass-through) to avoid blocking the engine at
        start-up before sufficient data has accumulated.
        """
        await asyncio.sleep(0)

        split      = cfg.GENOME_OOS_SPLIT_RATIO
        wb         = self._backtester.warmup_bars
        min_candles_for_oos = wb * 3  # need at least 150 candles to attempt a meaningful split

        train_candles: Dict[str, List[dict]] = {}
        test_candles:  Dict[str, List[dict]] = {}
        sufficient_data = False

        for symbol in symbols:
            all_c = self._candle_store.get(symbol, [])
            if not all_c:
                continue
            cut = max(int(len(all_c) * split), wb + 5)
            train_candles[symbol] = all_c[:cut]
            test_candles[symbol]  = all_c[cut:]
            if len(all_c) >= min_candles_for_oos:
                sufficient_data = True

        factory = lambda: self._build_strategy(strategy_type, dna)

        train_report: BacktestReport = self._backtester.run(train_candles, factory)

        # OOS evaluation — only when we have enough history.
        if sufficient_data and test_candles:
            oos_report: BacktestReport = self._backtester.run(test_candles, factory)
            oos_pf       = oos_report.profit_factor
            oos_win_rate = oos_report.win_rate
            oos_trades   = oos_report.trades
            oos_valid    = (
                oos_pf >= cfg.GENOME_OOS_MIN_PF
                and oos_trades >= 2
            )
        else:
            # Insufficient history — OOS gate is skipped (treated as passing).
            oos_pf = oos_win_rate = 0.0
            oos_trades = 0
            oos_valid  = True  # pass-through; early-session safety valve

        return GenomeResult(
            genome_id=str(uuid.uuid4())[:8],
            strategy_type=strategy_type,
            dna=copy.deepcopy(dna),
            trades=train_report.trades,
            win_rate=train_report.win_rate,
            profit_factor=train_report.profit_factor,
            net_pnl=train_report.net_pnl,
            sharpe=train_report.sharpe,
            avg_r_multiple=train_report.avg_r_multiple,
            total_fees=train_report.total_fees,
            cost_drag_pct=train_report.cost_drag_pct,
            oos_pf=oos_pf,
            oos_win_rate=oos_win_rate,
            oos_trades=oos_trades,
            oos_valid=oos_valid,
        )

    def _build_strategy(self, strategy_type: str, dna: dict):
        if strategy_type == "TrendFollowing":
            return TrendFollowingStrategy(dna)
        if strategy_type == "MeanReversion":
            return MeanReversionStrategy(dna)
        return VolatilityExpansionStrategy(dna)

    # ── Promotion (hardened — Phase 3) ───────────────────────────────────────

    async def _maybe_promote(self, strategy_type: str, candidate: GenomeResult):
        """
        Multi-gate promotion filter.  All four gates must pass:

        Gate 1 — Training thresholds (win-rate, profit-factor, trade count).
        Gate 2 — Out-of-sample PF ≥ 1.0 on unseen data (overfitting guard).
        Gate 3 — Execution-adjusted avg R-multiple ≥ GENOME_MIN_AVG_R.
        Gate 4 — Overfitting ratio: train_pf / oos_pf ≤ GENOME_OVERFITTING_MAX_RATIO.

        Every decision is appended to promotion_log for the audit trail.
        """
        # Gate 1: Training-window thresholds
        passes_train = (
            candidate.win_rate      >= cfg.GENOME_PROMOTE_WIN_RATE * 100
            and candidate.profit_factor >= cfg.GENOME_PROMOTE_PF
            and candidate.trades        >= 5
        )

        # Gate 2: OOS profit factor
        passes_oos = candidate.oos_valid

        # Gate 3: Post-cost average R-multiple
        passes_r = candidate.avg_r_multiple >= cfg.GENOME_MIN_AVG_R

        # Gate 4: Overfitting ratio
        if candidate.oos_pf > 0.0:
            overfit_ratio = candidate.profit_factor / candidate.oos_pf
        else:
            overfit_ratio = 999.0
        passes_overfit = overfit_ratio <= cfg.GENOME_OVERFITTING_MAX_RATIO

        all_pass = passes_train and passes_oos and passes_r and passes_overfit

        if not all_pass:
            reasons = []
            if not passes_train:
                reasons.append(
                    f"train_gate(PF={candidate.profit_factor:.2f} "
                    f"WR={candidate.win_rate:.1f}% "
                    f"T={candidate.trades})"
                )
            if not passes_oos:
                reasons.append(
                    f"oos_gate(OOS_PF={candidate.oos_pf:.2f} "
                    f"T={candidate.oos_trades})"
                )
            if not passes_r:
                reasons.append(f"r_gate(avg_R={candidate.avg_r_multiple:.2f})")
            if not passes_overfit:
                reasons.append(f"overfit(ratio={overfit_ratio:.1f})")

            self._record_promotion(candidate, "REJECTED", ", ".join(reasons))
            return

        # Promote only if strictly better than the current champion.
        current = self.active_metrics.get(strategy_type)
        if current is None or (
            candidate.profit_factor > current.profit_factor
            and candidate.win_rate > current.win_rate
        ):
            candidate.promoted = True
            self.active_dna[strategy_type]     = candidate.dna
            self.active_metrics[strategy_type] = candidate

            # Persist per-regime DNA for future Phase 4 routing.
            regime = candidate.regime
            if regime not in self.per_regime_dna:
                self.per_regime_dna[regime] = {}
            self.per_regime_dna[regime][strategy_type] = copy.deepcopy(candidate.dna)

            self._record_promotion(
                candidate, "PROMOTED",
                f"Train PF={candidate.profit_factor:.2f}  "
                f"OOS PF={candidate.oos_pf:.2f}  "
                f"avg_R={candidate.avg_r_multiple:.2f}  "
                f"cost_drag={candidate.cost_drag_pct:.1f}%",
            )
            logger.success(
                f"[GENOME] PROMOTED {strategy_type} ({candidate.regime}): "
                f"Train PF={candidate.profit_factor:.2f}  "
                f"OOS PF={candidate.oos_pf:.2f}  "
                f"avg_R={candidate.avg_r_multiple:.2f}"
            )

    def _record_promotion(
        self, candidate: GenomeResult, decision: str, reason: str,
    ):
        self.promotion_log.append(
            PromotionEvent(
                ts=int(time.time() * 1000),
                strategy_type=candidate.strategy_type,
                decision=decision,
                reason=reason,
                genome_id=candidate.genome_id,
                train_pf=candidate.profit_factor,
                oos_pf=candidate.oos_pf,
                avg_r_multiple=candidate.avg_r_multiple,
                cost_drag_pct=candidate.cost_drag_pct,
                dna=copy.deepcopy(candidate.dna),
            )
        )
        self.promotion_log = self.promotion_log[-500:]
        # Auto-save winning DNA to disk immediately (Fix A — survives Redis loss)
        if decision == "PROMOTED":
            self._persist_dna()

    # ── DNA Persistence (Fix A) ───────────────────────────────────────────────

    def _persist_dna(self):
        """
        Write active_dna + per_regime_dna to disk immediately after every
        successful promotion.  This survives engine restarts and Redis loss.
        """
        try:
            os.makedirs(os.path.dirname(_DNA_PERSIST_PATH), exist_ok=True)
            payload = {
                "saved_at":      int(time.time() * 1000),
                "active_dna":    self.active_dna,
                "per_regime_dna": self.per_regime_dna,
            }
            with open(_DNA_PERSIST_PATH, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            logger.info(f"[GENOME] DNA persisted → {_DNA_PERSIST_PATH}")
        except Exception as exc:
            logger.warning(f"[GENOME] DNA persist failed: {exc}")

    def load_persisted_dna(self):
        """
        Called once at startup.  Loads previously promoted DNA from disk so the
        engine continues with tuned parameters instead of factory defaults.
        """
        if not os.path.exists(_DNA_PERSIST_PATH):
            logger.info("[GENOME] No persisted DNA found — using strategy defaults.")
            return
        try:
            with open(_DNA_PERSIST_PATH, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            loaded = payload.get("active_dna", {})
            for st, dna in loaded.items():
                if st in self.active_dna and isinstance(dna, dict):
                    self.active_dna[st] = dna
            self.per_regime_dna = payload.get("per_regime_dna", {})
            saved_at_ms = self._normalize_saved_at_ms(payload.get("saved_at", 0))
            age_s = max(0.0, (int(time.time() * 1000) - saved_at_ms) / 1000)
            logger.success(
                f"[GENOME] DNA restored from disk "
                f"(saved {age_s / 60:.1f} min ago). "
                f"Strategies: {list(loaded.keys())}"
            )
        except Exception as exc:
            logger.warning(f"[GENOME] DNA load failed: {exc} — using defaults.")

    @staticmethod
    def _normalize_saved_at_ms(saved_at_raw) -> int:
        """
        Normalize persisted timestamp to epoch milliseconds.
        Supports legacy storage in seconds, milliseconds, microseconds,
        and minutes-since-epoch (from older bugged exports).
        """
        now_ms = int(time.time() * 1000)
        try:
            raw = float(saved_at_raw)
        except (TypeError, ValueError):
            return now_ms
        if raw <= 0:
            return now_ms

        # Heuristic by order of magnitude.
        if raw > 1e14:  # microseconds
            candidate_ms = int(raw / 1000)
        elif raw > 1e11:  # milliseconds
            candidate_ms = int(raw)
        elif raw > 1e9:  # seconds
            candidate_ms = int(raw * 1000)
        else:  # legacy bug: minutes
            candidate_ms = int(raw * 60_000)

        # Guard against corrupted future values.
        if candidate_ms > now_ms + 60_000:
            return now_ms
        return candidate_ms

    # ── State Export ──────────────────────────────────────────────────────────

    def export_state(self) -> dict:
        return {
            "active_dna":      self.active_dna,
            "per_regime_dna":  self.per_regime_dna,
            "active_metrics":  {k: asdict(v) for k, v in self.active_metrics.items()},
            "recent_genomes":  [asdict(g) for g in self.generation_log[-50:]],
            "promotion_log":   [asdict(p) for p in self.promotion_log[-50:]],
            # Number of evaluated genomes — used by deployability_index() to determine
            # whether the genome has run at least one evolution cycle (+10 pts RR Edge).
            "generation":      len(self.generation_log),
            # Per-symbol candle counts in the in-memory store (diagnostics).
            "candle_counts":   {sym: len(c) for sym, c in self._candle_store.items()},
        }
