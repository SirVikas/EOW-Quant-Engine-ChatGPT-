"""PCCP — Intelligence Bus: event-driven pub/sub for inter-layer communication."""
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Dict


@dataclass
class BusEvent:
    event_id: str
    source_layer: str
    event_type: str
    payload: dict
    timestamp: float
    consumed_by: List[str] = field(default_factory=list)


class IntelligenceBus:
    def __init__(self):
        self._lock = threading.RLock()
        self._events: List[BusEvent] = []
        self._subscriptions: Dict[str, List[str]] = {}
        self._total_published = 0

    def publish(self, source_layer: str, event_type: str, payload: dict) -> str:
        with self._lock:
            event_id = str(uuid.uuid4())
            ev = BusEvent(
                event_id=event_id,
                source_layer=source_layer,
                event_type=event_type,
                payload=payload,
                timestamp=time.time(),
            )
            self._events.append(ev)
            if len(self._events) > 1000:
                self._events = self._events[-1000:]
            self._total_published += 1
            return event_id

    def subscribe(self, layer_id: str, event_types: List[str]):
        with self._lock:
            existing = self._subscriptions.get(layer_id, [])
            for et in event_types:
                if et not in existing:
                    existing.append(et)
            self._subscriptions[layer_id] = existing
            return {"subscribed": layer_id, "event_types": existing}

    def consume(self, layer_id: str, limit: int = 50) -> List[dict]:
        with self._lock:
            subscribed = self._subscriptions.get(layer_id, [])
            result = []
            for ev in self._events:
                if layer_id in ev.consumed_by:
                    continue
                if subscribed and ev.event_type not in subscribed:
                    continue
                ev.consumed_by.append(layer_id)
                result.append(asdict(ev))
                if len(result) >= limit:
                    break
            return result

    def recent_events(self, limit: int = 20) -> List[dict]:
        with self._lock:
            return [asdict(e) for e in self._events[-limit:]]

    def bus_stats(self) -> dict:
        with self._lock:
            event_types = list({e.event_type for e in self._events})
            last_ts = self._events[-1].timestamp if self._events else None
            return {
                "total_published": self._total_published,
                "total_subscriptions": len(self._subscriptions),
                "event_types_seen": event_types,
                "last_event_at": last_ts,
            }


intelligence_bus = IntelligenceBus()
