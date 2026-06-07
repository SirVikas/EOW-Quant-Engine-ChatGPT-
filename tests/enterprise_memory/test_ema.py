"""
FTD-EMA-001 — Enterprise Memory Architecture test suite.

Validates all 14 EMA modules using the same isolated stub pattern
as test_dial.py and test_aeos.py.
"""
import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest


# ── Stub infrastructure ────────────────────────────────────────────────────────

class _StubIMRAF:
    class Category:
        pass

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS imraf_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL, subcategory TEXT DEFAULT '',
                title TEXT NOT NULL, data TEXT NOT NULL,
                tags TEXT DEFAULT '', engine_ver TEXT DEFAULT '',
                ts INTEGER NOT NULL, search_text TEXT DEFAULT ''
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_cat ON imraf_records(category)")
        self._conn.commit()

    def record(self, category, title, data, subcategory="", tags=None):
        cat_val = category if isinstance(category, str) else str(category)
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
        q = (query or "").lower()
        params = [f"%{q}%"]
        sql = ("SELECT id,category,subcategory,title,data,tags,engine_ver,ts "
               "FROM imraf_records WHERE search_text LIKE ?")
        if category:
            sql += " AND category=?"
            params.append(str(category))
        sql += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        rows = []
        for row in self._conn.execute(sql, params).fetchall():
            try:
                d = json.loads(row[4])
            except Exception:
                d = {}
            rows.append({"id": row[0], "category": row[1], "subcategory": row[2],
                         "title": row[3], "data": d,
                         "tags": row[5].split(",") if row[5] else [],
                         "engine_ver": row[6], "ts": row[7]})
        return rows

    def timeline(self, category=None, limit=100):
        return self.search("", category=category, limit=limit)

    def get_stats(self):
        cur = self._conn.execute(
            "SELECT category, COUNT(*) FROM imraf_records GROUP BY category"
        )
        by_cat = {row[0]: row[1] for row in cur.fetchall()}
        return {"total_records": sum(by_cat.values()), "by_category": by_cat,
                "db_path": ":memory:"}

    def close(self):
        self._conn.close()


def _make_dial(stub):
    from core.developer_intelligence.dial_engine import DIALEngine
    d = DIALEngine.__new__(DIALEngine)
    d._lock = threading.RLock()
    d._boot_ts = int(time.time() * 1000)
    d._imraf = stub
    d._imraf_available = True
    d._query_count = 0
    return d


def _make_aeos(stub, dial):
    from core.aeos.aeos_engine import AEOSEngine
    a = AEOSEngine.__new__(AEOSEngine)
    a._lock = threading.RLock()
    a._boot_ts = int(time.time() * 1000)
    a._assembly_count = 0
    a._dial = dial
    a._imraf = stub
    a._available = True
    return a


def _make_ema(stub, dial, aeos):
    from core.ema.ema_engine import EMAEngine
    e = EMAEngine.__new__(EMAEngine)
    e._lock = threading.RLock()
    e._boot_ts = int(time.time() * 1000)
    e._query_count = 0
    e._audit_log = []
    e._dial = dial
    e._imraf = stub
    e._aeos = aeos
    e._available = True
    return e


