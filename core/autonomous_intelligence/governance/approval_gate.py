"""FTD-AIL-001: Approval Gate — manages approve/reject/needs-more-evidence workflow."""
from __future__ import annotations
from datetime import datetime, timezone


VALID_TRANSITIONS = {
    "PENDING":              {"APPROVED", "REJECTED", "NEEDS_MORE_EVIDENCE"},
    "NEEDS_MORE_EVIDENCE":  {"APPROVED", "REJECTED"},
    "APPROVED":             set(),
    "REJECTED":             set(),
}


def apply_decision(finding_dict: dict, action: str, reason: str = "") -> dict:
    """
    Apply an approval decision to a finding dict (in-place update + return).
    action: 'APPROVED' | 'REJECTED' | 'NEEDS_MORE_EVIDENCE'
    Raises ValueError if transition is invalid.
    """
    current = finding_dict.get("status", "PENDING")
    allowed = VALID_TRANSITIONS.get(current, set())
    if action not in allowed:
        raise ValueError(f"Cannot transition {current} → {action}")

    now = datetime.now(timezone.utc).isoformat()
    finding_dict["status"] = action
    if action == "APPROVED":
        finding_dict["approved_at"] = now
    elif action == "REJECTED":
        finding_dict["rejected_at"] = now
        finding_dict["rejection_reason"] = reason
    return finding_dict
