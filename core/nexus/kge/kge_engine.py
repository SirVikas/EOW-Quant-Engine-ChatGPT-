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

_NEXUS_KEYWORDS = [
    "genome", "rsi", "alpha", "context", "memory", "loss", "risk", "rl",
    "engine", "adaptive", "scorer", "safe", "mode", "cluster", "signal",
    "trade", "manager", "data", "lake", "pnl", "calc", "strategy",
    "imraf", "doae", "kge", "hke", "governance", "confidence", "aeg",
    "nexus", "dcel", "ema", "dial", "aeos", "egi",
]

_FTD_TEMPORAL_ORDER = [
    "FTD-IMR-001", "FTD-DIAL-001", "FTD-AEOS-001", "FTD-EMA-001", "FTD-EGI-001",
    "FTD-033", "FTD-034", "FTD-035", "FTD-036", "FTD-037", "FTD-038",
    "FTD-039", "FTD-040", "FTD-057",
    "FTD-NEXUS-ACCEL-001",
]

_FTD_METRIC_MAP = {
    "FTD-033": ["win_rate", "drawdown", "hold_time"],
    "FTD-034": ["context_amplification", "win_rate"],
    "FTD-035": ["drawdown", "trade_frequency"],
    "FTD-036": ["win_rate", "trade_frequency"],
    "FTD-037": ["drawdown"],
    "FTD-038": ["win_rate", "context_amplification"],
    "FTD-039": ["win_rate", "trade_frequency"],
    "FTD-040": ["context_amplification"],
    "FTD-057": ["context_amplification", "win_rate"],
}

