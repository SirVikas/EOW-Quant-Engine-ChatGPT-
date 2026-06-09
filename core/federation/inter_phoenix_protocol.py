"""Inter-PHOENIX Protocol — protocol for inter-node communication."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


MessageType = Literal["KNOWLEDGE_SHARE", "GOVERNANCE_SYNC", "ALERT", "HEARTBEAT"]


@dataclass
class ProtocolMessage:
    message_id: str
    from_node: str
    to_node: str
    message_type: MessageType
    payload: dict
    sent_at: datetime = field(default_factory=datetime.utcnow)


class InterPhoenixProtocol:
    def __init__(self):
        self._lock = threading.RLock()
        self._messages: List[ProtocolMessage] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"MSG-{self._counter:03d}"

    def send_message(self, from_node: str, to_node: str, message_type: MessageType, payload: dict) -> ProtocolMessage:
        with self._lock:
            msg = ProtocolMessage(self._next_id(), from_node, to_node, message_type, payload)
            self._messages.append(msg)
            return msg

    def messages_for(self, node_id: str) -> List[dict]:
        with self._lock:
            return [vars(m) for m in self._messages if m.to_node == node_id or m.from_node == node_id]

    def protocol_stats(self) -> dict:
        with self._lock:
            by_type: dict = {}
            for m in self._messages:
                by_type[m.message_type] = by_type.get(m.message_type, 0) + 1
            return {"total_messages": len(self._messages), "by_type": by_type}


inter_phoenix_protocol = InterPhoenixProtocol()
