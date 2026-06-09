"""Verifier: FTD PHX-INSTITUTIONAL-FINAL-GAP-CLOSURE-001"""
import sys, importlib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

MODULES = [
    "core.real_market_validation.validation_engine",
    "core.real_market_validation.outcome_tracker",
    "core.real_market_validation.expectation_vs_reality",
    "core.real_market_validation.market_evidence_registry",
    "core.evidence_warehouse.evidence_warehouse",
    "core.evidence_warehouse.evidence_registry",
    "core.evidence_warehouse.evidence_query_engine",
    "core.evidence_warehouse.evidence_lineage",
    "core.performance_attribution.performance_attribution_engine",
    "core.performance_attribution.signal_contribution_analyzer",
    "core.performance_attribution.risk_contribution_analyzer",
    "core.performance_attribution.regime_contribution_analyzer",
    "core.regime_intelligence.regime_engine",
    "core.regime_intelligence.regime_classifier",
    "core.regime_intelligence.regime_history",
    "core.regime_intelligence.regime_transition_tracker",
    "core.board_governance.board_engine",
    "core.board_governance.board_review_engine",
    "core.board_governance.board_decision_registry",
    "core.board_governance.executive_oversight_engine",
    "core.reporting_hub.reporting_engine",
    "core.reporting_hub.executive_report_builder",
    "core.reporting_hub.governance_report_builder",
    "core.reporting_hub.trust_report_builder",
    "core.reporting_hub.evolution_report_builder",
    "core.reporting_hub.capital_report_builder",
    "core.lineage.snapshot_engine",
    "core.lineage.lineage_registry",
    "core.lineage.timeline_reconstruction_engine",
    "core.lineage.historical_state_engine",
    "core.human_governance.human_governance_engine",
    "core.human_governance.approval_registry",
    "core.human_governance.emergency_override_engine",
    "core.human_governance.rollback_authority",
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
