"""
Tests for FTD-GRVL: Guarded Reality Verification Layer.

Covers:
  - Fill divergence metric
  - Slippage divergence metric
  - Latency divergence metric
  - Liquidity survivability metric
  - Spread fragility metric
  - Market impact sensitivity
  - Pilot survivability composite score
  - Simulation-reality confidence
  - Reality classification
  - Pilot state assessment
  - Recommendation generation (recommendation-only enforcement)
  - Audit entry immutability
  - Full compute_reality_verification structure
  - Production isolation (no live engine imports)
  - Edge cases and backward compatibility
"""
import sys
from typing import List

import pytest

from core.reality_verification import (
    # Pilot state constants
    PAPER_ONLY,
    SHADOW_MARKET,
    MICRO_PILOT,
    HUMAN_CONFIRM_REQUIRED,
    AUTO_DISABLED,
    CONSTITUTION_LOCKDOWN,
    # Classification constants
    REALITY_ALIGNED,
    FRICTION_EROSION,
    LIQUIDITY_FRAGILE,
    LATENCY_SENSITIVE,
    MICROSTRUCTURE_DEPENDENT,
    PILOT_NOT_RECOMMENDED,
    # Constitutional objects
    PILOT_HARD_PRINCIPLES,
    PILOT_STATE_DESCRIPTIONS,
    # Private helpers
    _fill_divergence_metric,
    _slippage_divergence_metric,
    _latency_divergence_metric,
    _liquidity_survivability_metric,
    _spread_fragility_metric,
    _market_impact_sensitivity,
    _pilot_survivability_score,
    _simulation_reality_confidence,
    _classify_reality,
    _assess_pilot_state,
    _generate_pilot_recommendations,
    _generate_pilot_audit_entry,
    compute_reality_verification,
)


# ── Trade factory ─────────────────────────────────────────────────────────────

def _t(
    net_pnl:       float = 0.10,
    gross_pnl:     float = 0.15,
    fee_entry:     float = 0.02,
    fee_exit:      float = 0.02,
    slippage_cost: float = 0.005,
    entry_ts:      int   = 1_700_000_000,
    exit_ts:       int   = 1_700_003_600,   # 1-hour hold
    regime:        str   = "TRENDING",
    session:       str   = "NY",
) -> dict:
    return {
        "trade_id":       f"T{id(object())}",
        "entry_ts":       entry_ts,
        "exit_ts":        exit_ts,
        "net_pnl":        net_pnl,
        "gross_pnl":      gross_pnl,
        "fee_entry":      fee_entry,
        "fee_exit":       fee_exit,
        "slippage_cost":  slippage_cost,
        "borrow_cost":    0.0,
        "regime":         regime,
        "origin_session": session,
    }


def _trades(n: int = 20, **kw) -> List[dict]:
    return [_t(**kw) for _ in range(n)]


def _mixed_trades(n: int = 30) -> List[dict]:
    result = []
    for i in range(n):
        pnl = 0.10 if i % 3 != 0 else -0.05
        result.append(_t(
            net_pnl=pnl, gross_pnl=abs(pnl) + 0.05,
            entry_ts=1_700_000_000 + i * 3600,
            exit_ts=1_700_000_000 + i * 3600 + (1800 + i * 600 % 7200),
        ))
    return result


# ── Divergence metric helpers ─────────────────────────────────────────────────

def _div_metrics(
    fill=0.0, slip=0.0, lat=0.0, liq=100.0, spread=0.0, impact=0.0
) -> dict:
    return {
        "fill_divergence":           {"score": fill,   "tier": "LOW"},
        "slippage_divergence":       {"score": slip,   "tier": "LOW"},
        "latency_divergence":        {"score": lat,    "tier": "LOW"},
        "liquidity_survivability":   {"score": liq,    "tier": "STRONG"},
        "spread_fragility":          {"score": spread, "tier": "LOW"},
        "market_impact_sensitivity": {"score": impact, "tier": "LOW"},
    }


# ══════════════════════════════════════════════════════════════════════════════
# TestFillDivergence
# ══════════════════════════════════════════════════════════════════════════════

