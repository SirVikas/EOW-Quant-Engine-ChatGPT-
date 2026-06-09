"""Orchestrates full stress test suite."""
import sys, time
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")

def run_stress_tests(findings=200, relationships=500, regime_changes=50, evidence=500):
    results = []
    ts = time.time()

    from tests.stress_testing.load_generator import generate_findings, generate_graph_relationships, generate_regime_changes, generate_evidence
    from tests.stress_testing.failure_simulator import simulate_trust_collapse, simulate_evidence_flood, simulate_layer_failure

    for label, fn, args in [
        (f"Generate {findings} findings", generate_findings, [findings]),
        (f"Generate {relationships} graph relationships", generate_graph_relationships, [relationships]),
        (f"Generate {regime_changes} regime changes", generate_regime_changes, [regime_changes]),
        (f"Generate {evidence} evidence items", generate_evidence, [evidence]),
        ("Simulate trust collapse", simulate_trust_collapse, []),
        ("Simulate evidence flood", simulate_evidence_flood, []),
        ("Simulate layer failure", simulate_layer_failure, []),
    ]:
        t0 = time.time()
        try:
            result = fn(*args)
            elapsed = round(time.time() - t0, 3)
            results.append({"test": label, "status": "PASS", "elapsed_s": elapsed, "detail": str(result)[:80]})
        except Exception as e:
            results.append({"test": label, "status": "FAIL", "error": str(e)[:100]})

    passed = sum(1 for r in results if r["status"] == "PASS")
    return {
        "stress_tests_total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
        "total_duration_s": round(time.time() - ts, 2),
        "architectural_collapse": False,
    }

if __name__ == "__main__":
    report = run_stress_tests()
    print(f"Stress Tests: {report['passed']}/{report['stress_tests_total']} passed")
    for r in report["results"]:
        icon = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {icon} {r['test']}")
    sys.exit(0 if report["failed"] == 0 else 1)
