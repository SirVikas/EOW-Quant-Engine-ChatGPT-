"""
PHOENIX PCAO — Strategic Forecast Engine  [GAP-PEP-01, GAP-PEP-02, GAP-PEP-03]

PEP-01: Strategic Forecasting   — multi-year institutional trajectory projections
PEP-02: Scenario Planning       — what-if analysis across trust/governance/AEG/resources/roadmaps
PEP-03: Institutional Forecasting — full future-state modeling

Answers: "Where will PHOENIX be institutionally in 6 months? 1 year? 2 years?"
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


FORECAST_HORIZONS_DAYS = [90, 180, 365, 730]    # 3mo, 6mo, 1yr, 2yr


@dataclass
class FutureState:
    horizon_days: int
    label: str               # 3M / 6M / 1Y / 2Y
    trust_projection: dict
    aeg_projection:   dict
    pcao_projection:  dict
    health_projection: dict
    confidence: str          # HIGH / MEDIUM / LOW
    generated_at: float = field(default_factory=time.time)


@dataclass
class Scenario:
    scenario_id: str
    name: str
    assumptions: Dict[str, Any]
    projected_states: Dict[str, Any]    # horizon_label → projected metrics
    best_case: dict
    worst_case: dict
    base_case: dict
    recommended_action: str
    generated_at: float = field(default_factory=time.time)


class StrategicForecastEngine:
    """
    Multi-year strategic forecasting, scenario planning, and institutional future-state modeling.
    """

    # ── PEP-01: Strategic Forecasting ────────────────────────────────────────

    def strategic_forecast(self, horizon_days: int = 365) -> dict:
        label_map = {90: "3M", 180: "6M", 365: "1Y", 730: "2Y"}
        label = label_map.get(horizon_days, f"{horizon_days}D")

        trust   = self._project_trust(horizon_days)
        aeg     = self._project_aeg(horizon_days)
        pcao    = self._project_pcao(horizon_days)
        health  = self._project_health(horizon_days)
        confidence = "HIGH" if horizon_days <= 180 else "MEDIUM" if horizon_days <= 365 else "LOW"

        state = FutureState(
            horizon_days=horizon_days, label=label,
            trust_projection=trust, aeg_projection=aeg,
            pcao_projection=pcao, health_projection=health,
            confidence=confidence,
        )
        return self._ser_state(state)

    def multi_horizon_forecast(self) -> dict:
        forecasts = {}
        for days in FORECAST_HORIZONS_DAYS:
            label = {90: "3M", 180: "6M", 365: "1Y", 730: "2Y"}[days]
            forecasts[label] = self.strategic_forecast(days)
        return {
            "forecasts":    forecasts,
            "summary":      self._trajectory_summary(forecasts),
            "generated_at": time.time(),
        }

    def _trajectory_summary(self, forecasts: dict) -> dict:
        labels = list(forecasts.keys())
        if not labels:
            return {}
        first = forecasts[labels[0]]
        last  = forecasts[labels[-1]]
        health_now  = first.get("health_projection", {}).get("projected_score", 50)
        health_then = last.get("health_projection", {}).get("projected_score", 50)
        trajectory = ("IMPROVING" if health_then > health_now + 5 else
                      "DECLINING" if health_then < health_now - 5 else "STABLE")
        return {
            "trajectory":    trajectory,
            "health_now":    health_now,
            "health_2y":     health_then,
            "interpretation": f"PHOENIX institutional health projected to be {health_then:.0f}/100 in 2 years — {trajectory}",
        }

    # ── PEP-02: Scenario Planning ─────────────────────────────────────────────

    def scenario_plan(self, scenario_name: str, assumptions: Dict[str, Any]) -> dict:
        scenario_id = f"SCEN-{int(time.time()*1000)}"

        # Base case
        base = {
            "trust_score":     self._project_trust(365).get("projected_avg", 50),
            "aeg_readiness":   self._project_aeg(365).get("projected_readiness", 30),
            "health_score":    self._project_health(365).get("projected_score", 50),
        }

        # Perturb for scenarios
        best  = self._apply_optimistic(base, assumptions)
        worst = self._apply_pessimistic(base, assumptions)

        projected_states = {
            "3M":  self._apply_assumptions(self.strategic_forecast(90), assumptions, 0.3),
            "6M":  self._apply_assumptions(self.strategic_forecast(180), assumptions, 0.6),
            "1Y":  self._apply_assumptions(self.strategic_forecast(365), assumptions, 1.0),
        }

        recommended = self._recommend_from_scenario(assumptions, base, best, worst)

        scenario = Scenario(
            scenario_id=scenario_id, name=scenario_name, assumptions=assumptions,
            projected_states=projected_states, best_case=best, worst_case=worst,
            base_case=base, recommended_action=recommended,
        )
        return {
            "scenario_id":       scenario.scenario_id,
            "name":              scenario.name,
            "assumptions":       scenario.assumptions,
            "base_case":         scenario.base_case,
            "best_case":         scenario.best_case,
            "worst_case":        scenario.worst_case,
            "projected_states":  scenario.projected_states,
            "recommended_action": scenario.recommended_action,
            "generated_at":      scenario.generated_at,
        }

    def _apply_optimistic(self, base: dict, assumptions: dict) -> dict:
        mult = 1.0 + float(assumptions.get("optimism_factor", 0.20))
        return {k: round(min(100, v * mult), 1) for k, v in base.items()}

    def _apply_pessimistic(self, base: dict, assumptions: dict) -> dict:
        mult = 1.0 - float(assumptions.get("pessimism_factor", 0.20))
        return {k: round(max(0, v * mult), 1) for k, v in base.items()}

    def _apply_assumptions(self, forecast: dict, assumptions: dict, weight: float) -> dict:
        trust_mult   = 1.0 + float(assumptions.get("trust_acceleration", 0)) * weight
        aeg_mult     = 1.0 + float(assumptions.get("aeg_acceleration", 0)) * weight
        resource_adj = float(assumptions.get("resource_boost", 0)) * weight * 10
        hp = forecast.get("health_projection", {})
        return {
            "trust_score":    round(min(100, (hp.get("projected_score", 50) * trust_mult)), 1),
            "aeg_readiness":  round(min(100, (forecast.get("aeg_projection", {}).get("projected_readiness", 30) * aeg_mult)), 1),
            "health_score":   round(min(100, (hp.get("projected_score", 50) + resource_adj)), 1),
        }

    def _recommend_from_scenario(self, assumptions, base, best, worst) -> str:
        gap = best.get("health_score", 0) - worst.get("health_score", 0)
        if gap > 20:
            return "High variance scenario — focus on risk reduction to secure base case"
        if base.get("aeg_readiness", 0) < 40:
            return "AEG readiness critical bottleneck — prioritise shadow validation"
        if base.get("trust_score", 0) < 50:
            return "Trust score trajectory weak — accelerate evidence accumulation"
        return "Continue current trajectory — all indicators trending positively"

    # ── PEP-03: Institutional Future-State Modeling ───────────────────────────

    def institutional_forecast(self) -> dict:
        """Full future-state model across all horizons with trajectory analysis."""
        multi = self.multi_horizon_forecast()
        current_health = self._current_health()
        risk_forecast  = self._get_risk_forecast()

        # Milestones projected to complete within each horizon
        milestone_projections = self._project_milestones()

        return {
            "current_health":         current_health,
            "multi_horizon_forecast": multi,
            "milestone_projections":  milestone_projections,
            "risk_outlook":           risk_forecast,
            "institutional_trajectory": multi.get("summary", {}),
            "generated_at":           time.time(),
        }

    # ── Projection Helpers ────────────────────────────────────────────────────

    def _project_trust(self, days: int) -> dict:
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            audit  = _tew.full_audit()
            total  = audit.get("total_evidence", 0)
            now    = time.time()
            rate   = total / max(1, (now - 1700000000) / 86400)
            projected_count = total + rate * days
        except Exception:
            projected_count = 10

        try:
            from core.trust.trust_validation_registry import trust_validation_registry as _tvr
            try:
                from config import PTP_PILLARS; pillars = PTP_PILLARS
            except Exception:
                pillars = ["RECOMMENDATION_ACCURACY"]
            scores = [_tvr.pillar_status(p).get("trust_score", 30) for p in pillars]
            avg_score = sum(scores) / len(scores)
        except Exception:
            avg_score = 30

        # Trust grows as evidence accumulates
        evidence_factor = min(1.0, projected_count / 100)
        projected_score = min(95, avg_score + evidence_factor * 20)
        return {
            "current_avg":     round(avg_score, 1),
            "projected_avg":   round(projected_score, 1),
            "projected_evidence": int(projected_count),
            "delta":           round(projected_score - avg_score, 1),
        }

    def _project_aeg(self, days: int) -> dict:
        try:
            from core.nexus.aeg_pipeline.aeg_validation_program import aeg_validation_program as _avp
            readiness = _avp.autonomy_readiness_index()
            current = readiness.get("readiness_score", 20)
        except Exception:
            current = 20

        # Readiness grows with shadow sessions and promotions
        daily_gain = max(0.05, (80 - current) / 730)  # model convergence toward 80
        projected  = min(90, current + daily_gain * days)
        return {
            "current_readiness":   round(current, 1),
            "projected_readiness": round(projected, 1),
            "daily_gain":          round(daily_gain, 3),
        }

    def _project_pcao(self, days: int) -> dict:
        try:
            from core.pcao.risk_office import risk_office as _ro
            dash = _ro.risk_dashboard()
            open_risks = dash.get("open_risks", 4)
        except Exception:
            open_risks = 4

        # Risks trend down over time with active management
        projected_risks = max(0, open_risks - int(days / 90))
        return {
            "current_open_risks":   open_risks,
            "projected_open_risks": projected_risks,
            "risk_reduction":       open_risks - projected_risks,
        }

    def _project_health(self, days: int) -> dict:
        trust_proj = self._project_trust(days)
        aeg_proj   = self._project_aeg(days)
        try:
            from core.nexus.institutional_health_index import institutional_health_index as _ihi
            current = _ihi.health_report().get("overall_score", 50)
        except Exception:
            current = 50

        trust_contrib = (trust_proj["projected_avg"] - trust_proj["current_avg"]) * 0.25
        aeg_contrib   = (aeg_proj["projected_readiness"] - aeg_proj["current_readiness"]) * 0.20
        projected     = min(95, current + trust_contrib + aeg_contrib)
        return {
            "current_score":   round(current, 1),
            "projected_score": round(projected, 1),
            "delta":           round(projected - current, 1),
        }

    def _current_health(self) -> dict:
        try:
            from core.nexus.institutional_health_index import institutional_health_index as _ihi
            return _ihi.health_report()
        except Exception:
            return {"overall_score": 50, "health_label": "UNKNOWN"}

    def _get_risk_forecast(self) -> dict:
        try:
            from core.pcao.risk_forecaster import risk_forecaster as _rf
            return _rf.forecast(horizon_days=365)
        except Exception:
            return {}

    def _project_milestones(self) -> List[dict]:
        try:
            from core.pcao.roadmap_engine import roadmap_engine as _re
            roadmap = _re.generate_roadmap()
            return [
                {
                    "milestone": m["title"],
                    "subsystem": m["subsystem"],
                    "state":     m["current_state"],
                    "est_weeks": m.get("estimated_weeks"),
                }
                for m in roadmap.get("milestones", [])
            ]
        except Exception:
            return []

    @staticmethod
    def _ser_state(s: FutureState) -> dict:
        return {
            "horizon_days":       s.horizon_days,
            "label":              s.label,
            "trust_projection":   s.trust_projection,
            "aeg_projection":     s.aeg_projection,
            "pcao_projection":    s.pcao_projection,
            "health_projection":  s.health_projection,
            "confidence":         s.confidence,
            "generated_at":       s.generated_at,
        }


# Singleton
strategic_forecast_engine = StrategicForecastEngine()
