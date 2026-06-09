"""
Incident reconstructor — builds causal timeline for each incident.
"""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Reconstruction:
    recon_id: str
    incident_id: str
    timeline: List[dict]
    root_cause: str
    contributing_factors: List[str]
    reconstructed_at: str


class IncidentReconstructor:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: Dict[str, Reconstruction] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"IRC-{self._counter:03d}"

    def reconstruct(
        self,
        incident_id: str,
        timeline: List[dict],
        root_cause: str,
        contributing_factors: List[str],
    ) -> Reconstruction:
        with self._lock:
            rec = Reconstruction(
                recon_id=self._next_id(),
                incident_id=incident_id,
                timeline=timeline,
                root_cause=root_cause,
                contributing_factors=contributing_factors,
                reconstructed_at=datetime.utcnow().isoformat(),
            )
            self._records[incident_id] = rec
            return rec

    def get_reconstruction(self, incident_id: str) -> Optional[Reconstruction]:
        with self._lock:
            return self._records.get(incident_id)

    def all_reconstructions(self) -> List[Reconstruction]:
        with self._lock:
            return list(self._records.values())


incident_reconstructor = IncidentReconstructor()
