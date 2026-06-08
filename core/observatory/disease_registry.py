"""
PHOENIX OBSERVATORY-X — Institutional Disease Registry  [OX-MATURITY-01]

The Cross-Investigation Correlator detects diseases in real time.
The Disease Registry makes them permanent institutional knowledge.

A "disease" is a systemic pattern that:
  - Has been detected in ≥ 2 independent investigations
  - Represents a structural weakness, not a one-time anomaly
  - Requires tracking across the institution's lifetime

Pre-seeded founding diseases (from institutional history):
  DISEASE-001  Context Lineage Failure
  DISEASE-002  ATR Attribution Assumption Error
  DISEASE-003  Session Concentration Bias

Disease lifecycle:
  ACTIVE    — currently manifesting
  MONITORED — treated but under observation
  RESOLVED  — root cause eliminated and verified
  DORMANT   — not seen for 90+ days but not formally resolved
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiseaseRecord:
    disease_id: str
    name: str
    description: str
    root_cause: str
    dimension: str           # actor | session | defect_type | regime | strategy
    dimension_value: str     # the specific recurring value
    first_detected_at: float
    last_seen_at: float
    detection_count: int     # how many times correlated
    severity: str            # LOW | MEDIUM | HIGH | CRITICAL
    status: str = "ACTIVE"   # ACTIVE | MONITORED | RESOLVED | DORMANT
    investigation_ids: List[str] = field(default_factory=list)
    resolution_note: str = ""
    resolved_at: float = 0.0
    tags: List[str] = field(default_factory=list)


class InstitutionalDiseaseRegistry:
    """
    Permanent catalog of systemic institutional diseases.
    Persists across sessions. New correlations update existing disease records.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._diseases: Dict[str, DiseaseRecord] = {}
        self._bootstrap_founding_diseases()

    # ── Recording & Updating ──────────────────────────────────────────────────

    def declare_disease(
        self,
        disease_id: str,
        name: str,
        description: str,
        root_cause: str,
        dimension: str,
        dimension_value: str,
        severity: str,
        investigation_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> DiseaseRecord:
        with self._lock:
            if disease_id in self._diseases:
                # Update existing: increment detection count, refresh last_seen
                d = self._diseases[disease_id]
                d.detection_count += 1
                d.last_seen_at = time.time()
                if investigation_ids:
                    for inv_id in investigation_ids:
                        if inv_id not in d.investigation_ids:
                            d.investigation_ids.append(inv_id)
                if d.status == "DORMANT":
                    d.status = "ACTIVE"
                return d
            d = DiseaseRecord(
                disease_id=disease_id,
                name=name,
                description=description,
                root_cause=root_cause,
                dimension=dimension,
                dimension_value=dimension_value,
                first_detected_at=time.time(),
                last_seen_at=time.time(),
                detection_count=1,
                severity=severity,
                investigation_ids=investigation_ids or [],
                tags=tags or [],
            )
            self._diseases[disease_id] = d
        self._record_imraf(d)
        return d

    def register_from_correlation(self, pattern: dict) -> Optional[DiseaseRecord]:
        """Auto-register a disease from a CorrelationPattern."""
        if pattern.get("avg_significance") != "high":
            return None
        if pattern.get("confidence", 0) < 0.4:
            return None
        disease_id = f"DISEASE-{pattern['pattern_id'][:20]}"
        return self.declare_disease(
            disease_id=disease_id,
            name=pattern.get("disease_label", pattern["pattern_id"]),
            description=f"Auto-detected via cross-investigation correlation. Pattern: {pattern['value']}",
            root_cause=f"Recurring {pattern['dimension']} factor: '{pattern['value']}'",
            dimension=pattern["dimension"],
            dimension_value=str(pattern["value"]),
            severity="HIGH" if pattern["occurrence_count"] >= 4 else "MEDIUM",
            investigation_ids=pattern.get("investigation_ids", []),
        )

    def update_status(
        self,
        disease_id: str,
        new_status: str,
        resolution_note: str = "",
    ) -> bool:
        with self._lock:
            d = self._diseases.get(disease_id)
            if not d:
                return False
            d.status = new_status
            if new_status == "RESOLVED":
                d.resolved_at = time.time()
                d.resolution_note = resolution_note
        return True

    def age_dormant(self, dormant_days: float = 90.0) -> int:
        """Mark diseases not seen for dormant_days as DORMANT."""
        cutoff = time.time() - dormant_days * 86400
        count = 0
        with self._lock:
            for d in self._diseases.values():
                if d.status == "ACTIVE" and d.last_seen_at < cutoff:
                    d.status = "DORMANT"
                    count += 1
        return count

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, disease_id: str) -> Optional[dict]:
        with self._lock:
            d = self._diseases.get(disease_id)
        return self._serialise(d) if d else None

    def all_diseases(self, status_filter: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = list(self._diseases.values())
        if status_filter:
            items = [d for d in items if d.status == status_filter]
        return [self._serialise(d) for d in sorted(items, key=lambda x: x.first_detected_at)]

    def active_diseases(self) -> List[dict]:
        return self.all_diseases(status_filter="ACTIVE")

    def summary(self) -> dict:
        with self._lock:
            items = list(self._diseases.values())
        by_status: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for d in items:
            by_status[d.status] = by_status.get(d.status, 0) + 1
            by_severity[d.severity] = by_severity.get(d.severity, 0) + 1
        return {
            "total_diseases":  len(items),
            "active":          by_status.get("ACTIVE", 0),
            "monitored":       by_status.get("MONITORED", 0),
            "resolved":        by_status.get("RESOLVED", 0),
            "dormant":         by_status.get("DORMANT", 0),
            "by_severity":     by_severity,
            "critical_diseases": [d.disease_id for d in items if d.severity == "CRITICAL" and d.status == "ACTIVE"],
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _bootstrap_founding_diseases(self) -> None:
        _FOUNDING = [
            DiseaseRecord(
                disease_id="DISEASE-001",
                name="Context Lineage Failure",
                description=(
                    "Trade loss events lack sufficient upstream context — the lineage chain "
                    "breaks before reaching the originating module decision."
                ),
                root_cause=(
                    "Lineage tracker not capturing full decision chain at trade entry. "
                    "Observable as investigations with incomplete actor attribution."
                ),
                dimension="defect_type",
                dimension_value="incomplete_lineage",
                first_detected_at=time.time() - 30 * 86400,
                last_seen_at=time.time() - 7 * 86400,
                detection_count=3,
                severity="MEDIUM",
                status="MONITORED",
                tags=["lineage", "context", "founding"],
            ),
            DiseaseRecord(
                disease_id="DISEASE-002",
                name="ATR Attribution Assumption Error",
                description=(
                    "Investigations incorrectly name ATR as the primary cause without "
                    "counterfactual evidence — a recurring false-positive attribution pattern."
                ),
                root_cause=(
                    "ATR is a shared input to multiple modules. Correlation without "
                    "counterfactual leads to systematic misattribution. "
                    "See PREC-001 (Constitutional Precedent) for binding ruling."
                ),
                dimension="actor",
                dimension_value="atr_calculator",
                first_detected_at=time.time() - 60 * 86400,
                last_seen_at=time.time() - 14 * 86400,
                detection_count=5,
                severity="HIGH",
                status="MONITORED",
                investigation_ids=["FOUNDING-001"],
                tags=["atr", "attribution", "counterfactual", "founding"],
            ),
            DiseaseRecord(
                disease_id="DISEASE-003",
                name="Session Concentration Bias",
                description=(
                    "Loss events cluster in specific trading sessions (typically 06-08 UTC "
                    "and 20-22 UTC), suggesting regime-session interaction not captured by filters."
                ),
                root_cause=(
                    "Session filters do not account for regime state at session open. "
                    "Low-liquidity sessions combined with trending regime produce outsized losses."
                ),
                dimension="session",
                dimension_value="06-08_UTC",
                first_detected_at=time.time() - 45 * 86400,
                last_seen_at=time.time() - 3 * 86400,
                detection_count=7,
                severity="HIGH",
                status="ACTIVE",
                tags=["session", "regime", "liquidity", "founding"],
            ),
        ]
        for d in _FOUNDING:
            self._diseases[d.disease_id] = d

    def _record_imraf(self, d: DiseaseRecord) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[DISEASE] {d.disease_id}: {d.name}",
                    content=f"Root cause: {d.root_cause} | Severity: {d.severity}",
                    category="institutional_disease",
                    tags=["disease", d.severity.lower()] + d.tags,
                )
        except Exception:
            pass

    @staticmethod
    def _serialise(d: DiseaseRecord) -> dict:
        return {
            "disease_id":       d.disease_id,
            "name":             d.name,
            "description":      d.description,
            "root_cause":       d.root_cause,
            "dimension":        d.dimension,
            "dimension_value":  d.dimension_value,
            "first_detected_at": d.first_detected_at,
            "last_seen_at":     d.last_seen_at,
            "detection_count":  d.detection_count,
            "severity":         d.severity,
            "status":           d.status,
            "investigation_ids": d.investigation_ids,
            "resolution_note":  d.resolution_note,
            "resolved_at":      d.resolved_at or None,
            "tags":             d.tags,
        }


# Singleton
institutional_disease_registry = InstitutionalDiseaseRegistry()
