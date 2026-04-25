"""
FTD-030 — Auto Intelligence Engine

Autonomous closed-loop background runner that executes FTD-028 (Deep Validation)
+ FTD-029 (Self-Correction) on a configurable schedule without human intervention.

Design principles:
  • Runs every AUTO_INTELLIGENCE_INTERVAL_MIN minutes
  • Requires AUTO_INTELLIGENCE_MIN_TRADES before firing
  • After a correction, waits AUTO_INTELLIGENCE_POST_WAIT_TRADES trades, then resolves
  • Enforces AUTO_INTELLIGENCE_MAX_DAILY_CYCLES to prevent over-correction
  • Broadcasts each cycle result to callers via a callback hook

Cycle phases:
  1. VALIDATION  — FTD-028: run all 13 validators via MetaScoreEngine
  2. CORRECTION  — FTD-029: run_cycle() with validation results
  3. POST_CHECK  — FTD-029: resolve_cycle() after N trades settle
  4. REPORT      — write reports/auto_intelligence/latest.json + last_report.md
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from config import cfg


# ── Cycle phases ──────────────────────────────────────────────────────────────

PHASE_IDLE       = "IDLE"
PHASE_VALIDATING = "VALIDATING"
PHASE_CORRECTING = "CORRECTING"
PHASE_POST_CHECK = "POST_CHECK"
PHASE_COMPLETE   = "COMPLETE"
PHASE_BLOCKED    = "BLOCKED"


@dataclass
class CycleRecord:
    cycle_num:     int
    ts_start:      int
    ts_end:        int   = 0
    phase:         str   = PHASE_IDLE
    validation:    Dict[str, Any] = field(default_factory=dict)
    correction:    Dict[str, Any] = field(default_factory=dict)
    post_check:    Dict[str, Any] = field(default_factory=dict)
    meta_score:    float = 0.0
    blocked:       bool  = False
    block_reason:  str   = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_num":    self.cycle_num,
            "ts_start":     self.ts_start,
            "ts_end":       self.ts_end,
            "phase":        self.phase,
            "meta_score":   self.meta_score,
            "blocked":      self.blocked,
            "block_reason": self.block_reason,
            "correction_verdict": self.correction.get("verdict", "—"),
            "applied_count":      len(self.correction.get("applied", [])),
            "rollback_count":     self.post_check.get("rollback_count", 0),
        }


class AutoIntelligenceEngine:
    """
    FTD-030 autonomous closed-loop intelligence runner.

    Instantiated as a singleton. The background async loop is started by
    main.py lifespan via start_loop() and cancelled on shutdown.

    Args:
        state_fn:      Callable[[], tuple] returning the same 6-tuple as _sc_build_state()
                       (system_state, current_params, ftd028_validators, ftd028_meta,
                        ai_brain_score, halted)
        trades_fn:     Callable[[], int]  returning current trade count
        broadcast_fn:  Optional[Callable[[dict], None]]  WS broadcast hook
    """

    MODULE = "AUTO_INTELLIGENCE_ENGINE"
    PHASE  = "030"

    def __init__(
        self,
        state_fn:     Callable[[], tuple],
        trades_fn:    Callable[[], int],
        broadcast_fn: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self._state_fn     = state_fn
        self._trades_fn    = trades_fn
        self._broadcast_fn = broadcast_fn

        self._enabled:           bool = cfg.AUTO_INTELLIGENCE_ENABLED
        self._interval_sec:      float = cfg.AUTO_INTELLIGENCE_INTERVAL_MIN * 60.0
        self._min_trades:        int   = cfg.AUTO_INTELLIGENCE_MIN_TRADES
        self._min_score:         float = cfg.AUTO_INTELLIGENCE_MIN_SCORE
        self._post_wait_trades:  int   = cfg.AUTO_INTELLIGENCE_POST_WAIT_TRADES
        self._max_daily:         int   = cfg.AUTO_INTELLIGENCE_MAX_DAILY_CYCLES

        self._cycle_num:         int   = 0
        self._daily_cycles:      int   = 0
        self._day_reset_ts:      float = time.time()
        self._last_run_ts:       float = 0.0
        self._pending_cycle_id:  Optional[str] = None
        self._pending_trades_at: Optional[int] = None   # trade count when correction was applied

        self._history: List[CycleRecord] = []
        self._current: Optional[CycleRecord] = None
        self._running: bool = False

        # FTD-030B: metadata carried from correction phase to post-check phase
        self._pending_meta_score:    float = 0.0
        self._pending_ai_mode:       str   = "UNKNOWN"
        self._pending_regime:        str   = "UNKNOWN"
        self._pending_volatility_pct: float = 0.15

        logger.info(
            f"[FTD-030] AutoIntelligenceEngine initialised | "
            f"interval={cfg.AUTO_INTELLIGENCE_INTERVAL_MIN}min "
            f"min_trades={self._min_trades} max_daily={self._max_daily}"
        )

    # ── Public controls ───────────────────────────────────────────────────────

    def enable(self)  -> None:
        self._enabled = True
        logger.info("[FTD-030] Auto-intelligence ENABLED")

    def disable(self) -> None:
        self._enabled = False
        logger.info("[FTD-030] Auto-intelligence DISABLED")

    def force_run(self) -> None:
        """Force the next tick to run a cycle immediately (bypass interval gate)."""
        self._last_run_ts = 0.0
        logger.info("[FTD-030] Force-run requested — next tick will execute cycle")

    def reset_daily_counter(self) -> None:
        self._daily_cycles = 0
        self._day_reset_ts = time.time()

    # ── Main tick — called by the background loop every interval ─────────────

    def tick(self) -> Dict[str, Any]:
        """
        Evaluate whether a correction cycle should run and, if so, execute it.

        Returns a summary dict (always safe to discard).
        """
        now       = time.time()
        n_trades  = self._trades_fn()

        # ── Daily counter reset ───────────────────────────────────────────────
        if now - self._day_reset_ts > 86400:
            self._daily_cycles  = 0
            self._day_reset_ts  = now

        # ── Post-correction check (resolve) ──────────────────────────────────
        if self._pending_cycle_id and self._pending_trades_at is not None:
            trades_since = n_trades - self._pending_trades_at
            if trades_since >= self._post_wait_trades:
                self._do_post_check()

        # ── Gate checks ──────────────────────────────────────────────────────
        if not self._enabled:
            return self._skip("DISABLED")
        if now - self._last_run_ts < self._interval_sec:
            return self._skip("INTERVAL_NOT_ELAPSED")
        if n_trades < self._min_trades:
            return self._skip(f"INSUFFICIENT_TRADES({n_trades}<{self._min_trades})")
        if self._daily_cycles >= self._max_daily:
            return self._skip(f"DAILY_CAP_REACHED({self._daily_cycles}/{self._max_daily})")

        # ── Run cycle ────────────────────────────────────────────────────────
        return self._do_full_cycle(now, n_trades)

    # ── Internal cycle execution ──────────────────────────────────────────────

    def _do_full_cycle(self, now: float, n_trades: int) -> Dict[str, Any]:
        self._cycle_num += 1
        rec = CycleRecord(
            cycle_num=self._cycle_num,
            ts_start=int(now * 1000),
            phase=PHASE_VALIDATING,
        )
        self._current = rec
        # FTD-031C: config_snapshot logging at auto-intelligence cycle start
        logger.info(
            f"[FTD-030] Starting cycle #{self._cycle_num} | trades={n_trades} | "
            f"config_snapshot: interval_min={cfg.AUTO_INTELLIGENCE_INTERVAL_MIN} "
            f"min_trades={cfg.AUTO_INTELLIGENCE_MIN_TRADES} "
            f"min_score={cfg.AUTO_INTELLIGENCE_MIN_SCORE} "
            f"max_daily={cfg.AUTO_INTELLIGENCE_MAX_DAILY_CYCLES} "
            f"KELLY_FRACTION={cfg.KELLY_FRACTION} "
            f"MAX_DRAWDOWN_HALT={cfg.MAX_DRAWDOWN_HALT} "
            f"P7B_PERF_WIN_THRESHOLD={cfg.P7B_PERF_WIN_THRESHOLD} "
            f"TR_EV_WEIGHT={cfg.TR_EV_WEIGHT}"
        )

        try:
            # Step 1: Build system state + run FTD-028 full validators
            system_state, current_params, ftd028_validators, ftd028_meta, ai_brain_score, halted = (
                self._state_fn()
            )

            meta_score = float(ftd028_meta.get("system_score", 0.0) or 0.0)
            rec.meta_score   = meta_score
            rec.validation   = {"ftd028_meta": ftd028_meta, "meta_score": meta_score}

            # FTD-030B: update activation gate after each validation (orchestrator)
            try:
                from core.learning_memory import learning_memory_orchestrator
                learning_memory_orchestrator.check_activation(n_trades, meta_score)
            except Exception as _lm_exc:
                logger.debug(f"[FTD-030B] check_activation skipped: {_lm_exc}")

            if meta_score < self._min_score:
                rec.blocked      = True
                rec.block_reason = f"META_SCORE_TOO_LOW({meta_score:.1f}<{self._min_score})"
                rec.phase        = PHASE_BLOCKED
                self._finalise(rec)
                logger.warning(f"[FTD-030] Cycle #{self._cycle_num} blocked: {rec.block_reason}")
                return rec.to_dict()

            # Step 2: FTD-029 correction
            rec.phase = PHASE_CORRECTING
            from core.self_correction.correction_orchestrator import correction_orchestrator
            correction = correction_orchestrator.run_cycle(
                ftd028_validators=ftd028_validators,
                ftd028_meta=ftd028_meta,
                current_params=current_params,
                system_state=system_state,
                ai_brain_score=ai_brain_score,
                risk_halted=halted,
                risk_violated=halted,
                contradiction_critical=not ftd028_validators.get("contradiction", {}).get("passed", True),
            )
            rec.correction = correction

            # Step 3: If corrections were applied, arm the post-check
            if correction.get("verdict") == "APPLIED":
                self._pending_cycle_id       = correction.get("cycle_id")
                self._pending_trades_at      = n_trades
                self._pending_meta_score     = meta_score
                self._pending_ai_mode        = str(system_state.get("ai_mode", "UNKNOWN"))
                self._pending_regime         = str(system_state.get("regime", "UNKNOWN"))
                self._pending_volatility_pct = float(system_state.get("volatility_pct", 0.15))
                rec.phase = PHASE_POST_CHECK
                logger.info(
                    f"[FTD-030] Cycle #{self._cycle_num}: {len(correction.get('applied', []))} "
                    f"corrections applied — post-check armed at trade #{n_trades + self._post_wait_trades}"
                )
            else:
                rec.phase = PHASE_COMPLETE

        except Exception as exc:
            rec.blocked      = True
            rec.block_reason = f"EXCEPTION: {exc}"
            rec.phase        = PHASE_BLOCKED
            logger.error(f"[FTD-030] Cycle #{self._cycle_num} error: {exc}")

        self._last_run_ts  = now
        self._daily_cycles += 1
        self._finalise(rec)

        summary = rec.to_dict()
        self._broadcast(summary)
        return summary

    def _do_post_check(self) -> None:
        """Resolve the pending correction cycle (rollback evaluation)."""
        if not self._pending_cycle_id:
            return
        cycle_id = self._pending_cycle_id
        self._pending_cycle_id  = None
        self._pending_trades_at = None

        try:
            system_state, _, ftd028_validators, ftd028_meta, _, halted = self._state_fn()
            post_score = float(ftd028_meta.get("system_score", 0.0) or 0.0)

            from core.self_correction.correction_orchestrator import correction_orchestrator
            result = correction_orchestrator.resolve_cycle(
                cycle_id=cycle_id,
                post_state=system_state,
                post_ftd028_score=post_score,
                risk_violated=halted,
                validation_passed=not ftd028_validators.get("contradiction", {}).get("block_report", False),
            )

            if self._current and self._current.correction.get("cycle_id") == cycle_id:
                self._current.post_check = result
                self._current.phase      = PHASE_COMPLETE
                self._current.ts_end     = int(time.time() * 1000)
                self._write_report(self._current)

            logger.info(
                f"[FTD-030] Post-check cycle_id={cycle_id}: "
                f"rollbacks={result.get('rollback_count', 0)} "
                f"post_score={post_score:.1f}"
            )

            # FTD-030B: feed cycle outcome into learning memory (orchestrator)
            try:
                from core.learning_memory import learning_memory_orchestrator
                applied_changes = (
                    self._current.correction.get("applied", [])
                    if self._current else []
                )
                vol_pct = self._pending_volatility_pct
                vol_bucket = "HIGH" if vol_pct > 0.3 else "LOW" if vol_pct < 0.1 else "MED"
                lm_result = learning_memory_orchestrator.after_resolve_cycle(
                    cycle_id=cycle_id,
                    applied_changes=applied_changes,
                    rollbacks=result.get("rollbacks", []),
                    context={
                        "regime":     self._pending_regime,
                        "volatility": vol_bucket,
                        "instrument": "CRYPTO",
                        "timeframe":  "1m",
                    },
                    pre_meta_score=self._pending_meta_score,
                    post_meta_score=post_score,
                    ai_mode=self._pending_ai_mode,
                    contradiction=not ftd028_validators.get(
                        "contradiction", {}
                    ).get("passed", True),
                )
                logger.info(
                    f"[FTD-030B] Memory update: "
                    f"records={lm_result.get('stored', 0)} "
                    f"patterns={lm_result.get('patterns_formed', 0)}"
                )
            except Exception as _lm_exc:
                logger.debug(f"[FTD-030B] memory update skipped: {_lm_exc}")

            self._broadcast({"type": "post_check", "cycle_id": cycle_id, **result})

        except Exception as exc:
            logger.error(f"[FTD-030] Post-check error for cycle_id={cycle_id}: {exc}")

    # ── Report writing ────────────────────────────────────────────────────────

    def _write_report(self, rec: CycleRecord) -> None:
        """Persist latest cycle report to reports/auto_intelligence/."""
        try:
            import json
            from pathlib import Path

            out_dir = Path(__file__).resolve().parents[2] / "reports" / "auto_intelligence"
            out_dir.mkdir(parents=True, exist_ok=True)

            payload = {
                **rec.to_dict(),
                "validation": rec.validation,
                "correction": rec.correction,
                "post_check": rec.post_check,
            }
            (out_dir / "latest.json").write_text(json.dumps(payload, indent=2, default=str))

            md = self._build_md(rec)
            (out_dir / "last_report.md").write_text(md)

        except Exception as exc:
            logger.warning(f"[FTD-030] Report write failed: {exc}")

    def _build_md(self, rec: CycleRecord) -> str:
        corr   = rec.correction
        post   = rec.post_check
        applied = corr.get("applied", [])
        rolled  = post.get("rollbacks", [])

        lines = [
            f"# FTD-030 — Auto Intelligence Report",
            f"",
            f"**Cycle:** #{rec.cycle_num}",
            f"**Phase:** {rec.phase}",
            f"**Meta Score (FTD-028):** {rec.meta_score:.1f}/100",
            f"",
            f"## Correction Summary",
            f"",
            f"| Field | Value |",
            f"|---|---|",
            f"| Verdict | {corr.get('verdict', '—')} |",
            f"| Issues Found | {corr.get('issues_found', 0)} |",
            f"| Corrections Applied | {len(applied)} |",
            f"| Rollbacks | {len(rolled)} |",
            f"",
        ]

        if applied:
            lines += [
                "## Applied Corrections",
                "",
                "| Parameter | Before | After | Δ% |",
                "|---|---|---|---|",
            ]
            for ch in applied:
                lines.append(
                    f"| {ch.get('parameter')} | {ch.get('before')} | {ch.get('after')} "
                    f"| {ch.get('delta_pct', 0):.1f}% |"
                )
            lines.append("")

        if rolled:
            lines += [
                "## Rollbacks",
                "",
                "| Parameter | Trigger |",
                "|---|---|",
            ]
            for rb in rolled:
                lines.append(f"| {rb.get('parameter', '?')} | {rb.get('trigger', '?')} |")
            lines.append("")

        if rec.blocked:
            lines += [f"## Block Reason", f"", f"`{rec.block_reason}`", ""]

        lines.append(f"> FTD-028 validates — FTD-029 corrects — FTD-030 **automates**.")
        return "\n".join(lines)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _finalise(self, rec: CycleRecord) -> None:
        rec.ts_end = int(time.time() * 1000)
        self._history.append(rec)
        if len(self._history) > 50:
            self._history = self._history[-50:]
        self._write_report(rec)

    def _skip(self, reason: str) -> Dict[str, Any]:
        return {
            "module":  self.MODULE,
            "phase":   self.PHASE,
            "action":  "SKIPPED",
            "reason":  reason,
            "ts":      int(time.time() * 1000),
        }

    def _broadcast(self, payload: Dict[str, Any]) -> None:
        if self._broadcast_fn:
            try:
                self._broadcast_fn({"type": "auto_intelligence", **payload})
            except Exception:
                pass

    # ── Status / dashboard ────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        last = self._history[-1].to_dict() if self._history else {}
        return {
            "module":         self.MODULE,
            "phase":          self.PHASE,
            "enabled":        self._enabled,
            "interval_min":   self._interval_sec / 60.0,
            "min_trades":     self._min_trades,
            "min_score":      self._min_score,
            "cycles_run":     self._cycle_num,
            "daily_cycles":   self._daily_cycles,
            "max_daily":      self._max_daily,
            "last_run_ts":    int(self._last_run_ts * 1000) if self._last_run_ts else None,
            "pending_check":  self._pending_cycle_id is not None,
            "last_cycle":     last,
        }

    def history(self, n: int = 20) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._history[-n:]]
