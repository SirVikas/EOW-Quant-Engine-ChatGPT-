"""Verifier — confirms all 44 v1.81.0 ecosystem-scale modules are importable."""
import importlib
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

MODULES = [
    # GAP-01: Knowledge Operations (5)
    "core.knowledge_operations.knowledge_lifecycle_engine",
    "core.knowledge_operations.knowledge_curator",
    "core.knowledge_operations.knowledge_promotion_engine",
    "core.knowledge_operations.knowledge_retirement_engine",
    "core.knowledge_operations.knowledge_value_monitor",
    # GAP-02: Workforce Management (5)
    "core.workforce_management.agent_hr_engine",
    "core.workforce_management.agent_performance_tracker",
    "core.workforce_management.agent_certification_engine",
    "core.workforce_management.agent_retirement_manager",
    "core.workforce_management.agent_assignment_director",
    # GAP-03: Capital Command (4)
    "core.capital_command.capital_strategy_director",
    "core.capital_command.capital_deployment_engine",
    "core.capital_command.capital_reserve_manager",
    "core.capital_command.capital_command_engine",
    # GAP-04: Risk Command (4)
    "core.risk_command.risk_radar",
    "core.risk_command.risk_escalation_center",
    "core.risk_command.risk_response_director",
    "core.risk_command.risk_command_engine",
    # GAP-05: Organization Design (4)
    "core.organization_design.organization_registry",
    "core.organization_design.role_definition_engine",
    "core.organization_design.structure_optimizer",
    "core.organization_design.organizational_evolution_engine",
    # GAP-06: Strategy Office (4)
    "core.strategy_office.initiative_registry",
    "core.strategy_office.strategy_execution_monitor",
    "core.strategy_office.strategy_alignment_tracker",
    "core.strategy_office.strategy_engine",
    # GAP-07: Resource Planning (4)
    "core.resource_planning.resource_demand_predictor",
    "core.resource_planning.capacity_planner",
    "core.resource_planning.resource_procurement_engine",
    "core.resource_planning.resource_forecaster",
    # GAP-08: Ecosystem Governance (4)
    "core.ecosystem_governance.council_engine",
    "core.ecosystem_governance.federation_policy_manager",
    "core.ecosystem_governance.cross_instance_audit",
    "core.ecosystem_governance.ecosystem_alignment_engine",
    # GAP-09: Institutional Economics (4)
    "core.institutional_economics.institutional_cost_engine",
    "core.institutional_economics.value_creation_tracker",
    "core.institutional_economics.efficiency_governor",
    "core.institutional_economics.economic_sustainability_engine",
    # GAP-10: Meta Civilization (4)
    "core.meta_civilization.supervisory_council",
    "core.meta_civilization.cross_civilization_alignment",
    "core.meta_civilization.universal_governance_framework",
    "core.meta_civilization.meta_civilization_engine",
]


def main():
    passed = 0
    failed = 0
    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"  OK   {module}")
            passed += 1
        except Exception as exc:
            print(f"  FAIL {module}  —  {exc}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed  (total {len(MODULES)})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