class TestFillDivergence:

    def test_zero_slippage_gives_zero_score(self):
        trades = _trades(10, slippage_cost=0.0)
        r = _fill_divergence_metric(trades)
        assert r["score"] == 0.0

    def test_higher_slippage_gives_higher_score(self):
        low  = _fill_divergence_metric(_trades(10, slippage_cost=0.001, gross_pnl=0.10))
        high = _fill_divergence_metric(_trades(10, slippage_cost=0.05,  gross_pnl=0.10))
        assert high["score"] > low["score"]

    def test_score_in_range(self):
        r = _fill_divergence_metric(_trades(10, slippage_cost=0.20, gross_pnl=0.10))
        assert 0.0 <= r["score"] <= 100.0

    def test_ratio_pct_present(self):
        r = _fill_divergence_metric(_trades(10))
        assert "ratio_pct" in r

    def test_empty_trades_returns_zero(self):
        r = _fill_divergence_metric([])
        assert r["score"] == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# TestSlippageDivergence
# ══════════════════════════════════════════════════════════════════════════════

class TestSlippageDivergence:

    def test_no_slippage_gives_zero(self):
        trades = _trades(10, slippage_cost=0.0)
        r = _slippage_divergence_metric(trades)
        assert r["score"] == 0.0

    def test_high_slippage_gives_high_score(self):
        # slippage = gross → 100% ratio → score 100
        trades = _trades(10, slippage_cost=0.10, gross_pnl=0.10)
        r = _slippage_divergence_metric(trades)
        assert r["score"] >= 90.0

    def test_mean_ratio_pct_present(self):
        r = _slippage_divergence_metric(_trades(10))
        assert "mean_ratio_pct" in r

    def test_empty_trade_list_returns_zero(self):
        r = _slippage_divergence_metric([])
        assert r["score"] == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# TestLatencyDivergence
# ══════════════════════════════════════════════════════════════════════════════

class TestLatencyDivergence:

    def test_identical_hold_times_zero_cv(self):
        trades = [_t(entry_ts=1_700_000_000, exit_ts=1_700_003_600) for _ in range(10)]
        r = _latency_divergence_metric(trades)
        assert r["score"] == 0.0
        assert r["cv"] == 0.0

    def test_mixed_hold_times_gives_nonzero_cv(self):
        trades = [
            _t(entry_ts=1_700_000_000, exit_ts=1_700_000_000 + 60),    # 1 min
            _t(entry_ts=1_700_000_000, exit_ts=1_700_000_000 + 7200),  # 2 hrs
            _t(entry_ts=1_700_000_000, exit_ts=1_700_000_000 + 14400), # 4 hrs
        ] * 4
        r = _latency_divergence_metric(trades)
        assert r["score"] > 0.0

    def test_single_trade_returns_zero(self):
        r = _latency_divergence_metric([_t()])
        assert r["score"] == 0.0

    def test_mean_hold_min_present(self):
        r = _latency_divergence_metric(_trades(5))
        assert "mean_hold_min" in r

    def test_score_in_range(self):
        trades = [
            _t(entry_ts=1_700_000_000 + i * 1000, exit_ts=1_700_000_000 + i * 1000 + 60 * (i % 5 + 1))
            for i in range(20)
        ]
        r = _latency_divergence_metric(trades)
        assert 0.0 <= r["score"] <= 100.0


# ══════════════════════════════════════════════════════════════════════════════
# TestLiquiditySurvivability
# ══════════════════════════════════════════════════════════════════════════════

class TestLiquiditySurvivability:

    def test_empty_trades_returns_full_survival(self):
        r = _liquidity_survivability_metric([])
        assert r["score"] == 100.0

    def test_high_net_pnl_all_survive(self):
        # net_pnl=1.0, fee_entry=0.01 → adjusted_net=0.99 > 0 for all
        trades = _trades(10, net_pnl=1.0, fee_entry=0.01)
        r = _liquidity_survivability_metric(trades)
        assert r["score"] == 100.0

    def test_negative_net_pnl_none_survive(self):
        trades = _trades(10, net_pnl=-0.05)
        r = _liquidity_survivability_metric(trades)
        assert r["score"] == 0.0

    def test_half_survive_50_pct(self):
        trades = (
            _trades(10, net_pnl=0.10, fee_entry=0.01) +
            _trades(10, net_pnl=-0.10)
        )
        r = _liquidity_survivability_metric(trades)
        assert r["score"] == pytest.approx(50.0, abs=1.0)

    def test_tier_present(self):
        r = _liquidity_survivability_metric(_trades(10))
        assert "tier" in r


