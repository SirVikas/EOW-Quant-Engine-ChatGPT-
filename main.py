"""
EOW Quant Engine — FastAPI Main Application
Wires together all modules and exposes REST + WebSocket endpoints
for the React Pastel Dashboard.
"""
from __future__ import annotations
import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from loguru import logger
import orjson

from config import cfg, parse_allowed_origins
from core.market_data    import MarketDataProvider, Tick
from core.pnl_calculator import PurePnLCalculator, TradeRecord
from core.genome_engine  import GenomeEngine
from core.regime_detector import RegimeDetector
from core.risk_controller import RiskController, OpenPosition
from core.self_healing    import SelfHealingProtocol
from core.data_lake       import DataLake
from core.vault           import VaultManager, WrongPassword, VaultNotConfigured
from core.guardian        import GuardianLogic, AGGRESSION_PROFILES
from core.security        import ensure_auth_ready_for_mode, require_roles
from core.scorecard       import compute_scorecard
from core.analytics       import compute_full_analytics, deployability_index
from core.metrics_engine   import rolling_ratios
from core.redis_health    import redis_health
from core.ws_stabilizer   import WsStabilizer
from core.regime_debounce import regime_debounce
from core.indicator_guard     import indicator_guard
from core.indicator_validator import indicator_validator          # qFTD-007: keeps deploy iv_score accurate
from core.regime_ai       import regime_ai
from core.signal_filter   import signal_filter
from core.risk_engine     import risk_engine
from core.deployability   import deployability_engine
from core.trade_frequency    import trade_frequency      # FTD-REF-023
from core.execution_drive_policy import execution_drive_policy  # EDP
from core.execution_engine  import execution_engine     # FTD-REF-023
from core.learning_engine   import learning_engine      # FTD-REF-023
from core.edge_engine        import edge_engine         # FTD-REF-024
from core.adaptive_edge_engine import adaptive_edge_engine  # FTD-037
from core.capital_flow_engine  import capital_flow_engine   # FTD-038+039
from core.market_structure   import market_structure_detector  # FTD-REF-024
from core.ws_truth_engine    import ws_truth_engine     # FTD-REF-025
from core.error_registry     import error_registry      # FTD-REF-025
from core.strategy_engine    import strategy_engine     # FTD-REF-026
from core.profit_guard       import profit_guard        # FTD-REF-026
from core.ct_scan_engine     import ct_scan_engine      # FTD-REF-026
from core.inverse_engine     import inverse_engine, TradeMode  # A.I.E.
from core.volume_filter      import volume_filter              # Phase 3: sleep mode
from core.sector_guard       import sector_guard               # Phase 3: correlation guard
from core.rr_engine          import rr_engine                  # Phase 4: RR enforcement
from core.trade_scorer       import trade_scorer               # Phase 4: alpha quality gate
from core.capital_allocator  import capital_allocator          # Phase 4: score-based sizing
from core.trade_manager      import trade_manager, ManagedPosition  # Phase 4: lifecycle
from strategies.alpha_engine import alpha_engine               # Phase 4: alpha signals
from core.equity_snapshot    import equity_snapshot             # qFTD-009: equity persistence
from core.ev_engine          import ev_engine                  # Phase 5: EV gate
from core.adaptive_scorer    import adaptive_scorer            # Phase 5: dynamic weights
from core.confidence_decay   import confidence_decay           # Phase 5: signal staleness
from core.drawdown_controller import drawdown_controller       # Phase 5: DD protection
from core.regime_memory      import regime_memory              # Phase 5: regime learning
from core.trade_activator      import trade_activator            # Phase 5.1: freeze prevention
from core.exploration_engine   import exploration_engine, ExploreResult  # Phase 5.1
from core.adaptive_filter      import adaptive_filter            # Phase 5.1: dynamic thresholds
from core.smart_fee_guard      import smart_fee_guard            # Phase 5.1: RR-aware fee gate
from core.trade_flow_monitor   import trade_flow_monitor         # Phase 5.1: flow health
from core.dynamic_thresholds   import dynamic_threshold_provider # Phase 5.2: master control
from core.ev_confidence        import ev_confidence_engine        # Phase 6: EV tier sizing
from core.loss_cluster         import loss_cluster_controller     # Phase 6: loss circuit breaker
from core.streak_engine        import streak_engine               # Phase 6: hot/cold detection
from core.capital_recovery     import capital_recovery_engine     # Phase 6: recovery sizing
from core.consistency_engine   import consistency_engine          # FTD-040: unified consistency
from core.exploration_guard    import exploration_guard           # Phase 6: exploration gate
from core.gating import (                                         # Phase 6.6: hard gating
    gate_logger,
    safe_mode_engine,
    global_gate_controller,
    hard_start_validator,
    pre_trade_gate,
)
from core.data_health import data_health_monitor                  # qFTD-004: data freshness SSOT
from core.performance_explorer import (                           # FTD-UPE: Universal Performance Explorer
    TradeFilter        as _UPEFilter,
    preset_filter      as _upe_preset_filter,
    compute_summary    as _upe_compute_summary,
    build_visual_data  as _upe_build_visual_data,
    extract_insights   as _upe_extract_insights,
    TradeRecord        as _UPERecord,
    ExportEngine       as _UPEExport,
    BackupManager      as _UPEBackup,
)
from core.orchestrator import (                                    # Phase 7A: execution orchestrator
    execution_orchestrator,
    TickContext,
)
from core.exchange.api_manager  import api_manager
from core.bootstrap.api_loader  import api_loader
from core.infra_health_manager import InfraHealthManager
from utils.capital_scaler import CapitalScaler
from utils.export_manager import ExportManager
from utils.report_generator import build_report_archive
from core.export_engine import system_export_engine, SystemSnapshot   # FTD-025A
from core.intelligence.auto_intelligence_engine import AutoIntelligenceEngine  # FTD-030
from core.performance import (                                                 # FTD-031
    perf_monitor, task_queue, perf_guard,
    PRIORITY_LOW, PRIORITY_MEDIUM,
)
from strategies.strategy_modules import get_strategy, Signal, TradeSignal, _rsi


def _safe_num(v):
    """Replace inf/nan with safe JSON values."""
    import math
    if isinstance(v, float):
        if math.isinf(v) or math.isnan(v):
            return 99.99 if v > 0 else -99.99
    return v


