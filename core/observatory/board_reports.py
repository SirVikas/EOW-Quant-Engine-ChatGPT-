"""
PHOENIX OBSERVATORY-X — Board Reports  [OX-MATURITY-03]

Auto-generated institutional summary reports at three cadences:
  WEEKLY    — 7-day operational summary
  MONTHLY   — 30-day trend and pattern analysis
  QUARTERLY — 90-day strategic health review

Each report aggregates:
  - Investigations opened and resolved
  - Recommendations generated, applied, confirmed
  - Economic outcomes (PnL impact, WR delta)
  - Active and new diseases
  - Precedents established
  - Trust engine evolution
  - Top performing and worst performing recommendations

Reports are stored in memory (last 52 weekly, 12 monthly, 4 quarterly).
They can be exported via API for archiving.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


_WEEKLY_SECONDS    = 7 * 86400
_MONTHLY_SECONDS   = 30 * 86400
_QUARTERLY_SECONDS = 90 * 86400

_CADENCE_SECONDS = {
    "WEEKLY":    _WEEKLY_SECONDS,
    "MONTHLY":   _MONTHLY_SECONDS,
    "QUARTERLY": _QUARTERLY_SECONDS,
}

_MAX_REPORTS = {
    "WEEKLY":    52,
    "MONTHLY":   12,
    "QUARTERLY": 4,
}


@dataclass
class BoardReport:
    report_id: str
    cadence: str            # WEEKLY | MONTHLY | QUARTERLY
    period_start: float
    period_end: float
    generated_at: float = field(default_factory=time.time)
    # Investigation metrics
    investigations_opened: int = 0
    investigations_resolved: int = 0
    investigations_inconclusive: int = 0
    # Recommendation metrics
    recommendations_generated: int = 0
    recommendations_applied: int = 0
    recommendations_confirmed: int = 0
    recommendations_profitable: int = 0
    recommendations_harmful: int = 0
    # Economic metrics
    total_pnl_impact_usdt: float = 0.0
    avg_wr_delta: float = 0.0
    avg_pf_delta: float = 0.0
    # Disease metrics
    new_diseases: int = 0
    active_diseases: int = 0
    resolved_diseases: int = 0
    # Trust engine
    trust_types_institutional: int = 0
    trust_types_untrusted: int = 0
    # Precedents
    precedents_established: int = 0
    # Narrative
    observatory_score: int = 0
    executive_summary: str = ""
    top_recommendation: str = ""
    top_disease: str = ""
    highlights: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)


class ObservatoryBoardReports:
    """
    Generates and stores Observatory Board Reports at three cadences.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._reports: Dict[str, List[BoardReport]] = {
            "WEEKLY": [], "MONTHLY": [], "QUARTERLY": []
        }
        self._last_generated: Dict[str, float] = {
            "WEEKLY": 0.0, "MONTHLY": 0.0, "QUARTERLY": 0.0
        }

    # ── Report Generation ─────────────────────────────────────────────────────

    def generate(self, cadence: str) -> BoardReport:
        if cadence not in _CADENCE_SECONDS:
            raise ValueError(f"Invalid cadence '{cadence}'. Must be WEEKLY, MONTHLY, or QUARTERLY.")

        window = _CADENCE_SECONDS[cadence]
        period_end   = time.time()
        period_start = period_end - window
        report_id    = f"BRD_{cadence[0]}_{int(period_end)}"

        r = BoardReport(
            report_id=report_id,
            cadence=cadence,
            period_start=period_start,
            period_end=period_end,
        )

        self._populate_investigations(r, period_start)
        self._populate_recommendations(r, period_start)
        self._populate_economic(r)
        self._populate_diseases(r, period_start)
        self._populate_trust(r)
        self._populate_precedents(r, period_start)
        r.observatory_score  = self._compute_score(r)
        r.executive_summary  = self._executive_summary(r, cadence)
        r.highlights, r.concerns = self._highlights_concerns(r)

        with self._lock:
            bucket = self._reports[cadence]
            bucket.append(r)
            if len(bucket) > _MAX_REPORTS[cadence]:
                bucket.pop(0)
            self._last_generated[cadence] = time.time()

        return r

    def generate_due(self) -> List[BoardReport]:
        """Generate any reports that are overdue."""
        generated = []
        now = time.time()
        for cadence, interval in _CADENCE_SECONDS.items():
            with self._lock:
                last = self._last_generated[cadence]
            if now - last >= interval:
                try:
                    generated.append(self.generate(cadence))
                except Exception:
                    pass
        return generated

    # ── Query ─────────────────────────────────────────────────────────────────

    def latest(self, cadence: str) -> Optional[dict]:
        with self._lock:
            bucket = self._reports.get(cadence, [])
            r = bucket[-1] if bucket else None
        return self._serialise(r) if r else None

    def all_reports(self, cadence: str) -> List[dict]:
        with self._lock:
            bucket = list(self._reports.get(cadence, []))
        return [self._serialise(r) for r in reversed(bucket)]

    def summary(self) -> dict:
        result: dict = {}
        for cadence in ("WEEKLY", "MONTHLY", "QUARTERLY"):
            with self._lock:
                bucket = self._reports[cadence]
                last_gen = self._last_generated[cadence]
            result[cadence.lower()] = {
                "reports_stored": len(bucket),
                "last_generated": last_gen or None,
                "latest_score":   bucket[-1].observatory_score if bucket else None,
            }
        return result

    # ── Population helpers ────────────────────────────────────────────────────

    def _populate_investigations(self, r: BoardReport, since: float) -> None:
        try:
            from core.observatory.inspector import phoenix_inspector
            for inv in phoenix_inspector._investigations.values():
                if inv.started_at >= since:
                    r.investigations_opened += 1
                if inv.completed_at >= since:
                    if inv.status == "complete":
                        r.investigations_resolved += 1
                    elif inv.status == "inconclusive":
                        r.investigations_inconclusive += 1
        except Exception:
            pass

    def _populate_recommendations(self, r: BoardReport, since: float) -> None:
        try:
            from core.observatory.recommendation_outcome_registry import recommendation_outcome_registry as _ror
            all_recs = _ror.all_tracked()
            for rec in all_recs:
                if rec.get("applied_at", 0) >= since:
                    r.recommendations_applied += 1
                if rec.get("status") == "final":
                    r.recommendations_confirmed += 1
                    if rec.get("final_outcome") == "improved":
                        r.recommendations_profitable += 1
                    elif rec.get("final_outcome") == "worsened":
                        r.recommendations_harmful += 1
        except Exception:
            pass

    def _populate_economic(self, r: BoardReport) -> None:
        try:
            from core.observatory.economic_outcome_ledger import economic_outcome_ledger as _eol
            s = _eol.summary()
            r.total_pnl_impact_usdt = s.get("total_pnl_impact_usdt", 0.0)
            r.avg_wr_delta          = s.get("avg_wr_delta", 0.0)
            r.avg_pf_delta          = s.get("avg_pf_delta", 0.0)
            top = _eol.top_performers(1)
            if top:
                r.top_recommendation = top[0].get("rec_title", "")
        except Exception:
            pass

    def _populate_diseases(self, r: BoardReport, since: float) -> None:
        try:
            from core.observatory.disease_registry import institutional_disease_registry as _dr
            s = _dr.summary()
            r.active_diseases   = s.get("active", 0)
            r.resolved_diseases = s.get("resolved", 0)
            active = _dr.active_diseases()
            if active:
                critical = [d for d in active if d.get("severity") in ("CRITICAL", "HIGH")]
                r.top_disease = critical[0].get("name", active[0].get("name", "")) if critical else active[0].get("name", "")
        except Exception:
            pass

    def _populate_trust(self, r: BoardReport) -> None:
        try:
            from core.observatory.trust_engine import recommendation_trust_engine
            s = recommendation_trust_engine.summary()
            r.trust_types_institutional = len(s.get("institutional_types", []))
            r.trust_types_untrusted     = len(s.get("untrusted_types", []))
        except Exception:
            pass

    def _populate_precedents(self, r: BoardReport, since: float) -> None:
        try:
            from core.observatory.precedent_library import precedent_library
            all_cases = precedent_library.all_cases()
            r.precedents_established = sum(1 for c in all_cases if c.get("created_at", 0) >= since)
        except Exception:
            pass

    @staticmethod
    def _compute_score(r: BoardReport) -> int:
        score = 70  # baseline
        # Reward resolved investigations
        if r.investigations_resolved > r.investigations_inconclusive:
            score += 5
        # Reward profitable recommendations
        if r.recommendations_confirmed > 0:
            profit_rate = r.recommendations_profitable / max(1, r.recommendations_confirmed)
            score += int(profit_rate * 15)
        # Penalize harmful recommendations
        score -= r.recommendations_harmful * 3
        # Reward PnL impact
        if r.total_pnl_impact_usdt > 0:
            score += 5
        # Reward trust engine health
        score += r.trust_types_institutional * 2
        score -= r.trust_types_untrusted * 1
        # Penalize critical diseases
        if r.active_diseases > 3:
            score -= 5
        return max(0, min(100, score))

    @staticmethod
    def _executive_summary(r: BoardReport, cadence: str) -> str:
        period = {"WEEKLY": "week", "MONTHLY": "month", "QUARTERLY": "quarter"}[cadence]
        lines = [
            f"OBSERVATORY-X {cadence} BOARD REPORT",
            f"Period: {period} ending {time.strftime('%Y-%m-%d', time.gmtime(r.period_end))}",
            f"Observatory Score: {r.observatory_score}/100",
            "",
            f"Investigations: {r.investigations_opened} opened, {r.investigations_resolved} resolved.",
            f"Recommendations: {r.recommendations_applied} applied, {r.recommendations_profitable} profitable, {r.recommendations_harmful} harmful.",
            f"Economic Impact: {r.total_pnl_impact_usdt:+.2f} USDT | WR delta: {r.avg_wr_delta:+.3f}",
            f"Active Diseases: {r.active_diseases} | Resolved: {r.resolved_diseases}",
        ]
        if r.top_recommendation:
            lines.append(f"Top Recommendation: {r.top_recommendation}")
        if r.top_disease:
            lines.append(f"Active Disease: {r.top_disease}")
        return "\n".join(lines)

    @staticmethod
    def _highlights_concerns(r: BoardReport):
        highlights, concerns = [], []
        if r.recommendations_profitable > r.recommendations_harmful:
            highlights.append(f"{r.recommendations_profitable} profitable recommendations confirmed")
        if r.total_pnl_impact_usdt > 0:
            highlights.append(f"Positive economic impact: +{r.total_pnl_impact_usdt:.2f} USDT")
        if r.resolved_diseases > 0:
            highlights.append(f"{r.resolved_diseases} institutional diseases resolved")
        if r.trust_types_institutional > 0:
            highlights.append(f"{r.trust_types_institutional} recommendation types at INSTITUTIONAL trust level")
        if r.recommendations_harmful > 0:
            concerns.append(f"{r.recommendations_harmful} harmful recommendations — review cemetery")
        if r.active_diseases > 3:
            concerns.append(f"{r.active_diseases} active institutional diseases")
        if r.investigations_inconclusive > r.investigations_resolved:
            concerns.append("More inconclusive than resolved investigations — evidence quality issue")
        if r.trust_types_untrusted > 2:
            concerns.append(f"{r.trust_types_untrusted} recommendation types at UNTRUSTED level")
        return highlights, concerns

    @staticmethod
    def _serialise(r: BoardReport) -> dict:
        return {
            "report_id":                r.report_id,
            "cadence":                  r.cadence,
            "period_start":             r.period_start,
            "period_end":               r.period_end,
            "generated_at":             r.generated_at,
            "investigations_opened":    r.investigations_opened,
            "investigations_resolved":  r.investigations_resolved,
            "investigations_inconclusive": r.investigations_inconclusive,
            "recommendations_applied":  r.recommendations_applied,
            "recommendations_confirmed": r.recommendations_confirmed,
            "recommendations_profitable": r.recommendations_profitable,
            "recommendations_harmful":  r.recommendations_harmful,
            "total_pnl_impact_usdt":    r.total_pnl_impact_usdt,
            "avg_wr_delta":             r.avg_wr_delta,
            "avg_pf_delta":             r.avg_pf_delta,
            "new_diseases":             r.new_diseases,
            "active_diseases":          r.active_diseases,
            "resolved_diseases":        r.resolved_diseases,
            "trust_types_institutional": r.trust_types_institutional,
            "trust_types_untrusted":    r.trust_types_untrusted,
            "precedents_established":   r.precedents_established,
            "observatory_score":        r.observatory_score,
            "executive_summary":        r.executive_summary,
            "top_recommendation":       r.top_recommendation,
            "top_disease":              r.top_disease,
            "highlights":               r.highlights,
            "concerns":                 r.concerns,
        }


# Singleton
observatory_board_reports = ObservatoryBoardReports()
