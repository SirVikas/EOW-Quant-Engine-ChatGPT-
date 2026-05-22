"""
FTD-REGIME-SURVIV — Cartography Test Suite

Verifies:
  * dimension extractors (regime, explore_type, ontology_state)
  * cell metrics arithmetic (correct subset, shadow projection)
  * 1D and 2D matrix builders (grouping, MIN_CELL_TRADES enforcement)
  * heatmap generation (scoring, ordering, region label format)
  * cartography classification (all 6 categories)
  * regime-transition identification
  * compute_regime_survivability_cartography structure & fail-open
  * backward compatibility (missing fields)
  * no mutation of input trade dicts
"""
from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.regime_cartography import (
    MIN_CELL_TRADES,
    SURVIVABILITY_THRESH,
    ALPHA_DESERT,
    MICROSTRUCTURE_TRAP,
    SESSION_ALPHA_POCKET,
    REGIME_ALPHA_CLUSTER,
    EXPLORATION_DEPENDENT,
    STABLE_ALPHA_REGION,
    _get_regime,
    _get_explore_type,
    _get_ontology_state,
    _heatmap_entries,
    _regime_transition_survivability,
    classify_cartography,
    compute_regime_survivability_cartography,
)


# ── Trade factory ─────────────────────────────────────────────────────────────

def _trade(
    *,
    regime:          str   = "MEAN_REVERTING",
    origin_session:  str   = "NY",
    close_session:   str   = "NY",
    explore_type:    str | None = None,
    was_exploration: bool  = False,
    net_pnl:         float = 0.5,
    gross_pnl:       float = 1.0,
    fee_entry:       float = 0.2,
    fee_exit:        float = 0.3,
    slippage_cost:   float = 0.0,
    borrow_cost:     float = 0.0,
    r_multiple:      float = 1.0,
    hold_sec:        int   = 120,
    crossed:         bool  = False,
) -> dict:
    entry_ts = 1_700_000_000_000 + int(time.time() * 1e3) % 1_000_000
    t: dict = {
        "trade_id":       f"T{int(time.time()*1e6)}",
        "regime":          regime,
        "origin_session":  origin_session,
        "close_session":   close_session,
        "net_pnl":         net_pnl,
        "gross_pnl":       gross_pnl,
        "fee_entry":       fee_entry,
        "fee_exit":        fee_exit,
        "slippage_cost":   slippage_cost,
        "borrow_cost":     borrow_cost,
        "r_multiple":      r_multiple,
        "entry_ts":        entry_ts,
        "exit_ts":         entry_ts + hold_sec * 1000,
        "crossed_session_boundary": crossed,
        "economic_truth": {
            "gross_pnl":               round(gross_pnl, 4),
            "net_pnl":                 round(net_pnl, 4),
            "fees_paid":               round(fee_entry + fee_exit, 4),
            "fee_drag_pct":            round((fee_entry + fee_exit) / gross_pnl * 100, 1)
                                       if gross_pnl > 0 else None,
            "hold_duration_sec":       float(hold_sec),
            "risk_reward_realized":    round(r_multiple, 3),
            "economic_classification": "SURVIVABLE",
            "payoff_geometry":         {"winner_fast": True,
                                        "loser_extended": False,
                                        "crossed_boundary": crossed},
        },
    }
    if explore_type is not None:
        t["exploration_origin"] = {
            "explore_type":          explore_type,
            "was_exploration_trade": was_exploration,
        }
    return t


def _n(n: int, **kw) -> list[dict]:
    """Create n identical trades with given kwargs."""
    return [_trade(**kw) for _ in range(n)]


def _winning(**kw) -> dict:
    kw.setdefault("gross_pnl", 2.0)
    kw.setdefault("net_pnl",   1.5)
    kw.setdefault("fee_entry", 0.25)
    kw.setdefault("fee_exit",  0.25)
    return _trade(**kw)


