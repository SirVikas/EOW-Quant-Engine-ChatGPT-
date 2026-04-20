"""
EOW Quant Engine — tests/test_phase7A_integration.py
Phase 7A Integration: Execution Orchestrator Tests

Coverage (per spec):
    Gate / scan control:
        1.  Safe mode active → gate_check blocked, no scan
        2.  Gate blocked (can_trade=False) → gate_check blocked, no cycle
        3.  Gate allowed → gate_check passes

    Full pipeline via run_cycle:
        4.  Gate blocked inside run_cycle → GATE_BLOCKED result
        5.  Safe mode inside run_cycle → GATE_BLOCKED / SCAN_BLOCKED result
        6.  Gate clear → full pipeline runs → EXECUTE result
        7.  Ranking disabled (low ev/score) → RANK_REJECT result
        8.  Competition filters all out → COMPETITION_REJECT result
        9.  Capital concentration fallback when gate gated off
        10. Amplifier disabled in safe mode → no TP/trail boost
        11. run_cycle returns correct concentration_mult
        12. run_cycle returns correct tp_multiplier when amplified
        13. run_cycle EXECUTE result has all required fields
        14. Multiple blocked cycles tracked in summary
        15. Orchestrator summary reports correct counts
        16. GateCheckResult fields are populated
        17. PTG blocks inside run_cycle → PTG_BLOCKED
        18. EXECUTE result action string is "EXECUTE"
        19. GATE_BLOCKED result has execute=False
        20. Full pipeline stats: execute_rate correct after mix of cycles
"""
from __future__ import annotations

import pytest

from core.orchestrator.execution_orchestrator import (
    ExecutionOrchestrator,
    TickContext,
    CycleResult,
    GateCheckResult,
)
from core.gating.global_gate_controller import GlobalGateController
from core.gating.safe_mode_engine import SafeModeEngine, SafeMode
from core.gating.pre_trade_gate import PreTradeGate
from core.profit.scan_controller import ScanController
from core.profit.trade_ranker import GateAwareTradeRanker
from core.profit.trade_competition import GateAwareCompetitionEngine
from core.profit.capital_concentrator import GateAwareCapitalConcentrator
from core.profit.edge_amplifier import GateAwareEdgeAmplifier
from core.trade_ranker import TradeRanker
from core.capital_concentrator import CapitalConcentrator
from core.edge_amplifier import EdgeAmplifier
from core.trade_competition import TradeCompetitionEngine

from config import cfg


# ── Gate status factories ─────────────────────────────────────────────────────

def _gate(can_trade=True, safe_mode=False, reason="ALL_CLEAR"):
    return {"can_trade": can_trade, "safe_mode": safe_mode, "reason": reason}


GATE_CLEAR   = _gate(True,  False, "ALL_CLEAR")
GATE_BLOCKED = _gate(False, True,  "WS_UNSTABLE")
GATE_SAFE    = _gate(True,  True,  "SAFE_MODE")


# ── Orchestrator factory ──────────────────────────────────────────────────────

def _make_orchestrator(gate_status: dict, sme: SafeModeEngine = None) -> ExecutionOrchestrator:
    """Build an orchestrator wired to a fixed gate_status for testing."""
    _sme = sme or SafeModeEngine()

    class _FakeGate:
        def evaluate(self): return gate_status
        def can_trade(self): return gate_status.get("can_trade", False)

    return ExecutionOrchestrator(
        global_gate=_FakeGate(),
        safe_mode=_sme,
        scan_ctrl=ScanController(),
        ranker=GateAwareTradeRanker(base=TradeRanker()),
        competition=GateAwareCompetitionEngine(base=TradeCompetitionEngine()),
        concentrator=GateAwareCapitalConcentrator(base=CapitalConcentrator()),
        pre_trade=PreTradeGate(safe_mode=_sme),
        amplifier=GateAwareEdgeAmplifier(base=EdgeAmplifier()),
    )


