"""
Phase 5.1 — Activation + Exploration Control test suite

Validates:
  TestTradeActivator        — freeze prevention, tiered relaxation, timer reset
  TestExplorationEngine     — 10% slot allocation, daily cap, score floor
  TestAdaptiveFilterEngine  — relax/tighten states, priority ordering
  TestSmartFeeGuard         — RR-aware fee tolerance
  TestTradeFlowMonitor      — signal/trade/skip recording, metrics
  TestPhase51Pipeline       — end-to-end integration scenarios
"""
import time
import unittest

from config import cfg


# ─────────────────────────────────────────────────────────────────────────────
# TestTradeActivator
# ─────────────────────────────────────────────────────────────────────────────
class TestTradeActivator(unittest.TestCase):

    def setUp(self):
        from core.trade_activator import TradeActivator
        self.ta = TradeActivator()

    def test_normal_when_no_wait(self):
        result = self.ta.check(minutes_no_trade=0.0)
        self.assertEqual(result.tier, "NORMAL")
        self.assertFalse(result.active)
        self.assertEqual(result.effective_score_min, cfg.MIN_TRADE_SCORE)
        self.assertEqual(result.effective_vol_mult, 1.0)

    def test_tier1_at_30_minutes(self):
        result = self.ta.check(minutes_no_trade=30.0)
        self.assertEqual(result.tier, "TIER_1")
        self.assertTrue(result.active)
        self.assertLessEqual(result.effective_score_min, cfg.ACTIVATOR_T1_SCORE)
        self.assertAlmostEqual(result.effective_vol_mult, cfg.ACTIVATOR_T1_VOL_MULT)

    def test_tier2_at_60_minutes(self):
        result = self.ta.check(minutes_no_trade=60.0)
        self.assertEqual(result.tier, "TIER_2")
        self.assertTrue(result.active)
        self.assertLessEqual(result.effective_score_min, cfg.ACTIVATOR_T2_SCORE)
        self.assertAlmostEqual(result.effective_vol_mult, cfg.ACTIVATOR_T2_VOL_MULT)

    def test_tier3_at_90_minutes(self):
        result = self.ta.check(minutes_no_trade=90.0)
        self.assertEqual(result.tier, "TIER_3")
        self.assertTrue(result.active)
        # T3 uses T2_SCORE and T3_VOL_MULT
        self.assertAlmostEqual(result.effective_vol_mult, cfg.ACTIVATOR_T3_VOL_MULT)

    def test_score_never_below_floor(self):
        """Score floor of 0.45 must hold regardless of tier."""
        for mins in [30, 60, 90, 180]:
            result = self.ta.check(minutes_no_trade=float(mins))
            self.assertGreaterEqual(result.effective_score_min, 0.45,
                                    f"Score below floor at {mins} min")

    def test_vol_mult_never_below_floor(self):
        """Volume multiplier floor of 0.20 must hold."""
        for mins in [30, 60, 90, 180]:
            result = self.ta.check(minutes_no_trade=float(mins))
            self.assertGreaterEqual(result.effective_vol_mult, 0.20,
                                    f"Vol mult below floor at {mins} min")

    def test_record_trade_resets_timer(self):
        """After record_trade(), minutes_since_last_trade() should be near 0."""
        self.ta.record_trade()
        mins = self.ta.minutes_since_last_trade()
        self.assertLess(mins, 0.1)

    def test_score_relaxes_with_increasing_freeze(self):
        """Score threshold must be ≤ at T2 compared to T1."""
        r1 = self.ta.check(minutes_no_trade=35.0)
        r2 = self.ta.check(minutes_no_trade=65.0)
        self.assertLessEqual(r2.effective_score_min, r1.effective_score_min)

    def test_summary_structure(self):
        s = self.ta.summary()
        for key in ("tier", "active", "effective_score_min",
                    "effective_vol_mult", "module", "phase"):
            self.assertIn(key, s)
        self.assertEqual(s["module"], "TRADE_ACTIVATOR")