# ══════════════════════════════════════════════════════════════════════════════
# TestSpreadFragility
# ══════════════════════════════════════════════════════════════════════════════

class TestSpreadFragility:

    def test_empty_trades_zero_fragility(self):
        r = _spread_fragility_metric([])
        assert r["score"] == 0.0

    def test_large_edge_survives_all_stress(self):
        # net_pnl=1.0, fee_entry=0.001 → even 10x spread barely affects it
        trades = _trades(20, net_pnl=1.0, fee_entry=0.001)
        r = _spread_fragility_metric(trades)
        # survival_5x close to 100% → fragility score close to 0
        assert r["score"] < 20.0

    def test_fragile_edge_high_score(self):
        # net_pnl=0.03, fee_entry=0.02 → 5x spread kills most trades
        trades = _trades(20, net_pnl=0.03, fee_entry=0.02)
        r = _spread_fragility_metric(trades)
        assert r["score"] > 50.0

    def test_stress_scenarios_present(self):
        r = _spread_fragility_metric(_trades(10))
        assert "stress_scenarios" in r
        assert "2x_spread" in r["stress_scenarios"]
        assert "5x_spread" in r["stress_scenarios"]

    def test_score_in_range(self):
        r = _spread_fragility_metric(_trades(20))
        assert 0.0 <= r["score"] <= 100.0


# ══════════════════════════════════════════════════════════════════════════════
# TestMarketImpactSensitivity
# ══════════════════════════════════════════════════════════════════════════════

class TestMarketImpactSensitivity:

    def test_insufficient_trades_returns_minimal(self):
        r = _market_impact_sensitivity(_trades(2), 0.01)
        assert r["score"] == 0.0

    def test_score_in_range(self):
        r = _market_impact_sensitivity(_mixed_trades(20), 0.05)
        assert 0.0 <= r["score"] <= 100.0

    def test_zero_base_ne_gives_50(self):
        r = _market_impact_sensitivity(_trades(10), 0.0)
        assert r["score"] == 50.0

    def test_larger_fees_give_higher_sensitivity(self):
        # large fees → big NE drop under 2x stress → high sensitivity
        r_small = _market_impact_sensitivity(_trades(10, fee_entry=0.001, fee_exit=0.001), 0.10)
        r_large = _market_impact_sensitivity(_trades(10, fee_entry=0.10,  fee_exit=0.10),  0.10)
        assert r_large["score"] > r_small["score"]


# ══════════════════════════════════════════════════════════════════════════════
# TestPilotSurvivabilityScore
# ══════════════════════════════════════════════════════════════════════════════

class TestPilotSurvivabilityScore:

    def test_all_zero_divergence_good_liquidity_high_score(self):
        dm = _div_metrics(fill=0, slip=0, lat=0, liq=100, spread=0, impact=0)
        r  = _pilot_survivability_score(dm)
        assert r["score"] >= 80.0

    def test_high_divergence_low_score(self):
        dm = _div_metrics(fill=80, slip=80, lat=80, liq=20, spread=80, impact=80)
        r  = _pilot_survivability_score(dm)
        assert r["score"] < 40.0

    def test_score_in_range(self):
        dm = _div_metrics(fill=30, slip=20, lat=15, liq=70, spread=25, impact=30)
        r  = _pilot_survivability_score(dm)
        assert 0.0 <= r["score"] <= 100.0

    def test_tier_is_valid(self):
        dm = _div_metrics()
        r  = _pilot_survivability_score(dm)
        assert r["tier"] in ("PILOT_READY", "CONDITIONAL", "HIGH_RISK", "NOT_RECOMMENDED")

    def test_better_liquidity_improves_score(self):
        low_liq  = _pilot_survivability_score(_div_metrics(liq=10))
        high_liq = _pilot_survivability_score(_div_metrics(liq=100))
        assert high_liq["score"] > low_liq["score"]


