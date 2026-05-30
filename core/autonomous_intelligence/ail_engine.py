"""
FTD-AIL-001: AIL Engine — singleton orchestrator.
Boots the collection/analysis pipeline, exposes the governance API.

CONSTITUTIONAL RULE: AIL MUST NEVER modify code, deploy, change parameters,
or override human approval. All findings remain PENDING until a human approves.
"""
from __future__ import annotations
import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Optional

from loguru import logger

from core.autonomous_intelligence.collector.report_collector import collect_all
from core.autonomous_intelligence.collector.scheduler import AILScheduler
from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze
from core.autonomous_intelligence.analysis.finding_generator import generate_findings
from core.autonomous_intelligence.recommendation.recommendation_engine import enrich_recommendation
from core.autonomous_intelligence.recommendation.ftd_generator import maybe_draft_ftd
from core.autonomous_intelligence.governance.evidence_scoring_engine import score_finding
from core.autonomous_intelligence.governance.approval_gate import apply_decision
from core.autonomous_intelligence.storage import findings_store, history_store
from core.autonomous_intelligence.storage import archive_store


class AILEngine:
    def __init__(self) -> None:
        self._enabled = True
        self._booted  = False
        self._boot_ts: Optional[float] = None
        self._last_collection_ts: Optional[float] = None
        self._scheduler: Optional[AILScheduler] = None
        self._win_rate_history: list[float] = []
        self._collection_count = 0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def boot(self) -> None:
        if self._booted:
            return
        self._booted  = True
        self._boot_ts = time.time()
        self._scheduler = AILScheduler(
            collect_fn=collect_all,
            analyze_fn=self._analyze_snapshots,
            interval_sec=900.0,
        )
        self._scheduler.start()
        logger.info("[AIL] Autonomous Intelligence Layer booted | FTD-AIL-001")

    async def shutdown(self) -> None:
        if self._scheduler:
            await self._scheduler.stop()
        logger.info("[AIL] Shutdown complete")

    # ── Core analysis pipeline ────────────────────────────────────────────────

    async def _analyze_snapshots(self, snapshots: dict[str, Any]) -> dict:
        """
        Async analysis pipeline — called directly from scheduler (not via to_thread).
        Must be async so storage awaits work on the event loop.
        """
        self._last_collection_ts = time.time()
        self._collection_count  += 1

        # Archive all snapshots (non-blocking)
        for label, data in snapshots.items():
            try:
                await archive_store.archive(label, data)
            except Exception:
                pass

        # Track win rate history for trend analysis
        perf = snapshots.get("Performance Status", {})
        wr = perf.get("win_rate")
        if wr is not None:
            self._win_rate_history.append(float(wr))
            if len(self._win_rate_history) > 20:
                self._win_rate_history = self._win_rate_history[-20:]

        # Run rules (synchronous CPU work — fast enough to not need threading)
        rule_hits = analyze(snapshots, self._win_rate_history)

        # Generate findings and persist each one
        findings = generate_findings(rule_hits)
        new_count = 0
        for f in findings:
            f = enrich_recommendation(f)
            draft = maybe_draft_ftd(f)
            if draft:
                f.ftd_draft = draft
            ev_score = score_finding(f, self._last_collection_ts)
            d = f.to_dict()
            d["evidence_score"] = ev_score
            try:
                await findings_store.save_finding(d)
                new_count += 1
            except Exception as exc:
                logger.warning(f"[AIL] Failed to save finding: {exc}")

        logger.info(
            f"[AIL] Cycle #{self._collection_count} | "
            f"snapshots={len(snapshots)} rules_fired={len(rule_hits)} new_findings={new_count}"
        )
        return {"new_findings": new_count, "rules_fired": len(rule_hits)}

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_status(self) -> dict:
        findings = await findings_store.list_findings()
        counts = {"PENDING": 0, "APPROVED": 0, "REJECTED": 0, "NEEDS_MORE_EVIDENCE": 0}
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in findings:
            counts[f.get("status", "PENDING")] = counts.get(f.get("status", "PENDING"), 0) + 1
            severity_counts[f.get("severity", "INFO")] = severity_counts.get(f.get("severity", "INFO"), 0) + 1
        return {
            "enabled": self._enabled,
            "booted": self._booted,
            "boot_ts": self._boot_ts,
            "last_collection_ts": self._last_collection_ts,
            "collection_count": self._collection_count,
            "findings_by_status": counts,
            "findings_by_severity": severity_counts,
            "scheduler": self._scheduler.status if self._scheduler else {},
            "ts": int(time.time() * 1000),
        }

    async def get_findings(self, status: str | None = None) -> list[dict]:
        return await findings_store.list_findings(status)

    async def get_finding(self, lineage_id: str) -> dict | None:
        return await findings_store.get_finding(lineage_id)

    async def approve_finding(self, lineage_id: str) -> dict:
        f = await findings_store.get_finding(lineage_id)
        if not f:
            raise KeyError(f"Finding {lineage_id} not found")
        apply_decision(f, "APPROVED")
        await findings_store.update_status(lineage_id, "APPROVED", approved_at=f["approved_at"])
        await history_store.record(lineage_id, "APPROVED")
        logger.info(f"[AIL] Finding APPROVED: {lineage_id}")
        return f

    async def reject_finding(self, lineage_id: str, reason: str = "") -> dict:
        f = await findings_store.get_finding(lineage_id)
        if not f:
            raise KeyError(f"Finding {lineage_id} not found")
        apply_decision(f, "REJECTED", reason)
        await findings_store.update_status(
            lineage_id, "REJECTED",
            rejected_at=f["rejected_at"], rejection_reason=reason,
        )
        await history_store.record(lineage_id, "REJECTED", reason)
        logger.info(f"[AIL] Finding REJECTED: {lineage_id} | {reason}")
        return f

    async def needs_evidence(self, lineage_id: str, reason: str = "") -> dict:
        f = await findings_store.get_finding(lineage_id)
        if not f:
            raise KeyError(f"Finding {lineage_id} not found")
        apply_decision(f, "NEEDS_MORE_EVIDENCE", reason)
        await findings_store.update_status(lineage_id, "NEEDS_MORE_EVIDENCE")
        await history_store.record(lineage_id, "NEEDS_MORE_EVIDENCE", reason)
        return f

    async def get_history(self, limit: int = 100) -> list[dict]:
        return await history_store.get_history(limit)

    async def get_daily_brief(self) -> dict:
        findings = await findings_store.list_findings()
        pending  = [f for f in findings if f["status"] == "PENDING"]
        high_sev = [f for f in pending if f["severity"] in ("CRITICAL", "HIGH")]
        return {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "total_findings": len(findings),
            "pending": len(pending),
            "pending_high_severity": len(high_sev),
            "top_findings": sorted(
                pending, key=lambda x: x.get("evidence_score", 0), reverse=True
            )[:5],
            "collection_count": self._collection_count,
            "last_collection_ts": self._last_collection_ts,
            "ts": int(time.time() * 1000),
        }

    async def force_collect(self) -> dict:
        if not self._scheduler:
            raise RuntimeError("AIL not booted")
        return await self._scheduler.force_run()

    def enable(self) -> None:
        self._enabled = True
        if self._scheduler and not self._scheduler._running:
            self._scheduler.start()
        logger.info("[AIL] Enabled")

    def disable(self) -> None:
        self._enabled = False
        logger.info("[AIL] Disabled (scheduler paused at next cycle)")


# ── Singleton ─────────────────────────────────────────────────────────────────
ail_engine = AILEngine()
