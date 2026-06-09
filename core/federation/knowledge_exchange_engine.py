"""Knowledge Exchange Engine — manages knowledge sharing between federation nodes."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class KnowledgeExchange:
    exchange_id: str
    source_node: str
    topic: str
    knowledge_summary: str
    exchanged_at: datetime = field(default_factory=datetime.utcnow)


class KnowledgeExchangeEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._exchanges: List[KnowledgeExchange] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"KX-{self._counter:03d}"

    def record_exchange(self, source_node: str, topic: str, knowledge_summary: str) -> KnowledgeExchange:
        with self._lock:
            exc = KnowledgeExchange(self._next_id(), source_node, topic, knowledge_summary)
            self._exchanges.append(exc)
            return exc

    def recent_exchanges(self, limit: int = 20) -> List[dict]:
        with self._lock:
            return [vars(e) for e in self._exchanges[-limit:]]

    def exchange_stats(self) -> dict:
        with self._lock:
            topics: dict = {}
            for e in self._exchanges:
                topics[e.topic] = topics.get(e.topic, 0) + 1
            return {"total_exchanges": len(self._exchanges), "topics": topics}


knowledge_exchange_engine = KnowledgeExchangeEngine()