# ══════════════════════════════════════════════════════════════════════════════
# TestSimulationRealityConfidence
# ══════════════════════════════════════════════════════════════════════════════

class TestSimulationRealityConfidence:

    def test_empty_trades_zero_confidence(self):
        r = _simulation_reality_confidence([])
        assert r["score"] == 0.0
        assert r["tier"] == "INSUFFICIENT"

    def test_large_corpus_with_fees_gives_high_confidence(self):
        trades = _trades(600)
        r = _simulation_reality_confidence(trades)
        assert r["score"] >= 60.0

    def test_no_fee_data_lowers_confidence(self):
        trades = _trades(200, fee_entry=0.0, fee_exit=0.0)
        r = _simulation_reality_confidence(trades)
        r_with_fees = _simulation_reality_confidence(_trades(200))
        assert r["score"] < r_with_fees["score"]

    def test_fee_coverage_pct_in_output(self):
        trades = _trades(10)
        r = _simulation_reality_confidence(trades)
        assert "fee_coverage_pct" in r
        assert 0.0 <= r["fee_coverage_pct"] <= 100.0

    def test_trade_corpus_size_in_output(self):
        trades = _trades(42)
        r = _simulation_reality_confidence(trades)
        assert r["trade_corpus_size"] == 42


# ══════════════════════════════════════════════════════════════════════════════
# TestRealityClassification
# ══════════════════════════════════════════════════════════════════════════════

class TestRealityClassification:

    def test_pilot_not_recommended_low_score(self):
        cls = _classify_reality(20.0, _div_metrics())
        assert cls == PILOT_NOT_RECOMMENDED

    def test_pilot_not_recommended_high_fill_div(self):
        cls = _classify_reality(50.0, _div_metrics(fill=75.0))
        assert cls == PILOT_NOT_RECOMMENDED

    def test_microstructure_dependent_high_fill(self):
        cls = _classify_reality(50.0, _div_metrics(fill=55.0))
        assert cls == MICROSTRUCTURE_DEPENDENT

    def test_liquidity_fragile_low_liq(self):
        cls = _classify_reality(50.0, _div_metrics(liq=40.0))
        assert cls == LIQUIDITY_FRAGILE

    def test_latency_sensitive_high_lat(self):
        cls = _classify_reality(50.0, _div_metrics(lat=65.0))
        assert cls == LATENCY_SENSITIVE

    def test_friction_erosion_high_slippage(self):
        cls = _classify_reality(50.0, _div_metrics(slip=55.0))
        assert cls == FRICTION_EROSION

    def test_friction_erosion_high_spread_fragility(self):
        cls = _classify_reality(50.0, _div_metrics(spread=65.0))
        assert cls == FRICTION_EROSION

    def test_reality_aligned_clean_metrics(self):
        cls = _classify_reality(80.0, _div_metrics(fill=5, slip=5, lat=5, liq=90, spread=5, impact=5))
        assert cls == REALITY_ALIGNED


# ══════════════════════════════════════════════════════════════════════════════
# TestPilotStateAssessment
# ══════════════════════════════════════════════════════════════════════════════

