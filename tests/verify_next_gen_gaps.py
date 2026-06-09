"""Verifier: POST-v1.77.0 Next-Gen Gap Closure"""
import sys, importlib
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")

MODULES = [
    "core.observability_platform.observability_engine",
    "core.observability_platform.real_time_metrics_bus",
    "core.observability_platform.cross_layer_telemetry",
    "core.observability_platform.anomaly_center",
    "core.observability_platform.institutional_observability_dashboard",
    "core.portfolio_intelligence.portfolio_engine",
    "core.portfolio_intelligence.portfolio_risk_mapper",
    "core.portfolio_intelligence.capital_allocator",
    "core.portfolio_intelligence.exposure_analyzer",
    "core.causal_intelligence.causal_engine",
    "core.causal_intelligence.counterfactual_engine",
    "core.causal_intelligence.causal_validator",
    "core.causal_intelligence.intervention_tracker",
    "core.research_lab.research_report_builder",
    "core.research_lab.experiment_registry",
    "core.research_lab.hypothesis_engine",
    "core.research_lab.research_tracker",
    "core.agent_fabric.agent_coordinator",
    "core.agent_fabric.agent_registry",
    "core.agent_fabric.agent_consensus_engine",
    "core.agent_fabric.agent_conflict_resolver",
    "core.forecasting.forecast_engine",
    "core.forecasting.future_risk_mapper",
    "core.forecasting.scenario_projection",
    "core.forecasting.strategic_outlook_builder",
    "core.self_diagnostics.failure_reconstruction_engine",
    "core.self_diagnostics.incident_analyzer",
    "core.self_diagnostics.auto_postmortem_generator",
    "core.self_diagnostics.remediation_tracker",
    "core.policy_governance.policy_registry",
    "core.policy_governance.policy_enforcement_engine",
    "core.policy_governance.policy_versioning",
    "core.policy_governance.policy_approval_workflow",
    "core.institutional_scorecard.continuous_score_engine",
    "core.institutional_scorecard.institutional_kpi_tracker",
    "core.institutional_scorecard.trend_analyzer",
    "core.institutional_scorecard.degradation_detector",
    "core.command_center.command_center_engine",
    "core.command_center.alert_center",
    "core.command_center.mission_control",
    "core.command_center.executive_console",
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
