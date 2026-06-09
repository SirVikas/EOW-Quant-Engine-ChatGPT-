"""Future Architecture Engine — proposed architectural visions for PHOENIX evolution."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class ArchitecturalVision:
    vision_id: str
    title: str
    description: str
    target_horizon_years: int
    capabilities_required: List[str]
    dependencies: List[str]
    feasibility: str  # HIGH/MEDIUM/LOW
    created_at: str


class FutureArchitectureEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._visions: dict[str, ArchitecturalVision] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"VIS-{self._counter:03d}"

    def propose_vision(self, title: str, description: str, horizon_years: int,
                       capabilities_required: List[str], dependencies: Optional[List[str]] = None,
                       feasibility: str = "MEDIUM") -> str:
        with self._lock:
            vision_id = self._next_id()
            v = ArchitecturalVision(
                vision_id=vision_id,
                title=title,
                description=description,
                target_horizon_years=horizon_years,
                capabilities_required=capabilities_required,
                dependencies=dependencies or [],
                feasibility=feasibility,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._visions[vision_id] = v
            return vision_id

    def all_visions(self, horizon_years: Optional[int] = None) -> List[dict]:
        with self._lock:
            visions = list(self._visions.values())
            if horizon_years is not None:
                visions = [v for v in visions if v.target_horizon_years == horizon_years]
            return [asdict(v) for v in visions]

    def feasible_visions(self) -> List[dict]:
        with self._lock:
            return [asdict(v) for v in self._visions.values() if v.feasibility == "HIGH"]

    def architecture_outlook(self) -> dict:
        with self._lock:
            by_horizon: dict[int, int] = {}
            high_feasibility = 0
            for v in self._visions.values():
                by_horizon[v.target_horizon_years] = by_horizon.get(v.target_horizon_years, 0) + 1
                if v.feasibility == "HIGH":
                    high_feasibility += 1
            # next milestone = vision with lowest horizon
            next_milestone = None
            if self._visions:
                soonest = min(self._visions.values(), key=lambda x: x.target_horizon_years)
                next_milestone = soonest.title
            return {
                "total_visions": len(self._visions),
                "by_horizon": by_horizon,
                "high_feasibility_count": high_feasibility,
                "next_milestone": next_milestone,
            }


future_architecture_engine = FutureArchitectureEngine()
