"""Verifier: FTD PHX-AEI-PROGRAM-001"""
import sys, importlib, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

MODULES = [
    "core.digital_twin.digital_twin_engine",
    "core.digital_twin.scenario_simulator",
    "core.digital_twin.recommendation_sandbox",
    "core.digital_twin.impact_predictor",
    "core.digital_twin.deployment_validator",
    "core.evolution_governance.evolution_registry",
    "core.evolution_governance.evolution_proposal_engine",
    "core.evolution_governance.evolution_review_engine",
    "core.evolution_governance.evolution_approval_engine",
    "core.evolution_governance.evolution_rollback_engine",
    "core.pcao.pcao_engine",
    "core.pcao.priority_director",
    "core.pcao.resource_allocator",
    "core.pcao.executive_dashboard",
    "core.meta_governance.pccp_audit_engine",
    "core.meta_governance.compliance_engine",
    "core.meta_governance.governance_validator",
    "core.meta_governance.control_plane_monitor",
    "core.constitution.constitution_engine",
    "core.constitution.article_registry",
    "core.constitution.constitutional_validator",
    "core.constitution.change_history",
    "core.epistemic.epistemic_engine",
    "core.epistemic.evidence_tracker",
    "core.epistemic.uncertainty_registry",
    "core.epistemic.confidence_boundary_engine",
    "core.trust_fabric.trust_fabric_engine",
    "core.trust_fabric.trust_registry",
    "core.trust_fabric.trust_propagation_engine",
    "core.trust_fabric.trust_decay_engine",
    "core.autonomous_improvement.improvement_engine",
    "core.autonomous_improvement.policy_update_engine",
    "core.autonomous_improvement.behavior_update_engine",
    "core.autonomous_improvement.feedback_loop_engine",
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
