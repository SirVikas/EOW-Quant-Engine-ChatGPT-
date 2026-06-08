"""
PHOENIX NEXUS — Decision Outcome Attribution Engine (DOAE)
FTD-NEXUS-ACCELERATION-001 Phase-B

Tracks FTD registry, config change history, periodic trade snapshots, and
computes pre/post attribution for each deployed FTD.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

_DB_PATH = Path("data/doae.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ftd_registry (
    ftd_id TEXT PRIMARY KEY,
    title TEXT,
    category TEXT,
    deploy_date TEXT,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'ACTIVE',
    expected_impact TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS config_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    param_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    ftd_id TEXT DEFAULT '',
    change_date TEXT,
    source TEXT DEFAULT 'manual',
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS trade_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    engine_version TEXT,
    active_ftds TEXT,
    trades_count INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0.0,
    profit_factor REAL DEFAULT 0.0,
    avg_pnl REAL DEFAULT 0.0,
    total_pnl REAL DEFAULT 0.0,
    ts INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ftd_attribution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ftd_id TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    pre_win_rate REAL DEFAULT 0.0,
    post_win_rate REAL DEFAULT 0.0,
    pre_pf REAL DEFAULT 0.0,
    post_pf REAL DEFAULT 0.0,
    pre_avg_pnl REAL DEFAULT 0.0,
    post_avg_pnl REAL DEFAULT 0.0,
    pre_trades INTEGER DEFAULT 0,
    post_trades INTEGER DEFAULT 0,
    wr_delta REAL DEFAULT 0.0,
    pf_delta REAL DEFAULT 0.0,
    pnl_delta REAL DEFAULT 0.0,
    impact_score REAL DEFAULT 0.0,
    confidence TEXT DEFAULT 'LOW',
    notes TEXT DEFAULT ''
);
"""

_KNOWN_FTDS = [
    ("FTD-IMR-001", "IMRAF Institutional Memory", "ARCHITECTURE", "2024-01-01", "ACTIVE"),
    ("FTD-DIAL-001", "Developer Intelligence Assist Layer", "ARCHITECTURE", "2024-01-01", "ACTIVE"),
    ("FTD-AEOS-001", "Context Assembly Operating System", "ARCHITECTURE", "2024-01-01", "ACTIVE"),
    ("FTD-EMA-001", "Enterprise Memory Architecture", "ARCHITECTURE", "2024-01-01", "ACTIVE"),
    ("FTD-EGI-001", "Engineering Governance Integrity", "ARCHITECTURE", "2024-01-01", "ACTIVE"),
    ("FTD-057", "Adaptive RSI Governor", "TRADING", "2024-06-01", "ACTIVE"),
    ("FTD-037", "TIME_EXIT Extension (8→20min)", "TRADING", "2024-05-01", "ACTIVE"),
    ("FTD-LOSS", "FAST_FAIL loosening (-0.35→-0.55R)", "TRADING", "2024-05-01", "ACTIVE"),
    ("FTD-PHOENIX-ESR-001", "Sub-1min trade eradication", "RISK", "2024-07-01", "ACTIVE"),
    ("FTD-KGE-001", "Knowledge Graph Expansion", "ARCHITECTURE", "", "PENDING"),
    ("FTD-HKE-001", "Historical Knowledge Extraction", "ARCHITECTURE", "", "PENDING"),
    ("FTD-AEG-001", "Autonomous Engineering Governance", "ARCHITECTURE", "", "PENDING"),
    ("FTD-NEXUS-ACCELERATION-001", "NEXUS Acceleration Program", "ARCHITECTURE", "2026-06-08", "ACTIVE"),
]

_KNOWN_CONFIG_CHANGES = [
    ("BREAKEVEN_TRIGGER_R", "1.5", "1.0", "FTD-037", "2024-05-01"),
    ("BREAKEVEN_TRIGGER_R", "1.0", "0.40", "FTD-037", "2024-09-01"),
    ("GENOME_MIN_AVG_R", "0.20", "0.50", "", "2025-01-01"),
    ("GENOME_MIN_AVG_R", "0.50", "0.20", "FTD-NEXUS-ACCELERATION-001", "2026-06-08"),
    ("GENOME_PROMOTE_WIN_RATE", "0.55", "0.50", "", "2024-12-01"),
    ("GENOME_PROMOTE_PF", "1.5", "1.2", "", "2024-12-01"),
    ("_TR_LONG_RSI_TIGHT_MIN", "44.0", "46.0", "FTD-057", "2025-03-01"),
    ("_TR_LONG_RSI_TIGHT_MIN", "46.0", "42.0", "FTD-NEXUS-ACCELERATION-001", "2026-06-08"),
    ("_TIME_EXIT_SECONDS", "480", "1200", "FTD-037", "2024-05-01"),
    ("_FAST_FAIL_R", "-0.35", "-0.55", "FTD-LOSS", "2024-05-01"),
]