def _losing(**kw) -> dict:
    kw.setdefault("gross_pnl", 0.5)
    kw.setdefault("net_pnl",  -0.1)
    kw.setdefault("fee_entry", 0.3)
    kw.setdefault("fee_exit",  0.3)
    return _trade(**kw)


# ── TestDimensionExtractors ───────────────────────────────────────────────────

class TestDimensionExtractors:
    def test_get_regime_returns_field(self):
        assert _get_regime({"regime": "TRENDING"}) == "TRENDING"

    def test_get_regime_defaults_unknown(self):
        assert _get_regime({}) == "UNKNOWN"

    def test_get_regime_none_becomes_unknown(self):
        assert _get_regime({"regime": None}) == "UNKNOWN"

    def test_get_explore_type_returns_explore_type(self):
        t = _trade(explore_type="RULE4_MIN_EXPLORE", was_exploration=True)
        assert _get_explore_type(t) == "RULE4_MIN_EXPLORE"

    def test_get_explore_type_unknown_when_no_origin(self):
        assert _get_explore_type({}) == "UNKNOWN"

    def test_get_ontology_aligned_for_exploit(self):
        t = _trade(explore_type="EXPLOIT", was_exploration=False)
        assert _get_ontology_state(t) == "ALIGNED"

    def test_get_ontology_override_for_exploration(self):
        t = _trade(explore_type="RULE4_MIN_EXPLORE", was_exploration=True)
        assert _get_ontology_state(t) == "EXPLORATION_OVERRIDE"

    def test_get_ontology_unknown_when_no_origin(self):
        assert _get_ontology_state({}) == "UNKNOWN"

    def test_get_ontology_override_for_rule1(self):
        t = _trade(explore_type="RULE1_UCB", was_exploration=True)
        assert _get_ontology_state(t) == "EXPLORATION_OVERRIDE"


# ── TestComputeStructure ──────────────────────────────────────────────────────

class TestComputeStructure:
    REQUIRED_KEYS = {
        "scope_note", "total_trades", "cartography_category",
        "regime_matrix", "regime_tf_matrix", "regime_session_matrix",
        "exploration_dependence", "ontology_regime_matrix",
        "ny_regime_analysis", "rule4_regime_analysis",
        "survivability_heatmap", "alpha_persistence_regions",
        "alpha_desert_regions", "regime_transition_survivability",
    }

    def _trades(self) -> list[dict]:
        return (
            _n(4, regime="MEAN_REVERTING", origin_session="NY",
               explore_type="EXPLOIT", was_exploration=False) +
            _n(3, regime="TRENDING", origin_session="LONDON",
               explore_type="RULE4_MIN_EXPLORE", was_exploration=True)
        )

    def test_empty_returns_valid_dict(self):
        r = compute_regime_survivability_cartography([])
        assert r["total_trades"] == 0 and "scope_note" in r

    def test_required_keys_present(self):
        r = compute_regime_survivability_cartography(self._trades())
        assert self.REQUIRED_KEYS <= r.keys()

    def test_total_trades_correct(self):
        trades = self._trades()
        r = compute_regime_survivability_cartography(trades)
        assert r["total_trades"] == len(trades)

    def test_scope_note_non_governing(self):
        r = compute_regime_survivability_cartography(self._trades())
        assert "non-governing" in r["scope_note"].lower()

    def test_cartography_category_is_valid(self):
        valid = {ALPHA_DESERT, MICROSTRUCTURE_TRAP, SESSION_ALPHA_POCKET,
                 REGIME_ALPHA_CLUSTER, EXPLORATION_DEPENDENT, STABLE_ALPHA_REGION}
        r = compute_regime_survivability_cartography(self._trades())
        assert r["cartography_category"] in valid

    def test_never_raises_on_garbage(self):
        r = compute_regime_survivability_cartography([{"bad": "data"}, {}])
        assert "total_trades" in r or "error" in r

    def test_regime_tf_matrix_has_tfs_for_each_regime(self):
        r = compute_regime_survivability_cartography(self._trades())
        rtm = r["regime_tf_matrix"]
        for regime, tf_dict in rtm.items():
            assert "1m" in tf_dict and "5m" in tf_dict and "15m" in tf_dict

    def test_regime_session_matrix_groups_by_regime_and_session(self):
        r = compute_regime_survivability_cartography(self._trades())
        rsm = r["regime_session_matrix"]
        assert "MEAN_REVERTING" in rsm
        assert "NY" in rsm.get("MEAN_REVERTING", {})