_CAUSAL_HYPOTHESES = [
    ("FTD-033", "win_rate", "TSL fix removed premature BE exits → more trades capture profit"),
    ("FTD-034", "context_amplification", "Key fix restored 1.25x boost to 34 profitable contexts"),
    ("FTD-035", "drawdown", "LCC circuit breaker reduced consecutive-loss drawdown clusters"),
    ("FTD-038", "win_rate", "RL contextual bandit filters low-quality signals by regime"),
]


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
            ("FTD-033", "Alpha Engine Cost-Adjusted"),
            ("FTD-034", "Genome Engine Evolutionary Optimizer"),
            ("FTD-035", "Loss Cluster Controller"),
            ("FTD-036", "Adaptive RSI Governor"),
            ("FTD-037", "Risk Controller MDD Drawdown Gate"),
            ("FTD-038", "RL Engine Contextual Bandit"),
            ("FTD-039", "Adaptive Scorer"),
            ("FTD-040", "Alpha Context Memory"),
            ("FTD-057", "Adaptive RSI Governor Phase-2"),
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
            "LCC_MAX_CONSECUTIVE", "RSI_FLOOR", "MAX_DRAWDOWN_HALT",
            "RL_EXPLORATION_RATE", "MIN_SCORE", "ALPHA_BOOST_MULT",
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

    # ------------------------------------------------------------------
    # Intelligent Relationship Builder
    # ------------------------------------------------------------------

    _FTD_MODULE_MAP = {
        "FTD-033":                    ["trade_manager"],
        "FTD-034":                    ["alpha_context_memory"],
        "FTD-035":                    ["loss_cluster"],
        "FTD-036":                    ["adaptive_rsi_governor"],
        "FTD-037":                    ["trade_manager"],
        "FTD-057":                    ["adaptive_rsi_governor"],
        "FTD-038":                    ["rl_engine"],
        "FTD-039":                    ["adaptive_scorer"],
        "FTD-040":                    ["alpha_context_memory"],
        "FTD-IMR-001":                ["imraf_engine"],
        "FTD-NEXUS-ACCELERATION-001": ["doae_engine", "kge_engine", "governance_intelligence", "iq_dashboard"],
    }

    _MODULE_DEPS = [
        ("alpha_engine",    "net_edge_engine"),
        ("rl_engine",       "alpha_context_memory"),
        ("adaptive_scorer", "rl_engine"),
        ("trade_manager",   "risk_controller"),
        ("genome_engine",   "adaptive_scorer"),
    ]

    def build_intelligent_relationships(self) -> dict:
        edges_added = 0

        with self._connect() as con:
            module_rows   = con.execute("SELECT node_id, label FROM kg_nodes WHERE node_type='MODULE'").fetchall()
            config_rows   = con.execute("SELECT node_id, label FROM kg_nodes WHERE node_type='CONFIG'").fetchall()
            ftd_rows      = con.execute("SELECT node_id FROM kg_nodes WHERE node_type='FTD'").fetchall()
            strategy_rows = con.execute("SELECT node_id, label FROM kg_nodes WHERE node_type='STRATEGY'").fetchall()

        for mod_id, mod_label in module_rows:
            stem = mod_id.split(":")[-1].replace("_", " ").upper()
            keywords = [w for w in stem.split() if len(w) >= 3]
            for cfg_id, cfg_label in config_rows:
                cfg_upper = cfg_label.upper()
                if any(kw in cfg_upper for kw in keywords):
                    if self.add_edge(mod_id, cfg_id, "CONFIGURES"):
                        edges_added += 1

        existing_ftd_ids = {r[0] for r in ftd_rows}
        for ftd_id, modules in self._FTD_MODULE_MAP.items():
            if ftd_id not in existing_ftd_ids:
                continue
            for mod_name in modules:
                with self._connect() as con:
                    candidates = con.execute(
                        "SELECT node_id FROM kg_nodes WHERE node_type='MODULE' "
                        "AND (node_id=? OR node_id LIKE ?)",
                        (mod_name, f"%{mod_name}%"),
                    ).fetchall()
                for row in candidates:
                    if self.add_edge(ftd_id, row[0], "IMPLEMENTS"):
                        edges_added += 1

        strategy_module_map = {
            "TrendFollowing":      ["adaptive_rsi_governor", "signal_ecology"],
            "MeanReversion":       ["signal_ecology"],
            "VolatilityExpansion": ["regime_cartography"],
        }
        for strat_id, _label in strategy_rows:
            targets = strategy_module_map.get(strat_id, [])
            for mod_name in targets:
                with self._connect() as con:
                    candidates = con.execute(
                        "SELECT node_id FROM kg_nodes WHERE node_type='MODULE' "
                        "AND (node_id=? OR node_id LIKE ?)",
                        (mod_name, f"%{mod_name}%"),
                    ).fetchall()
                for row in candidates:
                    if self.add_edge(strat_id, row[0], "USES"):
                        edges_added += 1

        for from_mod, to_mod in self._MODULE_DEPS:
            with self._connect() as con:
                from_rows = con.execute(
                    "SELECT node_id FROM kg_nodes WHERE node_type='MODULE' "
                    "AND (node_id=? OR node_id LIKE ?)",
                    (from_mod, f"%{from_mod}%"),
                ).fetchall()
                to_rows = con.execute(
                    "SELECT node_id FROM kg_nodes WHERE node_type='MODULE' "
                    "AND (node_id=? OR node_id LIKE ?)",
                    (to_mod, f"%{to_mod}%"),
                ).fetchall()
            for f_row in from_rows:
                for t_row in to_rows:
                    if self.add_edge(f_row[0], t_row[0], "DEPENDS_ON"):
                        edges_added += 1

        logger.info("KGE build_intelligent_relationships: %d edges added", edges_added)
        return {"edges_added": edges_added}

    def relationship_intelligence_score(self) -> dict:
        with self._connect() as con:
            total_nodes = con.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
            total_edges = con.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
            edge_pairs  = con.execute("SELECT from_node, to_node FROM kg_edges").fetchall()
            node_ids    = [r[0] for r in con.execute("SELECT node_id FROM kg_nodes").fetchall()]
            semantic_edges    = con.execute("SELECT COUNT(*) FROM kg_edges WHERE relationship='RELATED_TO'").fetchone()[0]
            temporal_edges    = con.execute("SELECT COUNT(*) FROM kg_edges WHERE relationship='PRECEDED_BY'").fetchone()[0]
            causal_hypotheses = con.execute("SELECT COUNT(*) FROM kg_edges WHERE relationship='CAUSAL_HYPOTHESIS'").fetchone()[0]
            metric_nodes      = con.execute("SELECT COUNT(*) FROM kg_nodes WHERE node_type='METRIC'").fetchone()[0]

        if total_nodes == 0:
            return {
                "total_nodes": 0, "total_edges": 0, "avg_edges_per_node": 0.0,
                "isolated_nodes": 0, "well_connected": 0, "relationship_density": 0.0,
                "intelligence_score": 0.0, "top_hubs": [],
                "semantic_edges": 0, "temporal_edges": 0,
                "causal_hypotheses": 0, "metric_nodes": 0,
            }

        edge_counts: dict = {}
        for from_n, to_n in edge_pairs:
            edge_counts[from_n] = edge_counts.get(from_n, 0) + 1
            edge_counts[to_n]   = edge_counts.get(to_n,   0) + 1

        isolated     = sum(1 for nid in node_ids if edge_counts.get(nid, 0) == 0)
        well_conn    = sum(1 for nid in node_ids if edge_counts.get(nid, 0) >= 3)
        avg_edges    = round(sum(edge_counts.values()) / total_nodes, 4) if total_nodes else 0.0
        isolated_ratio = isolated / total_nodes

        max_possible = total_nodes * (total_nodes - 1) / 2
        density = round(total_edges / max_possible, 6) if max_possible > 0 else 0.0

        # Updated formula: rewards avg connectivity, non-isolation, and semantic richness
        semantic_bonus = min(20.0, (well_conn / max(total_nodes, 1)) * 40.0)
        intel_score = round(
            min(100.0, (avg_edges / 3.0) * 40.0 + (1.0 - isolated_ratio) * 40.0 + semantic_bonus),
            2,
        )

        hub_list = sorted(
            [{"node_id": nid, "edge_count": edge_counts.get(nid, 0)} for nid in node_ids],
            key=lambda x: x["edge_count"],
            reverse=True,
        )[:5]
        with self._connect() as con:
            for hub in hub_list:
                row = con.execute("SELECT label FROM kg_nodes WHERE node_id=?", (hub["node_id"],)).fetchone()
                hub["label"] = row[0] if row else hub["node_id"]

        return {
            "total_nodes":          total_nodes,
            "total_edges":          total_edges,
            "avg_edges_per_node":   avg_edges,
            "isolated_nodes":       isolated,
            "well_connected":       well_conn,
            "relationship_density": density,
            "intelligence_score":   intel_score,
            "top_hubs":             hub_list,
            "semantic_edges":       semantic_edges,
            "temporal_edges":       temporal_edges,
            "causal_hypotheses":    causal_hypotheses,
            "metric_nodes":         metric_nodes,
        }

    # ------------------------------------------------------------------
    # Codebase Bootstrap
    # ------------------------------------------------------------------

    def bootstrap_from_codebase(self, root_path: str = ".") -> dict:
        import re
        from pathlib import Path as _Path

        root = _Path(root_path).resolve()
        modules_added   = 0
        config_added    = 0
        verifiers_added = 0
        endpoints_added = 0
        edges_added     = 0

        try:
            core_dir = root / "core"
            for py_file in core_dir.rglob("*.py"):
                if "__pycache__" in py_file.parts:
                    continue
                node_id = "module:" + str(py_file.relative_to(root)).replace("/", ".").removesuffix(".py")
                label   = py_file.stem.replace("_", " ").title()
                added   = self.add_node("MODULE", node_id, label, {"path": str(py_file.relative_to(root))})
                if added:
                    modules_added += 1
                    stem_upper = py_file.stem.upper()
                    with self._connect() as con:
                        ftd_row = con.execute(
                            "SELECT node_id FROM kg_nodes WHERE node_type='FTD' AND UPPER(label) LIKE ?",
                            (f"%{stem_upper}%",),
                        ).fetchone()
                        if ftd_row:
                            if self.add_edge(node_id, ftd_row[0], "IMPLEMENTS"):
                                edges_added += 1
                        strat_row = con.execute(
                            "SELECT node_id FROM kg_nodes WHERE node_type='STRATEGY' AND UPPER(node_id) LIKE ?",
                            (f"%{stem_upper}%",),
                        ).fetchone()
                        if strat_row:
                            if self.add_edge(node_id, strat_row[0], "PART_OF"):
                                edges_added += 1
        except Exception as exc:
            logger.warning("KGE bootstrap_from_codebase modules scan error: %s", exc)

        try:
            config_file     = root / "config.py"
            config_pattern  = re.compile(r'^\s*([A-Z][A-Z0-9_]{2,})\s*(?::\s*\S+\s*)?=\s*')
            for line in config_file.read_text(errors="replace").splitlines():
                m = config_pattern.match(line)
                if m:
                    param = m.group(1)
                    added = self.add_node("CONFIG", param, param)
                    if added:
                        config_added += 1
        except Exception as exc:
            logger.warning("KGE bootstrap_from_codebase config scan error: %s", exc)

        try:
            tests_dir = root / "tests"
            for py_file in tests_dir.rglob("*.py"):
                if "__pycache__" in py_file.parts:
                    continue
                node_id = "verifier:" + py_file.stem
                label   = py_file.stem.replace("_", " ").title()
                added   = self.add_node("VERIFIER", node_id, label, {"path": str(py_file.relative_to(root))})
                if added:
                    verifiers_added += 1
        except Exception as exc:
            logger.warning("KGE bootstrap_from_codebase verifiers scan error: %s", exc)

        try:
            main_file        = root / "main.py"
            endpoint_pattern = re.compile(r'@app\.(get|post)\(["\']([^"\']+)["\']')
            for line in main_file.read_text(errors="replace").splitlines():
                m = endpoint_pattern.search(line)
                if m:
                    method  = m.group(1).upper()
                    path    = m.group(2)
                    node_id = f"endpoint:{method}:{path}"
                    label   = f"{method} {path}"
                    added   = self.add_node("ENDPOINT", node_id, label, {"method": method, "path": path})
                    if added:
                        endpoints_added += 1
        except Exception as exc:
            logger.warning("KGE bootstrap_from_codebase endpoints scan error: %s", exc)

        logger.info(
            "KGE bootstrap_from_codebase: modules=%d config=%d verifiers=%d endpoints=%d edges=%d",
            modules_added, config_added, verifiers_added, endpoints_added, edges_added,
        )

        intel = self.build_intelligent_relationships()
        deep  = self.build_deep_relationships()
        sem   = self.build_semantic_edges()
        temp  = self.build_temporal_chain()
        imp   = self.build_impact_propagation_edges()
        caus  = self.build_causal_hypothesis_edges()

        return {
            "modules_added":     modules_added,
            "config_added":      config_added,
            "verifiers_added":   verifiers_added,
            "endpoints_added":   endpoints_added,
            "edges_added":       edges_added + intel.get("edges_added", 0),
            "intelligent_edges": intel.get("edges_added", 0),
            "deep_edges":        sum(v for k, v in deep.items() if "edges" in k),
            "semantic_edges":    sem.get("semantic_edges_added", 0),
            "temporal_edges":    temp.get("temporal_edges_added", 0),
            "epoch_nodes":       temp.get("epoch_nodes_added", 0),
            "metric_nodes":      imp.get("metric_nodes_added", 0),
            "impact_edges":      imp.get("impact_edges_added", 0),
            "causal_edges":      caus.get("causal_edges_added", 0),
        }

    # ------------------------------------------------------------------
    # Deep Relationship Builder (Phase-4 KGE Intelligence Expansion)
    # ------------------------------------------------------------------

    _CONFIG_FTD_MAP = {
        "TRAIL_ATR_MULT":          "FTD-033",
        "BREAKEVEN_TRIGGER_R":     "FTD-033",
        "GENOME_MIN_AVG_R":        "FTD-034",
        "GENOME_PROMOTE_WIN_RATE": "FTD-034",
        "LCC_MAX_CONSECUTIVE":     "FTD-035",
        "RSI_FLOOR":               "FTD-036",
        "MAX_DRAWDOWN_HALT":       "FTD-037",
        "RL_EXPLORATION_RATE":     "FTD-038",
        "MIN_SCORE":               "FTD-039",
        "ALPHA_BOOST_MULT":        "FTD-040",
    }

    _VERIFIER_MODULE_MAP = {
        "hke":        "hke_engine",
        "doae":       "doae_engine",
        "kge":        "kge_engine",
        "governance": "governance_intelligence",
        "rl_engine":  "rl_engine",
        "genome":     "genome_engine",
    }

    def build_deep_relationships(self) -> dict:
        """
        Phase-4 KGE Intelligence Expansion.

        Adds 5 categories of new edges beyond build_intelligent_relationships():
          1. ENDPOINT→MODULE (CALLS): route path keywords → module nodes
          2. CONFIG→FTD (INTRODUCED_BY): hardcoded param→FTD mapping
          3. VERIFIER→MODULE (TESTS): verifier filename → module it covers
          4. DECISION→DECISION (SUPERSEDES): known supersession pairs
          5. ROADMAP nodes with PRECEDES and BLOCKS edges

        Idempotent — INSERT OR IGNORE on all nodes and edges.
        Returns dict with per-category edge counts.
        """
        results: dict = {
            "endpoint_module_edges": 0,
            "config_ftd_edges": 0,
            "verifier_module_edges": 0,
            "decision_supersedes_edges": 0,
            "roadmap_nodes_added": 0,
            "roadmap_edges_added": 0,
        }

        # 1. ENDPOINT→MODULE (CALLS)
        with self._connect() as con:
            endpoint_rows = con.execute(
                "SELECT node_id, label, data FROM kg_nodes WHERE node_type='ENDPOINT'"
            ).fetchall()
            module_ids = [r[0] for r in con.execute(
                "SELECT node_id FROM kg_nodes WHERE node_type='MODULE'"
            ).fetchall()]

        _route_module_hints = [
            ("doae",       "doae"),
            ("kge",        "kge"),
            ("nexus/rl",   "rl_engine"),
            ("hke",        "hke"),
            ("genome",     "genome"),
            ("imraf",      "imraf"),
            ("governance", "governance"),
            ("ema",        "ema"),
            ("aeos",       "aeos"),
            ("dial",       "dial"),
            ("dcel",       "dcel"),
            ("iq",         "iq"),
        ]
        for ep_id, ep_label, _data in endpoint_rows:
            route = ep_label.lower()
            for keyword, stem in _route_module_hints:
                if keyword in route:
                    for mod_id in module_ids:
                        if stem in mod_id.lower():
                            if self.add_edge(ep_id, mod_id, "CALLS"):
                                results["endpoint_module_edges"] += 1

        # 2. CONFIG→FTD (INTRODUCED_BY)
        with self._connect() as con:
            config_rows = con.execute(
                "SELECT node_id, label FROM kg_nodes WHERE node_type='CONFIG'"
            ).fetchall()
            ftd_ids = {r[0] for r in con.execute(
                "SELECT node_id FROM kg_nodes WHERE node_type='FTD'"
            ).fetchall()}

        for param_name, ftd_id in self._CONFIG_FTD_MAP.items():
            if ftd_id not in ftd_ids:
                continue
            for cfg_id, cfg_label in config_rows:
                if param_name.upper() in cfg_label.upper() or cfg_id.upper() == param_name.upper():
                    if self.add_edge(cfg_id, ftd_id, "INTRODUCED_BY"):
                        results["config_ftd_edges"] += 1

        # 3. VERIFIER→MODULE (TESTS)
        with self._connect() as con:
            verifier_rows = con.execute(
                "SELECT node_id FROM kg_nodes WHERE node_type='VERIFIER'"
            ).fetchall()
            module_ids_now = [r[0] for r in con.execute(
                "SELECT node_id FROM kg_nodes WHERE node_type='MODULE'"
            ).fetchall()]

        for (ver_id,) in verifier_rows:
            ver_stem = ver_id.lower()
            for pattern, mod_name in self._VERIFIER_MODULE_MAP.items():
                if pattern in ver_stem:
                    for mod_id in module_ids_now:
                        if mod_name in mod_id.lower():
                            if self.add_edge(ver_id, mod_id, "TESTS"):
                                results["verifier_module_edges"] += 1
                            break

        # 4. DECISION→DECISION (SUPERSEDES) — only when both nodes exist
        with self._connect() as con:
            decision_ids = {
                r[0] for r in con.execute(
                    "SELECT node_id FROM kg_nodes WHERE node_type='DECISION'"
                ).fetchall()
            }
        _supersedes_pairs = [
            ("DECISION:PBE_REENABLE", "DECISION:PBE_DISABLE"),
        ]
        for newer, older in _supersedes_pairs:
            if newer in decision_ids and older in decision_ids:
                if self.add_edge(newer, older, "SUPERSEDES"):
                    results["decision_supersedes_edges"] += 1

        # 5. ROADMAP nodes + PRECEDES chain + BLOCKS edges
        _roadmap_phases = [
            ("PHASE-1", "PHASE-1: Evidence Foundation",       "IN_PROGRESS"),
            ("PHASE-2", "PHASE-2: Historical Reconstruction",  "IN_PROGRESS"),
            ("PHASE-3", "PHASE-3: Attribution Truth",          "PENDING"),
            ("PHASE-4", "PHASE-4: KGE Intelligence",           "IN_PROGRESS"),
            ("PHASE-5", "PHASE-5: Confidence Engine",          "PENDING"),
            ("PHASE-6", "PHASE-6: Governance Completeness",    "PENDING"),
            ("PHASE-7", "PHASE-7: AEG Readiness",              "PENDING"),
        ]
        phase_ids = []
        for phase_id, label, status in _roadmap_phases:
            if self.add_node("ROADMAP", phase_id, label, {"status": status, "program": "FTD-NEXUS-100-PERCENT-001"}):
                results["roadmap_nodes_added"] += 1
            phase_ids.append(phase_id)

        for i in range(len(phase_ids) - 1):
            if self.add_edge(phase_ids[i], phase_ids[i + 1], "PRECEDES"):
                results["roadmap_edges_added"] += 1

        with self._connect() as con:
            aeg_row = con.execute(
                "SELECT node_id FROM kg_nodes WHERE node_id LIKE '%AEG%' LIMIT 1"
            ).fetchone()
        if aeg_row:
            aeg_id = aeg_row[0]
            for blocker in ("PHASE-3", "PHASE-7"):
                if self.add_edge(blocker, aeg_id, "BLOCKS"):
                    results["roadmap_edges_added"] += 1

        total_edges = sum(v for k, v in results.items() if "edges" in k)
        logger.info(
            "KGE build_deep_relationships: %d total new edges, %d roadmap nodes",
            total_edges, results["roadmap_nodes_added"],
        )
        return results

    # ------------------------------------------------------------------
    # Phase-5: Semantic, Temporal, Impact, and Causal Intelligence
    # ------------------------------------------------------------------

    def build_semantic_edges(self) -> dict:
        """
        For every MODULE, FTD, and STRATEGY node, tokenize the label into
        lowercase words and match against _NEXUS_KEYWORDS. Any pair of nodes
        that share at least 1 keyword gets a RELATED_TO edge weighted by the
        shared keyword count.
        """
        with self._connect() as con:
            rows = con.execute(
                "SELECT node_id, label FROM kg_nodes "
                "WHERE node_type IN ('MODULE','FTD','STRATEGY')"
            ).fetchall()

        keyword_set = set(_NEXUS_KEYWORDS)

        # Build per-node keyword sets
        node_keywords: dict = {}
        for node_id, label in rows:
            tokens = set(label.lower().replace("-", " ").replace("_", " ").split())
            matched = tokens & keyword_set
            if matched:
                node_keywords[node_id] = matched

        node_list = list(node_keywords.items())
        edges_added = 0
        for i in range(len(node_list)):
            nid_a, kws_a = node_list[i]
            for j in range(i + 1, len(node_list)):
                nid_b, kws_b = node_list[j]
                shared = kws_a & kws_b
                if shared:
                    weight = float(len(shared))
                    if self.add_edge(nid_a, nid_b, "RELATED_TO", weight=weight):
                        edges_added += 1

        logger.info("KGE build_semantic_edges: %d edges added", edges_added)
        return {"semantic_edges_added": edges_added}

    def build_temporal_chain(self) -> dict:
        """
        Connect FTDs in deployment order with PRECEDED_BY edges.
        Also create EPOCH cluster nodes and link FTDs to their epoch.
        """
        temporal_edges_added = 0
        epoch_nodes_added = 0

        # Add PRECEDED_BY edges between consecutive FTDs that exist in the graph
        with self._connect() as con:
            existing = {r[0] for r in con.execute(
                "SELECT node_id FROM kg_nodes WHERE node_type='FTD'"
            ).fetchall()}

        ordered = [fid for fid in _FTD_TEMPORAL_ORDER if fid in existing]
        for i in range(len(ordered) - 1):
            if self.add_edge(ordered[i], ordered[i + 1], "PRECEDED_BY"):
                temporal_edges_added += 1

        # EPOCH nodes grouping
        _epochs = [
            ("NEXUS_ERA_1", "NEXUS Era 1: Foundation FTDs 033-040", ["FTD-033", "FTD-034", "FTD-035", "FTD-036", "FTD-037", "FTD-038", "FTD-039", "FTD-040"]),
            ("NEXUS_ERA_2", "NEXUS Era 2: Acceleration", ["FTD-NEXUS-ACCEL-001", "FTD-057"]),
        ]
        for epoch_id, epoch_label, member_ftds in _epochs:
            if self.add_node("EPOCH", epoch_id, epoch_label):
                epoch_nodes_added += 1
            for ftd_id in member_ftds:
                if ftd_id in existing:
                    if self.add_edge(ftd_id, epoch_id, "BELONGS_TO"):
                        temporal_edges_added += 1

        logger.info(
            "KGE build_temporal_chain: %d temporal edges, %d epoch nodes",
            temporal_edges_added, epoch_nodes_added,
        )
        return {"temporal_edges_added": temporal_edges_added, "epoch_nodes_added": epoch_nodes_added}

    def build_impact_propagation_edges(self) -> dict:
        """
        Add METRIC nodes and connect FTDs and STRATEGYs to the metrics they influence.
        Edge type: INFLUENCES.
        """
        _metric_labels = {
            "win_rate":               "Win Rate",
            "profit_factor":          "Profit Factor",
            "drawdown":               "Drawdown",
            "avg_pnl":                "Average PnL",
            "trade_frequency":        "Trade Frequency",
            "hold_time":              "Hold Time",
            "context_amplification":  "Context Amplification",
        }

        metric_nodes_added = 0
        for metric_id, metric_label in _metric_labels.items():
            if self.add_node("METRIC", metric_id, metric_label):
                metric_nodes_added += 1

        impact_edges_added = 0

        # FTD → METRIC edges
        with self._connect() as con:
            existing_ftds = {r[0] for r in con.execute(
                "SELECT node_id FROM kg_nodes WHERE node_type='FTD'"
            ).fetchall()}

        for ftd_id, metrics in _FTD_METRIC_MAP.items():
            if ftd_id not in existing_ftds:
                continue
            for metric_id in metrics:
                if self.add_edge(ftd_id, metric_id, "INFLUENCES"):
                    impact_edges_added += 1

        # STRATEGY → METRIC edges — known connections
        _strategy_metric_map = {
            "TrendFollowing":      ["win_rate", "hold_time", "profit_factor"],
            "MeanReversion":       ["win_rate", "trade_frequency", "avg_pnl"],
            "VolatilityExpansion": ["drawdown", "trade_frequency"],
        }
        with self._connect() as con:
            existing_strategies = {r[0] for r in con.execute(
                "SELECT node_id FROM kg_nodes WHERE node_type='STRATEGY'"
            ).fetchall()}

        for strat_id, metrics in _strategy_metric_map.items():
            if strat_id not in existing_strategies:
                continue
            for metric_id in metrics:
                if self.add_edge(strat_id, metric_id, "INFLUENCES"):
                    impact_edges_added += 1

        logger.info(
            "KGE build_impact_propagation_edges: %d metric nodes, %d impact edges",
            metric_nodes_added, impact_edges_added,
        )
        return {"metric_nodes_added": metric_nodes_added, "impact_edges_added": impact_edges_added}

    def build_causal_hypothesis_edges(self) -> dict:
        """
        Add CAUSAL_HYPOTHESIS edges for known FTD→METRIC causal beliefs.
        Weaker than CAUSES but stronger than RELATED_TO — explicitly probabilistic.
        """
        with self._connect() as con:
            existing_nodes = {r[0] for r in con.execute("SELECT node_id FROM kg_nodes").fetchall()}

        causal_edges_added = 0
        for source_id, target_id, hypothesis in _CAUSAL_HYPOTHESES:
            if source_id not in existing_nodes or target_id not in existing_nodes:
                continue
            if self.add_edge(
                source_id, target_id, "CAUSAL_HYPOTHESIS",
                weight=0.65,
                data={"hypothesis": hypothesis, "confidence": 0.65},
            ):
                causal_edges_added += 1

        logger.info("KGE build_causal_hypothesis_edges: %d causal edges added", causal_edges_added)
        return {"causal_edges_added": causal_edges_added}


# Singleton — lazy so tests can override db_path
kge = KGEEngine()
