"""Roadmap Registry — institutional multi-horizon roadmap tracking."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Roadmap:
    roadmap_id: str
    title: str
    horizon_label: str  # 1Y/3Y/5Y/10Y
    objectives: List[str]
    milestones: List[dict]
    status: str  # DRAFT/ACTIVE/COMPLETED/SUPERSEDED
    created_at: str
    last_updated: str


class RoadmapRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._roadmaps: dict[str, Roadmap] = {}
        self._counter = 0
        # Seed default roadmap
        self.create("PHOENIX 3-Year Evolution Plan", "3Y",
                    ["Achieve Operational Intelligence Maturity",
                     "Full Institutional Certification",
                     "Autonomous Advisory Intelligence"])
        with self._lock:
            first_id = list(self._roadmaps.keys())[0]
            self._roadmaps[first_id].status = "ACTIVE"

    def _next_id(self) -> str:
        self._counter += 1
        return f"RMP-{self._counter:03d}"

    def create(self, title: str, horizon_label: str, objectives: List[str]) -> str:
        with self._lock:
            roadmap_id = self._next_id()
            now = datetime.now(timezone.utc).isoformat()
            r = Roadmap(
                roadmap_id=roadmap_id,
                title=title,
                horizon_label=horizon_label,
                objectives=objectives,
                milestones=[],
                status="DRAFT",
                created_at=now,
                last_updated=now,
            )
            self._roadmaps[roadmap_id] = r
            return roadmap_id

    def add_milestone(self, roadmap_id: str, title: str, target_date_days: int,
                      description: str = "") -> bool:
        with self._lock:
            r = self._roadmaps.get(roadmap_id)
            if r is None:
                return False
            r.milestones.append({
                "title": title,
                "target_date_days": target_date_days,
                "description": description,
                "added_at": datetime.now(timezone.utc).isoformat(),
            })
            r.last_updated = datetime.now(timezone.utc).isoformat()
            return True

    def activate(self, roadmap_id: str) -> bool:
        with self._lock:
            r = self._roadmaps.get(roadmap_id)
            if r is None:
                return False
            r.status = "ACTIVE"
            r.last_updated = datetime.now(timezone.utc).isoformat()
            return True

    def complete(self, roadmap_id: str) -> bool:
        with self._lock:
            r = self._roadmaps.get(roadmap_id)
            if r is None:
                return False
            r.status = "COMPLETED"
            r.last_updated = datetime.now(timezone.utc).isoformat()
            return True

    def supersede(self, roadmap_id: str, new_roadmap_id: str) -> bool:
        with self._lock:
            r = self._roadmaps.get(roadmap_id)
            if r is None:
                return False
            r.status = "SUPERSEDED"
            r.last_updated = datetime.now(timezone.utc).isoformat()
            return True

    def active_roadmaps(self) -> List[dict]:
        with self._lock:
            return [asdict(r) for r in self._roadmaps.values() if r.status == "ACTIVE"]

    def roadmap_stats(self) -> dict:
        with self._lock:
            by_horizon: dict[str, int] = {}
            active = completed = 0
            for r in self._roadmaps.values():
                by_horizon[r.horizon_label] = by_horizon.get(r.horizon_label, 0) + 1
                if r.status == "ACTIVE":
                    active += 1
                elif r.status == "COMPLETED":
                    completed += 1
            return {
                "total": len(self._roadmaps),
                "active": active,
                "completed": completed,
                "by_horizon": by_horizon,
            }


roadmap_registry = RoadmapRegistry()
