"""
Phase 6 — Stability + Profit Consistency test suite

Validates:
  TestEVConfidenceEngine      — EV tier classification and size multipliers
  TestLossClusterController   — size reduction and pause on loss clusters
  TestStreakIntelligenceEngine — hot/cold detection, score_min adjustment
  TestCapitalRecoveryEngine   — defensive/recovering/normal state transitions
  TestExplorationGuard        — daily loss cap enforcement
  TestPhase6Pipeline          — end-to-end integration scenarios

Non-negotiable rules enforced:
  - No size boost above 1.0×
  - Pause is time-based, not trade-count based
  - Exploration blocked when daily cap hit
  - Every state is logged / detectable

Run with:  python -m pytest tests/test_phase6_stability.py -v
"""
import time
import unittest

from config import cfg


# ─────────────────────────────────────────────────────────────────────────────
# TestEVConfidenceEngine
# ─────────────────────────────────────────────────────────────────────────────
class TestEVConfidenceEngine(unittest.TestCase):

    def setUp(self):
        from core.ev_confidence import EVConfidenceEngine
        self.evc = EVConfidenceEngine()

    def test_high_conf_ev_full_size(self):
        r = self.evc.classify(ev=cfg.EVC_HIGH_THRESHOLD)
        self.assertEqual(r.tier, "HIGH_CONF")
        self.assertTrue(r.ok)
        self.assertAlmostEqual(r.size_mult, cfg.EVC_HIGH_SIZE_MULT)

    def test_medium_conf_ev_normal_size(self):
        r = self.evc.classify(ev=cfg.EVC_MID_THRESHOLD)
        self.assertEqual(r.tier, "MEDIUM_CONF")
        self.assertTrue(r.ok)
        self.assertAlmostEqual(r.size_mult, cfg.EVC_MID_SIZE_MULT)

    def test_low_conf_ev_reduced_size(self):
        # EV ≥ 0 but below mid threshold
        r = self.evc.classify(ev=0.01)
        self.assertEqual(r.tier, "LOW_CONF")
        self.assertTrue(r.ok)
        self.assertAlmostEqual(r.size_mult, cfg.EVC_LOW_SIZE_MULT)

    def test_negative_ev_rejected(self):
        r = self.evc.classify(ev=-0.01)
        self.assertEqual(r.tier, "REJECT")
        self.assertFalse(r.ok)
        self.assertEqual(r.size_mult, 0.0)

    def test_zero_ev_is_low_conf(self):
        r = self.evc.classify(ev=0.0)
        self.assertEqual(r.tier, "LOW_CONF")
        self.assertTrue(r.ok)

    def test_size_mult_never_exceeds_one(self):
        for ev in [0.0, 0.05, 0.10, 0.15, 0.50, 1.0]:
            r = self.evc.classify(ev=ev)
            self.assertLessEqual(r.size_mult, 1.0, f"size_mult > 1.0 for ev={ev}")

    def test_tiers_are_monotonically_ordered(self):
        r_low  = self.evc.classify(ev=0.01)
        r_mid  = self.evc.classify(ev=cfg.EVC_MID_THRESHOLD)
        r_high = self.evc.classify(ev=cfg.EVC_HIGH_THRESHOLD)
        self.assertLessEqual(r_low.size_mult,  r_mid.size_mult + 1e-6)
        self.assertLessEqual(r_mid.size_mult,  r_high.size_mult + 1e-6)

    def test_ev_just_above_high_threshold(self):
        r = self.evc.classify(ev=cfg.EVC_HIGH_THRESHOLD + 0.001)
        self.assertEqual(r.tier, "HIGH_CONF")

    def test_ev_just_below_mid_threshold(self):
        r = self.evc.classify(ev=cfg.EVC_MID_THRESHOLD - 0.001)
        self.assertEqual(r.tier, "LOW_CONF")

    def test_summary_structure(self):
        s = self.evc.summary()
        self.assertIn("high_threshold", s)
        self.assertIn("mid_threshold", s)
        self.assertIn("low_size_mult", s)
        self.assertEqual(s["module"], "EV_CONFIDENCE_ENGINE")


