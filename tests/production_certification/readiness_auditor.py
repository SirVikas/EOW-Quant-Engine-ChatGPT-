"""Audits each certification domain for production readiness."""
import sys, importlib, time
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")

CERTIFICATION_DOMAINS = [
    {
        "domain": "GOVERNANCE",
        "check": lambda: __import__("core.constitution.constitution_engine", fromlist=["constitution_engine"]).constitution_engine.constitution_report(),
        "min_score_key": "constitutional_health_score",
        "min_score": 0.5,
    },
    {
        "domain": "CONSTITUTION",
        "check": lambda: __import__("core.constitution.article_registry", fromlist=["article_registry"]).article_registry.all_articles(),
        "validator": lambda r: len(r) >= 8,
    },
    {
        "domain": "TRUST",
        "check": lambda: __import__("core.trust_fabric.trust_registry", fromlist=["trust_registry"]).trust_registry.trust_summary(),
        "validator": lambda r: isinstance(r, dict),
    },
    {
        "domain": "EVOLUTION_GOVERNANCE",
        "check": lambda: __import__("core.evolution_governance.evolution_registry", fromlist=["evolution_registry"]).evolution_registry.evolution_stats(),
        "validator": lambda r: isinstance(r, dict),
    },
    {
        "domain": "ECONOMIC_INTELLIGENCE",
        "check": lambda: __import__("core.economic_intelligence.economic_intelligence_engine", fromlist=["economic_intelligence_engine"]).economic_intelligence_engine.economic_report(),
        "validator": lambda r: isinstance(r, dict),
    },
    {
        "domain": "REPORTING",
        "check": lambda: __import__("core.reporting_hub.reporting_engine", fromlist=["reporting_engine"]).reporting_engine.generate_all_reports(),
        "validator": lambda r: "reports" in r,
    },
    {
        "domain": "LINEAGE",
        "check": lambda: __import__("core.lineage.snapshot_engine", fromlist=["snapshot_engine"]).snapshot_engine.snapshot_stats(),
        "validator": lambda r: isinstance(r, dict),
    },
    {
        "domain": "HUMAN_OVERSIGHT",
        "check": lambda: __import__("core.human_governance.human_governance_engine", fromlist=["human_governance_engine"]).human_governance_engine.human_governance_status(),
        "validator": lambda r: isinstance(r, dict),
    },
    {
        "domain": "DISASTER_RECOVERY",
        "check": lambda: __import__("core.disaster_recovery.failover_manager", fromlist=["failover_manager"]).failover_manager.disaster_recovery_status(),
        "validator": lambda r: isinstance(r, dict),
    },
    {
        "domain": "AUDITABILITY",
        "check": lambda: __import__("core.lineage.lineage_registry", fromlist=["lineage_registry"]).lineage_registry.lineage_stats(),
        "validator": lambda r: isinstance(r, dict),
    },
]

def audit_all_domains():
    results = []
    for domain in CERTIFICATION_DOMAINS:
        try:
            result = domain["check"]()
            if "validator" in domain:
                passed = domain["validator"](result)
            elif "min_score_key" in domain:
                passed = result.get(domain["min_score_key"], 0) >= domain["min_score"]
            else:
                passed = result is not None
            results.append({"domain": domain["domain"], "PASS": passed, "operational": True})
        except Exception as e:
            results.append({"domain": domain["domain"], "PASS": False, "operational": False, "error": str(e)[:80]})
    return results
