"""Generates synthetic load for stress testing PHOENIX institutional layers."""
import time

def generate_findings(n=1000):
    from core.ctao.finding_registry import finding_registry
    import random
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    categories = ["RISK", "SIGNAL", "GOVERNANCE", "TRUST", "MONITORING"]
    ids = []
    for i in range(n):
        fid = finding_registry.record_finding(
            random.choice(categories), random.choice(severities),
            round(random.uniform(0.5, 1.0), 2), "STRESS_TEST",
            f"Stress test finding {i}"
        )
        ids.append(fid)
    return ids

def generate_graph_relationships(n=1000):
    from core.knowledge_graph.entity_registry import entity_registry
    from core.knowledge_graph.relationship_registry import relationship_registry
    import random
    rel_types = ["CAUSED_BY", "LED_TO", "RESOLVED_BY", "IMPACTS", "DEPENDS_ON"]
    entity_ids = []
    for i in range(min(n // 2, 500)):
        eid = entity_registry.register("FINDING", f"stress_entity_{i}", {"index": i})
        entity_ids.append(eid)
    rel_count = 0
    for i in range(min(n, len(entity_ids) - 1)):
        relationship_registry.create(entity_ids[i], entity_ids[(i+1) % len(entity_ids)], random.choice(rel_types))
        rel_count += 1
    return rel_count

def generate_regime_changes(n=100):
    from core.regime_intelligence.regime_engine import regime_engine
    regimes = ["BULL", "BEAR", "SIDEWAYS", "VOLATILE", "CRISIS"]
    import random
    for i in range(n):
        regime_engine.update_regime(random.choice(regimes), trigger=f"stress_{i}")
    return n

def generate_evidence(n=1000):
    from core.evidence_warehouse.evidence_warehouse import evidence_warehouse
    import random
    types = ["TRUST", "ECONOMIC", "SIMULATION", "RECOMMENDATION", "VALIDATION"]
    for i in range(n):
        evidence_warehouse.deposit(random.choice(types), f"stress_subj_{i % 100}", "STRESS_TEST", {"value": i}, quality=0.5)
    return n
