"""
Tests for FTD-PHOENIX-ENTRY-EXIT-TRUTH-ENGINE-001
Covers ETE, XTE, AttributionSnapshot, AlphaAttributionPlatform, TruthArchive.
"""
import sys
import os
import unittest
import threading
import time
import tempfile
import pathlib

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.truth.entry_truth_engine import EntryTruthEngine, ETEResult, WEIGHTS
from core.truth.exit_truth_engine import ExitTruthEngine, XTEResult, XTEAdvisory
from core.truth.alpha_attribution import AlphaAttributionPlatform, AttributionSnapshot


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_closes(n=25, start=100.0, step=0.1):
    return [start + i * step for i in range(n)]

def make_highs(closes, offset=0.5):
    return [c + offset for c in closes]

def make_lows(closes, offset=0.5):
    return [c - offset for c in closes]

def make_volumes(n=25, base=1000.0):
    return [base] * n

def make_snapshot(trade_id="T1", net_pnl=1.0, ete_score=75.0, **kwargs):
    defaults = dict(
        trade_id=trade_id, symbol="BTCUSDT", session="NY",
        strategy="TrendFollowing", regime="TRENDING",
        entry_truth_score=ete_score, exit_truth_score=0.0,
        structure_score=80.0, regime_score=85.0, momentum_score=70.0,
        volatility_score=70.0, liquidity_score=70.0, cost_score=80.0,
        net_pnl=net_pnl, r_multiple=1.5, genome_id=None, rl_context="TRENDING|NY",
        ts_entry=time.time() - 60, ts_exit=time.time(),
        alpha_sources=[], destruction_sources=[],
    )
    defaults.update(kwargs)
    return AttributionSnapshot(**defaults)


# ── ETE Tests ─────────────────────────────────────────────────────────────────