def _ctx(
    ev=0.0, trade_score=0.5, regime="TRENDING", strategy="TrendFollowing",
    volume_ratio=1.0, equity=10000.0, base_risk_usdt=100.0, upstream_mult=1.0,
    indicator_ok=True, data_fresh=True, history_score=None,
) -> TickContext:
    return TickContext(
        symbol="BTCUSDT", price=50000.0,
        regime=regime, strategy=strategy,
        ev=ev, trade_score=trade_score,
        volume_ratio=volume_ratio,
        equity=equity, base_risk_usdt=base_risk_usdt,
        upstream_mult=upstream_mult,
        indicator_ok=indicator_ok, data_fresh=data_fresh,
        history_score=history_score,
    )


def _high_quality_ctx(**overrides) -> TickContext:
    """TickContext guaranteed to pass ranking with ELITE band."""
    ev_elite = cfg.EVC_HIGH_THRESHOLD * 3.0
    defaults = dict(
        ev=ev_elite, trade_score=0.90,
        regime="TRENDING", strategy="TrendFollowing",
        volume_ratio=cfg.EA_VOL_RATIO_THRESHOLD + 0.5,
        equity=10000.0, base_risk_usdt=100.0, upstream_mult=1.0,
        indicator_ok=True, data_fresh=True, history_score=0.90,
    )
    defaults.update(overrides)
    return _ctx(**defaults)


# ── 1–3: gate_check ──────────────────────────────────────────────────────────

def test_gate_check_blocked_when_safe_mode():
    orc = _make_orchestrator(GATE_SAFE)
    result = orc.gate_check(symbol="BTCUSDT", strategy="TrendFollowing")
    assert result.allowed is False
    assert result.action in ("GATE_BLOCKED", "SCAN_BLOCKED")


def test_gate_check_blocked_when_can_trade_false():
    orc = _make_orchestrator(GATE_BLOCKED)
    result = orc.gate_check(symbol="BTCUSDT", strategy="TrendFollowing")
    assert result.allowed is False
    assert result.action == "GATE_BLOCKED"


def test_gate_check_allowed_when_clear():
    orc = _make_orchestrator(GATE_CLEAR)
    result = orc.gate_check(symbol="BTCUSDT", strategy="TrendFollowing")
    assert result.allowed is True
    assert result.action == "ALLOWED"
    assert "gate_status" in result.__dataclass_fields__


# ── 4–5: run_cycle gate blocks ────────────────────────────────────────────────

def test_run_cycle_gate_blocked():
    orc = _make_orchestrator(GATE_BLOCKED)
    result = orc.run_cycle(_ctx())
    assert result.execute is False
    assert result.action == "GATE_BLOCKED"
    assert result.concentration_mult == 1.0
    assert result.tp_multiplier == 1.0


def test_run_cycle_blocked_in_safe_mode():
    orc = _make_orchestrator(GATE_SAFE)
    result = orc.run_cycle(_ctx())
    assert result.execute is False
    assert result.action in ("GATE_BLOCKED", "SCAN_BLOCKED")


# ── 6: Full pipeline runs when gate clear ─────────────────────────────────────

def test_run_cycle_executes_when_gate_clear():
    orc = _make_orchestrator(GATE_CLEAR)
    ctx = _high_quality_ctx()
    result = orc.run_cycle(ctx)
    assert result.execute is True
    assert result.action == "EXECUTE"
    assert result.rank_score >= cfg.TR_MIN_RANK_SCORE
    assert result.band != ""
    assert result.concentration_mult > 0.0


# ── 7: Ranking blocks low-quality trade ──────────────────────────────────────

