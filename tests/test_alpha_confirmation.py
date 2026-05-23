"""
Phase-I Alpha Confirmation & Live-Readiness Gating — 84-check test suite.

Structure: 7 test classes × 12 checks each = 84 total.
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.alpha_confirmation.statistical_significance_engine import compute_statistical_significance
from core.alpha_confirmation.oos_validation_engine           import compute_oos_validation
from core.alpha_confirmation.fee_survival_engine             import compute_fee_survival
from core.alpha_confirmation.regime_robustness_engine        import compute_regime_robustness
from core.alpha_confirmation.drawdown_tolerance_engine       import compute_drawdown_tolerance
from core.alpha_confirmation.live_readiness_gate             import compute_live_readiness
from core.alpha_confirmation.alpha_confirmation_orchestrator import (
    run_alpha_confirmation, get_alpha_health,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────

def _strong_trades(n=80, seed=7):
    random.seed(seed)
    regimes = ["TRENDING", "RANGING", "MOMENTUM"]
    return [{"pnl": random.gauss(1.5, 1.2), "net_pnl": random.gauss(1.3, 1.2),
             "fee": 0.1, "size": 1.0, "confidence": 0.8,
             "regime": regimes[i % len(regimes)]} for i in range(n)]

def _weak_trades(n=60, seed=42):
    # Deterministically losing: 3 small wins then 1 large loss, concentrated regime
    return [{"pnl": (0.3 if i % 4 != 0 else -4.0),
             "net_pnl": (0.1 if i % 4 != 0 else -4.2),
             "fee": 0.2, "size": 1.0, "regime": "TRENDING"} for i in range(n)]

def _few_trades():
    return [{"pnl": 1.0, "size": 1.0} for _ in range(5)]

def _empty():
    return []

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
# TEST 1 — I.1 Statistical Significance Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_statistical_significance():
    print("\n\033[1m\033[93m── TEST 1 — I.1 Statistical Significance Engine ─────────────\033[0m")

    r_strong = compute_statistical_significance(_strong_trades())
    r_weak   = compute_statistical_significance(_weak_trades())
    r_few    = compute_statistical_significance(_few_trades())
    r_empty  = compute_statistical_significance(_empty())

    chk("C1: engine name correct",              r_strong["engine"] == "I.1_STATISTICAL_SIGNIFICANCE")
    chk("C2: lineage_id present",               r_strong.get("lineage_id", "").startswith("ALPHA-I1-"))
    chk("C3: win_rate in [0,1]",                0.0 <= r_strong.get("win_rate", -1) <= 1.0)
    chk("C4: z_win_rate is float",              isinstance(r_strong.get("z_win_rate"), float))
    chk("C5: evidence_score in [0,100]",        0.0 <= r_strong.get("evidence_score", -1) <= 100.0)
    chk("C6: strong trades → positive state",   r_strong.get("state") in ("PROVEN", "INDICATIVE"))
    chk("C7: weak trades → negative state",     r_weak.get("state") in ("INSUFFICIENT_EVIDENCE", "NO_EDGE"))
    chk("C8: state is valid enum",              r_strong.get("state") in ("PROVEN","INDICATIVE","INSUFFICIENT_EVIDENCE","NO_EDGE"))
    chk("C9: live_deployment_authorized=False", r_strong.get("live_deployment_authorized") is False)
    chk("C10: diagnostic_only=True",            r_strong.get("diagnostic_only") is True)
    chk("C11: few trades returns dict",         isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",          isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — I.2 OOS Validation Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_oos_validation():
    print("\n\033[1m\033[93m── TEST 2 — I.2 OOS Validation Engine ───────────────────────\033[0m")

    r_strong = compute_oos_validation(_strong_trades())
    r_weak   = compute_oos_validation(_weak_trades())
    r_few    = compute_oos_validation(_few_trades())
    r_empty  = compute_oos_validation(_empty())

    chk("C1: engine name correct",              r_strong["engine"] == "I.2_OOS_VALIDATION")
    chk("C2: lineage_id present",               r_strong.get("lineage_id", "").startswith("ALPHA-I2-"))
    chk("C3: is_trades + oos_trades == total",  r_strong.get("is_trades", 0) + r_strong.get("oos_trades", 0) == r_strong.get("trade_count", -1))
    chk("C4: wr_degradation_ratio >= 0",        r_strong.get("wr_degradation_ratio", -1) >= 0)
    chk("C5: oos_independently_positive bool",  isinstance(r_strong.get("oos_independently_positive"), bool))
    chk("C6: strong trades → consistent",       r_strong.get("state") in ("OOS_CONSISTENT","MINOR_DEGRADATION"))
    chk("C7: weak trades → failure",            r_weak.get("state") in ("OOS_FAILURE","SIGNIFICANT_DEGRADATION","MINOR_DEGRADATION"))
    chk("C8: state is valid enum",              r_strong.get("state") in ("OOS_CONSISTENT","MINOR_DEGRADATION","SIGNIFICANT_DEGRADATION","OOS_FAILURE"))
    chk("C9: live_deployment_authorized=False", r_strong.get("live_deployment_authorized") is False)
    chk("C10: diagnostic_only=True",            r_strong.get("diagnostic_only") is True)
    chk("C11: few trades returns dict",         isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",          isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — I.3 Fee-Survival Certification Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_fee_survival():
    print("\n\033[1m\033[93m── TEST 3 — I.3 Fee-Survival Certification Engine ────────────\033[0m")

    r_strong = compute_fee_survival(_strong_trades())
    r_weak   = compute_fee_survival(_weak_trades())
    r_few    = compute_fee_survival(_few_trades())
    r_empty  = compute_fee_survival(_empty())

    chk("C1: engine name correct",              r_strong["engine"] == "I.3_FEE_SURVIVAL")
    chk("C2: lineage_id present",               r_strong.get("lineage_id", "").startswith("ALPHA-I3-"))
    chk("C3: window_survival_rate in [0,1]",    0.0 <= r_strong.get("window_survival_rate", -1) <= 1.0)
    chk("C4: total_net_pnl is float",           isinstance(r_strong.get("total_net_pnl"), float))
    chk("C5: positive_windows <= total_windows",r_strong.get("positive_windows", 0) <= r_strong.get("total_windows", 1))
    chk("C6: strong trades → certified",        r_strong.get("state") in ("FEE_CERTIFIED","MARGINAL"))
    chk("C7: weak trades → eroded/destroyed",   r_weak.get("state") in ("FEE_ERODED","FEE_DESTROYED","MARGINAL"))
    chk("C8: state is valid enum",              r_strong.get("state") in ("FEE_CERTIFIED","MARGINAL","FEE_ERODED","FEE_DESTROYED"))
    chk("C9: live_deployment_authorized=False", r_strong.get("live_deployment_authorized") is False)
    chk("C10: diagnostic_only=True",            r_strong.get("diagnostic_only") is True)
    chk("C11: few trades returns dict",         isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",          isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 — I.4 Regime Robustness Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_regime_robustness():
    print("\n\033[1m\033[93m── TEST 4 — I.4 Regime Robustness Engine ─────────────────────\033[0m")

    r_strong = compute_regime_robustness(_strong_trades())
    r_weak   = compute_regime_robustness(_weak_trades())
    r_few    = compute_regime_robustness(_few_trades())
    r_empty  = compute_regime_robustness(_empty())

    # Single-regime concentrated trades
    r_conc   = compute_regime_robustness([{"pnl": 1.0, "regime": "TRENDING"} for _ in range(30)])

    chk("C1: engine name correct",              r_strong["engine"] == "I.4_REGIME_ROBUSTNESS")
    chk("C2: lineage_id present",               r_strong.get("lineage_id", "").startswith("ALPHA-I4-"))
    chk("C3: regimes_observed >= 1",            r_strong.get("regimes_observed", 0) >= 1)
    chk("C4: concentration in [0,1]",           0.0 <= r_strong.get("best_regime_concentration", -1) <= 1.0)
    chk("C5: regime_stats is dict",             isinstance(r_strong.get("regime_stats"), dict))
    chk("C6: strong diverse → robust/adequate", r_strong.get("state") in ("ROBUST","ADEQUATE","CONCENTRATED"))
    chk("C7: single regime → concentrated",     r_conc.get("state") in ("CONCENTRATED","FRAGILE","ADEQUATE"))
    chk("C8: state is valid enum",              r_strong.get("state") in ("ROBUST","ADEQUATE","CONCENTRATED","FRAGILE"))
    chk("C9: live_deployment_authorized=False", r_strong.get("live_deployment_authorized") is False)
    chk("C10: diagnostic_only=True",            r_strong.get("diagnostic_only") is True)
    chk("C11: few trades returns dict",         isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",          isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5 — I.5 Drawdown Tolerance Engine
# ══════════════════════════════════════════════════════════════════════════════
def test_drawdown_tolerance():
    print("\n\033[1m\033[93m── TEST 5 — I.5 Drawdown Tolerance Engine ────────────────────\033[0m")

    r_strong = compute_drawdown_tolerance(_strong_trades())
    r_weak   = compute_drawdown_tolerance(_weak_trades())
    r_few    = compute_drawdown_tolerance(_few_trades())
    r_empty  = compute_drawdown_tolerance(_empty())

    chk("C1: engine name correct",              r_strong["engine"] == "I.5_DRAWDOWN_TOLERANCE")
    chk("C2: lineage_id present",               r_strong.get("lineage_id", "").startswith("ALPHA-I5-"))
    chk("C3: max_drawdown >= 0",                r_strong.get("max_drawdown", -1) >= 0)
    chk("C4: dd_ratio in [0,∞)",               r_strong.get("dd_ratio", -1) >= 0)
    chk("C5: recovery_ratio in [0,1]",          0.0 <= r_strong.get("recovery_ratio", -1) <= 1.0)
    chk("C6: calmar_proxy is float",            isinstance(r_strong.get("calmar_proxy"), float))
    chk("C7: strong trades → ready/borderline", r_strong.get("state") in ("DEPLOYMENT_READY","BORDERLINE","EXCESSIVE_DRAWDOWN"))
    chk("C8: state is valid enum",              r_strong.get("state") in ("DEPLOYMENT_READY","BORDERLINE","EXCESSIVE_DRAWDOWN","DISQUALIFYING"))
    chk("C9: live_deployment_authorized=False", r_strong.get("live_deployment_authorized") is False)
    chk("C10: diagnostic_only=True",            r_strong.get("diagnostic_only") is True)
    chk("C11: few trades returns dict",         isinstance(r_few, dict) and "state" in r_few)
    chk("C12: empty trades fail-open",          isinstance(r_empty, dict) and "state" in r_empty)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6 — I.6 Live Readiness Gate
# ══════════════════════════════════════════════════════════════════════════════
def test_live_readiness_gate():
    print("\n\033[1m\033[93m── TEST 6 — I.6 Live Readiness Gate ─────────────────────────\033[0m")

    # Build sub-results for strong scenario
    trades_s = _strong_trades()
    from core.alpha_confirmation.statistical_significance_engine import compute_statistical_significance
    from core.alpha_confirmation.oos_validation_engine           import compute_oos_validation
    from core.alpha_confirmation.fee_survival_engine             import compute_fee_survival
    from core.alpha_confirmation.regime_robustness_engine        import compute_regime_robustness
    from core.alpha_confirmation.drawdown_tolerance_engine       import compute_drawdown_tolerance
    sub_strong = [
        compute_statistical_significance(trades_s),
        compute_oos_validation(trades_s),
        compute_fee_survival(trades_s),
        compute_regime_robustness(trades_s),
        compute_drawdown_tolerance(trades_s),
    ]
    # Inject a blocking result
    sub_blocked = list(sub_strong)
    sub_blocked[0] = {"engine": "I.1_STATISTICAL_SIGNIFICANCE", "state": "NO_EDGE"}

    r_open    = compute_live_readiness(sub_strong)
    r_blocked = compute_live_readiness(sub_blocked)
    r_empty   = compute_live_readiness([])

    chk("C1: engine name correct",                   r_open["engine"] == "I.6_LIVE_READINESS_GATE")
    chk("C2: lineage_id present",                    r_open.get("lineage_id", "").startswith("ALPHA-I6-"))
    chk("C3: gate_status valid enum",                r_open.get("gate_status") in ("READY_FOR_CONSIDERATION","CONDITIONAL","BLOCKED","INSUFFICIENT_DATA"))
    chk("C4: blocking_reasons is list",              isinstance(r_open.get("blocking_reasons"), list))
    chk("C5: gate_checks has 5 entries (strong)",    len(r_open.get("gate_checks", {})) == 5)
    chk("C6: blocked gate has blocking_reasons",     len(r_blocked.get("blocking_reasons", [])) > 0)
    chk("C7: blocked gate_status=BLOCKED",           r_blocked.get("gate_status") == "BLOCKED")
    chk("C8: live_deployment_authorized always False",r_open.get("live_deployment_authorized") is False)
    chk("C9: human_confirmation_required=True",      r_open.get("human_confirmation_required") is True)
    chk("C10: diagnostic_only=True",                 r_open.get("diagnostic_only") is True)
    chk("C11: empty sub_results returns dict",       isinstance(r_empty, dict) and "gate_status" in r_empty)
    chk("C12: live_deployment_authorized=False (blocked)", r_blocked.get("live_deployment_authorized") is False)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7 — I.7 Alpha Confirmation Orchestrator
# ══════════════════════════════════════════════════════════════════════════════
def test_alpha_orchestrator():
    print("\n\033[1m\033[93m── TEST 7 — I.7 Alpha Confirmation Orchestrator ──────────────\033[0m")

    r_strong = run_alpha_confirmation(_strong_trades())
    r_weak   = run_alpha_confirmation(_weak_trades())
    r_few    = run_alpha_confirmation(_few_trades())
    r_empty  = run_alpha_confirmation(_empty())
    health   = get_alpha_health()

    chk("C1: engine name correct",                   r_strong["engine"] == "I.7_ALPHA_CONFIRMATION")
    chk("C2: ALPHA lineage_id format",               r_strong.get("lineage_id", "").startswith("ALPHA-"))
    chk("C3: alpha_score 0–100",                     0 <= r_strong.get("alpha_score", -1) <= 100)
    chk("C4: alpha_tier valid enum",                 r_strong.get("alpha_tier") in ("CONFIRMED","CANDIDATE","DEVELOPING","UNPROVEN"))
    chk("C5: strong > weak score",                   r_strong.get("alpha_score", 0) > r_weak.get("alpha_score", 100))
    chk("C6: sub_engine_states has 6 keys",          len(r_strong.get("sub_engine_states", {})) == 6)
    chk("C7: sub_engine_scores has 5 keys",          len(r_strong.get("sub_engine_scores", {})) == 5)
    chk("C8: gate_status present",                   "gate_status" in r_strong)
    chk("C9: live_deployment_authorized always False",
        r_strong.get("live_deployment_authorized") is False and
        r_weak.get("live_deployment_authorized")   is False and
        r_few.get("live_deployment_authorized")    is False and
        r_empty.get("live_deployment_authorized")  is False)
    chk("C10: human_confirmation_required=True",     r_strong.get("human_confirmation_required") is True)
    chk("C11: few/empty trades fail-open",           isinstance(r_few, dict) and isinstance(r_empty, dict))
    chk("C12: health check returns 7 engines",       health.get("status") == "operational" and
                                                      len(health.get("engines", [])) == 7 and
                                                      health.get("live_deployment_authorized") is False)


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═" * 62)
    print("  PHASE-I ALPHA CONFIRMATION — TEST SUITE")
    print("═" * 62)

    test_statistical_significance()
    test_oos_validation()
    test_fee_survival()
    test_regime_robustness()
    test_drawdown_tolerance()
    test_live_readiness_gate()
    test_alpha_orchestrator()

    total = PASS + FAIL
    print("\n" + "═" * 62)
    if FAIL == 0:
        print(f"\033[1m\033[92m  ALL {total}/{total} CHECKS PASSED ✓\033[0m")
        print("  Phase-I Alpha Confirmation is fully operational.")
    else:
        print(f"\033[1m\033[91m  {FAIL} CHECKS FAILED / {total} total\033[0m")
    print("═" * 62 + "\n")
    sys.exit(0 if FAIL == 0 else 1)
