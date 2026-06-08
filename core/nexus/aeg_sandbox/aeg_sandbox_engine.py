"""
AEG Sandbox Engine.

Generates advisory recommendations from NEXUS state WITHOUT executing them.
Logged to data/aeg_sandbox.json for future accuracy validation.

Promotion to live AEG is only possible after ACCURACY_THRESHOLD is reached
over MIN_SANDBOX_RECOMMENDATIONS validated outcomes.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

import logging
logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).parent.parent.parent.parent.parent / "data" / "aeg_sandbox.json"
_MS_PER_DAY = 86_400_000


class AEGSandboxEngine:
    """
    AEG Sandbox — read-only recommendation generation.

    Recommendations are generated from IMRAF + DOAE + KGE patterns but
    NEVER applied autonomously. They are logged to data/aeg_sandbox.json
    for accuracy validation once live evidence accumulates.

    When sandbox recommendation accuracy exceeds ACCURACY_THRESHOLD (0.70)
    over MIN_SANDBOX_RECOMMENDATIONS (20+), AEG can be promoted to PARTIAL GO.
    """

    ACCURACY_THRESHOLD = 0.70
    MIN_SANDBOX_RECOMMENDATIONS = 20

    def __init__(self, data_file: Path = _DATA_FILE) -> None:
        self._data_file = data_file
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self._data_file.exists():
            try:
                return json.loads(self._data_file.read_text())
            except Exception:
                pass
        return {"recommendations": []}

    def _save(self, state: dict) -> None:
        self._data_file.write_text(json.dumps(state, indent=2))

    # ── Source miners ─────────────────────────────────────────────────────────

    def _mine_stale_decisions(self) -> List[dict]:
        """IMRAF DECISION records older than 90 days → stale review recommendations."""
        recs = []
        try:
            from core.institutional_memory.imraf_engine import imraf
            decisions = imraf.timeline(category="DECISION", limit=500)
            cutoff_ms = int(time.time() * 1000) - 90 * _MS_PER_DAY
            for d in decisions:
                ts = d.get("ts", 0)
                if ts and ts < cutoff_ms:
                    age_days = round((time.time() * 1000 - ts) / _MS_PER_DAY)
                    recs.append({
                        "type": "GOVERNANCE",
                        "title": f"Review stale decision: {d.get('title', 'Unknown')}",
                        "recommendation": (
                            f"IMRAF record #{d.get('id')} ('{d.get('title')}') "
                            f"is {age_days} days old with no supersession marker. "
                            "Verify it still reflects current system behaviour or mark deprecated."
                        ),
                        "confidence": min(0.5 + (age_days - 90) / 1000, 0.85),
                        "evidence_basis": [str(d.get("id"))],
                    })
        except Exception as exc:
            logger.debug("AEG mine_stale_decisions failed: %s", exc)
        return recs

    def _mine_doae_negative(self) -> List[dict]:
        """DOAE negative-impact FTDs → consider reverting recommendations."""
        recs = []
        try:
            from core.nexus.doae.doae_engine import DOAEEngine
            report = DOAEEngine().get_report()
            for entry in report.get("negative_impact", [])[:3]:
                ftd_id = entry.get("ftd_id") or entry.get("id") or "unknown"
                recs.append({
                    "type": "STRATEGY",
                    "title": f"Review negative-impact FTD: {ftd_id}",
                    "recommendation": (
                        f"FTD {ftd_id} shows negative DOAE impact "
                        f"(score: {entry.get('score', 'N/A')}). "
                        "Consider reverting or re-parameterising."
                    ),
                    "confidence": 0.65,
                    "evidence_basis": [str(ftd_id)],
                })
        except Exception as exc:
            logger.debug("AEG mine_doae_negative failed: %s", exc)
        return recs

    def _mine_stale_assumptions(self) -> List[dict]:
        """Governance stale assumptions → update assumption recommendations."""
        recs = []
        try:
            from core.nexus.governance_intelligence.governance_intelligence import (
                GovernanceIntelligenceEngine,
            )
            findings = GovernanceIntelligenceEngine().detect_stale_assumptions()
            for f in findings[:2]:
                recs.append({
                    "type": "GOVERNANCE",
                    "title": f"Update stale assumption: {f.get('title', 'Unknown')}",
                    "recommendation": (
                        f"Assumption in '{f.get('title')}' (introduced {f.get('version_introduced', '?')}) "
                        f"may be outdated by {f.get('minor_versions_old', '?')} minor versions. "
                        "Review and re-validate against current system state."
                    ),
                    "confidence": 0.72,
                    "evidence_basis": [str(f.get("record_id", ""))],
                })
        except Exception as exc:
            logger.debug("AEG mine_stale_assumptions failed: %s", exc)
        return recs

    def _mine_kge_isolated_nodes(self) -> List[dict]:
        """KGE nodes with high value but no edges → connect knowledge gap recommendations."""
        recs = []
        try:
            from core.nexus.kge.kge_engine import KGEEngine
            kge = KGEEngine()
            stats = kge.get_stats()
            isolated = stats.get("isolated_nodes", [])
            for node in isolated[:2]:
                node_id = node.get("node_id") or node if isinstance(node, str) else str(node)
                recs.append({
                    "type": "KNOWLEDGE",
                    "title": f"Connect isolated KGE node: {node_id}",
                    "recommendation": (
                        f"KGE node '{node_id}' has no relationships in the knowledge graph. "
                        "Link it to related decisions or components to improve institutional connectivity."
                    ),
                    "confidence": 0.60,
                    "evidence_basis": [node_id],
                })
        except Exception as exc:
            logger.debug("AEG mine_kge_isolated_nodes failed: %s", exc)
        return recs

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_recommendations(self) -> List[dict]:
        """
        Generate up to 5 advisory recommendations from current NEXUS state.
        Sources are mined lazily; failures in any source are silently skipped
        so a degraded subsystem cannot block the others.
        """
        candidates: List[dict] = []
        candidates.extend(self._mine_stale_decisions())
        candidates.extend(self._mine_doae_negative())
        candidates.extend(self._mine_stale_assumptions())
        candidates.extend(self._mine_kge_isolated_nodes())

        # Sort by confidence descending, take top 5
        candidates.sort(key=lambda r: r.get("confidence", 0), reverse=True)
        candidates = candidates[:5]

        now_ms = int(time.time() * 1000)
        new_recs = []
        for c in candidates:
            rec = {
                "id": str(uuid.uuid4()),
                "type": c["type"],
                "title": c["title"],
                "recommendation": c["recommendation"],
                "confidence": round(c.get("confidence", 0.5), 4),
                "evidence_basis": c.get("evidence_basis", []),
                "generated_at": now_ms,
                "status": "SANDBOX_PENDING",
                "outcome": None,
                "accurate": None,
            }
            new_recs.append(rec)

        with self._lock:
            state = self._load()
            state["recommendations"].extend(new_recs)
            self._save(state)

        return new_recs

    def record_outcome(self, rec_id: str, outcome: str, accurate: bool) -> bool:
        """Mark a sandbox recommendation as validated with actual outcome."""
        with self._lock:
            state = self._load()
            for rec in state["recommendations"]:
                if rec.get("id") == rec_id:
                    rec["outcome"] = outcome
                    rec["accurate"] = accurate
                    rec["status"] = "VALIDATED"
                    self._save(state)
                    return True
        return False

    def get_accuracy_stats(self) -> dict:
        """Return accuracy statistics and promotion eligibility."""
        with self._lock:
            state = self._load()
            recs = state.get("recommendations", [])

        total = len(recs)
        validated = [r for r in recs if r.get("status") == "VALIDATED"]
        accurate_count = sum(1 for r in validated if r.get("accurate") is True)
        validated_count = len(validated)
        accuracy_rate = accurate_count / validated_count if validated_count > 0 else 0.0

        promotion_eligible = (
            accuracy_rate >= self.ACCURACY_THRESHOLD
            and validated_count >= self.MIN_SANDBOX_RECOMMENDATIONS
        )

        if validated_count < self.MIN_SANDBOX_RECOMMENDATIONS:
            promotion_status = "INSUFFICIENT_DATA"
        elif accuracy_rate >= self.ACCURACY_THRESHOLD:
            promotion_status = "ELIGIBLE"
        else:
            promotion_status = "BELOW_THRESHOLD"

        recommendations_needed = max(0, self.MIN_SANDBOX_RECOMMENDATIONS - validated_count)

        return {
            "total_recommendations": total,
            "validated": validated_count,
            "accurate": accurate_count,
            "accuracy_rate": round(accuracy_rate, 4),
            "promotion_eligible": promotion_eligible,
            "promotion_status": promotion_status,
            "recommendations_needed": recommendations_needed,
        }

    def get_sandbox_status(self) -> dict:
        """Full status for API endpoint."""
        with self._lock:
            state = self._load()
            recs = state.get("recommendations", [])

        stats = self.get_accuracy_stats()
        pending = [r for r in recs if r.get("status") == "SANDBOX_PENDING"]

        return {
            "mode": "SANDBOX",
            "description": "AEG Sandbox — recommendations generated but not applied",
            "accuracy_threshold": self.ACCURACY_THRESHOLD,
            "min_recommendations": self.MIN_SANDBOX_RECOMMENDATIONS,
            "recommendations": recs[-20:],  # last 20 for API response size
            "pending_count": len(pending),
            **stats,
        }

    def run_sandbox_cycle(self) -> dict:
        """Generate new recommendations and return sandbox status."""
        new_recs = self.generate_recommendations()
        status = self.get_sandbox_status()
        status["cycle_generated"] = len(new_recs)
        return status


aeg_sandbox = AEGSandboxEngine()
