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
        """
        ts = int(time.time() * 1000)

        # --- IMRAF ---
        imraf_scores: List[float] = []
        try:
            from core.institutional_memory.imraf_engine import imraf
            records = imraf.timeline(limit=2000)
            for rec in records:
                imraf_scores.append(self.score_fact(rec))
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
        try:
            from core.nexus.doae.doae_engine import doae
            report = doae.get_attribution_report()
            for attr in report.get("attributions", []):
                attribution_scores.append(self.score_attribution(attr))
        except Exception as exc:
            logger.warning("ConfidenceEngine.compute_nexus_confidence DOAE error: %s", exc)

        attribution_avg = (
            round(sum(attribution_scores) / len(attribution_scores), 4)
            if attribution_scores
            else 0.0
        )

        # Composite: imraf*0.4 + attribution*0.6
        composite = round(imraf_avg * 0.4 + attribution_avg * 0.6, 4)
        recommendation_ready = composite >= 0.65
        gap = round(max(0.0, 0.65 - composite), 4)

        return {
            "imraf_avg_confidence": imraf_avg,
            "imraf_by_level": by_level,
            "attribution_avg_confidence": attribution_avg,
            "nexus_composite_confidence": composite,
            "recommendation_ready": recommendation_ready,
            "gap_to_recommendation": gap,
            "ts": ts,
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
