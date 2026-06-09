"""Timeline Reconstruction Engine — rebuilds chronological event timelines."""
import threading


class TimelineReconstructionEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def reconstruct(self, subject_id: str) -> dict:
        from core.lineage.lineage_registry import lineage_registry
        from core.lineage.snapshot_engine import snapshot_engine

        with self._lock:
            history = lineage_registry.history_of(subject_id)
            snapshots = snapshot_engine.all_snapshots(limit=1000)
            relevant_snaps = [s for s in snapshots
                              if subject_id in str(s.get("state", {}))]

            timeline = []
            for entry in history:
                timeline.append({
                    "timestamp": entry.get("timestamp"),
                    "type": "LINEAGE",
                    "action": entry.get("action"),
                    "actor": entry.get("actor"),
                    "entry_id": entry.get("entry_id"),
                })
            for snap in relevant_snaps:
                timeline.append({
                    "timestamp": snap.get("captured_at"),
                    "type": "SNAPSHOT",
                    "snapshot_id": snap.get("snapshot_id"),
                    "label": snap.get("label"),
                })

            timeline.sort(key=lambda x: x.get("timestamp", 0))
            return {
                "subject_id": subject_id,
                "timeline": timeline,
                "event_count": len(timeline),
            }

    def full_timeline(self, start_timestamp: float = None, end_timestamp: float = None) -> list:
        from core.lineage.lineage_registry import lineage_registry
        with self._lock:
            entries = lineage_registry.recent_changes(limit=10000)
            if start_timestamp:
                entries = [e for e in entries if e.get("timestamp", 0) >= start_timestamp]
            if end_timestamp:
                entries = [e for e in entries if e.get("timestamp", 0) <= end_timestamp]
            entries.sort(key=lambda x: x.get("timestamp", 0))
            return entries

    def audit_trail(self, subject_id: str) -> str:
        from core.lineage.lineage_registry import lineage_registry
        with self._lock:
            history = lineage_registry.history_of(subject_id)
            if not history:
                return f"No audit trail found for subject: {subject_id}"
            lines = [f"Audit Trail for: {subject_id}", "=" * 50]
            for entry in history:
                import datetime
                ts = datetime.datetime.utcfromtimestamp(entry.get("timestamp", 0)).isoformat()
                lines.append(
                    f"[{ts}] {entry.get('action')} by {entry.get('actor')} "
                    f"(entry: {entry.get('entry_id')})"
                )
            return "\n".join(lines)


timeline_reconstruction_engine = TimelineReconstructionEngine()
