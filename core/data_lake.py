"""
EOW Quant Engine — Data Lake
Persists every tick, closed candle, and funding rate to SQLite
(production: swap _db_path to TimescaleDB via asyncpg).
Acts as the "Big Data" store for Genome Engine backtests.
"""
from __future__ import annotations
import asyncio
import json
import os
import sqlite3
import time
from dataclasses import asdict
from typing import List, Optional
from loguru import logger

from config import cfg


class DataLake:
    """
    Lightweight async-friendly SQLite wrapper.
    All writes are batched and flushed every FLUSH_INTERVAL seconds
    to avoid hammering the disk on every tick.

    Schema
    ──────
    candles  (symbol, interval, open, high, low, close, volume, ts)
    ticks    (symbol, price, bid, ask, volume, ts)
    funding  (symbol, rate, next_funding_ts, ts)
    trades   (trade JSON blob)
    """

    FLUSH_INTERVAL = 10   # seconds between batch writes
    DB_PATH = "data/eow_lake.db"

    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._tick_buf:   List[tuple] = []
        self._candle_buf: List[tuple] = []
        self._funding_buf:List[tuple] = []
        self._running = False

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def start(self):
        self._conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        self._running = True
        logger.info(f"[LAKE] SQLite data lake open → {self.DB_PATH}")
        await self._flush_loop()

    async def stop(self):
        self._running = False
        self._flush_all()
        if self._conn:
            self._conn.close()
        logger.info("[LAKE] Data lake closed.")

    # ── Ingestion API ────────────────────────────────────────────────────────

    def ingest_tick(self, symbol: str, price: float, bid: float,
                    ask: float, volume: float, ts: int):
        self._tick_buf.append((symbol, price, bid, ask, volume, ts))

    def ingest_candle(self, symbol: str, interval: str,
                      o: float, h: float, l: float, c: float,
                      vol: float, ts: int):
        self._candle_buf.append((symbol, interval, o, h, l, c, vol, ts))

    def ingest_funding(self, symbol: str, rate: float, next_ts: int):
        self._funding_buf.append((symbol, rate, next_ts, int(time.time() * 1000)))

    def save_trade(self, trade_dict: dict):
        """Persist a completed TradeRecord as a JSON blob."""
        if not self._conn:
            return
        self._conn.execute(
            "INSERT OR IGNORE INTO trades(trade_id, symbol, data, ts) VALUES(?,?,?,?)",
            (trade_dict.get("trade_id"), trade_dict.get("symbol"),
             json.dumps(trade_dict, default=str),
             trade_dict.get("exit_ts", int(time.time() * 1000))),
        )
        self._conn.commit()

    # ── Query API ────────────────────────────────────────────────────────────

    def get_candles(
        self,
        symbol: str,
        interval: str = "1m",
        limit:  int = 1440,
        since_ts: int = 0,
    ) -> List[dict]:
        """Return up to `limit` closed candles for a symbol."""
        if not self._conn:
            return []
        cur = self._conn.execute(
            """SELECT open,high,low,close,volume,ts
               FROM candles WHERE symbol=? AND interval=? AND ts>?
               ORDER BY ts DESC LIMIT ?""",
            (symbol, interval, since_ts, limit),
        )
        rows = cur.fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_trades(self, symbol: str = "", limit: int = 500) -> List[dict]:
        if not self._conn:
            return []
        if symbol:
            cur = self._conn.execute(
                "SELECT data FROM trades WHERE symbol=? ORDER BY ts DESC LIMIT ?",
                (symbol, limit),
            )
        else:
            cur = self._conn.execute(
                "SELECT data FROM trades ORDER BY ts DESC LIMIT ?", (limit,)
            )
        return [json.loads(r["data"]) for r in cur.fetchall()]

    def db_stats(self) -> dict:
        if not self._conn:
            return {}
        stats = {}
        for tbl in ("ticks", "candles", "funding", "trades"):
            cur = self._conn.execute(f"SELECT COUNT(*) as n FROM {tbl}")
            stats[tbl] = cur.fetchone()["n"]
        size_mb = os.path.getsize(self.DB_PATH) / 1024 / 1024
        stats["db_size_mb"] = round(size_mb, 3)
        return stats

    # ── Internal ─────────────────────────────────────────────────────────────

    def _create_tables(self):
        ddl = [
            """CREATE TABLE IF NOT EXISTS candles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, interval TEXT,
                open REAL, high REAL, low REAL, close REAL, volume REAL,
                ts INTEGER,
                UNIQUE(symbol, interval, ts)
            )""",
            """CREATE TABLE IF NOT EXISTS ticks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, price REAL, bid REAL, ask REAL, volume REAL, ts INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS funding(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, rate REAL, next_funding_ts INTEGER, ts INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS trades(
                trade_id TEXT PRIMARY KEY,
                symbol TEXT, data TEXT, ts INTEGER
            )""",
            "CREATE INDEX IF NOT EXISTS idx_candles_sym_ts ON candles(symbol, ts)",
            "CREATE INDEX IF NOT EXISTS idx_ticks_sym_ts  ON ticks(symbol, ts)",
            "CREATE INDEX IF NOT EXISTS idx_trades_sym    ON trades(symbol)",
        ]
        for stmt in ddl:
            self._conn.execute(stmt)
        self._conn.commit()

    async def _flush_loop(self):
        while self._running:
            await asyncio.sleep(self.FLUSH_INTERVAL)
            self._flush_all()

    def _flush_all(self):
        if not self._conn:
            return
        try:
            if self._candle_buf:
                self._conn.executemany(
                    """INSERT OR IGNORE INTO candles
                       (symbol,interval,open,high,low,close,volume,ts)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    self._candle_buf,
                )
                self._candle_buf.clear()

            # Keep only last 2000 ticks per symbol (rolling)
            if self._tick_buf:
                self._conn.executemany(
                    "INSERT INTO ticks(symbol,price,bid,ask,volume,ts) VALUES(?,?,?,?,?,?)",
                    self._tick_buf,
                )
                self._tick_buf.clear()
                self._conn.execute(
                    """DELETE FROM ticks WHERE id NOT IN (
                        SELECT id FROM ticks ORDER BY ts DESC LIMIT 60000)"""
                )

            if self._funding_buf:
                self._conn.executemany(
                    "INSERT INTO funding(symbol,rate,next_funding_ts,ts) VALUES(?,?,?,?)",
                    self._funding_buf,
                )
                self._funding_buf.clear()

            self._conn.commit()
        except Exception as exc:
            logger.warning(f"[LAKE] Flush error: {exc}")
