"""
FTD-030B — Memory Orchestrator (Main Entry Point)

aFTD-030B Answers:
  Q1:  G  — ALL: corrections + outcomes + context + decision trace + validation + failures
  Q2:  B  — Correction-cycle record (atomic unit)
  Q3:  E  — ALL: volatility buckets + regime labels + timeframe class + instrument class
  Q4:  B  — Multi-factor tuple: (context + change + outcome)
  Q5:  D  — ALL: min 20 samples + confidence ≥70 + contexts ≥3 distinct buckets
  Q6:  D  — Hybrid: success_rate × recency × regime_bonus
  Q7:  B+C — Weighted (≤30%) + Dynamic (scales with confidence, low conf → 20%)
  Q8:  D  — ALL: FTD-027 PASS + FTD-028 score ≥70 + pattern confidence ≥60 + PolicyGuard
  Q9:  A+D — Weighted merge (0.5/0.5) + risk engine override always wins
  Q10: D  — ALL: time 0.95^age + perf ×0.7 + confidence drop threshold ≥25
  Q11: D  — ALL: min diversity ≥3 contexts + cross-regime validation + max influence cap
  Q12: A  — After each correction cycle (learn())
  Q13: A+B — Blacklist with decay (0.90^age) + confidence penalty (3 rollbacks = ban)
  Q14: A+B+C — Memory suggests → Planner validates + bounds → never bypass policy_guard
  Q15: MAX_DRAWDOWN_HALT, MAX_LEVERAGE_CAP, KILL_SWITCH_THRESHOLD, MIN_EQUITY_FLOOR, MAX_TRADES_PER_DAY
  Q16: A  — JSONL append-only
  Q17: A  — Mandatory: pattern + context match + confidence + historical success rate
  Q18: D  — ALL: top patterns + recent insights + applied memory + export section
  Q19: E  — ALL dashboard panels
  Q20: C  — BOTH: ≥50 trades AND FTD-028 score stable ≥70 over K cycles

Full loop:
  1. MemoryStore          → JSONL append-only entry store
  2. LearningUpdater      → ingest correction outcome → MemoryEntry
  3. RetentionManager     → 0.95^age time decay + ×0.7 rollback penalty + purge ≥0.25
  4. PatternDetector      → 3-tuple (instrument|param|direction) → Pattern; contexts = distinct regime×vol pairs
  5. PatternIndexer       → in-memory O(1) lookup index
  6. MemoryValidator      → 3-gate: samples≥20 + confidence≥70 + contexts≥3
  7. NegativeMemory       → rollback blacklist + permanent ban at 3 strikes
  8. MemoryApplier        → validated patterns → weighted suggestions (max 30%)
  9. MemoryGuard          → max shift 30%, no duplicates, PolicyGuard veto
  10. ExplainabilityEngine → mandatory rationale (Q17)
  11. ConflictResolver     → weighted merge + risk-engine override
"""
from __future__ import annotations
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from loguru import logger

from core.memory.memory_store          import MemoryStore
from core.memory.pattern_detector      import PatternDetector
from core.memory.pattern_indexer       import PatternIndexer
from core.memory.learning_updater      import LearningUpdater
from core.memory.retention_manager     import RetentionManager
from core.memory.memory_validator      import MemoryValidator
from core.memory.negative_memory       import NegativeMemory
from core.memory.memory_applier        import MemoryApplier
from core.memory.memory_guard          import MemoryGuard
from core.memory.explainability_engine import ExplainabilityEngine
from core.memory.conflict_resolver     import ConflictResolver


