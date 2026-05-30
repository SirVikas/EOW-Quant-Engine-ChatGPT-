"""
FTD-AIL-001: Findings Store — SQLite-backed findings queue.
All SQLite ops use asyncio.to_thread for non-blocking I/O.
"""
from __future__ import annotations
import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).parents[4] / "data" / "ail" / "findings.db"


def _conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(_DB_PATH))
    con.row_factory = sqlite3.Row
    return con


def _init_db() -> None:
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                lineage_id       TEXT PRIMARY KEY,
                title            TEXT,
                category         TEXT,
                severity         TEXT,
                evidence         TEXT,
                confidence_score REAL,
                sample_size      INTEGER,
                economic_impact_est TEXT,
                risk_level       TEXT,
                recommendation   TEXT,
                ftd_draft        TEXT,
                status           TEXT DEFAULT 'PENDING',
                created_at       TEXT,
                approved_at      TEXT,
                rejected_at      TEXT,
                rejection_reason TEXT,
                source_reports   TEXT,
                rule             TEXT,
                evidence_score   INTEGER DEFAULT 0
            )
        """)


async def save_finding(finding_dict: dict) -> None:
    def _save():
        _init_db()
        d = finding_dict
        with _conn() as con:
            con.execute("""
                INSERT OR REPLACE INTO findings
                (lineage_id, title, category, severity, evidence, confidence_score,
                 sample_size, economic_impact_est, risk_level, recommendation,
                 ftd_draft, status, created_at, approved_at, rejected_at,
                 rejection_reason, source_reports, rule, evidence_score)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                d["lineage_id"], d["title"], d["category"], d["severity"],
                json.dumps(d.get("evidence", [])),
                d["confidence_score"], d["sample_size"], d["economic_impact_est"],
                d["risk_level"], d["recommendation"], d.get("ftd_draft"),
                d["status"], d["created_at"], d.get("approved_at"),
                d.get("rejected_at"), d.get("rejection_reason"),
                json.dumps(d.get("source_reports", [])), d.get("rule", ""),
                d.get("evidence_score", 0),
            ))
    await asyncio.to_thread(_save)


async def get_finding(lineage_id: str) -> dict | None:
    def _get():
        _init_db()
        with _conn() as con:
            row = con.execute("SELECT * FROM findings WHERE lineage_id=?", (lineage_id,)).fetchone()
            return _row_to_dict(row) if row else None
    return await asyncio.to_thread(_get)


async def list_findings(status: str | None = None) -> list[dict]:
    def _list():
        _init_db()
        with _conn() as con:
            if status:
                rows = con.execute("SELECT * FROM findings WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
            else:
                rows = con.execute("SELECT * FROM findings ORDER BY created_at DESC").fetchall()
            return [_row_to_dict(r) for r in rows]
    return await asyncio.to_thread(_list)


async def active_finding_exists_for_rule(rule: str) -> bool:
    """Return True if a PENDING or APPROVED finding for this rule already exists.
    Used to prevent duplicate findings across collection cycles.
    """
    def _check():
        _init_db()
        with _conn() as con:
            row = con.execute(
                "SELECT 1 FROM findings WHERE rule=? AND status IN ('PENDING','APPROVED') LIMIT 1",
                (rule,)
            ).fetchone()
            return row is not None
    return await asyncio.to_thread(_check)


async def latest_collection_ts() -> float | None:
    """Return the most recent created_at timestamp from findings (for status display after restart)."""
    def _get():
        _init_db()
        with _conn() as con:
            row = con.execute(
                "SELECT created_at FROM findings ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            return row[0] if row else None
    val = await asyncio.to_thread(_get)
    if val is None:
        return None
    try:
        from datetime import datetime, timezone
        return datetime.fromisoformat(val).replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return None


async def update_status(lineage_id: str, status: str, approved_at: str | None = None,
                         rejected_at: str | None = None, rejection_reason: str | None = None) -> None:
    def _update():
        with _conn() as con:
            con.execute("""
                UPDATE findings SET status=?, approved_at=?, rejected_at=?, rejection_reason=?
                WHERE lineage_id=?
            """, (status, approved_at, rejected_at, rejection_reason, lineage_id))
    await asyncio.to_thread(_update)


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for key in ("evidence", "source_reports"):
        if isinstance(d.get(key), str):
            try:
                d[key] = json.loads(d[key])
            except Exception:
                pass
    return d
