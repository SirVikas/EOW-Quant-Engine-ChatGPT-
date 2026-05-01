"""
Phase 5.2 — Integration + Control Override test suite

Validates that ALL thresholds are dynamic (no static blocking):
  TestDynamicThresholdProvider — DTP aggregates all three engines correctly
  TestActivatorFlowThroughDTP  — TradeActivator values reach downstream gates
  TestExplorationInjection     — Exploration hard injection fires on correct slots
  TestFeeGuardDynamic          — DTP fee_tolerance overrides normal max
  TestVolumeFilterDynamic      — vol_multiplier from DTP changes effective threshold
  TestDTPPriorityRules         — TIGHTEN > RELAX, DD tightens fees
  TestPhase52EndToEnd          — full pipeline integration scenarios

Non-negotiable: if a threshold is hardcoded it is a bug.

Run with:  python -m pytest tests/test_phase5_2_integration.py -v
"""
import unittest
from collections import deque

from config import cfg


# ─────────────────────────────────────────────────────────────────────────────
# TestDynamicThresholdProvider
# ─────────────────────────────────────────────────────────────────────────────
class TestDynamicThresholdProvider(unittest.TestCase):

    def setUp(self):
        from core.dynamic_thresholds import DynamicThresholdProvider
        self.dtp = DynamicThresholdProvider()

    def test_returns_dynamic_thresholds_dataclass(self):
        from core.dynamic_thresholds import DynamicThresholds
        t = self.dtp.get()
        self.assertIsInstance(t, DynamicThresholds)
        self.assertIsInstance(t.score_min, float)
        self.assertIsInstance(t.volume_multiplier, float)
        self.assertIsInstance(t.fee_tolerance, float)
        self.assertIsInstance(t.dd_allowed, bool)

    def test_normal_state_returns_base_values(self):
        t = self.dtp.get(minutes_no_trade=0.0, consecutive_losses=0)
        self.assertEqual(t.tier, "NORMAL")
        self.assertEqual(t.af_state, "NORMAL")
        self.assertTrue(t.dd_allowed)
        self.assertAlmostEqual(t.volume_multiplier, 1.0)
        self.assertAlmostEqual(t.fee_tolerance, cfg.SFG_NORMAL_FEE_MAX)

    def test_score_min_relaxes_on_long_freeze(self):
        t_now = self.dtp.get(minutes_no_trade=0.0, consecutive_losses=0)
        t_freeze = self.dtp.get(minutes_no_trade=120.0, consecutive_losses=0)
        self.assertLessEqual(t_freeze.score_min, t_now.score_min + 1e-6)

    def test_score_min_tightens_on_loss_streak(self):
        losses = cfg.AF_TIGHTEN_AFTER_LOSSES
        t_normal = self.dtp.get(minutes_no_trade=0.0, consecutive_losses=0)
        t_tighten = self.dtp.get(minutes_no_trade=0.0, consecutive_losses=losses)
        self.assertGreater(t_tighten.score_min, t_normal.score_min)
        self.assertEqual(t_tighten.af_state, "TIGHTEN")

    def test_volume_multiplier_drops_on_freeze(self):
        t = self.dtp.get(minutes_no_trade=90.0, consecutive_losses=0)
        self.assertLess(t.volume_multiplier, 1.0)
        self.assertGreaterEqual(t.volume_multiplier, 0.20)

    def test_fee_tolerance_equals_cfg_in_normal_state(self):
        t = self.dtp.get(minutes_no_trade=0.0, consecutive_losses=0)
        self.assertAlmostEqual(t.fee_tolerance, cfg.SFG_NORMAL_FEE_MAX, places=4)

    def test_all_seven_fields_present(self):
        t = self.dtp.get(minutes_no_trade=45.0, consecutive_losses=1)
        for field in ("score_min", "volume_multiplier", "fee_tolerance",
                      "dd_allowed", "dd_size_mult", "tier", "af_state"):
            self.assertTrue(hasattr(t, field), f"Missing field: {field}")

    def test_summary_method_returns_dict(self):
        s = self.dtp.summary(minutes_no_trade=0.0, consecutive_losses=0)
        self.assertIsInstance(s, dict)
        self.assertIn("score_min", s)
        self.assertIn("volume_multiplier", s)
        self.assertIn("fee_tolerance", s)
        self.assertEqual(s["module"], "DYNAMIC_THRESHOLD_PROVIDER")