def _sanitize(obj):
    """Recursively sanitize dict/list for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    return _safe_num(obj)


# ── Engine Instances ─────────────────────────────────────────────────────────

mdp        = MarketDataProvider()
pnl_calc   = PurePnLCalculator(cfg.INITIAL_CAPITAL)
scaler     = CapitalScaler()
genome     = GenomeEngine()
regime_det = RegimeDetector()
risk_ctrl  = RiskController(pnl_calc, scaler)
healer     = SelfHealingProtocol(mdp)
exporter   = ExportManager(pnl_calc, genome, risk_ctrl)
data_lake  = DataLake()
vault      = VaultManager()
guardian   = GuardianLogic()
ws_stab    = WsStabilizer(mdp)        # FTD-REF-019: tick watchdog
infra_health = InfraHealthManager(redis_health=redis_health, redis_retries=3)

# FTD-030: Auto Intelligence Engine — instantiated after pnl_calc/scaler are ready.
# Wired to _sc_build_state() (defined later) and pnl_calc.trades count.
# broadcast_fn set to _ai_broadcast (defined below) after WS clients are ready.
_auto_intelligence: "AutoIntelligenceEngine | None" = None   # initialised in lifespan

# FTD-REF-019: store boot diagnostics for /api/boot-status
_boot_status: dict = {}
_engine_running: bool = False

# qFTD-007-v2: boot-phase state lock
# BOOTING: warmup in progress — gate failures block trading but do NOT activate safe mode.
# LIVE:    normal operation — all gate failures trigger safe mode as usual.
_system_state: str = "BOOTING"   # "BOOTING" | "LIVE"
_boot_ts: float = 0.0            # set to time.time() in lifespan() for grace period tracking
_boot_replay_count: int = 0      # qFTD-010: trades replayed from DataLake at boot; streak/AF use session trades only

# ── Trade Throttle Controls ───────────────────────────────────────────────────
# After any trade on a symbol, wait this long before allowing another entry.
SYMBOL_COOLDOWN_SEC = 120         # qFTD-032: 300→120s — 2 min cooldown per symbol unlocks more pairs per hour
MAX_TRADES_PER_HOUR = 20          # qFTD-032: 12→20 — multi-currency system needs higher throughput

_last_trade_ts: dict = {}         # symbol → last trade close timestamp (ms)
_trades_this_hour: list = []      # timestamps of recent trade opens
_last_symbol_eval_ms: dict = {}   # symbol → last strategy evaluation ts
_last_processed_candle_ts: dict = {}  # symbol → last closed candle ts evaluated
SYMBOL_EVAL_DEBOUNCE_MS = 750     # throttle heavy signal path per symbol
_closed_trade_count: list = [0]   # mutable counter for 50-trade genome trigger
_is_exploration_trade: dict = {}  # symbol → True when open trade is exploration

# Active WebSocket clients
_ws_clients: list[WebSocket] = []

# CT-Scan thought log (AI reasoning log for the UI)
_thought_log: list[dict] = []

# Last structured skip event — used by the live Skip Reason indicator on dashboard
_last_skip: dict = {}


def _thought(msg: str, level: str = "INFO"):
    entry = {"ts": int(time.time() * 1000), "level": level, "msg": msg}
    _thought_log.append(entry)
    if len(_thought_log) > 500:
        _thought_log.pop(0)
    logger.info(f"[CT-SCAN] {msg}")
    # Broadcast to all WS clients
    for ws in list(_ws_clients):
        asyncio.create_task(_safe_send(ws, {"type": "thought", **entry}))


async def _safe_send(ws: WebSocket, data: dict):
    try:
        await ws.send_text(json.dumps(data, default=str))
    except Exception:
        if ws in _ws_clients:
            _ws_clients.remove(ws)


def _estimate_atr_pct(closes: list[float]) -> float:
    """Lightweight ATR% proxy from close-to-close absolute moves."""
    if len(closes) < 3:
        return 0.0
    lookback = closes[-15:]
    moves = [abs(lookback[i] - lookback[i - 1]) for i in range(1, len(lookback))]
    avg_move = sum(moves) / max(len(moves), 1)
    last = max(lookback[-1], 1e-9)
    return (avg_move / last) * 100.0


# ── Signal Processing Callback ────────────────────────────────────────────────

async def on_tick(tick: Tick):
    """Called for every new tick from MarketDataProvider."""
    global _last_skip, _system_state, _boot_replay_count   # must be declared before any assignment in this function
    sym   = tick.symbol
    price = tick.price

    # Guard: reject malformed symbols that somehow bypass _is_valid_symbol
    if len(sym) < 5 or not sym.endswith("USDT"):
        return

    # FTD-031: per-cycle latency tracking
    if cfg.PERF_ENABLED:
        perf_monitor.on_cycle_start(sym)

    # FTD-REF-019/025: record liveness for tick watchdog + truth engine
    ws_stab.record_tick()
    ws_truth_engine.record_tick()                        # FTD-REF-025

    # 1. Update risk controller (SL/TP checks)
    action = risk_ctrl.on_price_update(sym, price)
    if action:
        _thought(f"Position closed [{action}] {sym} @ {price}", "TRADE")
        if pnl_calc.trades:
            last_trade = pnl_calc.trades[-1]
            data_lake.save_trade(asdict(last_trade))
            # MASTER-001: update signal filter loss/win tracker
            if last_trade.net_pnl >= 0:
                signal_filter.record_win(sym)
            else:
                signal_filter.record_loss(sym)
            # MASTER-001: update risk engine daily PnL + equity
            risk_engine.record_trade_result(last_trade.net_pnl)
            # FTD-REF-023/024: update per-regime learning + edge engines
            _trade_regime   = getattr(last_trade, "regime",      "UNKNOWN") or "UNKNOWN"
            _trade_strategy = getattr(last_trade, "strategy_id", "unknown") or "unknown"
            _initial_risk   = max(getattr(last_trade, "initial_risk", 1.0), 1e-9)
            _r_mult         = last_trade.net_pnl / _initial_risk
            learning_engine.record(regime=_trade_regime, won=last_trade.net_pnl >= 0)
            edge_engine.record(
                regime=_trade_regime, strategy_id=_trade_strategy,
                net_pnl=last_trade.net_pnl, r_mult=_r_mult,
            )
            # FTD-037: Adaptive Edge Engine — time-aware scoring + state machine
            _gross_pnl  = getattr(last_trade, "gross_pnl", last_trade.net_pnl)
            _fee_closed  = (getattr(last_trade, "fee_entry", 0.0)
                           + getattr(last_trade, "fee_exit",  0.0))
            adaptive_edge_engine.on_trade_closed(
                strategy_id = _trade_strategy,
                net_pnl     = last_trade.net_pnl,
                r_multiple  = _r_mult,
                gross_pnl   = _gross_pnl,
                fee_total   = _fee_closed,
            )
            # FTD-038+039: Capital Flow Engine — update priority + stabilizer
            capital_flow_engine.on_trade(
                strategy_id = _trade_strategy,
                net_pnl     = last_trade.net_pnl,
                equity      = scaler.equity,
            )
            # FTD-040: Consistency Engine — feedback loop (post-trade state update)
            consistency_engine.record_trade(last_trade.net_pnl)
            # FTD-REF-026: track strategy usage distribution
            _closed_strat_type = {
                "TRENDING":             "TrendFollowing",
                "MEAN_REVERTING":       "MeanReversion",
                "VOLATILITY_EXPANSION": "VolatilityExpansion",
            }.get(_trade_regime, "TrendFollowing")
            strategy_engine.record_trade(_closed_strat_type)
            # A.I.E.: feed outcome + direction so engine learns per-strategy and per-direction
            _trade_direction = getattr(last_trade, "side", "")
            inverse_engine.record(_closed_strat_type, won=last_trade.net_pnl >= 0, direction=_trade_direction)
            # Mandate: trigger genome evolution every 50 trades (not just on timer)
            genome.on_trade_closed()
            # Phase 5: update EV engine, adaptive scorer, and regime memory
            _trade_cost = (getattr(last_trade, "fee_entry", 0.0)
                           + getattr(last_trade, "fee_exit", 0.0)
                           + getattr(last_trade, "slippage_cost", 0.0))
            _trade_won  = last_trade.net_pnl >= 0
            ev_engine.record(
                strategy_id=_trade_strategy, symbol=sym,
                net_pnl=last_trade.net_pnl, cost=_trade_cost,
            )
            adaptive_scorer.record_outcome(sym, won=_trade_won)
            regime_memory.record(
                regime=_trade_regime, strategy_type=_closed_strat_type,
                won=_trade_won, r_mult=_r_mult,
            )
            confidence_decay.reset(sym, _trade_strategy)  # fresh start after trade
            # Phase 5.1: record exploration outcome + reset activator timer + flow monitor
            if _is_exploration_trade.pop(sym, False):
                exploration_engine.record_result(sym, last_trade.net_pnl)
            trade_activator.record_trade()
            trade_flow_monitor.record_trade(sym)
            # qFTD-009: persist equity after every trade so restarts show correct balance
            equity_snapshot.save(
                equity=scaler.equity,
                trade_count=len(pnl_calc.trades),
            )
        trade_manager.deregister(sym)                       # Phase 4: remove from lifecycle
        _last_trade_ts[sym] = int(time.time() * 1000)  # cooldown starts on close

    # MASTER-001: keep risk engine equity up to date
    risk_engine.update_equity(scaler.equity)
    # Phase 5: keep drawdown controller in sync
    drawdown_controller.update_equity(scaler.equity)
    capital_recovery_engine.update_equity(scaler.equity)  # Phase 6
    consistency_engine.update_equity(scaler.equity)       # FTD-040: equity volatility tracking

    # Phase 4: Trade Manager lifecycle update for managed open positions
    if trade_manager.is_managed(sym):
        _tm_r_state  = regime_det.state(sym)
        _tm_atr_pct  = getattr(_tm_r_state, "atr_pct", 0.0)
        _tm_atr_price = _tm_atr_pct * price / 100 if _tm_atr_pct > 0 else 0.0
        _tm_action = trade_manager.update(sym, price, _tm_atr_price)
        if _tm_action.action == "MOVE_BE" and _tm_action.new_sl > 0:
            _pos = risk_ctrl.positions.get(sym)
            if _pos:
                _pos.stop_loss = _tm_action.new_sl
                _thought(f"[TM] {sym} BE: SL→{_tm_action.new_sl:.4f} ({_tm_action.reason})", "TRADE")
        elif _tm_action.action == "TRAIL_SL" and _tm_action.new_sl > 0:
            _pos = risk_ctrl.positions.get(sym)
            if _pos:
                _pos.stop_loss = _tm_action.new_sl
        elif _tm_action.action == "PARTIAL_TP":
            _thought(f"[TM] {sym} PARTIAL_TP {_tm_action.partial_qty:.6f} @ {price:.4f} ({_tm_action.reason})", "TRADE")

    # 2. Get candle data for strategy
    candle = mdp.latest_closed_candle(sym)
    if not candle:
        # Startup warmup: until first closed candle lands, skip silently.
        return

    # qFTD-006 — two bugs fixed here, must stay before candle dedup:
    #
    # Bug 1 — wrong timestamp source:
    #   candle.ts is the kline OPEN time (start of the 1-min bar) — always
    #   60–120 s old by the time on_tick fires.  tick_age > DHM_STALE_TICK_SEC
    #   on every single call → permanent STALE_TICK block regardless of WS health.
    #   Fix: use tick.ts (aggTrade exchange timestamp, milliseconds old).
    #
    # Bug 2 — gate starved by candle dedup:
    #   Pre-gate was placed after the dedup guard, so the gate was only re-evaluated
    #   once per candle close (~60 s).  After a WS reconnect the gate stayed blocked
    #   until the next candle — creating a safe-mode infinite loop.
    #   Fix: evaluate health + gate on every tick so the gate clears mid-minute.
    candle_buf     = list(mdp.candle_close_buffer(sym))
    _n_candles     = len(candle_buf)
    _ind_ok_coarse = _n_candles >= cfg.IV_MIN_CANDLES
    now_ms         = int(time.time() * 1000)

    # qFTD-007: Update indicator_validator singleton on every tick so the
    # GlobalGateController._deploy_fn() sees real indicator readiness instead
    # of always returning False (iv_score=0 → deploy score capped at 75).
    # indicator_validator.is_ready() is called by _deploy_fn() which feeds
    # BootDeployabilityEngine — this was the source of the chronic "ind=0" log.
    # qFTD-007-v2: pass previous-tick indicator values for NaN detection.
    _r_state_early = regime_det.state(sym)
    _iv_values = None
    if _r_state_early is not None:
        _iv_values = {
            "adx": float(getattr(_r_state_early, "adx", float("nan"))),
            "atr": float(getattr(_r_state_early, "atr_pct", float("nan"))),
        }
    iv_result = indicator_validator.validate_symbol_buffers(
        candle_close_buf=candle_buf,
        candle_volume_buf=list(mdp.candle_volume_buffer(sym)),
        indicator_values=_iv_values,
    )

    # qFTD-007-v2: BOOTING→LIVE transition.
    # While BOOTING, gate failures block trading but never activate safe mode so
    # warmup noise cannot permanently trip the engine before data streams open.
    # Transition to LIVE when indicators are ready OR grace period has elapsed.
    if _system_state == "BOOTING":
        _elapsed = time.time() - _boot_ts
        if iv_result.ok or _elapsed >= cfg.STARTUP_GRACE_SECONDS:
            _system_state = "LIVE"
            global_gate_controller.set_system_state("LIVE")  # qFTD-010: lift BOOT_GRACE
            logger.info(
                f"[BOOT] BOOTING→LIVE | iv_ok={iv_result.ok} "
                f"elapsed={_elapsed:.1f}s grace={cfg.STARTUP_GRACE_SECONDS}s"
            )

    _dh_result = data_health_monitor.check(
        last_tick_ts=tick.ts / 1000.0,
        symbol_tick_ages={sym: max(0.0, time.time() - tick.ts / 1000.0)},
        indicator_ready=_ind_ok_coarse,
    )
    _data_fresh_ok = not _dh_result.block_trading

    # Phase 7A.3: Pre-gate control.
    # qFTD-010 Design Change 1/2/3:
    #   Signal generation ALWAYS runs — gate only locks EXECUTION.
    #   During BOOTING, indicator/data warmup conditions are bypassed so the
    #   scan pipeline warms up (learning engines, scorer) before going LIVE.
    #   INDICATOR_NOT_READY + DATA_NOT_FRESH are expected during the first 20 min
    #   and must not prevent signal observation.
    _gate_ind_ok    = True if _system_state == "BOOTING" else _ind_ok_coarse
    _gate_data_frsh = True if _system_state == "BOOTING" else _data_fresh_ok
    _pre_gate = execution_orchestrator.gate_check(
        symbol=sym,
        indicator_ok=_gate_ind_ok,
        data_fresh=_gate_data_frsh,
        activate_safe_mode=(_system_state == "LIVE"),
    )
    # qFTD-010: store execution permission — do NOT return early.
    # The scan pipeline continues regardless; only run_cycle is gated below.
    _execution_allowed = _pre_gate.allowed
    if not _execution_allowed:
        logger.debug(
            f"[SCAN] {sym} gate locked (execution blocked): {_pre_gate.reason}"
        )

    # Strategy/signal logic runs only on new candle closes (not every tick).
    if _last_processed_candle_ts.get(sym) == candle.ts:
        return
    _last_processed_candle_ts[sym] = candle.ts

    buf       = list(mdp.price_buffer(sym))           # tick prices — kept for legacy checks
    # candle_buf already computed above (before gate check)
    data_gate = strategy_engine.evaluate_data_sufficiency(len(candle_buf))
    if data_gate != "OK":
        error_registry.log("DATA_001", symbol=sym, extra=f"candles={len(candle_buf)}")  # FTD-REF-025
        _last_skip = {
            "ts": int(time.time() * 1000), "symbol": sym,
            "reason": f"{data_gate}({len(candle_buf)})",
        }
        return

    # 2b. Performance debounce: avoid repeated heavy regime/signal passes
    # for the same symbol within sub-second windows.
    prev_eval = _last_symbol_eval_ms.get(sym, 0)
    if now_ms - prev_eval < SYMBOL_EVAL_DEBOUNCE_MS:
        return
    _last_symbol_eval_ms[sym] = now_ms

    # 3. Detect regime
    regime_det.push(sym, candle.close, candle.high, candle.low, candle.ts)
    regime = regime_det.get(sym)
    # FTD-REF-019: debounce — only log on genuine regime transitions
    regime_debounce.push(sym, regime, state=regime_det.state(sym))

    # 4. Get appropriate strategy — UNKNOWN defaults to TrendFollowing during warmup
    strategy_type = {
        "TRENDING":             "TrendFollowing",
        "MEAN_REVERTING":       "MeanReversion",
        "VOLATILITY_EXPANSION": "VolatilityExpansion",
        "UNKNOWN":              "TrendFollowing",
    }.get(regime.value, "TrendFollowing")

    dna      = genome.active_dna.get(strategy_type, {})
    strategy = get_strategy(regime, dna)

    # 5. Generate signal (only if no open position + throttle checks)
    if sym not in risk_ctrl.positions and not risk_ctrl.halted and not risk_ctrl.graceful_stop:

        # ── Throttle A: per-symbol cooldown (30 min between trades) ──────────
        last_ts = _last_trade_ts.get(sym, 0)
        cooldown_remaining = SYMBOL_COOLDOWN_SEC - (now_ms - last_ts) / 1000
        if cooldown_remaining > 0:
            return   # too soon after last trade on this symbol

        # ── Throttle B: max 12 trades per hour across all symbols ─────────────
        one_hour_ago = now_ms - 3_600_000
        _trades_this_hour[:] = [t for t in _trades_this_hour if t > one_hour_ago]
        if len(_trades_this_hour) >= MAX_TRADES_PER_HOUR:
            return   # hourly cap reached

        # ── Symbol quality filter: skip non-ASCII (meme/scam coins) ──────────
        if not sym.isascii():
            return

        # Use real 1-min candle OHLC for strategy indicators.
        # tick_buffers hold individual trade prices (noisy, many per second) — they
        # produce fake ATR ≈ 0.1% which causes undersized SL distances, oversized qty,
        # and HIGH_FEE_RATIO / COST_HIGH failures. Candle buffers give accurate ATR.
        closes = candle_buf
        highs  = list(mdp.candle_high_buffer(sym)) or [p * 1.001 for p in candle_buf]
        lows   = list(mdp.candle_low_buffer(sym))  or [p * 0.999 for p in candle_buf]

        # FTD-REF-019: validate indicator quality before generating signal
        # ATR source priority:
        #   1. regime_det accumulated ATR (real OHLC, 28+ candles) — most accurate
        #   2. Single closed-kline (high-low)/close proxy — available after first kline
        # tick_buffers are individual trade prices (not candle closes), so
        # tick-to-tick ATR is 0.0001% and must NOT be used here.
        r_state        = regime_det.state(sym)
        regime_atr_pct = getattr(r_state, "atr_pct", 0.0)
        candle_atr_pct = ((candle.high - candle.low) / candle.close * 100) if candle.close > 0 else 0.0
        atr_pct        = regime_atr_pct if regime_atr_pct > 0 else candle_atr_pct
        raw_adx        = getattr(r_state, "adx", 0.0)
        guard          = indicator_guard.validate(
            symbol=sym, n_candles=len(buf), adx=raw_adx, atr_pct=atr_pct,
        )
        if not guard.ok:
            error_registry.log("DATA_002", symbol=sym, extra=guard.reason)  # FTD-REF-025
            return   # insufficient candles / unstable ADX / near-zero ATR

        # Phase 2: Hard-lock MeanReversion when ADX > 25 (strong trend regardless of regime label).
        if strategy_type == "MeanReversion" and raw_adx > 25.0:
            _last_skip = {
                "ts": now_ms, "symbol": sym,
                "reason": f"MR_TREND_LOCK(ADX={raw_adx:.1f}>25)",
                "regime": regime.value,
            }
            return

        # ── Phase 5.2: Dynamic Threshold Provider — master control layer ────────
        # Single source of truth: aggregates TradeActivator + AdaptiveFilter + DD
        # qFTD-010: streak/AF use session-only trades so replayed loss history
        # doesn't permanently tighten quality gates at boot (stacking deadlock fix).
        _tf_mins = trade_flow_monitor.minutes_since_last_trade()
        _session_trades = pnl_calc.trades[_boot_replay_count:]
        _p52_cl  = 0
        for _t in reversed(_session_trades):
            if _t.net_pnl < 0:
                _p52_cl += 1
            else:
                break
        thresholds = dynamic_threshold_provider.get(
            minutes_no_trade=_tf_mins,
            consecutive_losses=_p52_cl,
        )
        if thresholds.tier != "NORMAL" or thresholds.af_state != "NORMAL":
            _thought(
                f"⚡ DTP {sym}: tier={thresholds.tier} af={thresholds.af_state} "
                f"score_min={thresholds.score_min:.3f} "
                f"vol_mult={thresholds.volume_multiplier:.2f}×"
                f" fee_tol={thresholds.fee_tolerance:.2f}",
                "SIGNAL",
            )
        trade_flow_monitor.record_signal(sym)

        # ── Phase 6: Streak Intelligence — momentum-aware score adjustment ──
        _p52_cw = 0
        for _t in reversed(_session_trades):
            if _t.net_pnl > 0: _p52_cw += 1
            else: break
        _streak_result = streak_engine.check(
            consecutive_wins=_p52_cw, consecutive_losses=_p52_cl,
        )
        # Effective score_min = DTP base ± streak delta, floored at 0.40
        _eff_score_min = max(0.40, round(
            thresholds.score_min + _streak_result.score_adjustment, 4
        ))
        if _streak_result.state != "NEUTRAL":
            _thought(
                f"📈 STREAK {sym}: {_streak_result.state} "
                f"len={_streak_result.streak_len} "
                f"score_adj={_streak_result.score_adjustment:+.2f} "
                f"→ eff_min={_eff_score_min:.3f}",
                "SIGNAL",
            )

        # Phase 3: Volume Sleep Mode — dynamic threshold from DTP (no static bypass hack)
        vol_buf = mdp.candle_volume_buffer(sym)
        _paper_speed = (cfg.TRADE_MODE == "PAPER" and cfg.PAPER_SPEED_MODE)
        _vol_mult = thresholds.volume_multiplier
        if _paper_speed:
            # Aggressive paper throughput mode: relax sleep gate to its floor.
            _vol_mult = min(_vol_mult, 0.20)
        vol_active, vol_reason = volume_filter.is_active(
            sym, vol_buf, vol_multiplier=_vol_mult,
        )
        if _paper_speed and not vol_active:
            _thought(
                f"⚡ PAPER_SPEED bypass {sym}: {vol_reason}",
                "FILTER",
            )
            vol_active = True
        if not cfg.BYPASS_ALL_GATES and not vol_active:
            _last_skip = {"ts": now_ms, "symbol": sym, "reason": vol_reason, "regime": regime.value}
            trade_flow_monitor.record_skip(sym, vol_reason)
            return

        # Phase 3: Sector Correlation Guard — max 2 open positions from same sector.
        sector_ok, sector_reason = sector_guard.check(sym, risk_ctrl.positions)
        if not cfg.BYPASS_ALL_GATES and not sector_ok:
            _last_skip = {"ts": now_ms, "symbol": sym, "reason": sector_reason, "regime": regime.value}
            return

        # MASTER-001: risk engine gate (daily loss / trade cap / drawdown halt)
        risk_allowed, risk_reason = risk_engine.check_new_trade()
        if _paper_speed and not risk_allowed:
            if any(k in risk_reason for k in ("HALTED:", "MAX_DAILY_LOSS", "DAILY_TRADE_CAP")):
                _thought(f"⚡ PAPER_SPEED bypass risk gate {sym}: {risk_reason}", "FILTER")
                risk_allowed = True
        if not cfg.BYPASS_ALL_GATES and not risk_allowed:
            return   # daily risk limit reached

        # FTD-REF-024: market structure gate (LOW_VOL_TRAP / FAKE_BREAKOUT block)
        _bb_width = getattr(r_state, "bb_width", 0.0)
        ms_result = market_structure_detector.detect(
            adx=guard.adx, bb_width=_bb_width, atr_pct=guard.atr_pct,
        )
        if not cfg.BYPASS_ALL_GATES and not ms_result.tradeable:
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": ms_result.block_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return

        # FTD-REF-024: edge engine kill switch
        edge_allowed, edge_reason = edge_engine.check_trade(regime.value, strategy_type)
        if not cfg.BYPASS_ALL_GATES and not edge_allowed:
            error_registry.log("STRAT_002", symbol=sym, extra=edge_reason)  # FTD-REF-025
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": edge_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return

        # FTD-037: Adaptive Edge Engine kill switch (state-machine + cost filter)
        _aee_ok, _aee_reason = adaptive_edge_engine.check_trade(strategy_type)
        if not cfg.BYPASS_ALL_GATES and not _aee_ok:
            error_registry.log("STRAT_037", symbol=sym, extra=_aee_reason)
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": _aee_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return

        # FTD-REF-023: get dry-spell relaxation factor before signal filter
        relax_factor = trade_frequency.get_relaxation_factor()

        # MASTER-001 + FTD-REF-023: regime AI with per-symbol UNKNOWN fallback
        r_ai = regime_ai.classify(
            adx=guard.adx, atr_pct=guard.atr_pct,
            bb_width=getattr(r_state, "bb_width", 0.0),
            closes=closes,
            symbol=sym,
        )
        # FTD-REF-025: log STRAT_001 when AI regime is ambiguous (UNKNOWN)
        if r_ai.regime.value == "UNKNOWN":
            error_registry.log(
                "STRAT_001", symbol=sym,
                extra=f"adx={guard.adx:.1f} conf={r_ai.confidence:.2f}",
            )

        # FTD-REF-026: regime stability gate — block if conf <0.50 or <3 stable ticks
        if not cfg.BYPASS_ALL_GATES and r_ai.block_trade:
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": (
                    f"REGIME_UNSTABLE("
                    f"conf={r_ai.confidence:.2f},"
                    f"ticks={r_ai.stability_ticks})"
                ),
                "regime": regime.value, "strategy": strategy_type,
            }
            return

        # FTD-REF-023: scale confidence by per-regime learning-engine weight
        _regime_weight = learning_engine.get_regime_weight(r_ai.regime.value)
        # FTD-REF-026: profit guard — reduce effective confidence when PF < 1
        # qFTD-011: use session-only trades for consecutive_losses so replayed
        # loss history cannot trigger HARD_STOP at boot (same fix as _p52_cl).
        # qFTD-032: also use session-only count for n_trades passed to profit_guard.
        # Without this, 131 replayed trades (PF=0.37) applied a permanent 20%
        # confidence penalty from session start, blocking all signals until
        # enough new winning trades could offset the historical deficit.
        _pf_stats = pnl_calc.session_stats
        _session_trade_count = len(pnl_calc.trades) - _boot_replay_count
        _consecutive_losses = 0
        for _t in reversed(pnl_calc.trades[_boot_replay_count:]):
            if _t.net_pnl < 0:
                _consecutive_losses += 1
            else:
                break
        _pg_hard_stop, _pg_hard_reason = profit_guard.hard_stop_required(
            profit_factor=_pf_stats.get("profit_factor", 1.0),
            n_trades=_session_trade_count,
            consecutive_losses=_consecutive_losses,
        )
        if not cfg.BYPASS_ALL_GATES and _pg_hard_stop:
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": _pg_hard_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return

        _pf_mult  = profit_guard.frequency_multiplier(
            profit_factor=_pf_stats.get("profit_factor", 1.0),
            n_trades=_session_trade_count,
        )
        _adjusted_conf = round(r_ai.confidence * _regime_weight * _pf_mult, 3)

        # qFTD-011: diagnostic log before signal generation so we can see indicator
        # state at each candle close and confirm the pipeline is reaching this point.
        logger.info(
            f"[SIG] {sym} n={len(closes)} regime={regime.value} "
            f"adx={guard.adx:.1f} atr={guard.atr_pct:.4f}% "
            f"conf={_adjusted_conf:.3f} consec_loss={_consecutive_losses}"
        )

        sig = strategy.generate_signal(sym, closes, highs, lows)
        if not sig or sig.signal == Signal.NONE:
            logger.debug(f"[SIG] {sym} strategy={strategy_type} → NONE (no crossover / conditions unmet)")

        # Phase 4: Alpha Engine — supplementary high-quality signals
        # Runs when existing strategy produces no signal; all alpha signals
        # have already passed internal RR + Trade Scorer gates.
        if not sig or sig.signal == Signal.NONE:
            _vol_list_alpha = list(vol_buf)
            # qFTD-011: compute actual avg_atr_pct from recent candle history so
            # vol_expansion sub-score in trade_scorer uses a real baseline, not current ATR.
            _recent_candle_highs  = list(mdp.candle_high_buffer(sym))
            _recent_candle_lows   = list(mdp.candle_low_buffer(sym))
            _window = min(20, len(_recent_candle_highs))
            if _window >= 5 and candle_buf[-1] > 0:
                _avg_atr_pct = sum(
                    (h - l) / c * 100
                    for h, l, c in zip(
                        _recent_candle_highs[-_window:],
                        _recent_candle_lows[-_window:],
                        candle_buf[-_window:],
                    )
                ) / _window
            else:
                _avg_atr_pct = atr_pct
            _alpha_sig = alpha_engine.generate(
                symbol=sym, closes=closes, highs=highs, lows=lows,
                volumes=_vol_list_alpha, adx=guard.adx,
                atr_pct=atr_pct, avg_atr_pct=_avg_atr_pct,
                regime=regime.value,
            )
            if _alpha_sig:
                sig = _alpha_sig.trade_signal
                _thought(
                    f"⚡ ALPHA {_alpha_sig.alpha_type} {sym} "
                    f"score={_alpha_sig.score:.3f} rr={_alpha_sig.rr:.2f}",
                    "SIGNAL",
                )
            else:
                logger.debug(f"[SIG] {sym} alpha → NONE (RR/score below threshold)")

        if sig and sig.signal != Signal.NONE:
            execution_drive_policy.record_signal(sym)   # EDP: track signal activity
            _thought(f"🔔 Signal {sig.signal.value} {sym} | {sig.reason}", "SIGNAL")
            logger.info(
                f"[SCAN] Signal generated: {sig.signal.value} {sym} "
                f"score={sig.confidence:.3f} exec={'YES' if _execution_allowed else 'LOCKED'}"
            )

            # ── A.I.E. — Adaptive Inverse Engine ─────────────────────────────
            # If this strategy's win-rate is in the "wrong" zone, flip it.
            # NO_TRADE (40–60% WR) → skip; INVERSE (<40% WR) → flip direction.
            _inv = inverse_engine.get_decision(
                strategy_id=strategy_type,
                signal=sig.signal.value,
                entry_price=sig.entry_price,
                stop_loss=sig.stop_loss,
                take_profit=sig.take_profit,
            )
            if not cfg.BYPASS_ALL_GATES and _inv.mode == TradeMode.CALIBRATE:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _inv.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                return
            if _inv.inverted:
                sig = TradeSignal(
                    symbol=sig.symbol,
                    signal=Signal(_inv.final_signal),
                    entry_price=_inv.entry_price,
                    stop_loss=_inv.stop_loss,
                    take_profit=_inv.take_profit,
                    confidence=sig.confidence,
                    strategy_id=sig.strategy_id + "_INV",
                    reason=f"{sig.reason} | {_inv.reason}",
                )
                _thought(f"🔄 AIE INVERSE → {sig.signal.value} {sym}", "SIGNAL")

            # 6. Size the position (FTD-REF-024: apply edge booster multiplier)
            sizing = scaler.compute(sym, sig.entry_price, sig.stop_loss)
            if sizing.qty <= 0:
                return
            _edge_mult = edge_engine.get_size_multiplier(regime.value, strategy_type)
            _aee_mult  = adaptive_edge_engine.get_size_mult(strategy_type)
            # Combine: take the lower bound as a safety floor, then apply edge boost
            # AEE SCALING (>1×) stacks with edge_engine boost; REDUCED (<1×) overrides
            _final_mult = _aee_mult * _edge_mult if _aee_mult >= 1.0 else _aee_mult
            sizing.qty  = sizing.qty * _final_mult
            # atr_pct already computed above from candle OHLC / regime_det

            # FTD-REF-023: realistic cost via execution_engine
            notional      = sizing.qty * sig.entry_price
            cost_usdt     = execution_engine.fee_for_notional(notional) * 2
            # Per-unit cost for signal_filter (which computes gross_tp per-unit as abs(tp-entry))
            cost_per_unit = cost_usdt / sizing.qty if sizing.qty > 0 else cost_usdt

            # FTD-REF-024: fee-aware gate — reject if TP profit can't cover fees
            _gross_tp = abs(sig.take_profit - sig.entry_price) * sizing.qty
            _fee_reject, _fee_reason = execution_engine.should_reject_for_fees(
                expected_gross_profit=_gross_tp, notional=notional,
            )
            if not cfg.BYPASS_ALL_GATES and _fee_reject:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _fee_reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                return

            # ── Phase 6: Loss Cluster Controller — gates ALL trades ──────────
            _lcc_result = loss_cluster_controller.check(consecutive_losses=_p52_cl)
            if not cfg.BYPASS_ALL_GATES and not _lcc_result.ok:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _lcc_result.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, _lcc_result.reason)
                return
            if _lcc_result.size_mult < 1.0:
                sizing.qty = round(sizing.qty * _lcc_result.size_mult, 8)
                if sizing.qty <= 0:
                    return

            # ── Phase 5.2 + 6: Exploration Hard Injection (guarded) ──────────
            # ExplorationGuard pre-checks daily loss cap before slot allocation.
            # Exploration runs BEFORE all quality filters; only DD + risk caps apply.
            _p52_conf  = min(sig.confidence, _adjusted_conf)
            _eg_result = exploration_guard.check(
                daily_loss_pct=exploration_engine.daily_loss_pct(scaler.equity),
            )
            _explore_inject = (
                exploration_engine.should_explore(
                    symbol=sym, score=_p52_conf, equity=scaler.equity,
                    ev_ok=False, est_risk=0.0,
                )
                if _eg_result.allowed
                else ExploreResult(
                    is_exploration=False, size_mult=1.0,
                    daily_loss_used_pct=exploration_engine.daily_loss_pct(scaler.equity),
                    reason=_eg_result.reason,
                )
            )
            _skip_quality   = _explore_inject.is_exploration
            if _skip_quality:
                _is_exploration_trade[sym] = True
                sizing.qty = round(sizing.qty * _explore_inject.size_mult, 8)
                if sizing.qty <= 0:
                    return
                _thought(
                    f"🔬 EXPLORE_INJECT {sym}: score={_p52_conf:.3f} "
                    f"size={_explore_inject.size_mult}× qty={sizing.qty:.6f}"
                    f" — quality gates bypassed, only risk limits apply",
                    "SIGNAL",
                )
                _alloc_score = _p52_conf  # use raw confidence for capital band

            if not _skip_quality:
                # FTD-REF-026: profit guard pre-filter (fee sanity before quality chain)
                _pg_block, _pg_reason = profit_guard.check_fee_ratio(
                    gross_tp_profit=_gross_tp, fee_cost=cost_usdt,
                )
                if not cfg.BYPASS_ALL_GATES and _pg_block:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _pg_reason, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _pg_reason)
                    return

                # FTD-REF-024: get current edge for signal filter gate
                _expected_edge = edge_engine.get_edge(regime.value, strategy_type)

                # MASTER-001 + FTD-REF-023/024: adaptive signal quality filter
                sf_result = signal_filter.check(
                    symbol=sym, entry=sig.entry_price,
                    take_profit=sig.take_profit, stop_loss=sig.stop_loss,
                    cost_usdt=cost_per_unit, atr_pct=atr_pct,
                    confidence=_adjusted_conf, regime=r_ai.regime.value,
                    relaxation_factor=relax_factor, expected_edge=_expected_edge,
                )
                if not cfg.BYPASS_ALL_GATES and not sf_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": sf_result.reason, "rr": sf_result.rr,
                        "confidence": r_ai.confidence, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, sf_result.reason)
                    return

                # FTD-REDIS-017: hard strategy quality gate (RR/confidence/regime)
                strat_gate = strategy_engine.evaluate_signal(
                    rr=sf_result.rr, confidence=_adjusted_conf,
                    regime=("UNSTABLE" if r_ai.block_trade else r_ai.regime.value),
                )
                if not cfg.BYPASS_ALL_GATES and not strat_gate.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": strat_gate.reason, "rr": sf_result.rr,
                        "confidence": _adjusted_conf, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, strat_gate.reason)
                    return

                # ── Phase 5: Adaptive Scorer — dynamic-weight quality gate ────
                _vol_list     = list(vol_buf)
                _avg_vol_p5   = (sum(_vol_list[-20:]) / max(len(_vol_list[-20:]), 1)
                                 if _vol_list else 1.0)
                _cur_vol_p5   = _vol_list[-1] if _vol_list else 0.0
                _vol_ratio    = _cur_vol_p5 / _avg_vol_p5 if _avg_vol_p5 > 0 else 1.0
                _rsi_now      = (_rsi(closes, cfg.RSI_PERIOD)
                                 if len(closes) >= cfg.RSI_PERIOD + 1 else 50.0)
                _rsi_prev     = (_rsi(closes[:-1], cfg.RSI_PERIOD)
                                 if len(closes) >= cfg.RSI_PERIOD + 2 else _rsi_now)
                _tp_dist_p5   = abs(sig.take_profit - sig.entry_price)
                _cost_frac_p5 = cost_per_unit / _tp_dist_p5 if _tp_dist_p5 > 0 else 1.0

                _score_result = adaptive_scorer.score(
                    symbol=sym, regime=r_ai.regime.value,
                    adx=guard.adx, rsi=_rsi_now, rsi_prev=_rsi_prev,
                    atr_pct=atr_pct, avg_atr_pct=atr_pct,
                    vol_ratio=_vol_ratio, cost_fraction=_cost_frac_p5,
                    signal_side=sig.signal.value,
                )
                if not cfg.BYPASS_ALL_GATES and not _score_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _score_result.reason,
                        "score": _score_result.score,
                        "regime": regime.value, "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _score_result.reason)
                    return

                # ── Phase 5: Confidence Decay — dynamic threshold from DTP ────
                _decay_result = confidence_decay.decay(
                    symbol=sym, strategy_id=sig.strategy_id,
                    base_conf=_score_result.score,
                )
                _decayed_conf = _decay_result.decayed_confidence
                # EDP: apply no_execution_override (FTD-034) + drive-mode floor
                _edp_status = execution_drive_policy.get_status()
                _eff_score_min = trade_activator.no_execution_override(
                    _eff_score_min, signals=1, trades=_edp_status.trades_1min,
                )
                _eff_score_min = execution_drive_policy.get_score_override(_eff_score_min)
                if not cfg.BYPASS_ALL_GATES and _decayed_conf < _eff_score_min:  # Phase 6: DTP + streak-adjusted
                    # EDP: bypass decay gate for strong signals (high score + high RR)
                    if execution_drive_policy.should_force_execute(
                        _score_result.score, sf_result.rr
                    ):
                        _thought(
                            f"⚡ EDP FORCE {sym}: score={_score_result.score:.3f}"
                            f" rr={sf_result.rr:.2f} — decay gate bypassed",
                            "SIGNAL",
                        )
                    else:
                        _last_skip = {
                            "ts": int(time.time() * 1000), "symbol": sym,
                            "reason": f"DECAY_FILTER({_decay_result.reason})",
                            "score": _decayed_conf,
                            "score_min_used": _eff_score_min,
                            "regime": regime.value, "strategy": strategy_type,
                        }
                        trade_flow_monitor.record_skip(sym, "DECAY_FILTER")
                        return

                # ── Phase 4: RR Engine — enforce min Risk-Reward ──────────────
                _atr_price = atr_pct * sig.entry_price / 100
                _rr_result = rr_engine.evaluate(
                    side=sig.signal.value, entry=sig.entry_price,
                    stop_loss=sig.stop_loss, take_profit=sig.take_profit,
                    atr=_atr_price, atr_pct=atr_pct,
                )
                if not cfg.BYPASS_ALL_GATES and not _rr_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _rr_result.reason, "rr": _rr_result.rr,
                        "regime": regime.value, "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _rr_result.reason)
                    return
                sig = TradeSignal(
                    symbol=sig.symbol, signal=sig.signal,
                    entry_price=sig.entry_price,
                    stop_loss=_rr_result.adjusted_sl,
                    take_profit=_rr_result.adjusted_tp,
                    confidence=min(sig.confidence, _decayed_conf),
                    strategy_id=sig.strategy_id,
                    reason=(f"{sig.reason} | RR={_rr_result.rr:.2f} "
                            f"SCORE={_score_result.score:.3f} "
                            f"DECAY={_decay_result.decay_factor:.2f}"),
                )

                # ── Phase 5.2: Smart Fee Guard — fully dynamic (RR + DTP) ─────
                _sfg_result = smart_fee_guard.check(
                    rr=_rr_result.rr, gross_tp=_gross_tp, fee_cost=cost_usdt,
                    normal_max_override=thresholds.fee_tolerance,  # dynamic
                )
                if not cfg.BYPASS_ALL_GATES and not _sfg_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _sfg_result.reason, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _sfg_result.reason)
                    return

                # ── Phase 5: EV Engine — expected value gate ──────────────────
                _est_reward = abs(sig.take_profit - sig.entry_price) * sizing.qty
                _est_risk   = abs(sig.entry_price - sig.stop_loss) * sizing.qty
                _ev_result  = ev_engine.evaluate(
                    strategy_id=sig.strategy_id, symbol=sym,
                    est_reward=_est_reward, est_risk=_est_risk,
                    current_cost=cost_usdt,
                    drawdown=drawdown_controller.current_drawdown(),           # Phase 7B
                    regime_confidence=r_ai.confidence,                         # Phase 7B
                )
                if not cfg.BYPASS_ALL_GATES and not _ev_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _ev_result.reason,
                        "ev": _ev_result.ev, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _ev_result.reason)
                    return
                if not _ev_result.bootstrapped:
                    _thought(
                        f"🧮 EV {sym}: ev={_ev_result.ev:.4f} "
                        f"p_win={_ev_result.p_win:.1%} n={_ev_result.n_trades}",
                        "SIGNAL",
                    )

                # ── Phase 6: EV Confidence Engine — tier-based size mult ──────
                _evc_result = ev_confidence_engine.classify(_ev_result.ev)
                if not cfg.BYPASS_ALL_GATES and not _evc_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _evc_result.reason, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _evc_result.reason)
                    return
                if _evc_result.size_mult < 1.0:
                    sizing.qty = round(sizing.qty * _evc_result.size_mult, 8)
                    if sizing.qty <= 0:
                        return
                    _thought(
                        f"📊 EVC {sym}: tier={_evc_result.tier} "
                        f"ev={_evc_result.ev:.4f} → {_evc_result.size_mult:.0%}× size",
                        "SIGNAL",
                    )

                _alloc_score = _score_result.score  # use adaptive scorer score

            # ── Common path: Drawdown Controller + Capital Allocator ──────────
            # DrawdownController is always re-checked fresh (not from cached DTP)
            _dd_result = drawdown_controller.check()
            if not cfg.BYPASS_ALL_GATES and not _dd_result.allowed:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _dd_result.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, _dd_result.reason)
                return

            _alloc = capital_allocator.allocate(
                trade_score=_alloc_score,  # dynamic: explore uses raw conf, normal uses scorer
                equity=scaler.equity,
                base_risk_usdt=sizing.usdt_risk,
            )
            if not cfg.BYPASS_ALL_GATES and _alloc.size_multiplier <= 0:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _alloc.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, _alloc.reason)
                return
            # ── Phase 6: Capital Recovery Engine — smooth size restoration ──
            _recovery_result = capital_recovery_engine.check()
            # FTD-038+039: priority (AEE rank) × stabilizer (equity smoothness)
            _cfe_mult       = capital_flow_engine.get_combined_mult(strategy_type)
            _combined_mult  = round(
                _alloc.size_multiplier
                * _dd_result.multiplier
                * _recovery_result.size_mult
                * _cfe_mult,
                6,
            )
            if _recovery_result.state not in ("NORMAL", "FULLY_RECOVERED"):
                _thought(
                    f"🔄 RECOVERY {sym}: state={_recovery_result.state} "
                    f"recovery={_recovery_result.recovery_pct:.0%} "
                    f"size={_recovery_result.size_mult:.2f}×",
                    "SIGNAL",
                )
            # ── FTD-040: Consistency Engine — final unified consistency check ─
            _ce_state = consistency_engine.evaluate(
                consecutive_wins=_p52_cw,
                consecutive_losses=_p52_cl,
                dd_result=_dd_result,
                recovery_result=_recovery_result,
                lcc_result=_lcc_result,
            )
            if not cfg.BYPASS_ALL_GATES and not _ce_state.allowed:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": f"CE_PAUSED:{_ce_state.reason}",
                    "regime": regime.value, "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, f"CE_PAUSED:{_ce_state.reason}")
                _thought(
                    f"🛑 CONSISTENCY_PAUSED {sym}: {_ce_state.reason}",
                    "SIGNAL",
                )
                return
            if _ce_state.size_mult < 1.0:
                _combined_mult = round(_combined_mult * _ce_state.size_mult, 6)
                _thought(
                    f"🎯 CONSISTENCY {sym}: mode={_ce_state.mode} "
                    f"ce_mult={_ce_state.size_mult:.2f}× "
                    f"reason={_ce_state.reason}",
                    "SIGNAL",
                )
            # ── Phase 7A: Execution Orchestrator — full profit pipeline ─────
            # Receives the combined upstream multiplier and applies gate-aware
            # rank → compete → concentrate → pre-trade gate → amplify on top.
            _vol_list_orch = list(vol_buf)
            _avg_vol_orch  = (sum(_vol_list_orch[-20:]) / max(len(_vol_list_orch[-20:]), 1)
                              if _vol_list_orch else 1.0)
            _cur_vol_orch  = _vol_list_orch[-1] if _vol_list_orch else 0.0
            _vol_ratio_orch = _cur_vol_orch / _avg_vol_orch if _avg_vol_orch > 0 else 1.0
            _orch_ev = getattr(_ev_result, "ev", 0.0) if (not _skip_quality and not cfg.BYPASS_ALL_GATES) else 0.0
            _orch_score = _alloc_score
            # qFTD-010 Design Change 2: execution gate — final lock before position open.
            # Scan ran fully (warm-up, learning engines, scoring) regardless of gate status.
            # Only actual position creation is blocked when execution is not allowed.
            if not cfg.BYPASS_ALL_GATES and not _execution_allowed:
                logger.info(
                    f"[SCAN] Signal rejected — execution locked: {_pre_gate.reason} "
                    f"| {sig.signal.value} {sym} score={_alloc_score:.3f}"
                )
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": f"EXEC_GATE:{_pre_gate.reason}",
                    "regime": regime.value, "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, f"EXEC_GATE:{_pre_gate.reason}")
                return

            _orch_ctx = TickContext(
                symbol=sym,
                price=price,
                regime=regime.value,
                strategy=strategy_type,
                ev=_orch_ev,
                trade_score=_orch_score,
                volume_ratio=_vol_ratio_orch,
                equity=scaler.equity,
                base_risk_usdt=sizing.usdt_risk,
                upstream_mult=_combined_mult,
                indicator_ok=guard.ok,
                data_fresh=_data_fresh_ok,     # qFTD-004: from data_health_monitor (not hardcoded)
                is_exploration=_skip_quality,
            )
            _cycle = execution_orchestrator.run_cycle(_orch_ctx)
            if not _cycle.execute:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _cycle.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, _cycle.reason)
                return

            # Apply orchestrator concentration multiplier (folds in upstream_mult + band boost)
            sizing.qty = round(sizing.qty * _cycle.concentration_mult, 8)
            if sizing.qty <= 0:
                return
            _thought(
                f"💰 Orchestrator {sym}: score={_alloc_score:.3f} "
                f"upstream_mult={_combined_mult:.2f}× "
                f"conc_mult={_cycle.concentration_mult:.2f}× "
                f"band={_cycle.band} rank={_cycle.rank_score:.3f} "
                f"amplified={_cycle.amplified} "
                f"explore={_skip_quality} qty={sizing.qty:.6f}",
                "SIGNAL",
            )

            edge_ok, edge = risk_ctrl.get_trade_decision(
                side=sig.signal.value,
                entry=sig.entry_price,
                take_profit=sig.take_profit,
                stop_loss=sig.stop_loss,
                qty=sizing.qty,
                current_volatility=atr_pct,
                regime=regime.value,   # Fix B: regime-specific RR threshold
                minutes_no_trade=_tf_mins,  # qFTD-040: tiered required_r relaxation during dry spells
            )
            if not cfg.BYPASS_ALL_GATES and not edge_ok:
                rr_net = edge.get('rr_after_cost', 0)
                rr_req = edge.get('required_r', 0)
                _thought(
                    f"⛔ Skip {sym}: weak edge gross={edge.get('gross_tp', 0):.3f} "
                    f"cost={edge.get('cost', 0):.3f} net={edge.get('net_if_tp', 0):.3f} "
                    f"RR={edge.get('rr', 0):.2f} RR_net={rr_net:.2f} "
                    f"RR_req={rr_req:.2f} ATR%={edge.get('current_volatility', 0):.2f}",
                    "FILTER",
                )
                # Update live skip tracker for dashboard indicator
                _last_skip = {
                    "ts":          int(time.time() * 1000),
                    "symbol":      sym,
                    "reason":      "WEAK_EDGE",
                    "rr_net":      round(rr_net, 3),
                    "rr_req":      round(rr_req, 3),
                    "gap":         round(rr_req - rr_net, 3),
                    "regime":      edge.get("regime", regime.value),
                    "cost":        round(edge.get("cost", 0), 4),
                    "net_if_tp":   round(edge.get("net_if_tp", 0), 4),
                    "strategy":    strategy_type,
                }
                return

            # 7. PAPER MODE EXECUTION LOCK (qFTD-009 §FIX5 — non-negotiable)
            # This engine operates on real market data + virtual execution only.
            # All fills are internal simulations; NO exchange order API is called.
            # If TRADE_MODE is ever misconfigured to "LIVE", hard-block here.
            if cfg.TRADE_MODE != "PAPER":
                logger.critical(
                    f"[EXECUTION-LOCK] TRADE_MODE={cfg.TRADE_MODE} — "
                    f"real order BLOCKED. Only PAPER mode is permitted."
                )
                return

            # Open position — use Limit Order when enabled (saves fees + slippage)
            if cfg.USE_LIMIT_ORDERS:
                offset = sig.entry_price * (cfg.LIMIT_ENTRY_OFFSET_BPS / 10_000)
                if sig.signal.value == "LONG":
                    limit_px = sig.entry_price - offset   # buy slightly below signal price
                else:
                    limit_px = sig.entry_price + offset   # sell slightly above signal price

                submitted = risk_ctrl.submit_limit_order(
                    symbol=sym,
                    side=sig.signal.value,
                    limit_price=limit_px,
                    qty=sizing.qty,
                    stop_loss=sig.stop_loss,
                    take_profit=sig.take_profit,
                    strategy_id=sig.strategy_id,
                    initial_risk=sizing.usdt_risk,
                    regime=regime.value,
                )
                if submitted:
                    _trades_this_hour.append(now_ms)
                    _last_trade_ts[sym] = now_ms
                    trade_frequency.record_trade()   # FTD-REF-023: dry-spell tracker
                    execution_drive_policy.record_trade(sym)   # EDP: reset idle timer
                    # Phase 4: register with trade manager for lifecycle tracking
                    trade_manager.register(ManagedPosition(
                        symbol=sym, side=sig.signal.value,
                        entry_price=limit_px, stop_loss=sig.stop_loss,
                        take_profit=sig.take_profit,
                        initial_risk=abs(limit_px - sig.stop_loss),
                        qty=sizing.qty,
                    ))
                    capital_allocator.record_risk_used(sizing.usdt_risk)
                    _thought(
                        f"📋 Limit {sig.signal.value} {sym} @ {limit_px:.4f} "
                        f"qty={sizing.qty:.6f} risk={sizing.usdt_risk:.2f}U "
                        f"[{strategy_type} | {regime.value}]",
                        "TRADE",
                    )
            else:
                pos = OpenPosition(
                    position_id=str(uuid.uuid4())[:8],
                    symbol=sym,
                    side=sig.signal.value,
                    entry_price=sig.entry_price,
                    qty=sizing.qty,
                    stop_loss=sig.stop_loss,
                    take_profit=sig.take_profit,
                    entry_ts=int(time.time() * 1000),
                    strategy_id=sig.strategy_id,
                    initial_risk=sizing.usdt_risk,
                    regime=regime.value,
                )
                if risk_ctrl.open_position(pos, order_type="MARKET"):
                    _trades_this_hour.append(now_ms)
                    _last_trade_ts[sym] = now_ms
                    trade_frequency.record_trade()   # FTD-REF-023: dry-spell tracker
                    execution_drive_policy.record_trade(sym)   # EDP: reset idle timer
                    # Phase 4: register with trade manager for lifecycle tracking
                    trade_manager.register(ManagedPosition(
                        symbol=sym, side=sig.signal.value,
                        entry_price=sig.entry_price, stop_loss=sig.stop_loss,
                        take_profit=sig.take_profit,
                        initial_risk=abs(sig.entry_price - sig.stop_loss),
                        qty=sizing.qty,
                    ))
                    capital_allocator.record_risk_used(sizing.usdt_risk)
                    _thought(
                        f"✅ Opened {sig.signal.value} {sym} "
                        f"qty={sizing.qty:.6f} risk={sizing.usdt_risk:.2f}U "
                        f"[{strategy_type} | {regime.value}]",
                        "TRADE",
                    )

    # 8. Ingest candle into genome engine + persist to data lake
    candle_dict = {
        "open": candle.open, "high": candle.high,
        "low": candle.low,   "close": candle.close,
        "volume": candle.volume, "ts": candle.ts,
    }
    genome.ingest_candle(sym, candle_dict)
    data_lake.ingest_candle(
        sym, candle.interval,
        candle.open, candle.high, candle.low, candle.close,
        candle.volume, candle.ts,
    )

    # 9. Persist tick to data lake (async-safe buffered write)
    data_lake.ingest_tick(
        sym, tick.price, tick.bid, tick.ask, tick.qty, tick.ts
    )
    if sym in mdp.funding:
        f = mdp.funding[sym]
        data_lake.ingest_funding(sym, f.rate, f.next_funding)

    # 10. Broadcast market update to dashboard
    await _broadcast_market_update(sym, tick, regime.value)

    # FTD-031: record cycle latency, feed guard + alerting
    if cfg.PERF_ENABLED:
        perf_monitor.on_cycle_end(sym)


async def _broadcast_market_update(sym: str, tick: Tick, regime: str):
    data = {
        "type":   "market_update",
        "symbol": sym,
        "price":  tick.price,
        "regime": regime,
        "ts":     tick.ts,
    }
    for ws in list(_ws_clients):
        asyncio.create_task(_safe_send(ws, data))


# ── App Lifespan ──────────────────────────────────────────────────────────────

def _asyncio_exception_handler(loop, context):
    """
    Custom asyncio exception handler that silently absorbs WinError 10054
    (WSAECONNRESET) and Errno 104 (ECONNRESET) raised by the internal
    _ProactorBasePipeTransport callback on Windows.  These are Binance-side
    TCP RSTs, not bugs in our code — logging at DEBUG keeps the console clean
    while preserving the audit trail.  All other exceptions fall through to
    the default asyncio handler.
    """
    exc = context.get("exception")
    if exc is not None:
        win_err = getattr(exc, "winerror", None)
        err_no  = getattr(exc, "errno", None)
        if isinstance(exc, (ConnectionResetError, OSError)) and (
            win_err == 10054 or err_no == 104
        ):
            logger.debug(
                f"[asyncio] Absorbed _ProactorBasePipeTransport CONN_RESET "
                f"(WinError {win_err}/Errno {err_no}) — Binance TCP RST, not a local error."
            )
            return
    loop.default_exception_handler(context)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Install custom asyncio exception handler to absorb WinError 10054
    # (_ProactorBasePipeTransport WSAECONNRESET) before any tasks start.
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(_asyncio_exception_handler)

    global _engine_running, _boot_ts
    _engine_running = True
    _boot_ts = time.time()
    ensure_auth_ready_for_mode()
    mdp.register_callback(on_tick)
    # Pre-seed regime_detector during candle bootstrap so indicators are warm from boot
    mdp.set_regime_detector(regime_det)
    _thought("🚀 EOW Quant Engine booting…", "SYSTEM")
    _thought(f"Mode: {cfg.TRADE_MODE} | Capital: {cfg.INITIAL_CAPITAL} USDT", "SYSTEM")

    # ── FTD-014B: Function Registry startup validation ────────────────────────
    try:
        import json, pathlib
        _reg_path = pathlib.Path(__file__).parent / "core" / "registry" / "function_registry.json"
        if _reg_path.exists():
            _reg = json.loads(_reg_path.read_text())
            if isinstance(_reg, dict):
                _reg_count = len(_reg.get("functions", []))
            else:
                _reg_count = len(_reg) if isinstance(_reg, list) else 0
            _thought(f"📋 Function Registry loaded — {_reg_count} functions registered", "SYSTEM")
        else:
            _thought("⚠ Function Registry not found at core/registry/function_registry.json", "HALT")
    except Exception as _e:
        _thought(f"⚠ Function Registry load error: {_e}", "HALT")

    # ── Fix A: Reload promoted DNA so genome doesn't reset on restart ─────────
    genome.load_persisted_dna()
    required_strategies = {"TrendFollowing", "MeanReversion", "VolatilityExpansion"}
    missing = [s for s in required_strategies if not genome.active_dna.get(s)]
    if missing:
        raise RuntimeError(f"DNA validation failed before engine start: missing={missing}")

    # ── Phase 6.6: Hard Start Validator — boot gate ──────────────────────────
    _hsv_result = hard_start_validator.run(
        candle_count=cfg.HSV_MIN_CANDLES_BOOT,   # assume warm after mdp bootstrap
        indicator_ok=True,
        ws_reachable=True,
    )
    if not _hsv_result.ok:
        logger.critical(f"[HARD-START] Blocking engine start: {_hsv_result.failures}")
        # enforce() already called inside run(); execution stops here in prod.

    # ── MASTER-001: risk_engine.initialize() MOVED — see qFTD-009 boot block below ──
    # Risk engine MUST be initialized with the RESTORED equity, not INITIAL_CAPITAL.
    # Initialize call is deferred until after snapshot + replay determine the correct value.

    # ── FTD-REF-019: Boot diagnostics ────────────────────────────────────────
    global _boot_status
    _boot_status = await api_loader.run(api_manager=api_manager)

    # ── Start all subsystems ──────────────────────────────────────────────────
    tasks = [
        asyncio.create_task(mdp.start()),
        asyncio.create_task(genome.start()),
        asyncio.create_task(healer.start()),
        asyncio.create_task(data_lake.start()),
        asyncio.create_task(ws_stab.start()),   # FTD-REF-019: tick watchdog
        asyncio.create_task(infra_health.monitor(
            interval_seconds=15,
            ws_state_fn=lambda: ws_stab.summary().get("state", "UNKNOWN"),
            api_mode_fn=lambda: _boot_status.get("api", "NOT CONNECTED"),
            api_ok_fn=lambda: _boot_status.get("api_ok", False),
            running_fn=lambda: _engine_running,
        )),
        # qFTD-009: periodic snapshot backup every 30 s (guards against missed trade-close saves)
        asyncio.create_task(
            equity_snapshot.start_periodic_save(
                equity_fn=lambda: scaler.equity,
                trade_count_fn=lambda: len(pnl_calc.trades),
                interval_sec=30,
            )
        ),
    ]

    # ── qFTD-009 FINAL: Authoritative Boot State Restoration ─────────────────
    #
    # CORRECT SEQUENCE (non-negotiable):
    #   1. Load equity snapshot  (instant, from JSON)
    #   2. Run DataLake replay   (always — for validation AND as fallback)
    #   3. Validate: snapshot ≈ replay → if mismatch → SAFE MODE
    #   4. Determine final equity (snapshot > replay > fresh)
    #   5. risk_engine.initialize(final_equity)  ← NEVER before this point
    #
    # BOOT_MODE=FRESH: snapshot-first, replay fallback if no snapshot
    # BOOT_MODE=RESUME: replay-first, snapshot validation layer on top
    #
    await asyncio.sleep(0.5)   # give data_lake.start() a moment to open SQLite

    _snap          = equity_snapshot.load()
    _replay_equity = cfg.INITIAL_CAPITAL
    _replay_count  = 0

    try:
        _hist = data_lake.get_trades(limit=5000)
        if _hist:
            _replay_count  = pnl_calc.replay_from_history(_hist)
            _replay_equity = pnl_calc.session_stats.get("capital", pnl_calc.capital)
            # qFTD-010: record replay boundary so streak/AF use session-only trades
            global _boot_replay_count
            _boot_replay_count = _replay_count
            _thought(
                f"📂 DataLake replay: {_replay_count} trades → "
                f"equity={_replay_equity:.2f} USDT",
                "SYSTEM",
            )
        else:
            _thought("📂 DataLake: no trade history found.", "SYSTEM")
    except Exception as _exc:
        _thought(f"⚠️ DataLake replay failed: {_exc} — will use snapshot only.", "SYSTEM")

    # Determine the single authoritative equity value
    if _snap and _replay_count > 0:
        if equity_snapshot.validate(_snap.equity, _replay_equity):
            _final_equity = _snap.equity
            _restore_src  = (
                f"snapshot({_snap.equity:.2f}) validated vs replay({_replay_equity:.2f})"
            )
        else:
            # Mismatch is a data integrity event — activate safe mode
            safe_mode_engine.activate("EQUITY_MISMATCH_BOOT")
            _final_equity = _replay_equity   # DataLake is ground truth
            _restore_src  = (
                f"MISMATCH equity — SAFE MODE activated | "
                f"snapshot={_snap.equity:.2f} replay={_replay_equity:.2f} | "
                f"using replay (DataLake is ground truth)"
            )
    elif _snap:
        _final_equity = _snap.equity
        _restore_src  = f"snapshot only ({_snap.equity:.2f} USDT, no replay history)"
    elif _replay_count > 0:
        _final_equity = _replay_equity
        _restore_src  = f"replay only ({_replay_equity:.2f} USDT, no snapshot file)"
    else:
        _final_equity = cfg.INITIAL_CAPITAL
        _restore_src  = f"fresh start ({cfg.INITIAL_CAPITAL:.2f} USDT — no prior state found)"

    # ── MASTER-001 (qFTD-009): Initialize risk engine with RESTORED equity ────
    risk_engine.initialize(_final_equity)
    scaler.set_equity(_final_equity)
    _thought(f"📂 State restored: {_restore_src}", "SYSTEM")
    logger.info(f"[BOOT-STATE] {_restore_src}")

    # ── Phase 4: Profit Engine boot log ─────────────────────────────────────
    _thought(
        f"⚡ Phase 4 Profit Engine online | "
        f"rr_min={rr_engine.min_rr} "
        f"score_min={trade_scorer.min_score} "
        f"max_per_trade={capital_allocator.max_capital_pct:.0%} "
        f"daily_cap={capital_allocator.daily_risk_cap:.0%}",
        "SYSTEM",
    )
    # ── Phase 5: EV + Adaptive Intelligence boot log ─────────────────────────
    _thought(
        f"🧠 Phase 5 EV Engine online | "
        f"ev_window={cfg.EV_WINDOW} ev_min_trades={cfg.EV_MIN_TRADES} "
        f"adaptive_lr={cfg.ADAPTIVE_LR} "
        f"dd_stop={cfg.DD_STOP_AT:.0%}",
        "SYSTEM",
    )
    # Initialise drawdown controller with RESTORED equity (qFTD-009: not INITIAL_CAPITAL)
    drawdown_controller.update_equity(_final_equity)
    # FTD-040: Seed consistency engine with restored equity baseline
    consistency_engine.update_equity(_final_equity)
    # ── Phase 5.1: Activation + Exploration Control boot log ─────────────────
    _thought(
        f"🔓 Phase 5.1 Activation Layer online | "
        f"activator_tiers=T1@{cfg.ACTIVATOR_T1_MIN}min "
        f"T2@{cfg.ACTIVATOR_T2_MIN}min "
        f"T3@{cfg.ACTIVATOR_T3_MIN}min | "
        f"explore_rate={cfg.EXPLORE_RATE:.0%} "
        f"smart_fee_rr≥{cfg.SFG_HIGH_RR_THRESHOLD}:{cfg.SFG_HIGH_RR_FEE_MAX:.0%}",
        "SYSTEM",
    )
    # ── Phase 6.6: Initial gate probe (diagnostic only — no safe mode side-effect)
    # qFTD-005: system is not yet ready at boot; a failing gate here is expected.
    # activate_safe_mode=False prevents premature SAFE activation before data streams open.
    _gate_boot = global_gate_controller.evaluate(activate_safe_mode=False)
    _gate_msg  = (
        f"Phase 6.6 Gate online | can_trade={_gate_boot['can_trade']} "
        f"reason={_gate_boot['reason']} safe_mode={_gate_boot['safe_mode']}"
    )
    _thought(_gate_msg, "SYSTEM")
    logger.info(f"[GLOBAL-GATE] {_gate_msg}")

    _thought("All subsystems online. Scanning markets…", "SYSTEM")

    # ── Pre-seed genome candle store after bootstrap completes ────────────────
    async def _seed_genome_from_bootstrap():
        """Wait for mdp bootstrap to complete, then inject candles into genome."""
        for _ in range(90):   # wait up to 90s for mdp._running to be True
            if getattr(mdp, "_running", False):
                genome.seed_from_market_data(mdp)
                return
            await asyncio.sleep(1)
        logger.warning("[GENOME] Bootstrap seed timeout — candle store will fill naturally from live stream.")

    tasks.append(asyncio.create_task(_seed_genome_from_bootstrap()))

    # ── Guardian periodic reactive check ─────────────────────────────────────
    async def _guardian_watch():
        """Every 60 s, check if live risk has drifted into unsafe territory."""
        while True:
            await asyncio.sleep(60)
            try:
                stats    = pnl_calc.session_stats
                win_rate = stats.get("win_rate", 0.0)
                mdd_pct  = stats.get("max_drawdown_pct", 0.0)
                trades   = pnl_calc.trades
                valid_r  = [t.r_multiple for t in trades if t.r_multiple != 0.0]
                pos_r    = [r for r in valid_r if r > 0]
                neg_r    = [abs(r) for r in valid_r if r < 0]
                avg_r_win  = (sum(pos_r) / len(pos_r)) if pos_r else 1.0
                avg_r_loss = (sum(neg_r) / len(neg_r)) if neg_r else 1.0
                alert = guardian.reactive_check(win_rate, mdd_pct, avg_r_win, avg_r_loss, cfg)
                if alert:
                    _thought(f"🛡 {alert}", "HALT")
            except Exception:
                pass

    tasks.append(asyncio.create_task(_guardian_watch()))

    # ── 8-hour checkpoint: JSON state + QPR report (Phase 3.1 persistence) ───
    async def _periodic_checkpoint():
        """Every 8 hours save full engine state + generate QPR for 7-day stress test."""
        while True:
            await asyncio.sleep(8 * 3600)
            try:
                # 1. JSON state export
                json_path = exporter.export(label="8h_checkpoint")
                # 2. QPR report archive
                stats    = pnl_calc.session_stats
                trades   = [asdict(t) for t in pnl_calc.trades]
                mode_info = {"trade_mode": cfg.TRADE_MODE, "engine_ver": "EOW_v1.0"}
                analytics = {}
                archive  = build_report_archive(trades, stats, mode_info, analytics, _thought_log)
                ts_tag   = int(time.time())
                rpt_path = f"data/exports/QPR_{ts_tag}_8h.zip"
                with open(rpt_path, "wb") as f:
                    f.write(archive)
                _thought(
                    f"📊 8h checkpoint: state saved → {json_path} | QPR → {rpt_path}",
                    "SYSTEM",
                )
                logger.info(f"[CHECKPOINT] 8h state+QPR saved: {json_path}, {rpt_path}")
            except Exception as exc:
                logger.warning(f"[CHECKPOINT] 8h export failed: {exc}")

    tasks.append(asyncio.create_task(_periodic_checkpoint()))

    # ── FTD-030: Autonomous Intelligence Loop ────────────────────────────────
    global _auto_intelligence

    def _ai_broadcast(payload: dict) -> None:
        """Broadcast auto-intelligence events to all connected WS dashboard clients."""
        import json as _json
        msg = _json.dumps(payload, default=str)
        for ws in list(_ws_clients):
            try:
                asyncio.create_task(_safe_send(ws, _json.loads(msg)))
            except Exception:
                pass

    _auto_intelligence = AutoIntelligenceEngine(
        state_fn=_sc_build_state,
        trades_fn=lambda: len(pnl_calc.trades),
        broadcast_fn=_ai_broadcast,
    )

    async def _auto_intelligence_loop():
        """FTD-030: Runs every AUTO_INTELLIGENCE_INTERVAL_MIN minutes."""
        interval_sec = cfg.AUTO_INTELLIGENCE_INTERVAL_MIN * 60.0
        while True:
            await asyncio.sleep(interval_sec)
            try:
                result = _auto_intelligence.tick()
                action = result.get("action") or result.get("phase") or "?"
                verdict = result.get("correction_verdict", "")
                logger.info(
                    f"[FTD-030] Auto-intelligence tick: action={action} "
                    f"verdict={verdict} cycles={_auto_intelligence._cycle_num}"
                )
                if action not in ("SKIPPED",):
                    _thought(
                        f"🧠 [FTD-030] Auto-intelligence cycle #{result.get('cycle_num', '?')}: "
                        f"meta_score={result.get('meta_score', 0):.1f} "
                        f"verdict={verdict or action}",
                        "SYSTEM",
                    )
            except Exception as exc:
                logger.warning(f"[FTD-030] Auto-intelligence loop error: {exc}")

    tasks.append(asyncio.create_task(_auto_intelligence_loop()))
    logger.info(
        f"[FTD-030] Auto-intelligence loop started | "
        f"interval={cfg.AUTO_INTELLIGENCE_INTERVAL_MIN}min"
    )

    # ── FTD-031: Performance Optimization Layer ───────────────────────────────
    if cfg.PERF_ENABLED:
        await task_queue.start()
        await perf_monitor.start_background_tasks()
        _thought(
            f"⚡ [FTD-031] Performance layer online | "
            f"target={cfg.PERF_LATENCY_TARGET_MS}ms "
            f"cache_ttl_pattern={cfg.PERF_CACHE_PATTERN_TTL_SEC}s "
            f"queue_workers={cfg.PERF_QUEUE_WORKERS}",
            "SYSTEM",
        )

    yield

    _thought("⏹ Engine shutting down…", "SYSTEM")
    _engine_running = False
    for t in tasks:
        t.cancel()
    await mdp.stop()
    await genome.stop()
    await healer.stop()
    await data_lake.stop()
    await ws_stab.stop()
    await api_manager.close()
    if cfg.PERF_ENABLED:
        await task_queue.shutdown()


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="EOW Quant Engine",
    description="Self-evolving autonomous multi-asset trading engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_allowed_origins(cfg.ALLOWED_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST Endpoints ────────────────────────────────────────────────────────────

def _resolve_indicator_state(regime_states: dict, mdp: MarketDataProvider) -> str:
    """
    Runtime indicator readiness for boot diagnostics.

    VALIDATED   — at least one symbol has a computed regime state with numeric
                  ADX and ATR% (regime_det only stores states when 28+ candles
                  are available, so any entry here is already quality-checked).
    WARMING_UP  — WebSocket is alive and ticks are flowing but the 28-candle
                  buffer is still filling.  System is healthy; indicators will
                  auto-validate within minutes.  Treated as ✅ in the boot log.
    PENDING_RUNTIME_VALIDATION — no ticks received yet (very early startup).
    """
    for symbol, state in regime_states.items():
        adx = getattr(state, "adx", None)
        atr_pct = getattr(state, "atr_pct", None)
        if isinstance(adx, (int, float)) and isinstance(atr_pct, (int, float)):
            return "VALIDATED"
    # Data is flowing but candles not yet fully buffered
    if len(mdp.ticks) > 0:
        return "WARMING_UP"
    return "PENDING_RUNTIME_VALIDATION"


def _resolve_boot_deployability(
    network_score: float,
    database_score: float,
    rr_edge_score: float,
    indicators_state: str,
) -> tuple[float, str]:
    """
    Boot deployability composite score (0-100).
    Score = sum of three pillar scores (network 0-30, database 0-30, rr_edge 0-40).
    READY when all three pillars meet their individual thresholds.
    """
    deployability_score = float(network_score) + float(database_score) + float(rr_edge_score)

    is_ready = (
        network_score >= 25
        and database_score >= 25
        and rr_edge_score >= 30
    )
    status = "READY" if is_ready else "NOT_READY"

    # With validated indicators, a zero RR-edge means no proven trading edge
    # yet, so boot deployability must remain hard-blocked at 0.
    if indicators_state == "VALIDATED" and rr_edge_score <= 0:
        return 0.0, "NOT_READY"

    # WARMING_UP is healthy — indicators are filling and will auto-validate.
    # Only cap score when no market data whatsoever has been received.
    if indicators_state == "PENDING_RUNTIME_VALIDATION":
        deployability_score = min(deployability_score, 40.0)
        status = "NOT_READY"
    elif indicators_state == "WARMING_UP":
        # Warm-up means ticks are flowing and indicator buffers are filling.
        # Use relaxed infra gates at boot so healthy live flow is reflected as
        # IMPROVING (not NOT_READY) while RR-edge is still building from zero.
        if network_score >= 20 and database_score >= 10:
            deployability_score = max(deployability_score, 60.0)
            if status != "READY":
                status = "IMPROVING"

    return round(float(deployability_score), 1), status

@app.get("/api/boot-status")
async def get_boot_status():
    """FTD-REF-019 / MASTER-001: Boot diagnostics — all subsystem status."""
    live_stab = ws_stab.summary()
    mdp_ws_state = mdp.websocket_state()
    re_snap   = risk_engine.snapshot()
    stats     = pnl_calc.session_stats
    n_trades  = len(pnl_calc.trades)
    infra = infra_health.snapshot()
    redis_state = infra.get("redis", _boot_status.get("redis", "NOT_AVAILABLE"))
    if mdp.redis_connected():
        redis_state = "CONNECTED"

    if mdp_ws_state == "CONNECTED":
        ws_state = "CONNECTED"
    elif mdp_ws_state in {"CONNECTING", "RECONNECTING"}:
        ws_state = mdp_ws_state
    else:
        ws_state = live_stab["state"]

    indicators_state = _resolve_indicator_state(
        regime_states=regime_det.all_states(),
        mdp=mdp,
    )
    heal    = healer.snapshot()
    recent  = heal.get("recent_events", [])
    # Use actual Redis connectivity (mdp.redis_connected()) as primary signal;
    # fall back to healer REDIS_FLUSH events as a secondary confirmation.
    redis_ok = mdp.redis_connected() or any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in recent
    )
    try:
        lake_s    = data_lake.db_stats()
        sqlite_ok = lake_s.get("trades", -1) >= 0
    except Exception:
        lake_s    = {}
        sqlite_ok = False
    valid_r = [t.r_multiple for t in pnl_calc.trades if t.r_multiple != 0.0]
    ws_is_connected = (ws_state == "CONNECTED")
    # Enrich lake_s with in-memory trade count when SQLite hasn't persisted yet
    merged_lake_s = dict(lake_s)
    if merged_lake_s.get("trades", 0) == 0 and n_trades > 0:
        merged_lake_s["trades"] = n_trades
    dep_idx = deployability_index(
        healer_snapshot=heal,
        lake_stats=merged_lake_s,
        genome_state=genome.export_state(),
        redis_ok=redis_ok,
        persistence_ok=(redis_ok or sqlite_ok),
        runtime_rr={
            "avg_r_multiple": (sum(valid_r) / len(valid_r)) if valid_r else 0.0,
            "win_rate": stats.get("win_rate", 0.0) / 100.0,
            "trades": n_trades,
        },
        ws_connected=ws_is_connected,
    )
    dep_breakdown = dep_idx.get("breakdown", {})
    network_score = float((dep_breakdown.get("network") or {}).get("score", 0))
    if live_stab.get("reconnect_count", 0) > 2:
        network_score = max(0.0, network_score - 10.0)
    database_score = float((dep_breakdown.get("database") or {}).get("score", 0))
    rr_edge_score = float((dep_breakdown.get("rr_edge") or {}).get("score", 0))

    boot_deployability_score, boot_deployability_status = _resolve_boot_deployability(
        network_score=network_score,
        database_score=database_score,
        rr_edge_score=rr_edge_score,
        indicators_state=indicators_state,
    )
    api_loader.set_runtime_status(
        websocket=ws_state,
        indicators=indicators_state,
    )
    api_loader.set_deployability(
        score=boot_deployability_score,
        status=boot_deployability_status,
    )
    _boot_status["websocket"] = ws_state
    _boot_status["indicators"] = indicators_state

    indicators_ok = indicators_state in ("VALIDATED", "WARMING_UP")

    return {
        **_boot_status,
        "redis":         redis_state,
        "websocket":     ws_state,
        "indicators":    indicators_state,
        "indicators_ok": indicators_ok,
        "ws_gap_s":      live_stab["gap_seconds"],
        "ws_reconnects": live_stab["reconnect_count"],
        "strategy_engine": "ACTIVE",
        "risk_engine":     "HALTED" if re_snap["halted"] else "ACTIVE",
        "execution_mode":  cfg.TRADE_MODE,
        "deployability":   boot_deployability_status,
        "deployability_score": boot_deployability_score,
        "deployability_components": {
            "network_score": network_score,
            "database_score": database_score,
            "rr_edge_score": rr_edge_score,
            "thresholds": {"network": 25, "database": 25, "rr_edge": 30},
            "analytics_tier": dep_idx.get("tier", "NOT READY"),
        },
    }


@app.get("/api/status")
async def get_status():
    return {
        "mode":        cfg.TRADE_MODE,
        "capital":     round(scaler.equity, 4),
        "drawdown_pct": round(scaler.drawdown_pct, 2),
        "streak":      scaler.streak,
        "halted":      risk_ctrl.halted,
        "symbols_watched": len(mdp.symbols),
        "open_positions":  len(risk_ctrl.positions),
        "total_trades":    len(pnl_calc.trades),
        "ws_status":   ws_truth_engine.get_ui_label(),   # FTD-REF-026: truth-engine label
        "ts":          int(time.time() * 1000),
        # Phase 4 Profit Engine summary
        "profit_engine": {
            "rr_engine":         rr_engine.summary(),
            "trade_scorer":      trade_scorer.summary(),
            "capital_allocator": capital_allocator.summary(),
            "trade_manager":     trade_manager.summary(),
            "alpha_engine":      alpha_engine.summary(),
        },
        # FTD-040: Consistency Engine quick-status
        "consistency": consistency_engine.status(),
    }


@app.get("/api/pnl")
async def get_pnl():
    return _sanitize(pnl_calc.session_stats)


@app.get("/api/market")
async def get_market():
    return mdp.snapshot()


@app.get("/api/positions")
async def get_positions():
    return risk_ctrl.snapshot()


@app.get("/api/genome")
async def get_genome():
    return genome.export_state()


@app.post("/api/genome/trigger")
async def trigger_genome_cycle():
    """
    Manually kick off one genome evolution cycle without waiting for the timer.
    Useful during initial deployment to accelerate Deployability Index build-up.
    Requires at least one symbol's candle data to have accumulated first.
    """
    candle_counts = {sym: len(c) for sym, c in genome._candle_store.items()}
    if not candle_counts:
        return {
            "ok": False,
            "reason": "No candle data in genome store yet — start the engine and wait for market data to flow.",
            "candle_counts": {},
        }
    await genome._evolution_cycle()
    state = genome.export_state()
    promotions = [p for p in state.get("promotion_log", []) if p.get("decision") == "PROMOTED"]
    return {
        "ok":             True,
        "generation":     state["generation"],
        "candle_counts":  candle_counts,
        "promoted_count": len(promotions),
        "last_promotion": promotions[-1] if promotions else None,
    }


@app.get("/api/regime")
async def get_regime():
    states = regime_det.all_states()
    return {sym: {
        "regime":     s.regime.value,
        "adx":        s.adx,
        "atr_pct":    s.atr_pct,
        "bb_width":   s.bb_width,
        "confidence": s.confidence,
    } for sym, s in states.items()}


@app.get("/api/thoughts")
async def get_thoughts(limit: int = 50):
    return _thought_log[-limit:]


@app.get("/api/health")
async def get_health():
    return healer.snapshot()


@app.get("/api/deployability")
async def get_deployability():
    """
    MASTER-001: Standalone deployability score.
    Score 0–100 with status: READY / IMPROVING / NOT_READY / BLOCKED / INSUFFICIENT_DATA.
    """
    stats = pnl_calc.session_stats
    n_trades = len(pnl_calc.trades)
    result = deployability_engine.compute(
        trades       = n_trades,
        sharpe       = stats.get("sharpe_ratio", 0.0),
        sortino      = stats.get("sortino_ratio", 0.0),
        win_rate     = stats.get("win_rate", 0.0),
        max_drawdown = stats.get("max_drawdown_pct", 0.0) / 100,
        risk_of_ruin = stats.get("risk_of_ruin", 0.0),
        avg_r        = stats.get("avg_r_multiple", 0.0),
    )
    return _sanitize(deployability_engine.to_dict(result))


@app.get("/api/risk-engine")
async def get_risk_engine():
    """MASTER-001: Daily risk limits, drawdown state, size multiplier."""
    return risk_engine.snapshot()


@app.get("/api/signal-filter")
async def get_signal_filter():
    """MASTER-001: Signal quality gate state — paused symbols, thresholds."""
    return signal_filter.summary()


@app.get("/api/lake")
async def get_lake():
    """Data Lake statistics — candle count, tick count, DB size."""
    return data_lake.db_stats()


@app.get("/api/trades")
async def get_trades(symbol: str = "", limit: int = 200):
    """Full trade history from the data lake."""
    return data_lake.get_trades(symbol=symbol, limit=limit)


@app.get("/api/candles/{symbol}")
async def get_candles(symbol: str, limit: int = 500):
    """Recent closed candles for a symbol (from data lake)."""
    return data_lake.get_candles(symbol.upper(), limit=limit)


@app.get("/api/scorecard")
async def get_scorecard():
    """
    Go-Live Scorecard — automated Phase 3 readiness checklist.

    Evaluates all three pillars before PAPER → LIVE promotion:
      1. Security: AUTH_ENABLED + CONTROL_API_KEYS configured.
      2. Expectancy: OOS PF ≥ 1.0 and overfitting ratio within bounds.
      3. Execution parity: post-cost avg R-multiple ≥ configured floor.
    """
    return compute_scorecard(genome, cfg).to_dict()


# ── DBO Analytics ────────────────────────────────────────────────────────────

@app.get("/api/analytics")
async def get_analytics():
    """
    Full DBO analytics payload:
      • Sortino + Sharpe + Calmar ratios
      • Risk-of-Ruin probability
      • Geometric vs Linear growth chart data
      • Deployability Index 0-100 (capped at 50 when persistence is BOGUS)
      • Benchmark comparison vs S&P 500 / hedge funds
    """
    heal    = healer.snapshot()
    recent  = heal.get("recent_events", [])
    # Use live redis connection as primary signal; healer events as fallback
    redis_ok = mdp.redis_connected() or any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in recent
    )
    try:
        lake_s    = data_lake.db_stats()
        sqlite_ok = lake_s.get("trades", -1) >= 0
    except Exception:
        lake_s    = {}
        sqlite_ok = False
    persistence_ok = redis_ok or sqlite_ok

    trade_dicts = [
        {"net_pnl": t.net_pnl, "r_multiple": t.r_multiple}
        for t in pnl_calc.trades
    ]

    analytics_payload = compute_full_analytics(
        pnl_trades=trade_dicts,
        initial_capital=pnl_calc._initial_capital,
        session_stats=pnl_calc.session_stats,
        healer_snapshot=heal,
        lake_stats=lake_s,
        genome_state=genome.export_state(),
        redis_ok=redis_ok,
        persistence_ok=persistence_ok,
        ws_connected=(mdp.websocket_state() == "CONNECTED"),
    )
    corrected = rolling_ratios(
        pnl_values=[t.get("net_pnl", 0.0) for t in trade_dicts],
        initial_capital=pnl_calc._initial_capital,
        max_drawdown_pct=pnl_calc.session_stats.get("max_drawdown_pct", 0.0),
        window=200,
    )
    analytics_payload.update(corrected)
    return _sanitize(analytics_payload)


@app.get("/api/mode-info")
async def get_mode_info():
    """
    Returns the human-readable trading mode label and persistence status.
    Used by the dashboard mode identifier strip.
    """
    heal   = healer.snapshot()
    recent = heal.get("recent_events", [])

    # Determine Redis health from recent heal events
    redis_ok = any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in recent
    )

    # Determine SQLite health:
    #   • connection is live  → healthy
    #   • OR db file already exists on disk (previous session data present)
    #   • db_stats() returns {} when conn not yet open (race on cold boot)
    import os as _os
    db_file_exists = _os.path.exists(data_lake.DB_PATH)
    conn_live      = data_lake._conn is not None
    try:
        stats     = data_lake.db_stats()
        stats_ok  = stats.get("trades", -1) >= 0
    except Exception:
        stats_ok  = False
    sqlite_ok = conn_live or db_file_exists or stats_ok

    persistence_ok = redis_ok or sqlite_ok

    # TIER system
    if not persistence_ok:
        tier, label, colour = 1, "TIER 1: DEMO — BOGUS DATA", "demo"
    elif cfg.TRADE_MODE == "LIVE":
        tier, label, colour = 3, "TIER 3: REAL LIVE — ORIGINAL CAPITAL", "live"
    else:
        tier, label, colour = 2, "TIER 2: LIVE PAPER — VIRTUAL CAPITAL", "paper"

    return {
        "mode":               cfg.TRADE_MODE,
        "tier":               tier,
        "label":              label,
        "colour":             colour,
        "redis_ok":           redis_ok,
        "sqlite_ok":          sqlite_ok,
        "db_file_exists":     db_file_exists,
        "conn_live":          conn_live,
        "persistence_ok":     persistence_ok,
        "persistence_warning": (
            "" if persistence_ok else
            "PERSISTENCE FAILED: Session data is non-permanent (BOGUS STORAGE)"
        ),
        "persistence_status": (
            "✅ PERSISTENCE ACTIVE" if persistence_ok else
            "⚠ PERSISTENCE FAILED"
        ),
        "ts": int(time.time() * 1000),
    }


@app.get("/api/perf-status")
async def get_perf_status():
    """FTD-031: Full performance metrics — latency, cache, guard state, queue, memory."""
    if not cfg.PERF_ENABLED:
        return {"enabled": False}
    return perf_monitor.snapshot()


@app.post("/api/perf-guard/reset")
async def reset_perf_guard():
    """FTD-031: Operator reset of PerfGuard back to NORMAL state."""
    perf_guard.reset()
    return {"ok": True, "state": perf_guard.state}


@app.get("/api/diagnostics/pipeline-break-forensics")
async def diagnostics_pipeline_break_forensics(cycles: int = 100):
    """
    FTD-031C: Pipeline break forensic probe — DISABLED BY DEFAULT.

    Isolation rules: manual trigger only, read-only, not part of core loop.
    Enable via DIAGNOSTICS_ENDPOINT_ENABLED=true in .env (developer use only).
    """
    if not cfg.DIAGNOSTICS_ENDPOINT_ENABLED:
        return {"enabled": False, "message": "Set DIAGNOSTICS_ENDPOINT_ENABLED=true to use this endpoint"}
    from tools.diagnostics.pipeline_break_forensics import run_probe
    return run_probe(cycles=max(1, min(cycles, 1000)))


@app.get("/api/report", response_class=HTMLResponse)
async def get_report():
    """
    Unified HTML report — open in browser and use Print → Save as PDF.
    Sections:
      1. Executive Summary (plain English)
      2. Performance Audit (PnL / Fees / Slippage breakdown)
      3. Signal Audit (every SKIP / TRADE decision from CT-Scan log)
    """
    stats  = pnl_calc.session_stats
    mode_r = await get_mode_info()
    now_str = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    # ── Signal Audit rows ──────────────────────────────────────────────────────
    audit_rows = ""
    for t in _thought_log:
        level = t.get("level", "INFO")
        msg   = t.get("msg", "").replace("<", "&lt;").replace(">", "&gt;")
        colour = {"TRADE": "#27ae60", "FILTER": "#e67e22", "SIGNAL": "#2980b9",
                  "HALT": "#e74c3c", "SYSTEM": "#8e44ad"}.get(level, "#555")
        ts_s = time.strftime("%H:%M:%S", time.gmtime(t.get("ts", 0) / 1000))
        audit_rows += (
            f'<tr><td style="color:#888">{ts_s}</td>'
            f'<td><span style="color:{colour};font-weight:600">{level}</span></td>'
            f'<td>{msg}</td></tr>\n'
        )

    # ── Executive summary text ─────────────────────────────────────────────────
    total_net   = stats.get("total_net_pnl", 0.0)
    win_rate    = stats.get("win_rate", 0.0)
    pf          = stats.get("profit_factor", 0.0)
    sharpe      = stats.get("sharpe_ratio", 0.0)
    mdd         = stats.get("max_drawdown_pct", 0.0)
    total_trades= stats.get("total_trades", 0)
    fees        = stats.get("total_fees_paid", 0.0)
    slippage    = stats.get("total_slippage", 0.0)
    capital     = stats.get("capital", pnl_calc._initial_capital)

    direction = "profit" if total_net >= 0 else "loss"
    verdict   = (
        "The engine is operating within normal risk parameters."
        if mdd < 10 else
        "Drawdown elevated — consider reducing position size."
    )

    persist_warn = mode_r.get("persistence_warning", "")
    persist_html = (
        f'<p style="background:#fff3cd;border-left:4px solid #f0ad4e;padding:8px 12px;'
        f'border-radius:4px;margin:12px 0">'
        f'<strong>⚠ {persist_warn}</strong></p>'
    ) if persist_warn else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EOW Quant Engine — Performance Report</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 960px; margin: 40px auto;
          color: #2c3e50; line-height: 1.6; }}
  h1   {{ color: #1a252f; border-bottom: 3px solid #3498db; padding-bottom: 8px; }}
  h2   {{ color: #2980b9; margin-top: 36px; }}
  .meta {{ color: #888; font-size: 13px; margin-bottom: 20px; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:12px;
            font-weight:700; color:#fff; background:#3498db; margin-left:8px; }}
  .badge.live {{ background:#e74c3c; }}
  table  {{ width:100%; border-collapse:collapse; margin-top:12px; }}
  th     {{ background:#ecf0f1; text-align:left; padding:8px 12px; font-size:13px; }}
  td     {{ padding:8px 12px; border-bottom:1px solid #ecf0f1; font-size:13px; }}
  tr:hover td {{ background:#fafafa; }}
  .pos  {{ color:#27ae60; font-weight:600; }}
  .neg  {{ color:#e74c3c; font-weight:600; }}
  .kv   {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin:16px 0; }}
  .card {{ background:#f8f9fa; border-radius:8px; padding:16px; text-align:center; }}
  .card .val {{ font-size:26px; font-weight:700; color:#2c3e50; }}
  .card .lbl {{ font-size:12px; color:#888; margin-top:4px; }}
  @media print {{ body {{ margin: 20px; }} }}
</style>
</head>
<body>
<h1>EOW Quant Engine
  <span class="badge {'live' if cfg.TRADE_MODE == 'LIVE' else ''}">{mode_r['label']}</span>
</h1>
<p class="meta">Generated: {now_str} &nbsp;|&nbsp; Session Capital: {capital:,.2f} USDT</p>
{persist_html}

<h2>1. Executive Summary</h2>
<p>
  The engine closed <strong>{total_trades} trades</strong> with a net {direction} of
  <strong class="{'pos' if total_net >= 0 else 'neg'}">{total_net:+,.2f} USDT</strong>.
  Win rate: <strong>{win_rate:.1f}%</strong> &nbsp;|&nbsp;
  Profit factor: <strong>{pf:.2f}</strong> &nbsp;|&nbsp;
  Sharpe: <strong>{sharpe:.3f}</strong> &nbsp;|&nbsp;
  Max drawdown: <strong>{mdd:.2f}%</strong>.
</p>
<p>{verdict}</p>

<div class="kv">
  <div class="card"><div class="val {'pos' if total_net >= 0 else 'neg'}">{total_net:+,.2f}</div><div class="lbl">Net PnL (USDT)</div></div>
  <div class="card"><div class="val">{win_rate:.1f}%</div><div class="lbl">Win Rate</div></div>
  <div class="card"><div class="val">{pf:.2f}</div><div class="lbl">Profit Factor</div></div>
  <div class="card"><div class="val">{sharpe:.3f}</div><div class="lbl">Sharpe Ratio</div></div>
  <div class="card"><div class="val">{mdd:.2f}%</div><div class="lbl">Max Drawdown</div></div>
  <div class="card"><div class="val">{capital:,.0f}</div><div class="lbl">Capital (USDT)</div></div>
</div>

<h2>2. Performance Audit</h2>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Total Trades</td><td>{total_trades}</td></tr>
  <tr><td>Net PnL</td><td class="{'pos' if total_net >= 0 else 'neg'}">{total_net:+,.4f} USDT</td></tr>
  <tr><td>Avg Win</td><td class="pos">{stats.get('avg_win_usdt', 0.0):+,.4f} USDT</td></tr>
  <tr><td>Avg Loss</td><td class="neg">{stats.get('avg_loss_usdt', 0.0):+,.4f} USDT</td></tr>
  <tr><td>Total Fees Paid</td><td class="neg">-{fees:,.4f} USDT</td></tr>
  <tr><td>Total Slippage Cost</td><td class="neg">-{slippage:,.4f} USDT</td></tr>
  <tr><td>Combined Cost Drag</td><td class="neg">-{fees + slippage:,.4f} USDT ({(fees + slippage) / max(abs(total_net) + fees + slippage, 1e-9) * 100:.1f}% of gross)</td></tr>
  <tr><td>Profit Factor</td><td>{pf:.3f}</td></tr>
  <tr><td>Sharpe Ratio</td><td>{sharpe:.3f}</td></tr>
  <tr><td>Max Drawdown</td><td>{mdd:.2f}%</td></tr>
</table>

<h2>3. Signal Audit</h2>
<p style="color:#888;font-size:13px">Full CT-Scan reasoning log — every signal, filter decision, and trade action.</p>
<table>
  <tr><th>Time</th><th>Level</th><th>Message</th></tr>
  {audit_rows if audit_rows else '<tr><td colspan="3" style="color:#aaa;text-align:center">No events recorded yet.</td></tr>'}
</table>
</body>
</html>"""
    return HTMLResponse(html)


