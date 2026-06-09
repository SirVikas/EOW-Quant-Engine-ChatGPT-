"""PCCP — Global Priority Manager: ranks and orders all active problems/tasks."""
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class PriorityItem:
    item_id: str
    title: str
    source_layer: str
    impact: float
    confidence: float
    urgency: float
    implementation_cost: float
    priority_score: float
    status: str
    created_at: float


class GlobalPriorityManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._items: List[PriorityItem] = []
        self._auto_seed()

    def add_item(self, title: str, source_layer: str, impact: float, confidence: float,
                 urgency: float, implementation_cost: float) -> dict:
        with self._lock:
            score = (impact * confidence * urgency) / max(1.0, implementation_cost)
            item = PriorityItem(
                item_id=str(uuid.uuid4()),
                title=title,
                source_layer=source_layer,
                impact=impact,
                confidence=confidence,
                urgency=urgency,
                implementation_cost=implementation_cost,
                priority_score=round(score, 4),
                status="QUEUED",
                created_at=time.time(),
            )
            self._items.append(item)
            return asdict(item)

    def get_ranked_list(self, status_filter: str = None) -> List[dict]:
        with self._lock:
            items = self._items
            if status_filter:
                items = [i for i in items if i.status == status_filter]
            return [asdict(i) for i in sorted(items, key=lambda x: x.priority_score, reverse=True)]

    def update_status(self, item_id: str, status: str) -> dict:
        with self._lock:
            for item in self._items:
                if item.item_id == item_id:
                    item.status = status
                    return {"updated": item_id, "status": status}
            return {"error": f"Item {item_id} not found"}

    def top_priority(self) -> Optional[dict]:
        with self._lock:
            queued = [i for i in self._items if i.status == "QUEUED"]
            if not queued:
                return None
            return asdict(max(queued, key=lambda x: x.priority_score))

    def priority_summary(self) -> dict:
        with self._lock:
            total = len(self._items)
            queued = sum(1 for i in self._items if i.status == "QUEUED")
            in_progress = sum(1 for i in self._items if i.status == "IN_PROGRESS")
            resolved = sum(1 for i in self._items if i.status == "RESOLVED")
            ranked = sorted(self._items, key=lambda x: x.priority_score, reverse=True)
            top3 = [asdict(i) for i in ranked[:3]]
            return {
                "total_items": total,
                "queued": queued,
                "in_progress": in_progress,
                "resolved": resolved,
                "top_3": top3,
            }

    def _auto_seed(self):
        try:
            from core.pcao.risk_office import risk_office
            issues = getattr(risk_office, "open_issues", lambda: [])()
            for issue in (issues or [])[:3]:
                self.add_item(
                    title=str(issue.get("title", "PCAO Risk Issue")),
                    source_layer="PCAO",
                    impact=7.0, confidence=0.7, urgency=6.0, implementation_cost=4.0,
                )
        except Exception:
            pass

        try:
            from core.nexus.institutional_health_index import institutional_health_index
            report = institutional_health_index.health_report()
            score = report.get("overall_score", 100)
            if score < 70:
                self.add_item(
                    title=f"Institutional Health Low: {score}",
                    source_layer="NEXUS",
                    impact=8.0, confidence=0.8, urgency=7.0, implementation_cost=5.0,
                )
        except Exception:
            pass


global_priority_manager = GlobalPriorityManager()