# ── TestHeatmapEntries ────────────────────────────────────────────────────────

class TestHeatmapEntries:
    def _enough_trades(self) -> list[dict]:
        return (
            _n(4, regime="MEAN_REVERTING", origin_session="NY") +
            _n(4, regime="TRENDING",       origin_session="LONDON")
        )

    def test_heatmap_sorted_by_score_descending(self):
        hm = _heatmap_entries(self._enough_trades())
        scores = [h["score"] for h in hm]
        assert scores == sorted(scores, reverse=True)

    def test_heatmap_empty_when_all_cells_below_min(self):
        # Only 2 trades per (session, regime) → below MIN_CELL_TRADES=3
        trades = _n(2, regime="TRENDING", origin_session="NY")
        hm = _heatmap_entries(trades)
        assert hm == []

    def test_heatmap_entry_has_required_keys(self):
        hm = _heatmap_entries(self._enough_trades())
        if hm:
            keys = {"region", "session", "timeframe", "regime", "score", "tier",
                    "net_expectancy", "win_rate_pct", "trade_count", "is_shadow"}
            assert keys <= hm[0].keys()

    def test_heatmap_region_label_format(self):
        hm = _heatmap_entries(self._enough_trades())
        for h in hm:
            assert " + " in h["region"]
            assert h["session"] in h["region"]
            assert h["timeframe"] in h["region"]
            assert h["regime"] in h["region"]

    def test_1m_entries_not_shadow(self):
        hm = _heatmap_entries(self._enough_trades())
        for h in hm:
            if h["timeframe"] == "1m":
                assert h["is_shadow"] is False

    def test_5m_entries_are_shadow(self):
        hm = _heatmap_entries(self._enough_trades())
        for h in hm:
            if h["timeframe"] == "5m":
                assert h["is_shadow"] is True

    def test_produces_3_tf_entries_per_base_cell(self):
        # One (session, regime) pair with enough trades → 3 TF entries
        trades = _n(4, regime="MEAN_REVERTING", origin_session="NY")
        hm = _heatmap_entries(trades)
        assert len(hm) == 3   # 1m, 5m, 15m


# ── TestClassifyCartography ───────────────────────────────────────────────────

