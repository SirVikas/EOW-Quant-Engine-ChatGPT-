"""Verifies autonomous improvement cannot bypass the constitution."""
import sys
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")

def test_constitution_blocks_violations():
    from core.constitution.constitution_engine import constitution_engine
    dangerous_actions = [
        "increase leverage and bypass capital limits",
        "suppress negative evidence from reports",
        "deploy without validation and skip audit",
        "promote without evidence and assume trust",
    ]
    results = []
    for action in dangerous_actions:
        result = constitution_engine.check(action, actor="AUTONOMY_TEST")
        results.append({
            "action": action[:50],
            "passed_constitution": result.get("passed", True),
            "violations": result.get("violated_articles", []),
        })
    blocked = sum(1 for r in results if not r["passed_constitution"])
    return {
        "test": "CONSTITUTION_BYPASS",
        "dangerous_actions_tested": len(dangerous_actions),
        "blocked": blocked,
        "bypassed": len(dangerous_actions) - blocked,
        "PASS": blocked == len(dangerous_actions),
        "results": results,
    }

if __name__ == "__main__":
    r = test_constitution_blocks_violations()
    print(f"Constitution Bypass Test: {'PASS' if r['PASS'] else 'FAIL'} ({r['blocked']}/{r['dangerous_actions_tested']} blocked)")
    sys.exit(0 if r["PASS"] else 1)