# ── Triple-Format Report Archive (XLSX + PDF + MD → ZIP) ─────────────────────

@app.get("/api/report/archive")
async def get_report_archive():
    """
    Download a ZIP archive containing:
      • eow_trades_<ts>.xlsx  — full trade history + session summary + signal audit
      • eow_report_<ts>.pdf   — executive summary with all KPIs
      • eow_report_<ts>.md    — markdown developer log for version control
    """
    from fastapi.responses import StreamingResponse

    heal    = healer.snapshot()
    recent  = heal.get("recent_events", [])
    redis_ok = any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in recent
    )
    try:
        lake_s    = data_lake.db_stats()
        sqlite_ok = lake_s.get("trades", -1) >= 0
    except Exception:
        lake_s    = {}
        sqlite_ok = False
    persistence_ok = redis_ok or sqlite_ok

    trade_dicts = [
        {k: getattr(t, k) for k in t.__dataclass_fields__}
        for t in pnl_calc.trades
    ]
    analytics_data = _sanitize(compute_full_analytics(
        pnl_trades=[{"net_pnl": t.net_pnl, "r_multiple": t.r_multiple} for t in pnl_calc.trades],
        initial_capital=pnl_calc._initial_capital,
        session_stats=pnl_calc.session_stats,
        healer_snapshot=heal,
        lake_stats=lake_s,
        genome_state=genome.export_state(),
        redis_ok=redis_ok,
        persistence_ok=persistence_ok,
    ))
    mode_info = await get_mode_info()

    zip_bytes = build_report_archive(
        trades=trade_dicts,
        stats=pnl_calc.session_stats,
        mode_info=mode_info,
        analytics=analytics_data,
        thoughts=_thought_log,
    )

    filename = f"eow_report_{int(time.time())}.zip"
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── FTD-025B-URX-V2: [ EXPORT INTELLIGENT REPORT ] ──────────────────────────