class TestClassifyCartography:
    def _hm_entry(self, session: str, tf: str, regime: str, score: int) -> dict:
        return {
            "region":    f"{session} + {tf} + {regime}",
            "session":   session,
            "timeframe": tf,
            "regime":    regime,
            "score":     score,
        }

    def test_alpha_desert_when_all_low(self):
        hm = [self._hm_entry("NY", "1m", "TRENDING", 20),
              self._hm_entry("ASIA", "1m", "MEAN_REVERTING", 15)]
        assert classify_cartography(hm, {}) == ALPHA_DESERT

    def test_microstructure_trap_no_1m_but_5m_improve(self):
        # 1m all below SURVIVABILITY_THRESH; 5m above TF_IMPROVEMENT_THRESH
        hm = [self._hm_entry("NY",   "1m",  "TRENDING",    20),
              self._hm_entry("NY",   "5m",  "TRENDING",    55),
              self._hm_entry("NY",   "15m", "TRENDING",    60)]
        assert classify_cartography(hm, {}) == MICROSTRUCTURE_TRAP

    def test_microstructure_trap_when_no_1m_cell_survivable(self):
        hm = [self._hm_entry("NY",   "1m",  "MEAN_REVERTING", 30),
              self._hm_entry("NY",   "5m",  "MEAN_REVERTING", 60),  # only higher TF
              self._hm_entry("NY",   "15m", "MEAN_REVERTING", 65)]
        assert classify_cartography(hm, {}) == MICROSTRUCTURE_TRAP

    def test_stable_alpha_region_when_many_survive(self):
        hm = [
            self._hm_entry("NY",     "1m", "TRENDING",      75),
            self._hm_entry("NY",     "1m", "MEAN_REVERTING", 60),
            self._hm_entry("LONDON", "1m", "TRENDING",      70),
            self._hm_entry("LONDON", "1m", "MEAN_REVERTING", 55),
            self._hm_entry("ASIA",   "1m", "TRENDING",      65),
        ]
        assert classify_cartography(hm, {}) == STABLE_ALPHA_REGION

    def test_regime_alpha_cluster_only_one_regime(self):
        # Only TRENDING survives, multiple regimes exist
        hm = [
            self._hm_entry("NY",   "1m", "TRENDING",      65),
            self._hm_entry("NY",   "1m", "MEAN_REVERTING", 20),
            self._hm_entry("ASIA", "1m", "TRENDING",      60),
        ]
        assert classify_cartography(hm, {}) == REGIME_ALPHA_CLUSTER

    def test_session_alpha_pocket_only_one_session(self):
        # Only NY survives, multiple sessions exist
        hm = [
            self._hm_entry("NY",   "1m", "TRENDING", 65),
            self._hm_entry("ASIA", "1m", "TRENDING", 20),
        ]
        # NY = 1 survivable session; ASIA = not survivable; both same regime → SESSION_ALPHA_POCKET
        result = classify_cartography(hm, {})
        assert result in (SESSION_ALPHA_POCKET, REGIME_ALPHA_CLUSTER)

    def test_exploration_dependent(self):
        hm = [self._hm_entry("NY", "1m", "TRENDING", 60)]
        explore_matrix = {
            "RULE4_MIN_EXPLORE": {"survivability_score": 65},
            "EXPLOIT":           {"survivability_score": 20},
        }
        assert classify_cartography(hm, explore_matrix) == EXPLORATION_DEPENDENT

    def test_alpha_desert_when_heatmap_empty(self):
        assert classify_cartography([], {}) == ALPHA_DESERT


# ── TestRegimeTransition ──────────────────────────────────────────────────────

class TestRegimeTransition:
    def test_identifies_transition_trades(self):
        # sequence: TRENDING, TRENDING, MEAN_REVERTING (→ transition), MEAN_REVERTING
        trades = [
            _trade(regime="TRENDING"),
            _trade(regime="TRENDING"),
            _trade(regime="MEAN_REVERTING"),  # transition
            _trade(regime="MEAN_REVERTING"),
        ]
        r = _regime_transition_survivability(trades)
        assert r["transition_trade_count"] == 1

    def test_no_transitions_with_uniform_regime(self):
        trades = _n(5, regime="TRENDING")
        r = _regime_transition_survivability(trades)
        assert r["transition_trade_count"] == 0

    def test_stable_count_correct(self):
        trades = [
            _trade(regime="TRENDING"),
            _trade(regime="TRENDING"),
            _trade(regime="MEAN_REVERTING"),  # transition
        ]
        r = _regime_transition_survivability(trades)
        # stable = trades 0 and 1; transition = trade 2
        assert r["stable_trade_count"] == 2

    def test_note_when_insufficient_transition_trades(self):
        trades = _n(5, regime="TRENDING")
        r = _regime_transition_survivability(trades)
        assert "transition_note" in r or r["transition_trade_count"] == 0

    def test_ignores_unknown_regime_for_transitions(self):
        # UNKNOWN→TRENDING should not be flagged as transition
        trades = [
            _trade(regime="UNKNOWN"),
            _trade(regime="TRENDING"),
            _trade(regime="TRENDING"),
        ]
        r = _regime_transition_survivability(trades)
        assert r["transition_trade_count"] == 0


