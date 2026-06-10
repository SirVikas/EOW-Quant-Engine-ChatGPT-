"""
Truth Archive — persists AttributionSnapshot to SQLite for post-session analysis.
Uses existing DB path pattern from the codebase.
"""
from __future__ import annotations
import sqlite3, json, threading, time, pathlib
from typing import List, Optional
from loguru import logger
from core.truth.alpha_attribution import AttributionSnapshot

ARCHIVE_PATH = pathlib.Path("data/truth_archive.db")


class TruthArchive:
    def __init__(self):
        ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
        logger.info("[TRUTH-ARCHIVE] Initialized")

    def _init_db(self):
        with sqlite3.connect(ARCHIVE_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS truth_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT,
                    symbol TEXT,
                    session TEXT,
                    strategy TEXT,
                    regime TEXT,
                    entry_truth_score REAL,
                    exit_truth_score REAL,
                    structure_score REAL,
                    regime_score REAL,
                    momentum_score REAL,
                    volatility_score REAL,
                    liquidity_score REAL,
                    cost_score REAL,
                    net_pnl REAL,
                    r_multiple REAL,
                    genome_id TEXT,
                    rl_context TEXT,
                    ts_entry REAL,
                    ts_exit REAL,
                    alpha_sources TEXT,
                    destruction_sources TEXT,
                    created_at REAL DEFAULT (strftime('%s','now'))
                )
            """)
            conn.commit()

    def save(self, snap: AttributionSnapshot) -> None:
        with self._lock:
            try:
                with sqlite3.connect(ARCHIVE_PATH) as conn:
                    conn.execute("""
                        INSERT INTO truth_snapshots
                        (trade_id, symbol, session, strategy, regime,
                         entry_truth_score, exit_truth_score,
                         structure_score, regime_score, momentum_score,
                         volatility_score, liquidity_score, cost_score,
                         net_pnl, r_multiple, genome_id, rl_context,
                         ts_entry, ts_exit, alpha_sources, destruction_sources)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        snap.trade_id, snap.symbol, snap.session, snap.strategy,
                        snap.regime, snap.entry_truth_score, snap.exit_truth_score,
                        snap.structure_score, snap.regime_score, snap.momentum_score,
                        snap.volatility_score, snap.liquidity_score, snap.cost_score,
                        snap.net_pnl, snap.r_multiple, snap.genome_id, snap.rl_context,
                        snap.ts_entry, snap.ts_exit,
                        json.dumps(snap.alpha_sources),
                        json.dumps(snap.destruction_sources),
                    ))
                    conn.commit()
            except Exception as e:
                logger.warning(f"[TRUTH-ARCHIVE] Save failed: {e}")

    def recent(self, n: int = 100) -> List[dict]:
        with self._lock:
            try:
                with sqlite3.connect(ARCHIVE_PATH) as conn:
                    rows = conn.execute(
                        "SELECT * FROM truth_snapshots ORDER BY created_at DESC LIMIT ?", (n,)
                    ).fetchall()
                    cols = [d[1] for d in conn.execute("PRAGMA table_info(truth_snapshots)").fetchall()]
                    return [dict(zip(cols, r)) for r in rows]
            except Exception:
                return []

    def count(self) -> int:
        """Cumulative ETE-scored sample count — survives restarts.
        This is the Phase-2 calibration progress metric (target ≥500)."""
        with self._lock:
            try:
                with sqlite3.connect(ARCHIVE_PATH) as conn:
                    return conn.execute(
                        "SELECT COUNT(*) FROM truth_snapshots"
                    ).fetchone()[0]
            except Exception:
                return 0

    def load_all(self, limit: int = 10000) -> List[AttributionSnapshot]:
        """Rehydrate archived snapshots (oldest first) for boot-time AAP restore.
        Without this, calibration reports only cover the current session and a
        multi-session 500-sample calibration would be silently invalid."""
        with self._lock:
            try:
                with sqlite3.connect(ARCHIVE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    rows = conn.execute(
                        "SELECT * FROM truth_snapshots ORDER BY created_at ASC LIMIT ?",
                        (limit,),
                    ).fetchall()
            except Exception as e:
                logger.warning(f"[TRUTH-ARCHIVE] load_all failed: {e}")
                return []
        snaps: List[AttributionSnapshot] = []
        for r in rows:
            try:
                snaps.append(AttributionSnapshot(
                    trade_id=r["trade_id"] or "",
                    symbol=r["symbol"] or "",
                    session=r["session"] or "UNKNOWN",
                    strategy=r["strategy"] or "",
                    regime=r["regime"] or "UNKNOWN",
                    entry_truth_score=r["entry_truth_score"] or 0.0,
                    exit_truth_score=r["exit_truth_score"] or 0.0,
                    structure_score=r["structure_score"] or 0.0,
                    regime_score=r["regime_score"] or 0.0,
                    momentum_score=r["momentum_score"] or 0.0,
                    volatility_score=r["volatility_score"] or 0.0,
                    liquidity_score=r["liquidity_score"] or 0.0,
                    cost_score=r["cost_score"] or 0.0,
                    net_pnl=r["net_pnl"] or 0.0,
                    r_multiple=r["r_multiple"] or 0.0,
                    genome_id=r["genome_id"],
                    rl_context=r["rl_context"],
                    ts_entry=r["ts_entry"] or 0.0,
                    ts_exit=r["ts_exit"] or 0.0,
                    alpha_sources=json.loads(r["alpha_sources"] or "[]"),
                    destruction_sources=json.loads(r["destruction_sources"] or "[]"),
                ))
            except Exception:
                continue   # one corrupt row must not abort the whole restore
        return snaps


truth_archive = TruthArchive()
