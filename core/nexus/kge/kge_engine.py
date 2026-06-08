"""
KGE v2 — Knowledge Graph Engine.

SQLite-backed graph of institutional entities and their relationships.
Seeded from static known entities on first run; enriched incrementally from IMRAF.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections import deque
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

import logging
logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_graph.db"

_BOOTSTRAP_SENTINEL = "kge_bootstrap_v2_done"


class KGEEngine:
    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._last_enrichment_ts: int = 0
        self._init_db()
        if not self._is_bootstrapped():
            self.bootstrap_from_static()
            self._mark_bootstrapped()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._db_path), timeout=10)

    def _init_db(self):
        with self._connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS kg_nodes (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_type TEXT NOT NULL,
                    node_id   TEXT NOT NULL UNIQUE,
                    label     TEXT NOT NULL,
                    data      TEXT DEFAULT '{}',
                    ts        INTEGER NOT NULL
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS kg_edges (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_node    TEXT NOT NULL,
                    to_node      TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    weight       REAL DEFAULT 1.0,
                    data         TEXT DEFAULT '{}',
                    ts           INTEGER NOT NULL,
                    UNIQUE(from_node, to_node, relationship)
                )
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_node_type ON kg_nodes(node_type)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_from_node ON kg_edges(from_node)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_to_node ON kg_edges(to_node)")
            con.execute("""
                CREATE TABLE IF NOT EXISTS kg_meta (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            con.execute("PRAGMA journal_mode=WAL")
            con.commit()

    def _is_bootstrapped(self) -> bool:
        with self._connect() as con:
            row = con.execute(
                "SELECT value FROM kg_meta WHERE key=?", (_BOOTSTRAP_SENTINEL,)
            ).fetchone()
        return row is not None

    def _mark_bootstrapped(self):
        with self._lock:
            with self._connect() as con:
                con.execute(
                    "INSERT OR REPLACE INTO kg_meta (key, value) VALUES (?,?)",
                    (_BOOTSTRAP_SENTINEL, "1"),
                )
                con.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_node(self, node_type: str, node_id: str, label: str, data: dict = None) -> bool:
        ts = int(time.time() * 1000)
        with self._lock:
            with self._connect() as con:
                cur = con.execute(
                    "INSERT OR IGNORE INTO kg_nodes (node_type, node_id, label, data, ts) VALUES (?,?,?,?,?)",
                    (node_type, node_id, label, json.dumps(data or {}), ts),
                )
                con.commit()
                return cur.rowcount > 0

    def add_edge(self, from_node: str, to_node: str, relationship: str, weight: float = 1.0, data: dict = None) -> bool:
        ts = int(time.time() * 1000)
        with self._lock:
            with self._connect() as con:
                cur = con.execute(
                    "INSERT OR IGNORE INTO kg_edges (from_node, to_node, relationship, weight, data, ts) VALUES (?,?,?,?,?,?)",
                    (from_node, to_node, relationship, weight, json.dumps(data or {}), ts),
                )
                con.commit()
                return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def _fetch_node(self, con: sqlite3.Connection, node_id: str) -> Optional[dict]:
        row = con.execute(
            "SELECT node_type, node_id, label, data FROM kg_nodes WHERE node_id=?",
            (node_id,),
        ).fetchone()
        if row is None:
            return None
        return {"node_type": row[0], "node_id": row[1], "label": row[2], "data": json.loads(row[3])}

    def get_neighbors(self, node_id: str, max_depth: int = 2) -> dict:
        with self._connect() as con:
            root = self._fetch_node(con, node_id)
            if root is None:
                return {"node": None, "neighbors": []}

            visited: set = {node_id}
            queue: deque = deque()
            neighbors: List[dict] = []

            # Seed queue with depth-1 edges (both directions)
            rows = con.execute(
                "SELECT from_node, to_node, relationship, weight FROM kg_edges "
                "WHERE from_node=? OR to_node=?",
                (node_id, node_id),
            ).fetchall()
            for r in rows:
                other = r[1] if r[0] == node_id else r[0]
                if other not in visited:
                    visited.add(other)
                    queue.append((other, {"from_node": r[0], "to_node": r[1], "relationship": r[2], "weight": r[3]}, 1))

            while queue:
                nid, edge, depth = queue.popleft()
                node = self._fetch_node(con, nid)
                neighbors.append({"node": node, "edge": edge, "depth": depth})
                if depth < max_depth:
                    rows2 = con.execute(
                        "SELECT from_node, to_node, relationship, weight FROM kg_edges "
                        "WHERE from_node=? OR to_node=?",
                        (nid, nid),
                    ).fetchall()
                    for r in rows2:
                        other = r[1] if r[0] == nid else r[0]
                        if other not in visited:
                            visited.add(other)
                            queue.append((other, {"from_node": r[0], "to_node": r[1], "relationship": r[2], "weight": r[3]}, depth + 1))

        return {"node": root, "neighbors": neighbors}

    def get_stats(self) -> dict:
        with self._connect() as con:
            node_count = con.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
            edge_count = con.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
            by_type_rows = con.execute(
                "SELECT node_type, COUNT(*) FROM kg_nodes GROUP BY node_type"
            ).fetchall()
        by_type = {r[0]: r[1] for r in by_type_rows}
        coverage_score = min(100, int((node_count / 50) * 50 + (edge_count / 100) * 50))
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "by_type": by_type,
            "coverage_score": coverage_score,
        }

    def get_full_graph(self, limit: int = 200) -> dict:
        with self._connect() as con:
            total_nodes = con.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
            total_edges = con.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
            node_rows = con.execute(
                "SELECT node_type, node_id, label, data FROM kg_nodes LIMIT ?", (limit,)
            ).fetchall()
            edge_rows = con.execute(
                "SELECT from_node, to_node, relationship, weight FROM kg_edges LIMIT ?", (limit,)
            ).fetchall()
        nodes = [{"node_type": r[0], "node_id": r[1], "label": r[2], "data": json.loads(r[3])} for r in node_rows]
        edges = [{"from_node": r[0], "to_node": r[1], "relationship": r[2], "weight": r[3]} for r in edge_rows]
        return {"nodes": nodes, "edges": edges, "total_nodes": total_nodes, "total_edges": total_edges}

    def get_signal_chain(self) -> dict:
        chain_nodes = [
            "RSI_GATE", "LCC_GATE", "SCORE_GATE", "RL_GATE", "FEE_GATE",
            "signal_ecology", "trade_manager", "risk_engine",
        ]
        with self._connect() as con:
            existing = set()
            for nid in chain_nodes:
                row = con.execute("SELECT node_id FROM kg_nodes WHERE node_id=?", (nid,)).fetchone()
                if row:
                    existing.add(nid)
        completeness = len(existing) / len(chain_nodes) if chain_nodes else 0.0
        return {
            "chain": [
                {"step": 1, "node": "RSI_GATE", "type": "GATE", "description": "RSI regime gate — filters entries by RSI range per strategy"},
                {"step": 2, "node": "LCC_GATE", "type": "GATE", "description": "Loss cluster gate — pauses trading after rapid consecutive losses"},
                {"step": 3, "node": "SCORE_GATE", "type": "GATE", "description": "Signal score gate — minimum alpha score threshold"},
                {"step": 4, "node": "RL_GATE", "type": "GATE", "description": "RL approval gate — reinforcement learning entry approval"},
                {"step": 5, "node": "FEE_GATE", "type": "GATE", "description": "Fee viability gate — rejects trades where fees erode expected EV"},
                {"step": 6, "node": "signal_ecology", "type": "MODULE", "description": "Signal ecology — integrates gate outputs into final signal"},
                {"step": 7, "node": "trade_manager", "type": "MODULE", "description": "Trade manager — executes and manages positions"},
                {"step": 8, "node": "risk_engine", "type": "MODULE", "description": "Risk engine — real-time risk oversight on open positions"},
            ],
            "status": "DOCUMENTED",
            "completeness": round(completeness, 2),
        }

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def bootstrap_from_static(self):
        ts = int(time.time() * 1000)

        modules = [
            "trade_manager", "risk_engine", "alpha_context_memory", "data_lake",
            "pnl_calc", "genome_engine", "rl_engine", "signal_ecology",
            "loss_cluster", "safe_mode", "adaptive_scorer", "adaptive_rsi_governor",
            "regime_cartography", "trade_flow_monitor",
        ]
        for m in modules:
            self.add_node("MODULE", m, m.replace("_", " ").title())

        strategies = ["TrendFollowing", "MeanReversion", "VolatilityExpansion"]
        for s in strategies:
            self.add_node("STRATEGY", s, s)

        ftds = [
            ("FTD-IMR-001", "IMRAF Institutional Memory"),
            ("FTD-DIAL-001", "DIAL Developer Intelligence"),
            ("FTD-AEOS-001", "AEOS Context Assembly"),
            ("FTD-EMA-001", "EMA Enterprise Memory Architecture"),
            ("FTD-EGI-001", "EGI Engineering Governance Integrity"),
            ("FTD-057", "Adaptive RSI Governor"),
            ("FTD-037", "Breakeven and Time Exit Tuning"),
            ("FTD-LOSS", "Loss Cluster Fast Fail Configuration"),
            ("FTD-PHOENIX-ESR-001", "PHOENIX ESR Emergency Strategy Review"),
            ("FTD-KGE-001", "Knowledge Graph Expansion Program"),
            ("FTD-HKE-001", "Historical Knowledge Extraction Program"),
            ("FTD-AEG-001", "Autonomous Engineering Governance"),
            ("FTD-NEXUS-ACCELERATION-001", "NEXUS Acceleration Program"),
        ]
        for fid, flabel in ftds:
            self.add_node("FTD", fid, flabel)

        configs = [
            "BREAKEVEN_TRIGGER_R", "GENOME_MIN_AVG_R", "GENOME_PROMOTE_WIN_RATE",
            "LCC_PAUSE_MINUTES", "_TR_LONG_RSI_TIGHT_MIN", "TRAIL_ATR_MULT", "PARTIAL_TP_R",
        ]
        for c in configs:
            self.add_node("CONFIG", c, c)

        gates = ["RSI_GATE", "LCC_GATE", "SCORE_GATE", "RL_GATE", "FEE_GATE"]
        for g in gates:
            self.add_node("GATE", g, g.replace("_", " ").title())

        regimes = ["TRENDING", "MEAN_REVERTING", "VOLATILITY_EXPANSION", "UNKNOWN"]
        for r in regimes:
            self.add_node("REGIME", r, r.replace("_", " ").title())

        # Known edges
        edges = [
            ("FTD-057", "adaptive_rsi_governor", "INTRODUCED"),
            ("FTD-037", "BREAKEVEN_TRIGGER_R", "CONFIGURED_BY"),
            ("FTD-037", "_TR_LONG_RSI_TIGHT_MIN", "CONFIGURED_BY"),
            ("FTD-LOSS", "_fast_fail_R", "CONFIGURED_BY"),
            ("FTD-NEXUS-ACCELERATION-001", "FTD-KGE-001", "INTRODUCED"),
            ("adaptive_rsi_governor", "RSI_GATE", "DEPENDS_ON"),
            ("genome_engine", "TrendFollowing", "DEPENDS_ON"),
            ("genome_engine", "MeanReversion", "DEPENDS_ON"),
            ("risk_engine", "trade_manager", "DEPENDS_ON"),
            ("signal_ecology", "RSI_GATE", "DEPENDS_ON"),
            ("signal_ecology", "LCC_GATE", "DEPENDS_ON"),
            ("signal_ecology", "SCORE_GATE", "DEPENDS_ON"),
            ("signal_ecology", "RL_GATE", "DEPENDS_ON"),
            ("TrendFollowing", "TRENDING", "RELATED_TO"),
            ("MeanReversion", "MEAN_REVERTING", "RELATED_TO"),
        ]
        for from_n, to_n, rel in edges:
            self.add_edge(from_n, to_n, rel)

    # ------------------------------------------------------------------
    # Enrichment
    # ------------------------------------------------------------------

    def enrich_from_imraf(self):
        try:
            from core.institutional_memory.imraf_engine import imraf
        except ImportError:
            logger.warning("KGE: cannot import imraf for enrichment")
            return

        since_ts = self._last_enrichment_ts
        try:
            records = imraf.get_all(since_ts=since_ts if since_ts > 0 else None)
        except Exception as exc:
            logger.warning("KGE enrich_from_imraf error: %s", exc)
            return

        enriched = 0
        for rec in records:
            try:
                node_id = f"IMRAF-{rec.id}"
                # rec.category is a plain string (IMRAFRecord stores raw value)
                if rec.category == "EVOLUTION":
                    self.add_node("GENOME_DECISION", node_id, rec.title, {"ts": rec.ts, "subcategory": rec.subcategory})
                    self.add_edge(node_id, "genome_engine", "RELATED_TO")
                elif rec.category == "REGIME":
                    self.add_node("REGIME_EVENT", node_id, rec.title, {"ts": rec.ts})
                    self.add_edge(node_id, "regime_cartography", "RELATED_TO")
                elif rec.category == "INCIDENT":
                    self.add_node("INCIDENT", node_id, rec.title, {"ts": rec.ts})
                    if rec.subcategory:
                        self.add_edge(node_id, rec.subcategory, "RELATED_TO")
                elif rec.category == "FAILURE":
                    self.add_node("FAILURE", node_id, rec.title, {"ts": rec.ts})
                enriched += 1
                if rec.ts > self._last_enrichment_ts:
                    self._last_enrichment_ts = rec.ts
            except Exception:
                pass

        if enriched:
            logger.info("KGE enriched %d nodes from IMRAF", enriched)


# Singleton — lazy so tests can override db_path
kge = KGEEngine()
