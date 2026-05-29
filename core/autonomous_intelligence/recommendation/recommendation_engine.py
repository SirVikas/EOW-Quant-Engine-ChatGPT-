"""FTD-AIL-001: Recommendation Engine — converts findings into structured recommendations."""
from __future__ import annotations
from core.autonomous_intelligence.analysis.finding_generator import Finding


def enrich_recommendation(finding: Finding) -> Finding:
    """Add structured context to finding recommendation. Returns modified finding."""
    severity_prefix = {
        "CRITICAL": "URGENT: ",
        "HIGH": "ACTION REQUIRED: ",
        "MEDIUM": "REVIEW: ",
        "LOW": "MONITOR: ",
        "INFO": "FYI: ",
    }.get(finding.severity, "")

    if not finding.recommendation.startswith(severity_prefix):
        finding.recommendation = severity_prefix + finding.recommendation
    return finding
