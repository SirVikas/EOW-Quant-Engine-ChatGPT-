"""
PHOENIX PCAO — Executive Risk Forecaster  [PCAO-03]

Predictive risk forecasting based on current trends:
  - Decay velocity → projected trust collapse timeline
  - AEG accuracy drift → projected rollback probability
  - Evidence accumulation rate → projected milestone dates
  - Open risk aging → escalation probability

Output: Future Risk Forecast with confidence and horizon
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ForecastedRisk:
    forecast_id: str
    title: str
    source: str
    projected_severity: str     # CRITICAL / HIGH / MEDIUM / LOW
    probability: float          # 0–1
    horizon_days: int
    driver: str
    mitigation: str
    confidence: str             # HIGH / MEDIUM / LOW


class RiskForecaster:
    """
    Generates predictive risk forecasts from current institutional trends.
    """

    def forecast(self, horizon_days: int = 90) -> dict:
        forecasts: List[ForecastedRisk] = []
        ts = int(time.time() * 1000)

        self._forecast_trust_decay(forecasts, horizon_days, ts)
        self._forecast_evidence_starvation(forecasts, horizon_days, ts)
        self._forecast_aeg_drift(forecasts, horizon_days, ts)
        self._forecast_risk_aging(forecasts, horizon_days, ts)

        critical = [f for f in forecasts if f.projected_severity == "CRITICAL" and f.probability >= 0.6]
        high     = [f for f in forecasts if f.projected_severity == "HIGH"     and f.probability >= 0.5]

        return {
            "horizon_days":       horizon_days,
            "total_forecasted":   len(forecasts),
            "critical_probable":  len(critical),
            "high_probable":      len(high),
            "forecasts":          sorted(
                [self._ser(f) for f in forecasts],
                key=lambda x: x["probability"],
                reverse=True,
            ),
            "top_risk":           self._ser(forecasts[0]) if forecasts else None,
            "generated_at":       time.time(),
        }

    def _forecast_trust_decay(self, forecasts, horizon_days, ts) -> None:
        try:
            from core.trust.trust_decay_engine import trust_decay_engine as _tde
            for status in _tde.all_decay_statuses():
                if status.get("is_stale") and status.get("decay_applied", 0) > 5:
                    daily_rate = status.get("decay_applied", 0) / max(1, status.get("days_stale", 1))
                    current_score = status.get("current_score", 50)
                    days_to_critical = max(0, (current_score - 30) / max(0.1, daily_rate))
                    if days_to_critical <= horizon_days:
                        prob = min(0.95, 1.0 - days_to_critical / max(1, horizon_days))
                        forecasts.append(ForecastedRisk(
                            forecast_id=f"FCAST-DECAY-{ts}",
                            title=f"Trust score collapse: {status['pillar']}",
                            source="PTP",
                            projected_severity="CRITICAL" if days_to_critical < 14 else "HIGH",
                            probability=round(prob, 2),
                            horizon_days=int(days_to_critical) + 1,
                            driver=f"Decay rate {daily_rate:.2f}pts/day, current score {current_score:.1f}",
                            mitigation="Record new validation evidence immediately",
                            confidence="HIGH",
                        ))
        except Exception:
            pass

    def _forecast_evidence_starvation(self, forecasts, horizon_days, ts) -> None:
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            audit = _tew.full_audit()
            total = audit.get("total_evidence", 0)
            if total < 50:
                days_running = max(1, (time.time() - 1700000000) / 86400)
                rate_per_day = total / days_running
                days_to_100 = (100 - total) / max(0.01, rate_per_day)
                if days_to_100 > horizon_days:
                    forecasts.append(ForecastedRisk(
                        forecast_id=f"FCAST-EVID-{ts}",
                        title="Evidence starvation — PROVEN status unreachable this quarter",
                        source="PTP",
                        projected_severity="HIGH",
                        probability=0.75,
                        horizon_days=int(days_to_100),
                        driver=f"Accumulation rate {rate_per_day:.2f}/day, need 100 (have {total})",
                        mitigation="Increase recommendation outcome recording frequency",
                        confidence="MEDIUM",
                    ))
        except Exception:
            pass

    def _forecast_aeg_drift(self, forecasts, horizon_days, ts) -> None:
        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            all_stats = _ass.all_stats()
            degrading = [s for s in all_stats if (s.get("accuracy") or 0) < 0.65
                         and s.get("samples_with_outcome", 0) >= 10]
            if degrading:
                forecasts.append(ForecastedRisk(
                    forecast_id=f"FCAST-DRIFT-{ts}",
                    title=f"AEG sandbox accuracy degrading ({len(degrading)} rec types)",
                    source="AEG",
                    projected_severity="HIGH",
                    probability=0.65,
                    horizon_days=30,
                    driver=f"{len(degrading)} rec types below 65% accuracy",
                    mitigation="Review sandbox evidence quality; consider rollback",
                    confidence="MEDIUM",
                ))
        except Exception:
            pass

    def _forecast_risk_aging(self, forecasts, horizon_days, ts) -> None:
        try:
            from core.pcao.risk_office import risk_office as _ro
            open_risks = _ro.open_risks()
            now = time.time()
            aging = [r for r in open_risks
                     if (now - r.get("opened_at", now)) / 86400 > 30
                     and r.get("severity") in ("HIGH", "CRITICAL")]
            if aging:
                forecasts.append(ForecastedRisk(
                    forecast_id=f"FCAST-AGING-{ts}",
                    title=f"{len(aging)} high/critical risks aging beyond 30 days unresolved",
                    source="PCAO",
                    projected_severity="CRITICAL" if len(aging) > 2 else "HIGH",
                    probability=min(0.9, 0.5 + len(aging) * 0.1),
                    horizon_days=30,
                    driver=f"Risks unresolved for 30+ days: {[r['risk_id'] for r in aging[:3]]}",
                    mitigation="Assign owners and action plans to aging risks this sprint",
                    confidence="HIGH",
                ))
        except Exception:
            pass

    def risk_trend_analysis(self) -> dict:
        try:
            from core.pcao.risk_office import risk_office as _ro
            dashboard = _ro.risk_dashboard()
        except Exception:
            dashboard = {}
        forecast_30  = self.forecast(horizon_days=30)
        forecast_90  = self.forecast(horizon_days=90)
        return {
            "current_open":           dashboard.get("open_risks", 0),
            "current_critical":       dashboard.get("critical_open", 0),
            "forecast_30d_critical":  forecast_30.get("critical_probable", 0),
            "forecast_90d_critical":  forecast_90.get("critical_probable", 0),
            "trend":                  "WORSENING" if forecast_90.get("critical_probable", 0) > dashboard.get("critical_open", 0) else "STABLE",
            "generated_at":           time.time(),
        }

    @staticmethod
    def _ser(f: ForecastedRisk) -> dict:
        return {
            "forecast_id":        f.forecast_id,
            "title":              f.title,
            "source":             f.source,
            "projected_severity": f.projected_severity,
            "probability":        f.probability,
            "horizon_days":       f.horizon_days,
            "driver":             f.driver,
            "mitigation":         f.mitigation,
            "confidence":         f.confidence,
        }


# Singleton
risk_forecaster = RiskForecaster()
