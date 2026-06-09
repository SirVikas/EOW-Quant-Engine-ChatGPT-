"""Verifier: PHX-CTAO-PCCP-GAP-CLOSURE-001"""
import sys, importlib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

MODULES = [
    "core.knowledge_graph.knowledge_graph_engine",
    "core.knowledge_graph.entity_registry",
    "core.knowledge_graph.relationship_registry",
    "core.knowledge_graph.graph_query_engine",
    "core.knowledge_graph.graph_metrics",
    "core.strategic_memory.strategic_memory_engine",
    "core.strategic_memory.pattern_extractor",
    "core.strategic_memory.lesson_registry",
    "core.strategic_memory.repeat_failure_tracker",
    "core.economic_intelligence.economic_intelligence_engine",
    "core.economic_intelligence.profit_impact_analyzer",
    "core.economic_intelligence.capital_efficiency_tracker",
    "core.economic_intelligence.sharpe_impact_tracker",
    "core.ctao.recommendation_outcome_registry",
    "core.ctao.recommendation_accuracy_engine",
    "core.ctao.root_cause_validation_engine",
    "core.pccp.resource_governor",
    "core.pccp.strategic_goal_engine",
    "core.pccp.layer_dependency_engine",
    "core.pccp.health_intelligence_engine",
]

passed = 0
for mod in MODULES:
    try:
        importlib.import_module(mod)
        print(f"  OK  {mod}")
        passed += 1
    except Exception as e:
        print(f"  FAIL {mod}: {e}")

print(f"\n{passed}/{len(MODULES)} modules verified")
sys.exit(0 if passed == len(MODULES) else 1)
