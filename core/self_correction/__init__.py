"""
FTD-029 — Self-Correction Engine (Closed-Loop Intelligence)

Full architecture (11 modules):
  correction_orchestrator  → main entry point (Detect→Decide→Plan→Apply→Validate→Keep/Rollback)
  issue_extractor          → Part 1: parse FTD-027 + FTD-028 into actionable issues
  confidence_engine        → Part 2: composite confidence (0.4*Meta+0.3*Decision+0.2*Stability+0.1*Consistency)
  policy_guard             → Part 3: all gate conditions (Q4, Q7, Q8, Q14, Q15)
  priority_resolver        → Part 4a: sort by locked priority (risk-safety first)
  collision_handler        → Part 4b: conflict resolution + queue management
  change_planner           → Part 5: bounded change plans with rationale + impact
  change_applier           → Part 6: delegation to existing owners, session overlay
  cooldown_manager         → Part 7: ≤3/session, 4h cooldown, critical bypass
  rollback_manager         → Part 8: re-validate after apply, KEEP/ROLLBACK decision
  audit_logger             → Part 9: immutable append-only audit trail (Q11)

aFTD locked design answers: Q1–Q15 (see correction_orchestrator.py docstring)
"""
from core.self_correction.correction_orchestrator import CorrectionOrchestrator, correction_orchestrator
from core.self_correction.issue_extractor         import IssueExtractor, Issue, IssueType, IssueSeverity
from core.self_correction.confidence_engine       import ConfidenceEngine
from core.self_correction.policy_guard            import PolicyGuard
from core.self_correction.cooldown_manager        import CooldownManager
from core.self_correction.priority_resolver       import PriorityResolver
from core.self_correction.change_planner          import ChangePlanner, ChangePlan
from core.self_correction.collision_handler       import CollisionHandler
from core.self_correction.change_applier          import ChangeApplier, AppliedChange
from core.self_correction.rollback_manager        import RollbackManager, RollbackTrigger
from core.self_correction.audit_logger            import AuditLogger, FinalState
from core.self_correction.correction_proposal     import HARD_LIMITS, TUNABLE_PARAMS
# Legacy engine kept for backward compatibility with existing tests + singleton
from core.self_correction.correction_engine       import SelfCorrectionEngine, self_correction_engine

__all__ = [
    "CorrectionOrchestrator", "correction_orchestrator",
    "IssueExtractor", "Issue", "IssueType", "IssueSeverity",
    "ConfidenceEngine",
    "PolicyGuard",
    "CooldownManager",
    "PriorityResolver",
    "ChangePlanner", "ChangePlan",
    "CollisionHandler",
    "ChangeApplier", "AppliedChange",
    "RollbackManager", "RollbackTrigger",
    "AuditLogger", "FinalState",
    "HARD_LIMITS", "TUNABLE_PARAMS",
    "SelfCorrectionEngine", "self_correction_engine",
]
