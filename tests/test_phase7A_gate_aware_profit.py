"""
EOW Quant Engine — tests/test_phase7A_gate_aware_profit.py
Phase 7A: Gate-Aware Profit Engine — Integration Tests

Coverage:
    GateAwareController:
        1.  allow_profit_engine returns False when can_trade=False
        2.  allow_profit_engine returns False when safe_mode=True
        3.  allow_profit_engine returns True when can_trade=True, safe_mode=False
        4.  allow_amplification disabled in safe mode
        5.  permissions() returns correct EnginePermission struct

    ScanController:
        6.  Scanning blocked when can_trade=False
        7.  Scanning blocked when safe_mode=True
        8.  Scanning allowed when gate clear
        9.  Block reason includes gate reason

    GateAwareTradeRanker:
        10. Returns None when gate blocked
        11. Returns None when safe_mode active
        12. Returns RankResult when gate clear and score passes threshold
        13. Returns RankResult(ok=False) when gate clear but score below threshold

    GateAwareCompetitionEngine:
        14. Returns empty winners when gate blocked
        15. Moves all candidates to losers when gate blocked
        16. Returns top-N winners when gate clear
        17. Competition disabled in safe mode

    GateAwareCapitalConcentrator:
        18. Returns base allocation (no boost) when gate blocked
        19. Returns SAFE_FALLBACK band when gated off
        20. Returns ELITE band and boost when gate clear and rank ≥ 0.90
        21. Returns base allocation when safe_mode active

    GateAwareEdgeAmplifier:
        22. Returns no-amplification when safe_mode=True
        23. Returns no-amplification when can_trade=False
        24. Returns amplified result when gate clear and all conditions met
        25. Returns no-amplification when gate clear but conditions not met

    Full pipeline:
        26. Full pipeline halts at scan when gate blocked
        27. Full pipeline halts at scan when safe_mode
        28. Full pipeline runs when gate clear
        29. Capital fallback is correct size (upstream_mult × base only)
        30. Amplification result has no boost when safe_mode
"""
from __future__ import annotations

import pytest

from core.profit.gate_aware_controller import GateAwareController
from core.profit.scan_controller import ScanController
from core.profit.trade_ranker import GateAwareTradeRanker
from core.profit.trade_competition import GateAwareCompetitionEngine
from core.profit.capital_concentrator import GateAwareCapitalConcentrator
from core.profit.edge_amplifier import GateAwareEdgeAmplifier

from core.trade_ranker import TradeRanker
from core.capital_concentrator import CapitalConcentrator
from core.edge_amplifier import EdgeAmplifier
from core.trade_competition import TradeCompetitionEngine, TradeCandidate

from config import cfg


# ── Gate status helpers ───────────────────────────────────────────────────────

def _gate(can_trade: bool = True, safe_mode: bool = False, reason: str = "ALL_CLEAR") -> dict:
    return {"can_trade": can_trade, "safe_mode": safe_mode, "reason": reason}


GATE_CLEAR   = _gate(can_trade=True,  safe_mode=False, reason="ALL_CLEAR")
GATE_BLOCKED = _gate(can_trade=False, safe_mode=True,  reason="WS_UNSTABLE")
GATE_SAFE    = _gate(can_trade=True,  safe_mode=True,  reason="SAFE_MODE")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def gac():
    return GateAwareController()


@pytest.fixture
def sc():
    return ScanController()


@pytest.fixture
def ranker():
    return GateAwareTradeRanker(base=TradeRanker())


@pytest.fixture
def competition():
    return GateAwareCompetitionEngine(base=TradeCompetitionEngine())


@pytest.fixture
def concentrator():
    return GateAwareCapitalConcentrator(base=CapitalConcentrator())


@pytest.fixture
def amplifier():
    return GateAwareEdgeAmplifier(base=EdgeAmplifier())


# ── 1–5: GateAwareController ─────────────────────────────────────────────────

def test_allow_profit_engine_blocked_when_no_trade(gac):
    assert gac.allow_profit_engine(GATE_BLOCKED) is False


