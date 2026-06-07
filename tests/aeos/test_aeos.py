"""
FTD-AEOS-001 — AEOS test suite.

Verifies context assembly, roadmap guidance, change impact forecast,
verifier recommendation, and integration with DIAL's 5 new modules.
"""
import json
import os
import sqlite3
import sys
import tempfile
import time
import threading
import unittest


# ── Minimal IMRAF stub (same pattern as test_dial.py) ─────────────────────────
class _StubIMRAFCategory:
    DEVELOPER = KNOWLEDGE = INCIDENT = FAILURE = BUG = REGRESSION = "stub"
    ARCHITECTURE = DEPLOYMENT = SELF_IMPROVE = FTD = DELIVERY = "stub"
    VERIFIER = GOVERNANCE = "stub"


class _StubIMRAF:
    Category = _StubIMRAFCategory

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

    def timeline(self, category=None, limit=100):
        return self.search("", category=category, limit=limit)

    def get_stats(self):
        cur = self._conn.execute("SELECT category, COUNT(*) FROM imraf_records GROUP BY category")
        by_cat = {row[0]: row[1] for row in cur.fetchall()}
        return {"total_records": sum(by_cat.values()), "by_category": by_cat}

    def close(self):
        self._conn.close()


def _build_dial(stub_imraf):
    from core.developer_intelligence.dial_engine import DIALEngine
    dial = DIALEngine.__new__(DIALEngine)
    dial._lock = threading.RLock()
    dial._boot_ts = int(time.time() * 1000)
    dial._imraf = stub_imraf
    dial._imraf_available = True
    dial._query_count = 0
    return dial


def _build_aeos(stub_imraf, dial):
    from core.aeos.aeos_engine import AEOSEngine
    aeos = AEOSEngine.__new__(AEOSEngine)
    aeos._lock = threading.RLock()
    aeos._boot_ts = int(time.time() * 1000)
    aeos._assembly_count = 0
    aeos._dial = dial
    aeos._imraf = stub_imraf
    aeos._available = True
    return aeos


