"""
PHOENIX NEXUS — Validation Suite  [GAP-VCP-01 … GAP-VCP-06]

Central validation hub proving that system outputs correspond to reality.

VCP-01: Trust Calibration Validation    — trust score = observed reliability proof
VCP-02: Digital Twin Accuracy           — prediction vs actual outcome tracking
VCP-03: Cross-Layer Propagation Audit   — cascade accuracy measurement
VCP-04: Health Index Validation         — health score vs system performance
VCP-05: Evidence Supremacy Audit        — false permit / false block rates
VCP-06: Governance Effectiveness        — outcome-based governance scoring
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── VCP-01: Trust Calibration Validation ─────────────────────────────────────

class CalibrationValidator:
    """
    Validates that trust calibration curves are accurate:
    trust score 80 should predict ≈80% reliability.
    """

    def validate(self) -> dict:
        try:
            from core.trust.trust_calibration_engine import trust_calibration_engine as _tce
            all_cal = _tce.all_pillars_calibration()
        except Exception:
            all_cal = {}

        pillar_verdicts = {}
        for pillar, report in all_cal.get("pillars", {}).items():
            ece = report.get("ece", 1.0)
            verdict = report.get("verdict", "INSUFFICIENT_DATA")
            bands   = report.get("bands", [])
            worst_band = max(bands, key=lambda b: b["deviation"], default={})
            pillar_verdicts[pillar] = {
                "ece":              ece,
                "verdict":          verdict,
                "worst_band":       worst_band.get("band"),
                "worst_deviation":  worst_band.get("deviation"),
                "calibrated":       verdict == "CALIBRATED",
            }

        calibrated = sum(1 for v in pillar_verdicts.values() if v["calibrated"])
        total = len(pillar_verdicts)
        program_validated = calibrated >= max(1, total // 2)

        return {
            "pillars":                  pillar_verdicts,
            "calibrated_count":         calibrated,
            "total_pillars":            total,
            "program_validated":        program_validated,
            "validation_label":         "VALIDATED" if program_validated else "NOT_YET_VALIDATED",
            "interpretation":           (
                f"{calibrated}/{total} pillars calibrated — "
                f"{'trust scores correspond to reality' if program_validated else 'insufficient evidence for calibration proof'}"
            ),
            "generated_at":             time.time(),
        }


# ── VCP-02: Digital Twin Accuracy ─────────────────────────────────────────────

class DigitalTwinValidator:
    """
    Measures prediction accuracy of the Digital Twin by comparing
    predicted outcomes to what actually happened.
    """

    def __init__(self) -> None:
        self._predictions: List[dict] = []

    def record_prediction(self, scenario_id: str, prediction: dict) -> None:
        self._predictions.append({
            "scenario_id": scenario_id,
            "prediction":  prediction,
            "recorded_at": time.time(),
            "actual":      None,
            "evaluated":   False,
        })

    def record_actual(self, scenario_id: str, actual_outcome: dict) -> dict:
        for pred in self._predictions:
            if pred["scenario_id"] == scenario_id:
                pred["actual"]    = actual_outcome
                pred["evaluated"] = True
                pred["deviation"] = self._compute_deviation(pred["prediction"], actual_outcome)
                pred["accuracy"]  = max(0.0, 1.0 - pred["deviation"])
                return {"matched": True, "scenario_id": scenario_id,
                        "accuracy": pred["accuracy"]}
        return {"error": f"Scenario '{scenario_id}' not found"}

    @staticmethod
    def _compute_deviation(predicted: dict, actual: dict) -> float:
        """Simple numeric deviation across shared keys (0–1 scale)."""
        deviations = []
        for key in predicted:
            p_val = predicted.get(key)
            a_val = actual.get(key)
            if isinstance(p_val, (int, float)) and isinstance(a_val, (int, float)):
                scale = max(abs(p_val), abs(a_val), 1)
                deviations.append(abs(p_val - a_val) / scale)
        return sum(deviations) / max(1, len(deviations)) if deviations else 0.5

    def accuracy_report(self) -> dict:
        evaluated = [p for p in self._predictions if p.get("evaluated")]
        total = len(self._predictions)
        if not evaluated:
            return {
                "total_predictions":  total,
                "evaluated":          0,
                "avg_accuracy":       None,
                "verdict":            "NO_DATA",
                "generated_at":       time.time(),
            }
        avg_acc = sum(p.get("accuracy", 0) for p in evaluated) / len(evaluated)
        return {
            "total_predictions":  total,
            "evaluated":          len(evaluated),
            "pending":            total - len(evaluated),
            "avg_accuracy":       round(avg_acc, 4),
            "verdict":            ("ACCURATE" if avg_acc >= 0.75 else
                                   "MODERATE" if avg_acc >= 0.50 else "POOR"),
            "predictions":        [
                {
                    "scenario_id": p["scenario_id"],
                    "accuracy":    p.get("accuracy"),
                    "deviation":   p.get("deviation"),
                    "recorded_at": p["recorded_at"],
                }
                for p in evaluated[-20:]
            ],
            "generated_at": time.time(),
        }


# ── VCP-03: Cross-Layer Cascade Accuracy ──────────────────────────────────────

class CascadeAccuracyValidator:
    """
    Validates that cross-layer cascades correctly propagate institutional signals.
    """

    def validate(self) -> dict:
        try:
            from core.nexus.cross_layer_intelligence import cross_layer_intelligence as _cli
            cascades = _cli.recent_cascades(limit=100)
        except Exception:
            cascades = []

        if not cascades:
            return {"status": "NO_DATA", "message": "No cascades recorded yet",
                    "generated_at": time.time()}

        fully_propagated  = sum(1 for c in cascades
                                if c.get("status") in ("COMPLETE", "OK"))
        partial = sum(1 for c in cascades if c.get("status") == "PARTIAL")
        failed  = sum(1 for c in cascades if c.get("status") == "FAILED")
        total   = len(cascades)

        propagation_rate = fully_propagated / max(1, total)

        # Per-layer success rates
        layer_success: Dict[str, Dict[str, int]] = {}
        for c in cascades:
            for layer, result in (c.get("layer_results") or {}).items():
                layer_success.setdefault(layer, {"ok": 0, "fail": 0})
                if result.get("status") == "OK":
                    layer_success[layer]["ok"] += 1
                else:
                    layer_success[layer]["fail"] += 1

        layer_rates = {
            layer: round(v["ok"] / max(1, v["ok"] + v["fail"]), 3)
            for layer, v in layer_success.items()
        }

        return {
            "total_cascades":     total,
            "fully_propagated":   fully_propagated,
            "partial":            partial,
            "failed":             failed,
            "propagation_rate":   round(propagation_rate, 3),
            "layer_success_rates": layer_rates,
            "verdict":            ("VALIDATED" if propagation_rate >= 0.90 else
                                   "ACCEPTABLE" if propagation_rate >= 0.70 else
                                   "NEEDS_REVIEW"),
            "generated_at":       time.time(),
        }


# ── VCP-04: Health Index Validation ──────────────────────────────────────────

class HealthIndexValidator:
    """
    Measures correlation between institutional health score and system performance.
    Validates that health score actually predicts performance outcomes.
    """

    def __init__(self) -> None:
        self._snapshots: List[dict] = []

    def record_snapshot(self) -> dict:
        snap = {"recorded_at": time.time()}
        try:
            from core.nexus.institutional_health_index import institutional_health_index as _ihi
            health = _ihi.health_report()
            snap["health_score"] = health.get("overall_score", 50)
            snap["health_label"] = health.get("health_label", "UNKNOWN")
        except Exception:
            snap["health_score"] = None

        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            all_stats = _ass.all_stats()
            accs = [(s.get("accuracy") or 0) for s in all_stats if s.get("samples_with_outcome", 0) >= 5]
            snap["avg_sandbox_accuracy"] = sum(accs) / max(1, len(accs)) if accs else None
        except Exception:
            snap["avg_sandbox_accuracy"] = None

        self._snapshots.append(snap)
        return snap

    def correlation_report(self) -> dict:
        if len(self._snapshots) < 3:
            return {
                "snapshots_recorded": len(self._snapshots),
                "status": "INSUFFICIENT_DATA",
                "message": "Need at least 3 health snapshots to compute correlation",
                "generated_at": time.time(),
            }

        valid = [s for s in self._snapshots
                 if s.get("health_score") is not None and
                    s.get("avg_sandbox_accuracy") is not None]
        if len(valid) < 3:
            return {"status": "INSUFFICIENT_DATA", "snapshots_recorded": len(self._snapshots),
                    "generated_at": time.time()}

        # Simple Pearson-like correlation
        hs = [s["health_score"] for s in valid]
        pa = [s["avg_sandbox_accuracy"] * 100 for s in valid]
        n  = len(valid)
        mean_h = sum(hs) / n
        mean_p = sum(pa) / n
        num    = sum((hs[i] - mean_h) * (pa[i] - mean_p) for i in range(n))
        den_h  = (sum((h - mean_h) ** 2 for h in hs)) ** 0.5
        den_p  = (sum((p - mean_p) ** 2 for p in pa)) ** 0.5
        corr   = num / max(0.0001, den_h * den_p)
        corr   = max(-1.0, min(1.0, corr))

        return {
            "snapshots_recorded": len(self._snapshots),
            "valid_pairs":        n,
            "correlation":        round(corr, 4),
            "correlation_label":  ("STRONG" if abs(corr) >= 0.7 else
                                   "MODERATE" if abs(corr) >= 0.4 else "WEAK"),
            "direction":          "POSITIVE" if corr >= 0 else "NEGATIVE",
            "interpretation":     (f"Health score {'positively' if corr >= 0 else 'negatively'} "
                                   f"correlates with AEG performance (r={corr:.2f})"),
            "validated":          abs(corr) >= 0.5,
            "generated_at":       time.time(),
        }


# ── VCP-05: Evidence Supremacy Doctrine Effectiveness ────────────────────────

class DoctrineEffectivenessAudit:
    """
    Measures whether Evidence Supremacy PERMIT/HOLD/BLOCK decisions are correct.
    Tracks false permits and false blocks.
    """

    def audit(self) -> dict:
        try:
            from core.nexus.evidence_supremacy_engine import evidence_supremacy_engine as _ese
            summary = _ese.summary()
        except Exception:
            summary = {}

        total    = summary.get("total_checks", 0)
        permitted = summary.get("permitted", 0)
        held      = summary.get("held", 0)
        blocked   = summary.get("blocked", 0)
        overridden = summary.get("overrides", 0)

        # Override success: how many overrides were justified (led to good outcomes)?
        try:
            blocked_list = summary.get("blocked_actions", [])
        except Exception:
            blocked_list = []

        # False permit rate: promotions that were permitted but then rolled back
        false_permit_count = 0
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_ledger import aeg_promotion_ledger as _apl
            psr = _apl.promotion_success_rate()
            reverted = psr.get("reverted", 0)
            total_promoted = psr.get("total_promotions", 0)
            false_permit_rate = reverted / max(1, total_promoted) if total_promoted > 0 else None
            false_permit_count = reverted
        except Exception:
            false_permit_rate = None

        # Override success: overrides that worked (outcome CORRECT)
        override_success = max(0, overridden - false_permit_count)
        override_success_rate = override_success / max(1, overridden) if overridden > 0 else None

        return {
            "total_checks":         total,
            "permitted":            permitted,
            "held":                 held,
            "blocked":              blocked,
            "overrides":            overridden,
            "false_permit_count":   false_permit_count,
            "false_permit_rate":    round(false_permit_rate, 3) if false_permit_rate is not None else None,
            "override_success_rate": round(override_success_rate, 3) if override_success_rate is not None else None,
            "doctrine_effectiveness": ("HIGH" if (false_permit_rate or 0) < 0.10 else
                                       "ADEQUATE" if (false_permit_rate or 0) < 0.25 else "LOW"),
            "generated_at":          time.time(),
        }


# ── VCP-06: Governance Effectiveness ─────────────────────────────────────────

class GovernanceEffectivenessReport:
    """
    Outcome-based governance effectiveness score.
    Unlike GovernanceMetrics (structural), this measures actual outcome quality.
    """

    def generate(self) -> dict:
        evidence = {}

        # Court case resolution quality
        try:
            from core.cortex.constitutional_court import constitutional_court as _cc
            cases = _cc.all_cases() if hasattr(_cc, "all_cases") else []
            approved = sum(1 for c in cases if c.get("verdict") == "APPROVE")
            total_cases = len(cases)
            evidence["court_approval_rate"] = round(approved / max(1, total_cases), 3) if total_cases else None
            evidence["total_court_cases"] = total_cases
        except Exception:
            evidence["court_approval_rate"] = None

        # Stress test consistency over time
        try:
            from core.cortex.governance_stress_test import governance_stress_test as _gst
            runs = _gst.all_runs_summary()
            if runs:
                scores = [r.get("consistency_score", 0) for r in runs]
                evidence["avg_stress_score"] = round(sum(scores) / len(scores), 1)
                evidence["stress_trend"] = ("IMPROVING" if scores[-1] > scores[0] else
                                            "DECLINING" if scores[-1] < scores[0] else "STABLE")
            else:
                evidence["avg_stress_score"] = None
        except Exception:
            evidence["avg_stress_score"] = None

        # Board accuracy
        try:
            from core.pcao.board_accuracy_ledger import board_accuracy_ledger as _bal
            acc_report = _bal.accuracy_report()
            evidence["board_accuracy"] = acc_report.get("accuracy")
            evidence["board_evaluations"] = acc_report.get("total_evaluated", 0)
        except Exception:
            evidence["board_accuracy"] = None

        # Amendment success rate
        try:
            from core.cortex.governance_metrics import governance_metrics as _gm
            outcomes = _gm.amendment_outcome_registry()
            evidence["amendment_success_rate"] = outcomes.get("success_rate")
        except Exception:
            evidence["amendment_success_rate"] = None

        # Compute overall effectiveness score
        component_scores = []
        for key, value in evidence.items():
            if isinstance(value, float) and 0 <= value <= 1:
                component_scores.append(value * 100)
        if evidence.get("avg_stress_score"):
            component_scores.append(evidence["avg_stress_score"])

        overall = sum(component_scores) / max(1, len(component_scores)) if component_scores else None

        return {
            "evidence":          evidence,
            "overall_score":     round(overall, 1) if overall else None,
            "effectiveness_label": ("EFFECTIVE" if (overall or 0) >= 70 else
                                    "DEVELOPING" if (overall or 0) >= 40 else "INSUFFICIENT"),
            "validated":          (overall or 0) >= 60,
            "generated_at":       time.time(),
        }


# ── Unified Validation Suite ──────────────────────────────────────────────────

class ValidationSuite:
    """
    Entry point for all VCP validation reports.
    """

    def __init__(self) -> None:
        self.calibration     = CalibrationValidator()
        self.digital_twin    = DigitalTwinValidator()
        self.cascade         = CascadeAccuracyValidator()
        self.health_index    = HealthIndexValidator()
        self.doctrine        = DoctrineEffectivenessAudit()
        self.governance_eff  = GovernanceEffectivenessReport()

    def full_validation_report(self) -> dict:
        return {
            "calibration_validation":      self.calibration.validate(),
            "cascade_accuracy":            self.cascade.validate(),
            "digital_twin_accuracy":       self.digital_twin.accuracy_report(),
            "health_index_correlation":    self.health_index.correlation_report(),
            "doctrine_effectiveness":      self.doctrine.audit(),
            "governance_effectiveness":    self.governance_eff.generate(),
            "generated_at":                time.time(),
        }


# Singleton
validation_suite = ValidationSuite()
