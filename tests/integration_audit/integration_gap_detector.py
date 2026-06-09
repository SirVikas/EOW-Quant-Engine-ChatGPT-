"""Detects integration gaps — modules that exist but have no cross-layer wiring."""
import importlib, time

# All major singletons and the cross-layer calls they SHOULD be able to make
INTEGRATION_CHECKS = [
    {
        "name": "KG → Strategic Memory pattern extraction",
        "module": "core.strategic_memory.pattern_extractor",
        "method": "run_full_extraction",
        "args": [],
    },
    {
        "name": "PCCP → Layer Registry health",
        "module": "core.pccp.layer_registry",
        "method": "system_health_summary",
        "args": [],
    },
    {
        "name": "Constitution Engine check",
        "module": "core.constitution.constitution_engine",
        "method": "constitution_report",
        "args": [],
    },
    {
        "name": "Evidence Warehouse harvest",
        "module": "core.evidence_warehouse.evidence_warehouse",
        "method": "auto_harvest",
        "args": [],
    },
    {
        "name": "Trust Fabric unified report",
        "module": "core.trust_fabric.trust_fabric_engine",
        "method": "unified_trust_report",
        "args": [],
    },
    {
        "name": "Reporting Hub — all reports",
        "module": "core.reporting_hub.reporting_engine",
        "method": "generate_all_reports",
        "args": [],
    },
    {
        "name": "PCAO executive briefing",
        "module": "core.pcao.pcao_engine",
        "method": "executive_briefing",
        "args": [],
    },
    {
        "name": "Epistemic audit",
        "module": "core.epistemic.epistemic_engine",
        "method": "epistemic_audit",
        "args": [],
    },
    {
        "name": "Improvement engine status",
        "module": "core.autonomous_improvement.improvement_engine",
        "method": "improvement_status",
        "args": [],
    },
    {
        "name": "Human governance dashboard",
        "module": "core.human_governance.human_governance_engine",
        "method": "governance_dashboard",
        "args": [],
    },
]

def detect_gaps():
    results = []
    for check in INTEGRATION_CHECKS:
        try:
            mod = importlib.import_module(check["module"])
            # find singleton (last name component)
            singleton_name = check["module"].split(".")[-1]
            obj = getattr(mod, singleton_name, None)
            if obj is None:
                # try common variations
                for attr in dir(mod):
                    if not attr.startswith("_") and hasattr(getattr(mod, attr), check["method"]):
                        obj = getattr(mod, attr)
                        break
            if obj and hasattr(obj, check["method"]):
                result = getattr(obj, check["method"])(*check["args"])
                results.append({"check": check["name"], "status": "PASS", "result_type": type(result).__name__})
            else:
                results.append({"check": check["name"], "status": "WARN", "reason": "Singleton or method not found"})
        except Exception as e:
            results.append({"check": check["name"], "status": "FAIL", "error": str(e)[:100]})
    passed = sum(1 for r in results if r["status"] == "PASS")
    return {
        "total_checks": len(results),
        "passed": passed,
        "warned": sum(1 for r in results if r["status"] == "WARN"),
        "failed": sum(1 for r in results if r["status"] == "FAIL"),
        "results": results,
        "integration_health_pct": round(passed / len(results) * 100, 1),
        "generated_at": time.time(),
    }