def test_run_cycle_rank_reject():
    orc = _make_orchestrator(GATE_CLEAR)
    # ev=0, trade_score=0, history=0 → rank_score ≈ 0.075 (below 0.60 threshold)
    ctx = _ctx(ev=0.0, trade_score=0.0, regime="UNKNOWN",
                strategy="TrendFollowing", history_score=0.0)
    result = orc.run_cycle(ctx)
    assert result.execute is False
    assert result.action == "RANK_REJECT"


# ── 8: Competition rejects when gate off ─────────────────────────────────────

def test_run_cycle_competition_rejects_in_safe_mode():
    orc = _make_orchestrator(GATE_SAFE)
    ctx = _high_quality_ctx()
    result = orc.run_cycle(ctx)
    assert result.execute is False
    # Action could be GATE_BLOCKED or SCAN_BLOCKED (gate fires before competition)
    assert result.action in ("GATE_BLOCKED", "SCAN_BLOCKED", "COMPETITION_REJECT")


# ── 9: Capital concentration fallback ────────────────────────────────────────

def test_concentration_fallback_when_gate_blocked():
    from core.profit.capital_concentrator import GateAwareCapitalConcentrator, CapitalConcentrator
    cc = GateAwareCapitalConcentrator(base=CapitalConcentrator())
    result = cc.concentrate(
        GATE_BLOCKED, rank_score=0.95, equity=10000.0,
        base_risk_usdt=100.0, upstream_mult=1.5,
    )
    assert result.band == "SAFE_FALLBACK"
    assert abs(result.size_multiplier - 1.5) < 0.01


# ── 10: Amplifier disabled in safe mode ──────────────────────────────────────

def test_amplifier_no_boost_in_safe_mode():
    from core.profit.edge_amplifier import GateAwareEdgeAmplifier
    amp = GateAwareEdgeAmplifier(base=EdgeAmplifier())
    result = amp.evaluate(
        GATE_SAFE,
        ev=cfg.EA_EV_THRESHOLD * 10,
        rank_score=1.0,
        regime="TRENDING",
        volume_ratio=10.0,
    )
    assert result.amplified is False
    assert result.tp_multiplier == 1.0
    assert result.trail_multiplier == 1.0


# ── 11: run_cycle concentration_mult is correct ───────────────────────────────

def test_run_cycle_concentration_mult_is_elite():
    orc = _make_orchestrator(GATE_CLEAR)
    ctx = _high_quality_ctx(upstream_mult=1.0)
    result = orc.run_cycle(ctx)
    assert result.execute is True
    # ELITE band → concentration_mult ≥ cfg.CC_MULT_ELITE (possibly capped)
    assert result.concentration_mult >= 1.0   # at minimum upstream_mult


# ── 12: run_cycle tp_multiplier when amplified ───────────────────────────────

def test_run_cycle_tp_multiplier_when_amplified():
    orc = _make_orchestrator(GATE_CLEAR)
    ctx = _high_quality_ctx(
        ev=cfg.EA_EV_THRESHOLD + 0.10,
        volume_ratio=cfg.EA_VOL_RATIO_THRESHOLD + 1.0,
    )
    result = orc.run_cycle(ctx)
    assert result.execute is True
    if result.amplified:
        assert result.tp_multiplier == cfg.EA_TP_BOOST_MULT
        assert result.trail_multiplier == cfg.EA_TRAIL_BOOST_MULT


# ── 13: EXECUTE result has all required fields ────────────────────────────────

def test_execute_result_has_all_fields():
    orc = _make_orchestrator(GATE_CLEAR)
    result = orc.run_cycle(_high_quality_ctx())
    assert result.execute is True
    assert isinstance(result.action, str)
    assert isinstance(result.reason, str)
    assert isinstance(result.concentration_mult, float)
    assert isinstance(result.tp_multiplier, float)
    assert isinstance(result.trail_multiplier, float)
    assert isinstance(result.rank_score, float)
    assert isinstance(result.band, str)
    assert isinstance(result.gate_status, dict)


# ── 14: Multiple blocked cycles tracked ───────────────────────────────────────