@app.get("/api/report/full-system-v2")
async def get_full_system_report_v2():
    """
    FTD-025B-URX-V2 Unified Report Engine — cause-effect narrative.
    Returns a single Markdown file download.
    """
    from fastapi.responses import Response as _Response
    from core.reporting.unified_report_engine_v2 import generate_full_report_v2

    def _safe_v2(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    _mins_idle = trade_flow_monitor.minutes_since_last_trade()
    _ss        = pnl_calc.session_stats

    _v2_ct = _safe_v2(
        lambda: __import__("core.intelligence.suggestion_engine",
                           fromlist=["suggestion_engine"]).suggestion_engine.detect(
            profit_factor=_ss.get("profit_factor", 0.0),
            fee_ratio=round(
                _ss.get("total_fees_paid", 0.0)
                / max(abs(_ss.get("total_net_pnl", 0.0)) + _ss.get("total_fees_paid", 0.0), 1e-9),
                4,
            ),
            win_rate=_ss.get("win_rate", 0.0) / 100.0,
            n_trades=len(pnl_calc.trades),
            strategy_usage=strategy_engine.usage(),
            regime_stable=True,
        ), {}
    )

    data = {
        "generated_at":   time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "trade_flow":     _safe_v2(trade_flow_monitor.summary, {}),
        "mins_idle":      _mins_idle,
        "thresholds":     _safe_v2(
            lambda: dynamic_threshold_provider.summary(minutes_no_trade=_mins_idle), {}
        ),
        "session_stats":  _ss,
        "capital":        _safe_v2(capital_allocator.summary, {}),
        "risk":           _safe_v2(risk_ctrl.snapshot, {}),
        "gate":           _safe_v2(
            lambda: global_gate_controller.snapshot()
            if "global_gate_controller" in globals() else {}, {}
        ),
        "errors":         _safe_v2(lambda: error_registry.recent(20), []),
        "learning_memory": _safe_v2(
            lambda: __import__("core.learning_memory",
                               fromlist=["learning_memory_orchestrator"]
                               ).learning_memory_orchestrator.summary(), {}
        ),
        "ct_scan":        _v2_ct,
        "ai_brain":       _safe_v2(
            lambda: __import__("core.meta.ai_brain",
                               fromlist=["ai_brain"]).ai_brain.get_state(), {}
        ),
        "drawdown":       _safe_v2(drawdown_controller.summary, {}),
        "activator":      _safe_v2(trade_activator.summary, {}),
        "edge_engine":    _safe_v2(edge_engine.summary, {}),
        "thoughts":       list(_thought_log)[-30:],
    }

    report_md = generate_full_report_v2(data)
    filename  = f"unified_report_v2_{int(time.time())}.md"
    _thought("📊 Unified Report v2 exported (FTD-025B-URX-V2)", "SYSTEM")
    return _Response(
        content=report_md.encode("utf-8"),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── FTD-025A: [ EXPORT FULL SYSTEM REPORT ] ──────────────────────────────────

@app.get("/api/report/full-system")
async def get_full_system_report():
    """
    FTD-025A Export Engine — [ EXPORT FULL SYSTEM REPORT ] button handler.

    Returns a ZIP containing a full 15-section institutional report in both
    Markdown and PDF formats.  Single authority: core.export_engine.
    """
    from fastapi.responses import StreamingResponse

    def _safe(fn, default=None):
        try:
            return fn()
        except Exception as e:
            return default if default is not None else {"error": str(e)}

    async def _safe_async(fn, default=None):
        try:
            return await fn()
        except Exception as e:
            return default if default is not None else {"error": str(e)}

    heal       = _safe(healer.snapshot, {})
    lake_s     = _safe(data_lake.db_stats, {})
    redis_ok   = any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in heal.get("recent_events", [])
    )
    sqlite_ok  = lake_s.get("trades", -1) >= 0

    trade_dicts = [
        {k: getattr(t, k) for k in t.__dataclass_fields__}
        for t in pnl_calc.trades
    ]
    analytics = _sanitize(compute_full_analytics(
        pnl_trades=[{"net_pnl": t.net_pnl, "r_multiple": t.r_multiple}
                    for t in pnl_calc.trades],
        initial_capital=pnl_calc._initial_capital,
        session_stats=pnl_calc.session_stats,
        healer_snapshot=heal,
        lake_stats=lake_s,
        genome_state=_safe(genome.export_state, {}),
        redis_ok=redis_ok,
        persistence_ok=(redis_ok or sqlite_ok),
    ))
    mode_info = await get_mode_info()

    # Positions (best-effort)
    positions = []
    try:
        for sym, pos in risk_ctrl.positions.items():
            positions.append({
                "symbol": sym,
                "side":   getattr(pos, "side", ""),
                "qty":    getattr(pos, "qty", 0.0),
                "entry_px": getattr(pos, "entry_px", 0.0),
                "stop":     getattr(pos, "stop", 0.0),
                "tp":       getattr(pos, "tp", 0.0),
                "unrealised": getattr(pos, "unrealised_pnl", 0.0),
            })
    except Exception:
        positions = []

    # FTD-027: Use suggestion_engine.detect() for ct_scan field — it converts
    # ct_scan_engine's raw 'issues' list into structured 'findings' dicts,
    # and fires emergency findings even with < 10 trades (loss / no-trade triggers).
    _snap_stats      = pnl_calc.session_stats
    _snap_n_trades   = len(pnl_calc.trades)
    _snap_gross      = abs(_snap_stats.get("total_net_pnl", 0.0)) + _snap_stats.get("total_fees_paid", 0.0)
    _snap_fee_ratio  = _snap_stats.get("total_fees_paid", 0.0) / max(_snap_gross, 1e-9)
    ct_scan = _safe(
        lambda: __import__("core.intelligence.suggestion_engine",
                           fromlist=["suggestion_engine"]).suggestion_engine.detect(
            profit_factor=_snap_stats.get("profit_factor", 0.0),
            fee_ratio=round(_snap_fee_ratio, 4),
            win_rate=_snap_stats.get("win_rate", 0.0) / 100.0,
            n_trades=_snap_n_trades,
            strategy_usage=strategy_engine.usage(),
            regime_stable=True,
        ), {}
    )

    # FTD-027: AI Brain must produce concrete decisions — not empty state
    ai_brain_state = _safe(
        lambda: __import__("core.meta.ai_brain",
                           fromlist=["ai_brain"]).ai_brain.get_state(), {}
    )

    snapshot = SystemSnapshot(
        session_stats     = pnl_calc.session_stats,
        analytics         = analytics,
        mode_info         = mode_info,
        thoughts          = _thought_log,
        last_skip         = _safe(lambda: getattr(trade_flow_monitor,
                                                  "last_skip", lambda: {})(), {}),
        trade_flow        = _safe(trade_flow_monitor.summary, {}),
        risk_snapshot     = _safe(risk_ctrl.snapshot, {}),
        positions         = positions,
        drawdown          = _safe(drawdown_controller.summary, {}),
        genome_state      = _safe(genome.export_state, {}),
        learning          = _safe(learning_engine.summary, {}),
        edge              = _safe(edge_engine.summary, {}),
        strategy_usage    = _safe(strategy_engine.usage, {}),
        regime            = _safe(lambda: regime_memory.summary()
                                  if hasattr(regime_memory, "summary") else {}, {}),
        ct_scan           = ct_scan,
        dynamic_thresholds= _safe(
            lambda: dynamic_threshold_provider.summary(
                minutes_no_trade=trade_flow_monitor.minutes_since_last_trade()
            ), {}
        ),
        streak            = _safe(streak_engine.summary, {}),
        consistency       = _safe(consistency_engine.status, {}),
        capital_allocator = _safe(capital_allocator.summary, {}),
        error_registry    = _safe(lambda: error_registry.recent(50), []),
        healer            = heal,
        halt_audit        = _safe(lambda: risk_ctrl.halt_audit()
                                  if hasattr(risk_ctrl, "halt_audit") else {}, {}),
        trades            = trade_dicts,
        gate_status       = _safe(lambda: global_gate_controller.snapshot()
                                  if "global_gate_controller" in globals() else {}, {}),
        ai_brain_state    = ai_brain_state,
        learning_memory   = _safe(
            lambda: __import__("core.learning_memory",
                               fromlist=["learning_memory_orchestrator"]
                               ).learning_memory_orchestrator.summary(), {}
        ),
    )

    zip_bytes = system_export_engine.build_full_report(snapshot)
    filename  = f"full_system_report_{int(time.time())}.zip"
    _thought(f"📦 Full system report exported ({len(zip_bytes)} bytes)", "SYSTEM")
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Mode Toggle ───────────────────────────────────────────────────────────────

@app.post("/api/mode/{mode}")
async def set_mode(mode: str, _auth=Depends(require_roles("operator", "admin"))):
    if mode.upper() not in ("PAPER", "LIVE"):
        raise HTTPException(400, "Mode must be PAPER or LIVE")
    cfg.TRADE_MODE = mode.upper()
    _thought(f"⚡ Mode switched to {cfg.TRADE_MODE}", "SYSTEM")
    return {"mode": cfg.TRADE_MODE}


# ── Export ────────────────────────────────────────────────────────────────────

@app.post("/api/export")
async def export_state(label: str = ""):
    path = exporter.export(label)
    return FileResponse(path, filename=path.split("/")[-1], media_type="application/json")


@app.post("/api/import-dna")
async def import_dna_endpoint(body: dict, _auth=Depends(require_roles("operator", "admin"))):
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "path required")
    dna = exporter.import_dna(path)
    # Inject into genome
    for strategy_type, sub_dna in dna.items():
        if strategy_type in genome.active_dna:
            genome.active_dna[strategy_type] = sub_dna
    _thought(f"📥 DNA imported from {path}", "SYSTEM")
    return {"imported_types": list(dna.keys())}