class TestEMAEngine(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.stub = _StubIMRAF(os.path.join(self.tmpdir, "ema_test.db"))

        # Seed records across all major categories
        self.stub.record("INCIDENT", "WebSocket gap on risk_engine",
            {"root_cause": "event loop blocked", "resolution": "run_in_executor",
             "severity": "HIGH"}, subcategory="risk_engine", tags=["incident"])
        self.stub.record("FAILURE", "TSL below breakeven",
            {"root_cause": "ATR_MULT too loose", "resolution": "TRAIL_ATR_MULT=0.60"},
            subcategory="trade_manager", tags=["failure"])
        self.stub.record("ARCHITECTURE", "strategy_id as context key",
            {"decision": "use strategy_id", "alternatives": ["strategy_type"],
             "reasoning": "granular tracking", "trade_offs": "consistent key required"},
            subcategory="alpha_context_memory", tags=["architecture"])
        self.stub.record("REGRESSION", "BE mismatch after TSL change",
            {"component": "trade_manager", "trigger": "TRAIL_ATR_MULT change",
             "previous_behavior": "TSL below BE", "current_behavior": "TSL above BE"},
            subcategory="trade_manager", tags=["regression"])
        self.stub.record("FTD", "FTD-IMR-001: Institutional Memory",
            {"ftd_id": "FTD-IMR-001", "status": "DELIVERED",
             "delivered_by": "claude", "completion_date": "2026-06-07",
             "verification_result": "31 tests pass"},
            subcategory="FTD-IMR-001", tags=["ftd", "delivered"])
        self.stub.record("VERIFIER", "test_imraf.py run",
            {"verifier_name": "test_imraf.py", "passed_tests": 31, "failed_tests": 0,
             "pass_rate": 100.0, "coverage": 90.0, "confidence": "HIGH",
             "component": "imraf_engine"},
            subcategory="imraf_engine", tags=["verifier"])
        self.stub.record("GOVERNANCE", "ALPHA_TCB_v1 disabled",
            {"decision": "disable ALPHA_TCB_v1", "rationale": "excessive drawdown",
             "impact": "reduced trade frequency", "category_type": "DISABLE"},
            subcategory="DISABLE", tags=["governance"])
        self.stub.record("KNOWLEDGE", "Phase-H startup blocked event loop",
            {"finding": "asdict for 4818 trades blocked async lifespan",
             "source": "FTD startup investigation"},
            subcategory="FTD-startup", tags=["knowledge", "lesson"])
        self.stub.record("DEPLOYMENT", "Engine boot v1.54.0",
            {"event": "BOOT", "version": "1.54.0", "trade_mode": "PAPER"},
            subcategory="BOOT", tags=["boot", "deployment"])

        self.dial = _make_dial(self.stub)
        self.aeos = _make_aeos(self.stub, self.dial)
        self.ema  = _make_ema(self.stub, self.dial, self.aeos)

    def tearDown(self):
        self.stub.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── Module 1: AI Abstraction ──────────────────────────────────────────────

    def test_ai_abstraction_status_structure(self):
        result = self.ema.get_ai_abstraction_status()
        self.assertIn("principle", result)
        self.assertIn("supported_consumers", result)
        self.assertIn("standard_interfaces", result)
        self.assertTrue(result["vendor_independence"])

    def test_ai_abstraction_consumers_list(self):
        result = self.ema.get_ai_abstraction_status()
        consumers = result["supported_consumers"]
        self.assertIsInstance(consumers, list)
        self.assertGreater(len(consumers), 4)
        self.assertIn("Claude", consumers)
        self.assertIn("ChatGPT", consumers)

    # ── Module 2 + 8: Context Assembly + AI Package ───────────────────────────

    def test_generate_ai_context_package_status_ok(self):
        pkg = self.ema.generate_ai_context_package("fix TSL", "trade_manager")
        self.assertEqual(pkg["status"], "OK")

    def test_generate_ai_context_package_required_keys(self):
        pkg = self.ema.generate_ai_context_package("fix TSL", "trade_manager")
        for key in ("ema_version", "ai_consumer", "task", "module",
                    "project_overview", "roadmap_state", "module_context",
                    "similar_past_issues", "required_tests",
                    "recommended_actions", "permanent_known_risks"):
            self.assertIn(key, pkg, f"Missing key: {key}")

    def test_generate_ai_context_package_vendor_neutral(self):
        pkg = self.ema.generate_ai_context_package("refactor", "risk_engine")
        self.assertTrue(pkg["vendor_neutral"])

    def test_generate_ai_context_package_no_module(self):
        pkg = self.ema.generate_ai_context_package("general engineering task")
        self.assertEqual(pkg["status"], "OK")
        self.assertEqual(pkg["module"], "GENERAL")

    def test_generate_ai_context_package_degraded(self):
        from core.ema.ema_engine import EMAEngine
        deg = EMAEngine.__new__(EMAEngine)
        deg._lock = threading.RLock()
        deg._boot_ts = int(time.time() * 1000)
        deg._query_count = 0
        deg._audit_log = []
        deg._dial = deg._imraf = deg._aeos = None
        deg._available = False
        pkg = deg.generate_ai_context_package("task", "module")
        self.assertEqual(pkg["status"], "DEGRADED")

    # ── Module 3: Project Knowledge Core ─────────────────────────────────────

    def test_project_knowledge_required_keys(self):
        result = self.ema.get_project_knowledge()
        for key in ("project", "stack", "vision", "operating_principles",
                    "governance_rules", "critical_components",
                    "known_permanent_risks", "ftd_registry"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_project_knowledge_principles_is_list(self):
        result = self.ema.get_project_knowledge()
        self.assertIsInstance(result["operating_principles"], list)
        self.assertGreater(len(result["operating_principles"]), 3)

    def test_project_knowledge_ftd_registry_contains_ema(self):
        result = self.ema.get_project_knowledge()
        registry_str = " ".join(result["ftd_registry"])
        self.assertIn("EMA-001", registry_str)

    # ── Module 4: FTD Knowledge Hub ──────────────────────────────────────────

    def test_ftd_hub_structure(self):
        result = self.ema.get_ftd_hub()
        self.assertIn("ftd_records", result)
        self.assertIn("registry", result)
        self.assertIn("total_found", result)
        self.assertIsInstance(result["ftd_records"], list)

    def test_ftd_hub_finds_seeded_record(self):
        result = self.ema.get_ftd_hub("IMR-001")
        self.assertGreater(result["total_found"], 0)

    def test_ftd_hub_record_has_lifecycle_fields(self):
        result = self.ema.get_ftd_hub("IMR-001")
        if result["ftd_records"]:
            rec = result["ftd_records"][0]
            for field in ("status", "delivered_by", "completion_date",
                          "verification_result", "rollback_history"):
                self.assertIn(field, rec)

    # ── Module 5: Verifier Intelligence Hub ──────────────────────────────────

    def test_verifier_hub_structure(self):
        result = self.ema.get_verifier_hub()
        for key in ("verifier_records", "recommended_verifiers",
                    "run_command", "total_records"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_verifier_hub_finds_seeded_run(self):
        result = self.ema.get_verifier_hub("imraf_engine")
        self.assertGreater(result["total_records"], 0)
        self.assertGreater(result["verifier_records"][0]["pass_rate"], 0)

    def test_verifier_hub_pass_rate_present(self):
        result = self.ema.get_verifier_hub("imraf_engine")
        if result["verifier_records"]:
            self.assertIn("pass_rate", result["verifier_records"][0])

    # ── Module 6: Architecture Knowledge Graph ────────────────────────────────

    def test_knowledge_graph_structure(self):
        result = self.ema.get_knowledge_graph("trade_manager")
        self.assertIn("module", result)
        self.assertIn("relationships", result)
        self.assertIn("graph_stats", result)
        self.assertIn("all_registered_modules", result)

    def test_knowledge_graph_known_module(self):
        result = self.ema.get_knowledge_graph("trade_manager")
        rel = result["relationships"]
        self.assertIn("related_incidents", rel)
        self.assertIn("related_modules", rel)
        self.assertIn("related_ftds", rel)

    def test_knowledge_graph_all_modules_list(self):
        result = self.ema.get_knowledge_graph("risk_engine")
        self.assertIn("risk_engine", result["all_registered_modules"])
        self.assertIn("trade_manager", result["all_registered_modules"])

    def test_knowledge_graph_unknown_module_returns_empty_relationships(self):
        result = self.ema.get_knowledge_graph("nonexistent_xyz")
        self.assertEqual(result["relationships"], {})

    # ── Module 7: Roadmap Intelligence ───────────────────────────────────────

    def test_roadmap_state_structure(self):
        result = self.ema.get_roadmap_state()
        self.assertEqual(result["status"], "OK")
        for key in ("where_are_we", "what_was_completed", "what_is_pending",
                    "what_should_happen_next", "ftd_registry"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_roadmap_state_where_are_we_keys(self):
        result = self.ema.get_roadmap_state()
        where = result["where_are_we"]
        for key in ("completed_ftds", "in_progress_ftds", "planned_ftds",
                    "open_incidents"):
            self.assertIn(key, where)

    def test_roadmap_state_next_steps_is_list(self):
        result = self.ema.get_roadmap_state()
        self.assertIsInstance(result["what_should_happen_next"], list)

    # ── Module 9: Decision Traceability ───────────────────────────────────────

    def test_decision_trail_structure(self):
        result = self.ema.get_decision_trail()
        for key in ("trade_decisions", "architecture_decisions",
                    "governance_decisions", "total_decisions"):
            self.assertIn(key, result)

    def test_decision_trail_arch_decisions_has_reasoning(self):
        result = self.ema.get_decision_trail("strategy_id")
        if result["architecture_decisions"]:
            dec = result["architecture_decisions"][0]
            self.assertIn("reasoning", dec)
            self.assertIn("alternatives", dec)

    def test_decision_trail_governance_has_rationale(self):
        result = self.ema.get_decision_trail("ALPHA_TCB")
        if result["governance_decisions"]:
            gov = result["governance_decisions"][0]
            self.assertIn("rationale", gov)

    # ── Module 10: Lessons Learned ────────────────────────────────────────────

    def test_lessons_learned_structure(self):
        result = self.ema.get_lessons_learned()
        for key in ("lessons", "self_improvements", "meta_learning_observations",
                    "total_lessons"):
            self.assertIn(key, result)

    def test_lessons_learned_is_list(self):
        result = self.ema.get_lessons_learned()
        self.assertIsInstance(result["lessons"], list)

    def test_lessons_learned_finds_knowledge(self):
        result = self.ema.get_lessons_learned("startup")
        # The seeded KNOWLEDGE record "Phase-H startup blocked event loop" should appear
        self.assertGreater(result["total_lessons"], 0)

    # ── Module 11: Multi-AI Compatibility ────────────────────────────────────

    def test_multi_ai_package_has_compatibility_guarantee(self):
        result = self.ema.get_multi_ai_package("fix risk engine", "risk_engine",
                                               consumer="Claude")
        self.assertIn("compatibility_guarantee", result)
        self.assertIn("consumer_instructions", result)

    def test_multi_ai_package_same_output_different_consumers(self):
        pkg_claude = self.ema.get_multi_ai_package("fix TSL", "trade_manager",
                                                   consumer="Claude")
        pkg_gpt    = self.ema.get_multi_ai_package("fix TSL", "trade_manager",
                                                   consumer="ChatGPT")
        # Core knowledge sections must be identical regardless of consumer
        self.assertEqual(
            pkg_claude["project_overview"]["name"],
            pkg_gpt["project_overview"]["name"],
        )
        self.assertEqual(
            pkg_claude["permanent_known_risks"],
            pkg_gpt["permanent_known_risks"],
        )

    def test_multi_ai_package_consumer_instructions_covers_all(self):
        result = self.ema.get_multi_ai_package("task", consumer="Gemini")
        instructions = result["consumer_instructions"]
        for consumer in ("Claude", "ChatGPT", "Gemini", "Copilot"):
            self.assertIn(consumer, instructions)

    # ── Module 12: Governance Audit ───────────────────────────────────────────

    def test_governance_audit_structure(self):
        _ = self.ema.get_ai_abstraction_status()  # generate some audit entries
        result = self.ema.get_governance_audit()
        for key in ("audit_trail", "total_queries", "imraf_integrity",
                    "governance_rules", "integrity_status"):
            self.assertIn(key, result)

    def test_governance_audit_trail_is_list(self):
        result = self.ema.get_governance_audit()
        self.assertIsInstance(result["audit_trail"], list)

    def test_governance_audit_records_queries(self):
        _ = self.ema.get_project_knowledge()
        _ = self.ema.get_ftd_hub()
        result = self.ema.get_governance_audit()
        self.assertGreater(result["total_queries"], 0)

    def test_governance_audit_integrity_status_ok(self):
        result = self.ema.get_governance_audit()
        self.assertEqual(result["integrity_status"], "OK")

    # ── Module 13: Knowledge Health Monitor ──────────────────────────────────

    def test_knowledge_health_structure(self):
        result = self.ema.get_knowledge_health()
        for key in ("overall_health_score", "health_label", "metrics",
                    "recommendations", "checked_ts"):
            self.assertIn(key, result)

    def test_knowledge_health_score_range(self):
        result = self.ema.get_knowledge_health()
        self.assertGreaterEqual(result["overall_health_score"], 0.0)
        self.assertLessEqual(result["overall_health_score"], 100.0)

    def test_knowledge_health_label_valid(self):
        result = self.ema.get_knowledge_health()
        self.assertIn(result["health_label"], ("EXCELLENT", "GOOD", "FAIR", "POOR"))

    def test_knowledge_health_metrics_keys(self):
        result = self.ema.get_knowledge_health()
        metrics = result["metrics"]
        for key in ("coverage", "completeness", "freshness",
                    "link_integrity", "archive_growth"):
            self.assertIn(key, metrics)

    def test_knowledge_health_coverage_has_pct(self):
        result = self.ema.get_knowledge_health()
        coverage = result["metrics"]["coverage"]
        self.assertIn("coverage_pct", coverage)
        self.assertGreaterEqual(coverage["coverage_pct"], 0.0)
        self.assertLessEqual(coverage["coverage_pct"], 100.0)

    # ── Module 14: Engineering Intelligence Dashboard ─────────────────────────

    def test_dashboard_status_ok(self):
        result = self.ema.get_engineering_dashboard()
        self.assertEqual(result["status"], "OK")

    def test_dashboard_required_panels(self):
        result = self.ema.get_engineering_dashboard()
        for key in ("summary", "incident_panel", "roadmap_panel",
                    "verifier_panel", "knowledge_panel", "ftd_registry"):
            self.assertIn(key, result, f"Missing panel: {key}")

    def test_dashboard_summary_keys(self):
        result = self.ema.get_engineering_dashboard()
        summary = result["summary"]
        for key in ("total_institutional_records", "categories_active",
                    "knowledge_health_score", "knowledge_health_label"):
            self.assertIn(key, summary)

    def test_dashboard_incident_panel(self):
        result = self.ema.get_engineering_dashboard()
        panel = result["incident_panel"]
        for key in ("total_incidents", "open_bugs", "regressions"):
            self.assertIn(key, panel)

    def test_dashboard_verifier_panel(self):
        result = self.ema.get_engineering_dashboard()
        panel = result["verifier_panel"]
        self.assertIn("total_verifier_runs", panel)
        self.assertIn("avg_pass_rate_pct", panel)
        # We seeded 1 verifier record with 100% pass rate
        self.assertGreater(panel["total_verifier_runs"], 0)

    # ── Stats & Boot ─────────────────────────────────────────────────────────

    def test_stats_structure(self):
        result = self.ema.get_stats()
        self.assertEqual(result["module"], "EMAEngine")
        self.assertEqual(result["ftd"], "EMA-001")
        self.assertIsInstance(result["available"], bool)
        self.assertEqual(len(result["modules"]), 14)

    def test_boot_summary_string(self):
        s = self.ema.get_boot_summary()
        self.assertIsInstance(s, str)
        self.assertIn("available=True", s)
        self.assertIn("graph_modules=", s)


if __name__ == "__main__":
    unittest.main()
