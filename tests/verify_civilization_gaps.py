"""Verifier — confirms all 40 v1.79.0 civilization-scale modules are importable."""
import importlib.util
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Modules inside core.institutional_memory must be loaded from file directly
# because the package __init__.py imports imraf_engine which requires pydantic_settings
# (a runtime dep not available in bare Python). All other packages have empty __init__.py.
DIRECT_FILE_MODULES = {
    "core.institutional_memory.institutional_memory_engine",
    "core.institutional_memory.long_term_lesson_archive",
    "core.institutional_memory.memory_consolidation_engine",
    "core.institutional_memory.institutional_wisdom_registry",
}


def _load_module(dotted: str):
    if dotted in DIRECT_FILE_MODULES:
        path = os.path.join(ROOT, dotted.replace(".", os.sep) + ".py")
        spec = importlib.util.spec_from_file_location(dotted, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    else:
        importlib.import_module(dotted)


MODULES = [
    # Institutional Memory (4)
    "core.institutional_memory.institutional_memory_engine",
    "core.institutional_memory.long_term_lesson_archive",
    "core.institutional_memory.memory_consolidation_engine",
    "core.institutional_memory.institutional_wisdom_registry",
    # Meta Knowledge (4)
    "core.meta_knowledge.meta_knowledge_engine",
    "core.meta_knowledge.knowledge_decay_engine",
    "core.meta_knowledge.knowledge_importance_tracker",
    "core.meta_knowledge.knowledge_value_ranker",
    # Evolution Planning (4)
    "core.evolution_planning.evolution_planner",
    "core.evolution_planning.capability_progress_tracker",
    "core.evolution_planning.future_architecture_engine",
    "core.evolution_planning.roadmap_registry",
    # Collective Intelligence (4)
    "core.collective_intelligence.collective_intelligence_engine",
    "core.collective_intelligence.consensus_quality_tracker",
    "core.collective_intelligence.group_reasoning_engine",
    "core.collective_intelligence.institutional_brain",
    # Capability Governance (4)
    "core.capability_governance.capability_lifecycle_engine",
    "core.capability_governance.capability_registry",
    "core.capability_governance.capability_maturity_tracker",
    "core.capability_governance.capability_retirement_engine",
    # Digital DNA (4)
    "core.digital_dna.digital_dna_engine",
    "core.digital_dna.identity_registry",
    "core.digital_dna.doctrine_registry",
    "core.digital_dna.architectural_genome",
    # Knowledge Synthesis (4)
    "core.knowledge_synthesis.knowledge_synthesis_engine",
    "core.knowledge_synthesis.insight_generator",
    "core.knowledge_synthesis.cross_domain_reasoner",
    "core.knowledge_synthesis.pattern_fusion_engine",
    # War Gaming (4)
    "core.war_gaming.war_game_engine",
    "core.war_gaming.stress_outcome_predictor",
    "core.war_gaming.scenario_battlefield",
    "core.war_gaming.strategy_competition_engine",
    # Ecosystem Intelligence (4)
    "core.ecosystem_intelligence.ecosystem_mapper",
    "core.ecosystem_intelligence.external_dependency_tracker",
    "core.ecosystem_intelligence.environmental_risk_engine",
    "core.ecosystem_intelligence.competitive_intelligence_engine",
    # Civilization Orchestrator (4)
    "core.civilization_orchestrator.civilization_engine",
    "core.civilization_orchestrator.master_orchestrator",
    "core.civilization_orchestrator.institutional_alignment_engine",
    "core.civilization_orchestrator.long_horizon_director",
]

passed = failed = 0
for m in MODULES:
    try:
        _load_module(m)
        print(f"  OK  {m}")
        passed += 1
    except Exception as e:
        print(f"  FAIL {m}: {e}")
        failed += 1

print(f"\n{passed}/{len(MODULES)} modules verified")
sys.exit(0 if failed == 0 else 1)