# ─────────────────────────────────────────────────────────────────────────────
# TestExplorationEngine
# ─────────────────────────────────────────────────────────────────────────────
class TestExplorationEngine(unittest.TestCase):

    def setUp(self):
        from core.exploration_engine import ExplorationEngine
        self.eng = ExplorationEngine()

    def _fire_n_signals(self, n, score=0.50, equity=1000.0, ev_ok=False):
        results = []
        for _ in range(n):
            r = self.eng.should_explore("BTCUSDT", score=score,
                                         equity=equity, ev_ok=ev_ok)
            results.append(r)
        return results

    def test_exploration_rate_approximately_5_percent(self):
        """Every 20th slot should be exploration (EXPLORE_RATE=0.05)."""
        # score must be >= EXPLORE_SCORE_MIN (0.60) so score floor doesn't block slots
        results = self._fire_n_signals(100, score=cfg.EXPLORE_SCORE_MIN + 0.05)
        explore_count = sum(1 for r in results if r.is_exploration)
        self.assertEqual(explore_count, 5)

    def test_exploration_applies_reduced_size(self):
        """Exploration trades must use EXPLORE_SIZE_MULT."""
        results = self._fire_n_signals(20, score=cfg.EXPLORE_SCORE_MIN + 0.05)
        explore_results = [r for r in results if r.is_exploration]
        for r in explore_results:
            self.assertAlmostEqual(r.size_mult, cfg.EXPLORE_SIZE_MULT)

    def test_non_exploration_slots_use_full_size(self):
        results = self._fire_n_signals(9, score=0.80)
        for r in results:
            self.assertFalse(r.is_exploration)
            self.assertEqual(r.size_mult, 1.0)

    def test_score_below_floor_blocks_exploration(self):
        """Score < EXPLORE_SCORE_MIN must prevent exploration even on slot."""
        # Fire 9 non-slot signals to get to slot 10
        self._fire_n_signals(9, score=0.30)
        # 10th signal is the exploration slot — but score is too low
        r = self.eng.should_explore("BTCUSDT", score=0.30, equity=1000.0, ev_ok=False)
        self.assertFalse(r.is_exploration)

    def test_daily_cap_blocks_exploration_after_loss(self):
        """Exploration should stop when daily loss cap is reached."""
        equity = 1000.0
        # Record a loss that exhausts the daily cap (2% of 1000 = 20 USDT)
        self.eng.record_result("BTCUSDT", net_pnl=-20.0)
        # Now fire signals until we hit the exploration slot
        self._fire_n_signals(9, score=0.50, equity=equity)
        r = self.eng.should_explore("BTCUSDT", score=0.50, equity=equity, ev_ok=False)
        self.assertFalse(r.is_exploration, "Should be blocked by daily cap")

    def test_ev_ok_trade_does_not_become_exploration(self):
        """If ev_ok=True, exploration engine should not mark it as exploration."""
        # Get to the 10th slot
        self._fire_n_signals(9, score=0.50)
        r = self.eng.should_explore("BTCUSDT", score=0.50, equity=1000.0, ev_ok=True)
        self.assertFalse(r.is_exploration)
        self.assertEqual(r.size_mult, 1.0)

    def test_record_result_tracks_losses(self):
        equity = 1000.0
        self.eng.record_result("BTCUSDT", net_pnl=-5.0)
        pct = self.eng.daily_loss_pct(equity)
        self.assertAlmostEqual(pct, 0.005)  # 5/1000 = 0.5%

    def test_wins_not_counted_against_daily_cap(self):
        equity = 1000.0
        self.eng.record_result("BTCUSDT", net_pnl=50.0)
        self.assertAlmostEqual(self.eng.daily_loss_pct(equity), 0.0)

    def test_summary_structure(self):
        s = self.eng.summary(equity=1000.0)
        for key in ("explore_rate", "size_mult", "daily_cap_pct",
                    "daily_loss_pct", "module", "phase"):
            self.assertIn(key, s)
        self.assertEqual(s["module"], "EXPLORATION_ENGINE")


