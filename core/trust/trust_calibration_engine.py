"""
PHOENIX PTP — Trust Calibration Engine  [TP-03]

Proves that trust scores are statistically calibrated:
  If trust = 80, actual reliability should be ≈80%.

Method:
  1. Bucket all evidence records by trust score band at time of recording
  2. For each band, compute actual accuracy (correct / total)
  3. Calibration error = mean absolute deviation between band midpoint and actual accuracy
  4. Calibration curve = expected vs actual per band

Output:
  - Calibration curve per pillar
  - Expected Calibration Error (ECE)
  - Reliability diagram data
  - CALIBRATED / UNDER_CONFIDENT / OVER_CONFIDENT verdict
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


BANDS = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50),
         (50, 60), (60, 70), (70, 80), (80, 90), (90, 100)]


@dataclass
class CalibrationBand:
    low: float
    high: float
    midpoint: float
    sample_count: int
    correct_count: int
    actual_accuracy: float   # correct / sample_count
    expected_accuracy: float # midpoint / 100
    deviation: float         # |actual - expected|


@dataclass
class CalibrationReport:
    pillar: str
    bands: List[CalibrationBand]
    ece: float                  # Expected Calibration Error (0–1, lower is better)
    total_samples: int
    verdict: str                # CALIBRATED / OVER_CONFIDENT / UNDER_CONFIDENT / INSUFFICIENT_DATA
    generated_at: float = field(default_factory=time.time)


class TrustCalibrationEngine:
    """
    Computes trust score calibration curves to validate that trust scores
    predict actual recommendation reliability.
    """

    def calibration_report(self, pillar: str) -> dict:
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            evidence = _tew.for_pillar(pillar)
        except Exception:
            evidence = []

        try:
            from core.trust.trust_validation_registry import trust_validation_registry as _tvr
            status = _tvr.pillar_status(pillar)
            current_trust = status.get("trust_score", 50.0)
        except Exception:
            current_trust = 50.0

        # Group evidence by trust score band
        band_data: Dict[Tuple[float, float], List[dict]] = {b: [] for b in BANDS}
        for ev in evidence:
            score = ev.get("trust_score_at_recording", current_trust)
            for low, high in BANDS:
                if low <= score < high or (high == 100 and score == 100):
                    band_data[(low, high)].append(ev)
                    break

        bands = []
        weighted_error = 0.0
        total = sum(len(v) for v in band_data.values())

        for (low, high), items in band_data.items():
            n = len(items)
            if n == 0:
                continue
            correct = sum(1 for e in items if e.get("correct", False))
            actual_acc = correct / n
            midpoint = (low + high) / 2
            expected_acc = midpoint / 100.0
            deviation = abs(actual_acc - expected_acc)
            band = CalibrationBand(
                low=low, high=high, midpoint=midpoint,
                sample_count=n, correct_count=correct,
                actual_accuracy=round(actual_acc, 4),
                expected_accuracy=round(expected_acc, 4),
                deviation=round(deviation, 4),
            )
            bands.append(band)
            weighted_error += deviation * (n / max(1, total))

        ece = round(weighted_error, 4)

        if total < 20:
            verdict = "INSUFFICIENT_DATA"
        elif ece < 0.05:
            verdict = "CALIBRATED"
        else:
            # Determine direction of miscalibration
            over_sum = sum(b.actual_accuracy - b.expected_accuracy for b in bands if b.sample_count >= 3)
            verdict = "OVER_CONFIDENT" if over_sum < 0 else "UNDER_CONFIDENT"

        report = CalibrationReport(pillar=pillar, bands=bands, ece=ece,
                                   total_samples=total, verdict=verdict)
        return self._ser_report(report)

    def all_pillars_calibration(self) -> dict:
        try:
            from config import PTP_PILLARS
            pillars = PTP_PILLARS
        except Exception:
            pillars = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                       "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]
        reports = {p: self.calibration_report(p) for p in pillars}
        calibrated = sum(1 for r in reports.values() if r.get("verdict") == "CALIBRATED")
        return {
            "pillars": reports,
            "calibrated_count": calibrated,
            "total_pillars": len(pillars),
            "program_calibration_status": "PROVEN" if calibrated >= 3 else "ACCUMULATING",
        }

    def calibration_curve_data(self, pillar: str) -> List[dict]:
        report = self.calibration_report(pillar)
        return [
            {
                "band": f"{b['low']}-{b['high']}",
                "expected": b["expected_accuracy"],
                "actual": b["actual_accuracy"],
                "samples": b["sample_count"],
                "deviation": b["deviation"],
            }
            for b in report.get("bands", [])
        ]

    @staticmethod
    def _ser_report(r: CalibrationReport) -> dict:
        return {
            "pillar":         r.pillar,
            "ece":            r.ece,
            "total_samples":  r.total_samples,
            "verdict":        r.verdict,
            "generated_at":   r.generated_at,
            "bands": [
                {
                    "low":                b.low,
                    "high":               b.high,
                    "midpoint":           b.midpoint,
                    "sample_count":       b.sample_count,
                    "correct_count":      b.correct_count,
                    "actual_accuracy":    b.actual_accuracy,
                    "expected_accuracy":  b.expected_accuracy,
                    "deviation":          b.deviation,
                }
                for b in r.bands
            ],
        }


# Singleton
trust_calibration_engine = TrustCalibrationEngine()