class TestPilotStateAssessment:

    def _conf(self, score: float = 60.0) -> dict:
        return {"score": score, "tier": "MODERATE"}

    def test_very_low_score_high_confidence_is_auto_disabled(self):
        state = _assess_pilot_state(15.0, LATENCY_SENSITIVE, self._conf(70))
        assert state == AUTO_DISABLED

    def test_pilot_not_recommended_high_conf_is_lockdown(self):
        state = _assess_pilot_state(25.0, PILOT_NOT_RECOMMENDED, self._conf(70))
        assert state == CONSTITUTION_LOCKDOWN

    def test_friction_erosion_is_human_confirm_required(self):
        state = _assess_pilot_state(45.0, FRICTION_EROSION, self._conf(60))
        assert state == HUMAN_CONFIRM_REQUIRED

    def test_liquidity_fragile_is_human_confirm_required(self):
        state = _assess_pilot_state(45.0, LIQUIDITY_FRAGILE, self._conf(60))
        assert state == HUMAN_CONFIRM_REQUIRED

    def test_reality_aligned_high_score_is_micro_pilot(self):
        state = _assess_pilot_state(70.0, REALITY_ALIGNED, self._conf(70))
        assert state == MICRO_PILOT

    def test_moderate_score_is_shadow_market(self):
        state = _assess_pilot_state(45.0, LATENCY_SENSITIVE, self._conf(70))
        assert state == SHADOW_MARKET

    def test_low_score_low_confidence_is_paper_only(self):
        state = _assess_pilot_state(25.0, LATENCY_SENSITIVE, self._conf(20))
        assert state == PAPER_ONLY


# ══════════════════════════════════════════════════════════════════════════════
# TestRecommendationGeneration
# ══════════════════════════════════════════════════════════════════════════════

class TestRecommendationGeneration:

    def _recs(self, cls, pilot_score=50.0, conf_score=60.0, **dm_kw) -> list:
        dm   = _div_metrics(**dm_kw)
        conf = {"score": conf_score, "tier": "MODERATE"}
        return _generate_pilot_recommendations(cls, PAPER_ONLY, dm, conf, pilot_score)

    def test_pilot_not_recommended_generates_warning(self):
        recs = self._recs(PILOT_NOT_RECOMMENDED, pilot_score=20.0)
        types = [r["type"] for r in recs]
        assert "PILOT_NOT_RECOMMENDED_WARNING" in types

    def test_liquidity_fragile_generates_warning(self):
        recs = self._recs(LIQUIDITY_FRAGILE, liq=30.0)
        types = [r["type"] for r in recs]
        assert "LIQUIDITY_FRAGILITY_WARNING" in types

    def test_reality_aligned_high_score_generates_eligible(self):
        recs = self._recs(REALITY_ALIGNED, pilot_score=70.0)
        types = [r["type"] for r in recs]
        assert "MICRO_PILOT_ELIGIBLE" in types

    def test_low_confidence_generates_confidence_warning(self):
        recs = self._recs(REALITY_ALIGNED, pilot_score=65.0, conf_score=20.0)
        types = [r["type"] for r in recs]
        assert "LOW_CONFIDENCE_WARNING" in types

    def test_all_recs_have_auto_authorized_false(self):
        for cls in (PILOT_NOT_RECOMMENDED, FRICTION_EROSION, LIQUIDITY_FRAGILE,
                    LATENCY_SENSITIVE, MICROSTRUCTURE_DEPENDENT, REALITY_ALIGNED):
            recs = self._recs(cls, pilot_score=50.0)
            for rec in recs:
                assert rec["auto_authorized"] is False, (
                    f"{cls} rec {rec['type']} has auto_authorized=True"
                )

    def test_clean_state_generates_affirmation(self):
        recs = _generate_pilot_recommendations(
            REALITY_ALIGNED, PAPER_ONLY,
            _div_metrics(),
            {"score": 60.0, "tier": "MODERATE"},
            50.0,   # below MICRO_PILOT threshold → no eligible rec
        )
        types = [r["type"] for r in recs]
        assert "REALITY_ALIGNMENT_AFFIRMATION" in types


# ══════════════════════════════════════════════════════════════════════════════
# TestAuditEntry
# ══════════════════════════════════════════════════════════════════════════════

