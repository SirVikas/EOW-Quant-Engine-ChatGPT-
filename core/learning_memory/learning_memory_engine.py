"""
FTD-030B — learning_memory_engine.py
Main coordinator: wires all 9 learning memory modules.

Lifecycle:
  startup  → load MemoryStore → PatternIndexer.build_from_records()
  per cycle → update(cycle_record)   [called from auto_intelligence_engine after resolve_cycle]
  on apply  → suggest(context)       [called from change_planner when FTD-029 fires]
  on forget → run_forgetting_cycle() [called each FTD-030 tick]

Activation gate (Q20):
  ≥ 50 trades  AND  FTD-028 score ≥ 70 over K=3 consecutive stable cycles
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Dict, List, Optional

from loguru import logger

from core.learning_memory.memory_store         import MemoryStore, MemoryRecord
from core.learning_memory.pattern_engine       import PatternEngine
from core.learning_memory.confidence_updater   import compute_confidence
from core.learning_memory.memory_applier       import MemoryApplier, ApplyResult
from core.learning_memory.forgetting_engine    import ForgettingEngine
from core.learning_memory.negative_memory      import NegativeMemory
from core.learning_memory.memory_guard         import MemoryGuard
from core.learning_memory.pattern_indexer      import PatternIndexer
from core.learning_memory.explainability_engine import ExplainabilityEngine

REPORT_PATH = pathlib.Path("reports/learning_memory/last_memory_report.md")

# Activation gates (Q20)
ACTIVATION_MIN_TRADES  = 50
ACTIVATION_MIN_SCORE   = 70.0
ACTIVATION_STABLE_K    = 3    # consecutive cycles above min score


class LearningMemoryEngine:
    """
    FTD-030B main entry point.
    Singleton — one instance per process.
    """

    MODULE = "LEARNING_MEMORY_ENGINE"
    PHASE  = "030B"

    def __init__(self):
        self._store     = MemoryStore()
        self._engine    = PatternEngine()
        self._forgetter = ForgettingEngine()
        self._neg       = NegativeMemory()
        self._guard     = MemoryGuard()
        self._explainer = ExplainabilityEngine()
        self._applier   = MemoryApplier(self._guard, self._explainer, self._neg)
        self._indexer   = PatternIndexer(self._engine)

        # Activation state
        self._active:          bool  = False
        self._stable_cycles:   int   = 0
        self._total_updates:   int   = 0
        self._total_applied:   int   = 0

        # Boot: rebuild pattern index from persisted records
        loaded = self._indexer.build_from_records(self._store.all_records())
        logger.info(
            f"[FTD-030B] LearningMemoryEngine boot: "
            f"records={self._store.count()} valid_patterns={loaded}"
        )

    # ── Activation gate ───────────────────────────────────────────────────────

    def check_activation(self, n_trades: int, meta_score: float) -> bool:
        """
        Update activation status based on current system state.
        Learning activates only when BOTH gates are met (Q20).
        """
        if meta_score >= ACTIVATION_MIN_SCORE:
            self._stable_cycles += 1
        else:
            self._stable_cycles = 0   # reset on any dip below threshold

        prev = self._active
        self._active = (
            n_trades >= ACTIVATION_MIN_TRADES and
            self._stable_cycles >= ACTIVATION_STABLE_K
        )

        if self._active and not prev:
            logger.info(
                f"[FTD-030B] Learning ACTIVATED: "
                f"trades={n_trades} stable_cycles={self._stable_cycles}"
            )
        elif not self._active and prev:
            logger.info(f"[FTD-030B] Learning DEACTIVATED (gates not met)")

        return self._active

    # ── Main update (called after FTD-029 resolve_cycle) ─────────────────────

    def update(
        self,
        cycle_id:       str,
        applied_changes: List[Dict[str, Any]],
        rollbacks:      List[Dict[str, Any]],
        meta_score:     float,
        contradiction:  bool,
        ai_mode:        str,
        regime:         str,
        volatility_pct: float,
        score_delta:    float = 0.0,
    ) -> Dict[str, Any]:
        """
        Ingest a completed correction cycle into learning memory.
        Must be called after resolve_cycle() from auto_intelligence_engine.
        """
        if not self._active:
            return {"action": "SKIPPED", "reason": "LEARNING_NOT_ACTIVATED"}

        rollback_params = {r.get("parameter") for r in rollbacks if r.get("parameter")}
        records_added   = 0

        # Build one MemoryRecord per applied change
        for ch in applied_changes:
            param     = ch.get("parameter", "")
            direction = "DOWN" if (ch.get("after", 0) < ch.get("before", 0)) else "UP"
            did_rollback = param in rollback_params

            record = MemoryRecord.build(
                cycle_id=cycle_id,
                regime=regime,
                volatility_pct=volatility_pct,
                parameter=param,
                direction=direction,
                score_delta=score_delta,
                rollback=did_rollback,
                meta_score=meta_score,
                contradiction=contradiction,
                ai_mode=ai_mode,
            )

            if self._store.add(record):
                records_added += 1
                pat = self._engine.update(record, confidence_fn=compute_confidence)

                # Handle rollbacks: penalise + blacklist
                if did_rollback and pat:
                    old_conf, new_conf = self._forgetter.apply_rollback_penalty(
                        self._engine, pat.pattern_id
                    )
                    self._neg.record_rollback(pat.pattern_id)
                    # Release in-flight guard
                    self._applier.release_inflight(param)
                    logger.warning(
                        f"[FTD-030B] Rollback recorded for pattern={pat.pattern_id} "
                        f"conf {old_conf:.1f}→{new_conf:.1f} "
                        f"rollbacks={self._neg._entries.get(pat.pattern_id, object).__class__}"
                    )

        # Run forgetting cycle (decay all patterns)
        forget_result = self._forgetter.run_cycle(self._engine)

        # Decay negative memory blacklist entries
        self._neg.decay_cycle()

        # Flush updated pattern index
        self._indexer.flush_index()

        self._total_updates += 1

        # Write markdown report
        self._write_report()

        return {
            "records_added":    records_added,
            "valid_patterns":   len(self._engine.valid_patterns()),
            "decayed":          len(forget_result["decayed"]),
            "removed":          len(forget_result["removed"]),
            "blacklisted":      self._neg.blacklisted_count(),
            "ts":               int(time.time() * 1000),
        }

    # ── Suggestion (called from ChangePlanner) ────────────────────────────────

    def suggest(
        self,
        parameter:      str,
        direction:      str,
        live_suggest:   float,
        current_value:  float,
        meta_score:     float,
        ftd027_passed:  bool,
        regime:         str,
        volatility_pct: float,
        current_params: Optional[Dict[str, float]] = None,
    ) -> ApplyResult:
        """
        Look up best matching pattern and return a blended suggestion.
        Returns ApplyResult(applied=False) if no valid pattern found or gate fails.
        """
        if not self._active:
            from core.learning_memory.memory_applier import ApplyResult
            return ApplyResult(False, parameter, live_suggest, 0.0, "LEARNING_NOT_ACTIVATED")

        vol_bucket = (
            "LOW"  if volatility_pct < 0.1 else
            "HIGH" if volatility_pct > 0.3 else "MED"
        )
        pattern = self._indexer.lookup(
            regime=regime,
            volatility=vol_bucket,
            instrument="CRYPTO",
            parameter=parameter,
            direction=direction.upper(),
        )

        if pattern is None or not pattern.is_valid:
            from core.learning_memory.memory_applier import ApplyResult
            return ApplyResult(False, parameter, live_suggest, 0.0, "NO_VALID_PATTERN")

        # Compute memory suggestion: apply historical average delta
        historical_delta = (
            (pattern.success / pattern.samples) *
            (current_value * 0.05)   # conservative 5% base shift, scaled by success rate
        )
        direction_sign  = 1 if direction.upper() == "UP" else -1
        memory_suggest  = current_value + (direction_sign * historical_delta)

        result = self._applier.apply(
            pattern=pattern,
            memory_suggest=memory_suggest,
            live_suggest=live_suggest,
            current_value=current_value,
            meta_score=meta_score,
            ftd027_passed=ftd027_passed,
            current_params=current_params,
        )

        if result.applied:
            self._total_applied += 1
            logger.info(
                f"[FTD-030B] Memory applied: param={parameter} "
                f"pattern={pattern.pattern_id} "
                f"conf={pattern.confidence:.1f} "
                f"final={result.final_value:.6f} weight={result.memory_weight:.2f}"
            )

        return result

    # ── Report ────────────────────────────────────────────────────────────────

    def _write_report(self) -> None:
        try:
            top      = self._engine.top_by_confidence(5)
            bottom   = self._engine.bottom_by_confidence(3)
            last_exp = self._explainer.last()
            neg_sum  = self._neg.summary()
            for_sum  = self._forgetter.summary()

            lines = [
                "# FTD-030B — Learning Memory Report",
                "",
                f"**Active:** {'YES' if self._active else 'NO'}",
                f"**Total Records:** {self._store.count()}",
                f"**Valid Patterns:** {len(self._engine.valid_patterns())}",
                f"**Total Applied:** {self._total_applied}",
                f"**Blacklisted:** {neg_sum['blacklisted']}",
                f"**Permanently Banned:** {neg_sum['permanently_banned']}",
                f"**Total Removed (decay):** {for_sum['total_removed']}",
                "",
                "## Top Patterns (by confidence)",
                "",
                "| Pattern ID | Confidence | Success Rate | Samples |",
                "|---|---|---|---|",
            ]
            for p in top:
                lines.append(
                    f"| {p.pattern_id} | {p.confidence:.1f} "
                    f"| {p.success_rate:.2%} | {p.samples} |"
                )

            if bottom:
                lines += ["", "## Weakest Valid Patterns", "",
                          "| Pattern ID | Confidence |", "|---|---|"]
                for p in bottom:
                    lines.append(f"| {p.pattern_id} | {p.confidence:.1f} |")

            if last_exp:
                lines += [
                    "", "## Last Applied Memory", "",
                    f"- **Pattern:** `{last_exp.pattern_id}`",
                    f"- **Confidence:** {last_exp.confidence:.1f}",
                    f"- **Success Rate:** {last_exp.success_rate:.2%}",
                    f"- **Applied Weight:** {last_exp.applied_weight:.2f}",
                    f"- **Final Value:** {last_exp.final_value}",
                ]

            lines += [
                "", "> FTD-028 validates — FTD-029 corrects — "
                "FTD-030 automates — FTD-030B **learns**.",
            ]

            REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        except Exception:
            pass

    # ── Status / dashboard ────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        top = self._engine.top_by_confidence(10)
        return {
            "module":           self.MODULE,
            "phase":            self.PHASE,
            "active":           self._active,
            "stable_cycles":    self._stable_cycles,
            "activation_gates": {
                "min_trades":   ACTIVATION_MIN_TRADES,
                "min_score":    ACTIVATION_MIN_SCORE,
                "stable_k":     ACTIVATION_STABLE_K,
            },
            "store":            self._store.summary(),
            "patterns":         self._engine.summary(),
            "negative_memory":  self._neg.summary(),
            "forgetting":       self._forgetter.summary(),
            "applier":          self._applier.summary(),
            "indexer":          self._indexer.summary(),
            "total_updates":    self._total_updates,
            "total_applied":    self._total_applied,
            "top_patterns":     [p.to_dict() for p in top],
            "last_explain":     self._explainer.last().to_dict() if self._explainer.last() else None,
        }

    def pattern_heatmap(self) -> List[Dict[str, Any]]:
        """Heatmap data: regime × parameter → avg confidence."""
        result: Dict[str, Dict[str, list]] = {}
        for pat in self._engine.valid_patterns():
            r = pat.regime
            p = pat.parameter
            result.setdefault(r, {}).setdefault(p, []).append(pat.confidence)
        out = []
        for regime, params in result.items():
            for param, confs in params.items():
                out.append({
                    "regime":     regime,
                    "parameter":  param,
                    "avg_conf":   round(sum(confs) / len(confs), 1),
                    "count":      len(confs),
                })
        return out


# ── Singleton ─────────────────────────────────────────────────────────────────
learning_memory = LearningMemoryEngine()
