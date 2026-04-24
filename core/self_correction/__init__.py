"""
FTD-029 — Self-Correction Engine (Closed-Loop Intelligence)

aFTD (locked design answers):
  Q1  Scope:      A+C+D  — strategy params, signal tuning, portfolio allocation
                           (B risk hard-limits are FROZEN — see HARD_LIMITS)
  Q2  Autonomy:   B      — semi-auto (≤5% → auto; 5–15% → validation cycle; >15% → blocked)
  Q3  Change limit: C    — dynamic, bounded by confidence score
  Q4  Validation: C      — both FTD-027 AND FTD-028 must PASS before apply
  Q5  Rollback:   D      — all triggers: perf-drop + risk-violation + validation-fail
  Q6  Frequency:  D      — only after validation cycle; ≤3 cycles/session; 4 h cooldown
  Q7  Authority:  C      — combined AI Brain + MetaScoreEngine (both ≥ 70)
  Q8  Override:   C      — Risk Engine veto + human override both mandatory
  Q9  Target:     D      — multi-objective (Sharpe + win-rate + DD + consistency)
  Q10 Failure:    D      — all: stop auto-correction + safe-mode + alert
  Q11 Logging:    A      — every correction: what/why/before/after/result
  Q12 Export:     A      — corrections appear in session export report
  Q13 Dashboard:  D      — enable/disable + view last changes + manual override
  Q14 Hard limits — MAX_DRAWDOWN_HALT, MAX_LEVERAGE_CAP, KILL_SWITCH_THRESHOLD,
                    MIN_EQUITY_FLOOR, MAX_TRADES_PER_DAY  (never auto-changed)
  Q15 Start:      C      — ≥30 trades AND FTD-028 system_score ≥ 70
"""
from core.self_correction.correction_proposal import CorrectionProposal, HARD_LIMITS
from core.self_correction.correction_audit    import CorrectionAudit
from core.self_correction.rollback_engine     import RollbackEngine
from core.self_correction.correction_engine   import SelfCorrectionEngine, self_correction_engine

__all__ = [
    "CorrectionProposal",
    "CorrectionAudit",
    "RollbackEngine",
    "SelfCorrectionEngine",
    "self_correction_engine",
    "HARD_LIMITS",
]