class TestAuditEntry:

    def _entry(self, pilot_state: str = PAPER_ONLY) -> dict:
        conf = {"score": 60.0, "tier": "MODERATE"}
        recs = _generate_pilot_recommendations(REALITY_ALIGNED, pilot_state, _div_metrics(), conf, 55.0)
        return _generate_pilot_audit_entry(pilot_state, REALITY_ALIGNED, 55.0, conf, recs)

    def test_required_keys_present(self):
        entry = self._entry()
        for k in (
            "entry_id", "timestamp_ms", "pilot_state", "reality_classification",
            "pilot_survivability_score", "recommendations_generated",
            "human_approval_required", "auto_authorized", "immutable",
        ):
            assert k in entry, f"Missing key: {k}"

    def test_auto_authorized_always_false(self):
        for state in (PAPER_ONLY, HUMAN_CONFIRM_REQUIRED, AUTO_DISABLED, CONSTITUTION_LOCKDOWN):
            entry = self._entry(state)
            assert entry["auto_authorized"] is False

    def test_immutable_always_true(self):
        assert self._entry()["immutable"] is True

    def test_entry_id_starts_with_grvl(self):
        assert self._entry()["entry_id"].startswith("GRVL-")

    def test_paper_only_no_approval_required(self):
        assert self._entry(PAPER_ONLY)["human_approval_required"] is False

    def test_non_paper_only_requires_approval(self):
        for state in (SHADOW_MARKET, MICRO_PILOT, HUMAN_CONFIRM_REQUIRED, AUTO_DISABLED, CONSTITUTION_LOCKDOWN):
            assert self._entry(state)["human_approval_required"] is True


# ══════════════════════════════════════════════════════════════════════════════
# TestComputeStructure
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeStructure:

    def _result(self, n: int = 30) -> dict:
        return compute_reality_verification(_mixed_trades(n))

    def test_all_top_level_keys_present(self):
        r = self._result()
        for k in (
            "scope_note", "total_trades", "pilot_state", "pilot_state_description",
            "reality_classification", "pilot_survivability",
            "simulation_reality_confidence", "divergence_metrics",
            "baseline_economics", "recommendations", "pilot_hard_principles",
            "audit_entry",
        ):
            assert k in r, f"Missing key: {k}"

    def test_scope_note_mentions_grvl(self):
        assert "FTD-GRVL" in self._result()["scope_note"]

    def test_pilot_state_is_valid(self):
        valid = {PAPER_ONLY, SHADOW_MARKET, MICRO_PILOT,
                 HUMAN_CONFIRM_REQUIRED, AUTO_DISABLED, CONSTITUTION_LOCKDOWN}
        assert self._result()["pilot_state"] in valid

    def test_reality_classification_is_valid(self):
        valid = {REALITY_ALIGNED, FRICTION_EROSION, LIQUIDITY_FRAGILE,
                 LATENCY_SENSITIVE, MICROSTRUCTURE_DEPENDENT, PILOT_NOT_RECOMMENDED}
        assert self._result()["reality_classification"] in valid

    def test_pilot_survivability_has_score_and_tier(self):
        ps = self._result()["pilot_survivability"]
        assert "score" in ps and "tier" in ps
        assert 0.0 <= ps["score"] <= 100.0

    def test_divergence_metrics_has_six_keys(self):
        dm = self._result()["divergence_metrics"]
        assert len(dm) == 6

    def test_recommendations_is_list(self):
        assert isinstance(self._result()["recommendations"], list)

    def test_audit_entry_has_grvl_prefix(self):
        ae = self._result()["audit_entry"]
        assert ae["entry_id"].startswith("GRVL-")

    def test_no_error_key_on_valid_input(self):
        assert "error" not in self._result()

    def test_total_trades_matches(self):
        trades = _mixed_trades(30)
        r = compute_reality_verification(trades)
        assert r["total_trades"] == 30


# ══════════════════════════════════════════════════════════════════════════════
# TestProductionIsolation
# ══════════════════════════════════════════════════════════════════════════════

class TestProductionIsolation:

    def test_no_main_import(self):
        import core.reality_verification as rv
        src = __import__("inspect").getsource(rv)
        assert "import main" not in src
        assert "from main" not in src

    def test_no_pnl_calc_reference(self):
        import core.reality_verification as rv
        src = __import__("inspect").getsource(rv)
        assert "pnl_calc" not in src

    def test_no_rl_engine_reference(self):
        import core.reality_verification as rv
        src = __import__("inspect").getsource(rv)
        assert "rl_engine" not in src

    def test_never_raises(self):
        compute_reality_verification(None)
        compute_reality_verification([])
        compute_reality_verification([{"bad": "data"}] * 10)
        compute_reality_verification(_trades(20))

    def test_input_not_mutated(self):
        trades = _trades(20)
        original = [dict(t) for t in trades]
        compute_reality_verification(trades)
        for orig, after in zip(original, trades):
            assert orig == after


