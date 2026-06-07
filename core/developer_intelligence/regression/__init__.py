"""DIAL — Regression Risk Engine (Module 3)."""
from core.developer_intelligence.dial_engine import dial

def check_risk(file_or_component: str) -> dict:
    """Assess regression risk before modifying a component."""
    return dial.check_regression_risk(file_or_component)