# ─────────────────────────────────────────────────────────────────────────────
# TestAdaptiveFilterEngine
# ─────────────────────────────────────────────────────────────────────────────
class TestAdaptiveFilterEngine(unittest.TestCase):

    def setUp(self):
        from core.adaptive_filter import AdaptiveFilterEngine
        self.af = AdaptiveFilterEngine()

    def test_normal_state_no_adjustment(self):
        result = self.af.check(consecutive_losses=0, minutes_no_trade=0.0)
        self.assertEqual(result.state, "NORMAL")
        self.assertEqual(result.score_offset, 0.0)
        self.assertEqual(result.effective_score_min, cfg.MIN_TRADE_SCORE)

    def test_relax_after_no_trade_period(self):
        result = self.af.check(consecutive_losses=0,
                                minutes_no_trade=float(cfg.AF_RELAX_AFTER_MIN))
        self.assertEqual(result.state, "RELAX")
        self.assertLess(result.score_offset, 0.0)
        self.assertLess(result.effective_score_min, cfg.MIN_TRADE_SCORE)

    def test_tighten_after_loss_streak(self):
        result = self.af.check(
            consecutive_losses=cfg.AF_TIGHTEN_AFTER_LOSSES,
            minutes_no_trade=0.0,
        )
        self.assertEqual(result.state, "TIGHTEN")
        self.assertGreater(result.score_offset, 0.0)
        self.assertGreater(result.effective_score_min, cfg.MIN_TRADE_SCORE)

    def test_tighten_takes_priority_over_relax(self):
        """Loss streak + long no-trade period → TIGHTEN wins."""
        result = self.af.check(
            consecutive_losses=cfg.AF_TIGHTEN_AFTER_LOSSES + 1,
            minutes_no_trade=float(cfg.AF_RELAX_AFTER_MIN + 60),
        )
        self.assertEqual(result.state, "TIGHTEN")

    def test_relax_step_increases_with_time(self):
        r1 = self.af.check(consecutive_losses=0,
                            minutes_no_trade=float(cfg.AF_RELAX_AFTER_MIN))
        r2 = self.af.check(consecutive_losses=0,
                            minutes_no_trade=float(cfg.AF_RELAX_AFTER_MIN + 30))
        self.assertGreater(abs(r2.score_offset), abs(r1.score_offset))

    def test_relax_capped_at_max(self):
        result = self.af.check(consecutive_losses=0, minutes_no_trade=9999.0)
        self.assertGreaterEqual(result.score_offset, -cfg.AF_MAX_RELAX - 1e-9)

    def test_tighten_capped_at_max(self):
        result = self.af.check(consecutive_losses=100, minutes_no_trade=0.0)
        self.assertLessEqual(result.score_offset, cfg.AF_MAX_TIGHTEN + 1e-9)

    def test_effective_score_never_below_040(self):
        result = self.af.check(consecutive_losses=0, minutes_no_trade=9999.0)
        self.assertGreaterEqual(result.effective_score_min, 0.40)

    def test_effective_score_never_above_085(self):
        result = self.af.check(consecutive_losses=100, minutes_no_trade=0.0)
        self.assertLessEqual(result.effective_score_min, 0.85)

    def test_summary_structure(self):
        s = self.af.summary()
        for key in ("state", "score_offset", "effective_score_min",
                    "base_score_min", "module", "phase"):
            self.assertIn(key, s)
        self.assertEqual(s["module"], "ADAPTIVE_FILTER")


