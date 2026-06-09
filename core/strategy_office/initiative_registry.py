"""Initiative Registry — registry of strategic initiatives."""
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Initiative:
    init_id: str
    title: str
    strategic_theme: str
    owner: str
    status: str
    priority: str
    start_date: datetime
    target_completion: datetime
    progress_pct: float


class InitiativeRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._initiatives: dict[str, Initiative] = {}
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"INI-{self._counter:03d}"

    def _seed(self):
        seeds = [
            ("Knowledge Graph Expansion", "Institutional Intelligence", "System", "P1", 180),
            ("Historical Knowledge Extraction", "Memory Architecture", "System", "P2", 365),
            ("Autonomous Engineering Governance", "Governance Automation", "System", "P3", 540),
        ]
        for title, theme, owner, priority, days in seeds:
            self._create_internal(title, theme, owner, priority, days)

    def _create_internal(self, title: str, strategic_theme: str, owner: str,
                         priority: str, target_completion_days: int) -> Initiative:
        now = datetime.utcnow()
        init = Initiative(
            init_id=self._next_id(),
            title=title,
            strategic_theme=strategic_theme,
            owner=owner,
            status="PLANNING",
            priority=priority,
            start_date=now,
            target_completion=now + timedelta(days=target_completion_days),
            progress_pct=0.0,
        )
        self._initiatives[init.init_id] = init
        return init

    def register(self, title: str, strategic_theme: str, owner: str,
                 priority: str, target_completion_days: int) -> Initiative:
        with self._lock:
            return self._create_internal(title, strategic_theme, owner, priority, target_completion_days)

    def update_progress(self, init_id: str, progress_pct: float) -> Optional[Initiative]:
        with self._lock:
            init = self._initiatives.get(init_id)
            if init:
                init.progress_pct = max(0.0, min(100.0, progress_pct))
                if init.progress_pct >= 100.0:
                    init.status = "COMPLETED"
                elif init.status == "PLANNING":
                    init.status = "EXECUTING"
            return init

    def active_initiatives(self) -> list[dict]:
        with self._lock:
            return [
                {"init_id": i.init_id, "title": i.title, "strategic_theme": i.strategic_theme,
                 "owner": i.owner, "status": i.status, "priority": i.priority,
                 "progress_pct": i.progress_pct,
                 "target_completion": i.target_completion.isoformat()}
                for i in self._initiatives.values()
                if i.status not in ("COMPLETED", "CANCELLED")
            ]

    def initiative_summary(self) -> dict:
        with self._lock:
            by_status: dict[str, int] = {}
            for i in self._initiatives.values():
                by_status[i.status] = by_status.get(i.status, 0) + 1
            return {"total": len(self._initiatives), "by_status": by_status}


initiative_registry = InitiativeRegistry()
