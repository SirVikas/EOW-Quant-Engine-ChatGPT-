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
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from loguru import logger
import orjson

from config import cfg
from core.market_data    import MarketDataProvider, Tick
from core.pnl_calculator import PurePnLCalculator, TradeRecord
from core.genome_engine  import GenomeEngine
from core.regime_detector import RegimeDetector
from core.risk_controller import RiskController, OpenPosition
from core.self_healing    import SelfHealingProtocol
from core.data_lake       import DataLake
from utils.capital_scaler import CapitalScaler
from utils.export_manager import ExportManager
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
        _ws_clients.discard(ws)


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
    if sym not in risk_ctrl.positions and not risk_ctrl.halted:

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
            )
            if not edge_ok:
                _thought(
                    f"⛔ Skip {sym}: weak edge gross={edge.get('gross_tp', 0):.3f} "
                    f"cost={edge.get('cost', 0):.3f} net={edge.get('net_if_tp', 0):.3f} "
                    f"RR={edge.get('rr', 0):.2f} RR_net={edge.get('rr_after_cost', 0):.2f} "
                    f"RR_req={edge.get('required_r', 0):.2f} ATR%={edge.get('current_volatility', 0):.2f}",
                    "FILTER",
                )
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

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    mdp.register_callback(on_tick)
    _thought("🚀 EOW Quant Engine booting…", "SYSTEM")
    _thought(f"Mode: {cfg.TRADE_MODE} | Capital: {cfg.INITIAL_CAPITAL} USDT", "SYSTEM")

    tasks = [
        asyncio.create_task(mdp.start()),
        asyncio.create_task(genome.start()),
        asyncio.create_task(healer.start()),
        asyncio.create_task(data_lake.start()),
    ]
    _thought("All subsystems online. Scanning markets…", "SYSTEM")
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
    allow_origins=["*"],
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


# ── Mode Toggle ───────────────────────────────────────────────────────────────

@app.post("/api/mode/{mode}")
async def set_mode(mode: str):
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
async def import_dna_endpoint(body: dict):
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
async def emergency_close():
    prices = {sym: tick.price for sym, tick in mdp.ticks.items()}
    risk_ctrl.emergency_close_all(prices)
    _thought("🚨 EMERGENCY CLOSE ALL triggered", "HALT")
    return {"closed": len(prices)}


@app.post("/api/resume")
async def resume_engine():
    risk_ctrl.halted = False
    _thought("✅ Engine manually resumed", "SYSTEM")
    return {"halted": False}


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