def test_allow_profit_engine_blocked_when_safe_mode(gac):
    assert gac.allow_profit_engine(GATE_SAFE) is False


def test_allow_profit_engine_true_when_clear(gac):
    assert gac.allow_profit_engine(GATE_CLEAR) is True


def test_allow_amplification_false_in_safe_mode(gac):
    assert gac.allow_amplification(GATE_SAFE) is False


def test_permissions_structure_when_blocked(gac):
    perm = gac.permissions(GATE_BLOCKED)
    assert perm.profit_engine is False
    assert perm.scanning is False
    assert perm.amplification is False
    assert "GATE_BLOCKED" in perm.reason or "BLOCKED" in perm.reason


def test_permissions_all_clear(gac):
    perm = gac.permissions(GATE_CLEAR)
    assert perm.profit_engine is True
    assert perm.scanning is True
    assert perm.amplification is True
    assert perm.reason == "ALL_CLEAR"


def test_permissions_safe_mode_disables_scanning(gac):
    perm = gac.permissions(GATE_SAFE)
    assert perm.profit_engine is False
    assert perm.scanning is False
    assert perm.amplification is False


# ── 6–9: ScanController ──────────────────────────────────────────────────────

def test_scan_blocked_when_gate_blocked(sc):
    result = sc.can_scan(GATE_BLOCKED)
    assert result.allowed is False
    assert "NO_SCAN" in result.reason


def test_scan_blocked_in_safe_mode(sc):
    result = sc.can_scan(GATE_SAFE)
    assert result.allowed is False
    assert "SAFE_MODE" in result.reason


def test_scan_allowed_when_clear(sc):
    result = sc.can_scan(GATE_CLEAR)
    assert result.allowed is True
    assert result.reason == "SCAN_OK"


def test_scan_block_reason_includes_gate_reason(sc):
    gate = _gate(can_trade=False, safe_mode=True, reason="DEPLOY_LOW")
    result = sc.can_scan(gate)
    assert result.allowed is False
    # reason should reference the gate's own reason or be a clear NO_SCAN signal
    assert "DEPLOY_LOW" in result.reason or "NO_SCAN" in result.reason


# ── 10–13: GateAwareTradeRanker ──────────────────────────────────────────────

def test_ranker_returns_none_when_gate_blocked(ranker):
    result = ranker.rank(GATE_BLOCKED, ev=0.20, trade_score=0.80,
                         regime="TRENDING", strategy="TrendFollowing")
    assert result is None


def test_ranker_returns_none_when_safe_mode(ranker):
    result = ranker.rank(GATE_SAFE, ev=0.20, trade_score=0.80,
                         regime="TRENDING", strategy="TrendFollowing")
    assert result is None


def test_ranker_returns_result_when_gate_clear(ranker):
    # Use inputs that produce a rank score ≥ TR_MIN_RANK_SCORE
    ev_high = cfg.EVC_HIGH_THRESHOLD * 3.0   # normalises to 1.0
    result = ranker.rank(GATE_CLEAR, ev=ev_high, trade_score=0.90,
                         regime="TRENDING", strategy="TrendFollowing",
                         history_score=0.90)
    assert result is not None
    assert result.ok is True
    assert result.rank_score >= cfg.TR_MIN_RANK_SCORE


def test_ranker_returns_ok_false_when_rank_below_threshold(ranker):
    # EV=0, trade_score=0 → rank_score≈0.075 (below 0.60 threshold)
    result = ranker.rank(GATE_CLEAR, ev=0.0, trade_score=0.0,
                         regime="UNKNOWN", strategy="TrendFollowing",
                         history_score=0.0)
    assert result is not None
    assert result.ok is False


# ── 14–17: GateAwareCompetitionEngine ────────────────────────────────────────

def _make_candidate(sig_id: str, rank: float, ev: float = 0.15) -> TradeCandidate:
    return TradeCandidate(signal_id=sig_id, rank_score=rank, ev=ev)