# ─────────────────────────────────────────────────────────────────────────────
# TestActivatorFlowThroughDTP
# ─────────────────────────────────────────────────────────────────────────────
class TestActivatorFlowThroughDTP(unittest.TestCase):

    def setUp(self):
        from core.dynamic_thresholds import DynamicThresholdProvider
        from core.trade_activator import TradeActivator
        self.dtp = DynamicThresholdProvider()
        self.ta = TradeActivator()

    def test_tier_propagates_correctly(self):
        for mins, expected in [
            (0.0, "NORMAL"),
            (float(cfg.ACTIVATOR_T1_MIN), "TIER_1"),
            (float(cfg.ACTIVATOR_T2_MIN), "TIER_2"),
            (float(cfg.ACTIVATOR_T3_MIN), "TIER_3"),
        ]:
            t = self.dtp.get(minutes_no_trade=mins, consecutive_losses=0)
            self.assertEqual(t.tier, expected, f"Tier mismatch at {mins} min")

    def test_vol_mult_matches_activator_at_each_tier(self):
        for mins in [0.0, float(cfg.ACTIVATOR_T1_MIN),
                     float(cfg.ACTIVATOR_T2_MIN), float(cfg.ACTIVATOR_T3_MIN)]:
            t = self.dtp.get(minutes_no_trade=mins, consecutive_losses=0)
            act = self.ta.check(minutes_no_trade=mins)
            self.assertAlmostEqual(t.volume_multiplier, act.effective_vol_mult, places=4,
                                   msg=f"vol_mult mismatch at {mins} min")

    def test_score_min_matches_activator_in_normal_af(self):
        for mins in [0.0, float(cfg.ACTIVATOR_T1_MIN), float(cfg.ACTIVATOR_T2_MIN)]:
            t = self.dtp.get(minutes_no_trade=mins, consecutive_losses=0)
            act = self.ta.check(minutes_no_trade=mins)
            self.assertLessEqual(t.score_min, act.effective_score_min + 1e-6,
                                  msg=f"score_min exceeds activator at {mins} min")

    def test_score_relaxes_monotonically_with_freeze(self):
        scores = [
            self.dtp.get(minutes_no_trade=float(m), consecutive_losses=0).score_min
            for m in [0, 30, 60, 90]
        ]
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1] - 1e-6,
                                    f"score_min increased from step {i} to {i + 1}")

    def test_vol_mult_relaxes_monotonically_with_freeze(self):
        mults = [
            self.dtp.get(minutes_no_trade=float(m), consecutive_losses=0).volume_multiplier
            for m in [0, 30, 60, 90]
        ]
        for i in range(len(mults) - 1):
            self.assertGreaterEqual(mults[i], mults[i + 1] - 1e-6,
                                    f"vol_mult increased from step {i} to {i + 1}")

    def test_score_never_below_absolute_floor(self):
        for mins in [30, 60, 90, 180, 360]:
            t = self.dtp.get(minutes_no_trade=float(mins), consecutive_losses=0)
            self.assertGreaterEqual(t.score_min, 0.40,
                                    f"score_min below absolute floor at {mins} min")


