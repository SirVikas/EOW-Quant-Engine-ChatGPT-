"""
FTD-030B — Learning Memory Orchestrator (Main Entry Point)

Wires all 9 sub-modules into a coherent self-learning layer.
Two primary integration hooks into FTD-029:

  1. enhance_change_plans(plans, context, ftd028_meta_score, ftd027_passed)
       → Called inside run_cycle(), before change_applier.apply()
       → Returns memory-blended plans + explainability log

  2. after_resolve_cycle(cycle_id, applied_changes, rollbacks, context, meta_score, ai_mode)
       → Called inside resolve_cycle() after rollback decisions
       → Writes to memory store, updates pattern index, runs forgetting pass
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from loguru import logger

from config import cfg
from core.learning_memory.memory_store          import MemoryStore
from core.learning_memory.pattern_engine        import PatternEngine
from core.learning_memory.confidence_updater    import ConfidenceUpdater
from core.learning_memory.memory_applier        import MemoryApplier
from core.learning_memory.forgetting_engine     import ForgettingEngine
from core.learning_memory.negative_memory       import NegativeMemory
from core.learning_memory.memory_guard          import MemoryGuard
from core.learning_memory.pattern_indexer       import PatternIndexer
from core.learning_memory.explainability_engine import ExplainabilityEngine


class LearningMemoryOrchestrator:
    """
    FTD-030B singleton. All external callers use `learning_memory_orchestrator`.
    """

    MODULE = "LEARNING_MEMORY"
    PHASE  = "030B"

    def __init__(self):
        self._store       = MemoryStore()
        self._engine      = PatternEngine()
        self._updater     = ConfidenceUpdater()
        self._applier     = MemoryApplier()
        self._forgetter   = ForgettingEngine()
        self._neg_memory  = NegativeMemory()
        self._indexer     = PatternIndexer(self._store, self._engine)
        self._explain     = ExplainabilityEngine()

        self._enabled:       bool = True
        self._last_prune_ts: float = 0.0
        self._cycle_count:   int  = 0

        # Bootstrap pattern index from persisted store
        try:
            loaded = self._indexer.build_from_store()
            if loaded:
                logger.info(f"[FTD-030B] Bootstrapped {loaded} memory records, "
                            f"{self._indexer.formed_count()} patterns formed")
        except Exception as exc:
            logger.warning(f"[FTD-030B] Bootstrap failed (non-fatal): {exc}")

    # ── Hook 1: Memory-influenced change planning ─────────────────────────────

    def enhance_change_plans(
        self,
        plans: List[Dict[str, Any]],
        context: Dict[str, Any],
        ftd028_meta_score: float = 0.0,
        ftd027_passed: bool = True,
    ) -> Dict[str, Any]:
        """
        Blend memory patterns into FTD-029 change plans.
        Safe to call even if no patterns exist — returns original plans unchanged.

        Args:
            plans:             list of plan dicts from ChangePlanner
            context:           {regime, volatility, instrument, timeframe}
            ftd028_meta_score: system score from MetaScoreEngine
            ftd027_passed:     True if FTD-027 decision intelligence passed

        Returns:
            {
              "plans":      enhanced or original plans list,
              "memory_log": list of explainability entries,
              "applied":    int count of memory hints applied,
            }
        """
        if not self._enabled or not plans:
            return {"plans": plans, "memory_log": [], "applied": 0}

        self._applier.reset_cycle()

        enhanced, memory_log = self._applier.enhance_plans(
            plans,
            context,
            self._engine,
            self._neg_memory,
            ftd028_meta_score,
            ftd027_passed,
        )

        applied = sum(1 for p in enhanced if p.get("memory_hint"))
        if applied:
            logger.info(f"[FTD-030B] Memory applied to {applied}/{len(plans)} plans")

        return {"plans": enhanced, "memory_log": memory_log, "applied": applied}

    # ── Hook 2: Post-cycle memory update ─────────────────────────────────────

    def after_resolve_cycle(
        self,
        cycle_id: str,
        applied_changes: List[Dict[str, Any]],
        rollbacks: List[Dict[str, Any]],
        context: Dict[str, Any],
        pre_meta_score: float,
        post_meta_score: float,
        ai_mode: str = "AUTO",
        contradiction: bool = False,
    ) -> Dict[str, Any]:
        """
        Called after FTD-029 resolve_cycle(). Stores outcomes and updates patterns.

        Args:
            cycle_id:         FTD-029 cycle identifier
            applied_changes:  list of {change_id, parameter, before, after, delta_pct}
            rollbacks:        list of rollback dicts from resolve_cycle
            context:          {regime, volatility, instrument, timeframe}
            pre_meta_score:   FTD-028 score before corrections
            post_meta_score:  FTD-028 score after corrections
            ai_mode:          e.g. "AUTO", "MANUAL", "MEMORY"
            contradiction:    True if FTD-028 contradiction flag active

        Returns:
            summary dict
        """
        if not self._enabled:
            return {"stored": 0, "patterns_updated": 0}

        # FTD-031C: config_snapshot logging at learning cycle start
        logger.info(
            f"[FTD-030B] learning_cycle config_snapshot | "
            f"cycle_id={cycle_id} ts={int(time.time() * 1000)} "
            f"KELLY_FRACTION={cfg.KELLY_FRACTION} "
            f"MAX_DRAWDOWN_HALT={cfg.MAX_DRAWDOWN_HALT} "
            f"CORRECTION_CONF_HIGH={cfg.CORRECTION_CONF_HIGH} "
            f"CORRECTION_CONF_MED={cfg.CORRECTION_CONF_MED} "
            f"P7B_PERF_WIN_THRESHOLD={cfg.P7B_PERF_WIN_THRESHOLD} "
            f"ADAPTIVE_LR={cfg.ADAPTIVE_LR}"
        )

        self._cycle_count += 1
        rollback_params = {r.get("parameter", r.get("change_id", "")) for r in rollbacks}
        score_delta     = post_meta_score - pre_meta_score

        stored = 0
        for change in applied_changes:
            param     = change.get("parameter", "")
            before    = change.get("before", 0.0)
            after     = change.get("after", 0.0)
            direction = "UP" if after > before else "DOWN"
            did_rollback = param in rollback_params

            record = MemoryStore.build_record(
                cycle_id     = cycle_id,
                regime       = context.get("regime", "UNKNOWN"),
                volatility   = context.get("volatility", "MEDIUM"),
                timeframe    = context.get("timeframe", "1m"),
                instrument   = context.get("instrument", "UNKNOWN"),
                parameter    = param,
                direction    = direction,
                score_delta  = score_delta,
                rollback     = did_rollback,
                meta_score   = post_meta_score,
                contradiction= contradiction,
                ai_mode      = ai_mode,
                rationale    = change.get("rationale", ""),
            )

            if self._store.append(record):
                stored += 1
                pat = self._engine.ingest(record)

                if pat:
                    self._updater.update(pat, self._cycle_count)

                    if did_rollback:
                        key = self._engine._make_key(record)
                        if key:
                            self._neg_memory.record_rollback(key)
                            self._forgetter.apply_rollback_penalty(pat)
                            logger.warning(
                                f"[FTD-030B] Rollback penalty + negative memory: {param}"
                            )

        # Advance negative memory decay
        self._neg_memory.advance_cycle()

        # Periodic forgetting pass (every 10 cycles)
        pruned: List[str] = []
        if self._cycle_count % 10 == 0:
            pruned = self._forgetter.run(self._engine, self._cycle_count)
            if pruned:
                logger.info(f"[FTD-030B] Forgot {len(pruned)} low-confidence patterns")

        # Refresh index
        try:
            self._indexer._save_index()
        except Exception:
            pass

        formed = self._indexer.formed_count()
        logger.info(
            f"[FTD-030B] Cycle {cycle_id}: stored={stored}, "
            f"patterns_formed={formed}, pruned={len(pruned)}"
        )

        return {
            "cycle_id":        cycle_id,
            "stored":          stored,
            "patterns_formed": formed,
            "pruned":          len(pruned),
            "rollbacks_logged": len(rollback_params & {c.get("parameter", "") for c in applied_changes}),
        }

    # ── Dashboard / status ────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        formed    = self._engine.formed_patterns()
        all_pats  = self._engine.all_patterns()
        top5      = sorted(formed, key=lambda p: p.confidence, reverse=True)[:5]

        return {
            "module":              self.MODULE,
            "phase":               self.PHASE,
            "enabled":             self._enabled,
            "total_records":       self._store.count(),
            "total_patterns":      len(all_pats),
            "formed_patterns":     len(formed),
            "negative_memory":     self._neg_memory.count(),
            "cycle_count":         self._cycle_count,
            "top_patterns":        [p.to_dict() for p in top5],
            "snapshot_ts":         int(time.time() * 1000),
        }

    def pattern_leaderboard(self, n: int = 10) -> List[Dict[str, Any]]:
        formed = self._engine.formed_patterns()
        return [
            p.to_dict()
            for p in sorted(formed, key=lambda p: p.confidence, reverse=True)[:n]
        ]

    def failed_patterns(self, n: int = 10) -> List[Dict[str, Any]]:
        all_pats = self._engine.all_patterns()
        failed   = sorted(all_pats, key=lambda p: p.confidence)[:n]
        return [p.to_dict() for p in failed]

    def recent_memory_log(self, n: int = 20) -> List[Dict[str, Any]]:
        return self._store.recent(n)

    def negative_memory_list(self) -> List[Dict[str, Any]]:
        return self._neg_memory.to_list()

    def enable(self)  -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False


# ── Singleton ─────────────────────────────────────────────────────────────────
learning_memory_orchestrator = LearningMemoryOrchestrator()
