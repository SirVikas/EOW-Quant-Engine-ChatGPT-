"""
EOW Quant Engine — tests/test_execution_exclusivity.py
Phase 7A.1: Execution Exclusivity — Single Authority Enforcement

Validates that:
  A. The codebase contains EXACTLY ONE execution path (code audit)
  B. The orchestrator enforces exclusivity at runtime
  C. Safe mode → no scan, no signal generation, no execution
  D. Gate blocked → no cycle, no execution
  E. Exploration path respects hard gate but bypasses ranking
  F. Normal execution path works end-to-end under clear gate

Tests:
    Code audit:
        1.  main.py has NO legacy Phase 6.6 pre-trade gate block
        2.  main.py contains orchestrator.gate_check() call
        3.  main.py contains execution_orchestrator.run_cycle() call
        4.  main.py contains orchestrator import
        5.  No ungated scan_market() / scan_markets() function exists in main.py

    Exclusivity enforcement:
        6.  First orchestrator becomes execution authority
        7.  Second orchestrator raises RuntimeError on run_cycle()
        8.  detect_external_execution() returns True for usurper
        9.  Non-exclusive orchestrator (exclusive=False) never raises
        10. _reset_authority() clears the registry

    Safe mode → no scan:
        11. gate_check returns BLOCKED when safe_mode=True
        12. gate_check returns BLOCKED when can_trade=False
        13. run_cycle returns GATE_BLOCKED when safe_mode=True in run_cycle
        14. run_cycle returns SCAN_BLOCKED when scan controller blocks

    Gate blocked → no execution:
        15. run_cycle returns execute=False when gate blocked
        16. run_cycle execute=False has concentration_mult=1.0 (safe default)
        17. run_cycle execute=False has tp_multiplier=1.0

    Exploration path:
        18. Exploration trade executes when gate clear (bypasses rank)
        19. Exploration trade blocked by gate even in exploration mode
        20. Exploration CycleResult has band="EXPLORATION"
        21. Exploration CycleResult concentration_mult == upstream_mult
        22. Exploration CycleResult tp_multiplier==1.0 (no amplification)
        23. Exploration blocked by pre-trade gate (indicators not ready)

    Normal execution:
        24. High-quality trade executes (full pipeline)
        25. Low-quality trade is RANK_REJECT
        26. Total cycles / blocked / execute tracked correctly
        27. Summary reports phase 7A.1
        28. Summary is_authority True for registered orchestrator
"""
from __future__ import annotations

import pathlib
import pytest

from core.orchestrator.execution_orchestrator import (
    ExecutionOrchestrator,
    TickContext,
    CycleResult,
    GateCheckResult,
)
from core.gating.safe_mode_engine import SafeModeEngine
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _gate(can_trade=True, safe_mode=False, reason="ALL_CLEAR"):
    return {"can_trade": can_trade, "safe_mode": safe_mode, "reason": reason}


GATE_CLEAR   = _gate(True,  False, "ALL_CLEAR")
GATE_BLOCKED = _gate(False, True,  "WS_UNSTABLE")
GATE_SAFE    = _gate(True,  True,  "SAFE_MODE")


class _FakeGate:
    def __init__(self, status): self._s = status
    def evaluate(self, **kwargs): return self._s
    def can_trade(self): return self._s.get("can_trade", False)


def _make_orc(gate_status=None, exclusive=False) -> ExecutionOrchestrator:
    """Build a fresh, non-exclusive orchestrator for isolated tests."""
    status = gate_status or GATE_CLEAR
    sme = SafeModeEngine()
    return ExecutionOrchestrator(
        global_gate=_FakeGate(status),
        safe_mode=sme,
        scan_ctrl=ScanController(),
        ranker=GateAwareTradeRanker(base=TradeRanker()),
        competition=GateAwareCompetitionEngine(base=TradeCompetitionEngine()),
        concentrator=GateAwareCapitalConcentrator(base=CapitalConcentrator()),
        pre_trade=PreTradeGate(safe_mode=sme),
        amplifier=GateAwareEdgeAmplifier(base=EdgeAmplifier()),
        exclusive=exclusive,
    )


def _ctx(
    is_exploration=False, ev=0.0, trade_score=0.5,
    regime="TRENDING", strategy="TrendFollowing",
    indicator_ok=True, data_fresh=True, upstream_mult=1.0,
    volume_ratio=1.0, history_score=None,
) -> TickContext:
    return TickContext(
        symbol="BTCUSDT", price=50000.0,
        regime=regime, strategy=strategy,
        ev=ev, trade_score=trade_score, volume_ratio=volume_ratio,
        equity=10000.0, base_risk_usdt=100.0,
        upstream_mult=upstream_mult,
        indicator_ok=indicator_ok, data_fresh=data_fresh,
        history_score=history_score,
        is_exploration=is_exploration,
    )


