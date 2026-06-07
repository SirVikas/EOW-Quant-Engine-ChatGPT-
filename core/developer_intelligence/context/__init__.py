"""DIAL — Historical Context Engine (Module 1)."""
from core.developer_intelligence.dial_engine import dial

def get_context(module_name: str) -> dict:
    """Return full historical context for a module before modification."""
    return dial.get_historical_context(module_name)

def get_autonomous_context(module_name: str) -> dict:
    """Return AI-agent-ready context package for a module."""
    return dial.get_autonomous_context(module_name)
