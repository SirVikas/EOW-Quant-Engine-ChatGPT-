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
from core.indicator_guard import indicator_guard
from core.regime_ai       import regime_ai
from core.signal_filter   import signal_filter
from core.risk_engine     import risk_engine
from core.deployability   import deployability_engine
from core.trade_frequency    import trade_frequency      # FTD-REF-023
from core.execution_engine  import execution_engine     # FTD-REF-023
from core.learning_engine   import learning_engine      # FTD-REF-023
from core.edge_engine        import edge_engine         # FTD-REF-024
from core.market_structure   import market_structure_detector  # FTD-REF-024
from core.ws_truth_engine    import ws_truth_engine     # FTD-REF-025
from core.error_registry     import error_registry      # FTD-REF-025
from core.strategy_engine    import strategy_engine     # FTD-REF-026
from core.profit_guard       import profit_guard        # FTD-REF-026
from core.ct_scan_engine     import ct_scan_engine      # FTD-REF-026
from core.exchange.api_manager  import api_manager
from core.bootstrap.api_loader  import api_loader
from core.infra_health_manager import InfraHealthManager
from utils.capital_scaler import CapitalScaler
from utils.export_manager import ExportManager
from utils.report_generator import build_report_archive
from strategies.strategy_modules import get_strategy, Signal


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

# FTD-REF-019: store boot diagnostics for /api/boot-status
_boot_status: dict = {}
_engine_running: bool = False

# ── Trade Throttle Controls ───────────────────────────────────────────────────
# After any trade on a symbol, wait this long before allowing another entry.
SYMBOL_COOLDOWN_SEC = 1800        # 30 minutes per symbol
MAX_TRADES_PER_HOUR = 12          # absolute cap across all symbols

