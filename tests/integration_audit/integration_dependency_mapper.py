"""Maps all cross-module dependencies across PHOENIX institutional layers."""
import importlib, time

INTEGRATION_PAIRS = [
    ("core.knowledge_graph.knowledge_graph_engine", "core.strategic_memory.strategic_memory_engine"),
    ("core.strategic_memory.strategic_memory_engine", "core.trust_fabric.trust_fabric_engine"),
    ("core.trust_fabric.trust_fabric_engine", "core.economic_intelligence.economic_intelligence_engine"),
    ("core.economic_intelligence.economic_intelligence_engine", "core.pcao.pcao_engine"),
    ("core.pcao.pcao_engine", "core.board_governance.board_engine"),
    ("core.board_governance.board_engine", "core.human_governance.human_governance_engine"),
    ("core.digital_twin.digital_twin_engine", "core.evolution_governance.evolution_registry"),
    ("core.ctao.ctao_orchestrator", "core.pccp.pccp_orchestrator"),
    ("core.evidence_warehouse.evidence_warehouse", "core.reporting_hub.reporting_engine"),
    ("core.lineage.snapshot_engine", "core.evidence_warehouse.evidence_warehouse"),
]

def map_dependencies():
    results = []
    for mod_a, mod_b in INTEGRATION_PAIRS:
        a_ok = _can_import(mod_a)
        b_ok = _can_import(mod_b)
        results.append({
            "layer_a": mod_a.split(".")[-1],
            "layer_b": mod_b.split(".")[-1],
            "layer_a_status": "OK" if a_ok else "FAIL",
            "layer_b_status": "OK" if b_ok else "FAIL",
            "integration_viable": a_ok and b_ok,
        })
    viable = sum(1 for r in results if r["integration_viable"])
    return {
        "total_pairs": len(results),
        "viable": viable,
        "broken": len(results) - viable,
        "pairs": results,
        "generated_at": time.time(),
    }

def _can_import(module_path):
    try:
        importlib.import_module(module_path)
        return True
    except Exception:
        return False
