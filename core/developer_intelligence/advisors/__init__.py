"""DIAL — Engineering Decision Assistant + Similar Issue Detection (Modules 2, 11)."""
from core.developer_intelligence.dial_engine import dial

def find_similar(error_description: str, limit: int = 5) -> list:
    """Search institutional memory for historically similar failures."""
    return dial.find_similar_issues(error_description, limit=limit)

def get_recommendation(query: str) -> dict:
    """Recommend based on historical precedent for an engineering question."""
    return dial.get_engineering_recommendation(query)

def get_architecture_rationale(component: str) -> list:
    """Retrieve why architectural decisions were made for a component."""
    return dial.get_architecture_rationale(component)

def get_ftd_knowledge(ftd_id: str) -> list:
    """Retrieve all IMRAF records related to a specific FTD."""
    return dial.get_ftd_knowledge(ftd_id)