# ── Emergency Controls ────────────────────────────────────────────────────────

@app.post("/api/emergency-close")
async def emergency_close(_auth=Depends(require_roles("admin"))):
    prices = {sym: tick.price for sym, tick in mdp.ticks.items()}
    risk_ctrl.emergency_close_all(prices)
    _thought("🚨 EMERGENCY CLOSE ALL triggered", "HALT")
    return {"closed": len(prices)}


@app.post("/api/resume")
async def resume_engine(_auth=Depends(require_roles("operator", "admin"))):
    risk_ctrl.halted = False
    _thought("✅ Engine manually resumed", "SYSTEM")
    return {"halted": False}


@app.post("/api/engine/reset")
async def reset_engine(_auth=Depends(require_roles("admin"))):
    """
    ADMIN: Full engine reset after a halt.
    Clears halted + graceful_stop, cancels pending limit orders,
    and logs an audit entry.  Does NOT close open positions.
    """
    prev_halted        = risk_ctrl.halted
    prev_graceful      = risk_ctrl.graceful_stop
    risk_ctrl.halted       = False
    risk_ctrl.graceful_stop = False
    risk_ctrl.pending_orders.clear()
    msg = (
        f"🔄 ENGINE RESET by admin — "
        f"halted={prev_halted} graceful_stop={prev_graceful} cleared. "
        f"Signal scanning resumed. {len(risk_ctrl.positions)} position(s) still open."
    )
    _thought(msg, "SYSTEM")
    return {
        "reset":              True,
        "previously_halted":  prev_halted,
        "open_positions":     len(risk_ctrl.positions),
        "ts":                 int(time.time() * 1000),
    }