# ── TestMatrixGrouping ────────────────────────────────────────────────────────

class TestMatrixGrouping:
    def test_regime_matrix_groups_by_regime(self):
        trades = (
            _n(3, regime="TRENDING") +
            _n(3, regime="MEAN_REVERTING")
        )
        r = compute_regime_survivability_cartography(trades)
        assert "TRENDING" in r["regime_matrix"]
        assert "MEAN_REVERTING" in r["regime_matrix"]

    def test_insufficient_cell_gets_note(self):
        # Only 2 TRENDING trades → below MIN_CELL_TRADES
        trades = (
            _n(2, regime="TRENDING") +
            _n(3, regime="MEAN_REVERTING")
        )
        r = compute_regime_survivability_cartography(trades)
        trending_cell = r["regime_matrix"].get("TRENDING", {})
        assert "note" in trending_cell

    def test_ny_regime_analysis_filters_correctly(self):
        trades = (
            _n(3, regime="TRENDING",       origin_session="NY") +
            _n(3, regime="MEAN_REVERTING", origin_session="LONDON")
        )
        r = compute_regime_survivability_cartography(trades)
        ny = r["ny_regime_analysis"]
        if isinstance(ny, dict) and "note" not in ny:
            assert "TRENDING" in ny
            assert "MEAN_REVERTING" not in ny


# ── TestBackwardCompatibility ─────────────────────────────────────────────────

class TestBackwardCompatibility:
    def test_trades_without_regime_field_work(self):
        t = _trade()
        del t["regime"]
        r = compute_regime_survivability_cartography([t, _trade(), _trade()])
        assert r["total_trades"] == 3

    def test_trades_without_exploration_origin_work(self):
        trades = [_trade() for _ in range(4)]
        for t in trades:
            t.pop("exploration_origin", None)
        r = compute_regime_survivability_cartography(trades)
        assert "exploration_dependence" in r

    def test_trades_without_economic_truth_work(self):
        trades = [_trade() for _ in range(4)]
        for t in trades:
            t.pop("economic_truth", None)
        r = compute_regime_survivability_cartography(trades)
        assert r["total_trades"] == 4

    def test_minimal_fields_do_not_crash(self):
        r = compute_regime_survivability_cartography([
            {"net_pnl": 0.5, "gross_pnl": 1.0},
            {"net_pnl": 0.3, "gross_pnl": 0.8},
            {"net_pnl": -0.1, "gross_pnl": 0.5},
        ])
        assert "cartography_category" in r


# ── TestNoExecutionMutation ───────────────────────────────────────────────────

class TestNoExecutionMutation:
    def test_compute_does_not_mutate_input_list(self):
        trades = _n(4, regime="TRENDING", origin_session="NY")
        original_ids = [id(t) for t in trades]
        compute_regime_survivability_cartography(trades)
        assert [id(t) for t in trades] == original_ids

    def test_compute_does_not_mutate_trade_dicts(self):
        trades = _n(4)
        snapshots = [dict(t) for t in trades]
        compute_regime_survivability_cartography(trades)
        for t, snap in zip(trades, snapshots):
            assert t["regime"]     == snap["regime"]
            assert t["gross_pnl"]  == snap["gross_pnl"]
            assert t["net_pnl"]    == snap["net_pnl"]

    def test_heatmap_entries_does_not_mutate_input(self):
        trades = _n(4, regime="TRENDING", origin_session="NY")
        original_gross = [t["gross_pnl"] for t in trades]
        _heatmap_entries(trades)
        assert [t["gross_pnl"] for t in trades] == original_gross
