"""
FTD-AIL-001: History Store — immutable approval/rejection history.
Records are append-only; no updates ever.
"""
from __future__ import annotations
import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_DB_PATH = Path(__file__).parents[4] / "data" / "ail" / "history.db"


def _conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(_DB_PATH))
    con.row_factory = sqlite3.Row
    return con


def _init_db() -> None:
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                lineage_id  TEXT NOT NULL,
                action      TEXT NOT NULL,
                reason      TEXT,
                actor       TEXT DEFAULT 'human',
                ts          TEXT NOT NULL
            )
        """)


async def record(lineage_id: str, action: str, reason: str = "") -> None:
    def _rec():
        _init_db()
        with _conn() as con:
            con.execute(
                "INSERT INTO history (lineage_id, action, reason, ts) VALUES (?,?,?,?)",
                (lineage_id, action, reason, datetime.now(timezone.utc).isoformat()),
            )
    await asyncio.to_thread(_rec)


async def get_history(limit: int = 100) -> list[dict]:
    def _get():
        _init_db()
        with _conn() as con:
            rows = con.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
    return await asyncio.to_thread(_get)
