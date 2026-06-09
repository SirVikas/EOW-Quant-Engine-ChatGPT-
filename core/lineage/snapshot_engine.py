"""Snapshot Engine — captures point-in-time system state snapshots."""
import threading
import time
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Snapshot:
    snapshot_id: str
    label: str
    state: dict
    captured_at: float
    snapshot_type: str  # SCHEDULED/MANUAL/PRE_DEPLOYMENT/POST_DEPLOYMENT/INCIDENT


class SnapshotEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._snapshots: dict[str, Snapshot] = {}

    def _make_id(self) -> str:
        return "SNAP-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    def capture(self, label: str, snapshot_type: str = "MANUAL") -> dict:
        with self._lock:
            state: dict = {}

            try:
                from core.nexus.institutional_health_index import institutional_health_index
                state["health_report"] = institutional_health_index.health_report()
            except Exception:
                pass

            try:
                from core.trust_fabric.trust_fabric_engine import trust_fabric_engine
                report = trust_fabric_engine.unified_trust_report()
                # Summary only
                state["trust_summary"] = {k: v for k, v in report.items()
                                           if k != "details"}
            except Exception:
                pass

            try:
                from core.nexus.layer_registry import layer_registry
                state["layer_health"] = layer_registry.system_health_summary()
            except Exception:
                pass

            try:
                from core.evolution_governance.evolution_registry import evolution_registry
                state["evolution_stats"] = evolution_registry.evolution_stats()
            except Exception:
                pass

            try:
                from core.institutional_memory.decision_ledger import decision_ledger
                state["decision_ledger_stats"] = decision_ledger.ledger_stats()
            except Exception:
                pass

            snap_id = self._make_id()
            snap = Snapshot(
                snapshot_id=snap_id,
                label=label,
                state=state,
                captured_at=time.time(),
                snapshot_type=snapshot_type,
            )
            self._snapshots[snap_id] = snap
            return vars(snap)

    def get(self, snapshot_id: str) -> dict:
        with self._lock:
            s = self._snapshots.get(snapshot_id)
            return vars(s) if s else {}

    def all_snapshots(self, limit: int = 20) -> list:
        with self._lock:
            items = sorted(self._snapshots.values(), key=lambda x: x.captured_at)
            return [vars(s) for s in items[-limit:]]

    def snapshot_stats(self) -> dict:
        with self._lock:
            items = list(self._snapshots.values())
            by_type: dict = {}
            for s in items:
                by_type[s.snapshot_type] = by_type.get(s.snapshot_type, 0) + 1
            last_at = max((s.captured_at for s in items), default=0.0)
            return {
                "total": len(items),
                "by_type": by_type,
                "last_captured_at": last_at,
            }


snapshot_engine = SnapshotEngine()