_last_trade_ts: dict = {}         # symbol → last trade close timestamp (ms)
_trades_this_hour: list = []      # timestamps of recent trade opens
_last_symbol_eval_ms: dict = {}   # symbol → last strategy evaluation ts
_last_processed_candle_ts: dict = {}  # symbol → last closed candle ts evaluated
SYMBOL_EVAL_DEBOUNCE_MS = 750     # throttle heavy signal path per symbol

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
    global _last_skip   # must be declared before any assignment in this function
    sym   = tick.symbol
    price = tick.price

    # Guard: reject malformed symbols that somehow bypass _is_valid_symbol
    if len(sym) < 5 or not sym.endswith("USDT"):
        return

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
            # FTD-REF-026: track strategy usage distribution
            _closed_strat_type = {
                "TRENDING":             "TrendFollowing",
                "MEAN_REVERTING":       "MeanReversion",
                "VOLATILITY_EXPANSION": "VolatilityExpansion",
            }.get(_trade_regime, "TrendFollowing")
            strategy_engine.record_trade(_closed_strat_type)
        _last_trade_ts[sym] = int(time.time() * 1000)  # cooldown starts on close

    # MASTER-001: keep risk engine equity up to date
    risk_engine.update_equity(scaler.equity)

    # 2. Get candle data for strategy
    candle = mdp.latest_closed_candle(sym)
    if not candle:
        # Startup warmup: until first closed candle lands, skip silently.
        return

    # Evaluate each symbol once per freshly closed candle to avoid
    # repeatedly rejecting open candles between kline close events.
    if _last_processed_candle_ts.get(sym) == candle.ts:
        return
    _last_processed_candle_ts[sym] = candle.ts

    buf     = list(mdp.price_buffer(sym))
    data_gate = strategy_engine.evaluate_data_sufficiency(len(buf))
    if data_gate != "OK":
        error_registry.log("DATA_001", symbol=sym, extra=f"buf={len(buf)}")  # FTD-REF-025
        _last_skip = {
            "ts": int(time.time() * 1000), "symbol": sym,
            "reason": f"{data_gate}({len(buf)})",
        }
        return

    # 2b. Performance debounce: avoid repeated heavy regime/signal passes
    # for the same symbol within sub-second windows.
    prev_eval = _last_symbol_eval_ms.get(sym, 0)
    now_ms = int(time.time() * 1000)
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

        closes = buf
        highs  = [p * 1.001 for p in buf]
        lows   = [p * 0.999 for p in buf]

        # FTD-REF-019: validate indicator quality before generating signal
        # NOTE: regime_det.state().atr_pct is 0 for single-price ticks (high=low=close),
        # so we compute atr_pct from the close buffer BEFORE calling indicator_guard.
        r_state  = regime_det.state(sym)
        atr_pct  = _estimate_atr_pct(closes)
        raw_adx  = getattr(r_state, "adx", 0.0)
        adx_val  = raw_adx if (raw_adx > 0 or len(buf) >= 28) else None
        guard    = indicator_guard.validate(
            symbol=sym, n_candles=len(buf), adx=adx_val, atr_pct=atr_pct,
        )
        if not guard.ok:
            error_registry.log("DATA_002", symbol=sym, extra=guard.reason)  # FTD-REF-025
            return   # insufficient candles / unstable ADX / near-zero ATR

        # MASTER-001: risk engine gate (daily loss / trade cap / drawdown halt)
        risk_allowed, risk_reason = risk_engine.check_new_trade()
        if not risk_allowed:
            return   # daily risk limit reached

        # FTD-REF-024: market structure gate (LOW_VOL_TRAP / FAKE_BREAKOUT block)
        _bb_width = getattr(r_state, "bb_width", 0.0)
        ms_result = market_structure_detector.detect(
            adx=guard.adx, bb_width=_bb_width, atr_pct=guard.atr_pct,
        )
        if not ms_result.tradeable:
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": ms_result.block_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return

        # FTD-REF-024: edge engine kill switch
        edge_allowed, edge_reason = edge_engine.check_trade(regime.value, strategy_type)
        if not edge_allowed:
            error_registry.log("STRAT_002", symbol=sym, extra=edge_reason)  # FTD-REF-025
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": edge_reason, "regime": regime.value,
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
        if r_ai.block_trade:
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
        _pf_stats = pnl_calc.session_stats
        _consecutive_losses = 0
        for _t in reversed(pnl_calc.trades):
            if _t.net_pnl < 0:
                _consecutive_losses += 1
            else:
                break
        _pg_hard_stop, _pg_hard_reason = profit_guard.hard_stop_required(
            profit_factor=_pf_stats.get("profit_factor", 1.0),
            n_trades=len(pnl_calc.trades),
            consecutive_losses=_consecutive_losses,
        )
        if _pg_hard_stop:
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": _pg_hard_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return

        _pf_mult  = profit_guard.frequency_multiplier(
            profit_factor=_pf_stats.get("profit_factor", 1.0),
            n_trades=len(pnl_calc.trades),
        )
        _adjusted_conf = round(r_ai.confidence * _regime_weight * _pf_mult, 3)

        sig = strategy.generate_signal(sym, closes, highs, lows)
        if sig and sig.signal != Signal.NONE:
            _thought(f"🔔 Signal {sig.signal.value} {sym} | {sig.reason}", "SIGNAL")

            # 6. Size the position (FTD-REF-024: apply edge booster multiplier)
            sizing = scaler.compute(sym, sig.entry_price, sig.stop_loss)
            if sizing.qty <= 0:
                return
            _edge_mult = edge_engine.get_size_multiplier(regime.value, strategy_type)
            sizing.qty = sizing.qty * _edge_mult   # boost qty on strong positive edge
            # atr_pct already computed above from close buffer (not regime_det tick ATR)

            # FTD-REF-023: realistic cost via execution_engine
            notional  = sizing.qty * sig.entry_price
            cost_usdt = execution_engine.fee_for_notional(notional) * 2

            # FTD-REF-024: fee-aware gate — reject if TP profit can't cover fees
            _gross_tp = abs(sig.take_profit - sig.entry_price) * sizing.qty
            _fee_reject, _fee_reason = execution_engine.should_reject_for_fees(
                expected_gross_profit=_gross_tp, notional=notional,
            )
            if _fee_reject:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _fee_reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                return

            # FTD-REF-026: profit guard fee-ratio check (fees > 20% of gross TP)
            _pg_block, _pg_reason = profit_guard.check_fee_ratio(
                gross_tp_profit=_gross_tp, fee_cost=cost_usdt,
            )
            if _pg_block:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _pg_reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                return

            # FTD-REF-024: get current edge for signal filter gate
            _expected_edge = edge_engine.get_edge(regime.value, strategy_type)

            # MASTER-001 + FTD-REF-023 + FTD-REF-024: adaptive signal quality filter
            sf_result = signal_filter.check(
                symbol=sym, entry=sig.entry_price,
                take_profit=sig.take_profit, stop_loss=sig.stop_loss,
                cost_usdt=cost_usdt, atr_pct=atr_pct,
                confidence=_adjusted_conf,
                regime=r_ai.regime.value,
                relaxation_factor=relax_factor,
                expected_edge=_expected_edge,
            )
            if not sf_result.ok:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": sf_result.reason, "rr": sf_result.rr,
                    "confidence": r_ai.confidence, "regime": regime.value,
                    "strategy": strategy_type,
                }
                return

            # FTD-REDIS-017: hard strategy quality gate (RR/confidence/regime)
            strat_gate = strategy_engine.evaluate_signal(
                rr=sf_result.rr,
                confidence=_adjusted_conf,
                regime=("UNSTABLE" if r_ai.block_trade else r_ai.regime.value),
            )
            if not strat_gate.ok:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": strat_gate.reason, "rr": sf_result.rr,
                    "confidence": _adjusted_conf, "regime": regime.value,
                    "strategy": strategy_type,
                }
                return

            edge_ok, edge = risk_ctrl.get_trade_decision(
                side=sig.signal.value,
                entry=sig.entry_price,
                take_profit=sig.take_profit,
                stop_loss=sig.stop_loss,
                qty=sizing.qty,
                current_volatility=atr_pct,
                regime=regime.value,   # Fix B: regime-specific RR threshold
            )
            if not edge_ok:
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

            # 7. Open position — use Limit Order when enabled (saves fees + slippage)
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

    global _engine_running
    _engine_running = True
    ensure_auth_ready_for_mode()
    mdp.register_callback(on_tick)
    _thought("🚀 EOW Quant Engine booting…", "SYSTEM")
    _thought(f"Mode: {cfg.TRADE_MODE} | Capital: {cfg.INITIAL_CAPITAL} USDT", "SYSTEM")

    # ── Fix A: Reload promoted DNA so genome doesn't reset on restart ─────────
    genome.load_persisted_dna()
    required_strategies = {"TrendFollowing", "MeanReversion", "VolatilityExpansion"}
    missing = [s for s in required_strategies if not genome.active_dna.get(s)]
    if missing:
        raise RuntimeError(f"DNA validation failed before engine start: missing={missing}")

    # ── MASTER-001: Initialise risk engine with current equity ───────────────
    risk_engine.initialize(cfg.INITIAL_CAPITAL)

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
    ]

    # ── Fix D: Restore previous session's trade history from DataLake ─────────
    # Give the data_lake task a moment to open the SQLite connection.
    await asyncio.sleep(0.5)
    try:
        historical_trades = data_lake.get_trades(limit=5000)
        if historical_trades:
            n = pnl_calc.replay_from_history(historical_trades)
            # Sync risk_engine and scaler equity after replay so RoR/sizing use real capital
            replayed_equity = pnl_calc.session_stats.get("capital", pnl_calc.capital)
            risk_engine.update_equity(replayed_equity)
            scaler.equity = replayed_equity
            _thought(
                f"📂 Session restored: {n} trades replayed from DataLake. "
                f"Equity: {replayed_equity:.2f} USDT",
                "SYSTEM",
            )
        else:
            _thought("📂 No prior trade history found — starting fresh.", "SYSTEM")
    except Exception as exc:
        _thought(f"⚠️ Session restore failed: {exc} — starting fresh.", "SYSTEM")

    _thought("All subsystems online. Scanning markets…", "SYSTEM")

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
