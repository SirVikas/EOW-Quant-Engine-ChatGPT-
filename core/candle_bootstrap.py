"""Bootstrap recent candles so indicators are warm at startup."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger


class CandleBootstrapper:
    """
    Fetches recent 1m candles for selected symbols.

    Why this exists:
    - cold boot starts with empty per-symbol buffers
    - strategy engine may emit DATA_001 (insufficient data) for the first minutes
    - preloading closes gives indicators immediate context
    """

    def __init__(self, base_url: str, *, lookback: int = 120, concurrency: int = 8):
        self.base_url = base_url
        self.lookback = max(30, int(lookback))
        self.concurrency = max(1, int(concurrency))

    async def warmup(self, market_data: Any, symbols: list[str], regime_detector=None) -> None:
        if not symbols:
            return

        timeout = httpx.Timeout(10.0, connect=5.0)
        sem = asyncio.Semaphore(self.concurrency)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=timeout) as client:
            tasks = [self._warm_symbol(client, sem, market_data, sym, regime_detector) for sym in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        ok = sum(1 for r in results if r is True)
        fail = sum(1 for r in results if r is False or isinstance(r, Exception))
        logger.info(
            f"[MDP] Candle warmup complete — seeded {ok}/{len(symbols)} symbols "
            f"(failed={fail})."
        )

    async def _warm_symbol(self, client: httpx.AsyncClient, sem: asyncio.Semaphore, market_data: Any, symbol: str, regime_detector=None) -> bool:
        async with sem:
            try:
                resp = await client.get(
                    "/api/v3/klines",
                    params={"symbol": symbol, "interval": "1m", "limit": self.lookback},
                )
                resp.raise_for_status()
                rows = resp.json()
                if not rows:
                    return False

                for row in rows:
                    close_price = float(row[4])
                    high_price  = float(row[2])
                    low_price   = float(row[3])
                    volume      = float(row[5])
                    market_data.tick_buffers[symbol].append(close_price)
                    # Seed OHLC + volume buffers for accurate ATR and sleep-mode baseline from boot.
                    market_data.candle_close_buffers[symbol].append(close_price)
                    market_data.candle_high_buffers[symbol].append(high_price)
                    market_data.candle_low_buffers[symbol].append(low_price)
                    market_data.candle_volume_buffers[symbol].append(volume)
                    # Pre-seed regime_detector with historical OHLC so indicators are
                    # warm from boot (avoids 28-minute regime warmup blackout per session).
                    if regime_detector is not None:
                        try:
                            regime_detector.push(
                                symbol,
                                close_price,
                                high_price,
                                low_price,
                                int(row[0]),     # ts
                            )
                        except Exception:
                            pass

                last = rows[-1]
                candle = {
                    "symbol": symbol,
                    "interval": "1m",
                    "open": float(last[1]),
                    "high": float(last[2]),
                    "low": float(last[3]),
                    "close": float(last[4]),
                    "volume": float(last[5]),
                    "ts": int(last[0]),
                    "closed": True,
                }
                # write through canonical Candle dataclass via existing constructor path
                from core.market_data import Candle  # local import avoids cycle at module load

                c = Candle(**candle)
                market_data.candles[symbol] = c
                market_data.closed_candles[symbol] = c

                # Seed latest tick approximation from last close (bid/ask same at bootstrap)
                from core.market_data import Tick

                market_data.ticks[symbol] = Tick(
                    symbol=symbol,
                    price=float(last[4]),
                    qty=0.0,
                    bid=float(last[4]),
                    ask=float(last[4]),
                    volume_24h=0.0,
                    ts=int(last[6]),
                )
                return True
            except Exception as exc:
                logger.debug(f"[MDP] Warmup skipped for {symbol}: {exc}")
                return False