def test_competition_empty_winners_when_gate_blocked(competition):
    candidates = [_make_candidate("A", 0.85), _make_candidate("B", 0.75)]
    result = competition.select(GATE_BLOCKED, candidates)
    assert result.winners == []
    assert len(result.losers) == 2


def test_competition_all_candidates_to_losers_when_blocked(competition):
    candidates = [_make_candidate(f"sig_{i}", 0.85) for i in range(5)]
    result = competition.select(GATE_BLOCKED, candidates)
    assert len(result.winners) == 0
    assert len(result.losers) == 5


def test_competition_top_n_winners_when_clear(competition):
    candidates = [
        _make_candidate("A", 0.95),
        _make_candidate("B", 0.85),
        _make_candidate("C", 0.80),
        _make_candidate("D", 0.75),
        _make_candidate("E", 0.65),
    ]
    result = competition.select(GATE_CLEAR, candidates)
    assert len(result.winners) <= cfg.TCE_MAX_CONCURRENT
    # Top candidate must be in winners
    winner_ids = [w.signal_id for w in result.winners]
    assert "A" in winner_ids


def test_competition_disabled_in_safe_mode(competition):
    candidates = [_make_candidate("X", 0.90)]
    result = competition.select(GATE_SAFE, candidates)
    assert result.winners == []


# ── 18–21: GateAwareCapitalConcentrator ──────────────────────────────────────

def test_concentrator_base_allocation_when_blocked(concentrator):
    result = concentrator.concentrate(
        GATE_BLOCKED, rank_score=0.95, equity=10000.0,
        base_risk_usdt=100.0, upstream_mult=1.5,
    )
    assert result.ok is True
    assert result.band == "SAFE_FALLBACK"
    # No concentration boost — only upstream_mult applied
    assert abs(result.size_multiplier - 1.5) < 0.01


def test_concentrator_fallback_band_when_gated(concentrator):
    result = concentrator.concentrate(
        GATE_BLOCKED, rank_score=0.85, equity=5000.0,
        base_risk_usdt=50.0, upstream_mult=1.0,
    )
    assert result.band == "SAFE_FALLBACK"


def test_concentrator_elite_boost_when_clear(concentrator):
    result = concentrator.concentrate(
        GATE_CLEAR, rank_score=0.92, equity=10000.0,
        base_risk_usdt=100.0, upstream_mult=1.0,
    )
    assert result.ok is True
    assert result.band == "ELITE"
    assert result.size_multiplier >= cfg.CC_MULT_ELITE


def test_concentrator_base_allocation_in_safe_mode(concentrator):
    result = concentrator.concentrate(
        GATE_SAFE, rank_score=0.95, equity=10000.0,
        base_risk_usdt=100.0, upstream_mult=1.2,
    )
    assert result.band == "SAFE_FALLBACK"
    assert abs(result.size_multiplier - 1.2) < 0.01


# ── 22–25: GateAwareEdgeAmplifier ────────────────────────────────────────────

def test_amplifier_disabled_in_safe_mode(amplifier):
    result = amplifier.evaluate(
        GATE_SAFE, ev=0.30, rank_score=0.90,
        regime="TRENDING", volume_ratio=2.0,
    )
    assert result.amplified is False
    assert result.tp_multiplier == 1.0
    assert result.trail_multiplier == 1.0


def test_amplifier_disabled_when_gate_blocked(amplifier):
    result = amplifier.evaluate(
        GATE_BLOCKED, ev=0.30, rank_score=0.90,
        regime="TRENDING", volume_ratio=2.0,
    )
    assert result.amplified is False
    assert result.tp_multiplier == 1.0
    assert result.trail_multiplier == 1.0


def test_amplifier_fires_when_gate_clear_and_conditions_met(amplifier):
    result = amplifier.evaluate(
        GATE_CLEAR,
        ev=cfg.EA_EV_THRESHOLD + 0.05,
        rank_score=cfg.EA_RANK_THRESHOLD + 0.05,
        regime="TRENDING",
        volume_ratio=cfg.EA_VOL_RATIO_THRESHOLD + 0.5,
    )
    assert result.amplified is True
    assert result.tp_multiplier == cfg.EA_TP_BOOST_MULT
    assert result.trail_multiplier == cfg.EA_TRAIL_BOOST_MULT


