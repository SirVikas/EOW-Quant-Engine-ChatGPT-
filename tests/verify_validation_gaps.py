"""Verify all 32 validation-era gap modules (v1.82.0) can be imported successfully."""
import importlib
import sys
import pathlib

# Ensure project root is on sys.path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

MODULES = [
    "core.strategy_truth.alpha_source_tracker",
    "core.strategy_truth.signal_truth_validator",
    "core.strategy_truth.edge_decay_monitor",
    "core.strategy_truth.strategy_truth_engine",
    "core.live_market_lab.expectation_gap_tracker",
    "core.live_market_lab.market_reaction_analyzer",
    "core.live_market_lab.behavior_validation_engine",
    "core.live_market_lab.live_behavior_engine",
    "core.alpha_attribution.profit_source_mapper",
    "core.alpha_attribution.edge_contribution_tracker",
    "core.alpha_attribution.performance_decomposition",
    "core.alpha_attribution.alpha_attribution_engine",
    "core.long_horizon_validation.survivability_tracker",
    "core.long_horizon_validation.stability_monitor",
    "core.long_horizon_validation.performance_persistence_engine",
    "core.long_horizon_validation.validation_engine",
    "core.regime_survivability.regime_scorecard",
    "core.regime_survivability.transition_resilience_tracker",
    "core.regime_survivability.crisis_response_validator",
    "core.regime_survivability.regime_survival_engine",
    "core.operations_center.runtime_monitor",
    "core.operations_center.incident_center",
    "core.operations_center.operations_scoreboard",
    "core.operations_center.operations_engine",
    "core.benchmarking.peer_comparison_tracker",
    "core.benchmarking.performance_ranker",
    "core.benchmarking.improvement_gap_detector",
    "core.benchmarking.benchmark_engine",
    "core.economic_proof.roi_validation_engine",
    "core.economic_proof.capital_efficiency_validator",
    "core.economic_proof.economic_claim_auditor",
    "core.economic_proof.economic_proof_engine",
]

passed = 0
failed = 0

for module_name in MODULES:
    try:
        importlib.import_module(module_name)
        print(f"  OK  {module_name}")
        passed += 1
    except Exception as e:
        print(f"FAIL  {module_name}: {e}")
        failed += 1

print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed out of {len(MODULES)} modules")

if failed > 0:
    sys.exit(1)

print("All validation-era gap modules imported successfully.")
sys.exit(0)
