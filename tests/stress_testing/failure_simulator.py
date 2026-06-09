"""Simulates catastrophic failure scenarios."""
import time

def simulate_trust_collapse():
    """Drive all trust scores to 0 and verify system still responds."""
    from core.trust_fabric.trust_registry import trust_registry
    # Register a bunch of items with zero trust
    for i in range(10):
        trust_registry.set_trust(f"collapse_test_{i}", "RECOMMENDATION", 0.0, 0)
    summary = trust_registry.trust_summary()
    return {"scenario": "TRUST_COLLAPSE", "status": "SURVIVED", "summary": summary}

def simulate_evidence_flood():
    """Flood the evidence warehouse and verify stability."""
    from core.evidence_warehouse.evidence_warehouse import evidence_warehouse
    for i in range(500):
        evidence_warehouse.deposit("VALIDATION", f"flood_{i}", "FLOOD_TEST", {"flood_index": i})
    report = evidence_warehouse.warehouse_report()
    return {"scenario": "EVIDENCE_FLOOD", "status": "SURVIVED", "warehouse_total": report.get("registry_stats", {}).get("total", 0)}

def simulate_layer_failure():
    """Simulate TRUST_ENGINE failure and check dependency impact."""
    from core.pccp.layer_dependency_engine import layer_dependency_engine
    from core.pccp.layer_registry import layer_registry
    layer_registry.update_health("TRUST_ENGINE", "CRITICAL", "Simulated failure")
    impact = layer_dependency_engine.impact_of_failure("TRUST_ENGINE")
    layer_registry.update_health("TRUST_ENGINE", "HEALTHY", "Recovered")
    return {"scenario": "LAYER_FAILURE", "status": "SURVIVED", "impact": impact.get("severity"), "affected": len(impact.get("directly_affected", []))}