class MemoryOrchestrator:
    MODULE                 = "MEMORY_ORCHESTRATOR"
    PHASE                  = "030B"
    START_CONDITION_TRADES = 50    # Q20: ≥50 trades
    START_CONDITION_SCORE  = 70.0  # Q20: FTD-028 score ≥70

    def __init__(self):
        self._store      = MemoryStore()
        self._detector   = PatternDetector()
        self._indexer    = PatternIndexer(self._store, self._detector)
        self._updater    = LearningUpdater(self._store, self._detector)
        self._retention  = RetentionManager(self._store)
        self._validator  = MemoryValidator()
        self._neg_memory = NegativeMemory()
        self._applier    = MemoryApplier()
        self._guard      = MemoryGuard()
        self._explainer  = ExplainabilityEngine()
        self._resolver   = ConflictResolver()
        self._total_ingested = 0

    # ── Q12: learn() — after each correction cycle ────────────────────────────

    def learn(
        self,
        change_id:        str,
        parameter:        str,
        delta_pct:        float,
        direction:        str,
        value_before:     float,
        value_after:      float,
        pnl_delta:        float,
        score_delta:      float,
        rolled_back:      bool,
        rollback_trigger: Optional[str] = None,
        rationale:        str = "",
        confidence:       float = 50.0,
        market_regime:    str = "UNKNOWN",
        volatility:       float = 0.0,
        symbol:           str = "PORTFOLIO",
    ) -> Dict[str, Any]:
        entry = self._updater.ingest(
            change_id=change_id, parameter=parameter, delta_pct=delta_pct,
            direction=direction, value_before=value_before, value_after=value_after,
            pnl_delta=pnl_delta, score_delta=score_delta, rolled_back=rolled_back,
            rollback_trigger=rollback_trigger, rationale=rationale,
            confidence=confidence, market_regime=market_regime,
            volatility=volatility, symbol=symbol,
        )
        self._total_ingested += 1

        # Track negative memory on rollbacks (Q13)
        if rolled_back:
            # 3-tuple pattern_id matches PatternDetector key
            pattern_id = f"{symbol}|{parameter}|{direction}"
            self._neg_memory.record_rollback(pattern_id)

        decay_result = self._retention.apply_decay()
        self._neg_memory.apply_decay()
        patterns     = self._updater.get_patterns()
        self._indexer.rebuild()
        validation   = self._validator.validate_patterns(patterns)

        logger.info(
            f"[FTD-030B] learn({change_id}): outcome={entry.outcome_score:.2f} "
            f"total={self._store.count()} patterns={len(patterns)} "
            f"valid={len(validation['valid_patterns'])}"
        )
        return {
            "entry_id":       entry.entry_id,
            "outcome_score":  entry.outcome_score,
            "total_entries":  self._store.count(),
            "patterns":       len(patterns),
            "valid_patterns": len(validation["valid_patterns"]),
            "decay":          decay_result,
            "memory_ready":   validation["memory_ready"],
            "negative_memory": self._neg_memory.summary(),
            "ts":             entry.ts,
        }

    # ── validate() — after validation cycle (Q12-B) ──────────────────────────

    def validate(self) -> Dict[str, Any]:
        patterns   = self._updater.get_patterns()
        validation = self._validator.validate_patterns(patterns)
        return {
            "module":           self.MODULE,
            "memory_ready":     validation["memory_ready"],
            "total_samples":    validation["total_samples"],
            "valid_patterns":   validation["valid_patterns"],
            "invalid_patterns": validation["invalid_patterns"],
            "stability_counts": validation["stability_counts"],
            "negative_memory":  self._neg_memory.summary(),
            "ts":               int(time.time() * 1000),
        }

    # ── suggest() — Q8: ALL gates; Q7: dynamic influence ─────────────────────

    def suggest(
        self,
        current_params:   Dict[str, float],
        total_trades:     int = 0,
        validation_score: float = 0.0,
        regime_context:   str = "UNKNOWN",
        live_signals:     Optional[Dict[str, Any]] = None,
        risk_halted:      bool = False,
        risk_violated:    bool = False,
        policy_ok:        bool = True,
    ) -> Dict[str, Any]:
        patterns   = self._updater.get_patterns()
        validation = self._validator.validate_patterns(patterns)

        # Q20: start condition — both gates
        if not validation["memory_ready"]:
            return self._not_ready("INSUFFICIENT_MEMORY", validation, total_trades)
        if total_trades < self.START_CONDITION_TRADES:
            return self._not_ready("INSUFFICIENT_TRADES", validation, total_trades)
        if validation_score < self.START_CONDITION_SCORE:
            return self._not_ready("VALIDATION_SCORE_LOW", validation, total_trades)

        # Filter out blacklisted patterns (Q13)
        safe_patterns = {
            pid: p for pid, p in patterns.items()
            if not self._neg_memory.is_banned(pid)
        }

        raw       = self._applier.suggest(safe_patterns, current_params, regime_context, total_trades)
        explained = self._explainer.explain_all(raw)
        allowed, blocked = self._guard.validate(explained, policy_ok=policy_ok)
        resolved  = self._resolver.resolve(allowed, live_signals or {}, risk_halted, risk_violated)

        logger.info(
            f"[FTD-030B] suggest(): {len(resolved)} resolved "
            f"(raw={len(raw)} guard_blocked={len(blocked)})"
        )
        return {
            "module":           self.MODULE,
            "phase":            self.PHASE,
            "suggestions":      resolved,
            "suggestion_count": len(resolved),
            "guard_blocked":    blocked,
            "memory_ready":     True,
            "valid_patterns":   validation["valid_patterns"],
            "total_entries":    self._store.count(),
            "ts":               int(time.time() * 1000),
        }

    # ── Dashboard (Q18-D ALL, Q19-E ALL) ─────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        patterns   = self._updater.get_patterns()
        validation = self._validator.validate_patterns(patterns)
        successes  = {pid: p for pid, p in patterns.items() if p.avg_outcome_score > 0.2}
        failures   = {pid: p for pid, p in patterns.items() if p.avg_outcome_score <= -0.2}
        top_n      = self._indexer.top_n(5)
        return {
            "module":          self.MODULE,
            "phase":           self.PHASE,
            "total_entries":   self._store.count(),
            "total_ingested":  self._total_ingested,
            "memory_ready":    validation["memory_ready"],
            "valid_patterns":  validation["valid_patterns"],
            "patterns": {
                pid: {
                    "sample_count":   p.sample_count,
                    "success_count":  p.success_count,
                    "failure_count":  p.failure_count,
                    "confidence":     p.confidence,
                    "validated":      p.validated,
                    "avg_outcome":    p.avg_outcome_score,
                    "context_count":  p.context_count,
                }
                for pid, p in patterns.items()
            },
            "success_patterns":   list(successes.keys()),
            "failure_patterns":   list(failures.keys()),
            "top_patterns":       [p.pattern_id for p in top_n],
            "retention":          self._retention.summary(),
            "negative_memory":    self._neg_memory.summary(),
            "index":              self._indexer.summary(),
            "guard":              self._guard.summary(),
            "start_condition":    f"≥{self.START_CONDITION_TRADES} trades AND memory_ready",
            "snapshot_ts":        int(time.time() * 1000),
        }

    # ── Export (Q17, Q18) ────────────────────────────────────────────────────

    def logs(self, n: int = 50) -> List[Dict[str, Any]]:
        return [asdict(e) for e in self._store.recent(n)]

    def patterns(self) -> Dict[str, Any]:
        return {
            pid: {
                "pattern_id":   p.pattern_id,
                "regime":       p.regime,
                "volatility":   p.volatility,
                "instrument":   p.instrument,
                "parameter":    p.parameter,
                "direction":    p.direction,
                "sample_count": p.sample_count,
                "success_count": p.success_count,
                "failure_count": p.failure_count,
                "avg_outcome":  p.avg_outcome_score,
                "confidence":   p.confidence,
                "validated":    p.validated,
                "context_count": p.context_count,
                "banned":       self._neg_memory.is_banned(pid),
            }
            for pid, p in self._updater.get_patterns().items()
        }

    def negative_memory_summary(self) -> Dict[str, Any]:
        return self._neg_memory.summary()

    # ── Reset ────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        self._store.clear()
        self._validator.reset_all()
        self._neg_memory.__init__()
        self._guard.reset_session()
        self._indexer.rebuild()
        self._total_ingested = 0
        logger.warning("[FTD-030B] Memory RESET — all entries, patterns, negative memory cleared")

    # ── Internal ─────────────────────────────────────────────────────────────

    def _not_ready(
        self,
        reason:     str,
        validation: Dict[str, Any],
        trades:     int,
    ) -> Dict[str, Any]:
        return {
            "module":        self.MODULE,
            "phase":         self.PHASE,
            "suggestions":   [],
            "memory_ready":  validation["memory_ready"],
            "reason":        reason,
            "total_entries": self._store.count(),
            "total_trades":  trades,
            "ts":            int(time.time() * 1000),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
memory_orchestrator = MemoryOrchestrator()
