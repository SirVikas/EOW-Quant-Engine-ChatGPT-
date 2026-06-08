"""
PHOENIX OBSERVATORY-X — Unified Reporting, Knowledge, Archive & Intelligence Framework

Architecture:
  OX-1  registry.py            Universal Report Registry (URR)
  OX-1  scheduler.py           Report Scheduler
  OX-1  health_monitor.py      Report Health Monitor

  OX-2  relationship_engine.py Report Relationship Graph
  OX-2  lineage_tracker.py     Event Lineage Tracker

  OX-3  defect_engine.py       Defect Discovery Engine
  OX-3  inspector.py           PHOENIX Inspector (automated investigator)
  OX-3  recommendation_engine.py Recommendation Engine

  OX-4  ownership.py           Report Ownership, SLA & Version Lineage
  OX-4  truth_layer.py         Observed→Explained→Verified truth lifecycle
  OX-4  trust_engine.py        Recommendation Trust Scoring (5-factor)
  OX-4  nexus_bridge.py        IMRAF Integration Bridge

PHOENIX Institutional Stack:
  Layer 2  NEXUS        (Connectivity + Intelligence)
  Layer 3  OBSERVATORY-X (Observation)    ← THIS PACKAGE
  Layer 4  CORTEX       (Governance)      pending
"""
from core.observatory.registry              import report_registry
from core.observatory.scheduler             import report_scheduler
from core.observatory.health_monitor        import report_health_monitor
from core.observatory.relationship_engine   import report_relationship_engine
from core.observatory.lineage_tracker       import event_lineage_tracker
from core.observatory.defect_engine         import defect_engine
from core.observatory.inspector             import phoenix_inspector
from core.observatory.recommendation_engine import recommendation_engine
from core.observatory.ownership             import report_ownership_registry
from core.observatory.truth_layer           import observatory_truth_layer
from core.observatory.trust_engine          import recommendation_trust_engine

__all__ = [
    "report_registry",
    "report_scheduler",
    "report_health_monitor",
    "report_relationship_engine",
    "event_lineage_tracker",
    "defect_engine",
    "phoenix_inspector",
    "recommendation_engine",
    "report_ownership_registry",
    "observatory_truth_layer",
    "recommendation_trust_engine",
]