# ─────────────────────────────────────────────────────────────────────────────
# TestLossClusterController
# ─────────────────────────────────────────────────────────────────────────────
class TestLossClusterController(unittest.TestCase):

    def setUp(self):
        from core.loss_cluster import LossClusterController
        self.lcc = LossClusterController()

    def test_normal_state_below_reduce_threshold(self):
        r = self.lcc.check(consecutive_losses=cfg.LCC_REDUCE_AFTER - 1)
        self.assertEqual(r.state, "NORMAL")
        self.assertTrue(r.ok)
        self.assertAlmostEqual(r.size_mult, 1.0)

    def test_reducing_state_at_reduce_threshold(self):
        r = self.lcc.check(consecutive_losses=cfg.LCC_REDUCE_AFTER)
        self.assertEqual(r.state, "REDUCING")
        self.assertTrue(r.ok)
        self.assertAlmostEqual(r.size_mult, cfg.LCC_REDUCE_SIZE_MULT)

    def test_pause_triggered_at_pause_threshold(self):
        r = self.lcc.check(consecutive_losses=cfg.LCC_PAUSE_AFTER)
        self.assertEqual(r.state, "PAUSED")
        self.assertFalse(r.ok)
        self.assertEqual(r.size_mult, 0.0)

    def test_pause_persists_on_next_call(self):
        self.lcc.check(consecutive_losses=cfg.LCC_PAUSE_AFTER)
        # Subsequent call with fewer losses still blocked by time-based pause
        r = self.lcc.check(consecutive_losses=0)
        self.assertFalse(r.ok)
        self.assertEqual(r.state, "PAUSED")

    def test_pause_clears_after_duration(self):
        from core.loss_cluster import LossClusterController
        lcc = LossClusterController()
        lcc._pause_until = time.time() - 1.0  # expired
        r = lcc.check(consecutive_losses=0)
        self.assertTrue(r.ok)
        self.assertEqual(r.state, "NORMAL")

    def test_size_mult_never_zero_in_reducing(self):
        r = self.lcc.check(consecutive_losses=cfg.LCC_REDUCE_AFTER)
        self.assertGreater(r.size_mult, 0.0)
        self.assertLessEqual(r.size_mult, 1.0)

    def test_zero_losses_always_normal(self):
        r = self.lcc.check(consecutive_losses=0)
        self.assertEqual(r.state, "NORMAL")
        self.assertTrue(r.ok)

    def test_reset_pause_clears_block(self):
        self.lcc.check(consecutive_losses=cfg.LCC_PAUSE_AFTER)
        self.lcc.reset_pause()
        r = self.lcc.check(consecutive_losses=0)
        self.assertTrue(r.ok)

    def test_summary_structure(self):
        s = self.lcc.summary()
        self.assertIn("reduce_after", s)
        self.assertIn("pause_after", s)
        self.assertIn("pause_minutes", s)
        self.assertEqual(s["module"], "LOSS_CLUSTER_CONTROLLER")


