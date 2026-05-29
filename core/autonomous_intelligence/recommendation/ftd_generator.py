"""FTD-AIL-001: FTD Generator — drafts FTD candidate documents for significant findings."""
from __future__ import annotations
from datetime import datetime, timezone
from core.autonomous_intelligence.analysis.finding_generator import Finding

_SIGNIFICANT = {"CRITICAL", "HIGH"}


def maybe_draft_ftd(finding: Finding) -> str | None:
    """Returns a draft FTD text if the finding is significant enough, else None."""
    if finding.severity not in _SIGNIFICANT:
        return None

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        f"# FTD CANDIDATE — AUTO-DRAFTED (PENDING HUMAN REVIEW)\n\n"
        f"**Lineage**: {finding.lineage_id}\n"
        f"**Date**: {now}\n"
        f"**Category**: {finding.category}\n"
        f"**Severity**: {finding.severity}\n\n"
        f"## Finding\n{finding.title}\n\n"
        f"## Evidence\n{finding.evidence}\n\n"
        f"## Recommendation\n{finding.recommendation}\n\n"
        f"## Source Reports\n{', '.join(finding.source_reports)}\n\n"
        f"---\n"
        f"*This document was auto-drafted by AIL. Human approval required before any action.*"
    )
