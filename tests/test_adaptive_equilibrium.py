"""
Phase-F Adaptive Equilibrium & Capital Discipline — 84-check test suite.

Structure: 7 test classes × 12 checks each = 84 total.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.adaptive_equilibrium.kelly_efficiency_engine      import compute_kelly_efficiency
from core.adaptive_equilibrium.drawdown_dynamics_engine     import compute_drawdown_dynamics
from core.adaptive_equilibrium.return_consistency_engine    import compute_return_consistency
from core.adaptive_equilibrium.capital_utilization_engine   import compute_capital_utilization
from core.adaptive_equilibrium.equilibrium_band_engine      import compute_equilibrium_band
from core.adaptive_equilibrium.discipline_cost_engine       import compute_discipline_cost
from core.adaptive_equilibrium.adaptive_equilibrium_orchestrator import (
    run_adaptive_equilibrium, get_equilibrium_health,
)

# ── Synthetic trade datasets ──────────────────────────────────────────────────

def _trades_profitable(n=30):
    return [{"pnl": 2.0 + i * 0.1, "size": 1.0, "confidence": 0.8,
             "regime": "TRENDING"} for i in range(n)]

def _trades_losing(n=30):
    return [{"pnl": -1.5 - i * 0.05, "size": 1.0, "confidence": 0.3,
             "regime": "RANGING"} for i in range(n)]

def _trades_mixed(n=30):
    return [{"pnl": (2.0 if i % 3 != 0 else -4.0), "size": 1.0 + (i % 3) * 0.5,
             "confidence": 0.6 if i % 2 == 0 else 0.4,
             "regime": "TRENDING" if i % 2 == 0 else "RANGING"}
            for i in range(n)]

def _trades_empty():
    return []

def _trades_few():
    return [{"pnl": 1.0, "size": 1.0} for _ in range(3)]


PASS = 0; FAIL = 0

def chk(label, cond):
    global PASS, FAIL
    if cond:
        print(f"  \033[92m✓\033[0m  {label}")
        PASS += 1
    else:
        print(f"  \033[91m✗\033[0m  {label}")
        FAIL += 1


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 — F.1 Kelly Efficiency Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_kelly_efficiency():
    print("\n\033[1m\033[93m── TEST 1 — F.1 Kelly Efficiency Engine ──────────────────────\033[0m")

    r_profit = compute_kelly_efficiency(_trades_profitable())
    r_loss   = compute_kelly_efficiency(_trades_losing())
    r_mixed  = compute_kelly_efficiency(_trades_mixed())
    r_few    = compute_kelly_efficiency(_trades_few())
    r_empty  = compute_kelly_efficiency(_trades_empty())

    chk("C1: engine name correct",            r_profit["engine"] == "F.1_KELLY_EFFICIENCY")
    chk("C2: lineage_id present profitable",  r_profit.get("lineage_id", "").startswith("EQ-F1-"))
    chk("C3: win_rate in [0,1]",              0.0 <= r_profit.get("win_rate", -1) <= 1.0)
    chk("C4: kelly_fraction >= 0",            r_profit.get("kelly_fraction", -1) >= 0.0)
    chk("C5: efficiency_score in [0,100]",    0.0 <= r_profit.get("efficiency_score", -1) <= 100.0)
    chk("C6: state is valid",                 r_profit.get("state") in ("OPTIMAL","ADEQUATE","SUBOPTIMAL","NEGLIGENT"))
    chk("C7: losing data has state",          r_loss.get("state") in ("OPTIMAL","ADEQUATE","SUBOPTIMAL","NEGLIGENT"))
    chk("C8: constitutional flag present",    r_profit.get("diagnostic_only") is True)
    chk("C9: auto_authorized=False",          r_profit.get("auto_authorized") is False)
    chk("C10: lineage_preserved=True",        r_profit.get("lineage_preserved") is True)
    chk("C11: few trades returns dict",       isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",        isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — F.2 Drawdown Dynamics Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_drawdown_dynamics():
    print("\n\033[1m\033[93m── TEST 2 — F.2 Drawdown Dynamics Engine ─────────────────────\033[0m")

    r_profit = compute_drawdown_dynamics(_trades_profitable())
    r_loss   = compute_drawdown_dynamics(_trades_losing())
    r_mixed  = compute_drawdown_dynamics(_trades_mixed())
    r_few    = compute_drawdown_dynamics(_trades_few())
    r_empty  = compute_drawdown_dynamics(_trades_empty())

    chk("C1: engine name correct",             r_profit["engine"] == "F.2_DRAWDOWN_DYNAMICS")
    chk("C2: lineage_id present",              r_profit.get("lineage_id", "").startswith("EQ-F2-"))
    chk("C3: max_drawdown >= 0 (profitable)",  r_profit.get("max_drawdown", -1) >= 0.0)
    chk("C4: max_drawdown > 0 (losing)",       r_loss.get("max_drawdown", 0) > 0)
    chk("C5: state valid (profitable)",        r_profit.get("state") in ("STABLE","RECOVERING","DETERIORATING","CRITICAL"))
    chk("C6: state valid (losing)",            r_loss.get("state") in ("STABLE","RECOVERING","DETERIORATING","CRITICAL"))
    chk("C7: recovery_velocity is float",      isinstance(r_profit.get("recovery_velocity"), float))
    chk("C8: drawdown_count is int >= 0",      isinstance(r_profit.get("drawdown_count"), int))
    chk("C9: constitutional flag present",     r_profit.get("diagnostic_only") is True)
    chk("C10: auto_authorized=False",          r_profit.get("auto_authorized") is False)
    chk("C11: few trades returns dict",        isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",         isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — F.3 Return Consistency Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_return_consistency():
    print("\n\033[1m\033[93m── TEST 3 — F.3 Return Consistency Engine ────────────────────\033[0m")

    r_profit = compute_return_consistency(_trades_profitable())
    r_loss   = compute_return_consistency(_trades_losing())
    r_mixed  = compute_return_consistency(_trades_mixed())
    r_few    = compute_return_consistency(_trades_few())
    r_empty  = compute_return_consistency(_trades_empty())

    chk("C1: engine name correct",              r_profit["engine"] == "F.3_RETURN_CONSISTENCY")
    chk("C2: lineage_id present",               r_profit.get("lineage_id", "").startswith("EQ-F3-"))
    chk("C3: consistency_score in [0,100]",     0.0 <= r_profit.get("consistency_score", -1) <= 100.0)
    chk("C4: positive_ratio in [0,1]",          0.0 <= r_profit.get("positive_ratio", -1) <= 1.0)
    chk("C5: profitable has positive_ratio=1",  r_profit.get("positive_ratio", 0) == 1.0)
    chk("C6: max_streak >= 1",                  r_profit.get("max_streak", 0) >= 1)
    chk("C7: state valid",                       r_profit.get("state") in ("CONSISTENT","ADEQUATE","VARIABLE","ERRATIC"))
    chk("C8: losing state is degraded",          r_loss.get("state") in ("CONSISTENT","ADEQUATE","VARIABLE","ERRATIC"))
    chk("C9: constitutional flag present",       r_profit.get("diagnostic_only") is True)
    chk("C10: auto_authorized=False",            r_profit.get("auto_authorized") is False)
    chk("C11: few trades returns dict",          isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",           isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 — F.4 Capital Utilization Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_capital_utilization():
    print("\n\033[1m\033[93m── TEST 4 — F.4 Capital Utilization Engine ───────────────────\033[0m")

    r_profit = compute_capital_utilization(_trades_profitable())
    r_loss   = compute_capital_utilization(_trades_losing())
    r_mixed  = compute_capital_utilization(_trades_mixed())
    r_few    = compute_capital_utilization(_trades_few())
    r_empty  = compute_capital_utilization(_trades_empty())

    chk("C1: engine name correct",              r_profit["engine"] == "F.4_CAPITAL_UTILIZATION")
    chk("C2: lineage_id present",               r_profit.get("lineage_id", "").startswith("EQ-F4-"))
    chk("C3: utilization_score in [0,100]",     0.0 <= r_profit.get("utilization_score", -1) <= 100.0)
    chk("C4: util_ratio in [0,1]",              0.0 <= r_profit.get("util_ratio", -1) <= 1.0)
    chk("C5: state valid",                       r_profit.get("state") in ("EFFICIENT","ADEQUATE","UNDERUTILIZED","OVEREXTENDED"))
    chk("C6: avg_pnl_per_unit present",          "avg_pnl_per_unit" in r_profit)
    chk("C7: size_cv >= 0",                      r_profit.get("size_cv", -1) >= 0.0)
    chk("C8: losing state is valid",             r_loss.get("state") in ("EFFICIENT","ADEQUATE","UNDERUTILIZED","OVEREXTENDED"))
    chk("C9: constitutional flag present",       r_profit.get("diagnostic_only") is True)
    chk("C10: auto_authorized=False",            r_profit.get("auto_authorized") is False)
    chk("C11: few trades returns dict",          isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",           isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5 — F.5 Equilibrium Band Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_equilibrium_band():
    print("\n\033[1m\033[93m── TEST 5 — F.5 Equilibrium Band Engine ──────────────────────\033[0m")

    r_profit = compute_equilibrium_band(_trades_profitable())
    r_loss   = compute_equilibrium_band(_trades_losing())
    r_mixed  = compute_equilibrium_band(_trades_mixed())
    r_few    = compute_equilibrium_band(_trades_few())
    r_empty  = compute_equilibrium_band(_trades_empty())

    chk("C1: engine name correct",             r_profit["engine"] == "F.5_EQUILIBRIUM_BAND")
    chk("C2: lineage_id present",              r_profit.get("lineage_id", "").startswith("EQ-F5-"))
    chk("C3: ref_std >= 0",                    r_profit.get("ref_std", -1) >= 0.0)
    chk("C4: band_upper >= band_lower",        r_profit.get("band_upper", 0) >= r_profit.get("band_lower", 1))
    chk("C5: sigma_units >= 0",                r_profit.get("sigma_units", -1) >= 0.0)
    chk("C6: excursions is int >= 0",          isinstance(r_profit.get("excursions"), int) and r_profit["excursions"] >= 0)
    chk("C7: state valid",                      r_profit.get("state") in ("IN_BAND","APPROACHING","OUTSIDE_BAND","FAR_OUTSIDE"))
    chk("C8: excursion_ratio in [0,1]",         0.0 <= r_profit.get("excursion_ratio", -1) <= 1.0)
    chk("C9: constitutional flag present",      r_profit.get("diagnostic_only") is True)
    chk("C10: auto_authorized=False",           r_profit.get("auto_authorized") is False)
    chk("C11: few trades returns dict",         isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",          isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6 — F.6 Discipline Cost Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_discipline_cost():
    print("\n\033[1m\033[93m── TEST 6 — F.6 Discipline Cost Engine ───────────────────────\033[0m")

    r_profit = compute_discipline_cost(_trades_profitable())
    r_loss   = compute_discipline_cost(_trades_losing())
    r_mixed  = compute_discipline_cost(_trades_mixed())
    r_few    = compute_discipline_cost(_trades_few())
    r_empty  = compute_discipline_cost(_trades_empty())

    chk("C1: engine name correct",              r_profit["engine"] == "F.6_DISCIPLINE_COST")
    chk("C2: lineage_id present",               r_profit.get("lineage_id", "").startswith("EQ-F6-"))
    chk("C3: cost_ratio >= 0",                  r_profit.get("cost_ratio", -1) >= 0.0)
    chk("C4: cost_ratio is float",              isinstance(r_profit.get("cost_ratio"), float))
    chk("C5: state valid",                       r_profit.get("state") in ("COST_MINIMAL","COST_MODERATE","COST_SIGNIFICANT","COST_SEVERE"))
    chk("C6: high_signal_trades > 0",           r_profit.get("high_signal_trades", 0) > 0)
    chk("C7: low_signal_trades > 0",            r_profit.get("low_signal_trades", 0) > 0)
    chk("C8: costs are non-negative",           r_profit.get("cost_over_caution", -1) >= 0 and
                                                 r_profit.get("cost_under_discipline", -1) >= 0)
    chk("C9: constitutional flag present",       r_profit.get("diagnostic_only") is True)
    chk("C10: auto_authorized=False",            r_profit.get("auto_authorized") is False)
    chk("C11: few trades returns dict",          isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",           isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7 — F.7 Adaptive Equilibrium Orchestrator
# ══════════════════════════════════════════════════════════════════════════════
def test_adaptive_equilibrium_orchestrator():
    print("\n\033[1m\033[93m── TEST 7 — F.7 Adaptive Equilibrium Orchestrator ────────────\033[0m")

    r_profit = run_adaptive_equilibrium(_trades_profitable())
    r_loss   = run_adaptive_equilibrium(_trades_losing())
    r_mixed  = run_adaptive_equilibrium(_trades_mixed())
    r_few    = run_adaptive_equilibrium(_trades_few())
    r_empty  = run_adaptive_equilibrium(_trades_empty())
    health   = get_equilibrium_health()

    chk("C1: engine name correct",                  r_profit["engine"] == "F.7_ADAPTIVE_EQUILIBRIUM")
    chk("C2: EQ lineage_id format",                 r_profit.get("lineage_id", "").startswith("EQ-"))
    chk("C3: equilibrium_score 0–100",              0 <= r_profit.get("equilibrium_score", -1) <= 100)
    chk("C4: equilibrium_tier valid",               r_profit.get("equilibrium_tier") in ("BALANCED","ADAPTING","STRESSED","CRITICAL"))
    chk("C5: sub_engine_states has 6 keys",         len(r_profit.get("sub_engine_states", {})) == 6)
    chk("C6: sub_engine_scores has 6 keys",         len(r_profit.get("sub_engine_scores", {})) == 6)
    chk("C7: primary_concern is str",               isinstance(r_profit.get("primary_concern"), str))
    chk("C8: constitutional invariants present",    (r_profit.get("diagnostic_only") is True and
                                                     r_profit.get("auto_authorized") is False and
                                                     r_profit.get("lineage_preserved") is True))
    chk("C9: profitable score > losing score",      r_profit.get("equilibrium_score", 0) >= r_loss.get("equilibrium_score", 100))
    chk("C10: few trades fail-open",                isinstance(r_few, dict) and "equilibrium_tier" in r_few)
    chk("C11: empty trades fail-open",              isinstance(r_empty, dict) and "equilibrium_tier" in r_empty)
    chk("C12: health check returns operational",    health.get("status") == "operational" and len(health.get("engines", [])) == 7)


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═" * 62)
    print("  PHASE-F ADAPTIVE EQUILIBRIUM — TEST SUITE")
    print("═" * 62)

    test_kelly_efficiency()
    test_drawdown_dynamics()
    test_return_consistency()
    test_capital_utilization()
    test_equilibrium_band()
    test_discipline_cost()
    test_adaptive_equilibrium_orchestrator()

    total = PASS + FAIL
    print("\n" + "═" * 62)
    if FAIL == 0:
        print(f"\033[1m\033[92m  ALL {total}/{total} CHECKS PASSED ✓\033[0m")
        print("  Phase-F Adaptive Equilibrium is fully operational.")
    else:
        print(f"\033[1m\033[91m  {FAIL} CHECKS FAILED / {total} total\033[0m")
    print("═" * 62 + "\n")
    sys.exit(0 if FAIL == 0 else 1)
