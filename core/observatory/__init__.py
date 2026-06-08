"""
PHOENIX OBSERVATORY-X — OX-1 Foundation
Unified Reporting, Scheduling, and Health Monitoring Layer

Architecture:
  registry.py      — Universal Report Registry (URR): catalog of all known reports
  scheduler.py     — Report Scheduler: timely automated execution
  health_monitor.py — Report Health Monitor: staleness, errors, completeness

OX-1 scope: Visibility only — know what exists, when it ran, whether it's healthy.
No AI analysis, no diagnosis, no recommendations (those are OX-2 and OX-3).
"""
from core.observatory.registry       import report_registry
from core.observatory.scheduler      import report_scheduler
from core.observatory.health_monitor import report_health_monitor

__all__ = ["report_registry", "report_scheduler", "report_health_monitor"]