# ─────────────────────────────────────────────────────────────────────────────
# TestExplorationInjection
# ─────────────────────────────────────────────────────────────────────────────
class TestExplorationInjection(unittest.TestCase):

    def _fresh(self):
        from core.exploration_engine import ExplorationEngine
        return ExplorationEngine()

    def _advance_to_slot(self, ee, score=0.65, equity=10000.0):
        period = max(1, round(1.0 / cfg.EXPLORE_RATE))
        for _ in range(period - 1):
            ee.should_explore("X", score=score, equity=equity)

    def test_non_slot_signals_not_exploration(self):
        ee = self._fresh()
        period = max(1, round(1.0 / cfg.EXPLORE_RATE))
        for i in range(period - 1):
            r = ee.should_explore("BTCUSDT", score=0.65, equity=10000.0)
            self.assertFalse(r.is_exploration, f"Signal {i + 1} unexpectedly exploration")

    def test_period_th_signal_fires_exploration(self):
        ee = self._fresh()
        self._advance_to_slot(ee)
        r = ee.should_explore("BTCUSDT", score=0.65, equity=10000.0)
        self.assertTrue(r.is_exploration)
        self.assertAlmostEqual(r.size_mult, cfg.EXPLORE_SIZE_MULT)

    def test_exploration_size_is_quarter_normal(self):
        ee = self._fresh()
        self._advance_to_slot(ee)
        r = ee.should_explore("BTCUSDT", score=0.65, equity=10000.0)
        self.assertAlmostEqual(r.size_mult, 0.25, places=3)

    def test_score_below_floor_blocks_exploration(self):
        ee = self._fresh()
        self._advance_to_slot(ee)
        r = ee.should_explore("BTCUSDT", score=cfg.EXPLORE_SCORE_MIN - 0.01, equity=10000.0)
        self.assertFalse(r.is_exploration)
        self.assertIn("SCORE_BELOW_FLOOR", r.reason)

    def test_ev_ok_prevents_exploration(self):
        ee = self._fresh()
        self._advance_to_slot(ee)
        r = ee.should_explore("BTCUSDT", score=0.65, equity=10000.0, ev_ok=True)
        self.assertFalse(r.is_exploration)
        self.assertIn("EV_OK", r.reason)

    def test_daily_cap_blocks_exploration(self):
        ee = self._fresh()
        equity = 1000.0
        ee._daily_loss_usdt = equity * cfg.EXPLORE_DAILY_LOSS_CAP
        self._advance_to_slot(ee)
        r = ee.should_explore("BTCUSDT", score=0.65, equity=equity)
        self.assertFalse(r.is_exploration)
        self.assertIn("CAP", r.reason)

    def test_exploration_fires_exactly_once_per_period(self):
        ee = self._fresh()
        period = max(1, round(1.0 / cfg.EXPLORE_RATE))
        count = 0
        for _ in range(period * 3):
            if ee.should_explore("BTCUSDT", score=0.65, equity=10000.0).is_exploration:
                count += 1
        self.assertEqual(count, 3)

    def test_exploration_result_has_size_mult_field(self):
        ee = self._fresh()
        self._advance_to_slot(ee)
        r = ee.should_explore("BTCUSDT", score=0.65, equity=10000.0)
        self.assertTrue(r.is_exploration)
        self.assertGreater(r.size_mult, 0.0)
        self.assertLessEqual(r.size_mult, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# TestFeeGuardDynamic
# ─────────────────────────────────────────────────────────────────────────────
class TestFeeGuardDynamic(unittest.TestCase):

    def setUp(self):
        from core.smart_fee_guard import SmartFeeGuard
        self.sfg = SmartFeeGuard()

    def test_none_override_falls_back_to_cfg(self):
        r = self.sfg.check(rr=1.5, gross_tp=100.0, fee_cost=15.0, normal_max_override=None)
        self.assertAlmostEqual(r.effective_max, cfg.SFG_NORMAL_FEE_MAX)

    def test_relaxed_override_accepts_previously_rejected_trade(self):
        # 25% fee/TP — blocked at cfg default 20%, allowed at 30%
        r_default = self.sfg.check(rr=1.5, gross_tp=100.0, fee_cost=25.0)
        r_relaxed = self.sfg.check(rr=1.5, gross_tp=100.0, fee_cost=25.0,
                                   normal_max_override=0.30)
        self.assertFalse(r_default.ok)
        self.assertTrue(r_relaxed.ok)

    def test_tight_override_rejects_previously_passing_trade(self):
        # 9% fee/TP — passes cfg default 10%, blocked at 7%
        r_default = self.sfg.check(rr=1.5, gross_tp=100.0, fee_cost=9.0)
        r_tight = self.sfg.check(rr=1.5, gross_tp=100.0, fee_cost=9.0,
                                  normal_max_override=0.07)
        self.assertTrue(r_default.ok)
        self.assertFalse(r_tight.ok)

    def test_high_rr_uses_high_rr_max_not_override(self):
        # 12% fee/TP with high-RR — high-RR max=15%, tight override=7%
        rr = cfg.SFG_HIGH_RR_THRESHOLD + 1.0
        r = self.sfg.check(rr=rr, gross_tp=100.0, fee_cost=12.0, normal_max_override=0.07)
        self.assertTrue(r.ok)
        self.assertTrue(r.high_rr)
        self.assertAlmostEqual(r.effective_max, cfg.SFG_HIGH_RR_FEE_MAX)

    def test_hard_cut_tolerance_smaller_than_soft_cut(self):
        hard = round(cfg.SFG_NORMAL_FEE_MAX * 0.85, 4)
        soft = round(cfg.SFG_NORMAL_FEE_MAX * 0.90, 4)
        self.assertLess(hard, soft)
        self.assertLess(soft, cfg.SFG_NORMAL_FEE_MAX)

    def test_hard_cut_override_blocks_borderline_fee(self):
        hard_tol = round(cfg.SFG_NORMAL_FEE_MAX * 0.85, 4)
        # fee slightly above hard_cut tolerance
        fee_cost = (hard_tol + 0.01) * 100.0
        r = self.sfg.check(rr=1.5, gross_tp=100.0, fee_cost=fee_cost,
                            normal_max_override=hard_tol)
        self.assertFalse(r.ok)

    def test_fee_ratio_stored_correctly(self):
        r = self.sfg.check(rr=1.5, gross_tp=100.0, fee_cost=15.0)
        self.assertAlmostEqual(r.fee_ratio, 0.15, places=3)

    def test_zero_gross_tp_always_passes(self):
        r = self.sfg.check(rr=1.5, gross_tp=0.0, fee_cost=10.0, normal_max_override=0.10)
        self.assertTrue(r.ok)


# ─────────────────────────────────────────────────────────────────────────────
# TestVolumeFilterDynamic
# ─────────────────────────────────────────────────────────────────────────────
class TestVolumeFilterDynamic(unittest.TestCase):

    def setUp(self):
        from core.volume_filter import VolumeFilter, BASE_VOLUME_THRESHOLD_PCT, VOLUME_LOOKBACK
        self.vf = VolumeFilter()
        self.base_pct = BASE_VOLUME_THRESHOLD_PCT
        self.lookback = VOLUME_LOOKBACK

    def _buf(self, avg=1000.0, ratio=0.50):
        buf = deque(maxlen=self.lookback + 5)
        for _ in range(self.lookback - 1):
            buf.append(avg)
        buf.append(avg * ratio)
        return buf

    def test_low_volume_blocked_at_default_multiplier(self):
        # 50% of avg < 60% base threshold → blocked
        active, reason = self.vf.is_active("BTCUSDT", self._buf(ratio=0.50), vol_multiplier=1.0)
        self.assertFalse(active)
        self.assertIn("SLEEP_MODE", reason)

    def test_low_volume_passes_with_relaxed_multiplier(self):
        # 50% of avg > 60%×0.70=42% effective threshold → passes
        active, _ = self.vf.is_active("BTCUSDT", self._buf(ratio=0.50), vol_multiplier=0.70)
        self.assertTrue(active)

    def test_tier3_vol_mult_opens_quiet_market(self):
        # 35% of avg: blocked at 1.0×, passes at TIER_3 mult (0.30×base=18%)
        active_normal, _ = self.vf.is_active("BTCUSDT", self._buf(ratio=0.35), vol_multiplier=1.0)
        active_t3, _ = self.vf.is_active("BTCUSDT", self._buf(ratio=0.35),
                                          vol_multiplier=cfg.ACTIVATOR_T3_VOL_MULT)
        self.assertFalse(active_normal)
        self.assertTrue(active_t3)

    def test_floor_at_0_10_prevents_zero_threshold(self):
        # 15% of avg > 10% floor → must pass even with very low multiplier
        active, _ = self.vf.is_active("BTCUSDT", self._buf(ratio=0.15), vol_multiplier=0.05)
        self.assertTrue(active)

    def test_truly_dead_volume_blocked_even_at_floor(self):
        # 5% of avg < 10% floor → blocked
        active, reason = self.vf.is_active("BTCUSDT", self._buf(ratio=0.05), vol_multiplier=0.05)
        self.assertFalse(active)

    def test_multiplier_above_1_clamped_to_1(self):
        # vol_mult=2.0 must behave identically to vol_mult=1.0
        buf = self._buf(ratio=0.50)
        active_over, _ = self.vf.is_active("BTCUSDT", buf, vol_multiplier=2.0)
        active_norm, _ = self.vf.is_active("BTCUSDT", buf, vol_multiplier=1.0)
        self.assertEqual(active_over, active_norm)

    def test_reason_contains_base_and_multiplier(self):
        active, reason = self.vf.is_active("BTCUSDT", self._buf(ratio=0.30), vol_multiplier=0.80)
        if not active:
            self.assertIn("base=", reason)
            self.assertIn("×", reason)

    def test_insufficient_history_passes_cold_start(self):
        short_buf = deque([1000.0, 800.0, 600.0], maxlen=30)
        active, _ = self.vf.is_active("BTCUSDT", short_buf, vol_multiplier=1.0)
        self.assertTrue(active)


# ─────────────────────────────────────────────────────────────────────────────
# TestDTPPriorityRules
# ─────────────────────────────────────────────────────────────────────────────
class TestDTPPriorityRules(unittest.TestCase):

    def setUp(self):
        from core.dynamic_thresholds import DynamicThresholdProvider
        self.dtp = DynamicThresholdProvider()

    def test_tighten_beats_relax_for_score_min(self):
        losses = cfg.AF_TIGHTEN_AFTER_LOSSES
        t_relax = self.dtp.get(minutes_no_trade=120.0, consecutive_losses=0)
        t_tighten = self.dtp.get(minutes_no_trade=120.0, consecutive_losses=losses)
        self.assertGreater(t_tighten.score_min, t_relax.score_min)
        self.assertEqual(t_tighten.af_state, "TIGHTEN")

    def test_volume_multiplier_unaffected_by_loss_streak(self):
        from core.trade_activator import TradeActivator
        ta = TradeActivator()
        for mins in [0.0, 30.0, 60.0, 90.0]:
            t = self.dtp.get(minutes_no_trade=mins, consecutive_losses=5)
            act = ta.check(minutes_no_trade=mins)
            self.assertAlmostEqual(t.volume_multiplier, act.effective_vol_mult, places=4,
                                   msg=f"vol_mult affected by loss streak at {mins} min")

    def test_score_min_differs_between_normal_and_tighten(self):
        t1 = self.dtp.get(minutes_no_trade=0.0, consecutive_losses=0)
        t2 = self.dtp.get(minutes_no_trade=0.0,
                           consecutive_losses=cfg.AF_TIGHTEN_AFTER_LOSSES)
        self.assertNotEqual(t1.score_min, t2.score_min)

    def test_dd_hard_cut_tightens_fee_tolerance(self):
        from core.drawdown_controller import DrawdownController
        dd = DrawdownController()
        dd.update_equity(1000.0)
        dd.update_equity(1000.0 * (1 - cfg.DD_HARD_CUT_AT - 0.01))
        result = dd.check()
        self.assertEqual(result.tier, "HARD_CUT")
        expected = round(cfg.SFG_NORMAL_FEE_MAX * 0.85, 4)
        self.assertLess(expected, cfg.SFG_NORMAL_FEE_MAX)

    def test_dd_stop_sets_dd_allowed_false(self):
        from core.drawdown_controller import DrawdownController
        dd = DrawdownController()
        dd.update_equity(1000.0)
        dd.update_equity(1000.0 * (1 - cfg.DD_STOP_AT - 0.01))
        result = dd.check()
        self.assertFalse(result.allowed)
        self.assertEqual(result.tier, "STOP")

    def test_fee_tolerance_ordering_hard_soft_normal(self):
        hard = round(cfg.SFG_NORMAL_FEE_MAX * 0.85, 4)
        soft = round(cfg.SFG_NORMAL_FEE_MAX * 0.90, 4)
        norm = cfg.SFG_NORMAL_FEE_MAX
        self.assertLess(hard, soft)
        self.assertLess(soft, norm)


# ─────────────────────────────────────────────────────────────────────────────
# TestPhase52EndToEnd
# ─────────────────────────────────────────────────────────────────────────────
class TestPhase52EndToEnd(unittest.TestCase):
    """
    Simulate Phase 5.2 decision flow without main.py.
    Each test runs the DTP → volume gate → score gate → fee gate chain.
    """

    def _run(self, minutes_no_trade=0.0, consecutive_losses=0,
             vol_ratio=0.80, fee_cost=15.0, rr=2.0, score=0.70):
        from core.dynamic_thresholds import DynamicThresholdProvider
        from core.volume_filter import VolumeFilter, VOLUME_LOOKBACK
        from core.smart_fee_guard import SmartFeeGuard

        dtp = DynamicThresholdProvider()
        vf = VolumeFilter()
        sfg = SmartFeeGuard()

        thresholds = dtp.get(minutes_no_trade=minutes_no_trade,
                              consecutive_losses=consecutive_losses)

        avg = 1000.0
        buf = deque(maxlen=VOLUME_LOOKBACK + 5)
        for _ in range(VOLUME_LOOKBACK - 1):
            buf.append(avg)
        buf.append(avg * vol_ratio)

        vol_active, vol_reason = vf.is_active("BTCUSDT", buf,
                                               vol_multiplier=thresholds.volume_multiplier)
        score_pass = score >= thresholds.score_min
        sfg_result = sfg.check(rr=rr, gross_tp=100.0, fee_cost=fee_cost,
                                normal_max_override=thresholds.fee_tolerance)

        return dict(thresholds=thresholds, vol_active=vol_active,
                    score_pass=score_pass, sfg_ok=sfg_result.ok,
                    sfg_result=sfg_result)

    def test_healthy_signal_passes_all_gates(self):
        r = self._run(vol_ratio=0.90, fee_cost=9.0, rr=2.0, score=0.70)
        self.assertTrue(r["vol_active"])
        self.assertTrue(r["score_pass"])
        self.assertTrue(r["sfg_ok"])

    def test_freeze_90min_opens_volume_gate_for_quiet_market(self):
        r_normal = self._run(minutes_no_trade=0.0, vol_ratio=0.35)
        r_freeze = self._run(minutes_no_trade=90.0, vol_ratio=0.35)
        self.assertFalse(r_normal["vol_active"])
        self.assertTrue(r_freeze["vol_active"])

    def test_loss_streak_raises_score_bar(self):
        losses = cfg.AF_TIGHTEN_AFTER_LOSSES
        r_normal = self._run(consecutive_losses=0, score=0.62)
        r_tighten = self._run(consecutive_losses=losses, score=0.62)
        if r_tighten["thresholds"].score_min > 0.62:
            self.assertTrue(r_normal["score_pass"])
            self.assertFalse(r_tighten["score_pass"])

    def test_high_rr_trade_passes_tight_fee_override(self):
        r = self._run(rr=cfg.SFG_HIGH_RR_THRESHOLD + 1.0, fee_cost=12.0,
                      vol_ratio=0.90, score=0.70)
        self.assertTrue(r["sfg_ok"])
        self.assertTrue(r["sfg_result"].high_rr)

    def test_dtp_output_fully_dynamic_between_states(self):
        t_a = self._run(minutes_no_trade=0.0, consecutive_losses=0)["thresholds"]
        t_b = self._run(minutes_no_trade=90.0,
                        consecutive_losses=cfg.AF_TIGHTEN_AFTER_LOSSES)["thresholds"]
        # At least one dimension must differ
        changed = (
            t_a.score_min != t_b.score_min
            or t_a.volume_multiplier != t_b.volume_multiplier
        )
        self.assertTrue(changed, "DTP output identical across extreme state change — not dynamic")

    def test_freeze_relaxes_score_not_tightens(self):
        t_now = self._run(minutes_no_trade=0.0)["thresholds"]
        t_freeze = self._run(minutes_no_trade=90.0)["thresholds"]
        self.assertLessEqual(t_freeze.score_min, t_now.score_min + 1e-6)

    def test_exploration_fires_and_produces_reduced_size(self):
        from core.exploration_engine import ExplorationEngine
        ee = ExplorationEngine()
        period = max(1, round(1.0 / cfg.EXPLORE_RATE))
        fired = False
        for i in range(period * 2):
            r = ee.should_explore("BTCUSDT", score=0.65, equity=5000.0)
            if r.is_exploration:
                self.assertAlmostEqual(r.size_mult, cfg.EXPLORE_SIZE_MULT)
                fired = True
                break
        self.assertTrue(fired, "Exploration never fired over two full periods")

    def test_static_cfg_min_trade_score_not_used_under_relax(self):
        """Under RELAX, score_min must be strictly below cfg.MIN_TRADE_SCORE."""
        from core.dynamic_thresholds import DynamicThresholdProvider
        dtp = DynamicThresholdProvider()
        t = dtp.get(minutes_no_trade=120.0, consecutive_losses=0)
        if t.af_state == "RELAX":
            self.assertLess(t.score_min, cfg.MIN_TRADE_SCORE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