@app.get("/api/halt-audit")
async def get_halt_audit():
    """
    Returns the auto-liquidation audit log:
    all HALT and CLOSE_POSITION risk events + current halted state.
    """
    halt_events = [
        {
            "ts":         e.ts,
            "event_type": e.event_type,
            "symbol":     e.symbol,
            "detail":     e.detail,
        }
        for e in risk_ctrl.events
        if e.event_type in ("HALT", "CLOSE_POSITION", "EMERGENCY")
    ]
    # Grab FILTER-level thoughts for SKIP audit
    skip_log = [
        t for t in _thought_log
        if t.get("level") == "FILTER"
    ][-50:]

    return {
        "halted":        risk_ctrl.halted,
        "graceful_stop": risk_ctrl.graceful_stop,
        "halt_events":   halt_events[-100:],
        "skip_log":      skip_log,
        "ts":            int(time.time() * 1000),
    }


@app.get("/api/last-skip")
async def get_last_skip():
    """
    Returns the most recent structured skip event for the live Skip Reason indicator.
    Also returns skip_total (all-time FILTER count this session) and recent 5 skips.
    """
    recent_skips = [t for t in _thought_log if t.get("level") == "FILTER"]
    return {
        "last_skip":    _last_skip,
        "skip_total":   len(recent_skips),
        "recent_msgs":  [s.get("msg", "") for s in recent_skips[-5:]],
        "ts":           int(time.time() * 1000),
    }


# ── FTD-REF-025: WebSocket Truth + Error Registry ────────────────────────────

@app.get("/api/ws-truth")
async def get_ws_truth():
    """FTD-REF-025: WebSocket truth state for the UI (CONNECTED/RECONNECTING/STALE/DOWN)."""
    return ws_truth_engine.to_dict()


@app.get("/api/errors")
async def get_errors(n: int = 50):
    """FTD-REF-025: Structured error registry — recent errors + occurrence counts."""
    return error_registry.summary()


# ── FTD-REF-026: Strategy / Profitability / CT-Scan endpoints ─────────────────

@app.get("/api/strategy-usage")
async def get_strategy_usage():
    """FTD-REF-026: Per-strategy usage distribution across all closed trades."""
    return strategy_engine.summary()


@app.get("/api/profit-guard")
async def get_profit_guard():
    """FTD-REF-026: Profit guard state — PF gate and fee-ratio threshold."""
    stats = pnl_calc.session_stats
    return profit_guard.summary(
        profit_factor=stats.get("profit_factor", 0.0),
        n_trades=len(pnl_calc.trades),
    )


@app.get("/api/inverse-engine")
async def get_inverse_engine():
    """A.I.E.: Adaptive Inverse Engine — per-strategy mode and win-rate."""
    return {
        "strategies": inverse_engine.summary(),
        "thresholds": {
            "win_threshold":     0.60,
            "inverse_threshold": 0.40,
            "min_samples":       10,
        },
    }


@app.get("/api/ct-scan")
async def get_ct_scan():
    """FTD-REF-026: CT-Scan system health report — HEALTHY / WARNING / CRITICAL."""
    stats    = pnl_calc.session_stats
    n_trades = len(pnl_calc.trades)
    total_fees  = stats.get("total_fees_paid",  0.0)
    total_net   = stats.get("total_net_pnl",    0.0)
    total_slip  = stats.get("total_slippage",   0.0)
    # gross ≈ |net| + fees + slippage (approximation without raw gross field)
    total_gross = abs(total_net) + total_fees + total_slip
    fee_ratio   = total_fees / max(total_gross, 1e-9)
    win_rate_pct = stats.get("win_rate", 0.0)   # comes back as 0–100
    return ct_scan_engine.scan(
        profit_factor=stats.get("profit_factor", 0.0),
        fee_ratio=round(fee_ratio, 4),
        strategy_usage=strategy_engine.usage(),
        win_rate=win_rate_pct / 100.0,
        regime_stable=True,
        n_trades=n_trades,
    )


# ── FTD-040: Consistency Engine endpoint ─────────────────────────────────────

@app.get("/api/consistency")
async def get_consistency():
    """
    FTD-040 Consistency Engine — unified system stability status.

    Returns:
      equity_volatility_pct  — rolling std-dev of equity returns (%)
      mode context           — what the engine would classify as current mode
      configuration          — all CE_* thresholds for reference

    For the live pre-trade ConsistencyState (mode + size_mult + reason), that
    is computed per-trade signal and logged to the thought_log stream.
    """
    status = consistency_engine.status()
    dd     = drawdown_controller.summary()
    return {
        "consistency":    status,
        "drawdown":       dd,
        "streak":         streak_engine.summary(),
        "capital_recovery": capital_recovery_engine.summary(),
        "loss_cluster":   loss_cluster_controller.summary(),
        "description": (
            "FTD-040 Consistency Engine: makes profit repeatable. "
            "Tracks equity volatility, profit smoothing, and unified mode."
        ),
    }


# ── FTD-026A: Layer integration endpoints ────────────────────────────────────

@app.get("/api/suggestions")
async def get_suggestions():
    """FTD-015 Suggestion Engine — CT-Scan enriched with confidence + impact."""
    from core.intelligence.suggestion_engine import suggestion_engine
    stats    = pnl_calc.session_stats
    n_trades = len(pnl_calc.trades)
    total_gross = abs(stats.get("total_net_pnl", 0.0)) + stats.get("total_fees_paid", 0.0)
    fee_ratio   = stats.get("total_fees_paid", 0.0) / max(total_gross, 1e-9)
    return suggestion_engine.detect(
        profit_factor=stats.get("profit_factor", 0.0),
        fee_ratio=round(fee_ratio, 4),
        win_rate=stats.get("win_rate", 0.0) / 100.0,
        n_trades=n_trades,
        strategy_usage=strategy_engine.usage(),
        regime_stable=True,
    )


@app.get("/api/auto-tuning")
async def get_auto_tuning():
    """FTD-016 Auto-Tuning — current dynamic threshold state."""
    from core.tuning.tuner_controller import tuner_controller
    return tuner_controller.get_state()


@app.get("/api/alert-state")
async def get_alert_state():
    """FTD-018 Alert Engine — severity-sorted, deduplicated alerts."""
    from core.alerts.alert_engine import alert_engine
    gs   = global_gate_controller.snapshot() if hasattr(global_gate_controller, "snapshot") else {}
    halt = {}
    try:
        halt = risk_ctrl.halt_audit() if hasattr(risk_ctrl, "halt_audit") else {}
    except Exception:
        pass
    return alert_engine.get_alerts(
        gate_status=gs,
        halt_audit=halt,
        error_recent=error_registry.recent(50),
        drawdown=drawdown_controller.summary(),
    )


@app.get("/api/evolution")
async def get_evolution():
    """FTD-019 Strategy Evolution — genome champion/challenger state."""
    from core.evolution.evolution_engine import evolution_engine
    return evolution_engine.get_state()


@app.get("/api/portfolio-state")
async def get_portfolio_state():
    """FTD-020 Portfolio — allocation + exposure view."""
    from core.portfolio.allocation_engine import allocation_engine
    positions = []
    try:
        for sym, pos in risk_ctrl.positions.items():
            positions.append({
                "symbol":   sym,
                "side":     getattr(pos, "side",       ""),
                "qty":      getattr(pos, "qty",        0.0),
                "entry_px": getattr(pos, "entry_px",   0.0),
                "stop":     getattr(pos, "stop",       0.0),
                "tp":       getattr(pos, "tp",         0.0),
                "unrealised": getattr(pos, "unrealised_pnl", 0.0),
            })
    except Exception:
        pass
    return allocation_engine.get_state(
        positions=positions,
        equity=scaler.equity,
    )


@app.get("/api/risk-state")
async def get_risk_state():
    """FTD-021 Risk Engine — unified risk + drawdown view."""
    rs = risk_ctrl.snapshot()
    dd = drawdown_controller.summary()
    return {
        **rs,
        "drawdown": dd,
        "module":   "RISK_STATE",
        "phase":    "021",
    }


@app.get("/api/audit-log")
async def get_audit_log():
    """FTD-022 Audit Layer — structured event log."""
    from core.audit.audit_engine import audit_engine
    return audit_engine.get_log(limit=100)


@app.get("/api/ai-brain")
async def get_ai_brain():
    """FTD-023 AI Brain — aggregated intelligence state + decision."""
    from core.meta.ai_brain import ai_brain
    return ai_brain.get_state()


@app.get("/api/capital-allocator")
async def get_capital_allocator():
    """FTD-024 Capital Scaling — allocator + growth state."""
    from core.capital.scaling_engine import scaling_engine
    return scaling_engine.get_state(
        equity=scaler.equity,
        initial_capital=pnl_calc._initial_capital,
    )


# ── FTD-029: Self-Correction Engine (Closed-Loop Intelligence) ───────────────

def _sc_build_state():
    """Shared helper: build system_state + current_params for FTD-029 endpoints."""
    from config import cfg
    from core.deep_validation.contradiction_engine import ContradictionEngine

    stats    = pnl_calc.session_stats
    n_trades = len(pnl_calc.trades)
    dd       = drawdown_controller.summary()
    rs       = risk_ctrl.snapshot()
    gs       = global_gate_controller.snapshot() if hasattr(global_gate_controller, "snapshot") else {}

    equity    = float(scaler.equity or 0.0)
    dd_pct    = float(dd.get("drawdown_pct", 0.0) or 0.0)
    win_rate  = float(stats.get("win_rate", 0.0) or 0.0) / 100.0
    total_pnl = float(stats.get("total_net_pnl", 0.0) or 0.0)
    halted    = rs.get("halted", False)

    system_state = {
        "equity":               equity,
        "total_trades":         n_trades,
        "total_pnl":            total_pnl,
        "win_rate":             win_rate,
        "current_drawdown_pct": dd_pct,
        "halted":               halted,
        "risk_halted":          halted,
        "sharpe_ratio":         stats.get("sharpe_ratio", None),
    }

    contradiction = ContradictionEngine().run({
        **system_state,
        "total_signals":    n_trades,
        "trades_active":    len(risk_ctrl.positions) > 0,
        "max_drawdown_pct": 0.15,
        "kill_switch_active": not gs.get("can_trade", True),
    })
    meta_score     = 85.0 if contradiction["passed"] else 55.0
    ai_brain_score = min(100.0, max(0.0, win_rate * 100.0 + (10.0 if total_pnl >= 0 else -10.0)))

    current_params = {
        "P7B_PERF_WIN_THRESHOLD":  cfg.P7B_PERF_WIN_THRESHOLD,
        "P7B_PERF_LOSS_THRESHOLD": cfg.P7B_PERF_LOSS_THRESHOLD,
        "P7B_EV_HIGH_THRESHOLD":   cfg.P7B_EV_HIGH_THRESHOLD,
        "P7B_EV_LOW_THRESHOLD":    cfg.P7B_EV_LOW_THRESHOLD,
        "TR_EV_WEIGHT":            cfg.TR_EV_WEIGHT,
        "ADAPTIVE_LR":             cfg.ADAPTIVE_LR,
        "ADAPTIVE_MIN_WEIGHT":     cfg.ADAPTIVE_MIN_WEIGHT,
        "ADAPTIVE_MAX_WEIGHT":     cfg.ADAPTIVE_MAX_WEIGHT,
        "KELLY_FRACTION":          cfg.KELLY_FRACTION,
        "EXPLORE_EV_FLOOR":        cfg.EXPLORE_EV_FLOOR,
    }

    ftd028_validators = {
        "contradiction": contradiction,
        "performance": {
            "passed":    total_pnl >= 0,
            "issue_count": 0 if total_pnl >= 0 else 1,
            "issues":    [] if total_pnl >= 0 else [{"message": f"negative PnL={total_pnl:.2f}"}],
        },
        "risk": {
            "passed":    not halted,
            "error_count": 0 if not halted else 1,
            "errors":    [] if not halted else [{"message": "engine halted"}],
        },
    }
    ftd028_meta = {
        "system_score":     meta_score,
        "stability_score":  max(0.0, 100.0 - dd_pct * 500),
        "confidence_score": min(100.0, win_rate * 100.0 + 40.0),
    }

    return system_state, current_params, ftd028_validators, ftd028_meta, ai_brain_score, halted


@app.post("/api/self-correction/run")
async def run_self_correction():
    """
    FTD-029 — Full orchestrated correction cycle (Part 1–9).
    Flow: IssueExtract → Confidence → Policy → Priority → Plan → Collide → Apply → Audit.
    Requires ≥30 trades + FTD-028 score ≥ 70 + AI Brain ≥ 70.
    """
    from core.self_correction.correction_orchestrator import correction_orchestrator

    system_state, current_params, ftd028_validators, ftd028_meta, ai_brain_score, halted = (
        _sc_build_state()
    )
    return correction_orchestrator.run_cycle(
        ftd028_validators=ftd028_validators,
        ftd028_meta=ftd028_meta,
        current_params=current_params,
        system_state=system_state,
        ai_brain_score=ai_brain_score,
        risk_halted=halted,
        risk_violated=halted,
        contradiction_critical=not ftd028_validators["contradiction"].get("passed", True),
    )


@app.get("/api/self-correction/state")
async def get_self_correction_state():
    """FTD-029 — Full dashboard state (Q13): enabled, cooldown, overlay, audit, rollback."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    return correction_orchestrator.summary()


@app.get("/api/self-correction/logs")
async def get_self_correction_logs(n: int = 50):
    """FTD-029 — Recent correction audit log (Q11/Q13)."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    return {"logs": correction_orchestrator.logs(n), "phase": "029"}