# ─────────────────────────────────────────────────────────────────────────────
# TestSmartFeeGuard
# ─────────────────────────────────────────────────────────────────────────────
class TestSmartFeeGuard(unittest.TestCase):

    def setUp(self):
        from core.smart_fee_guard import SmartFeeGuard
        self.sg = SmartFeeGuard()

    def test_normal_rr_below_20pct_passes(self):
        # qFTD-008-EDGE: SFG_NORMAL_FEE_MAX = 0.10; use fee_cost just below
        result = self.sg.check(rr=2.0, gross_tp=100.0,
                                fee_cost=round(cfg.SFG_NORMAL_FEE_MAX * 100 * 0.9, 1))
        self.assertTrue(result.ok)
        self.assertFalse(result.high_rr)

    def test_normal_rr_above_20pct_blocked(self):
        # Fee clearly above SFG_NORMAL_FEE_MAX
        result = self.sg.check(rr=2.0, gross_tp=100.0,
                                fee_cost=round(cfg.SFG_NORMAL_FEE_MAX * 100 * 2.0, 1))
        self.assertFalse(result.ok)

    def test_high_rr_allows_up_to_35pct(self):
        # qFTD-008-EDGE: SFG_HIGH_RR_FEE_MAX = 0.15; use fee_cost just below
        result = self.sg.check(rr=4.0, gross_tp=100.0,
                                fee_cost=round(cfg.SFG_HIGH_RR_FEE_MAX * 100 * 0.9, 1))
        self.assertTrue(result.ok)
        self.assertTrue(result.high_rr)

    def test_high_rr_above_35pct_blocked(self):
        # Fee clearly above SFG_HIGH_RR_FEE_MAX
        result = self.sg.check(rr=4.0, gross_tp=100.0,
                                fee_cost=round(cfg.SFG_HIGH_RR_FEE_MAX * 100 * 2.5, 1))
        self.assertFalse(result.ok)
        self.assertTrue(result.high_rr)

    def test_rr_exactly_at_threshold_uses_high_rr(self):
        # Fee just below SFG_HIGH_RR_FEE_MAX
        result = self.sg.check(rr=cfg.SFG_HIGH_RR_THRESHOLD,
                                gross_tp=100.0,
                                fee_cost=round(cfg.SFG_HIGH_RR_FEE_MAX * 100 * 0.9, 1))
        self.assertTrue(result.ok)
        self.assertTrue(result.high_rr)

    def test_zero_gross_tp_always_passes(self):
        result = self.sg.check(rr=1.0, gross_tp=0.0, fee_cost=10.0)
        self.assertTrue(result.ok)

    def test_fee_ratio_reported_correctly(self):
        result = self.sg.check(rr=2.0, gross_tp=100.0, fee_cost=15.0)
        self.assertAlmostEqual(result.fee_ratio, 0.15, places=4)

    def test_effective_max_matches_rr_band(self):
        low_rr  = self.sg.check(rr=2.0, gross_tp=100.0, fee_cost=5.0)
        high_rr = self.sg.check(rr=5.0, gross_tp=100.0, fee_cost=5.0)
        self.assertEqual(low_rr.effective_max, cfg.SFG_NORMAL_FEE_MAX)
        self.assertEqual(high_rr.effective_max, cfg.SFG_HIGH_RR_FEE_MAX)

    def test_summary_structure(self):
        s = self.sg.summary()
        for key in ("high_rr_threshold", "high_rr_fee_max",
                    "normal_fee_max", "module", "phase"):
            self.assertIn(key, s)
        self.assertEqual(s["module"], "SMART_FEE_GUARD")


