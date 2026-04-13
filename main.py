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
from core.analytics       import compute_full_analytics
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

# ── Trade Throttle Controls ───────────────────────────────────────────────────
# After any trade on a symbol, wait this long before allowing another entry.
SYMBOL_COOLDOWN_SEC = 1800        # 30 minutes per symbol
MAX_TRADES_PER_HOUR = 12          # absolute cap across all symbols

_last_trade_ts: dict = {}         # symbol → last trade close timestamp (ms)
_trades_this_hour: list = []      # timestamps of recent trade opens

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
    sym   = tick.symbol
    price = tick.price

    # 1. Update risk controller (SL/TP checks)
    action = risk_ctrl.on_price_update(sym, price)
    if action:
        _thought(f"Position closed [{action}] {sym} @ {price}", "TRADE")
        if pnl_calc.trades:
            data_lake.save_trade(asdict(pnl_calc.trades[-1]))
        _last_trade_ts[sym] = int(time.time() * 1000)  # cooldown starts on close

    # 2. Get candle data for strategy
    candle = mdp.latest_candle(sym)
    if not candle or not candle.closed:
        return   # Only act on closed candles

    buf     = list(mdp.price_buffer(sym))
    if len(buf) < 50:
        return

    # 3. Detect regime
    regime_det.push(sym, candle.close, candle.high, candle.low, candle.ts)
    regime = regime_det.get(sym)

    # 4. Get appropriate strategy — skip if warmup incomplete
    if regime.value == "UNKNOWN":
        return   # need 28+ candles before trading

    strategy_type = {
        "TRENDING":             "TrendFollowing",
        "MEAN_REVERTING":       "MeanReversion",
        "VOLATILITY_EXPANSION": "VolatilityExpansion",
    }.get(regime.value, "TrendFollowing")

    dna      = genome.active_dna.get(strategy_type, {})
    strategy = get_strategy(regime, dna)

    # 5. Generate signal (only if no open position + throttle checks)
    now_ms = int(time.time() * 1000)
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

        sig = strategy.generate_signal(sym, closes, highs, lows)
        if sig and sig.signal != Signal.NONE:
            _thought(f"🔔 Signal {sig.signal.value} {sym} | {sig.reason}", "SIGNAL")

            # 6. Size the position
            sizing = scaler.compute(sym, sig.entry_price, sig.stop_loss)
            if sizing.qty <= 0:
                return
            atr_pct = _estimate_atr_pct(closes)
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
                global _last_skip
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

    ensure_auth_ready_for_mode()
    mdp.register_callback(on_tick)
    _thought("🚀 EOW Quant Engine booting…", "SYSTEM")
    _thought(f"Mode: {cfg.TRADE_MODE} | Capital: {cfg.INITIAL_CAPITAL} USDT", "SYSTEM")

    # ── Fix A: Reload promoted DNA so genome doesn't reset on restart ─────────
    genome.load_persisted_dna()

    # ── Start all subsystems ──────────────────────────────────────────────────
    tasks = [
        asyncio.create_task(mdp.start()),
        asyncio.create_task(genome.start()),
        asyncio.create_task(healer.start()),
        asyncio.create_task(data_lake.start()),
    ]

    # ── Fix D: Restore previous session's trade history from DataLake ─────────
    # Give the data_lake task a moment to open the SQLite connection.
    await asyncio.sleep(0.5)
    try:
        historical_trades = data_lake.get_trades(limit=5000)
        if historical_trades:
            n = pnl_calc.replay_from_history(historical_trades)
            _thought(
                f"📂 Session restored: {n} trades replayed from DataLake. "
                f"Equity: {pnl_calc.capital:.2f} USDT",
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
    for t in tasks:
        t.cancel()
    await mdp.stop()
    await genome.stop()
    await healer.stop()
    await data_lake.stop()


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
        {"net_pnl": t.net_pnl, "r_multiple": t.r_multiple}
        for t in pnl_calc.trades
    ]

    return _sanitize(compute_full_analytics(
        pnl_trades=trade_dicts,
        initial_capital=pnl_calc._initial_capital,
        session_stats=pnl_calc.session_stats,
        healer_snapshot=heal,
        lake_stats=lake_s,
        genome_state=genome.export_state(),
        redis_ok=redis_ok,
        persistence_ok=persistence_ok,
    ))


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
        # Send initial state burst
        await ws.send_text(json.dumps({
            "type":   "init",
            "status": await get_status(),
            "pnl":    pnl_calc.session_stats,
            "thoughts": _thought_log[-20:],
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