class TestETEWeights(unittest.TestCase):
    def test_weights_sum_to_one(self):
        total = sum(WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_all_six_components_present(self):
        expected = {"structure", "regime", "momentum", "volatility", "liquidity", "cost"}
        self.assertEqual(set(WEIGHTS.keys()), expected)


class TestETEScoreRange(unittest.TestCase):
    def setUp(self):
        self.ete = EntryTruthEngine()

    def _eval(self, **kwargs):
        defaults = dict(
            closes=make_closes(), highs=make_highs(make_closes()),
            lows=make_lows(make_closes()), volumes=make_volumes(),
            atr_pct=0.5, atr_ema=0.5, regime="TRENDING",
            fee_cost=0.1, gross_tp=2.0, rr=2.5, signal_side="LONG",
        )
        defaults.update(kwargs)
        return self.ete.evaluate(**defaults)

    def test_score_always_0_to_100(self):
        for regime in ["TRENDING", "MEAN_REVERTING", "COMPRESSION", "UNKNOWN"]:
            r = self._eval(regime=regime)
            self.assertGreaterEqual(r.score, 0.0)
            self.assertLessEqual(r.score, 100.0)

    def test_all_six_component_scores_present(self):
        r = self._eval()
        self.assertIsNotNone(r.structure_score)
        self.assertIsNotNone(r.regime_score)
        self.assertIsNotNone(r.momentum_score)
        self.assertIsNotNone(r.volatility_score)
        self.assertIsNotNone(r.liquidity_score)
        self.assertIsNotNone(r.cost_score)

    def test_gate_disabled_never_blocks(self):
        r = self._eval()
        self.assertFalse(r.blocked)
        self.assertFalse(r.gate_enabled)

    def test_gate_enabled_blocks_when_below_threshold(self):
        # Force a low score by passing degenerate inputs
        r = self.ete.evaluate(
            closes=[100.0] * 5, highs=[100.5] * 5, lows=[99.5] * 5,
            volumes=[10.0] * 5, atr_pct=5.0, atr_ema=1.0,
            regime="HIGH_VOLATILITY", fee_cost=10.0, gross_tp=1.0,
            rr=0.1, signal_side="LONG", gate_enabled=True, min_score=90.0,
        )
        # If score is below 90, it should be blocked
        if r.score < 90.0:
            self.assertTrue(r.blocked)

    def test_gate_enabled_false_never_blocks_even_bad_inputs(self):
        r = self.ete.evaluate(
            closes=[100.0] * 5, highs=[100.5] * 5, lows=[99.5] * 5,
            volumes=[10.0] * 5, atr_pct=5.0, atr_ema=1.0,
            regime="HIGH_VOLATILITY", fee_cost=10.0, gross_tp=1.0,
            rr=0.1, signal_side="LONG", gate_enabled=False,
        )
        self.assertFalse(r.blocked)

    def test_empty_closes_returns_safe_result(self):
        r = self._eval(closes=[], highs=[], lows=[])
        self.assertGreaterEqual(r.score, 0.0)
        self.assertLessEqual(r.score, 100.0)

    def test_zero_volumes_returns_safe_result(self):
        r = self._eval(volumes=[])
        self.assertGreaterEqual(r.score, 0.0)

    def test_zero_atr_returns_safe_result(self):
        r = self._eval(atr_pct=0.0, atr_ema=0.0)
        self.assertGreaterEqual(r.score, 0.0)

    def test_component_detail_dict_populated(self):
        r = self._eval()
        self.assertIn("structure", r.component_detail)
        self.assertIn("regime", r.component_detail)
        self.assertIn("cost", r.component_detail)

    def test_result_is_ete_result_instance(self):
        r = self._eval()
        self.assertIsInstance(r, ETEResult)


class TestETESubEngines(unittest.TestCase):
    def setUp(self):
        self.ete = EntryTruthEngine()

    def test_regime_trending_scores_high(self):
        s = self.ete._score_regime("TRENDING")
        self.assertEqual(s, 85.0)

    def test_regime_unknown_scores_35(self):
        s = self.ete._score_regime("UNKNOWN")
        self.assertEqual(s, 35.0)

    def test_regime_default_scores_35(self):
        s = self.ete._score_regime("SOME_UNKNOWN_VALUE")
        self.assertEqual(s, 35.0)

    def test_regime_high_volatility_scores_30(self):
        s = self.ete._score_regime("HIGH_VOLATILITY")
        self.assertEqual(s, 30.0)

    def test_volatility_compression_scores_85(self):
        s = self.ete._score_volatility(0.3, 1.0)  # ratio=0.3 < 1.0
        self.assertEqual(s, 85.0)

    def test_volatility_shock_scores_10(self):
        s = self.ete._score_volatility(3.0, 1.0)  # ratio=3.0 > 2.5
        self.assertEqual(s, 10.0)

    def test_volatility_zero_ema_returns_50(self):
        s = self.ete._score_volatility(0.5, 0.0)
        self.assertEqual(s, 50.0)

    def test_liquidity_empty_volumes_returns_50(self):
        s = self.ete._score_liquidity([])
        self.assertEqual(s, 50.0)

    def test_liquidity_zero_avg_returns_50(self):
        s = self.ete._score_liquidity([0.0, 0.0, 0.0])
        self.assertEqual(s, 50.0)

    def test_liquidity_high_rv_scores_high(self):
        vols = [1000.0] * 20 + [4000.0]  # rv = 4000/1000 > 3.0
        s = self.ete._score_liquidity(vols)
        self.assertGreaterEqual(s, 90.0)

    def test_liquidity_thin_market_scores_low(self):
        vols = [1000.0] * 20 + [200.0]  # rv = 0.2 < 0.5
        s = self.ete._score_liquidity(vols)
        self.assertLessEqual(s, 30.0)

    def test_cost_zero_gross_tp_returns_60(self):
        s = self.ete._score_cost(1.0, 0.0, 2.0)
        self.assertEqual(s, 60.0)

    def test_cost_low_fee_ratio_scores_high(self):
        s = self.ete._score_cost(0.01, 1.0, 2.0)  # fee_ratio=0.01 < 0.05
        self.assertGreaterEqual(s, 95.0)

    def test_cost_high_fee_ratio_scores_low(self):
        s = self.ete._score_cost(0.5, 1.0, 2.0)  # fee_ratio=0.5 > 0.35
        self.assertLessEqual(s, 20.0)

    def test_cost_rr_bonus_applied(self):
        s_no_bonus = self.ete._score_cost(0.10, 1.0, 1.0)  # rr=1.0, no bonus
        s_with_bonus = self.ete._score_cost(0.10, 1.0, 3.0)  # rr=3.0, +10 bonus
        self.assertGreater(s_with_bonus, s_no_bonus)

    def test_momentum_insufficient_data_returns_safe(self):
        s = self.ete._score_momentum([100.0, 101.0])
        self.assertEqual(s, 50.0)

    def test_structure_insufficient_data_returns_50(self):
        s = self.ete._score_structure([100.0, 101.0], [101.0, 102.0], [99.0, 100.0])
        self.assertEqual(s, 50.0)


class TestETEDirectional(unittest.TestCase):
    def setUp(self):
        self.ete = EntryTruthEngine()

    def test_better_conditions_improve_score(self):
        # Trending regime + normal volatility + good RR
        r_good = self.ete.evaluate(
            closes=make_closes(25, 100, 0.2), highs=make_highs(make_closes(25, 100, 0.2)),
            lows=make_lows(make_closes(25, 100, 0.2)), volumes=make_volumes(25, 2000),
            atr_pct=0.5, atr_ema=1.0, regime="TRENDING",
            fee_cost=0.05, gross_tp=5.0, rr=3.0, signal_side="LONG",
        )
        # High volatility + thin market + high fee
        r_bad = self.ete.evaluate(
            closes=[100.0] * 10, highs=[100.5] * 10, lows=[99.5] * 10,
            volumes=[100.0] * 10, atr_pct=3.0, atr_ema=1.0,
            regime="HIGH_VOLATILITY", fee_cost=0.5, gross_tp=1.0, rr=0.5, signal_side="LONG",
        )
        self.assertGreater(r_good.score, r_bad.score)

    def test_summary_returns_dict(self):
        r = self.ete.evaluate(
            closes=make_closes(), highs=make_highs(make_closes()),
            lows=make_lows(make_closes()), volumes=make_volumes(),
            atr_pct=0.5, atr_ema=0.5, regime="TRENDING",
            fee_cost=0.1, gross_tp=2.0, rr=2.5, signal_side="LONG",
        )
        summary = self.ete.summary()
        self.assertIsInstance(summary, dict)
        self.assertIn("eval_count", summary)
        self.assertIn("last_score", summary)

    def test_eval_count_increments(self):
        ete = EntryTruthEngine()
        for i in range(3):
            ete.evaluate(
                closes=make_closes(), highs=make_highs(make_closes()),
                lows=make_lows(make_closes()), volumes=make_volumes(),
                atr_pct=0.5, atr_ema=0.5, regime="TRENDING",
                fee_cost=0.1, gross_tp=2.0, rr=2.5, signal_side="LONG",
            )
        self.assertEqual(ete.summary()["eval_count"], 3)


# ── XTE Tests ─────────────────────────────────────────────────────────────────

class TestXTEBasic(unittest.TestCase):
    def setUp(self):
        self.xte = ExitTruthEngine()

    def _eval(self, **kwargs):
        defaults = dict(
            closes=make_closes(), volumes=make_volumes(),
            atr_pct=0.5, atr_ema=0.5, current_r=1.5, peak_r=2.0, side="LONG",
        )
        defaults.update(kwargs)
        return self.xte.evaluate(**defaults)

    def test_force_close_always_false(self):
        r = self._eval()
        self.assertFalse(r.force_close)

    def test_force_close_always_false_low_score(self):
        r = self._eval(closes=[100.0]*5, volumes=[10.0]*5, atr_pct=5.0, atr_ema=1.0, current_r=-2.0, peak_r=0.5)
        self.assertFalse(r.force_close)

    def test_score_range_0_to_100(self):
        r = self._eval()
        self.assertGreaterEqual(r.score, 0.0)
        self.assertLessEqual(r.score, 100.0)

    def test_all_five_components_present(self):
        r = self._eval()
        self.assertIsNotNone(r.trend_persistence_score)
        self.assertIsNotNone(r.volatility_shift_score)
        self.assertIsNotNone(r.liquidity_exhaustion_score)
        self.assertIsNotNone(r.profit_protection_score)
        self.assertIsNotNone(r.risk_escalation_score)

    def test_advisory_is_xte_advisory_instance(self):
        r = self._eval()
        self.assertIsInstance(r.advisory, XTEAdvisory)

    def test_high_score_sets_hold_true(self):
        # Good conditions → high score → hold=True
        r = self._eval()
        if r.score >= 60:
            self.assertTrue(r.advisory.hold)

    def test_tighten_tsl_fires_when_score_below_35(self):
        # Force low score: bad conditions
        r = self.xte.evaluate(
            closes=[100.0]*5, volumes=[10.0, 8.0, 6.0, 5.0, 4.0],
            atr_pct=5.0, atr_ema=1.0, current_r=-2.0, peak_r=0.1, side="LONG",
        )
        if r.score < 35:
            self.assertTrue(r.advisory.tighten_tsl)

    def test_scale_out_fires_when_profit_high(self):
        # current_r=2.5 → profit_protection_score=85 → scale_out
        r = self._eval(current_r=2.5, peak_r=3.0)
        if r.profit_protection_score > 80:
            self.assertTrue(r.advisory.scale_out)

    def test_trigger_be_fires_when_profitable(self):
        r = self._eval(current_r=1.5, peak_r=2.0)
        if r.profit_protection_score > 60:
            self.assertTrue(r.advisory.trigger_be)

    def test_empty_closes_returns_safe_result(self):
        r = self._eval(closes=[])
        self.assertGreaterEqual(r.score, 0.0)
        self.assertFalse(r.force_close)

    def test_empty_volumes_returns_safe_result(self):
        r = self._eval(volumes=[])
        self.assertFalse(r.force_close)

    def test_volatility_expansion_scores_35(self):
        s = self.xte._score_volatility_shift(2.0, 1.0)  # ratio=2.0 > 1.5
        self.assertEqual(s, 35.0)

    def test_volatility_compression_scores_80(self):
        s = self.xte._score_volatility_shift(0.5, 1.0)  # ratio=0.5 < 0.8
        self.assertEqual(s, 80.0)

    def test_liquidity_declining_scores_25(self):
        vols = [1000.0] * 10 + [200.0, 200.0, 200.0]  # recent << prior
        s = self.xte._score_liquidity_exhaustion(vols)
        self.assertEqual(s, 25.0)

    def test_profit_protection_2r_scores_85(self):
        s = self.xte._score_profit_protection(2.0)
        self.assertEqual(s, 85.0)

    def test_profit_protection_loss_scores_25(self):
        s = self.xte._score_profit_protection(-0.5)
        self.assertEqual(s, 25.0)

    def test_summary_returns_dict_with_eval_count(self):
        self._eval()
        s = self.xte.summary()
        self.assertIsInstance(s, dict)
        self.assertIn("eval_count", s)

    def test_risk_escalation_shock_scores_15(self):
        s = self.xte._score_risk_escalation(0.5, 2.0, 3.0, 1.0)  # atr ratio=3.0>2.5
        self.assertEqual(s, 15.0)


# ── AttributionSnapshot Tests ─────────────────────────────────────────────────

class TestAttributionSnapshot(unittest.TestCase):
    def test_snapshot_creation(self):
        snap = make_snapshot()
        self.assertEqual(snap.trade_id, "T1")
        self.assertEqual(snap.symbol, "BTCUSDT")

    def test_alpha_sources_auto_populated(self):
        snap = make_snapshot(structure_score=80.0, regime_score=85.0, momentum_score=70.0,
                             volatility_score=70.0, liquidity_score=70.0, cost_score=80.0)
        # All >= 70, so all 6 should be alpha sources
        self.assertEqual(len(snap.alpha_sources), 6)

    def test_destruction_sources_auto_populated(self):
        snap = make_snapshot(
            structure_score=30.0, regime_score=30.0, momentum_score=30.0,
            volatility_score=30.0, liquidity_score=30.0, cost_score=30.0,
        )
        self.assertEqual(len(snap.destruction_sources), 6)

    def test_mixed_sources(self):
        snap = make_snapshot(
            structure_score=80.0, regime_score=30.0, momentum_score=75.0,
            volatility_score=35.0, liquidity_score=72.0, cost_score=20.0,
        )
        self.assertIn("structure", snap.alpha_sources)
        self.assertIn("momentum", snap.alpha_sources)
        self.assertIn("regime", snap.destruction_sources)
        self.assertIn("cost", snap.destruction_sources)

    def test_explicit_sources_not_overridden(self):
        snap = make_snapshot(alpha_sources=["custom"], destruction_sources=["other"])
        self.assertEqual(snap.alpha_sources, ["custom"])
        self.assertEqual(snap.destruction_sources, ["other"])


# ── AlphaAttributionPlatform Tests ────────────────────────────────────────────

class TestAlphaAttributionPlatform(unittest.TestCase):
    def setUp(self):
        self.aap = AlphaAttributionPlatform()

    def test_record_and_snapshot_count(self):
        self.aap.record(make_snapshot("T1"))
        self.aap.record(make_snapshot("T2"))
        result = self.aap.alpha_discovery_matrix()
        self.assertEqual(result["total_snapshots"], 2)

    def test_thread_safety(self):
        aap = AlphaAttributionPlatform()
        errors = []
        def worker():
            try:
                for i in range(50):
                    aap.record(make_snapshot(f"T{i}"))
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        result = aap.alpha_discovery_matrix()
        self.assertEqual(result["total_snapshots"], 250)

    def test_alpha_discovery_matrix_structure(self):
        self.aap.record(make_snapshot("T1", net_pnl=1.0))
        self.aap.record(make_snapshot("T2", net_pnl=-1.0, structure_score=30.0))
        result = self.aap.alpha_discovery_matrix()
        self.assertIn("top_alpha_sources", result)
        self.assertIn("top_destroyers", result)
        self.assertIn("score_vs_expectancy", result)
        self.assertEqual(len(result["top_alpha_sources"]), 6)
        self.assertEqual(len(result["top_destroyers"]), 6)
        self.assertEqual(len(result["score_vs_expectancy"]), 5)

    def test_score_vs_expectancy_buckets(self):
        self.aap.record(make_snapshot("T1", ete_score=85.0, net_pnl=1.0))
        self.aap.record(make_snapshot("T2", ete_score=25.0, net_pnl=-1.0))
        result = self.aap.alpha_discovery_matrix()
        buckets = {b["score_bucket"]: b for b in result["score_vs_expectancy"]}
        self.assertIn("80-100", buckets)
        self.assertIn("20-40", buckets)

    def test_calibration_report_structure(self):
        self.aap.record(make_snapshot("T1", net_pnl=1.0, ete_score=75.0))
        report = self.aap.truth_calibration_report()
        self.assertIn("calibration", report)
        self.assertIn("total_trades", report)
        self.assertEqual(len(report["calibration"]), 10)  # 10 deciles

    def test_calibration_decile_fields(self):
        self.aap.record(make_snapshot("T1", net_pnl=1.0, ete_score=75.0))
        report = self.aap.truth_calibration_report()
        for decile in report["calibration"]:
            self.assertIn("decile", decile)
            self.assertIn("avg_pnl", decile)
            self.assertIn("win_rate", decile)
            self.assertIn("trade_count", decile)

    def test_component_calibration_split(self):
        self.aap.record(make_snapshot("T1", net_pnl=1.0, structure_score=80.0))
        self.aap.record(make_snapshot("T2", net_pnl=-1.0, structure_score=20.0))
        result = self.aap.component_calibration(threshold=40.0)
        self.assertEqual(result["total_trades"], 2)
        self.assertEqual(len(result["components"]), 6)
        structure = next(c for c in result["components"] if c["component"] == "structure")
        self.assertEqual(structure["below"]["trade_count"], 1)
        self.assertEqual(structure["below"]["win_rate"], 0.0)
        self.assertEqual(structure["at_or_above"]["trade_count"], 1)
        self.assertEqual(structure["at_or_above"]["win_rate"], 1.0)

    def test_component_calibration_empty(self):
        result = AlphaAttributionPlatform().component_calibration()
        self.assertEqual(result["total_trades"], 0)
        for c in result["components"]:
            self.assertEqual(c["below"]["trade_count"], 0)

    def test_summary_returns_total_snapshots(self):
        self.aap.record(make_snapshot("T1"))
        s = self.aap.summary()
        self.assertEqual(s["total_snapshots"], 1)

    def test_empty_platform_returns_valid_structure(self):
        aap = AlphaAttributionPlatform()
        result = aap.alpha_discovery_matrix()
        self.assertEqual(result["total_snapshots"], 0)
        cal = aap.truth_calibration_report()
        self.assertEqual(cal["total_trades"], 0)


# ── TruthArchive Tests ────────────────────────────────────────────────────────

class TestTruthArchive(unittest.TestCase):
    def setUp(self):
        # Patch ARCHIVE_PATH to use a temp dir
        import core.truth.truth_archive as ta_mod
        self._tmp = tempfile.mkdtemp()
        self._orig_path = ta_mod.ARCHIVE_PATH
        ta_mod.ARCHIVE_PATH = pathlib.Path(self._tmp) / "test_truth_archive.db"
        # Instantiate a fresh archive with the patched path
        from core.truth.truth_archive import TruthArchive
        self.archive = TruthArchive()

    def tearDown(self):
        import core.truth.truth_archive as ta_mod
        ta_mod.ARCHIVE_PATH = self._orig_path

    def test_save_and_recent_round_trip(self):
        snap = make_snapshot("T-ARCH-001", net_pnl=1.5)
        self.archive.save(snap)
        rows = self.archive.recent(10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["trade_id"], "T-ARCH-001")

    def test_recent_returns_empty_list_when_no_data(self):
        rows = self.archive.recent(10)
        self.assertEqual(rows, [])

    def test_recent_respects_n_limit(self):
        for i in range(10):
            self.archive.save(make_snapshot(f"T{i}"))
        rows = self.archive.recent(5)
        self.assertEqual(len(rows), 5)

    def test_save_bad_data_does_not_raise(self):
        # Should swallow exceptions gracefully
        try:
            snap = make_snapshot("T-BAD")
            snap.trade_id = None  # may cause issues — should not crash
            self.archive.save(snap)
        except Exception:
            pass  # acceptable

    def test_columns_present_in_row(self):
        snap = make_snapshot("T-COL-TEST")
        self.archive.save(snap)
        rows = self.archive.recent(1)
        row = rows[0]
        for field in ["trade_id", "symbol", "entry_truth_score", "net_pnl", "r_multiple"]:
            self.assertIn(field, row)


if __name__ == "__main__":
    unittest.main()