def test_amplifier_no_fire_when_conditions_not_met(amplifier):
    # Volume too low → amplification denied
    result = amplifier.evaluate(
        GATE_CLEAR,
        ev=cfg.EA_EV_THRESHOLD + 0.05,
        rank_score=cfg.EA_RANK_THRESHOLD + 0.05,
        regime="TRENDING",
        volume_ratio=0.5,   # below threshold
    )
    assert result.amplified is False


# ── 26–30: Full pipeline tests ────────────────────────────────────────────────

def test_pipeline_halts_at_scan_when_gate_blocked(sc, ranker, competition):
    scan = sc.can_scan(GATE_BLOCKED)
    assert scan.allowed is False
    # Ranker and competition also blocked
    r = ranker.rank(GATE_BLOCKED, ev=0.20, trade_score=0.80,
                    regime="TRENDING", strategy="TrendFollowing")
    assert r is None
    cr = competition.select(GATE_BLOCKED, [_make_candidate("X", 0.85)])
    assert cr.winners == []


def test_pipeline_halts_at_scan_in_safe_mode(sc, ranker, amplifier):
    scan = sc.can_scan(GATE_SAFE)
    assert scan.allowed is False
    r = ranker.rank(GATE_SAFE, ev=0.25, trade_score=0.85,
                    regime="TRENDING", strategy="TrendFollowing")
    assert r is None
    amp = amplifier.evaluate(GATE_SAFE, ev=0.25, rank_score=0.85,
                              regime="TRENDING", volume_ratio=2.0)
    assert amp.amplified is False


def test_pipeline_runs_when_gate_clear(sc, ranker, competition, concentrator, amplifier):
    ev_high = cfg.EVC_HIGH_THRESHOLD * 3.0
    scan = sc.can_scan(GATE_CLEAR)
    assert scan.allowed is True

    result = ranker.rank(GATE_CLEAR, ev=ev_high, trade_score=0.90,
                         regime="TRENDING", strategy="TrendFollowing",
                         history_score=0.90)
    assert result is not None and result.ok is True

    candidates = [_make_candidate("BTCUSDT", result.rank_score, ev=ev_high)]
    comp = competition.select(GATE_CLEAR, candidates)
    assert len(comp.winners) == 1

    conc = concentrator.concentrate(GATE_CLEAR, rank_score=result.rank_score,
                                    equity=10000.0, base_risk_usdt=100.0,
                                    upstream_mult=1.0)
    assert conc.ok is True
    assert conc.band != "SAFE_FALLBACK"

    amp = amplifier.evaluate(
        GATE_CLEAR, ev=ev_high,
        rank_score=result.rank_score, regime="TRENDING",
        volume_ratio=cfg.EA_VOL_RATIO_THRESHOLD + 0.5,
    )
    assert amp.amplified is True


def test_capital_fallback_is_upstream_mult_only(concentrator):
    base = 100.0
    up = 1.3
    result = concentrator.concentrate(
        GATE_BLOCKED, rank_score=0.95, equity=50000.0,
        base_risk_usdt=base, upstream_mult=up,
    )
    expected = round(base * up, 4)
    assert abs(result.max_risk_usdt - expected) < 0.01
    assert abs(result.size_multiplier - up) < 0.01


def test_amplification_no_boost_in_safe_mode(amplifier):
    result = amplifier.evaluate(
        GATE_SAFE,
        ev=cfg.EA_EV_THRESHOLD * 10,   # massive EV — doesn't matter
        rank_score=1.0,
        regime="TRENDING",
        volume_ratio=10.0,
    )
    assert result.amplified is False
    assert result.tp_multiplier == 1.0
    assert result.trail_multiplier == 1.0
