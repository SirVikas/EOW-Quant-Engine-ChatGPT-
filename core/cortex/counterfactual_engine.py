"""
PHOENIX CORTEX — Counterfactual Engine  [CX-5 Extension]

Implements ARTICLE-008 of the PHOENIX Constitution:
  "A module shall not be declared the primary cause of a loss unless a
   counterfactual analysis shows the loss would not have occurred without
   that module's signal."

The Counterfactual Engine answers:
  "If module X were absent from this trade's decision chain,
   would the trade still have been executed?"

Methodology
───────────
  For each blamed module in a loss record:

  1. Identify the module's decisive signal (APPROVE / BUY / INCREASE)
  2. Determine if any other module in the chain already provided a
     conflicting or confirming signal that would have the same effect
  3. Classify the counterfactual:
       DECISIVE      — removing this module would have changed the outcome
       REDUNDANT     — other modules would have produced the same result
       AMPLIFYING    — module made a bad outcome worse but didn't cause it
       PERMISSIVE    — module allowed a bad signal through (gatekeeper role)

  4. Compute counterfactual confidence (0–1):
       Based on how many alternative signal sources existed and how
       strongly they contradict the blamed module's signal

  5. Update blame score:
       Final blame = original_blame × counterfactual_weight

  Counterfactual weights by classification:
    DECISIVE    → 1.0  (full blame confirmed)
    PERMISSIVE  → 0.8  (should have blocked, didn't)
    AMPLIFYING  → 0.4  (worsened but didn't cause)
    REDUNDANT   → 0.1  (outcome same without this module)
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Counterfactual Classifications ────────────────────────────────────────────

CF_DECISIVE   = "DECISIVE"
CF_PERMISSIVE = "PERMISSIVE"
CF_AMPLIFYING = "AMPLIFYING"
CF_REDUNDANT  = "REDUNDANT"

_CF_WEIGHTS = {
    CF_DECISIVE:   1.0,
    CF_PERMISSIVE: 0.8,
    CF_AMPLIFYING: 0.4,
    CF_REDUNDANT:  0.1,
}


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class CounterfactualEntry:
    module_key: str
    classification: str        # DECISIVE | PERMISSIVE | AMPLIFYING | REDUNDANT
    cf_confidence: float       # 0–1: how confident in this classification
    original_blame: float
    adjusted_blame: float
    reasoning: str
    alternative_sources: List[str] = field(default_factory=list)


@dataclass
class CounterfactualReport:
    trade_id: str
    entries: List[CounterfactualEntry]
    revised_primary_cause: str
    revised_primary_score: float
    analysis_confidence: float
    generated_at: float = field(default_factory=time.time)
    narrative: str = ""


# ── Engine ────────────────────────────────────────────────────────────────────

class CounterfactualEngine:
    """
    Performs counterfactual analysis on blame records to separate
    causation from correlation.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._reports: Dict[str, CounterfactualReport] = {}

    def analyse(self, blame_record: dict) -> CounterfactualReport:
        """
        Given a blame record (from blame_engine), compute counterfactual
        classifications for each blamed module.
        """
        trade_id = blame_record.get("trade_id", "unknown")
        entries  = blame_record.get("entries", [])

        # Build signal index: module_key → signal_value
        signal_map: Dict[str, str] = {
            e["module_key"]: str(e.get("signal_value", ""))
            for e in entries
        }

        cf_entries: List[CounterfactualEntry] = []

        for entry in entries:
            mod_key    = entry["module_key"]
            orig_blame = entry["blame_score"]
            role       = entry.get("role", "")
            sig_val    = str(entry.get("signal_value", ""))
            confidence = float(entry.get("signal_confidence", 0.5))

            classification, cf_conf, reasoning, alts = self._classify(
                mod_key, sig_val, role, signal_map, entries
            )

            adjusted = orig_blame * _CF_WEIGHTS[classification]

            cf_entries.append(CounterfactualEntry(
                module_key=mod_key,
                classification=classification,
                cf_confidence=round(cf_conf, 3),
                original_blame=round(orig_blame, 4),
                adjusted_blame=round(adjusted, 4),
                reasoning=reasoning,
                alternative_sources=alts,
            ))

        # Re-rank by adjusted blame
        cf_entries.sort(key=lambda e: e.adjusted_blame, reverse=True)
        if cf_entries:
            revised_primary = cf_entries[0].module_key
            revised_score   = cf_entries[0].adjusted_blame
        else:
            revised_primary = "unknown"
            revised_score   = 0.0

        # Overall analysis confidence: avg of individual cf_confidence values
        analysis_conf = (
            sum(e.cf_confidence for e in cf_entries) / len(cf_entries)
            if cf_entries else 0.0
        )

        decisive_modules = [e.module_key for e in cf_entries if e.classification == CF_DECISIVE]
        narrative = (
            f"Counterfactual analysis of trade {trade_id}: "
            f"{len(decisive_modules)} decisive module(s) identified — "
            f"{', '.join(decisive_modules) if decisive_modules else 'none'}. "
            f"Revised primary cause: '{revised_primary}' "
            f"(adjusted_blame={revised_score:.3f}). "
            f"Analysis confidence: {analysis_conf:.0%}."
        )

        report = CounterfactualReport(
            trade_id=trade_id,
            entries=cf_entries,
            revised_primary_cause=revised_primary,
            revised_primary_score=revised_score,
            analysis_confidence=round(analysis_conf, 3),
            narrative=narrative,
        )

        with self._lock:
            self._reports[trade_id] = report
            if len(self._reports) > 500:
                oldest = next(iter(self._reports))
                del self._reports[oldest]

        return report

    def get_report(self, trade_id: str) -> Optional[dict]:
        with self._lock:
            r = self._reports.get(trade_id)
        return self._serialise(r) if r else None

    def summary(self) -> dict:
        with self._lock:
            total = len(self._reports)
            decisive_counts: Dict[str, int] = {}
            for r in self._reports.values():
                for e in r.entries:
                    if e.classification == CF_DECISIVE:
                        decisive_counts[e.module_key] = decisive_counts.get(e.module_key, 0) + 1
        top_decisive = sorted(decisive_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return {
            "total_analyses": total,
            "top_decisive_modules": [{"module": k, "count": v} for k, v in top_decisive],
        }

    # ── Classification Logic ──────────────────────────────────────────────────

    @staticmethod
    def _classify(
        module_key: str,
        signal_value: str,
        role: str,
        signal_map: Dict[str, str],
        all_entries: List[dict],
    ):
        """
        Classify a module's counterfactual role in a losing trade.
        Returns (classification, confidence, reasoning, alternative_sources).
        """
        # Find other modules with the same signal direction
        confirming: List[str] = []
        blocking: List[str]   = []

        for other_key, other_sig in signal_map.items():
            if other_key == module_key:
                continue
            if CounterfactualEngine._same_direction(signal_value, other_sig):
                confirming.append(other_key)
            elif CounterfactualEngine._opposite_direction(signal_value, other_sig):
                blocking.append(other_key)

        # Risk/governance modules: were they the gatekeeper that let it through?
        if role in ("risk", "governance"):
            if signal_value in ("APPROVE", "ALLOW", "OPEN"):
                # They approved — are they DECISIVE or REDUNDANT?
                other_approvers = [k for k in confirming
                                   if any(e["module_key"] == k and
                                          e.get("role") in ("risk", "governance")
                                          for e in all_entries)]
                if other_approvers:
                    return (
                        CF_REDUNDANT, 0.6,
                        f"Other governance modules ({other_approvers}) also approved.",
                        other_approvers,
                    )
                # Sole gatekeeper — permissive
                return (
                    CF_PERMISSIVE, 0.8,
                    f"'{module_key}' was the sole gatekeeper that approved this trade.",
                    [],
                )

        # Signal modules: would the trade have entered without this module's signal?
        if role == "signal":
            if confirming:
                # Other signals agreed — this one is redundant
                return (
                    CF_REDUNDANT, 0.7,
                    f"Other signal modules ({confirming[:3]}) produced the same direction.",
                    confirming[:3],
                )
            elif blocking:
                # This module's signal overrode a blocking signal — it was decisive
                return (
                    CF_DECISIVE, 0.85,
                    f"Without '{module_key}', blocking signals ({blocking[:2]}) "
                    "would have prevented the trade.",
                    [],
                )
            else:
                # Only signal in this direction — decisive
                return (
                    CF_DECISIVE, 0.75,
                    f"'{module_key}' was the only module signaling this direction.",
                    [],
                )

        # Capital/execution modules: they amplify, they don't cause
        if role in ("capital", "execution"):
            return (
                CF_AMPLIFYING, 0.7,
                f"'{module_key}' sized/executed the trade but did not originate the signal.",
                [],
            )

        # Default: classify as amplifying with low confidence
        return (
            CF_AMPLIFYING, 0.4,
            f"Role '{role}' is supporting — not primary causal.",
            [],
        )

    @staticmethod
    def _same_direction(a: str, b: str) -> bool:
        _LONG  = {"BUY", "LONG", "APPROVE", "INCREASE"}
        _SHORT = {"SELL", "SHORT", "REJECT", "REDUCE"}
        return (a in _LONG and b in _LONG) or (a in _SHORT and b in _SHORT)

    @staticmethod
    def _opposite_direction(a: str, b: str) -> bool:
        _LONG  = {"BUY", "LONG", "APPROVE", "INCREASE"}
        _SHORT = {"SELL", "SHORT", "REJECT", "REDUCE"}
        return (a in _LONG and b in _SHORT) or (a in _SHORT and b in _LONG)

    @staticmethod
    def _serialise(r: CounterfactualReport) -> dict:
        return {
            "trade_id":              r.trade_id,
            "revised_primary_cause": r.revised_primary_cause,
            "revised_primary_score": r.revised_primary_score,
            "analysis_confidence":   r.analysis_confidence,
            "narrative":             r.narrative,
            "generated_at":          r.generated_at,
            "entries": [
                {
                    "module_key":        e.module_key,
                    "classification":    e.classification,
                    "cf_confidence":     e.cf_confidence,
                    "original_blame":    e.original_blame,
                    "adjusted_blame":    e.adjusted_blame,
                    "reasoning":         e.reasoning,
                    "alternative_sources": e.alternative_sources,
                }
                for e in r.entries
            ],
        }


# Singleton
counterfactual_engine = CounterfactualEngine()
