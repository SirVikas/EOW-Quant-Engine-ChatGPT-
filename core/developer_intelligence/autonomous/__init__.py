"""DIAL — Autonomous Developer Context Engine (Module 8)."""
from core.developer_intelligence.dial_engine import dial

def get_context_for_agent(module_name: str) -> dict:
    """
    Return a structured context package for AI coding agents.
    Combines historical context, regression risk, architecture rationale,
    and dependency impact in a single call.
    """
    return dial.get_autonomous_context(module_name)
