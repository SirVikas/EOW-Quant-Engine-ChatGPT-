"""
FTD-NEXUS-100-PERCENT-001 Phase 7 — AEG Readiness Framework

Validates whether Autonomous Engineering Governance can be safely activated.
ALL 8 prerequisites must pass before AEG GO is declared.

This engine does NOT activate AEG. It only audits readiness.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

import logging
logger = logging.getLogger(__name__)

_CHECK_NAMES = [
    "memory_maturity",
    "attribution_operational",
    "kge_intelligence",
    "confidence_model",
    "historical_coverage",
    "governance_completeness",
    "safety_system",
    "evidence_quality",
]


def _check_result(check: str, status: str, value: Any, threshold: Any, message: str) -> dict:
    return {
        "check": check,
        "status": status,   # PASS | FAIL | WARN
        "value": value,
        "threshold": threshold,
        "message": message,
    }


class AEGReadinessEngine:

    # ── 8 prerequisite checks ─────────────────────────────────────────────────

    def check_memory_maturity(self) -> dict:
        """IMRAF record count >= 500 AND provenance coverage >= 60%."""
        check = "memory_maturity"
        try:
            from core.institutional_memory.imraf_engine import imraf
            stats = imraf.get_stats()
            total = stats.get("total_records", 0)
            # Provenance coverage: records with non-empty data.provenance
            records = imraf.timeline(limit=2000)
            with_provenance = sum(
                1 for r in records
                if isinstance(r.get("data"), dict) and r["data"].get("provenance")
            )
            pct = round(with_provenance / len(records) * 100, 1) if records else 0.0
        except Exception as exc:
            logger.warning("check_memory_maturity error: %s", exc)
            return _check_result(check, "FAIL", {"total": 0, "provenance_pct": 0.0},
                                 {"min_records": 500, "min_provenance_pct": 60.0},
                                 f"IMRAF unavailable: {exc}")

        passes = total >= 500 and pct >= 60.0
        status = "PASS" if passes else "FAIL"
        return _check_result(
            check, status,
            {"total_records": total, "provenance_pct": pct},
            {"min_records": 500, "min_provenance_pct": 60.0},
            f"{total} records, {pct}% provenance coverage"
            + ("" if passes else " — need ≥500 records and ≥60% provenance"),
        )

    def check_attribution_operational(self) -> dict:
        """DOAE has >= 1 non-synthetic attribution with post_trades >= 100."""
        check = "attribution_operational"
        try:
            from core.nexus.doae.doae_engine import doae
            report = doae.get_attribution_report()
            attributions = report.get("attributions", [])
            non_synthetic = [
                a for a in attributions
                if "synthetic" not in (a.get("notes") or "").lower()
                and (a.get("post_trades") or 0) >= 100
            ]
            count = len(non_synthetic)
        except Exception as exc:
            logger.warning("check_attribution_operational error: %s", exc)
            return _check_result(check, "FAIL", 0, 1,
                                 f"DOAE unavailable: {exc}")

        status = "PASS" if count >= 1 else "FAIL"
        return _check_result(
            check, status, count, 1,
            f"{count} non-synthetic attributions with ≥100 post-trades"
            + ("" if count >= 1 else " — need at least 1"),
        )

    def check_kge_intelligence(self) -> dict:
        """KGE intelligence_score >= 60."""
        check = "kge_intelligence"
        try:
            from core.nexus.kge.kge_engine import kge
            intel = kge.relationship_intelligence_score()
            score = intel.get("intelligence_score", 0.0)
        except Exception as exc:
            logger.warning("check_kge_intelligence error: %s", exc)
            return _check_result(check, "FAIL", 0.0, 60.0, f"KGE unavailable: {exc}")

        status = "PASS" if score >= 60.0 else "FAIL"
        return _check_result(
            check, status, score, 60.0,
            f"KGE intelligence_score={score}"
            + ("" if score >= 60.0 else " — need ≥60"),
        )

    def check_confidence_model(self) -> dict:
        """ConfidenceEngine composite >= 0.65."""
        check = "confidence_model"
        try:
            from core.nexus.confidence.confidence_engine import confidence_engine
            report = confidence_engine.compute_nexus_confidence()
            composite = report.get("nexus_composite_confidence", 0.0)
        except Exception as exc:
            logger.warning("check_confidence_model error: %s", exc)
            return _check_result(check, "FAIL", 0.0, 0.65, f"ConfidenceEngine unavailable: {exc}")

        status = "PASS" if composite >= 0.65 else "FAIL"
        return _check_result(
            check, status, composite, 0.65,
            f"Composite confidence={composite}"
            + ("" if composite >= 0.65 else " — need ≥0.65"),
        )

    def check_historical_coverage(self) -> dict:
        """HKE has extracted from >= 5 source types."""
        check = "historical_coverage"
        try:
            from core.nexus.hke.hke_engine import hke
            stats = hke.get_stats()
            sources = stats.get("sources", [])
            count = len(sources)
        except Exception as exc:
            logger.warning("check_historical_coverage error: %s", exc)
            return _check_result(check, "FAIL", 0, 5, f"HKE unavailable: {exc}")

        status = "PASS" if count >= 5 else "FAIL"
        return _check_result(
            check, status, count, 5,
            f"HKE extracts from {count} source types"
            + ("" if count >= 5 else " — need ≥5"),
        )

    def check_governance_completeness(self) -> dict:
        """Governance coverage >= 70% and no unresolved HIGH contradictions."""
        check = "governance_completeness"
        try:
            from core.nexus.governance_intelligence.governance_intelligence import (
                GovernanceIntelligenceEngine,
            )
            gov = GovernanceIntelligenceEngine()
            coverage = gov.governance_coverage_report()
            contradictions = gov.detect_real_contradictions()
            coverage_pct = coverage.get("coverage_pct", 0.0)
            high_unresolved = sum(1 for c in contradictions if c.get("severity") == "HIGH")
        except Exception as exc:
            logger.warning("check_governance_completeness error: %s", exc)
            return _check_result(check, "FAIL",
                                 {"coverage_pct": 0.0, "high_contradictions": 0},
                                 {"min_coverage_pct": 70.0, "max_high_contradictions": 0},
                                 f"GovernanceIntelligenceEngine unavailable: {exc}")

        passes = coverage_pct >= 70.0 and high_unresolved == 0
        status = "PASS" if passes else "FAIL"
        return _check_result(
            check, status,
            {"coverage_pct": coverage_pct, "high_contradictions": high_unresolved},
            {"min_coverage_pct": 70.0, "max_high_contradictions": 0},
            f"Coverage={coverage_pct}%, high contradictions={high_unresolved}"
            + ("" if passes else " — need ≥70% coverage and 0 HIGH contradictions"),
        )

    def check_safety_system(self) -> dict:
        """Safety system (approval queue + rollback) not yet implemented."""
        # Per spec: always FAIL until safety system is built
        return _check_result(
            "safety_system", "FAIL", None, "implemented",
            "Safety system (approval queue + rollback) not yet implemented. "
            "Implement before AEG activation.",
        )

    def check_evidence_quality(self) -> dict:
        """IMRAF verified facts (confidence >= 0.75) >= 100."""
        check = "evidence_quality"
        try:
            from core.institutional_memory.imraf_engine import imraf
            from core.nexus.confidence.confidence_engine import confidence_engine
            records = imraf.timeline(limit=2000)
            verified_count = sum(
                1 for r in records if confidence_engine.score_fact(r) >= 0.75
            )
        except Exception as exc:
            logger.warning("check_evidence_quality error: %s", exc)
            return _check_result(check, "FAIL", 0, 100, f"Error: {exc}")

        status = "PASS" if verified_count >= 100 else "FAIL"
        return _check_result(
            check, status, verified_count, 100,
            f"{verified_count} verified facts (confidence ≥0.75)"
            + ("" if verified_count >= 100 else " — need ≥100"),
        )

    # ── Audit ─────────────────────────────────────────────────────────────────

    def run_readiness_audit(self) -> dict:
        """
        Run all 8 prerequisite checks and return a composite verdict.

        Verdict:
          GO      — all 8 PASS
          PARTIAL — 5-7 PASS
          NO_GO   — <5 PASS
        """
        ts = int(time.time() * 1000)

        checks = [
            self.check_memory_maturity(),
            self.check_attribution_operational(),
            self.check_kge_intelligence(),
            self.check_confidence_model(),
            self.check_historical_coverage(),
            self.check_governance_completeness(),
            self.check_safety_system(),
            self.check_evidence_quality(),
        ]

        pass_count = sum(1 for c in checks if c["status"] == "PASS")
        fail_count = sum(1 for c in checks if c["status"] == "FAIL")
        warn_count = sum(1 for c in checks if c["status"] == "WARN")
        blocking = [c for c in checks if c["status"] == "FAIL"]
        readiness_pct = round(pass_count / 8 * 100, 2)

        if pass_count == 8:
            verdict = "GO"
            recommendation = "All prerequisites satisfied. AEG activation is approved."
        elif pass_count >= 5:
            verdict = "PARTIAL"
            remaining = [c["check"] for c in blocking]
            recommendation = (
                f"Partial readiness ({pass_count}/8). Resolve failing checks before "
                f"AEG activation: {', '.join(remaining)}"
            )
        else:
            verdict = "NO_GO"
            remaining = [c["check"] for c in blocking]
            recommendation = (
                f"AEG not ready ({pass_count}/8 checks passing). Critical gaps: "
                f"{', '.join(remaining)}"
            )

        return {
            "verdict": verdict,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "warn_count": warn_count,
            "checks": checks,
            "blocking_failures": blocking,
            "readiness_pct": readiness_pct,
            "recommendation": recommendation,
            "ts": ts,
        }


# Singleton
aeg_readiness = AEGReadinessEngine()
