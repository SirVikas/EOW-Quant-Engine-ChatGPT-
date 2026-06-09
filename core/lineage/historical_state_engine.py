"""Historical State Engine — queries system state at any point in time."""
import threading


class HistoricalStateEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def state_at(self, timestamp: float) -> dict:
        from core.lineage.snapshot_engine import snapshot_engine
        with self._lock:
            snapshots = snapshot_engine.all_snapshots(limit=1000)
            # Find nearest snapshot at or before timestamp
            candidates = [s for s in snapshots if s.get("captured_at", 0) <= timestamp]
            if not candidates:
                return {}
            nearest = max(candidates, key=lambda x: x.get("captured_at", 0))
            return nearest.get("state", {})

    def state_diff(self, snapshot_id_a: str, snapshot_id_b: str) -> dict:
        from core.lineage.snapshot_engine import snapshot_engine
        with self._lock:
            snap_a = snapshot_engine.get(snapshot_id_a)
            snap_b = snapshot_engine.get(snapshot_id_b)
            state_a = snap_a.get("state", {})
            state_b = snap_b.get("state", {})
            changed: dict = {}
            all_keys = set(state_a.keys()) | set(state_b.keys())
            for k in all_keys:
                va = state_a.get(k)
                vb = state_b.get(k)
                if va != vb:
                    changed[k] = {"before": va, "after": vb}
            return {
                "snapshot_a": snapshot_id_a,
                "snapshot_b": snapshot_id_b,
                "changed_keys": list(changed.keys()),
                "diff": changed,
            }

    def knowledge_at(self, timestamp: float) -> dict:
        state = self.state_at(timestamp)
        return {
            "question": "What did PHOENIX know at this time?",
            "timestamp": timestamp,
            "known_state": state,
            "keys_known": list(state.keys()),
        }


historical_state_engine = HistoricalStateEngine()