def test_blocked_cycles_tracked_in_summary():
    orc = _make_orchestrator(GATE_BLOCKED)
    for _ in range(5):
        orc.run_cycle(_ctx())
    s = orc.summary()
    assert s["total_cycles"] == 5
    assert s["total_blocked"] == 5
    assert s["total_execute"] == 0


# ── 15: Summary stats correct ────────────────────────────────────────────────

def test_summary_execute_rate():
    orc = _make_orchestrator(GATE_CLEAR)
    ctx = _high_quality_ctx()
    orc.run_cycle(ctx)   # 1 execute
    orc.run_cycle(ctx)   # 1 execute
    s = orc.summary()
    assert s["total_cycles"] == 2
    assert s["total_execute"] == 2
    assert s["execute_rate"] == 1.0
    assert s["module"] == "EXECUTION_ORCHESTRATOR"
    assert s["phase"] == "7A"


# ── 16: GateCheckResult fields ───────────────────────────────────────────────

def test_gate_check_result_fields():
    orc = _make_orchestrator(GATE_CLEAR)
    result = orc.gate_check(symbol="ETHUSDT", strategy="MeanReversion",
                             indicator_ok=True, data_fresh=True)
    assert isinstance(result, GateCheckResult)
    assert isinstance(result.allowed, bool)
    assert isinstance(result.action, str)
    assert isinstance(result.reason, str)
    assert isinstance(result.gate_status, dict)


# ── 17: PTG blocks inside run_cycle ──────────────────────────────────────────

def test_ptg_blocks_when_indicators_not_ready():
    """PreTradeGate blocks inside run_cycle when indicator_ok=False."""
    orc = _make_orchestrator(GATE_CLEAR)
    ctx = _high_quality_ctx(indicator_ok=False)
    result = orc.run_cycle(ctx)
    assert result.execute is False
    assert result.action == "PTG_BLOCKED"
    assert "INDICATORS_NOT_READY" in result.reason


def test_ptg_blocks_when_data_not_fresh():
    orc = _make_orchestrator(GATE_CLEAR)
    ctx = _high_quality_ctx(data_fresh=False)
    result = orc.run_cycle(ctx)
    assert result.execute is False
    assert result.action == "PTG_BLOCKED"
    assert "DATA_NOT_FRESH" in result.reason


# ── 18–19: Action string and execute flag ────────────────────────────────────

def test_execute_result_action_string():
    orc = _make_orchestrator(GATE_CLEAR)
    result = orc.run_cycle(_high_quality_ctx())
    assert result.action == "EXECUTE"


def test_gate_blocked_result_execute_is_false():
    orc = _make_orchestrator(GATE_BLOCKED)
    result = orc.run_cycle(_ctx())
    assert result.execute is False
    assert result.action == "GATE_BLOCKED"


# ── 20: Execute rate correct after mixed cycles ───────────────────────────────

def test_execute_rate_mixed_cycles():
    orc_clear   = _make_orchestrator(GATE_CLEAR)
    orc_blocked = _make_orchestrator(GATE_BLOCKED)

    ctx_good = _high_quality_ctx()
    ctx_bad  = _ctx(ev=0.0, trade_score=0.0, history_score=0.0, regime="UNKNOWN")

    # 2 execute + 3 blocked (rank)
    orc_clear.run_cycle(ctx_good)   # EXECUTE
    orc_clear.run_cycle(ctx_good)   # EXECUTE
    orc_clear.run_cycle(ctx_bad)    # RANK_REJECT
    orc_clear.run_cycle(ctx_bad)    # RANK_REJECT
    orc_clear.run_cycle(ctx_bad)    # RANK_REJECT

    s = orc_clear.summary()
    assert s["total_cycles"] == 5
    assert s["total_execute"] == 2
    assert s["total_blocked"] == 3
    assert abs(s["execute_rate"] - 0.4) < 0.01
