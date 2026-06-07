"""
FTD-IMR-001 — IMRAF test suite.
Uses a temp directory so production DB is never touched.
"""
from __future__ import annotations

import sys
import os
import tempfile
import time
import unittest
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _make_engine(tmp_dir: str):
    """Construct a fresh IMRAFEngine pointed at a temp DB."""
    from core.institutional_memory.imraf_engine import IMRAFEngine
    db_path = Path(tmp_dir) / "test_imraf.db"
    return IMRAFEngine(db_path=db_path)


class TestIMRAFDBCreation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.engine = _make_engine(self.tmp)

    def tearDown(self):
        self.engine.close()

    def test_db_file_created(self):
        db = Path(self.tmp) / "test_imraf.db"
        self.assertTrue(db.exists())

    def test_connection_active(self):
        # get_stats() exercises the connection
        stats = self.engine.get_stats()
        self.assertIn("total_records", stats)


class TestIMRAFRecord(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.engine = _make_engine(self.tmp)

    def tearDown(self):
        self.engine.close()

    def test_record_returns_int(self):
        from core.institutional_memory.imraf_engine import Category
        rid = self.engine.record(Category.KNOWLEDGE, "Test title", {"key": "val"})
        self.assertIsInstance(rid, int)
        self.assertGreater(rid, 0)

    def test_get_record_round_trips(self):
        from core.institutional_memory.imraf_engine import Category
        rid = self.engine.record(Category.BUG, "Test bug", {"detail": "oops"},
                                 subcategory="core", tags=["bug", "test"])
        rec = self.engine.get_record(rid)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["title"], "Test bug")
        self.assertEqual(rec["category"], "BUG")
        self.assertEqual(rec["data"]["detail"], "oops")
        self.assertIn("bug", rec["tags"])


class TestIMRAFSearch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.engine = _make_engine(self.tmp)
        from core.institutional_memory.imraf_engine import Category
        self.engine.record(Category.KNOWLEDGE, "RSI divergence finding",
                           {"finding": "RSI works in trending markets"}, tags=["rsi"])
        self.engine.record(Category.BUG, "Memory leak in executor",
                           {"detail": "executor buffer overflow"}, tags=["memory"])

    def tearDown(self):
        self.engine.close()

    def test_search_finds_by_keyword(self):
        results = self.engine.search("rsi")
        self.assertTrue(any("RSI" in r["title"] or "rsi" in r["search_text"]
                            for r in results))

    def test_search_filters_by_category(self):
        from core.institutional_memory.imraf_engine import Category
        results = self.engine.search("memory", category=Category.BUG)
        for r in results:
            self.assertEqual(r["category"], "BUG")

    def test_search_no_match_returns_empty(self):
        results = self.engine.search("xyzzy_nonexistent_term_zzzz")
        self.assertEqual(results, [])


class TestIMRAFTimeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.engine = _make_engine(self.tmp)
        from core.institutional_memory.imraf_engine import Category
        self.engine.record(Category.KNOWLEDGE, "First", {"v": 1})
        time.sleep(0.01)
        self.engine.record(Category.KNOWLEDGE, "Second", {"v": 2})

    def tearDown(self):
        self.engine.close()

    def test_timeline_newest_first(self):
        tl = self.engine.timeline(limit=10)
        tss = [r["ts"] for r in tl]
        self.assertEqual(tss, sorted(tss, reverse=True))


