"""Verifier — confirms all 43 v1.80.0 enterprise-scale modules are importable."""
import importlib
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

MODULES = [
    # GAP-01: Data Governance (5)
    "core.data_governance.data_catalog",
    "core.data_governance.data_lineage_engine",
    "core.data_governance.data_quality_monitor",
    "core.data_governance.data_retention_engine",
    "core.data_governance.data_classification_registry",
    # GAP-02: Model Governance (5)
    "core.model_governance.model_registry",
    "core.model_governance.model_validation_engine",
    "core.model_governance.model_version_control",
    "core.model_governance.model_promotion_workflow",
    "core.model_governance.model_retirement_engine",
    # GAP-03: Decision Intelligence (4)
    "core.decision_intelligence.decision_registry",
    "core.decision_intelligence.decision_quality_engine",
    "core.decision_intelligence.decision_regret_tracker",
    "core.decision_intelligence.decision_accuracy_tracker",
    # GAP-04: Workflow Orchestration (4)
    "core.workflow_orchestration.workflow_registry",
    "core.workflow_orchestration.workflow_dependency_manager",
    "core.workflow_orchestration.workflow_monitor",
    "core.workflow_orchestration.workflow_engine",
    # GAP-05: Resource Economics (4)
    "core.resource_economics.resource_cost_engine",
    "core.resource_economics.resource_roi_tracker",
    "core.resource_economics.resource_efficiency_analyzer",
    "core.resource_economics.optimization_recommender",
    # GAP-06: Change Management (4)
    "core.change_management.change_registry",
    "core.change_management.change_approval_board",
    "core.change_management.change_risk_engine",
    "core.change_management.change_impact_assessor",
    # GAP-07: Service Governance (4)
    "core.service_governance.sla_registry",
    "core.service_governance.slo_tracker",
    "core.service_governance.availability_monitor",
    "core.service_governance.service_quality_engine",
    # GAP-08: Dependency Governance (4)
    "core.dependency_governance.vendor_registry",
    "core.dependency_governance.dependency_risk_engine",
    "core.dependency_governance.external_service_monitor",
    "core.dependency_governance.dependency_audit_engine",
    # GAP-09: Executive Management (4)
    "core.executive_management.okr_registry",
    "core.executive_management.goal_tracker",
    "core.executive_management.strategic_kpi_engine",
    "core.executive_management.executive_performance_dashboard",
    # GAP-10: Federation (4)
    "core.federation.federation_registry",
    "core.federation.inter_phoenix_protocol",
    "core.federation.knowledge_exchange_engine",
    "core.federation.federated_governance",
]

passed = failed = 0
for m in MODULES:
    try:
        importlib.import_module(m)
        print(f"  OK  {m}")
        passed += 1
    except Exception as e:
        print(f"  FAIL {m}: {e}")
        failed += 1

print(f"\n{passed}/{len(MODULES)} modules verified")
sys.exit(0 if failed == 0 else 1)
