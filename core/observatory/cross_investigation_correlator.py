"""
PHOENIX OBSERVATORY-X — Cross-Investigation Correlator  [OX-GAP-03]

Individual issue detection → Institutional Disease Detection.

When three investigations all implicate the same actor, session, or defect type,
that is no longer a coincidence — it is a systemic pattern.

The Correlator scans across all completed investigations and surfaces:
  - Shared primary suspects (same actor blamed ≥ threshold times)
  - Shared defect types clustering across different investigations
  - Shared time windows dominating across investigations
  - Shared session patterns recurring in separate loss events

Correlation confidence is based on:
  - Count of investigations sharing the pattern
  - Significance level of findings within each investigation
  - Recency of the investigations (recent clusters carry more weight)
"""
from __future__ import annotations

import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional


CORRELATION_THRESHOLD = 2   # minimum occurrences to declare a correlation
RECENCY_WINDOW_DAYS   = 14  # only correlate investigations from last 14 days


@dataclass
class CorrelationPattern:
    pattern_id: str
    dimension: str          # actor | session | defect_type | regime | strategy
    value: str              # the specific recurring value
    occurrence_count: int
    investigation_ids: List[str]
    avg_significance: str   # high | medium | low
    first_seen: float
    last_seen: float
    disease_label: str      # human-readable systemic pattern name
    confidence: float       # 0.0–1.0


@dataclass
class CorrelationReport:
    report_id: str
    generated_at: float
    investigations_scanned: int
    patterns: List[CorrelationPattern]
    systemic_diseases: List[str]      # high-confidence patterns
    summary: str


class CrossInvestigationCorrelator:
    """
    Scans across all InvestigationReports to detect shared root causes
    that would not be visible when looking at individual investigations.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._last_report: Optional[CorrelationReport] = None

    # ── Core Analysis ─────────────────────────────────────────────────────────

    def correlate(self) -> CorrelationReport:
        investigations = self._fetch_investigations()
        report_id = f"CORR_{int(time.time())}"

        if not investigations:
            r = CorrelationReport(
                report_id=report_id,
                generated_at=time.time(),
                investigations_scanned=0,
                patterns=[],
                systemic_diseases=[],
                summary="No completed investigations available for correlation.",
            )
            with self._lock:
                self._last_report = r
            return r

        # Collect dimension:value occurrences with investigation_id
        dim_counter: Dict[str, List[tuple]] = {}  # "dim:val" → [(inv_id, sig, ts), ...]
        for inv in investigations:
            ts = inv.get("completed_at", inv.get("started_at", 0.0))
            for finding in inv.get("findings", []):
                dim = finding.get("dimension", "")
                val = str(finding.get("value", ""))
                sig = finding.get("significance", "low")
                key = f"{dim}:{val}"
                if key not in dim_counter:
                    dim_counter[key] = []
                dim_counter[key].append((inv.get("investigation_id", ""), sig, ts))

        patterns: List[CorrelationPattern] = []
        for key, occurrences in dim_counter.items():
            if len(occurrences) < CORRELATION_THRESHOLD:
                continue
            dim, val = key.split(":", 1)
            inv_ids = [o[0] for o in occurrences]
            sigs = [o[1] for o in occurrences]
            timestamps = [o[2] for o in occurrences]

            # Significance weighting
            sig_weights = {"high": 3, "medium": 2, "low": 1}
            avg_w = sum(sig_weights.get(s, 1) for s in sigs) / len(sigs)
            avg_sig = "high" if avg_w >= 2.5 else ("medium" if avg_w >= 1.5 else "low")

            confidence = min(1.0, len(occurrences) / 5.0) * (avg_w / 3.0)

            patterns.append(CorrelationPattern(
                pattern_id=f"PAT_{dim.upper()}_{val[:20].replace(' ', '_').upper()}",
                dimension=dim,
                value=val,
                occurrence_count=len(occurrences),
                investigation_ids=list(set(inv_ids)),
                avg_significance=avg_sig,
                first_seen=min(timestamps),
                last_seen=max(timestamps),
                disease_label=self._disease_label(dim, val, len(occurrences)),
                confidence=round(confidence, 3),
            ))

        patterns.sort(key=lambda p: p.confidence, reverse=True)
        diseases = [p.disease_label for p in patterns if p.avg_significance == "high" and p.confidence >= 0.5]

        summary = (
            f"Scanned {len(investigations)} investigations. "
            f"Found {len(patterns)} correlation patterns. "
            f"Systemic diseases detected: {len(diseases)}."
            if patterns else
            f"Scanned {len(investigations)} investigations. No cross-investigation correlations found."
        )

        r = CorrelationReport(
            report_id=report_id,
            generated_at=time.time(),
            investigations_scanned=len(investigations),
            patterns=patterns,
            systemic_diseases=diseases,
            summary=summary,
        )
        with self._lock:
            self._last_report = r
        return r

    def last_report(self) -> Optional[dict]:
        with self._lock:
            r = self._last_report
        return self._serialise(r) if r else None

    # ── Internal ──────────────────────────────────────────────────────────────

    def _fetch_investigations(self) -> List[dict]:
        try:
            from core.observatory.inspector import phoenix_inspector
            cutoff = time.time() - RECENCY_WINDOW_DAYS * 86400
            result = []
            for inv_id, inv in phoenix_inspector._investigations.items():
                if inv.status not in ("complete",):
                    continue
                if inv.completed_at < cutoff:
                    continue
                result.append({
                    "investigation_id": inv.investigation_id,
                    "completed_at": inv.completed_at,
                    "started_at": inv.started_at,
                    "findings": [
                        {
                            "dimension": f.dimension,
                            "value": f.value,
                            "significance": f.significance,
                        }
                        for f in inv.findings
                    ],
                })
            return result
        except Exception:
            return []

    @staticmethod
    def _disease_label(dim: str, val: str, count: int) -> str:
        labels = {
            "actor":       f"Systemic Actor Failure: '{val}' implicated in {count} investigations",
            "session":     f"Session Disease: '{val}' dominates {count} investigations",
            "defect_type": f"Recurring Defect: '{val}' across {count} investigations",
            "regime":      f"Regime Vulnerability: '{val}' regime in {count} investigations",
            "strategy":    f"Strategy Weakness: '{val}' in {count} investigations",
        }
        return labels.get(dim, f"Pattern: {dim}={val} in {count} investigations")

    def _serialise(self, r: CorrelationReport) -> dict:
        return {
            "report_id":              r.report_id,
            "generated_at":           r.generated_at,
            "investigations_scanned": r.investigations_scanned,
            "pattern_count":          len(r.patterns),
            "systemic_diseases":      r.systemic_diseases,
            "summary":                r.summary,
            "patterns": [
                {
                    "pattern_id":        p.pattern_id,
                    "dimension":         p.dimension,
                    "value":             p.value,
                    "occurrence_count":  p.occurrence_count,
                    "investigation_ids": p.investigation_ids,
                    "avg_significance":  p.avg_significance,
                    "confidence":        p.confidence,
                    "disease_label":     p.disease_label,
                    "first_seen":        p.first_seen,
                    "last_seen":         p.last_seen,
                }
                for p in r.patterns
            ],
        }


# Singleton
cross_investigation_correlator = CrossInvestigationCorrelator()
