"""DIAL — Code Change Memory Engine + Lessons Learned (Modules 9, 10)."""
from core.developer_intelligence.dial_engine import dial

def record_change(module: str, description: str, reason: str, expected_outcome: str,
                  author: str = "claude") -> int:
    """Record an engineering change for long-term traceability."""
    return dial.record_code_change(module, description, reason, expected_outcome, author)

def extract_lesson(issue: str, root_cause: str, fix: str, prevention: str,
                   related_components: list = None) -> int:
    """Convert an incident into reusable institutional knowledge."""
    return dial.extract_lesson(issue, root_cause, fix, prevention, related_components or [])