class DOAEEngine:
    """
    Decision Outcome Attribution Engine — tracks FTDs, config changes,
    trade snapshots, and computes pre/post attribution for deployed FTDs.
    """

    def __init__(self, db_path: Path = _DB_PATH):
        self._db_path = db_path
        self._lock = threading.RLock()
        os.makedirs(self._db_path.parent, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self.seed()
        logger.info(f"[DOAE] Decision Outcome Attribution Engine ready → {self._db_path}")

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def seed(self) -> None:
        """Insert known FTDs and config changes if tables are empty."""
        with self._lock:
            existing_ftds = self._conn.execute(
                "SELECT COUNT(*) FROM ftd_registry"
            ).fetchone()[0]
            if existing_ftds == 0:
                self._conn.executemany(
                    "INSERT OR IGNORE INTO ftd_registry (ftd_id, title, category, deploy_date, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    _KNOWN_FTDS,
                )
                self._conn.commit()

            existing_cfg = self._conn.execute(
                "SELECT COUNT(*) FROM config_changes"
            ).fetchone()[0]
            if existing_cfg == 0:
                self._conn.executemany(
                    "INSERT INTO config_changes (param_name, old_value, new_value, ftd_id, change_date) "
                    "VALUES (?, ?, ?, ?, ?)",
                    _KNOWN_CONFIG_CHANGES,
                )
                self._conn.commit()

    def get_ftd_registry(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM ftd_registry ORDER BY deploy_date DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_config_changes(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM config_changes ORDER BY change_date DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def record_snapshot(
        self,
        win_rate: float,
        profit_factor: float,
        avg_pnl: float,
        total_pnl: float,
        trades_count: int,
        active_ftds: Optional[List[str]] = None,
    ) -> int:
        from datetime import datetime
        try:
            from config import APP_VERSION
        except Exception:
            APP_VERSION = ""

        snapshot_date = datetime.utcnow().strftime("%Y-%m-%d")
        active_ftds_json = json.dumps(active_ftds or [])
        ts = int(time.time() * 1000)
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO trade_snapshots "
                "(snapshot_date, engine_version, active_ftds, trades_count, "
                "win_rate, profit_factor, avg_pnl, total_pnl, ts) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (snapshot_date, APP_VERSION, active_ftds_json,
                 trades_count, win_rate, profit_factor, avg_pnl, total_pnl, ts),
            )
            self._conn.commit()
            return cur.lastrowid  # type: ignore[return-value]

    def compute_attribution(self, ftd_id: str) -> Dict[str, Any]:
        """
        Compare pre/post trade snapshots around the FTD deploy_date.
        Stores result in ftd_attribution and returns the dict.
        """
        with self._lock:
            ftd_row = self._conn.execute(
                "SELECT * FROM ftd_registry WHERE ftd_id=?", (ftd_id,)
            ).fetchone()

        if ftd_row is None:
            return {"error": f"FTD {ftd_id} not found"}

        deploy_date = ftd_row["deploy_date"] or ""
        from datetime import datetime
        computed_at = datetime.utcnow().isoformat()

        notes = ""
        pre_snap = post_snap = None

        if deploy_date:
            with self._lock:
                pre_snap = self._conn.execute(
                    "SELECT * FROM trade_snapshots WHERE snapshot_date < ? "
                    "ORDER BY snapshot_date DESC LIMIT 1",
                    (deploy_date,),
                ).fetchone()
                post_snap = self._conn.execute(
                    "SELECT * FROM trade_snapshots WHERE snapshot_date >= ? "
                    "ORDER BY snapshot_date ASC LIMIT 1",
                    (deploy_date,),
                ).fetchone()

        if pre_snap is None or post_snap is None:
            notes = "insufficient snapshot history"
            pre_wr = post_wr = pre_pf = post_pf = pre_avg = post_avg = 0.0
            pre_trades = post_trades = 0
        else:
            pre_wr     = pre_snap["win_rate"]
            post_wr    = post_snap["win_rate"]
            pre_pf     = pre_snap["profit_factor"]
            post_pf    = post_snap["profit_factor"]
            pre_avg    = pre_snap["avg_pnl"]
            post_avg   = post_snap["avg_pnl"]
            pre_trades  = pre_snap["trades_count"]
            post_trades = post_snap["trades_count"]

        wr_delta  = round(post_wr - pre_wr, 4)
        pf_delta  = round(post_pf - pre_pf, 4)
        pnl_delta = round(post_avg - pre_avg, 4)

        impact_score = round(
            (pf_delta * 30) + (wr_delta * 100 * 0.5) + (pnl_delta * 0.2), 4
        )

        min_trades = min(pre_trades, post_trades)
        if min_trades < 20:
            confidence = "LOW"
        elif min_trades < 100:
            confidence = "MEDIUM"
        else:
            confidence = "HIGH"

        with self._lock:
            self._conn.execute(
                "INSERT INTO ftd_attribution "
                "(ftd_id, computed_at, pre_win_rate, post_win_rate, pre_pf, post_pf, "
                "pre_avg_pnl, post_avg_pnl, pre_trades, post_trades, "
                "wr_delta, pf_delta, pnl_delta, impact_score, confidence, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ftd_id, computed_at, pre_wr, post_wr, pre_pf, post_pf,
                 pre_avg, post_avg, pre_trades, post_trades,
                 wr_delta, pf_delta, pnl_delta, impact_score, confidence, notes),
            )
            self._conn.commit()

        return {
            "ftd_id":       ftd_id,
            "computed_at":  computed_at,
            "deploy_date":  deploy_date,
            "pre_win_rate": pre_wr,
            "post_win_rate": post_wr,
            "pre_pf":       pre_pf,
            "post_pf":      post_pf,
            "pre_avg_pnl":  pre_avg,
            "post_avg_pnl": post_avg,
            "pre_trades":   pre_trades,
            "post_trades":  post_trades,
            "wr_delta":     wr_delta,
            "pf_delta":     pf_delta,
            "pnl_delta":    pnl_delta,
            "impact_score": impact_score,
            "confidence":   confidence,
            "notes":        notes,
        }

    def get_top_positive(self, n: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM ftd_attribution ORDER BY impact_score DESC LIMIT ?", (n,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_top_negative(self, n: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM ftd_attribution ORDER BY impact_score ASC LIMIT ?", (n,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_attribution_report(self) -> Dict[str, Any]:
        with self._lock:
            attr_rows = self._conn.execute(
                "SELECT * FROM ftd_attribution ORDER BY impact_score DESC"
            ).fetchall()
        attributions = [dict(r) for r in attr_rows]
        return {
            "ftd_registry":   self.get_ftd_registry(),
            "config_changes": self.get_config_changes(),
            "attributions":   attributions,
            "is_operational": len(attributions) > 0,
        }

    def compute_all_attributions(self) -> None:
        """Run compute_attribution for all FTDs with a deploy_date set."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT ftd_id FROM ftd_registry WHERE deploy_date != '' AND deploy_date IS NOT NULL"
            ).fetchall()
        for row in rows:
            try:
                self.compute_attribution(row["ftd_id"])
            except Exception as exc:
                logger.warning(f"[DOAE] Attribution failed for {row['ftd_id']}: {exc}")

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_ftds = self._conn.execute(
                "SELECT COUNT(*) FROM ftd_registry"
            ).fetchone()[0]
            ftds_with_attr = self._conn.execute(
                "SELECT COUNT(DISTINCT ftd_id) FROM ftd_attribution"
            ).fetchone()[0]
            attr_count = self._conn.execute(
                "SELECT COUNT(*) FROM ftd_attribution"
            ).fetchone()[0]
            total_cfg = self._conn.execute(
                "SELECT COUNT(*) FROM config_changes"
            ).fetchone()[0]
            snap_count = self._conn.execute(
                "SELECT COUNT(*) FROM trade_snapshots"
            ).fetchone()[0]
        return {
            "total_ftds":             total_ftds,
            "ftds_with_attribution":  ftds_with_attr,
            "attribution_operational": attr_count > 0,
            "total_config_changes":   total_cfg,
            "snapshot_count":         snap_count,
        }

    def close(self) -> None:
        with self._lock:
            self._conn.close()


# ── Singleton ─────────────────────────────────────────────────────────────────
doae = DOAEEngine()
