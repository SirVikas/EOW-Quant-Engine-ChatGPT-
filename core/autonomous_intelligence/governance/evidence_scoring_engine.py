"""
FTD-AIL-001: Evidence Scoring Engine.
Scores each finding 0-100 across 5 dimensions.
"""
from __future__ import annotations
import time
from datetime import datetime, timezone
from core.autonomous_intelligence.analysis.finding_generator import Finding


def score_finding(finding: Finding, collection_ts: float | None = None) -> int:
    """
    Score a finding 0-100:
      confidence_score × 30
      sample_size adequacy × 25
      data_freshness × 20
      economic_impact × 15
      corroboration (multiple sources) × 10
    """
    score = 0.0

    # Confidence (0-30)
    score += min(finding.confidence_score, 1.0) * 30

    # Sample size adequacy (0-25): 1000+ = full, 100+ = half, < 100 = quarter
    if finding.sample_size >= 1000:
        score += 25
    elif finding.sample_size >= 100:
        score += 12.5
    elif finding.sample_size >= 10:
        score += 6

    # Data freshness (0-20): collection_ts vs now
    if collection_ts is not None:
        age_sec = time.time() - collection_ts
        if age_sec < 7200:     # < 2 hr
            score += 20
        elif age_sec < 21600:  # < 6 hr
            score += 10

    # Economic impact (0-15)
    impact_pts = {"HIGH": 15, "MEDIUM": 9, "LOW": 4, "UNKNOWN": 0}
    score += impact_pts.get(finding.economic_impact_est, 0)

    # Corroboration — multiple source reports (0-10)
    if len(finding.source_reports) >= 2:
        score += 10
    elif len(finding.source_reports) == 1:
        score += 5

    return min(100, int(round(score)))