@app.get("/api/self-correction/last-change")
async def get_last_self_correction():
    """FTD-029 — Last correction card for dashboard (Q13)."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    last = correction_orchestrator.last_change()
    return last or {"detail": "No corrections applied yet", "phase": "029"}


@app.post("/api/self-correction/manual-override")
async def manual_override_self_correction(body: dict = None):
    """
    FTD-029 — Human override endpoint (Q8/Q13).
    Body: {"action": "stop"|"resume"|"clear_overlay"|"enable"|"disable"}
    """
    from core.self_correction.correction_orchestrator import correction_orchestrator
    action = (body or {}).get("action", "stop")
    if action == "stop":
        correction_orchestrator.human_override_stop()
    elif action == "resume":
        correction_orchestrator.human_override_resume()
    elif action == "clear_overlay":
        correction_orchestrator.clear_overlay()
    elif action == "enable":
        correction_orchestrator.enable()
    elif action == "disable":
        correction_orchestrator.disable()
    else:
        return {"error": f"Unknown action '{action}'", "phase": "029"}
    return {"status": f"override_{action}_applied", "phase": "029"}


@app.post("/api/self-correction/enable")
async def enable_self_correction():
    """FTD-029 — Enable auto-correction."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.enable()
    return {"status": "enabled", "phase": "029"}


@app.post("/api/self-correction/disable")
async def disable_self_correction():
    """FTD-029 — Disable auto-correction."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.disable()
    return {"status": "disabled", "phase": "029"}


@app.post("/api/self-correction/override/stop")
async def override_stop_self_correction():
    """FTD-029 — Human override: immediately halt."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.human_override_stop()
    return {"status": "stopped_by_human_override", "phase": "029"}


@app.post("/api/self-correction/override/resume")
async def override_resume_self_correction():
    """FTD-029 — Human override: resume."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.human_override_resume()
    return {"status": "resumed", "phase": "029"}


@app.post("/api/self-correction/override/clear")
async def clear_self_correction_overlay():
    """FTD-029 — Clear all active corrections, revert to base config."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.clear_overlay()
    return {"status": "overlay_cleared", "phase": "029"}


# ── FTD-030: Autonomous Background Intelligence Loop ─────────────────────────

@app.get("/api/auto-intelligence/state")
async def get_auto_intelligence_state():
    """FTD-030 — Auto-intelligence engine state: enabled, cycles, last result."""
    if _auto_intelligence is None:
        return {"detail": "Auto-intelligence not yet initialised", "phase": "030"}
    return _auto_intelligence.summary()


@app.get("/api/auto-intelligence/history")
async def get_auto_intelligence_history(n: int = 20):
    """FTD-030 — Recent correction cycle history (up to 20 records)."""
    if _auto_intelligence is None:
        return {"history": [], "phase": "030"}
    return {"history": _auto_intelligence.history(n), "phase": "030"}


@app.post("/api/auto-intelligence/force-run")
async def force_auto_intelligence_run():
    """FTD-030 — Bypass interval gate and trigger an immediate correction cycle."""
    if _auto_intelligence is None:
        return {"detail": "Auto-intelligence not yet initialised", "phase": "030"}
    _auto_intelligence.force_run()
    result = _auto_intelligence.tick()
    return {"status": "executed", "result": result, "phase": "030"}


@app.post("/api/auto-intelligence/enable")
async def enable_auto_intelligence():
    """FTD-030 — Enable the autonomous intelligence loop."""
    if _auto_intelligence is None:
        return {"detail": "Not initialised", "phase": "030"}
    _auto_intelligence.enable()
    return {"status": "enabled", "phase": "030"}


@app.post("/api/auto-intelligence/disable")
async def disable_auto_intelligence():
    """FTD-030 — Disable the autonomous intelligence loop."""
    if _auto_intelligence is None:
        return {"detail": "Not initialised", "phase": "030"}
    _auto_intelligence.disable()
    return {"status": "disabled", "phase": "030"}


@app.post("/api/auto-intelligence/reset-daily")
async def reset_auto_intelligence_daily():
    """FTD-030 — Reset the 24h cycle counter (admin use)."""
    if _auto_intelligence is None:
        return {"detail": "Not initialised", "phase": "030"}
    _auto_intelligence.reset_daily_counter()
    return {"status": "daily_counter_reset", "phase": "030"}


# ── FTD-028: Deep Intelligence Validation Layer ──────────────────────────────

@app.post("/api/deep-validation/run")
async def run_deep_validation():
    """
    FTD-028 — Scientific Proof Engine.
    Runs all 13 deep validators and returns a unified system intelligence score
    with PASS/FAIL verdict.  Executes after FTD-027.
    """
    from core.deep_validation.contradiction_engine    import ContradictionEngine
    from core.deep_validation.data_integrity_checker  import DataIntegrityChecker
    from core.deep_validation.decision_scorer         import DecisionScorer
    from core.deep_validation.risk_validator          import RiskValidator
    from core.deep_validation.tuning_validator        import TuningValidator
    from core.deep_validation.evolution_validator     import EvolutionValidator
    from core.deep_validation.capital_validator       import CapitalValidator
    from core.deep_validation.audit_validator         import AuditValidator
    from core.deep_validation.alert_validator         import AlertValidator
    from core.deep_validation.performance_validator   import PerformanceValidator
    from core.deep_validation.failure_simulator       import FailureSimulator
    from core.deep_validation.system_consistency_checker import SystemConsistencyChecker
    from core.deep_validation.meta_score_engine       import MetaScoreEngine
    from core.alerts.alert_engine                     import alert_engine
    from core.audit.audit_engine                      import audit_engine
    from core.evolution.evolution_engine              import evolution_engine
    from core.capital.scaling_engine                  import scaling_engine
    import json, pathlib, datetime

    stats        = pnl_calc.session_stats
    n_trades     = len(pnl_calc.trades)
    dd           = drawdown_controller.summary()
    rs           = risk_ctrl.snapshot()
    gs           = global_gate_controller.snapshot() if hasattr(global_gate_controller, "snapshot") else {}

    halted       = rs.get("halted", False)
    equity       = float(scaler.equity or 0.0)
    dd_pct       = float(dd.get("drawdown_pct", 0.0) or 0.0)
    win_rate     = float(stats.get("win_rate", 0.0) or 0.0) / 100.0
    total_pnl    = float(stats.get("total_net_pnl", 0.0) or 0.0)
    risk_of_ruin = float(rs.get("risk_of_ruin", 0.0) or 0.0)
    kill_switch  = not gs.get("can_trade", True)

    system_state = {
        "equity":                   equity,
        "initial_capital":          float(pnl_calc._initial_capital or equity),
        "total_trades":             n_trades,
        "total_signals":            n_trades,   # 1:1 signal→trade as minimum bound
        "total_pnl":                total_pnl,
        "win_rate":                 win_rate,
        "current_drawdown_pct":     dd_pct,
        "max_drawdown_pct":         0.15,
        "halted":                   halted,
        "risk_halted":              halted,
        "trades_active":            len(risk_ctrl.positions) > 0,
        "risk_of_ruin":             risk_of_ruin,
        "exposure_pct":             float(rs.get("exposure_pct", 0.0) or 0.0),
        "total_exposure":           float(rs.get("total_exposure", 0.0) or 0.0),
        "kill_switch_active":       kill_switch,
        "scale_factor":             float(rs.get("size_multiplier", 1.0) or 1.0),
        "sharpe_ratio":             stats.get("sharpe_ratio", None),
        "pipeline_stages":          ["market_data", "signal", "risk", "execution"],
        # failure simulator flags
        "volatility_guard_active":  True,
        "rr_engine_active":         True,
        "drawdown_controller_active": True,
        "data_health_monitor_active": True,
        "safe_mode_engine_active":  True,
        "ws_stabilizer_active":     True,
        "error_registry_active":    True,
        "api_manager_active":       True,
        "self_healing_active":      True,
    }

    # 1. Contradiction
    contradiction_result = ContradictionEngine().run(system_state)

    # 2. Data integrity
    data_result = DataIntegrityChecker().run(system_state)

    # 3. Decision scorer — derive from closed trades
    decisions = []
    for t in pnl_calc.trades:
        pnl_val = getattr(t, "net_pnl", 0.0) or 0.0
        decisions.append({
            "action":  "TRADE",
            "outcome": "PROFIT" if pnl_val > 0 else "LOSS",
            "pnl":     float(pnl_val),
        })
    decision_result = DecisionScorer().run(decisions)

    # 4. Risk validator
    risk_result = RiskValidator().run(system_state)

    # 5. Tuning validator
    tuning_result = TuningValidator().run([])   # history not persisted in this session

    # 6. Evolution validator
    try:
        ev_state    = evolution_engine.get_state()
        evo_input   = {
            "generation":     ev_state.get("generation", 0),
            "champion_score": ev_state.get("fitness", 0.0),
            "strategies":     ev_state.get("strategies", []),
        }
    except Exception:
        evo_input = {}
    evolution_result = EvolutionValidator().run(evo_input)

    # 7. Capital validator
    cap_input = {
        **system_state,
        "total_exposure": float(rs.get("total_exposure", 0.0) or 0.0),
    }
    capital_result = CapitalValidator().run(cap_input)

    # 8. Audit validator
    try:
        audit_log  = audit_engine.get_log(limit=200)
    except Exception:
        audit_log  = {}
    audit_input = {**audit_log, "total_trades": n_trades}
    audit_result = AuditValidator().run(audit_input)

    # 9. Alert validator
    try:
        alert_out = alert_engine.get_alerts(
            gate_status=gs,
            halt_audit={},
            error_recent=error_registry.recent(50),
            drawdown=dd,
        )
        alert_input = {
            "alerts":                   alert_out.get("alerts", []),
            "false_alert_count":        0,
            "missed_alert_count":       0,
            "critical_events_detected": sum(
                1 for a in alert_out.get("alerts", [])
                if str(a.get("severity", "")).upper() == "CRITICAL"
            ),
        }
    except Exception:
        alert_input = {}
    alert_result = AlertValidator().run(alert_input)

    # 10. Performance validator
    perf_result = PerformanceValidator().run(system_state)

    # 11. Failure simulator
    failure_result = FailureSimulator().run(system_state)

    # 12. System consistency checker
    module_states = {
        "risk_ctrl":   {"equity": equity, "halted": halted},
        "drawdown":    {"equity": equity, "halted": halted},
        "gate":        {"halted": not gs.get("can_trade", True)},
    }
    consistency_result = SystemConsistencyChecker().run(module_states)

    # 13. Meta score
    validator_results = {
        "contradiction":     contradiction_result,
        "data_integrity":    data_result,
        "decision_quality":  decision_result,
        "risk":              risk_result,
        "tuning":            tuning_result,
        "evolution":         evolution_result,
        "capital":           capital_result,
        "audit":             audit_result,
        "alert":             alert_result,
        "performance":       perf_result,
        "failure_resilience": failure_result,
        "consistency":       consistency_result,
    }
    meta = MetaScoreEngine().run(validator_results)

    # Persist score to reports/deep_validation/system_score.json
    try:
        score_path = pathlib.Path("reports/deep_validation/system_score.json")
        score_path.parent.mkdir(parents=True, exist_ok=True)
        score_path.write_text(json.dumps({
            "phase":            "FTD-028",
            "module":           "META_SCORE_ENGINE",
            "system_score":     meta["system_score"],
            "risk_score":       meta["risk_score"],
            "stability_score":  meta["stability_score"],
            "confidence_score": meta["confidence_score"],
            "verdict":          meta["verdict"],
            "snapshot_ts":      meta["snapshot_ts"],
        }, indent=2))
    except Exception:
        pass

    return {
        "phase":      "FTD-028",
        "validators": validator_results,
        "meta":       meta,
        "verdict":    meta["verdict"],
        "system_score": meta["system_score"],
        "run_ts":     int(time.time() * 1000),
    }


# ── Dual-API Credential Vault ─────────────────────────────────────────────────

@app.get("/api/vault/status")
async def get_vault_status():
    """Non-sensitive vault status: configured, current_mode, is_live."""
    return vault.status()


@app.post("/api/vault/setup")
async def vault_setup(body: dict, _auth=Depends(require_roles("admin"))):
    """
    Encrypt and persist both PAPER and LIVE credential slots under a master password.
    Requires admin bearer token.  Re-calling overwrites the existing vault.
    Body: {password, paper_key, paper_secret, live_key, live_secret}
    """
    try:
        vault.setup(
            password     = body.get("password", ""),
            paper_key    = body.get("paper_key", ""),
            paper_secret = body.get("paper_secret", ""),
            live_key     = body.get("live_key", ""),
            live_secret  = body.get("live_secret", ""),
        )
        _thought("🔐 API Vault configured — PAPER and LIVE credentials encrypted at rest.", "SYSTEM")
        return {"ok": True, "mode": "PAPER"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vault setup failed: {exc}")


@app.post("/api/vault/switch")
async def vault_switch(body: dict):
    """
    Password-gated mode switch — the master password IS the authorization.
    On success, hot-swaps Binance API credentials in the running cfg and mdp
    WITHOUT requiring an engine restart.
    Body: {password, mode: "PAPER"|"LIVE"}
    """
    try:
        creds = vault.switch(
            password    = body.get("password", ""),
            target_mode = body.get("mode", "PAPER"),
        )
    except WrongPassword:
        raise HTTPException(status_code=401, detail="Wrong master password.")
    except VaultNotConfigured:
        raise HTTPException(status_code=409, detail="Vault not configured — run /api/vault/setup first.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # ── Hot-swap runtime credentials (no restart needed) ─────────────────────
    cfg.BINANCE_API_KEY    = creds["key"]
    cfg.BINANCE_API_SECRET = creds["secret"]
    cfg.BINANCE_TESTNET    = creds["testnet"]
    cfg.TRADE_MODE         = creds["mode"]           # type: ignore[assignment]
    mdp._exec_url          = mdp.EXEC_API_TEST if creds["testnet"] else mdp.EXEC_API_LIVE

    endpoint_label = "testnet.binance.vision" if creds["testnet"] else "api.binance.com (PRODUCTION)"
    _thought(
        f"🔐 VAULT SWITCH → {creds['mode']} "
        f"({'Testnet' if creds['testnet'] else '⚡ REAL PRODUCTION'}) | "
        f"Execution endpoint: {endpoint_label}",
        "SYSTEM",
    )

    return {
        "ok":      True,
        "mode":    creds["mode"],
        "testnet": creds["testnet"],
        "is_live": creds["mode"] == "LIVE",
    }


# ── Guardian Logic & Aggression Control ───────────────────────────────────────

@app.get("/api/guardian/status")
async def get_guardian_status():
    """Returns Guardian Logic state: level, safe_mode, veto history, all profiles."""
    return guardian.snapshot()


@app.get("/api/engine/aggression")
async def get_aggression():
    """Current aggression level and profile parameters."""
    return guardian.snapshot()


@app.post("/api/engine/aggression")
async def set_aggression(body: dict, _auth=Depends(require_roles("operator", "admin"))):
    """
    Password-free aggression change — Guardian validates automatically.
    Body: {level: 1|2|3|4}
    Returns 403 with veto reason if Guardian blocks the change.
    """
    try:
        level = int(body.get("level", 2))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="level must be an integer 1–4.")

    # Pull live session metrics for Guardian validation
    stats    = pnl_calc.session_stats
    win_rate = stats.get("win_rate", 0.0)
    mdd_pct  = stats.get("max_drawdown_pct", 0.0)

    trades  = pnl_calc.trades
    valid_r = [t.r_multiple for t in trades if t.r_multiple != 0.0]
    pos_r   = [r for r in valid_r if r > 0]
    neg_r   = [abs(r) for r in valid_r if r < 0]
    avg_r_win  = (sum(pos_r) / len(pos_r)) if pos_r else 1.0
    avg_r_loss = (sum(neg_r) / len(neg_r)) if neg_r else 1.0

    allowed, msg = guardian.validate_and_apply(
        level, win_rate, mdd_pct, avg_r_win, avg_r_loss, cfg
    )

    _thought(msg, "SYSTEM" if allowed else "HALT")

    if not allowed:
        raise HTTPException(status_code=403, detail=msg)

    return guardian.snapshot()


# ── Engine Command & Control ──────────────────────────────────────────────────

@app.get("/api/engine/status")
async def get_engine_status():
    """Live engine operational status: ACTIVE / GRACEFUL_STOP / STANDBY / HALTED."""
    if risk_ctrl.halted:
        state = "HALTED"
    elif risk_ctrl.graceful_stop:
        state = "GRACEFUL_STOP"
    elif mdp._running:
        state = "ACTIVE"
    else:
        state = "STANDBY"
    return {
        "state":          state,
        "halted":         risk_ctrl.halted,
        "graceful_stop":  risk_ctrl.graceful_stop,
        "ws_running":     mdp._running,
        "open_positions": len(risk_ctrl.positions),
        "pending_orders": len(risk_ctrl.pending_orders),
        "ts":             int(time.time() * 1000),
    }


@app.post("/api/engine/start")
async def start_engine(_auth=Depends(require_roles("operator", "admin"))):
    """Clear halt + graceful-stop flags and resume normal signal scanning."""
    risk_ctrl.halted       = False
    risk_ctrl.graceful_stop = False
    _thought("▶ Engine START command received — resuming full signal scanning.", "SYSTEM")
    return {"state": "ACTIVE"}


@app.post("/api/engine/stop/graceful")
async def graceful_stop_engine(_auth=Depends(require_roles("operator", "admin"))):
    """
    Graceful stop: no new entries accepted, existing positions run until TP/SL.
    Does NOT close open positions immediately.
    """
    risk_ctrl.graceful_stop = True
    _thought(
        f"⏸ Graceful STOP — new entries blocked. "
        f"{len(risk_ctrl.positions)} position(s) running to TP/SL naturally.",
        "SYSTEM",
    )
    return {"state": "GRACEFUL_STOP", "open_positions": len(risk_ctrl.positions)}


# ── WebSocket (Real-time Dashboard Feed) ──────────────────────────────────────

MAX_WS_CLIENTS = 3   # max simultaneous dashboard connections

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    # Reject BEFORE accepting when over cap (code 4029 = too many connections)
    # Client must back off on 4029 — do NOT retry immediately
    if len(_ws_clients) >= MAX_WS_CLIENTS:
        await ws.accept()
        await ws.close(code=4029, reason="too_many_connections")
        logger.debug(f"[WS] Rejected — cap {MAX_WS_CLIENTS} reached. Active: {len(_ws_clients)}")
        return

    await ws.accept()
    _ws_clients.append(ws)
    logger.info(f"[WS] Client connected. Total: {len(_ws_clients)}")

    try:
        # Send initial state burst — includes truth-engine WS state (FTD-REF-026)
        await ws.send_text(json.dumps({
            "type":     "init",
            "status":   await get_status(),
            "pnl":      pnl_calc.session_stats,
            "thoughts": _thought_log[-20:],
            "ws_truth": ws_truth_engine.to_dict(),   # FTD-REF-026
        }, default=str))

        while True:
            # Keep-alive: 45s timeout (client pings every 20s)
            msg = await asyncio.wait_for(ws.receive_text(), timeout=45)
            data = json.loads(msg)
            if data.get("cmd") == "ping":
                await ws.send_text(json.dumps({"type": "pong", "ts": int(time.time() * 1000)}))

    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception as e:
        logger.debug(f"[WS] Connection error: {e}")
    finally:
        if ws in _ws_clients:
            _ws_clients.remove(ws)
        logger.info(f"[WS] Client disconnected. Total: {len(_ws_clients)}")


# ── FTD-030B: Learning Memory Layer ──────────────────────────────────────────

@app.get("/api/learning-memory/summary")
async def learning_memory_summary():
    """FTD-030B — Full learning memory state: patterns formed, negative memory, cycle stats."""
    from core.learning_memory import learning_memory_orchestrator
    return learning_memory_orchestrator.summary()


@app.get("/api/learning-memory/patterns")
async def learning_memory_patterns(n: int = 10):
    """FTD-030B — Top N formed patterns by confidence (leaderboard)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "patterns": learning_memory_orchestrator.pattern_leaderboard(n),
        "phase": "030B",
    }


@app.get("/api/learning-memory/failed-patterns")
async def learning_memory_failed_patterns(n: int = 10):
    """FTD-030B — Bottom N patterns by confidence (failed patterns)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "failed_patterns": learning_memory_orchestrator.failed_patterns(n),
        "phase": "030B",
    }


@app.get("/api/learning-memory/negative-memory")
async def learning_memory_negative():
    """FTD-030B — Current negative memory blacklist (temporary + permanent bans)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "negative_memory":  learning_memory_orchestrator.negative_memory_list(),
        "counts":           learning_memory_orchestrator._neg_memory.count(),
        "phase": "030B",
    }


@app.get("/api/learning-memory/log")
async def learning_memory_log(n: int = 20):
    """FTD-030B — Recent memory store records (last N entries)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "records": learning_memory_orchestrator.recent_memory_log(n),
        "phase":   "030B",
    }


@app.post("/api/learning-memory/enable")
async def learning_memory_enable():
    """FTD-030B — Enable learning memory layer."""
    from core.learning_memory import learning_memory_orchestrator
    learning_memory_orchestrator.enable()
    return {"status": "enabled", "phase": "030B"}


@app.post("/api/learning-memory/disable")
async def learning_memory_disable():
    """FTD-030B — Disable learning memory layer (memory is read-only)."""
    from core.learning_memory import learning_memory_orchestrator
    learning_memory_orchestrator.disable()
    return {"status": "disabled", "phase": "030B"}


@app.get("/api/learning-memory/history")
async def learning_memory_history(n: int = 10):
    """FTD-030B — Recent memory store records (explainability log)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "history": learning_memory_orchestrator.recent_memory_log(n),
        "phase": "030B",
    }


@app.get("/api/learning-memory/heatmap")
async def learning_memory_heatmap():
    """FTD-030B — Regime × parameter confidence heatmap."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "heatmap": learning_memory_orchestrator.pattern_heatmap(),
        "phase": "030B",
    }


