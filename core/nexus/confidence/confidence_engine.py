"""
FTD-NEXUS-100-PERCENT-001 Phase 5 — Confidence Engine

Unified confidence scoring across all NEXUS layers.
Every fact, decision, attribution, and recommendation must have
a confidence score before AEG can use it.

Confidence levels:
  VERIFIED (0.90-1.00): Confirmed by multiple sources or real data
  HIGH     (0.75-0.89): Single reliable source, recent, consistent
  MEDIUM   (0.50-0.74): Inferred or extracted, plausible
  LOW      (0.25-0.49): Synthetic, old, or single weak source
  MINIMAL  (0.00-0.24): Speculative, unverified, legacy
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

import logging
logger = logging.getLogger(__name__)

_CATEGORY_BASE: Dict[str, float] = {
    "VERIFIER":   0.90,
    "DEPLOYMENT": 0.85,
    "INCIDENT":   0.80,
    "DECISION":   0.75,
    "GOVERNANCE": 0.70,
    "KNOWLEDGE":  0.50,
}

_CONFIDENCE_TEXT_MAP: Dict[str, float] = {
    "LOW":    0.25,
    "MEDIUM": 0.60,
    "HIGH":   0.90,
}

_EDGE_WEIGHTS: Dict[str, float] = {
    "DEPENDS_ON":     0.80,
    "IMPLEMENTS":     0.85,
    "INTRODUCED_BY":  0.80,
    "CALLS":          0.70,
    "TESTS":          0.85,
    "CONFIGURES":     0.65,
    "SUPERSEDES":     0.75,
    "PRECEDES":       0.70,
    "BLOCKS":         0.75,
}


def _confidence_level(score: float) -> str:
    if score >= 0.90:
        return "VERIFIED"
    if score >= 0.75:
        return "HIGH"
    if score >= 0.50:
        return "MEDIUM"
    if score >= 0.25:
        return "LOW"
    return "MINIMAL"


class ConfidenceEngine:

    def score_fact(self, record: dict) -> float:
        """
        Score a single IMRAF record.

        Base score by category; bonuses for provenance and git_sha;
        penalties for missing tags and age.
        """
        category = (record.get("category") or "").upper()
        score = _CATEGORY_BASE.get(category, 0.50)

        # Provenance bonus
        data = record.get("data", {})
        if isinstance(data, dict):
            provenance = data.get("provenance", {})
            if provenance:
                score += 0.10
                if isinstance(provenance, dict) and provenance.get("git_sha"):
                    score += 0.05

        # No tags penalty
        tags = record.get("tags", [])
        if not tags:
            score -= 0.15

        # Age penalty: >6 months old
        # Use engine_ver as proxy for age; if it looks old relative to current version,
        # apply penalty. Since we can't reliably diff semver across all edge cases
        # without current version context, we check ts directly instead.
        ts = record.get("ts", 0) or 0
        if ts > 0:
            age_ms = int(time.time() * 1000) - ts
            six_months_ms = 6 * 30 * 24 * 60 * 60 * 1000
            if age_ms > six_months_ms:
                score -= 0.10

        return float(max(0.0, min(1.0, score)))

    def score_attribution(self, attribution_record: dict) -> float:
        """
        Score a DOAE attribution record.

        Maps confidence text field to base score, penalises synthetic data,
        and rewards large post-deployment sample sizes.
        """
        confidence_text = (attribution_record.get("confidence") or "LOW").upper()
        score = _CONFIDENCE_TEXT_MAP.get(confidence_text, 0.25)

        # Synthetic penalty — notes field contains "synthetic_baseline" when seeded at boot
        notes = (attribution_record.get("notes") or "").lower()
        if "synthetic" in notes:
            score -= 0.30

        # Large post-trade sample bonus
        post_trades = attribution_record.get("post_trades", 0) or 0
        if post_trades >= 200:
            score += 0.10

        return float(max(0.0, min(1.0, score)))

    def score_kge_edge(self, edge: dict) -> float:
        """Score a KGE edge by its relationship type."""
        relationship = (edge.get("relationship") or "").upper()
        return _EDGE_WEIGHTS.get(relationship, 0.50)

    def compute_nexus_confidence(self) -> dict:
        """
        Aggregate confidence report across IMRAF and DOAE.

        Fetches all IMRAF records and DOAE attributions, scores each,
        and returns composite metrics.

        Adaptive weighting: attribution weight scales from 0.3→0.6 based on how
        much attribution data is real (HIGH confidence) vs synthetic. When all
        attribution is synthetic, IMRAF carries more weight since it represents
        verified institutional memory.
        """
        ts = int(time.time() * 1000)

        # --- IMRAF ---
        imraf_scores: List[float] = []
        imraf_total = 0
        provenance_coverage = 0.0
        try:
            from core.institutional_memory.imraf_engine import imraf
            records = imraf.timeline(limit=2000)
            imraf_total = len(records)
            for rec in records:
                imraf_scores.append(self.score_fact(rec))
            prov_stats = imraf.get_provenance_stats()
            provenance_coverage = prov_stats.get("coverage_pct", 0.0)
        except Exception as exc:
            logger.warning("ConfidenceEngine.compute_nexus_confidence IMRAF error: %s", exc)

        imraf_avg = round(sum(imraf_scores) / len(imraf_scores), 4) if imraf_scores else 0.0

        by_level: Dict[str, int] = {
            "VERIFIED": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "MINIMAL": 0
        }
        for s in imraf_scores:
            by_level[_confidence_level(s)] += 1

        # --- DOAE ---
        attribution_scores: List[float] = []
        attrib_records: List[dict] = []
        try:
            from core.nexus.doae.doae_engine import doae
            report = doae.get_attribution_report()
            attrib_records = report.get("attributions", [])
            for attr in attrib_records:
                attribution_scores.append(self.score_attribution(attr))
        except Exception as exc:
            logger.warning("ConfidenceEngine.compute_nexus_confidence DOAE error: %s", exc)

        attribution_avg = (
            round(sum(attribution_scores) / len(attribution_scores), 4)
            if attribution_scores
            else 0.0
        )

        # Detect how much attribution is real vs synthetic.
        # HIGH confidence records indicate real post-trade data rather than seeded baselines.
        real_attribution_pct = (
            sum(1 for r in attrib_records if r.get("confidence") == "HIGH")
            / max(len(attrib_records), 1)
        )

        # Attribution weight scales 0.3→0.6 as real data fraction grows.
        # At 0% real data (all synthetic): attribution_weight=0.30, imraf_weight=0.70
        # At 100% real data: attribution_weight=0.60, imraf_weight=0.40
        attribution_weight = round(0.3 + real_attribution_pct * 0.3, 4)
        imraf_weight = round(1.0 - attribution_weight, 4)

        # Provenance coverage bonus: +0.05 if ≥90%
        provenance_bonus = 0.05 if provenance_coverage >= 90.0 else 0.0
        # Memory size bonus: +0.03 if ≥500 IMRAF records
        size_bonus = 0.03 if imraf_total >= 500 else 0.0

        base_composite = imraf_avg * imraf_weight + attribution_avg * attribution_weight
        composite = round(min(1.0, base_composite + provenance_bonus + size_bonus), 4)
        recommendation_ready = composite >= 0.65
        gap = round(max(0.0, 0.65 - composite), 4)

        breakdown = (
            f"imraf={imraf_avg:.3f}×{imraf_weight:.2f} + "
            f"attr={attribution_avg:.3f}×{attribution_weight:.2f} + "
            f"bonuses={provenance_bonus + size_bonus:.3f}"
        )

        return {
            "imraf_avg_confidence": imraf_avg,
            "imraf_by_level": by_level,
            "imraf_total": imraf_total,
            "attribution_avg_confidence": attribution_avg,
            "real_attribution_pct": round(real_attribution_pct, 4),
            "attribution_weight": attribution_weight,
            "imraf_weight": imraf_weight,
            "provenance_coverage_pct": provenance_coverage,
            "provenance_bonus": provenance_bonus,
            "size_bonus": size_bonus,
            "nexus_composite_confidence": composite,
            "recommendation_ready": recommendation_ready,
            "gap_to_recommendation": gap,
            "breakdown": breakdown,
            "ts": ts,
        }

    def compute_nexus_self_awareness(self) -> dict:
        """
        Self-Awareness Score — "How well does NEXUS know what it knows?"

        Five dimensions (each 0-100) combined into a weighted composite:
          provenance (0.25) — % of facts with traceable provenance
          consistency (0.20) — fewer governance contradictions = more consistent
          coverage (0.20) — breadth of institutional facts indexed
          confidence_distribution (0.20) — fraction of facts that are VERIFIED or HIGH
          recency (0.15) — fraction of records from current version era
        """
        ts = int(time.time() * 1000)

        # --- Provenance score ---
        provenance_score = 0.0
        try:
            from core.institutional_memory.imraf_engine import imraf
            prov = imraf.get_provenance_stats()
            provenance_score = min(100.0, prov.get("coverage_pct", 0.0))
        except Exception as exc:
            logger.warning("compute_nexus_self_awareness provenance error: %s", exc)

        # --- Consistency score ---
        consistency_score = 100.0
        try:
            from core.nexus.governance_intelligence.governance_intelligence import (
                GovernanceIntelligenceEngine,
            )
            gov = GovernanceIntelligenceEngine()
            contradictions = gov.detect_real_contradictions()
            # Each contradiction reduces score by 20 points, floored at 0
            consistency_score = max(0.0, 100.0 - len(contradictions) * 20.0)
        except Exception as exc:
            logger.warning("compute_nexus_self_awareness consistency error: %s", exc)

        # --- Coverage score ---
        coverage_score = 0.0
        try:
            from core.institutional_memory.imraf_engine import imraf
            stats = imraf.get_stats()
            total_records = stats.get("total_records", 0)
            coverage_score = min(100.0, total_records / 10.0)
        except Exception as exc:
            logger.warning("compute_nexus_self_awareness coverage error: %s", exc)

        # --- Confidence distribution score ---
        confidence_distribution_score = 0.0
        try:
            from core.institutional_memory.imraf_engine import imraf
            records = imraf.timeline(limit=2000)
            if records:
                high_conf_count = sum(
                    1 for r in records
                    if self.score_fact(r) >= 0.75  # VERIFIED or HIGH threshold
                )
                confidence_distribution_score = round(high_conf_count / len(records) * 100, 2)
        except Exception as exc:
            logger.warning("compute_nexus_self_awareness conf_dist error: %s", exc)

        # --- Recency score ---
        # Records from within the last 6 months are considered "current era"
        recency_score = 0.0
        try:
            from core.institutional_memory.imraf_engine import imraf
            records = imraf.timeline(limit=2000)
            if records:
                now_ms = int(time.time() * 1000)
                six_months_ms = 6 * 30 * 24 * 60 * 60 * 1000
                recent_count = sum(
                    1 for r in records
                    if (now_ms - (r.get("ts") or 0)) <= six_months_ms
                )
                recency_score = round(recent_count / len(records) * 100, 2)
        except Exception as exc:
            logger.warning("compute_nexus_self_awareness recency error: %s", exc)

        self_awareness_score = round(
            provenance_score * 0.25
            + consistency_score * 0.20
            + coverage_score * 0.20
            + confidence_distribution_score * 0.20
            + recency_score * 0.15,
            2,
        )

        if self_awareness_score >= 80:
            interpretation = "HIGH"
        elif self_awareness_score >= 60:
            interpretation = "MEDIUM"
        else:
            interpretation = "LOW"

        return {
            "self_awareness_score": self_awareness_score,
            "provenance_score": round(provenance_score, 2),
            "consistency_score": round(consistency_score, 2),
            "coverage_score": round(coverage_score, 2),
            "confidence_distribution_score": round(confidence_distribution_score, 2),
            "recency_score": round(recency_score, 2),
            "interpretation": interpretation,
            "gap_to_high": round(max(0.0, 80.0 - self_awareness_score), 2),
            "ts": ts,
        }

    def compute_nexus_brain_score(self) -> dict:
        """
        Brain Score — "Is NEXUS ready to be PHOENIX's Institutional Brain?"

        Single composite 0-100 across 8 dimensions representing the full
        institutional intelligence capability of NEXUS.
        """
        ts = int(time.time() * 1000)

        # Gather raw values for each dimension
        total_records = 0
        provenance_pct = 0.0
        kge_intelligence_score = 0.0
        attribution_avg = 0.0
        governance_health_score = 100.0
        nexus_composite = 0.0
        hke_source_count = 0
        aeg_pass_count = 0

        try:
            from core.institutional_memory.imraf_engine import imraf
            stats = imraf.get_stats()
            total_records = stats.get("total_records", 0)
            prov = imraf.get_provenance_stats()
            provenance_pct = prov.get("coverage_pct", 0.0)
        except Exception as exc:
            logger.warning("compute_nexus_brain_score IMRAF error: %s", exc)

        try:
            from core.nexus.kge.kge_engine import kge
            intel = kge.relationship_intelligence_score()
            kge_intelligence_score = intel.get("intelligence_score", 0.0)
        except Exception as exc:
            logger.warning("compute_nexus_brain_score KGE error: %s", exc)

        try:
            from core.nexus.doae.doae_engine import doae
            report = doae.get_attribution_report()
            attribs = report.get("attributions", [])
            if attribs:
                scores = [self.score_attribution(a) for a in attribs]
                attribution_avg = sum(scores) / len(scores)
        except Exception as exc:
            logger.warning("compute_nexus_brain_score DOAE error: %s", exc)

        try:
            from core.nexus.governance_intelligence.governance_intelligence import (
                GovernanceIntelligenceEngine,
            )
            gov = GovernanceIntelligenceEngine()
            contradictions = gov.detect_real_contradictions()
            governance_health_score = max(0.0, 100.0 - len(contradictions) * 20.0)
        except Exception as exc:
            logger.warning("compute_nexus_brain_score governance error: %s", exc)

        try:
            conf_report = self.compute_nexus_confidence()
            nexus_composite = conf_report.get("nexus_composite_confidence", 0.0)
        except Exception as exc:
            logger.warning("compute_nexus_brain_score confidence error: %s", exc)

        try:
            from core.nexus.hke.hke_engine import hke
            hke_stats = hke.get_stats()
            hke_source_count = len(hke_stats.get("sources", []))
        except Exception as exc:
            logger.warning("compute_nexus_brain_score HKE error: %s", exc)

        try:
            from core.nexus.aeg_readiness.aeg_readiness_engine import aeg_readiness
            audit = aeg_readiness.run_readiness_audit()
            aeg_pass_count = audit.get("pass_count", 0)
        except Exception as exc:
            logger.warning("compute_nexus_brain_score AEG error: %s", exc)

        components = {
            "memory": round(min(100.0, total_records / 5.0), 2),
            "provenance": round(provenance_pct, 2),
            "knowledge_graph": round(kge_intelligence_score, 2),
            "attribution": round(min(100.0, attribution_avg * 150.0), 2),
            "governance": round(governance_health_score, 2),
            "confidence": round(min(100.0, nexus_composite * 150.0), 2),
            "historical": round(min(100.0, hke_source_count * 10.0), 2),
            "aeg_readiness": round(aeg_pass_count / 8.0 * 100.0, 2),
        }

        weights: Dict[str, float] = {
            "memory": 0.15,
            "provenance": 0.15,
            "knowledge_graph": 0.15,
            "attribution": 0.10,
            "governance": 0.15,
            "confidence": 0.10,
            "historical": 0.10,
            "aeg_readiness": 0.10,
        }

        brain_score = round(
            sum(components[k] * weights[k] for k in weights), 2
        )

        if brain_score >= 90:
            grade = "A"
            interpretation = "NEXUS is functioning as PHOENIX's Institutional Brain"
        elif brain_score >= 80:
            grade = "B"
            interpretation = "NEXUS is approaching full Institutional Brain capability"
        elif brain_score >= 70:
            grade = "C"
            interpretation = "NEXUS is a mature Institutional Intelligence Platform"
        elif brain_score >= 60:
            grade = "D"
            interpretation = "NEXUS is an operational Knowledge Platform"
        else:
            grade = "F"
            interpretation = "NEXUS is still in development"

        blockers = [k for k, v in components.items() if v < 60.0]

        # Determine what will push score to the next grade threshold
        grade_thresholds = [("A", 90), ("B", 80), ("C", 70), ("D", 60)]
        next_milestone = "Maintain score to retain grade A"
        for g, threshold in grade_thresholds:
            if brain_score < threshold:
                gap = round(threshold - brain_score, 2)
                weakest = min(components, key=components.get)
                next_milestone = (
                    f"+{gap} points to grade {g} — "
                    f"focus on {weakest} (currently {components[weakest]:.1f}/100)"
                )
                break

        return {
            "brain_score": brain_score,
            "components": components,
            "weights": weights,
            "grade": grade,
            "interpretation": interpretation,
            "blockers": blockers,
            "next_milestone": next_milestone,
            "ts": ts,
        }

    def compute_confidence_trajectory(self) -> dict:
        """
        Project confidence trajectory toward 0.80+ based on current velocity
        and known improvement levers.

        Models each lever's marginal contribution to composite confidence
        given the adaptive weighting formula in compute_nexus_confidence().
        """
        conf = self.compute_nexus_confidence()
        current = conf.get("nexus_composite_confidence", 0.0)
        target = 0.80
        gap = round(target - current, 4)

        real_pct = conf.get("real_attribution_pct", 0.0)
        imraf_avg = conf.get("imraf_avg_confidence", 0.0)
        attribution_avg = conf.get("attribution_avg_confidence", 0.0)
        provenance_pct = conf.get("provenance_coverage_pct", 0.0)

        # KGE connectivity — read from kge engine
        kge_score = 0.0
        try:
            from core.nexus.kge.kge_engine import kge
            intel = kge.relationship_intelligence_score()
            kge_score = intel.get("intelligence_score", 0.0)
        except Exception:
            pass

        # --- Lever analysis ---
        # real_attribution_pct: drives attribution_weight from 0.3→0.6 and removes synthetic_penalty.
        # Estimated impact: shifting from current real_pct to 100% raises composite ~0.08-0.13
        real_attr_impact = round(0.30 * (1.0 - real_pct) * (attribution_avg - imraf_avg if attribution_avg > imraf_avg else 0.10), 4)
        real_attr_impact = max(real_attr_impact, 0.08)  # floor: minimum raises composite ~0.08

        # imraf_avg_confidence: directly scales the IMRAF component
        # Moving from current imraf_avg to 0.85 (HIGH level) would add imraf_weight*(0.85-imraf_avg)
        imraf_weight_now = conf.get("imraf_weight", 0.70)
        imraf_avg_impact = round(imraf_weight_now * max(0.0, 0.85 - imraf_avg), 4)

        # synthetic_penalty: already captured in real_attribution_pct lever — low incremental
        synthetic_penalty_impact = round(0.05 * (1.0 - real_pct), 4)

        # kge_connectivity: already at 100 → near-zero incremental impact
        kge_impact = round(max(0.0, 0.02 * (1.0 - kge_score / 100.0)), 4)

        # provenance_coverage: already 97%+ → near-zero incremental impact
        provenance_impact = round(max(0.0, 0.05 * max(0.0, 1.0 - provenance_pct / 100.0)), 4)

        levers = [
            {
                "lever": "real_attribution_pct",
                "current_value": round(real_pct, 4),
                "impact_on_confidence": real_attr_impact,
                "how_to_improve": "Accumulate live trades so DOAE generates HIGH-confidence post-trade snapshots",
                "time_dependent": True,
            },
            {
                "lever": "imraf_avg_confidence",
                "current_value": round(imraf_avg, 4),
                "impact_on_confidence": imraf_avg_impact,
                "how_to_improve": "Add VERIFIER and DEPLOYMENT records with provenance+git_sha to raise average",
                "time_dependent": False,
            },
            {
                "lever": "synthetic_penalty",
                "current_value": round(1.0 - real_pct, 4),
                "impact_on_confidence": synthetic_penalty_impact,
                "how_to_improve": "Reduced automatically as real_attribution_pct grows via live trades",
                "time_dependent": True,
            },
            {
                "lever": "kge_connectivity",
                "current_value": round(kge_score, 1),
                "impact_on_confidence": kge_impact,
                "how_to_improve": "Already near maximum — minimal incremental gain",
                "time_dependent": False,
            },
            {
                "lever": "provenance_coverage",
                "current_value": round(provenance_pct, 2),
                "impact_on_confidence": provenance_impact,
                "how_to_improve": "Already 97%+ — minimal incremental gain",
                "time_dependent": False,
            },
        ]
        # Sort by impact descending
        levers.sort(key=lambda x: x["impact_on_confidence"], reverse=True)

        # --- Milestone projections ---
        # Rough model: 50 trades → ~20% real attribution → raises composite by ~real_attr_impact/5
        def _trades_for_confidence(conf_target: float) -> int:
            if current >= conf_target:
                return 0
            needed_gain = conf_target - current
            gain_per_50_trades = real_attr_impact / 5.0 if real_attr_impact > 0 else 0.01
            return int((needed_gain / gain_per_50_trades) * 50)

        milestones = [
            {
                "target": 0.70,
                "status": "REACHED" if current >= 0.70 else "PENDING",
                "estimated_trades_needed": _trades_for_confidence(0.70),
            },
            {
                "target": 0.75,
                "status": "REACHED" if current >= 0.75 else "PENDING",
                "estimated_trades_needed": _trades_for_confidence(0.75),
            },
            {
                "target": 0.80,
                "status": "REACHED" if current >= 0.80 else "PENDING",
                "estimated_trades_needed": _trades_for_confidence(0.80),
            },
        ]

        est_trades_to_080 = _trades_for_confidence(0.80)
        bottleneck = (
            "real_attribution_pct is near zero — confidence is dominated by synthetic DOAE data; "
            "accumulate live trades to unlock full confidence range"
            if real_pct < 0.10
            else "imraf_avg_confidence is the primary limiter — add high-confidence IMRAF records"
            if imraf_avg_impact > real_attr_impact
            else "real_attribution_pct — live trade accumulation required to reach 0.80 target"
        )

        return {
            "current": current,
            "target": target,
            "gap": gap,
            "levers": levers,
            "projected_milestones": milestones,
            "estimated_trades_to_0_80": est_trades_to_080,
            "bottleneck": bottleneck,
        }

    def get_recommendation_confidence_floor(self) -> dict:
        """
        Return the minimum confidence required before a recommendation is trustworthy,
        and whether current state meets that floor.

        ADVISORY floor: 0.65 — can generate recommendations, not guaranteed
        TRUSTED floor:  0.75 — recommendations are institutionally credible
        HIGH_TRUST floor: 0.85 — recommendations can be acted on with minimal review
        """
        conf = self.compute_nexus_confidence()
        current = conf.get("nexus_composite_confidence", 0.0)

        advisory_floor = 0.65
        trusted_floor = 0.75
        high_trust_floor = 0.85

        advisory_met = current >= advisory_floor
        trusted_met = current >= trusted_floor
        high_trust_met = current >= high_trust_floor

        if high_trust_met:
            current_tier = "HIGH_TRUST"
        elif trusted_met:
            current_tier = "TRUSTED"
        elif advisory_met:
            current_tier = "ADVISORY"
        else:
            current_tier = "BELOW_ADVISORY"

        return {
            "current_confidence": current,
            "advisory": {
                "floor": advisory_floor,
                "met": advisory_met,
                "description": "Can generate recommendations, not guaranteed",
            },
            "trusted": {
                "floor": trusted_floor,
                "met": trusted_met,
                "description": "Recommendations are institutionally credible",
            },
            "high_trust": {
                "floor": high_trust_floor,
                "met": high_trust_met,
                "description": "Recommendations can be acted on with minimal review",
            },
            "current_tier": current_tier,
            "gap_to_trusted": round(max(0.0, trusted_floor - current), 4),
            "gap_to_high_trust": round(max(0.0, high_trust_floor - current), 4),
        }

    def get_low_confidence_facts(self, threshold: float = 0.5, limit: int = 20) -> list:
        """Return IMRAF records whose confidence score falls below threshold."""
        results: List[dict] = []
        try:
            from core.institutional_memory.imraf_engine import imraf
            records = imraf.timeline(limit=2000)
            for rec in records:
                score = self.score_fact(rec)
                if score < threshold:
                    results.append({**rec, "_confidence_score": score})
                    if len(results) >= limit:
                        break
        except Exception as exc:
            logger.warning("ConfidenceEngine.get_low_confidence_facts error: %s", exc)
        return results


# Singleton
confidence_engine = ConfidenceEngine()
