"""
PHOENIX PTP — Trust Error Classifier  [TP-04]

False Positive / False Negative Analysis:
  TP (True Positive):  Predicted correct → was correct
  TN (True Negative):  Predicted incorrect → was incorrect
  FP (False Positive): Predicted correct → was WRONG  (overconfidence)
  FN (False Negative): Predicted incorrect → was RIGHT (underconfidence)

Metrics:
  Precision  = TP / (TP + FP)
  Recall     = TP / (TP + FN)
  F1 Score   = 2 × Precision × Recall / (Precision + Recall)
  Error Rate = (FP + FN) / Total

Deliverable: Trust Error Audit per pillar + cross-pillar summary
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ErrorClassification:
    pillar: str
    tp: int
    tn: int
    fp: int
    fn: int
    total: int
    precision: float
    recall: float
    f1_score: float
    error_rate: float
    fp_rate: float    # FP / (FP + TN) — false alarm rate
    fn_rate: float    # FN / (FN + TP) — miss rate
    dominant_error: str  # FP / FN / BALANCED / INSUFFICIENT_DATA
    generated_at: float = field(default_factory=time.time)


class TrustErrorClassifier:
    """
    Classifies trust prediction errors by type to diagnose systematic biases.
    """

    def classify_pillar(self, pillar: str) -> dict:
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            evidence = _tew.for_pillar(pillar)
        except Exception:
            evidence = []

        # Each evidence record has: correct (bool), predicted_correct (bool, if available)
        # If predicted_correct is absent we use trust_score_at_recording > 50 as prediction
        tp = tn = fp = fn = 0
        for ev in evidence:
            actual_correct = bool(ev.get("correct", False))
            # Derive prediction: trust > 50 means we predicted it would be correct
            trust_at_rec = float(ev.get("trust_score_at_recording", 50.0))
            predicted_correct = trust_at_rec >= 50.0

            if predicted_correct and actual_correct:
                tp += 1
            elif (not predicted_correct) and (not actual_correct):
                tn += 1
            elif predicted_correct and (not actual_correct):
                fp += 1
            else:
                fn += 1

        total = tp + tn + fp + fn
        precision = tp / max(1, tp + fp)
        recall    = tp / max(1, tp + fn)
        f1        = 2 * precision * recall / max(0.0001, precision + recall)
        error_rate = (fp + fn) / max(1, total)
        fp_rate    = fp / max(1, fp + tn)
        fn_rate    = fn / max(1, fn + tp)

        if total < 10:
            dominant = "INSUFFICIENT_DATA"
        elif fp > fn * 1.5:
            dominant = "FP_DOMINANT"    # System overconfident
        elif fn > fp * 1.5:
            dominant = "FN_DOMINANT"    # System underconfident
        else:
            dominant = "BALANCED"

        c = ErrorClassification(
            pillar=pillar, tp=tp, tn=tn, fp=fp, fn=fn, total=total,
            precision=round(precision, 4), recall=round(recall, 4),
            f1_score=round(f1, 4), error_rate=round(error_rate, 4),
            fp_rate=round(fp_rate, 4), fn_rate=round(fn_rate, 4),
            dominant_error=dominant,
        )
        return self._ser(c)

    def all_pillars_audit(self) -> dict:
        try:
            from config import PTP_PILLARS
            pillars = PTP_PILLARS
        except Exception:
            pillars = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                       "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]

        reports = {p: self.classify_pillar(p) for p in pillars}
        fp_dominant = sum(1 for r in reports.values() if r.get("dominant_error") == "FP_DOMINANT")
        fn_dominant = sum(1 for r in reports.values() if r.get("dominant_error") == "FN_DOMINANT")
        balanced    = sum(1 for r in reports.values() if r.get("dominant_error") == "BALANCED")

        avg_f1 = sum(r.get("f1_score", 0) for r in reports.values()) / max(1, len(reports))
        avg_err = sum(r.get("error_rate", 0) for r in reports.values()) / max(1, len(reports))

        overall_bias = "FP_BIAS" if fp_dominant > fn_dominant else ("FN_BIAS" if fn_dominant > fp_dominant else "BALANCED")

        return {
            "pillars":        reports,
            "fp_dominant":    fp_dominant,
            "fn_dominant":    fn_dominant,
            "balanced":       balanced,
            "average_f1":     round(avg_f1, 4),
            "average_error_rate": round(avg_err, 4),
            "overall_bias":   overall_bias,
            "generated_at":   time.time(),
        }

    def error_summary(self, pillar: str) -> dict:
        report = self.classify_pillar(pillar)
        return {
            "pillar":         pillar,
            "total_evidence": report.get("total", 0),
            "fp":             report.get("fp", 0),
            "fn":             report.get("fn", 0),
            "precision":      report.get("precision"),
            "recall":         report.get("recall"),
            "f1_score":       report.get("f1_score"),
            "dominant_error": report.get("dominant_error"),
        }

    @staticmethod
    def _ser(c: ErrorClassification) -> dict:
        return {
            "pillar":         c.pillar,
            "tp":             c.tp,
            "tn":             c.tn,
            "fp":             c.fp,
            "fn":             c.fn,
            "total":          c.total,
            "precision":      c.precision,
            "recall":         c.recall,
            "f1_score":       c.f1_score,
            "error_rate":     c.error_rate,
            "fp_rate":        c.fp_rate,
            "fn_rate":        c.fn_rate,
            "dominant_error": c.dominant_error,
            "generated_at":   c.generated_at,
        }


# Singleton
trust_error_classifier = TrustErrorClassifier()
