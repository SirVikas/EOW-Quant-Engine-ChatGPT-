"""
PHOENIX Epistemic Intelligence — Confidence Boundary Engine
Tracks confidence levels per domain as hard/soft boundaries.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


@dataclass
class ConfidenceBoundary:
    boundary_id: str
    domain: str
    confidence_level: float  # 0-1
    basis: str              # EVIDENCE/ASSUMPTION/THEORY/UNKNOWN
    boundary_type: str      # HARD/SOFT
    notes: str
    created_at: str


class ConfidenceBoundaryEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._boundaries: Dict[str, ConfidenceBoundary] = {}  # key: domain

    def set_boundary(
        self,
        domain: str,
        confidence_level: float,
        basis: str,
        boundary_type: str = "SOFT",
        notes: str = "",
    ) -> dict:
        with self._lock:
            existing = self._boundaries.get(domain)
            if existing:
                existing.confidence_level = confidence_level
                existing.basis = basis
                existing.boundary_type = boundary_type
                existing.notes = notes
                return asdict(existing)
            boundary = ConfidenceBoundary(
                boundary_id=f"CB-{uuid.uuid4().hex[:8].upper()}",
                domain=domain,
                confidence_level=confidence_level,
                basis=basis,
                boundary_type=boundary_type,
                notes=notes,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._boundaries[domain] = boundary
            return asdict(boundary)

    def get_boundary(self, domain: str) -> Optional[dict]:
        with self._lock:
            b = self._boundaries.get(domain)
        return asdict(b) if b else None

    def all_boundaries(self) -> list:
        with self._lock:
            return [asdict(b) for b in self._boundaries.values()]

    def confidence_map(self) -> dict:
        with self._lock:
            return {domain: b.confidence_level for domain, b in self._boundaries.items()}

    def low_confidence_domains(self, threshold: float = 0.4) -> list:
        with self._lock:
            return [
                asdict(b) for b in self._boundaries.values()
                if b.confidence_level < threshold
            ]


confidence_boundary_engine = ConfidenceBoundaryEngine()