class TestAEOSEngine(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "aeos_test.db")
        self.stub = _StubIMRAF(self.db_path)

        # Seed records
        self.stub.record("INCIDENT", "WebSocket gap on risk_engine",
            {"root_cause": "event loop blocked", "resolution": "moved to run_in_executor",
             "severity": "HIGH"}, subcategory="risk_engine", tags=["incident", "risk_engine"])
        self.stub.record("FAILURE", "TSL below breakeven price",
            {"root_cause": "ATR_MULT too loose", "resolution": "TRAIL_ATR_MULT=0.60",
             "prevention": "validate TSL > BE price"}, subcategory="trade_manager",
            tags=["failure", "trade_manager"])
        self.stub.record("ARCHITECTURE", "Context memory uses strategy_id",
            {"decision": "use strategy_id", "alternatives": ["strategy_type"],
             "reasoning": "granular per-variant tracking", "trade_offs": "consistent key required"},
            subcategory="alpha_context_memory", tags=["architecture"])
        self.stub.record("REGRESSION", "BE trigger mismatch after TSL change",
            {"component": "trade_manager", "trigger": "TRAIL_ATR_MULT change",
             "previous_behavior": "TSL below BE", "current_behavior": "TSL above BE"},
            subcategory="trade_manager", tags=["regression", "trade_manager"])
        self.stub.record("GOVERNANCE", "ALPHA_TCB_v1 disabled pending volatility review",
            {"decision": "disable ALPHA_TCB_v1", "rationale": "excessive drawdown in ranging regimes",
             "impact": "reduced trade frequency", "category_type": "DISABLE"},
            subcategory="DISABLE", tags=["governance", "disable"])

        self.dial = _build_dial(self.stub)
        self.aeos = _build_aeos(self.stub, self.dial)

    def tearDown(self):
        self.stub.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── Context Assembly ──────────────────────────────────────────────────────

    def test_assemble_context_status_ok(self):
        ctx = self.aeos.assemble_context("fix trailing stop", "trade_manager")
        self.assertEqual(ctx["status"], "OK")

    def test_assemble_context_required_keys(self):
        ctx = self.aeos.assemble_context("fix trailing stop", "trade_manager")
        for key in ("task", "module", "historical_incidents", "similar_past_issues",
                    "architecture_decisions", "dependency_blast_radius",
                    "known_risks", "roadmap_constraints", "verifier_history",
                    "recommended_actions", "assembled_ts"):
            self.assertIn(key, ctx, f"Missing key: {key}")

    def test_assemble_context_recommended_actions_is_list(self):
        ctx = self.aeos.assemble_context("refactor data_lake", "data_lake")
        self.assertIsInstance(ctx["recommended_actions"], list)
        self.assertGreater(len(ctx["recommended_actions"]), 0)

    def test_assemble_context_no_module(self):
        ctx = self.aeos.assemble_context("general query")
        self.assertEqual(ctx["status"], "OK")
        self.assertEqual(ctx["module"], "GENERAL")

    def test_assemble_context_degraded_mode(self):
        from core.aeos.aeos_engine import AEOSEngine
        degraded = AEOSEngine.__new__(AEOSEngine)
        degraded._lock = threading.RLock()
        degraded._boot_ts = int(time.time() * 1000)
        degraded._assembly_count = 0
        degraded._dial = None
        degraded._imraf = None
        degraded._available = False
        ctx = degraded.assemble_context("some task", "some_module")
        self.assertEqual(ctx["status"], "DEGRADED")

    # ── Roadmap Guidance ─────────────────────────────────────────────────────

    def test_roadmap_guidance_status_ok(self):
        result = self.aeos.get_roadmap_guidance()
        self.assertEqual(result["status"], "OK")

    def test_roadmap_guidance_required_keys(self):
        result = self.aeos.get_roadmap_guidance()
        for key in ("recommended_next_steps", "high_risk_modules",
                    "governance_constraints", "generated_ts"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_roadmap_guidance_steps_is_list(self):
        result = self.aeos.get_roadmap_guidance()
        self.assertIsInstance(result["recommended_next_steps"], list)

    # ── Change Impact Forecast ────────────────────────────────────────────────

    def test_forecast_change_impact_structure(self):
        result = self.aeos.forecast_change_impact("trade_manager", "reduce ATR multiplier")
        for key in ("component", "overall_risk", "direct_impact",
                    "required_verifiers", "pre_change_checklist", "forecasted_ts"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_forecast_change_impact_risk_level_valid(self):
        result = self.aeos.forecast_change_impact("trade_manager", "change TSL logic")
        self.assertIn(result["overall_risk"], ("LOW", "MEDIUM", "HIGH"))

    def test_forecast_change_impact_checklist_not_empty(self):
        result = self.aeos.forecast_change_impact("risk_engine", "tweak drawdown threshold")
        self.assertIsInstance(result["pre_change_checklist"], list)
        self.assertGreater(len(result["pre_change_checklist"]), 0)

    # ── Verifier Recommendation ───────────────────────────────────────────────

    def test_recommend_verifiers_structure(self):
        result = self.aeos.recommend_verifiers("trade_manager")
        for key in ("component", "recommended_verifiers", "run_command", "priority"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_recommend_verifiers_is_list(self):
        result = self.aeos.recommend_verifiers("trade_manager")
        self.assertIsInstance(result["recommended_verifiers"], list)
        self.assertGreater(len(result["recommended_verifiers"]), 0)

    def test_recommend_verifiers_run_command_is_string(self):
        result = self.aeos.recommend_verifiers("imraf_engine")
        self.assertIsInstance(result["run_command"], str)
        self.assertIn("pytest", result["run_command"])

    def test_recommend_verifiers_known_component(self):
        result = self.aeos.recommend_verifiers("imraf_engine")
        self.assertIn("tests/institutional_memory/test_imraf.py",
                      result["recommended_verifiers"])

    # ── AEOS Stats ────────────────────────────────────────────────────────────

    def test_aeos_stats_structure(self):
        stats = self.aeos.get_stats()
        self.assertEqual(stats["module"], "AEOSEngine")
        self.assertEqual(stats["ftd"], "AEOS-001")
        self.assertIsInstance(stats["available"], bool)
        self.assertIn("capabilities", stats)

    # ── DIAL Module 12: Autonomous Planning ───────────────────────────────────

    def test_plan_next_steps_structure(self):
        result = self.dial.plan_next_steps()
        self.assertIn("recommended_next_steps", result)
        self.assertIsInstance(result["recommended_next_steps"], list)
        self.assertGreater(len(result["recommended_next_steps"]), 0)

    def test_plan_next_steps_has_priority(self):
        result = self.dial.plan_next_steps()
        first = result["recommended_next_steps"][0]
        self.assertIn("priority", first)
        self.assertIn("action", first)
        self.assertIn("urgency", first)

    # ── DIAL Module 13: Change Proposal ───────────────────────────────────────

    def test_generate_change_proposal_structure(self):
        result = self.dial.generate_change_proposal("improve trailing stop", "trade_manager")
        for key in ("goal", "component", "recommended_files", "historical_risks",
                    "regression_risk", "required_verifiers", "checklist"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_generate_change_proposal_checklist_not_empty(self):
        result = self.dial.generate_change_proposal("fix TSL", "trade_manager")
        self.assertIsInstance(result["checklist"], list)
        self.assertGreater(len(result["checklist"]), 0)

    def test_generate_change_proposal_impact_valid(self):
        result = self.dial.generate_change_proposal("refactor", "risk_engine")
        self.assertIn(result["estimated_impact"], ("LOW", "MEDIUM", "HIGH"))

    # ── DIAL Module 14: FTD Drafting ──────────────────────────────────────────

    def test_draft_ftd_structure(self):
        result = self.dial.draft_ftd("trailing stop")
        self.assertIn("draft_ftd", result)
        draft = result["draft_ftd"]
        for key in ("id", "title", "status", "motivation", "objectives",
                    "acceptance_criteria", "estimated_size"):
            self.assertIn(key, draft, f"Missing draft key: {key}")

    def test_draft_ftd_objectives_is_list(self):
        result = self.dial.draft_ftd("context memory")
        self.assertIsInstance(result["draft_ftd"]["objectives"], list)

    def test_draft_ftd_status_is_draft(self):
        result = self.dial.draft_ftd("risk engine latency")
        self.assertEqual(result["draft_ftd"]["status"], "DRAFT")

    # ── DIAL Module 15: Module Health Score ───────────────────────────────────

    def test_module_health_score_structure(self):
        result = self.dial.get_module_health_score("risk_engine")
        for key in ("module", "risk_score", "risk_label", "incident_count",
                    "regression_count", "complexity", "developer_attention"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_module_health_score_range(self):
        result = self.dial.get_module_health_score("risk_engine")
        self.assertGreaterEqual(result["risk_score"], 0.0)
        self.assertLessEqual(result["risk_score"], 10.0)

    def test_module_health_score_label_valid(self):
        result = self.dial.get_module_health_score("trade_manager")
        self.assertIn(result["risk_label"], ("LOW", "MEDIUM", "HIGH", "CRITICAL"))

    def test_module_health_score_high_risk_core(self):
        result = self.dial.get_module_health_score("risk_engine")
        self.assertTrue(result["is_core_component"])

    # ── DIAL Module 16: Observe and Learn ─────────────────────────────────────

    def test_observe_and_learn_records(self):
        result = self.dial.observe_and_learn(
            "trade_manager", "TSL fired below breakeven", "FAILURE"
        )
        self.assertEqual(result["status"], "RECORDED")
        self.assertIsInstance(result["record_id"], int)
        self.assertGreater(result["record_id"], 0)

    def test_observe_and_learn_failure_extracts_lesson(self):
        result = self.dial.observe_and_learn(
            "risk_engine", "drawdown limit hit unexpectedly", "FAILURE"
        )
        self.assertIsNotNone(result.get("lesson_id"))
        self.assertGreater(result["lesson_id"], 0)

    def test_observe_and_learn_non_failure_no_lesson(self):
        result = self.dial.observe_and_learn(
            "data_lake", "query latency improved after index", "SUCCESS"
        )
        self.assertEqual(result["status"], "RECORDED")
        self.assertIsNone(result.get("lesson_id"))

    def test_observe_and_learn_learning_loop_keys(self):
        result = self.dial.observe_and_learn(
            "pnl_calc", "PnL calculation observed", "SUCCESS"
        )
        loop = result.get("learning_loop", {})
        for key in ("observe", "learn", "record", "improve"):
            self.assertIn(key, loop)


if __name__ == "__main__":
    unittest.main()
