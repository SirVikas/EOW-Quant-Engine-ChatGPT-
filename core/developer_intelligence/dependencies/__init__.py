"""DIAL — Dependency Impact Analyzer (Module 5)."""
from core.developer_intelligence.dial_engine import dial

def analyze_impact(component: str) -> dict:
    """Identify downstream modules affected by a change and historical breakages."""
    return dial.analyze_dependency_impact(component)