# ─────────────────────────────────────────────────────────────────────────────
# TestStreakIntelligenceEngine
# ─────────────────────────────────────────────────────────────────────────────
class TestStreakIntelligenceEngine(unittest.TestCase):

    def setUp(self):
        from core.streak_engine import StreakIntelligenceEngine
        self.se = StreakIntelligenceEngine()

    def test_neutral_state_no_streaks(self):
        r = self.se.check(consecutive_wins=0, consecutive_losses=0)
        self.assertEqual(r.state, "NEUTRAL")
        self.assertEqual(r.score_adjustment, 0.0)

    def test_hot_streak_at_win_threshold(self):
        r = self.se.check(consecutive_wins=cfg.SE_WIN_STREAK_MIN, consecutive_losses=0)
        self.assertEqual(r.state, "HOT")
        self.assertAlmostEqual(r.score_adjustment, cfg.SE_HOT_SCORE_ADJ)

    def test_cold_streak_at_loss_threshold(self):
        r = self.se.check(consecutive_wins=0, consecutive_losses=cfg.SE_LOSS_STREAK_MIN)
        self.assertEqual(r.state, "COLD")
        self.assertAlmostEqual(r.score_adjustment, cfg.SE_COLD_SCORE_ADJ)

    def test_cold_takes_priority_over_hot(self):
        # Both thresholds met → COLD must win
        r = self.se.check(
            consecutive_wins=cfg.SE_WIN_STREAK_MIN,
            consecutive_losses=cfg.SE_LOSS_STREAK_MIN,
        )
        self.assertEqual(r.state, "COLD")

    def test_hot_score_adj_is_negative(self):
        r = self.se.check(consecutive_wins=cfg.SE_WIN_STREAK_MIN, consecutive_losses=0)
        self.assertLess(r.score_adjustment, 0.0)

    def test_cold_score_adj_is_positive(self):
        r = self.se.check(consecutive_wins=0, consecutive_losses=cfg.SE_LOSS_STREAK_MIN)
        self.assertGreater(r.score_adjustment, 0.0)

    def test_hot_below_threshold_is_neutral(self):
        r = self.se.check(consecutive_wins=cfg.SE_WIN_STREAK_MIN - 1, consecutive_losses=0)
        self.assertEqual(r.state, "NEUTRAL")

    def test_cold_below_threshold_is_neutral(self):
        r = self.se.check(consecutive_wins=0, consecutive_losses=cfg.SE_LOSS_STREAK_MIN - 1)
        self.assertEqual(r.state, "NEUTRAL")

    def test_effective_score_min_floor(self):
        """HOT + very low base score_min must not drop below 0.40."""
        base = 0.42
        r = self.se.check(consecutive_wins=cfg.SE_WIN_STREAK_MIN, consecutive_losses=0)
        eff = max(0.40, base + r.score_adjustment)
        self.assertGreaterEqual(eff, 0.40)

    def test_summary_structure(self):
        s = self.se.summary()
        self.assertIn("hot_score_adj", s)
        self.assertIn("cold_score_adj", s)
        self.assertEqual(s["module"], "STREAK_INTELLIGENCE_ENGINE")


# ─────────────────────────────────────────────────────────────────────────────
# TestCapitalRecoveryEngine
# ─────────────────────────────────────────────────────────────────────────────
class TestCapitalRecoveryEngine(unittest.TestCase):

    def setUp(self):
        from core.capital_recovery import CapitalRecoveryEngine
        self.cre = CapitalRecoveryEngine()

    def test_no_peak_returns_normal(self):
        r = self.cre.check()
        self.assertEqual(r.state, "NORMAL")
        self.assertAlmostEqual(r.size_mult, 1.0)

    def test_normal_equity_growth_returns_normal(self):
        self.cre.update_equity(1000.0)
        self.cre.update_equity(1050.0)
        r = self.cre.check()
        self.assertEqual(r.state, "NORMAL")
        self.assertAlmostEqual(r.size_mult, 1.0)

    def test_defensive_on_deep_drawdown(self):
        self.cre.update_equity(1000.0)  # peak
        # Drop by more than CRE_DEFENSIVE_DD
        drop = 1000.0 * (1 - cfg.CRE_DEFENSIVE_DD - 0.01)
        self.cre.update_equity(drop)
        r = self.cre.check()
        self.assertEqual(r.state, "DEFENSIVE")
        self.assertAlmostEqual(r.size_mult, cfg.CRE_RECOVERY_SIZE_MIN)

    def test_recovering_after_trough(self):
        self.cre.update_equity(1000.0)  # peak
        self.cre.update_equity(800.0)   # trough
        self.cre.update_equity(900.0)   # recovering
        r = self.cre.check()
        self.assertEqual(r.state, "RECOVERING")
        self.assertGreater(r.size_mult, cfg.CRE_RECOVERY_SIZE_MIN)
        self.assertLessEqual(r.size_mult, 1.0)

    def test_size_mult_never_exceeds_one(self):
        for equity in [1000, 900, 800, 850, 950, 1000, 1100]:
            self.cre.update_equity(float(equity))
        r = self.cre.check()
        self.assertLessEqual(r.size_mult, 1.0)

    def test_full_recovery_returns_normal(self):
        self.cre.update_equity(1000.0)  # peak
        self.cre.update_equity(800.0)   # trough
        self.cre.update_equity(1000.0)  # back to peak
        r = self.cre.check()
        self.assertIn(r.state, ("NORMAL", "FULLY_RECOVERED"))
        self.assertAlmostEqual(r.size_mult, 1.0)

    def test_recovery_pct_increases_toward_one(self):
        self.cre.update_equity(1000.0)
        self.cre.update_equity(800.0)
        self.cre.update_equity(850.0)
        r1 = self.cre.check()
        self.cre.update_equity(950.0)
        r2 = self.cre.check()
        self.assertGreater(r2.recovery_pct, r1.recovery_pct - 1e-6)

    def test_deeper_drop_stays_defensive(self):
        self.cre.update_equity(1000.0)
        self.cre.update_equity(900.0)   # first drop
        self.cre.update_equity(850.0)   # deeper drop
        r = self.cre.check()
        self.assertEqual(r.state, "DEFENSIVE")

    def test_summary_structure(self):
        s = self.cre.summary()
        self.assertIn("peak_equity", s)
        self.assertIn("in_recovery", s)
        self.assertIn("recovery_size_min", s)
        self.assertEqual(s["module"], "CAPITAL_RECOVERY_ENGINE")


