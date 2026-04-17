"""
EOW Quant Engine — MarketDataProvider
Step 1: WebSocket multi-currency stream from Binance.
Publishes tick data to Redis pub/sub for all consumers.
"""
import asyncio
import json
import random
import time
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable, Any
from loguru import logger
import websockets
import httpx
import redis.asyncio as aioredis

from config import cfg
from core.candle_bootstrap import CandleBootstrapper
from core.redis_client import get_async_redis


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Tick:
    symbol:     str
    price:      float
    qty:        float
    bid:        float
    ask:        float
    volume_24h: float
    ts:         int          # epoch ms


@dataclass
class Candle:
    symbol:   str
    interval: str
    open:     float
    high:     float
    low:      float
    close:    float
    volume:   float
    ts:       int
    closed:   bool = False


@dataclass
class OrderBook:
    symbol: str
    bids:   List[List[float]] = field(default_factory=list)   # [[price, qty],…]
    asks:   List[List[float]] = field(default_factory=list)
    ts:     int = 0


@dataclass
class FundingRate:
    symbol:       str
    rate:         float
    next_funding: int    # epoch ms


# ── MarketDataProvider ────────────────────────────────────────────────────────

class MarketDataProvider:
    """
    Async WebSocket client that streams real-time market data from Binance.
    Maintains an in-memory registry of latest ticks, candles, and order books.
    Broadcasts everything to Redis channels so other modules can subscribe.
    """

    # Market data is PUBLIC — always use real Binance, no auth needed.
    # BINANCE_TESTNET only affects order EXECUTION (placing real trades).
    BASE_WS  = "wss://stream.binance.com:9443/stream?streams="
    BASE_API = "https://api.binance.com"
    EXEC_API_LIVE = "https://api.binance.com"
    EXEC_API_TEST = "https://testnet.binance.vision"

    def __init__(self):
        self.symbols:      List[str]              = []
        self.ticks:        Dict[str, Tick]        = {}
        self.candles:      Dict[str, Candle]      = {}
        self.closed_candles: Dict[str, Candle]    = {}
        self.order_books:  Dict[str, OrderBook]   = {}
        self.funding:      Dict[str, FundingRate] = {}

        # Rolling 500-tick buffers per symbol (for fast indicators)
        self.tick_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))

        self._redis:          Optional[aioredis.Redis] = None
        self._ws:             Optional[Any]            = None
        self._running:        bool                     = False
        self._callbacks:      List[Callable]           = []
        self._last_ws_error:  Optional[str]            = None

        # Market data always uses real Binance public endpoints (no API key needed)
        self._ws_url  = self.BASE_WS
        self._api_url = self.BASE_API
        # Execution URL: testnet only when BINANCE_TESTNET=true
        self._exec_url = self.EXEC_API_TEST if cfg.BINANCE_TESTNET else self.EXEC_API_LIVE
        self._candle_bootstrap = CandleBootstrapper(self._api_url)
        logger.info(
            f"[MDP] Streams → real Binance (public) | "
            f"Execution → {'TESTNET' if cfg.BINANCE_TESTNET else 'LIVE'}"
        )

    # ── Public API ──────────────────────────────────────────────────────────

    async def start(self):
        """Discover top-N pairs then open the combined WebSocket stream."""
        # Redis is optional, but we only fall back to in-memory mode
        # after 3 failed retries to avoid transient startup false negatives.
        self._redis = await self._connect_redis_with_retries(retries=3)
        if self._redis is not None:
            logger.info("[MDP] Redis connected — pub/sub active.")
        else:
            logger.info(
                "[MDP] Redis unavailable after 3 retries — "
                "running in-memory only. Engine will auto-reconnect if Redis starts later."
            )
        self.symbols = await self._discover_symbols()
        logger.info(f"[MDP] Watching {len(self.symbols)} symbols: {self.symbols[:5]}…")
        await self._candle_bootstrap.warmup(self, self.symbols)
        self._running = True
        await asyncio.gather(
            self._stream_loop(),
            self._funding_rate_loop(),
            self._redis_reconnect_loop(),
        )

    async def stop(self):
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._redis:
            await self._redis.aclose()
        logger.info("[MDP] Stopped.")

    def register_callback(self, fn: Callable):
        """Register a coroutine to be called on every new tick."""
        self._callbacks.append(fn)

    def latest_tick(self, symbol: str) -> Optional[Tick]:
        return self.ticks.get(symbol)

    def latest_candle(self, symbol: str) -> Optional[Candle]:
        return self.candles.get(symbol)

    def latest_closed_candle(self, symbol: str) -> Optional[Candle]:
        return self.closed_candles.get(symbol)

    def price_buffer(self, symbol: str) -> deque:
        return self.tick_buffers[symbol]

    def redis_connected(self) -> bool:
        """True when Redis pub/sub client is active."""
        return self._redis is not None

    def websocket_state(self) -> str:
        """Runtime websocket state for health endpoints."""
        ws = self._ws
        if not self._running:
            return "STOPPED"
        if ws is None:
            return "CONNECTING"
        if getattr(ws, "closed", False):
            return "RECONNECTING"
        return "CONNECTED"

    # ── Symbol Discovery ────────────────────────────────────────────────────

    # Fallback top pairs used when API call fails or returns too few symbols
    FALLBACK_PAIRS = [
        "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
        "DOGEUSDT","ADAUSDT","AVAXUSDT","DOTUSDT","LINKUSDT",
        "MATICUSDT","LTCUSDT","UNIUSDT","ATOMUSDT","NEARUSDT",
        "APTUSDT","OPUSDT","ARBUSDT","INJUSDT","SUIUSDT",
    ]

    # Stablecoins and pegged assets — never trade these
    BLOCKED_PAIRS = {
        # Stablecoins & pegged assets
        "USDCUSDT", "BUSDUSDT", "TUSDUSDT", "USDPUSDT", "FDUSDUSDT",
        "USD1USDT", "PAXGUSDT", "DAIUSDT", "FRAXUSDT", "GUSDUSDT",
        "USTCUSDT", "EURUSDT", "GBPUSDT", "AEURUSDT", "BRLLUSDT",
        # Meme/high-risk coins
        "PEPEUSDT", "SHIBUSDT", "FLOKIUSDT", "BONKUSDT", "WIFUSDT",
        "DOGEUSDT", "BOMEUSDT", "MEMEUSDT",
        # Consistently losing — low liquidity / high spread
        "TAOUSDT", "ZECUSDT", "ENJUSDT", "XAUTUSDT",
        # TP too tight relative to costs — never profitable
        "STOUSDT",
        # Ripple RLUSD stablecoin — pegged to USD, no directional edge
        "RLUSDUSDT",
    }

    async def _discover_symbols(self) -> List[str]:
        """Fetch top-N USDT pairs by 24h quote volume. Falls back to hardcoded list."""
        try:
            async with httpx.AsyncClient(
                base_url=self._api_url, timeout=10.0
            ) as client:
                resp = await client.get("/api/v3/ticker/24hr")
                resp.raise_for_status()
                tickers = resp.json()

            usdt = [
                t for t in tickers
                if self._is_valid_symbol(t.get("symbol", ""))
                and float(t.get("quoteVolume", 0)) >= cfg.MIN_VOLUME_USDT
            ]
            usdt.sort(key=lambda t: float(t["quoteVolume"]), reverse=True)
            result = [t["symbol"] for t in usdt[: cfg.TOP_N_PAIRS]]

            if len(result) < 5:
                # Volume filter too strict (e.g. quiet market) — relax it
                logger.warning(
                    f"[MDP] Only {len(result)} pairs passed volume filter "
                    f"(>{cfg.MIN_VOLUME_USDT/1e6:.0f}M). Relaxing filter..."
                )
                usdt_all = [t for t in tickers if self._is_valid_symbol(t.get("symbol", ""))]
                usdt_all.sort(key=lambda t: float(t.get("quoteVolume", 0)), reverse=True)
                result = [t["symbol"] for t in usdt_all[: cfg.TOP_N_PAIRS]]

            if not result:
                raise ValueError("Empty symbol list from API")

            return result

        except Exception as exc:
            logger.warning(
                f"[MDP] Symbol discovery failed ({exc}). "
                f"Using fallback top-{len(self.FALLBACK_PAIRS)} pairs."
            )
            clean = [p for p in self.FALLBACK_PAIRS if self._is_valid_symbol(p)]
            return clean[: cfg.TOP_N_PAIRS]

    @staticmethod
    def _is_valid_symbol(symbol: str) -> bool:
        if not symbol or not symbol.endswith("USDT"):
            return False
        if not symbol.isascii():
            return False
        if not re.fullmatch(r"[A-Z0-9]{5,20}", symbol):
            return False
        if symbol in MarketDataProvider.BLOCKED_PAIRS:
            return False
        return True

    # ── WebSocket Stream ────────────────────────────────────────────────────

    def _build_streams(self) -> str:
        streams = []
        for sym in self.symbols:
            s = sym.lower()
            streams += [
                f"{s}@bookTicker",      # best bid/ask
                f"{s}@aggTrade",        # aggregate trades (tick)
                f"{s}@kline_1m",        # 1-min candles
            ]
        return "/".join(streams)

    async def _stream_loop(self):
        url = self._ws_url + self._build_streams()
        backoff = 1
        while self._running:
            try:
                async with websockets.connect(
                    url,
                    # Binance combined-stream server responds to WebSocket protocol
                    # PINGs with close code 1011 (internal error) instead of PONG,
                    # triggering spurious reconnects every ~30 s.  Disable the
                    # websockets library's built-in keepalive; the self-healing
                    # protocol and Binance's own stream management handle liveness.
                    ping_interval=None,
                    close_timeout=10,
                ) as ws:
                    self._ws = ws
                    self._last_ws_error = None
                    backoff = 1   # reset on successful connect
                    logger.info("[MDP] WebSocket connected.")
                    async for raw in ws:
                        if not self._running:
                            break
                        await self._dispatch(json.loads(raw))
            except (ConnectionResetError, OSError) as exc:
                # WinError 10054 (Windows WSAECONNRESET) / Errno 104 (Linux ECONNRESET):
                # Binance dropped the TCP connection — not a local bug, reconnect quietly.
                win_err = getattr(exc, "winerror", None)
                err_no  = getattr(exc, "errno", None)
                if win_err == 10054 or err_no == 104:
                    self._last_ws_error = f"CONN_RESET (winerror={win_err}, errno={err_no})"
                    logger.debug(
                        f"[MDP] Remote host reset connection (WinError {win_err}/Errno {err_no}). "
                        "Reconnecting — this is a Binance-side or network-level RST, not a local bug."
                    )
                else:
                    self._last_ws_error = str(exc)
                    logger.warning(f"[MDP] WS OSError: {exc}. Reconnecting…")
                jitter = random.uniform(0, backoff * 0.3)
                delay  = backoff + jitter
                await asyncio.sleep(delay)
                backoff = min(backoff * 2, 60)
            except Exception as exc:
                # Fix C: exponential backoff with ±30% jitter prevents
                # thundering-herd reconnects after a mass-disconnect event.
                self._last_ws_error = str(exc)
                jitter = random.uniform(0, backoff * 0.3)
                delay  = backoff + jitter
                msg = str(exc)
                # Expected during intentional close/reconnect races on some platforms.
                if "sent 1000 (OK); no close frame received" in msg:
                    logger.debug(
                        f"[MDP] WS close-race during reconnect: {msg}. "
                        f"Retrying in {delay:.1f}s (backoff={backoff}s)…"
                    )
                else:
                    logger.warning(
                        f"[MDP] WS error: {msg}. "
                        f"Reconnecting in {delay:.1f}s (backoff={backoff}s)…"
                    )
                await asyncio.sleep(delay)
                backoff = min(backoff * 2, 60)

    async def _connect_redis_with_retries(self, retries: int = 3) -> Optional[aioredis.Redis]:
        for attempt in range(1, max(1, retries) + 1):
            try:
                r = get_async_redis(timeout=5.0)
                await r.ping()
                return r
            except Exception as exc:
                if attempt >= retries:
                    logger.debug(f"[MDP] Redis connect failed: {type(exc).__name__}")
                await asyncio.sleep(0.2 * attempt)
        return None

    async def _redis_reconnect_loop(self):
        """
        Background task: silently retry Redis connection every 60 s when not connected.
        If the operator starts Redis after engine launch, it will be picked up here
        without any restart — pub/sub activates automatically.
        """
        while self._running:
            await asyncio.sleep(60)
            if self._redis is not None:
                continue   # already connected
            r = await self._connect_redis_with_retries(retries=1)
            if r is not None:
                self._redis = r
                logger.info("[MDP] Redis reconnected — pub/sub now active.")

    async def reconnect(self):
        """
        Fix C: Force-close the active WebSocket so _stream_loop reconnects.
        Called by SelfHealingProtocol when ticks become stale.
        """
        ws = getattr(self, "_ws", None)
        if ws is not None:
            try:
                await ws.close()
                logger.info("[MDP] Forced reconnect triggered by self-healing.")
            except Exception:
                pass   # already closed — ignore

    async def _dispatch(self, msg: dict):
        stream = msg.get("stream", "")
        data   = msg.get("data", msg)
        event  = data.get("e", "")

        if event == "aggTrade":
            await self._handle_trade(data)
        elif event == "bookTicker" or "b" in data and "a" in data and "s" in data:
            await self._handle_book_ticker(data)
        elif event == "kline":
            await self._handle_kline(data)

    async def _handle_trade(self, d: dict):
        sym   = d["s"]
        price = float(d["p"])
        qty   = float(d["q"])
        ts    = int(d["T"])

        tick = Tick(
            symbol=sym, price=price, qty=qty,
            bid=self.ticks.get(sym, Tick(sym, price, 0, price, price, 0, ts)).bid,
            ask=self.ticks.get(sym, Tick(sym, price, 0, price, price, 0, ts)).ask,
            volume_24h=0, ts=ts,
        )
        self.ticks[sym] = tick
        self.tick_buffers[sym].append(price)

        # Publish to Redis
        await self._publish("ticks", asdict(tick))

        # Fire callbacks
        for cb in self._callbacks:
            asyncio.create_task(cb(tick))

    async def _handle_book_ticker(self, d: dict):
        sym = d["s"]
        if sym in self.ticks:
            self.ticks[sym].bid = float(d["b"])
            self.ticks[sym].ask = float(d["a"])
        self.order_books[sym] = OrderBook(
            symbol=sym,
            bids=[[float(d["b"]), float(d["B"])]],
            asks=[[float(d["a"]), float(d["A"])]],
            ts=int(time.time() * 1000),
        )
        await self._publish("order_books", {"symbol": sym, "bid": d["b"], "ask": d["a"]})

    async def _handle_kline(self, d: dict):
        k   = d["k"]
        sym = k["s"]
        candle = Candle(
            symbol=sym, interval=k["i"],
            open=float(k["o"]), high=float(k["h"]),
            low=float(k["l"]),  close=float(k["c"]),
            volume=float(k["v"]), ts=int(k["t"]),
            closed=k["x"],
        )
        self.candles[sym] = candle
        if candle.closed:
            self.closed_candles[sym] = candle
            await self._publish("closed_candles", asdict(candle))

    # ── Funding Rate Loop ───────────────────────────────────────────────────

    async def _funding_rate_loop(self):
        """Poll premium/funding rates every 5 minutes."""
        while self._running:
            try:
                async with httpx.AsyncClient(base_url=self._api_url) as client:
                    resp = await client.get("/fapi/v1/premiumIndex")
                    if resp.status_code == 200:
                        for item in resp.json():
                            sym = item.get("symbol", "")
                            if sym in self.symbols:
                                self.funding[sym] = FundingRate(
                                    symbol=sym,
                                    rate=float(item.get("lastFundingRate", 0)),
                                    next_funding=int(item.get("nextFundingTime", 0)),
                                )
            except Exception as exc:
                logger.debug(f"[MDP] Funding rate fetch skipped: {exc}")
            await asyncio.sleep(300)

    # ── Redis Publish ───────────────────────────────────────────────────────

    async def _publish(self, channel: str, data: dict):
        if self._redis:
            try:
                await self._redis.publish(f"eow:{channel}", json.dumps(data))
            except Exception:
                pass

    # ── Snapshot (for API responses) ────────────────────────────────────────

    def snapshot(self) -> dict:
        return {
            "symbols": self.symbols,
            "ticks": {s: asdict(t) for s, t in self.ticks.items()},
            "candles": {s: asdict(c) for s, c in self.candles.items()},
            "funding": {s: asdict(f) for s, f in self.funding.items()},
            "ts": int(time.time() * 1000),
        }