# ─────────────────────────────────────────────────────────────────────────────
# TestTradeFlowMonitor
# ─────────────────────────────────────────────────────────────────────────────
class TestTradeFlowMonitor(unittest.TestCase):

    def setUp(self):
        from core.trade_flow_monitor import TradeFlowMonitor
        self.mon = TradeFlowMonitor()

    def test_zero_minutes_since_trade_initially(self):
        """No trades recorded → returns 0.0."""
        self.assertEqual(self.mon.minutes_since_last_trade(), 0.0)

    def test_record_trade_updates_timer(self):
        self.mon.record_trade("BTCUSDT")
        mins = self.mon.minutes_since_last_trade()
        self.assertLess(mins, 0.1)

    def test_trades_per_hour_counts_correctly(self):
        for _ in range(5):
            self.mon.record_trade("BTCUSDT")
        stats = self.mon.get_stats()
        # 5 trades in a 60-min window = 5.0 trades/hour
        self.assertAlmostEqual(stats.trades_per_hour, 5.0, places=1)

    def test_signals_per_hour_counts_correctly(self):
        for _ in range(12):
            self.mon.record_signal("BTCUSDT")
        stats = self.mon.get_stats()
        self.assertAlmostEqual(stats.signals_per_hour, 12.0, places=1)

    def test_rejection_rate_computed_correctly(self):
        for _ in range(8):
            self.mon.record_skip("BTCUSDT", "WEAK_EDGE(rr=1.0)")
        for _ in range(2):
            self.mon.record_trade("BTCUSDT")
        stats = self.mon.get_stats()
        # 8 skips / (8 skips + 2 trades) = 0.80
        self.assertAlmostEqual(stats.rejection_rate, 0.80, places=2)

    def test_rejection_reasons_aggregated_by_prefix(self):
        self.mon.record_skip("BTCUSDT", "WEAK_EDGE(rr=1.0)")
        self.mon.record_skip("BTCUSDT", "WEAK_EDGE(rr=1.1)")
        self.mon.record_skip("BTCUSDT", "DECAY_FILTER(freq=5)")
        stats = self.mon.get_stats()
        self.assertIn("WEAK_EDGE", stats.top_reasons)
        self.assertEqual(stats.top_reasons["WEAK_EDGE"], 2)

    def test_rejection_rate_zero_with_no_skips(self):
        self.mon.record_trade("BTCUSDT")
        stats = self.mon.get_stats()
        self.assertEqual(stats.rejection_rate, 0.0)

    def test_top_reasons_capped_at_five(self):
        for i in range(10):
            self.mon.record_skip("BTCUSDT", f"REASON_{i}")
        stats = self.mon.get_stats()
        self.assertLessEqual(len(stats.top_reasons), 5)

    def test_summary_structure(self):
        s = self.mon.summary()
        for key in ("trades_per_hour", "signals_per_hour", "rejection_rate_pct",
                    "minutes_since_last_trade", "top_rejection_reasons",
                    "window_min", "module", "phase"):
            self.assertIn(key, s)
        self.assertEqual(s["module"], "TRADE_FLOW_MONITOR")


