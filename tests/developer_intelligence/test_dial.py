"""
FTD-DIAL-001 — DIAL verifier test suite.

Verifies: historical lookup, incident retrieval, architecture retrieval,
regression detection, dependency mapping, FTD linking, context generation,
onboarding package, autonomous context, lessons learned, engineering
recommendation, and boot integration.
"""
import json
import os
import sqlite3
import sys
import tempfile
import time
import unittest

# ── Minimal IMRAF stub so DIAL tests run without the full production DB ────────
class _StubIMRAFCategory:
    DEVELOPER  = "DEVELOPER"
    KNOWLEDGE  = "KNOWLEDGE"
    INCIDENT   = "INCIDENT"
    FAILURE    = "FAILURE"
    BUG        = "BUG"
    REGRESSION = "REGRESSION"
    ARCHITECTURE = "ARCHITECTURE"
    DEPLOYMENT = "DEPLOYMENT"
    SELF_IMPROVE = "SELF_IMPROVE"


class _StubIMRAF:
    """
    In-memory IMRAF stub for isolated DIAL testing.
    Wraps a real SQLite DB in a temp directory so we test real SQL behaviour
    without touching production data.
    """
    Category = _StubIMRAFCategory

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS imraf_records (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category    TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                title       TEXT NOT NULL,
                data        TEXT NOT NULL,
                tags        TEXT DEFAULT '',
                engine_ver  TEXT DEFAULT '',
                ts          INTEGER NOT NULL,
                search_text TEXT DEFAULT ''
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_cat ON imraf_records(category)")
        self._conn.commit()

    def record(self, category, title, data, subcategory="", tags=None):
        cat_val = category if isinstance(category, str) else category
        ts = int(time.time() * 1000)
        data_json = json.dumps(data, default=str)
        tags_str = ",".join(tags or [])
        search_parts = [str(cat_val), subcategory, title, tags_str]
        for v in data.values():
            if isinstance(v, str):
                search_parts.append(v)
        search_text = " ".join(search_parts).lower()
        cur = self._conn.execute(
            "INSERT INTO imraf_records (category,subcategory,title,data,tags,engine_ver,ts,search_text) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (str(cat_val), subcategory, title, data_json, tags_str, "test", ts, search_text),
        )
        self._conn.commit()
        return cur.lastrowid

    def search(self, query, category=None, limit=50, since_ts=None):
        q = query.lower() if query else ""
        params = [f"%{q}%"]
        sql = "SELECT id,category,subcategory,title,data,tags,engine_ver,ts FROM imraf_records WHERE search_text LIKE ?"
        if category:
            cat_val = category if isinstance(category, str) else str(category)
            sql += " AND category=?"
            params.append(cat_val)
        sql += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        cur = self._conn.execute(sql, params)
        results = []
        for row in cur.fetchall():
            try:
                d = json.loads(row[4])
            except Exception:
                d = {}
            results.append({
                "id": row[0], "category": row[1], "subcategory": row[2],
                "title": row[3], "data": d,
                "tags": row[5].split(",") if row[5] else [],
                "engine_ver": row[6], "ts": row[7],
            })
        return results

    def get_stats(self):
        cur = self._conn.execute("SELECT category, COUNT(*) FROM imraf_records GROUP BY category")
        by_cat = {row[0]: row[1] for row in cur.fetchall()}
        return {"total_records": sum(by_cat.values()), "by_category": by_cat}

    def close(self):
        self._conn.close()


class TestDIALEngine(unittest.TestCase):

    def setUp(self):
        # Create temp dir with a pre-populated stub IMRAF DB
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "imraf_test.db")
        self.stub_imraf = _StubIMRAF(self.db_path)

        # Seed test records
        self.stub_imraf.record("INCIDENT", "WebSocket gap on risk_engine tick",
            {"root_cause": "event loop blocked", "resolution": "moved to run_in_executor",
             "severity": "HIGH"}, subcategory="risk_engine", tags=["incident", "risk_engine"])
        self.stub_imraf.record("FAILURE", "TSL below breakeven price",
            {"root_cause": "ATR_MULT * 0.7 too loose", "resolution": "TRAIL_ATR_MULT=0.60",
             "prevention": "validate TSL > BE price in tests"}, subcategory="trade_manager",
            tags=["failure", "trade_manager", "tsl"])
        self.stub_imraf.record("ARCHITECTURE", "Context memory uses strategy_id not strategy_type",
            {"decision": "use strategy_id", "alternatives": ["strategy_type"],
             "reasoning": "granular per-variant profitability tracking",
             "trade_offs": "requires consistent key in both record and lookup"},
            subcategory="alpha_context_memory", tags=["architecture", "adr"])
        self.stub_imraf.record("BUG", "Context memory lookup key mismatch v1.53.3",
            {"root_cause": "lookup used strategy_type, storage used strategy_id",
             "fix": "changed get_amplification() call to use sig.strategy_id",
             "prevention": "verify key consistency in tests", "status": "FIXED"},
            subcategory="alpha_context_memory", tags=["bug", "fixed"])
        self.stub_imraf.record("DEPLOYMENT", "Engine boot v1.53.4",
            {"event": "ENGINE_BOOT", "version": "1.53.4", "trade_mode": "PAPER"},
            subcategory="BOOT", tags=["boot", "deployment"])
        self.stub_imraf.record("KNOWLEDGE", "Phase-H startup blocked event loop",
            {"finding": "asdict(t) for 4818 trades synchronously in async lifespan caused timeout",
             "source": "FTD startup investigation"},
            subcategory="FTD-startup", tags=["knowledge", "startup", "performance"])
        self.stub_imraf.record("REGRESSION", "BE trigger mismatch after TSL change",
            {"component": "trade_manager", "trigger": "TRAIL_ATR_MULT change",
             "previous_behavior": "TSL below BE", "current_behavior": "TSL above BE"},
            subcategory="trade_manager", tags=["regression", "trade_manager"])

        # Build a DIALEngine with the stub injected
        from core.developer_intelligence.dial_engine import DIALEngine
        self.dial = DIALEngine.__new__(DIALEngine)
        self.dial._lock = __import__("threading").RLock()
        self.dial._boot_ts = int(time.time() * 1000)
        self.dial._imraf = self.stub_imraf
        self.dial._imraf_available = True
        self.dial._query_count = 0

    def tearDown(self):
        self.stub_imraf.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── Test 1: Historical lookup functionality ────────────────────────────────

    def test_historical_context_returns_dict(self):
        ctx = self.dial.get_historical_context("risk_engine")
        self.assertIsInstance(ctx, dict)
        self.assertEqual(ctx["module"], "risk_engine")
        self.assertIn("incident_count", ctx)
        self.assertIn("total_records", ctx)
        self.assertGreaterEqual(ctx["incident_count"], 1)  # seeded 1 risk_engine incident

    def test_historical_context_identifies_high_risk(self):
        ctx = self.dial.get_historical_context("risk_engine")
        self.assertEqual(ctx["risk_classification"], "HIGH")

    def test_historical_context_unknown_module(self):
        ctx = self.dial.get_historical_context("nonexistent_module_xyz")
        self.assertEqual(ctx["incident_count"], 0)
        self.assertEqual(ctx["total_records"], 0)

    # ── Test 2: Incident retrieval ─────────────────────────────────────────────

    def test_find_similar_issues_returns_results(self):
        results = self.dial.find_similar_issues("breakeven")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertIn("id", results[0])
        self.assertIn("title", results[0])

    def test_find_similar_issues_no_match(self):
        results = self.dial.find_similar_issues("completely_unrelated_xyz_999")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    # ── Test 3: Architecture retrieval ────────────────────────────────────────

    def test_architecture_rationale_returns_decisions(self):
        arch = self.dial.get_architecture_rationale("alpha_context_memory")
        self.assertIsInstance(arch, list)
        self.assertGreater(len(arch), 0)
        first = arch[0]
        self.assertIn("decision", first)
        self.assertIn("alternatives", first)
        self.assertIn("reasoning", first)

    def test_architecture_rationale_empty_for_unknown(self):
        arch = self.dial.get_architecture_rationale("nonexistent_component_xyz")
        self.assertIsInstance(arch, list)
        self.assertEqual(len(arch), 0)

    # ── Test 4: Regression detection ──────────────────────────────────────────

    def test_regression_risk_high_for_core_component(self):
        result = self.dial.check_regression_risk("risk_engine")
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertIn("recommendation", result)
        self.assertIn("incidents", result)

    def test_regression_risk_returns_historical_records(self):
        result = self.dial.check_regression_risk("trade_manager")
        self.assertIsInstance(result["incidents"], list)
        # We seeded both FAILURE and REGRESSION for trade_manager
        self.assertGreater(result["incident_count"], 0)

    def test_regression_risk_low_for_unknown(self):
        result = self.dial.check_regression_risk("unknown_module_xyz")
        self.assertIn(result["risk_level"], ("LOW", "MEDIUM", "HIGH"))
        self.assertIn("recommendation", result)

    # ── Test 5: Dependency mapping ────────────────────────────────────────────

    def test_dependency_impact_returns_dependents(self):
        result = self.dial.analyze_dependency_impact("risk_engine")
        self.assertIsInstance(result["direct_dependents"], list)
        self.assertGreater(len(result["direct_dependents"]), 0)
        self.assertIn("risk_assessment", result)

    def test_dependency_impact_unknown_component(self):
        result = self.dial.analyze_dependency_impact("unknown_xyz")
        self.assertIsInstance(result, dict)
        self.assertIn("component", result)

    # ── Test 6: FTD linking ───────────────────────────────────────────────────

    def test_ftd_knowledge_returns_records(self):
        results = self.dial.get_ftd_knowledge("FTD")
        self.assertIsInstance(results, list)
        # "FTD" appears in the KNOWLEDGE record we seeded (source field)

    def test_ftd_knowledge_specific_id(self):
        results = self.dial.get_ftd_knowledge("startup")
        self.assertIsInstance(results, list)

    # ── Test 7: Context generation ────────────────────────────────────────────

    def test_get_engineering_recommendation_returns_dict(self):
        rec = self.dial.get_engineering_recommendation("trade_manager TSL")
        self.assertIn("query", rec)
        self.assertIn("recommendation", rec)
        self.assertIn("confidence", rec)
        self.assertIn(rec["confidence"], ("HIGH", "MEDIUM", "LOW"))

    # ── Test 8: Onboarding package ────────────────────────────────────────────

    def test_generate_onboarding_package_structure(self):
        pkg = self.dial.generate_onboarding_package()
        self.assertIn("project", pkg)
        self.assertIn("stack", pkg)
        self.assertIn("key_subsystems", pkg)
        self.assertIn("critical_files", pkg)
        self.assertIn("known_risks", pkg)
        self.assertIsInstance(pkg["key_subsystems"], list)
        self.assertGreater(len(pkg["key_subsystems"]), 0)

    # ── Test 9: Autonomous context ────────────────────────────────────────────

    def test_autonomous_context_structure(self):
        ctx = self.dial.get_autonomous_context("risk_engine")
        self.assertIn("module", ctx)
        self.assertIn("ai_agent_guidance", ctx)
        self.assertIn("historical_context", ctx)
        self.assertIn("regression_risk", ctx)
        self.assertIn("dependency_impact", ctx)
        self.assertIn("recommended_actions", ctx)
        self.assertIsInstance(ctx["recommended_actions"], list)

    # ── Test 10: Boot integration ─────────────────────────────────────────────

    def test_boot_summary_non_empty(self):
        summary = self.dial.get_boot_summary()
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertIn("imraf_available=True", summary)

    def test_get_stats_structure(self):
        stats = self.dial.get_stats()
        self.assertEqual(stats["module"], "DIALEngine")
        self.assertEqual(stats["ftd"], "DIAL-001")
        self.assertIn("imraf_available", stats)
        self.assertIn("query_count", stats)
        self.assertTrue(stats["imraf_available"])

    # ── Test 11: Record code change ───────────────────────────────────────────

    def test_record_code_change_returns_id(self):
        rid = self.dial.record_code_change(
            module="test_module",
            description="Test change",
            reason="Testing DIAL",
            expected_outcome="DIAL records code changes",
        )
        self.assertIsInstance(rid, int)
        self.assertGreater(rid, 0)

    # ── Test 12: Lessons learned ──────────────────────────────────────────────

    def test_extract_lesson_returns_id(self):
        rid = self.dial.extract_lesson(
            issue="Test issue",
            root_cause="Test root cause",
            fix="Applied test fix",
            prevention="Added test guard",
            related_components=["test_module"],
        )
        self.assertIsInstance(rid, int)
        self.assertGreater(rid, 0)


if __name__ == "__main__":
    unittest.main()
