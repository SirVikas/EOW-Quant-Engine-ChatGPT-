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

    # ------------------------------------------------------------------
    # Intelligent Relationship Builder
    # ------------------------------------------------------------------

    # FTDs that map to specific implementation modules
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

    # Known architectural module→module dependencies
    _MODULE_DEPS = [
        ("alpha_engine",    "net_edge_engine"),
        ("rl_engine",       "alpha_context_memory"),
        ("adaptive_scorer", "rl_engine"),
        ("trade_manager",   "risk_controller"),
        ("genome_engine",   "adaptive_scorer"),
    ]

    def build_intelligent_relationships(self) -> dict:
        """
        Creates semantically meaningful edges between existing graph nodes:

        1. MODULE→CONFIG  (CONFIGURES): module label keywords match config param names
        2. FTD→MODULE     (IMPLEMENTS): _FTD_MODULE_MAP hardcoded mapping
        3. STRATEGY→MODULE (USES): strategies connect to their implementing modules
        4. MODULE→MODULE  (DEPENDS_ON): known architectural dependencies

        Returns a summary dict with edges_added count.
        """
        edges_added = 0

        with self._connect() as con:
            module_rows   = con.execute("SELECT node_id, label FROM kg_nodes WHERE node_type='MODULE'").fetchall()
            config_rows   = con.execute("SELECT node_id, label FROM kg_nodes WHERE node_type='CONFIG'").fetchall()
            ftd_rows      = con.execute("SELECT node_id FROM kg_nodes WHERE node_type='FTD'").fetchall()
            strategy_rows = con.execute("SELECT node_id, label FROM kg_nodes WHERE node_type='STRATEGY'").fetchall()

        # 1. MODULE→CONFIG (CONFIGURES)
        for mod_id, mod_label in module_rows:
            stem = mod_id.split(":")[-1].replace("_", " ").upper()
            keywords = [w for w in stem.split() if len(w) >= 3]
            for cfg_id, cfg_label in config_rows:
                cfg_upper = cfg_label.upper()
                if any(kw in cfg_upper for kw in keywords):
                    if self.add_edge(mod_id, cfg_id, "CONFIGURES"):
                        edges_added += 1

        # 2. FTD→MODULE (IMPLEMENTS)
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

        # 3. STRATEGY→MODULE (USES)
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

        # 4. MODULE→MODULE (DEPENDS_ON)
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
        """
        Returns metrics quantifying how well-connected the knowledge graph is.

        intelligence_score = min(100,
            (avg_edges_per_node / 5) * 50 + (1 - isolated_nodes/total_nodes) * 50)
        """
        with self._connect() as con:
            total_nodes = con.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
            total_edges = con.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
            edge_pairs  = con.execute("SELECT from_node, to_node FROM kg_edges").fetchall()
            node_ids    = [r[0] for r in con.execute("SELECT node_id FROM kg_nodes").fetchall()]

        if total_nodes == 0:
            return {
                "total_nodes": 0, "total_edges": 0, "avg_edges_per_node": 0.0,
                "isolated_nodes": 0, "well_connected": 0, "relationship_density": 0.0,
                "intelligence_score": 0.0, "top_hubs": [],
            }

        edge_counts: dict = {}
        for from_n, to_n in edge_pairs:
            edge_counts[from_n] = edge_counts.get(from_n, 0) + 1
            edge_counts[to_n]   = edge_counts.get(to_n,   0) + 1

        isolated  = sum(1 for nid in node_ids if edge_counts.get(nid, 0) == 0)
        well_conn = sum(1 for nid in node_ids if edge_counts.get(nid, 0) >= 3)
        avg_edges = round(sum(edge_counts.values()) / total_nodes, 4) if total_nodes else 0.0

        max_possible = total_nodes * (total_nodes - 1) / 2
        density = round(total_edges / max_possible, 6) if max_possible > 0 else 0.0

        intel_score = round(
            min(100.0, (avg_edges / 5.0) * 50.0 + (1.0 - isolated / total_nodes) * 50.0),
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
        }

    # ------------------------------------------------------------------
    # Codebase Bootstrap
    # ------------------------------------------------------------------

    def bootstrap_from_codebase(self, root_path: str = ".") -> dict:
        """
        Scan the codebase and add MODULE, CONFIG, VERIFIER, and ENDPOINT nodes.
        Deduplicates via INSERT OR IGNORE (add_node returns False on duplicate).
        Then calls build_intelligent_relationships() to add semantic edges.
        """
        import re
        from pathlib import Path as _Path

        root = _Path(root_path).resolve()
        modules_added   = 0
        config_added    = 0
        verifiers_added = 0
        endpoints_added = 0
        edges_added     = 0

        # MODULE nodes: every .py file under core/ (skip __pycache__)
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

        # CONFIG nodes: parameter names in config.py
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

        # VERIFIER nodes: every .py test file under tests/
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

        # ENDPOINT nodes: @app.get / @app.post decorators in main.py
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
        return {
            "modules_added":     modules_added,
            "config_added":      config_added,
            "verifiers_added":   verifiers_added,
            "endpoints_added":   endpoints_added,
            "edges_added":       edges_added + intel.get("edges_added", 0),
            "intelligent_edges": intel.get("edges_added", 0),
        }


# Singleton — lazy so tests can override db_path
kge = KGEEngine()