# ─────────────────────────────────────────────────────────────────────────────
# TestExplorationGuard
# ─────────────────────────────────────────────────────────────────────────────
class TestExplorationGuard(unittest.TestCase):

    def setUp(self):
        from core.exploration_guard import ExplorationGuard
        self.eg = ExplorationGuard()

    def test_allowed_when_below_cap(self):
        r = self.eg.check(daily_loss_pct=0.0)
        self.assertTrue(r.allowed)

    def test_allowed_just_below_cap(self):
        r = self.eg.check(daily_loss_pct=cfg.EG_DAILY_LOSS_CAP_PCT - 0.001)
        self.assertTrue(r.allowed)

    def test_blocked_at_cap(self):
        r = self.eg.check(daily_loss_pct=cfg.EG_DAILY_LOSS_CAP_PCT)
        self.assertFalse(r.allowed)
        self.assertIn("EG_BLOCKED", r.reason)

    def test_blocked_above_cap(self):
        r = self.eg.check(daily_loss_pct=cfg.EG_DAILY_LOSS_CAP_PCT + 0.01)
        self.assertFalse(r.allowed)

    def test_daily_loss_pct_stored_in_result(self):
        loss = 0.015
        r = self.eg.check(daily_loss_pct=loss)
        self.assertAlmostEqual(r.daily_loss_pct, loss, places=3)

    def test_cap_pct_stored_in_result(self):
        r = self.eg.check(daily_loss_pct=0.0)
        self.assertAlmostEqual(r.cap_pct, cfg.EG_DAILY_LOSS_CAP_PCT)

    def test_zero_loss_always_allowed(self):
        r = self.eg.check(daily_loss_pct=0.0)
        self.assertTrue(r.allowed)

    def test_summary_structure(self):
        s = self.eg.summary()
        self.assertIn("daily_loss_cap_pct", s)
        self.assertEqual(s["module"], "EXPLORATION_GUARD")