def _high_ctx(**kw) -> TickContext:
    ev_elite = cfg.EVC_HIGH_THRESHOLD * 3.0
    defaults = dict(
        ev=ev_elite, trade_score=0.90,
        regime="TRENDING", strategy="TrendFollowing",
        volume_ratio=cfg.EA_VOL_RATIO_THRESHOLD + 0.5,
        history_score=0.90,
    )
    defaults.update(kw)
    return _ctx(**defaults)


@pytest.fixture(autouse=True)
def reset_authority():
    """Reset global authority registry before and after every test."""
    ExecutionOrchestrator._reset_authority()
    yield
    ExecutionOrchestrator._reset_authority()


# ── A. Code audit ─────────────────────────────────────────────────────────────

MAIN_PY = pathlib.Path("main.py").read_text()


def test_no_legacy_phase66_gate_block_in_main():
    """The old Phase 6.6 pre-trade gate block must be gone."""
    assert "Phase 6.6: Pre-trade gate — master permission check" not in MAIN_PY


def test_main_contains_gate_check_call():
    """Orchestrator gate_check must be called in main.py."""
    assert "orchestrator.gate_check(" in MAIN_PY or "execution_orchestrator.gate_check(" in MAIN_PY


def test_main_contains_run_cycle_call():
    """Orchestrator run_cycle must be called in main.py."""
    assert "execution_orchestrator.run_cycle(" in MAIN_PY


def test_main_imports_orchestrator():
    """main.py must import the execution orchestrator."""
    assert "execution_orchestrator" in MAIN_PY
    assert "from core.orchestrator" in MAIN_PY


def test_no_ungated_scan_function_in_main():
    """No bare scan_market() / scan_markets() call outside orchestrator."""
    assert "scan_market(" not in MAIN_PY
    assert "scan_markets(" not in MAIN_PY


# ── B. Exclusivity enforcement ────────────────────────────────────────────────

def test_first_orchestrator_becomes_authority():
    orc = _make_orc(exclusive=True)
    orc.run_cycle(_high_ctx())
    from core.orchestrator.execution_orchestrator import _EXECUTION_AUTHORITY
    assert _EXECUTION_AUTHORITY is orc


def test_second_orchestrator_raises_on_run_cycle():
    orc1 = _make_orc(exclusive=True)
    orc2 = _make_orc(exclusive=True)
    orc1.run_cycle(_high_ctx())  # orc1 claims authority
    with pytest.raises(RuntimeError, match="Legacy execution path detected"):
        orc2.run_cycle(_high_ctx())  # orc2 is the usurper


def test_detect_external_execution_true_for_usurper():
    orc1 = _make_orc(exclusive=True)
    orc2 = _make_orc(exclusive=True)
    orc1.run_cycle(_high_ctx())
    assert orc2.detect_external_execution() is True


def test_non_exclusive_orchestrator_never_raises():
    orc1 = _make_orc(exclusive=True)
    orc2 = _make_orc(exclusive=False)
    orc1.run_cycle(_high_ctx())   # orc1 claims authority
    orc2.run_cycle(_high_ctx())   # orc2 is non-exclusive, no raise


def test_reset_authority_clears_registry():
    orc1 = _make_orc(exclusive=True)
    orc1.run_cycle(_high_ctx())
    ExecutionOrchestrator._reset_authority()
    orc2 = _make_orc(exclusive=True)
    orc2.run_cycle(_high_ctx())  # should not raise after reset


# ── C. Safe mode → no scan ────────────────────────────────────────────────────

def test_gate_check_blocked_in_safe_mode():
    # qFTD-010: scanning is ALWAYS ON — gate_check returns allowed=True even in safe_mode.
    # Execution is blocked downstream by the ranker (not the scan layer).
    orc = _make_orc(GATE_SAFE)
    result = orc.gate_check(symbol="BTCUSDT", strategy="TrendFollowing")
    assert result.allowed is True
    assert result.action == "ALLOWED"


def test_gate_check_blocked_when_can_trade_false():
    orc = _make_orc(GATE_BLOCKED)
    result = orc.gate_check()
    assert result.allowed is False
    assert result.action == "GATE_BLOCKED"