class TestConvenienceFunctions(unittest.TestCase):
    """Each convenience function should produce a record with the correct category."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # Monkeypatch global imraf singleton to use temp DB
        import core.institutional_memory.imraf_engine as _mod
        self._orig_imraf = _mod.imraf
        self._engine = _make_engine(self.tmp)
        _mod.imraf = self._engine

    def tearDown(self):
        import core.institutional_memory.imraf_engine as _mod
        _mod.imraf = self._orig_imraf
        self._engine.close()

    def _check(self, rid: int, expected_cat: str):
        rec = self._engine.get_record(rid)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["category"], expected_cat)

    def test_record_failure(self):
        from core.institutional_memory.imraf_engine import record_failure
        rid = record_failure("comp", "rc", "impact")
        self._check(rid, "FAILURE")

    def test_record_incident(self):
        from core.institutional_memory.imraf_engine import record_incident
        rid = record_incident("INC-1", ["t1"], "rc", ["fix"])
        self._check(rid, "INCIDENT")

    def test_record_decision(self):
        from core.institutional_memory.imraf_engine import record_decision
        rid = record_decision("BTCUSDT", "LONG", "TREND", "scalper", 0.8, "EXECUTED", "ok")
        self._check(rid, "DECISION")

    def test_record_evolution(self):
        from core.institutional_memory.imraf_engine import record_evolution
        rid = record_evolution("scalper", "1.0", "1.1", 0.5, 0.6, "improved")
        self._check(rid, "EVOLUTION")

    def test_record_regime(self):
        from core.institutional_memory.imraf_engine import record_regime
        rid = record_regime("TREND", "BTCUSDT", {"atr": 1.2})
        self._check(rid, "REGIME")

    def test_record_knowledge(self):
        from core.institutional_memory.imraf_engine import record_knowledge
        rid = record_knowledge("Finding A", "RSI useful")
        self._check(rid, "KNOWLEDGE")

    def test_record_postmortem(self):
        from core.institutional_memory.imraf_engine import record_postmortem
        rid = record_postmortem("Inc", {}, {}, {}, "rc", [])
        self._check(rid, "POSTMORTEM")

    def test_record_bug(self):
        from core.institutional_memory.imraf_engine import record_bug
        rid = record_bug("BUG-001", "core", "rc", "fix", "prevention")
        self._check(rid, "BUG")

    def test_record_architecture(self):
        from core.institutional_memory.imraf_engine import record_architecture
        rid = record_architecture("Title", "decision", [], "reasoning", {})
        self._check(rid, "ARCHITECTURE")

    def test_record_self_improvement(self):
        from core.institutional_memory.imraf_engine import record_self_improvement
        rid = record_self_improvement("change", "impact", {}, "stable", "WIN")
        self._check(rid, "SELF_IMPROVE")

    def test_record_research(self):
        from core.institutional_memory.imraf_engine import record_research
        rid = record_research("scalper", "1.0", "TREND", {}, {})
        self._check(rid, "RESEARCH")

    def test_record_regression(self):
        from core.institutional_memory.imraf_engine import record_regression
        rid = record_regression("core", "trigger", "before", "after", ["1.0"])
        self._check(rid, "REGRESSION")

    def test_record_operational(self):
        from core.institutional_memory.imraf_engine import record_operational
        rid = record_operational("latency", 12, {"ctx": "test"})
        self._check(rid, "OPERATIONAL")

    def test_record_ai_training(self):
        from core.institutional_memory.imraf_engine import record_ai_training
        rid = record_ai_training({}, "LONG", "WIN", 0.8, "TREND", {})
        self._check(rid, "AI_TRAINING")

    def test_record_meta_learning(self):
        from core.institutional_memory.imraf_engine import record_meta_learning
        rid = record_meta_learning("A/B", "hypothesis", "result", "backtest", True)
        self._check(rid, "META_LEARNING")

    def test_record_developer(self):
        from core.institutional_memory.imraf_engine import record_developer
        rid = record_developer("Title", "rationale", {}, "notes")
        self._check(rid, "DEVELOPER")

    def test_record_deployment_event(self):
        from core.institutional_memory.imraf_engine import record_deployment_event
        rid = record_deployment_event("1.54.0", "DEPLOY", "desc")
        self._check(rid, "DEPLOYMENT")

    def test_record_attribution(self):
        from core.institutional_memory.imraf_engine import record_attribution
        rid = record_attribution("BTCUSDT", 10.0, 0.5, 0.3, 0.2, "scalper")
        self._check(rid, "ATTRIBUTION")

    def test_record_evolution_timeline(self):
        from core.institutional_memory.imraf_engine import record_evolution_timeline
        rid = record_evolution_timeline("v1.0 launch", "desc", "high")
        self._check(rid, "EVOLUTION_TL")


class TestIMRAFStats(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.engine = _make_engine(self.tmp)

    def tearDown(self):
        self.engine.close()

    def test_stats_structure(self):
        stats = self.engine.get_stats()
        self.assertIn("total_records", stats)
        self.assertIn("by_category", stats)
        self.assertIn("db_path", stats)
        self.assertIn("boot_ts", stats)

    def test_stats_counts_match(self):
        from core.institutional_memory.imraf_engine import Category
        before = self.engine.get_stats()["total_records"]
        self.engine.record(Category.KNOWLEDGE, "k1", {"v": 1})
        self.engine.record(Category.BUG, "b1", {"v": 2})
        after = self.engine.get_stats()["total_records"]
        self.assertEqual(after, before + 2)


class TestIMRAFBootSummary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.engine = _make_engine(self.tmp)

    def tearDown(self):
        self.engine.close()

    def test_boot_summary_nonempty(self):
        s = self.engine.boot_summary()
        self.assertIsInstance(s, str)
        self.assertGreater(len(s), 10)
        self.assertIn("IMRAF", s)


class TestIMRAFPersistence(unittest.TestCase):
    def test_records_survive_close_reopen(self):
        tmp = tempfile.mkdtemp()
        db_path = Path(tmp) / "persist_test.db"
        from core.institutional_memory.imraf_engine import IMRAFEngine, Category

        # Write then close
        e1 = IMRAFEngine(db_path=db_path)
        rid = e1.record(Category.KNOWLEDGE, "Persist test", {"data": "important"})
        e1.close()

        # Reopen and verify
        e2 = IMRAFEngine(db_path=db_path)
        rec = e2.get_record(rid)
        e2.close()
        self.assertIsNotNone(rec)
        self.assertEqual(rec["title"], "Persist test")


if __name__ == "__main__":
    unittest.main()
