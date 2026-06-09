"""Checks all reports for consistency — no contradictions across report types."""
import sys, time
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")
from tests.reporting_audit.report_truth_validator import validate_report

def check_all_reports():
    results = []
    report_types = ["EXECUTIVE", "GOVERNANCE", "TRUST", "EVOLUTION", "CAPITAL"]

    try:
        from core.reporting_hub.reporting_engine import reporting_engine
        all_reports = reporting_engine.generate_all_reports()
        reports_dict = all_reports.get("reports", {})
        for rtype in report_types:
            report = reports_dict.get(rtype, {})
            validation = validate_report(rtype, report)
            results.append({"report_type": rtype, "generated": report != {}, "valid": validation["PASS"], "issues": validation["issues"]})
    except Exception as e:
        for rtype in report_types:
            results.append({"report_type": rtype, "generated": False, "valid": False, "issues": [str(e)[:80]]})

    passed = sum(1 for r in results if r["valid"])
    return {
        "reports_checked": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
        "consistency_score": round(passed / max(1, len(results)) * 100, 1),
        "generated_at": time.time(),
    }

if __name__ == "__main__":
    r = check_all_reports()
    print(f"Report Consistency: {r['consistency_score']}% ({r['passed']}/{r['reports_checked']})")
    for res in r["results"]:
        icon = "✓" if res["valid"] else "✗"
        print(f"  {icon} {res['report_type']}")
    sys.exit(0 if r["failed"] == 0 else 1)
