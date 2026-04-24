"""
FTD-028 — Deep Intelligence Validation Layer (Scientific Proof Engine)

Validates system correctness, logical consistency, decision quality,
risk safety, and overall health. Runs after FTD-027.
"""
from core.deep_validation.contradiction_engine    import ContradictionEngine
from core.deep_validation.data_integrity_checker  import DataIntegrityChecker
from core.deep_validation.decision_scorer         import DecisionScorer
from core.deep_validation.risk_validator          import RiskValidator
from core.deep_validation.tuning_validator        import TuningValidator
from core.deep_validation.evolution_validator     import EvolutionValidator
from core.deep_validation.capital_validator       import CapitalValidator
from core.deep_validation.audit_validator         import AuditValidator
from core.deep_validation.alert_validator         import AlertValidator
from core.deep_validation.performance_validator   import PerformanceValidator
from core.deep_validation.failure_simulator       import FailureSimulator
from core.deep_validation.system_consistency_checker import SystemConsistencyChecker
from core.deep_validation.meta_score_engine       import MetaScoreEngine

__all__ = [
    "ContradictionEngine",
    "DataIntegrityChecker",
    "DecisionScorer",
    "RiskValidator",
    "TuningValidator",
    "EvolutionValidator",
    "CapitalValidator",
    "AuditValidator",
    "AlertValidator",
    "PerformanceValidator",
    "FailureSimulator",
    "SystemConsistencyChecker",
    "MetaScoreEngine",
]
