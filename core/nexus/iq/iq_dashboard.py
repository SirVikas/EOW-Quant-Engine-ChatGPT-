"""
Institutional IQ Dashboard.

Computes a multi-dimensional Institutional IQ score across 5 dimensions:
  1. Memory Coverage (IMRAF depth)
  2. Economic Attribution (DOAE completeness)
  3. Knowledge Coverage (KGE graph coverage)
  4. Governance Health (governance contradiction/stale scan)
  5. AEG Readiness (all preconditions for Autonomous Engineering Governance)

Weights: memory=0.25, attribution=0.30, knowledge=0.20, governance=0.15, aeg=0.10
Baseline: 28.0 (as assessed at NEXUS acceleration planning)
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Any

import logging
logger = logging.getLogger(__name__)

_IQ_BASELINE = 28.0

_WEIGHTS = {
    "memory_coverage": 0.25,
    "economic_attribution": 0.30,
    "knowledge_coverage": 0.20,
    "governance_health": 0.15,
    "aeg_readiness": 0.10,
}

_MEMORY_TARGET = 550  # EVOLUTION>=200, OPERATIONAL>=200, REGIME>=50, DECISION>=100


def _grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _trend(score: float, baseline: float) -> str:
    delta = score - baseline
    if delta > 2:
        return "UP"
    if delta < -2:
        return "DOWN"
    return "FLAT"


@dataclass
class DimensionScore:
    name: str
    score: float
    grade: str
    trend: str
    detail: str
    gap: str

    def to_dict(self) -> dict:
        return asdict(self)


class IQDashboard:

    def compute_memory_coverage(self) -> DimensionScore:
        try:
            from core.institutional_memory.imraf_engine import imraf
            stats = imraf.get_stats()
        except Exception as exc:
            logger.warning("IQDashboard memory_coverage error: %s", exc)
            stats = {"total_records": 0, "by_category": {}}

        total = stats.get("total_records", 0)
        by_cat = stats.get("by_category", {})

        dcel = (
            by_cat.get("EVOLUTION", 0)
            + by_cat.get("OPERATIONAL", 0)
            + by_cat.get("REGIME", 0)
            + by_cat.get("DECISION", 0)
        )
        score = float(min(100, int(dcel / _MEMORY_TARGET * 100)))
        return DimensionScore(
            name="memory_coverage",
            score=score,
            grade=_grade(score),
            trend=_trend(score, 30.0),
            detail=f"{total} total IMRAF records; {dcel} in DCEL categories (target {_MEMORY_TARGET})",
            gap=f"Need {max(0, _MEMORY_TARGET - dcel)} more DCEL records to reach 100%",
        )

    def compute_economic_attribution(self, doae_stats: dict) -> DimensionScore:
        is_operational = doae_stats.get("is_operational", False)
        ftds_with_attr = doae_stats.get("ftds_with_attribution", 0)
        total_ftds = max(1, doae_stats.get("total_active_ftds", 13))

        if not is_operational:
            score = 5.0
            detail = "Economic attribution engine not operational — no trade attribution data"
            gap = "Deploy and run DOAE engine with live trade data"
        else:
            score = float(min(100, 20 + int(ftds_with_attr / total_ftds * 80)))
            detail = f"{ftds_with_attr}/{total_ftds} FTDs have attribution data"
            gap = f"Add attribution for {total_ftds - ftds_with_attr} remaining FTDs"

        return DimensionScore(
            name="economic_attribution",
            score=score,
            grade=_grade(score),
            trend=_trend(score, 5.0),
            detail=detail,
            gap=gap,
        )

    def compute_knowledge_coverage(self, kge_stats: dict) -> DimensionScore:
        score = float(kge_stats.get("coverage_score", 0))
        node_count = kge_stats.get("node_count", 0)
        edge_count = kge_stats.get("edge_count", 0)
        return DimensionScore(
            name="knowledge_coverage",
            score=score,
            grade=_grade(score),
            trend=_trend(score, 0.0),
            detail=f"Knowledge graph: {node_count} nodes, {edge_count} edges",
            gap="Expand graph to 50+ nodes and 100+ edges for full coverage",
        )

    def compute_governance_health(self, gov_stats: dict) -> DimensionScore:
        score = float(gov_stats.get("health_score", 100))
        total_issues = gov_stats.get("total_issues", 0)
        return DimensionScore(
            name="governance_health",
            score=score,
            grade=_grade(score),
            trend=_trend(score, 70.0),
            detail=f"Governance health {score:.0f}/100; {total_issues} active issues",
            gap="Resolve HIGH severity assumption drift and contradiction findings",
        )

    def compute_aeg_readiness(self, memory_score: float, attribution_score: float, kge_score: float) -> DimensionScore:
        try:
            from core.institutional_memory.imraf_engine import imraf
            imraf_stats = imraf.get_stats()
            total_records = imraf_stats.get("total_records", 0)
        except Exception:
            total_records = 0

        memory_gate = 25 if memory_score >= 70 else 0
        attribution_gate = 25 if attribution_score >= 20 else 0
        kge_gate = 25 if kge_score >= 50 else 0
        facts_gate = 25 if total_records >= 500 else 0

        score = float(memory_gate + attribution_gate + kge_gate + facts_gate)

        gates_met = sum(1 for g in [memory_gate, attribution_gate, kge_gate, facts_gate] if g > 0)
        detail = f"{gates_met}/4 AEG precondition gates met (memory, attribution, KGE, 500+ facts)"
        gap_parts = []
        if not memory_gate:
            gap_parts.append("raise memory_coverage to >=70")
        if not attribution_gate:
            gap_parts.append("make attribution operational")
        if not kge_gate:
            gap_parts.append("grow KGE to >=50% coverage")
        if not facts_gate:
            gap_parts.append(f"accumulate {max(0, 500 - total_records)} more IMRAF records")
        gap = "; ".join(gap_parts) if gap_parts else "All AEG gates met — ready to implement"

        return DimensionScore(
            name="aeg_readiness",
            score=score,
            grade=_grade(score),
            trend=_trend(score, 0.0),
            detail=detail,
            gap=gap,
        )

    def compute(self) -> dict:
        # Gather external stats with graceful fallback
        try:
            from core.nexus.kge.kge_engine import kge
            kge_stats = kge.get_stats()
        except Exception as exc:
            logger.warning("IQDashboard: KGE unavailable: %s", exc)
            kge_stats = {"coverage_score": 0, "node_count": 0, "edge_count": 0}

        try:
            from core.nexus.governance_intelligence.governance_intelligence import GovernanceIntelligenceEngine
            gov_stats = GovernanceIntelligenceEngine().get_stats()
        except Exception as exc:
            logger.warning("IQDashboard: governance unavailable: %s", exc)
            gov_stats = {"health_score": 50, "total_issues": 0}

        # DOAE does not exist yet — supply sentinel
        doae_stats = {"is_operational": False, "ftds_with_attribution": 0, "total_active_ftds": 13}

        mem = self.compute_memory_coverage()
        attr = self.compute_economic_attribution(doae_stats)
        kge_dim = self.compute_knowledge_coverage(kge_stats)
        gov = self.compute_governance_health(gov_stats)
        aeg = self.compute_aeg_readiness(mem.score, attr.score, kge_dim.score)

        dims = {
            "memory_coverage": mem,
            "economic_attribution": attr,
            "knowledge_coverage": kge_dim,
            "governance_health": gov,
            "aeg_readiness": aeg,
        }

        iq = sum(_WEIGHTS[k] * d.score for k, d in dims.items())
        iq = round(iq, 1)
        grade = _grade(iq)
        aeg_blocked = aeg.score < 100

        # Most impactful dimension to improve (highest weight * gap)
        def _impact(k: str, d: DimensionScore) -> float:
            return _WEIGHTS[k] * (100.0 - d.score)

        next_dim_key = max(dims.keys(), key=lambda k: _impact(k, dims[k]))
        next_milestone = dims[next_dim_key].gap or f"Improve {next_dim_key}"

        try:
            from config import APP_VERSION
        except Exception:
            APP_VERSION = "unknown"

        return {
            "institutional_iq": iq,
            "grade": grade,
            "vs_baseline": round(iq - _IQ_BASELINE, 1),
            "dimensions": {k: d.to_dict() for k, d in dims.items()},
            "aeg_blocked": aeg_blocked,
            "next_milestone": next_milestone,
            "computed_at": datetime.datetime.utcnow().isoformat() + "Z",
            "engine_version": APP_VERSION,
        }

    def get_quick_score(self) -> dict:
        result = self.compute()
        return {
            "institutional_iq": result["institutional_iq"],
            "grade": result["grade"],
            "vs_baseline": result["vs_baseline"],
        }


# Singleton
iq_dashboard = IQDashboard()