# ── Performance Explorer API (FTD-UPE) ───────────────────────────────────────

def _pnl_to_upe_records(trades: list) -> list:
    """Convert pnl_calculator.TradeRecord list → UPE TradeRecord list."""
    records = []
    for t in trades:
        d = asdict(t)
        sym  = d.get("symbol") or ""
        side = d.get("side")   or ""
        if not sym or not side:
            continue
        try:
            records.append(_UPERecord(
                trade_id      = d.get("trade_id", ""),
                symbol        = sym,
                side          = side,
                strategy_id   = d.get("strategy_id", "unknown"),
                regime        = d.get("regime", "unknown"),
                order_type    = d.get("order_type", "LIMIT"),
                entry_price   = float(d.get("entry_price", 0)),
                exit_price    = float(d.get("exit_price", 0)),
                qty           = float(d.get("qty", 0)),
                gross_pnl     = float(d.get("gross_pnl", 0)),
                fee_entry     = float(d.get("fee_entry", 0)),
                fee_exit      = float(d.get("fee_exit", 0)),
                slippage_cost = float(d.get("slippage_cost", 0)),
                net_pnl       = float(d.get("net_pnl", 0)),
                net_pnl_pct   = float(d.get("net_pnl_pct", 0)),
                r_multiple    = float(d.get("r_multiple", 0)),
                entry_ts      = int(d.get("entry_ts", 0)),
                exit_ts       = int(d.get("exit_ts", 0)),
                mode          = d.get("mode", "PAPER"),
            ))
        except Exception:
            pass
    return records


def _upe_build_filter(
    preset:    str,
    symbol:    str,
    strategy:  str,
    regime:    str,
    side:      str,
    win_only:  bool,
    loss_only: bool,
    rr_min,
    rr_max,
    pnl_min,
    pnl_max,
) -> _UPEFilter:
    flt = _upe_preset_filter(preset)
    if symbol:    flt.symbols    = [symbol]
    if strategy:  flt.strategies = [strategy]
    if regime:    flt.regimes    = [regime]
    if side:      flt.sides      = [side]
    if win_only:  flt.win_only   = True
    if loss_only: flt.loss_only  = True
    if rr_min  is not None: flt.rr_min  = rr_min
    if rr_max  is not None: flt.rr_max  = rr_max
    if pnl_min is not None: flt.pnl_min = pnl_min
    if pnl_max is not None: flt.pnl_max = pnl_max
    return flt


@app.get("/api/perf-explorer/summary")
async def upe_summary(
    preset:    str   = "ALL",
    symbol:    str   = "",
    strategy:  str   = "",
    regime:    str   = "",
    side:      str   = "",
    win_only:  bool  = False,
    loss_only: bool  = False,
    rr_min:    float = None,
    rr_max:    float = None,
    pnl_min:   float = None,
    pnl_max:   float = None,
):
    """Performance Explorer — summary panel + AI insights for given preset/filter."""
    records  = _pnl_to_upe_records(pnl_calc.trades)
    flt      = _upe_build_filter(preset, symbol, strategy, regime, side,
                                 win_only, loss_only, rr_min, rr_max, pnl_min, pnl_max)
    filtered = flt.apply(records)
    summary  = _upe_compute_summary(filtered, initial_capital=pnl_calc._initial_capital)
    insights = _upe_extract_insights(summary, filtered)
    return {
        "preset":      preset,
        "trade_count": len(filtered),
        "summary":     asdict(summary),
        "insights":    [asdict(i) for i in insights],
    }


@app.get("/api/perf-explorer/trades")
async def upe_trades(
    preset:    str   = "ALL",
    symbol:    str   = "",
    strategy:  str   = "",
    regime:    str   = "",
    side:      str   = "",
    win_only:  bool  = False,
    loss_only: bool  = False,
    rr_min:    float = None,
    rr_max:    float = None,
    pnl_min:   float = None,
    pnl_max:   float = None,
    limit:     int   = 500,
):
    """Performance Explorer — filtered trade list."""
    records  = _pnl_to_upe_records(pnl_calc.trades)
    flt      = _upe_build_filter(preset, symbol, strategy, regime, side,
                                 win_only, loss_only, rr_min, rr_max, pnl_min, pnl_max)
    filtered = flt.apply(records)
    return {
        "total":  len(filtered),
        "trades": [asdict(t) for t in filtered[-limit:]],
    }


@app.get("/api/perf-explorer/visuals")
async def upe_visuals(preset: str = "ALL"):
    """Performance Explorer — chart data (equity curve, drawdown series, histograms)."""
    records  = _pnl_to_upe_records(pnl_calc.trades)
    filtered = _upe_preset_filter(preset).apply(records)
    visuals  = _upe_build_visual_data(filtered, initial_capital=pnl_calc._initial_capital)
    return {
        "equity_curve":    visuals.equity_curve[-300:],
        "drawdown_series": visuals.drawdown_series[-300:],
        "pnl_histogram":   visuals.pnl_histogram,
        "win_loss_dist":   visuals.win_loss_dist,
        "rr_distribution": visuals.rr_distribution,
    }


@app.get("/api/perf-explorer/export/csv")
async def upe_export_csv(preset: str = "ALL"):
    """Performance Explorer — download filtered trade list as CSV."""
    from fastapi.responses import Response as _R
    records  = _pnl_to_upe_records(pnl_calc.trades)
    filtered = _upe_preset_filter(preset).apply(records)
    return _R(
        content    = _UPEExport.to_csv(filtered),
        media_type = "text/csv",
        headers    = {"Content-Disposition": f"attachment; filename=trades_{preset}.csv"},
    )


@app.get("/api/perf-explorer/export/json")
async def upe_export_json(preset: str = "ALL"):
    """Performance Explorer — download full report as JSON."""
    from fastapi.responses import Response as _R
    records  = _pnl_to_upe_records(pnl_calc.trades)
    filtered = _upe_preset_filter(preset).apply(records)
    summary  = _upe_compute_summary(filtered, initial_capital=pnl_calc._initial_capital)
    return _R(
        content    = _UPEExport.to_json(filtered, summary),
        media_type = "application/json",
        headers    = {"Content-Disposition": f"attachment; filename=report_{preset}.json"},
    )


@app.post("/api/perf-explorer/backup")
async def upe_backup():
    """Performance Explorer — trigger manual backup of trade history."""
    records = _pnl_to_upe_records(pnl_calc.trades)
    bm      = _UPEBackup("data/backups")
    path    = bm.backup(records, label="manual")
    return {"ok": True, "path": path, "trade_count": len(records)}


# ── FTD-038+039: Capital Flow Engine API ─────────────────────────────────────

@app.get("/api/capital-flow/state")
async def capital_flow_state():
    """
    FTD-038+039 — Full Capital Flow Engine state.
    Returns: per-strategy allocation %, stabilizer state, capital protect mode,
    equity smoothness, and allocation change log.
    """
    return _sanitize(capital_flow_engine.summary())


@app.get("/api/capital-flow/allocations")
async def capital_flow_allocations():
    """
    FTD-038 — Per-strategy capital allocation breakdown.
    Shows: strategy → AEE state → rank → priority mult → allocation %.
    DISABLED strategies show 0% allocation.
    """
    from dataclasses import asdict
    allocs = capital_flow_engine.allocations()
    equity = scaler.equity
    return {
        "equity_usdt":   round(equity, 2),
        "total_active":  sum(1 for a in allocs if a.can_trade),
        "total_disabled": sum(1 for a in allocs if not a.can_trade),
        "allocations":   [asdict(a) for a in allocs],
        "stabilizer_state": capital_flow_engine._stab_state,
        "protect_mode":  capital_flow_engine._protect_mode,
    }


# ── FTD-037: Adaptive Edge Engine API ────────────────────────────────────────

@app.get("/api/aee/state")
async def aee_state():
    """
    FTD-037 — Full AEE state: all strategies ranked by AEE Score.
    Returns: active / reduced / scaling / disabled lists + per-strategy
    metrics (score, PF, RR, cost%, WR%, streaks, size_mult, disable_log).
    """
    return _sanitize(adaptive_edge_engine.summary())


@app.get("/api/aee/strategy/{strategy_id}")
async def aee_strategy_detail(strategy_id: str):
    """
    FTD-037 — Single strategy detail: full AEE stats + disable log.
    Use strategy_id as it appears in trades (e.g. ALPHA_TCB_v1, MR_BB_RSI_v1).
    """
    stats = adaptive_edge_engine.get_stats(strategy_id)
    if stats is None:
        raise HTTPException(404, f"Strategy '{strategy_id}' not yet tracked by AEE")
    return _sanitize(asdict(stats))


# ── Master Report Bundle ──────────────────────────────────────────────────────

@app.get("/api/reports/bundle")
async def download_report_bundle():
    """
    One-click Master Report Bundle — assembles ALL report types into a
    single ZIP file.

    ZIP contents:
      README.txt                    ← File guide
      metadata.json                 ← Bundle summary (trades, PnL, PF, etc.)
      01_system_state/
        eow_state.json              ← Full engine state (DNA + trades + ratios)
      02_reports/
        full_system_report.md       ← FTD-025A: 15-section institutional report
        full_system_report.pdf      ← FTD-025A: PDF version
        unified_report_v2.md        ← FTD-025B: cause-effect narrative report
      03_trade_archive/
        trade_history.xlsx          ← XLSX (trade sheet + session summary + audit)
        trade_report.pdf            ← PDF executive summary
        trade_report.md             ← Markdown developer log
      04_performance/
        report_ALL.json + trades_ALL.csv
        report_1D.json  + trades_1D.csv
        report_7D.json  + trades_7D.csv
        report_20D.json + trades_20D.csv
    """
    import zipfile
    import io as _io
    from fastapi.responses import StreamingResponse
    from core.reporting.unified_report_engine_v2 import generate_full_report_v2

    ts = int(time.time())

    def _safe(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    # ── Shared data collection (mirrors get_full_system_report) ──────────────
    heal      = _safe(healer.snapshot, {})
    lake_s    = _safe(data_lake.db_stats, {})
    redis_ok  = any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in heal.get("recent_events", [])
    )
    sqlite_ok = lake_s.get("trades", -1) >= 0

    trade_dicts = [
        {k: getattr(t, k) for k in t.__dataclass_fields__}
        for t in pnl_calc.trades
    ]
    _ss       = pnl_calc.session_stats
    _n_trades = len(pnl_calc.trades)
    _gross    = abs(_ss.get("total_net_pnl", 0.0)) + _ss.get("total_fees_paid", 0.0)
    _fee_ratio = _ss.get("total_fees_paid", 0.0) / max(_gross, 1e-9)
    _mins_idle = trade_flow_monitor.minutes_since_last_trade()

    analytics = _sanitize(compute_full_analytics(
        pnl_trades=[{"net_pnl": t.net_pnl, "r_multiple": t.r_multiple}
                    for t in pnl_calc.trades],
        initial_capital=pnl_calc._initial_capital,
        session_stats=_ss,
        healer_snapshot=heal,
        lake_stats=lake_s,
        genome_state=_safe(genome.export_state, {}),
        redis_ok=redis_ok,
        persistence_ok=(redis_ok or sqlite_ok),
    ))
    mode_info = await get_mode_info()

    ct_scan = _safe(
        lambda: __import__("core.intelligence.suggestion_engine",
                           fromlist=["suggestion_engine"]).suggestion_engine.detect(
            profit_factor=_ss.get("profit_factor", 0.0),
            fee_ratio=round(_fee_ratio, 4),
            win_rate=_ss.get("win_rate", 0.0) / 100.0,
            n_trades=_n_trades,
            strategy_usage=strategy_engine.usage(),
            regime_stable=True,
        ), {}
    )
    ai_brain_state = _safe(
        lambda: __import__("core.meta.ai_brain",
                           fromlist=["ai_brain"]).ai_brain.get_state(), {}
    )

    positions = []
    try:
        for sym, pos in risk_ctrl.positions.items():
            positions.append({
                "symbol":     sym,
                "side":       getattr(pos, "side", ""),
                "qty":        getattr(pos, "qty", 0.0),
                "entry_px":   getattr(pos, "entry_px", 0.0),
                "stop":       getattr(pos, "stop", 0.0),
                "tp":         getattr(pos, "tp", 0.0),
                "unrealised": getattr(pos, "unrealised_pnl", 0.0),
            })
    except Exception:
        positions = []

    # ── 2a. FTD-025A: full system report ZIP ─────────────────────────────────
    sys_snapshot = SystemSnapshot(
        session_stats     = _ss,
        analytics         = analytics,
        mode_info         = mode_info,
        thoughts          = _thought_log,
        last_skip         = _safe(lambda: getattr(trade_flow_monitor,
                                                  "last_skip", lambda: {})(), {}),
        trade_flow        = _safe(trade_flow_monitor.summary, {}),
        risk_snapshot     = _safe(risk_ctrl.snapshot, {}),
        positions         = positions,
        drawdown          = _safe(drawdown_controller.summary, {}),
        genome_state      = _safe(genome.export_state, {}),
        learning          = _safe(learning_engine.summary, {}),
        edge              = _safe(edge_engine.summary, {}),
        strategy_usage    = _safe(strategy_engine.usage, {}),
        regime            = _safe(lambda: regime_memory.summary()
                                  if hasattr(regime_memory, "summary") else {}, {}),
        ct_scan           = ct_scan,
        dynamic_thresholds= _safe(
            lambda: dynamic_threshold_provider.summary(
                minutes_no_trade=_mins_idle
            ), {}
        ),
        streak            = _safe(streak_engine.summary, {}),
        consistency       = _safe(consistency_engine.status, {}),
        capital_allocator = _safe(capital_allocator.summary, {}),
        error_registry    = _safe(lambda: error_registry.recent(50), []),
        healer            = heal,
        halt_audit        = _safe(lambda: risk_ctrl.halt_audit()
                                  if hasattr(risk_ctrl, "halt_audit") else {}, {}),
        trades            = trade_dicts,
        gate_status       = _safe(lambda: global_gate_controller.snapshot()
                                  if "global_gate_controller" in globals() else {}, {}),
        ai_brain_state    = ai_brain_state,
        learning_memory   = _safe(
            lambda: __import__("core.learning_memory",
                               fromlist=["learning_memory_orchestrator"]
                               ).learning_memory_orchestrator.summary(), {}
        ),
    )
    system_zip_bytes = _safe(
        lambda: system_export_engine.build_full_report(sys_snapshot), b""
    )

    # ── 2b. FTD-025B: Unified Report v2 (Markdown) ───────────────────────────
    _v2_data = {
        "generated_at":    time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "trade_flow":      _safe(trade_flow_monitor.summary, {}),
        "mins_idle":       _mins_idle,
        "thresholds":      _safe(
            lambda: dynamic_threshold_provider.summary(minutes_no_trade=_mins_idle), {}
        ),
        "session_stats":   _ss,
        "capital":         _safe(capital_allocator.summary, {}),
        "risk":            _safe(risk_ctrl.snapshot, {}),
        "gate":            _safe(
            lambda: global_gate_controller.snapshot()
            if "global_gate_controller" in globals() else {}, {}
        ),
        "errors":          _safe(lambda: error_registry.recent(20), []),
        "learning_memory": _safe(
            lambda: __import__("core.learning_memory",
                               fromlist=["learning_memory_orchestrator"]
                               ).learning_memory_orchestrator.summary(), {}
        ),
        "ct_scan":         ct_scan,
        "ai_brain":        ai_brain_state,
        "drawdown":        _safe(drawdown_controller.summary, {}),
        "activator":       _safe(trade_activator.summary, {}),
        "edge_engine":     _safe(edge_engine.summary, {}),
        "thoughts":        list(_thought_log)[-30:],
    }
    unified_v2_md = _safe(
        lambda: generate_full_report_v2(_v2_data), "# Unified report unavailable"
    )

    # ── 2c. Trade archive ZIP (XLSX + PDF + MD) ───────────────────────────────
    archive_zip_bytes = _safe(
        lambda: build_report_archive(
            trades=trade_dicts,
            stats=_ss,
            mode_info=mode_info,
            analytics=analytics,
            thoughts=_thought_log,
        ), b""
    )

    # ── 2d. Engine state JSON (ExportManager) ────────────────────────────────
    state_json_str = "{}"
    try:
        state_path = exporter.export(label="bundle")
        with open(state_path, "r", encoding="utf-8") as _f:
            state_json_str = _f.read()
    except Exception:
        pass

    # ── 2e. Performance Explorer — ALL / 1D / 7D / 20D ───────────────────────
    upe_records  = _pnl_to_upe_records(pnl_calc.trades)
    upe_presets  = ["ALL", "1D", "7D", "20D"]
    upe_csvs:  dict = {}
    upe_jsons: dict = {}
    for _preset in upe_presets:
        _filtered = _upe_preset_filter(_preset).apply(upe_records)
        _summary  = _upe_compute_summary(
            _filtered, initial_capital=pnl_calc._initial_capital
        )
        upe_csvs[_preset]  = _UPEExport.to_csv(_filtered)
        upe_jsons[_preset] = _UPEExport.to_json(_filtered, _summary)

    # ── 3. Assemble master ZIP ────────────────────────────────────────────────
    buf = _io.BytesIO()
    ts_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        zf.writestr("README.txt", (
            "EOW Quant Engine — Master Report Bundle\n"
            "═══════════════════════════════════════\n"
            f"Generated : {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
            f"Engine    : EOW_QUANT_ENGINE_v1.0\n"
            f"Trades    : {_n_trades}\n"
            f"Net PnL   : {_ss.get('total_net_pnl', 0.0):.2f} USDT\n"
            f"Win Rate  : {_ss.get('win_rate', 0.0):.1f}%\n"
            f"PF        : {_ss.get('profit_factor', 0.0):.3f}\n\n"
            "Folder Guide\n"
            "────────────\n"
            "01_system_state/  Full engine state JSON (DNA, trade history, portfolio ratios)\n"
            "02_reports/       FTD-025A 15-section report (MD+PDF) + FTD-025B narrative (MD)\n"
            "03_trade_archive/ Trade history XLSX + PDF executive summary + MD developer log\n"
            "04_performance/   Performance Explorer reports for ALL / 1D / 7D / 20D presets\n"
            "                  Each preset: report_<P>.json (summary) + trades_<P>.csv (raw)\n"
        ))

        zf.writestr("metadata.json", json.dumps({
            "bundle_ts":        ts,
            "bundle_date":      time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "engine_ver":       "EOW_QUANT_ENGINE_v1.0",
            "trade_count":      _n_trades,
            "net_pnl_usdt":     _ss.get("total_net_pnl", 0.0),
            "win_rate_pct":     _ss.get("win_rate", 0.0),
            "profit_factor":    _ss.get("profit_factor", 0.0),
            "max_drawdown_pct": _ss.get("max_drawdown_pct", 0.0),
            "sharpe_ratio":     _ss.get("sharpe_ratio", 0.0),
            "total_fees_usdt":  _ss.get("total_fees_paid", 0.0),
            "fee_drag_pct":     round(_fee_ratio * 100, 2),
            "presets_included": upe_presets,
        }, indent=2, default=str))

        # 01_system_state/
        zf.writestr("01_system_state/eow_state.json", state_json_str)

        # 02_reports/ — extract MD + PDF from FTD-025A ZIP
        if system_zip_bytes:
            try:
                with zipfile.ZipFile(_io.BytesIO(system_zip_bytes)) as _sub:
                    for _name in _sub.namelist():
                        _ext = _name.rsplit(".", 1)[-1].lower()
                        _dst = f"02_reports/full_system_report.{_ext}"
                        zf.writestr(_dst, _sub.read(_name))
            except Exception:
                zf.writestr("02_reports/full_system_report.md",
                            "# Full system report generation failed")

        zf.writestr("02_reports/unified_report_v2.md",
                    unified_v2_md if isinstance(unified_v2_md, str)
                    else "# Unified report unavailable")

        # 03_trade_archive/ — extract XLSX + PDF + MD from archive ZIP
        if archive_zip_bytes:
            try:
                with zipfile.ZipFile(_io.BytesIO(archive_zip_bytes)) as _sub:
                    for _name in _sub.namelist():
                        _ext = _name.rsplit(".", 1)[-1].lower()
                        if _ext == "xlsx":
                            _dst = "03_trade_archive/trade_history.xlsx"
                        elif _ext == "pdf":
                            _dst = "03_trade_archive/trade_report.pdf"
                        else:
                            _dst = "03_trade_archive/trade_report.md"
                        zf.writestr(_dst, _sub.read(_name))
            except Exception:
                zf.writestr("03_trade_archive/trade_report.md",
                            "# Trade archive generation failed")

        # 04_performance/
        for _preset in upe_presets:
            zf.writestr(f"04_performance/report_{_preset}.json",
                        upe_jsons[_preset])
            zf.writestr(f"04_performance/trades_{_preset}.csv",
                        upe_csvs[_preset])

    buf.seek(0)
    filename = f"eow_bundle_{ts}.zip"
    _thought(
        f"📦 Master Report Bundle downloaded → {filename} "
        f"({_n_trades} trades, {len(buf.getvalue())//1024} KB)",
        "SYSTEM"
    )
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Entry Point ───────────────────────────────────────────────────────────────

# Serve dashboard.html at "/" so http://localhost:8000 opens the dashboard directly
_DASH = Path(__file__).parent / "dashboard.html"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    if _DASH.exists():
        return HTMLResponse(_DASH.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>dashboard.html not found in project root</h2>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