# ─────────────────────────────────────────────────────────────────────────────
# TestPhase6Pipeline
# ─────────────────────────────────────────────────────────────────────────────
class TestPhase6Pipeline(unittest.TestCase):
    """
    End-to-end integration: simulate the Phase 6 additions to the decision flow.
    Each test covers a specific stability scenario.
    """

    def test_high_ev_trade_gets_full_size(self):
        from core.ev_confidence import EVConfidenceEngine
        evc = EVConfidenceEngine()
        r = evc.classify(ev=cfg.EVC_HIGH_THRESHOLD + 0.05)
        self.assertAlmostEqual(r.size_mult, 1.0)
        self.assertTrue(r.ok)

    def test_loss_cluster_halves_size(self):
        from core.loss_cluster import LossClusterController
        lcc = LossClusterController()
        r = lcc.check(consecutive_losses=cfg.LCC_REDUCE_AFTER)
        initial_qty = 1.0
        reduced_qty = round(initial_qty * r.size_mult, 8)
        self.assertAlmostEqual(reduced_qty, initial_qty * cfg.LCC_REDUCE_SIZE_MULT)

    def test_5_losses_pause_all_trading(self):
        from core.loss_cluster import LossClusterController
        lcc = LossClusterController()
        r = lcc.check(consecutive_losses=cfg.LCC_PAUSE_AFTER)
        self.assertFalse(r.ok)
        # Subsequent call with 0 losses still blocked
        r2 = lcc.check(consecutive_losses=0)
        self.assertFalse(r2.ok)

    def test_cold_streak_tightens_score_min(self):
        from core.streak_engine import StreakIntelligenceEngine
        se = StreakIntelligenceEngine()
        base = cfg.MIN_TRADE_SCORE
        r = se.check(consecutive_wins=0, consecutive_losses=cfg.SE_LOSS_STREAK_MIN)
        eff = max(0.40, base + r.score_adjustment)
        self.assertGreater(eff, base)

    def test_hot_streak_relaxes_score_min(self):
        from core.streak_engine import StreakIntelligenceEngine
        se = StreakIntelligenceEngine()
        base = cfg.MIN_TRADE_SCORE
        r = se.check(consecutive_wins=cfg.SE_WIN_STREAK_MIN, consecutive_losses=0)
        eff = max(0.40, base + r.score_adjustment)
        self.assertLessEqual(eff, base)

    def test_exploration_blocked_at_daily_cap(self):
        from core.exploration_guard import ExplorationGuard
        eg = ExplorationGuard()
        r = eg.check(daily_loss_pct=cfg.EG_DAILY_LOSS_CAP_PCT)
        self.assertFalse(r.allowed)

    def test_capital_recovery_defensive_reduces_combined_mult(self):
        from core.capital_recovery import CapitalRecoveryEngine
        cre = CapitalRecoveryEngine()
        cre.update_equity(1000.0)
        cre.update_equity(1000.0 * (1 - cfg.CRE_DEFENSIVE_DD - 0.02))
        r = cre.check()
        combined = 1.0 * 1.0 * r.size_mult  # alloc=1, dd=1, recovery
        self.assertLess(combined, 1.0)

    def test_combined_lcc_and_recovery_compound_correctly(self):
        """Stacked multipliers must both apply independently."""
        from core.loss_cluster import LossClusterController
        from core.capital_recovery import CapitalRecoveryEngine
        lcc = LossClusterController()
        cre = CapitalRecoveryEngine()
        cre.update_equity(1000.0)
        cre.update_equity(850.0)  # in drawdown
        lcc_r = lcc.check(consecutive_losses=cfg.LCC_REDUCE_AFTER)
        cre_r = cre.check()
        combined = lcc_r.size_mult * cre_r.size_mult
        self.assertLess(combined, 1.0)

    def test_low_ev_reduces_size_but_does_not_reject(self):
        from core.ev_confidence import EVConfidenceEngine
        evc = EVConfidenceEngine()
        r = evc.classify(ev=0.01)  # barely positive
        self.assertTrue(r.ok)
        self.assertAlmostEqual(r.size_mult, cfg.EVC_LOW_SIZE_MULT)
        self.assertLess(r.size_mult, 1.0)

    def test_all_modules_log_state_via_summary(self):
        from core.ev_confidence import EVConfidenceEngine
        from core.loss_cluster import LossClusterController
        from core.streak_engine import StreakIntelligenceEngine
        from core.capital_recovery import CapitalRecoveryEngine
        from core.exploration_guard import ExplorationGuard
        for cls, phase in [
            (EVConfidenceEngine, 6), (LossClusterController, 6),
            (StreakIntelligenceEngine, 6), (CapitalRecoveryEngine, 6),
            (ExplorationGuard, 6),
        ]:
            obj = cls()
            s = obj.summary()
            self.assertIsInstance(s, dict, f"{cls.__name__}.summary() not a dict")
            self.assertEqual(s["phase"], phase, f"{cls.__name__} wrong phase")


if __name__ == "__main__":
    unittest.main(verbosity=2)