def test_run_cycle_gate_blocked_in_safe_mode():
    # qFTD-010: scan proceeds but ranker blocks in safe_mode → RANK_REJECT
    orc = _make_orc(GATE_SAFE)
    result = orc.run_cycle(_ctx())
    assert result.execute is False
    assert result.action in ("GATE_BLOCKED", "SCAN_BLOCKED", "RANK_REJECT")


def test_run_cycle_scan_blocked_returns_no_execute():
    orc = _make_orc(GATE_SAFE)
    result = orc.run_cycle(_high_ctx())
    assert result.execute is False


# ── D. Gate blocked → no execution ───────────────────────────────────────────

def test_run_cycle_execute_false_when_gate_blocked():
    orc = _make_orc(GATE_BLOCKED)
    result = orc.run_cycle(_ctx())
    assert result.execute is False
    assert result.action == "GATE_BLOCKED"


def test_run_cycle_blocked_concentration_mult_is_safe():
    orc = _make_orc(GATE_BLOCKED)
    result = orc.run_cycle(_ctx())
    assert result.concentration_mult == 1.0


def test_run_cycle_blocked_tp_mult_is_one():
    orc = _make_orc(GATE_BLOCKED)
    result = orc.run_cycle(_ctx())
    assert result.tp_multiplier == 1.0


# ── E. Exploration path ───────────────────────────────────────────────────────

def test_exploration_executes_when_gate_clear():
    orc = _make_orc(GATE_CLEAR)
    result = orc.run_cycle(_ctx(is_exploration=True, ev=0.0, trade_score=0.4))
    assert result.execute is True
    assert result.action == "EXECUTE"


def test_exploration_blocked_by_gate():
    orc = _make_orc(GATE_BLOCKED)
    result = orc.run_cycle(_ctx(is_exploration=True))
    assert result.execute is False
    assert result.action == "GATE_BLOCKED"


def test_exploration_band_label():
    orc = _make_orc(GATE_CLEAR)
    result = orc.run_cycle(_ctx(is_exploration=True))
    assert result.execute is True
    assert result.band == "EXPLORATION"


def test_exploration_concentration_mult_equals_upstream():
    upstream = 1.35
    orc = _make_orc(GATE_CLEAR)
    result = orc.run_cycle(_ctx(is_exploration=True, upstream_mult=upstream))
    assert result.execute is True
    assert abs(result.concentration_mult - upstream) < 0.01


def test_exploration_no_amplification():
    orc = _make_orc(GATE_CLEAR)
    result = orc.run_cycle(_ctx(is_exploration=True))
    assert result.tp_multiplier == 1.0
    assert result.trail_multiplier == 1.0


def test_exploration_blocked_by_ptg_when_indicators_not_ready():
    orc = _make_orc(GATE_CLEAR)
    result = orc.run_cycle(_ctx(is_exploration=True, indicator_ok=False))
    assert result.execute is False
    assert result.action == "PTG_BLOCKED"
    assert "INDICATORS_NOT_READY" in result.reason


# ── F. Normal execution ───────────────────────────────────────────────────────

def test_high_quality_trade_executes():
    orc = _make_orc(GATE_CLEAR)
    result = orc.run_cycle(_high_ctx())
    assert result.execute is True
    assert result.action == "EXECUTE"
    assert result.rank_score >= cfg.TR_MIN_RANK_SCORE


def test_low_quality_trade_rank_rejected():
    orc = _make_orc(GATE_CLEAR)
    result = orc.run_cycle(_ctx(ev=0.0, trade_score=0.0, regime="UNKNOWN"))
    assert result.execute is False
    assert result.action == "RANK_REJECT"


def test_cycle_counts_tracked():
    orc = _make_orc(GATE_CLEAR)
    orc.run_cycle(_high_ctx())     # execute
    orc.run_cycle(_ctx(ev=0.0, trade_score=0.0, regime="UNKNOWN"))  # rank_reject
    orc.run_cycle(_ctx(is_exploration=True))  # exploration execute
    s = orc.summary()
    assert s["total_cycles"] == 3
    assert s["total_execute"] == 2
    assert s["total_blocked"] == 1
    assert s["total_exploration"] == 1


def test_summary_phase_label():
    orc = _make_orc(GATE_CLEAR)
    s = orc.summary()
    assert s["phase"] == "7A.1"
    assert s["module"] == "EXECUTION_ORCHESTRATOR"


def test_summary_is_authority_true_for_registered():
    orc = _make_orc(exclusive=True)
    orc.run_cycle(_high_ctx())
    s = orc.summary()
    assert s["is_authority"] is True
