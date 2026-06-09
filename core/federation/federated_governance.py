"""Federated Governance — master federation engine."""
import threading


class FederatedGovernance:
    def __init__(self):
        self._lock = threading.RLock()

    def federation_status(self) -> dict:
        from core.federation.federation_registry import federation_registry
        from core.federation.knowledge_exchange_engine import knowledge_exchange_engine
        from core.federation.inter_phoenix_protocol import inter_phoenix_protocol
        with self._lock:
            summary = federation_registry.federation_summary()
            exchange_stats = knowledge_exchange_engine.exchange_stats()
            proto_stats = inter_phoenix_protocol.protocol_stats()
            active = len(federation_registry.active_nodes())
            protocol_health = "HEALTHY" if proto_stats["total_messages"] >= 0 else "DEGRADED"
            return {
                "total_nodes": summary["total_nodes"],
                "active_nodes": active,
                "knowledge_exchanges": exchange_stats["total_exchanges"],
                "protocol_health": protocol_health,
            }

    def one_liner(self) -> str:
        status = self.federation_status()
        return f"Federation: {status['active_nodes']}/{status['total_nodes']} nodes active, {status['knowledge_exchanges']} exchanges, {status['protocol_health']}"


federated_governance = FederatedGovernance()
