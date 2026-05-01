"""
EOW Quant Engine — Phase 7 Verifier
Tests: TradeRanker, CapitalConcentrator, EdgeAmplifier,
       TradeCompetitionEngine, EdgeMemoryEngine
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from core.trade_ranker import TradeRanker, RankResult
from core.capital_concentrator import CapitalConcentrator, ConcentrationResult
from core.edge_amplifier import EdgeAmplifier, AmplifyResult
from core.trade_competition import TradeCompetitionEngine, TradeCandidate
from core.edge_memory import EdgeMemoryEngine
from config import cfg


# ═══════════════════════════════════════════════════════════════════════════════
# TradeRanker
# ═══════════════════════════════════════════════════════════════════════════════

class TestTradeRanker:

    def setup_method(self):
        self.ranker = TradeRanker()

    def test_strong_trade_passes(self):
        result = self.ranker.rank(
            ev=0.20, trade_score=0.85,
            regime="TRENDING", strategy="TrendFollowing",
            history_score=0.70,
        )
        assert result.ok is True
        assert result.rank_score >= cfg.TR_MIN_RANK_SCORE

    def test_weak_trade_rejected(self):
        result = self.ranker.rank(
            ev=0.01, trade_score=0.40,
            regime="UNKNOWN", strategy="TrendFollowing",
            history_score=0.20,
        )
        assert result.ok is False
        assert result.rank_score < cfg.TR_MIN_RANK_SCORE

    def test_negative_ev_lowers_rank(self):
        pos = self.ranker.rank(
            ev=0.15, trade_score=0.75, regime="TRENDING",
            strategy="TrendFollowing", history_score=0.5,
        )
        neg = self.ranker.rank(
            ev=-0.10, trade_score=0.75, regime="TRENDING",
            strategy="TrendFollowing", history_score=0.5,
        )
        assert pos.rank_score > neg.rank_score

    def test_regime_alignment_affects_rank(self):
        aligned = self.ranker.rank(
            ev=0.10, trade_score=0.70, regime="TRENDING",
            strategy="TrendFollowing", history_score=0.5,
        )
        misaligned = self.ranker.rank(
            ev=0.10, trade_score=0.70, regime="TRENDING",
            strategy="MeanReversion", history_score=0.5,
        )
        assert aligned.rank_score > misaligned.rank_score

    def test_history_score_none_uses_neutral(self):
        with_neutral = self.ranker.rank(
            ev=0.12, trade_score=0.70, regime="TRENDING",
            strategy="TrendFollowing", history_score=None,
        )
        with_explicit_half = self.ranker.rank(
            ev=0.12, trade_score=0.70, regime="TRENDING",
            strategy="TrendFollowing", history_score=0.5,
        )
        assert with_neutral.rank_score == with_explicit_half.rank_score

    def test_components_sum_correctly(self):
        result = self.ranker.rank(
            ev=0.45, trade_score=1.0, regime="TRENDING",
            strategy="TrendFollowing", history_score=1.0,
        )
        assert result.ok is True
        assert 0.0 <= result.rank_score <= 1.0

    def test_summary_returns_phase7(self):
        s = self.ranker.summary()
        assert s["phase"] == 7
        assert s["module"] == "TRADE_RANKER"


# ═══════════════════════════════════════════════════════════════════════════════
# CapitalConcentrator
# ═══════════════════════════════════════════════════════════════════════════════

class TestCapitalConcentrator:

    def setup_method(self):
        self.cc = CapitalConcentrator()

    def test_elite_band_gets_max_multiplier(self):
        result = self.cc.concentrate(
            rank_score=0.95, equity=10_000, base_risk_usdt=100, upstream_mult=1.0
        )
        assert result.ok is True
        assert result.band == "ELITE"
        assert result.size_multiplier == pytest.approx(cfg.CC_MULT_ELITE, abs=0.01)

    def test_high_band(self):
        result = self.cc.concentrate(
            rank_score=0.85, equity=10_000, base_risk_usdt=100, upstream_mult=1.0
        )
        assert result.band == "HIGH"
        assert result.size_multiplier == pytest.approx(cfg.CC_MULT_HIGH, abs=0.01)

    def test_mid_band(self):
        result = self.cc.concentrate(
            rank_score=0.75, equity=10_000, base_risk_usdt=100, upstream_mult=1.0
        )
        assert result.band == "MID"
        assert result.size_multiplier == pytest.approx(cfg.CC_MULT_MID, abs=0.01)

    def test_low_band(self):
        result = self.cc.concentrate(
            rank_score=0.65, equity=10_000, base_risk_usdt=100, upstream_mult=1.0
        )
        assert result.band == "LOW"
        assert result.size_multiplier == pytest.approx(cfg.CC_MULT_LOW, abs=0.01)

    def test_below_min_rank_rejected(self):
        result = self.cc.concentrate(
            rank_score=0.45, equity=10_000, base_risk_usdt=100, upstream_mult=1.0
        )
        assert result.ok is False
        assert result.size_multiplier == 0.0

    def test_equity_cap_enforced(self):
        # base_risk=1000 × elite mult=2.0 → proposed 2000, but 5% of 10k = 500 cap
        result = self.cc.concentrate(
            rank_score=0.95, equity=10_000, base_risk_usdt=1000, upstream_mult=1.0
        )
        assert result.capped is True
        assert result.max_risk_usdt <= 10_000 * cfg.CC_MAX_POSITION_PCT

    def test_upstream_mult_applied(self):
        # upstream_mult=0.5 should halve the final size
        result_full = self.cc.concentrate(
            rank_score=0.75, equity=10_000, base_risk_usdt=100, upstream_mult=1.0
        )
        result_half = self.cc.concentrate(
            rank_score=0.75, equity=10_000, base_risk_usdt=100, upstream_mult=0.5
        )
        assert result_half.size_multiplier < result_full.size_multiplier

    def test_higher_rank_more_capital(self):
        elite = self.cc.concentrate(0.95, 10_000, 100, 1.0)
        low   = self.cc.concentrate(0.65, 10_000, 100, 1.0)
        assert elite.size_multiplier > low.size_multiplier

    def test_summary_phase7(self):
        s = self.cc.summary()
        assert s["phase"] == 7


# ═══════════════════════════════════════════════════════════════════════════════
# EdgeAmplifier
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeAmplifier:

    def setup_method(self):
        self.amp = EdgeAmplifier()

    def test_all_conditions_met_amplifies(self):
        result = self.amp.evaluate(
            ev=cfg.EA_EV_THRESHOLD + 0.05,
            rank_score=cfg.EA_RANK_THRESHOLD + 0.05,
            regime="TRENDING",
            volume_ratio=cfg.EA_VOL_RATIO_THRESHOLD + 0.5,
        )
        assert result.amplified is True
        assert result.tp_multiplier == cfg.EA_TP_BOOST_MULT
        assert result.trail_multiplier == cfg.EA_TRAIL_BOOST_MULT

    def test_low_ev_no_amplify(self):
        result = self.amp.evaluate(
            ev=0.01, rank_score=0.90, regime="TRENDING", volume_ratio=2.0
        )
        assert result.amplified is False
        assert result.tp_multiplier == 1.0

    def test_wrong_regime_no_amplify(self):
        result = self.amp.evaluate(
            ev=0.20, rank_score=0.90, regime="MEAN_REVERTING", volume_ratio=2.0
        )
        assert result.amplified is False

    def test_low_volume_no_amplify(self):
        result = self.amp.evaluate(
            ev=0.20, rank_score=0.90, regime="TRENDING", volume_ratio=0.5
        )
        assert result.amplified is False

    def test_low_rank_no_amplify(self):
        result = self.amp.evaluate(
            ev=0.20, rank_score=0.50, regime="TRENDING", volume_ratio=2.0
        )
        assert result.amplified is False

    def test_volatility_expansion_regime_amplifies(self):
        result = self.amp.evaluate(
            ev=cfg.EA_EV_THRESHOLD + 0.05,
            rank_score=cfg.EA_RANK_THRESHOLD + 0.05,
            regime="VOLATILITY_EXPANSION",
            volume_ratio=cfg.EA_VOL_RATIO_THRESHOLD + 0.5,
        )
        assert result.amplified is True

    def test_tp_multiplier_above_1_when_amplified(self):
        result = self.amp.evaluate(
            ev=0.20, rank_score=0.90,
            regime="TRENDING", volume_ratio=2.0,
        )
        assert result.tp_multiplier >= 1.0

    def test_summary_phase7(self):
        s = self.amp.summary()
        assert s["phase"] == 7


# ═══════════════════════════════════════════════════════════════════════════════
# TradeCompetitionEngine
# ═══════════════════════════════════════════════════════════════════════════════

class TestTradeCompetitionEngine:

    def setup_method(self):
        self.engine = TradeCompetitionEngine()

    def _make(self, signal_id: str, rank: float, ev: float = 0.10) -> TradeCandidate:
        return TradeCandidate(signal_id=signal_id, rank_score=rank, ev=ev)

    def test_top_n_selected(self):
        candidates = [
            self._make("A", 0.90),
            self._make("B", 0.85),
            self._make("C", 0.80),
            self._make("D", 0.70),
            self._make("E", 0.65),
        ]
        result = self.engine.select(candidates)
        assert len(result.winners) == cfg.TCE_MAX_CONCURRENT
        winner_ids = {w.signal_id for w in result.winners}
        assert "A" in winner_ids
        assert "B" in winner_ids
        assert "C" in winner_ids

    def test_weak_trades_rejected(self):
        # TR_MIN_RANK_SCORE=0.30 — B with rank=0.20 is below threshold and must be rejected
        candidates = [self._make("A", 0.90), self._make("B", 0.20)]
        result = self.engine.select(candidates)
        loser_ids = {l.signal_id for l in result.losers}
        assert "B" in loser_ids

    def test_fewer_than_max_all_accepted(self):
        candidates = [self._make("A", 0.85), self._make("B", 0.75)]
        result = self.engine.select(candidates)
        assert len(result.winners) == 2
        assert len(result.losers) == 0

    def test_empty_input(self):
        result = self.engine.select([])
        assert result.winners == []
        assert result.losers == []

    def test_ev_tiebreak(self):
        candidates = [
            self._make("A", 0.80, ev=0.10),
            self._make("B", 0.80, ev=0.20),
            self._make("C", 0.80, ev=0.05),
            self._make("D", 0.80, ev=0.15),
        ]
        result = self.engine.select(candidates)
        winner_ids = [w.signal_id for w in result.winners]
        # B (0.20 EV), D (0.15 EV), A (0.10 EV) should be top 3
        assert winner_ids[0] == "B"
        assert winner_ids[1] == "D"
        assert winner_ids[2] == "A"

    def test_cycle_id_increments(self):
        c1 = self.engine.select([self._make("X", 0.80)])
        c2 = self.engine.select([self._make("Y", 0.80)])
        assert c2.cycle_id == c1.cycle_id + 1

    def test_all_below_threshold_all_rejected(self):
        # TR_MIN_RANK_SCORE=0.30 — all ranks strictly below threshold
        candidates = [
            self._make("A", 0.10),
            self._make("B", 0.15),
            self._make("C", 0.20),
        ]
        result = self.engine.select(candidates)
        assert len(result.winners) == 0
        assert len(result.losers) == 3

    def test_summary_phase7(self):
        s = self.engine.summary()
        assert s["phase"] == 7


# ═══════════════════════════════════════════════════════════════════════════════
# EdgeMemoryEngine
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeMemoryEngine:

    def setup_method(self):
        self.mem = EdgeMemoryEngine()

    def test_insufficient_data_returns_neutral(self):
        result = self.mem.query("TrendFollowing", "BTCUSDT", "TRENDING")
        assert result.state == "INSUFFICIENT"
        assert result.history_score == 0.5

    def test_high_win_rate_boosts_score(self):
        for _ in range(cfg.EM_MIN_TRADES + 5):
            self.mem.record_outcome("TrendFollowing", "BTCUSDT", "TRENDING", won=True)
        result = self.mem.query("TrendFollowing", "BTCUSDT", "TRENDING")
        assert result.state == "BOOSTED"
        assert result.history_score > 0.5

    def test_low_win_rate_penalizes_score(self):
        for _ in range(cfg.EM_MIN_TRADES + 5):
            self.mem.record_outcome("TrendFollowing", "ETHUSDT", "TRENDING", won=False)
        result = self.mem.query("TrendFollowing", "ETHUSDT", "TRENDING")
        assert result.state == "PENALIZED"
        assert result.history_score < 0.5

    def test_neutral_win_rate_neutral_score(self):
        n = cfg.EM_MIN_TRADES + 4
        for i in range(n):
            # 50% win rate
            self.mem.record_outcome("MeanReversion", "BNBUSDT", "MEAN_REVERTING", won=(i % 2 == 0))
        result = self.mem.query("MeanReversion", "BNBUSDT", "MEAN_REVERTING")
        assert result.state == "NEUTRAL"
        assert result.history_score == pytest.approx(0.5, abs=0.01)

    def test_keys_are_independent(self):
        for _ in range(cfg.EM_MIN_TRADES + 2):
            self.mem.record_outcome("TrendFollowing", "SOLUSDT", "TRENDING", won=True)
            self.mem.record_outcome("MeanReversion", "SOLUSDT", "TRENDING", won=False)
        r_trend = self.mem.query("TrendFollowing", "SOLUSDT", "TRENDING")
        r_mean  = self.mem.query("MeanReversion",  "SOLUSDT", "TRENDING")
        assert r_trend.history_score > r_mean.history_score

    def test_rolling_window_evicts_old_trades(self):
        # Fill window with wins
        for _ in range(cfg.EM_WINDOW):
            self.mem.record_outcome("VolatilityExpansion", "XRPUSDT", "VOLATILITY_EXPANSION", won=True)
        # Overwrite with all losses
        for _ in range(cfg.EM_WINDOW):
            self.mem.record_outcome("VolatilityExpansion", "XRPUSDT", "VOLATILITY_EXPANSION", won=False)
        result = self.mem.query("VolatilityExpansion", "XRPUSDT", "VOLATILITY_EXPANSION")
        assert result.state == "PENALIZED"

    def test_score_bounded_01(self):
        for _ in range(cfg.EM_WINDOW):
            self.mem.record_outcome("TrendFollowing", "ADAUSDT", "TRENDING", won=True)
        result = self.mem.query("TrendFollowing", "ADAUSDT", "TRENDING")
        assert 0.0 <= result.history_score <= 1.0

    def test_summary_phase7(self):
        s = self.mem.summary()
        assert s["phase"] == 7
        assert s["module"] == "EDGE_MEMORY_ENGINE"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: Full Phase 7 Decision Chain
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhase7Integration:
    """
    Verifies the complete Phase 7 chain:
    EdgeMemory → TradeRanker → TradeCompetition → CapitalConcentrator → EdgeAmplifier
    """

    def test_elite_trade_gets_max_allocation_and_amplification(self):
        mem  = EdgeMemoryEngine()
        rank = TradeRanker()
        cc   = CapitalConcentrator()
        amp  = EdgeAmplifier()
        comp = TradeCompetitionEngine()

        # Build memory: proven winning combo
        for _ in range(cfg.EM_MIN_TRADES + 10):
            mem.record_outcome("TrendFollowing", "BTCUSDT", "TRENDING", won=True)
        hist = mem.query("TrendFollowing", "BTCUSDT", "TRENDING")

        # Use high EV (≥ ceiling) + high score to guarantee ELITE rank (≥ 0.90)
        # c_ev=1.0, c_score=0.90, c_regime=1.0, c_hist≈0.65 → rank ≈ 0.905
        ev_elite = cfg.EVC_HIGH_THRESHOLD * 3.0  # hits EV ceiling → c_ev = 1.0
        rank_result = rank.rank(
            ev=ev_elite, trade_score=0.90,
            regime="TRENDING", strategy="TrendFollowing",
            history_score=hist.history_score,
        )
        assert rank_result.ok is True
        assert rank_result.rank_score >= cfg.TR_MIN_RANK_SCORE

        # Competition: this trade vs a weaker one
        candidates = [
            TradeCandidate("strong", rank_result.rank_score, ev=ev_elite),
            TradeCandidate("weak",   0.62,                   ev=0.03),
        ]
        comp_result = comp.select(candidates)
        winner_ids = {w.signal_id for w in comp_result.winners}
        assert "strong" in winner_ids

        # Capital concentration — elite rank → ELITE or HIGH band (≥ 1.5×)
        cc_result = cc.concentrate(
            rank_score=rank_result.rank_score,
            equity=10_000, base_risk_usdt=100, upstream_mult=1.0,
        )
        assert cc_result.ok is True
        assert cc_result.size_multiplier >= cfg.CC_MULT_HIGH

        # Edge amplification — rank ≥ EA_RANK_THRESHOLD (0.80)
        amp_result = amp.evaluate(
            ev=ev_elite,
            rank_score=rank_result.rank_score,
            regime="TRENDING",
            volume_ratio=2.0,
        )
        assert amp_result.amplified is True
        assert amp_result.tp_multiplier > 1.0

    def test_weak_trade_rejected_at_ranker(self):
        rank = TradeRanker()
        result = rank.rank(
            ev=-0.02, trade_score=0.45,
            regime="UNKNOWN", strategy="MeanReversion",
            history_score=0.2,
        )
        assert result.ok is False

    def test_competition_rejects_overflow_trades(self):
        comp = TradeCompetitionEngine()
        candidates = [
            TradeCandidate(f"trade_{i}", rank_score=0.70 + i * 0.02, ev=0.10)
            for i in range(10)
        ]
        result = comp.select(candidates)
        assert len(result.winners) == cfg.TCE_MAX_CONCURRENT
        assert len(result.losers) == 10 - cfg.TCE_MAX_CONCURRENT

    def test_memory_boost_pushes_borderline_trade_over_threshold(self):
        mem  = EdgeMemoryEngine()
        rank = TradeRanker()

        # No memory: borderline trade
        r_no_mem = rank.rank(
            ev=0.08, trade_score=0.68, regime="TRENDING",
            strategy="TrendFollowing", history_score=0.5,
        )

        # Strong positive memory
        for _ in range(cfg.EM_MIN_TRADES + 10):
            mem.record_outcome("TrendFollowing", "BTCUSDT", "TRENDING", won=True)
        hist = mem.query("TrendFollowing", "BTCUSDT", "TRENDING")

        r_with_mem = rank.rank(
            ev=0.08, trade_score=0.68, regime="TRENDING",
            strategy="TrendFollowing", history_score=hist.history_score,
        )

        assert r_with_mem.rank_score >= r_no_mem.rank_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
