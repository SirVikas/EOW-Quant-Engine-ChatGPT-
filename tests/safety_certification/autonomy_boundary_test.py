"""Verifies PCAO cannot override the constitutional hierarchy."""
import sys
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")

def test_autonomy_boundaries():
    results = []

    # Test 1: PCAO posture is bounded (can't be UNDEFINED)
    try:
        from core.pcao.pcao_engine import pcao_engine
        posture = pcao_engine.strategic_posture()
        results.append({"check": "PCAO_POSTURE_BOUNDED", "PASS": posture in ("OFFENSIVE", "DEFENSIVE", "NEUTRAL"), "posture": posture})
    except Exception as e:
        results.append({"check": "PCAO_POSTURE_BOUNDED", "PASS": False, "error": str(e)[:60]})

    # Test 2: Strategic goal tier 1 (Capital Preservation) is highest priority
    try:
        from core.pccp.strategic_goal_engine import strategic_goal_engine
        hier = strategic_goal_engine.goal_hierarchy_report()
        goals = hier.get("goals", {})
        cap_pres = goals.get("CAPITAL_PRESERVATION", {})
        results.append({"check": "CAPITAL_PRESERVATION_TIER_1", "PASS": cap_pres.get("tier") == 1, "tier": cap_pres.get("tier")})
    except Exception as e:
        results.append({"check": "CAPITAL_PRESERVATION_TIER_1", "PASS": False, "error": str(e)[:60]})

    # Test 3: Human governance can override autonomous decisions
    try:
        from core.human_governance.emergency_override_engine import emergency_override_engine
        oid = emergency_override_engine.issue_override("STOP", "SAFETY_TEST", "TEST_TARGET", "autonomy boundary test")
        active = emergency_override_engine.active_overrides()
        found = any(o.get("override_id") == oid for o in active)
        emergency_override_engine.revoke(oid, "SAFETY_TEST")
        results.append({"check": "HUMAN_OVERRIDE_WORKS", "PASS": found})
    except Exception as e:
        results.append({"check": "HUMAN_OVERRIDE_WORKS", "PASS": False, "error": str(e)[:60]})

    passed = sum(1 for r in results if r["PASS"])
    return {"test": "AUTONOMY_BOUNDARY", "PASS": passed == len(results), "checks": results, "passed": passed, "total": len(results)}

if __name__ == "__main__":
    r = test_autonomy_boundaries()
    print(f"Autonomy Boundary Test: {'PASS' if r['PASS'] else 'FAIL'} ({r['passed']}/{r['total']})")
    sys.exit(0 if r["PASS"] else 1)