# ─────────────────────────────────────────────────────────────────────────────
# TestPhase51Pipeline  — end-to-end scenarios
# ─────────────────────────────────────────────────────────────────────────────
class TestPhase51Pipeline(unittest.TestCase):

    def setUp(self):
        from core.trade_activator    import TradeActivator
        from core.exploration_engine import ExplorationEngine
        from core.adaptive_filter    import AdaptiveFilterEngine
        from core.smart_fee_guard    import SmartFeeGuard
        from core.trade_flow_monitor import TradeFlowMonitor

        self.ta  = TradeActivator()
        self.exp = ExplorationEngine()
        self.af  = AdaptiveFilterEngine()
        self.sg  = SmartFeeGuard()
        self.mon = TradeFlowMonitor()

    def test_no_trade_freeze_triggers_full_relaxation_chain(self):
        """After 90 min no trade: activator T3, filter RELAX, score drops."""
        a_result = self.ta.check(minutes_no_trade=90.0)
        f_result = self.af.check(consecutive_losses=0, minutes_no_trade=90.0)
        self.assertEqual(a_result.tier, "TIER_3")
        self.assertEqual(f_result.state, "RELAX")
        # Combined effective score = min of the two relaxed values
        effective = min(a_result.effective_score_min, f_result.effective_score_min)
        self.assertLess(effective, cfg.MIN_TRADE_SCORE)

    def test_loss_streak_overrides_no_trade_relaxation(self):
        """Loss streak should tighten even when system has been quiet."""
        a_result = self.ta.check(minutes_no_trade=70.0)   # would relax
        f_result = self.af.check(consecutive_losses=4, minutes_no_trade=70.0)
        # Adaptive filter tightens despite long no-trade duration
        self.assertEqual(f_result.state, "TIGHTEN")
        self.assertGreater(f_result.effective_score_min, cfg.MIN_TRADE_SCORE)

    def test_exploration_rescues_ev_failed_signal(self):
        """When EV fails, exploration engine can rescue every Nth slot
        (qFTD-008-EDGE: EXPLORE_RATE=0.05 → period=20)."""
        equity = 1000.0
        # score must be >= EXPLORE_SCORE_MIN (0.60)
        score = cfg.EXPLORE_SCORE_MIN + 0.05
        period = max(1, round(1.0 / cfg.EXPLORE_RATE))
        # Advance counter to just before the next slot
        for _ in range(period - 1):
            self.exp.should_explore("BTCUSDT", score=score,
                                    equity=equity, ev_ok=False)
        # Nth signal — EV failed but exploration should step in
        r = self.exp.should_explore("BTCUSDT", score=score,
                                    equity=equity, ev_ok=False)
        self.assertTrue(r.is_exploration)
        self.assertEqual(r.size_mult, cfg.EXPLORE_SIZE_MULT)

    def test_high_rr_trade_passes_fee_guard_despite_high_ratio(self):
        """High-RR trade (RR=4) with fee just under SFG_HIGH_RR_FEE_MAX should pass."""
        fee = round(cfg.SFG_HIGH_RR_FEE_MAX * 100 * 0.9, 1)
        result = self.sg.check(rr=4.0, gross_tp=100.0, fee_cost=fee)
        self.assertTrue(result.ok)

    def test_normal_rr_trade_blocked_at_25pct_fee(self):
        """Normal-RR trade (RR=2) with 25% fee ratio must be blocked."""
        result = self.sg.check(rr=2.0, gross_tp=100.0, fee_cost=25.0)
        self.assertFalse(result.ok)

    def test_flow_monitor_tracks_full_signal_lifecycle(self):
        """Signal → skip → trade → verify metrics."""
        self.mon.record_signal("BTCUSDT")
        self.mon.record_skip("BTCUSDT", "WEAK_EDGE(rr=0.8)")
        self.mon.record_signal("ETHUSDT")
        self.mon.record_trade("ETHUSDT")

        stats = self.mon.get_stats()
        self.assertGreater(stats.signals_per_hour, 0)
        self.assertGreater(stats.trades_per_hour, 0)
        self.assertGreater(stats.rejection_rate, 0)

    def test_exploration_daily_cap_stops_after_limit(self):
        """Exploration must stop for the day once 2% equity is lost."""
        equity = 1000.0
        # Record a 20 USDT loss (= 2% of 1000)
        self.exp.record_result("BTCUSDT", net_pnl=-20.0)
        # All subsequent exploration slots should be blocked
        for _ in range(9):
            self.exp.should_explore("BTCUSDT", score=0.50, equity=equity)
        r = self.exp.should_explore("BTCUSDT", score=0.50,
                                    equity=equity, ev_ok=False)
        self.assertFalse(r.is_exploration,
                         "Exploration should be halted after daily cap")

    def test_activator_vol_bypass_logic(self):
        """TIER_2+ should trigger volume bypass (vol_mult ≤ 0.40)."""
        r = self.ta.check(minutes_no_trade=65.0)
        self.assertLessEqual(r.effective_vol_mult, 0.40)

    def test_record_trade_resets_freeze_condition(self):
        """After recording a trade, activator returns to NORMAL."""
        self.ta.record_trade()
        r = self.ta.check()
        self.assertEqual(r.tier, "NORMAL")


if __name__ == "__main__":
    unittest.main()