# ══════════════════════════════════════════════════════════════════════════════
# TestEdgeCases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_none_input_returns_note(self):
        r = compute_reality_verification(None)
        assert "note" in r or "error" in r

    def test_empty_list_returns_note(self):
        r = compute_reality_verification([])
        assert "note" in r

    def test_below_min_trades_returns_note(self):
        r = compute_reality_verification(_trades(3))
        assert "note" in r

    def test_all_losing_trades_handled(self):
        trades = _trades(20, net_pnl=-0.10, gross_pnl=-0.05)
        r = compute_reality_verification(trades)
        assert isinstance(r, dict)
        assert "error" not in r

    def test_all_zero_pnl_handled(self):
        trades = _trades(10, net_pnl=0.0, gross_pnl=0.0, slippage_cost=0.0)
        r = compute_reality_verification(trades)
        assert isinstance(r, dict)


# ══════════════════════════════════════════════════════════════════════════════
# TestBackwardCompatibility
# ══════════════════════════════════════════════════════════════════════════════

class TestBackwardCompatibility:

    def test_missing_fee_fields_handled(self):
        trades = [{"net_pnl": 0.10, "gross_pnl": 0.15, "entry_ts": 1_700_000_000,
                   "exit_ts": 1_700_003_600} for _ in range(20)]
        r = compute_reality_verification(trades)
        assert isinstance(r, dict)
        assert "error" not in r

    def test_missing_slippage_field_handled(self):
        def _no_slip():
            t = _t()
            del t["slippage_cost"]
            return t
        r = compute_reality_verification([_no_slip() for _ in range(20)])
        assert isinstance(r, dict)

    def test_none_fee_fields_handled(self):
        def _null_fees():
            t = _t()
            t["fee_entry"]    = None
            t["fee_exit"]     = None
            t["slippage_cost"] = None
            return t
        r = compute_reality_verification([_null_fees() for _ in range(20)])
        assert isinstance(r, dict)
        assert "error" not in r

    def test_extra_unknown_fields_ignored(self):
        trades = [dict(_t(), unknown_field=42) for _ in range(20)]
        r = compute_reality_verification(trades)
        assert "error" not in r


# ══════════════════════════════════════════════════════════════════════════════
# TestConstitutionalPrinciples
# ══════════════════════════════════════════════════════════════════════════════

class TestConstitutionalPrinciples:

    def test_autonomous_trading_impossible(self):
        assert PILOT_HARD_PRINCIPLES["autonomous_live_trading"] is False

    def test_self_granted_authority_impossible(self):
        assert PILOT_HARD_PRINCIPLES["self_granted_economic_authority"] is False

    def test_capital_scaling_not_automatic(self):
        assert PILOT_HARD_PRINCIPLES["capital_scaling_automatic"] is False

    def test_human_supremacy_required(self):
        assert PILOT_HARD_PRINCIPLES["human_supremacy"] is True

    def test_output_has_pilot_hard_principles(self):
        r = compute_reality_verification(_mixed_trades(30))
        hp = r.get("pilot_hard_principles", {})
        assert hp.get("autonomous_live_trading") is False
        assert hp.get("human_supremacy") is True

    def test_all_audit_entries_non_autonomous(self):
        r = compute_reality_verification(_mixed_trades(30))
        ae = r.get("audit_entry", {})
        assert ae.get("auto_authorized") is False

    def test_all_six_states_have_descriptions(self):
        for state in (PAPER_ONLY, SHADOW_MARKET, MICRO_PILOT,
                      HUMAN_CONFIRM_REQUIRED, AUTO_DISABLED, CONSTITUTION_LOCKDOWN):
            assert state in PILOT_STATE_DESCRIPTIONS
            assert len(PILOT_STATE_DESCRIPTIONS[state]) > 0
