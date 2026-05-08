"""
EOW Quant Engine — Delta Reporter  (FTD-053-GAIA Phase 2)

Compares consecutive compressed snapshots and surfaces only meaningful changes.
Prevents redundant writes and AI token waste by gating on significance thresholds.

Design principles:
  • DELTA-FIRST   — only report when a metric changes beyond its significance floor
  • TOKEN-SAFE    — identical or trivially-different snapshots are suppressed
  • NON-THROWING  — all methods catch internally; never halts trading engine
  • READ-ONLY     — zero mutation of engine state
  • ADDITIVE      — layered on top of Phase 1 compression without modifying it

Delta significance thresholds (per field):
  Each field has a min_delta that must be exceeded before the field is
  considered "meaningfully changed" and included in the delta report.
  Tiny floating-point drift is suppressed.

Delta report structure:
  {
    "delta_ts":           int (ms),
    "prev_ts":            int (ms),
    "elapsed_secs":       float,
    "changed_fields":     {field: {prev, curr, abs_delta, rel_delta_pct}},
    "new_fields":         {field: value},    # appeared in curr, absent in prev
    "removed_fields":     [field, ...],      # in prev, absent in curr
    "significance_score": float (0–100),     # how important is this delta
    "has_meaningful_delta": bool,
    "summary":            str,               # one-line human-readable
  }
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


# ── Significance thresholds (per compressed field) ────────────────────────────
# If abs(curr - prev) < threshold → field is not "meaningfully changed"
# Thresholds calibrated to suppress sensor noise while catching real drift.

_FIELD_THRESHOLDS: Dict[str, float] = {
    "pnl":               0.50,   # $0.50 PnL change
    "n_trades":          1.0,    # 1 additional trade
    "profit_factor":     0.05,
    "win_rate":          0.02,   # 2 percentage points
    "rl_contexts":       2.0,
    "rl_decisions":      5.0,
    "iq_score":          2.0,    # 2 IQ points
    "rl_toxic":          1.0,    # any new toxic context
    "rl_allow_rate":     0.03,
    "rl_profitable_pct": 2.0,
    "rl_maturity_pct":   3.0,
    "le_trending_wr":    0.03,
    "le_mean_rev_wr":    0.03,
    "le_vol_exp_wr":     0.03,
    "consec_losses":     1.0,
    "daily_trades":      1.0,
    "uptime_secs":       300.0,  # 5-minute uptime change is noise
    "error_count":       1.0,
}

# Fields where ANY change (regardless of magnitude) is significant
_ALWAYS_SIGNIFICANT: frozenset = frozenset({
    "risk_halted",
    "gate_open",
    "regime",
    "rl_maturity_status",
    "rl_explore_pressure",
    "rl_confidence_dir",
})

# Significance score weights — how much each changed field contributes to
# the overall significance score (0–100).
_SIGNIFICANCE_WEIGHTS: Dict[str, float] = {
    "risk_halted":       30.0,
    "gate_open":         25.0,
    "rl_toxic":          20.0,
    "consec_losses":     15.0,
    "iq_score":          10.0,
    "pnl":               8.0,
    "win_rate":          8.0,
    "rl_allow_rate":     7.0,
    "rl_confidence_dir": 6.0,
    "regime":            6.0,
    "profit_factor":     5.0,
    "rl_maturity_status":4.0,
}
_DEFAULT_WEIGHT = 2.0

# Minimum significance score to trigger a "meaningful delta" flag
MEANINGFUL_DELTA_THRESHOLD = 5.0


class DeltaReporter:
    """
    Stateful delta reporter: keeps the last compressed snapshot and compares
    each new snapshot against it to produce a structured delta report.
    """

    MODULE  = "DELTA_REPORTER"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._prev_snapshot: Optional[Dict[str, Any]] = None
        self._total_reports:   int = 0
        self._total_suppressed: int = 0
        self._total_meaningful: int = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def compute_delta(
        self,
        current: Dict[str, Any],
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Compare current compressed snapshot against the previous one.

        Returns a delta report dict. If there is no previous snapshot, the
        first call always returns a "baseline" report (no prev to diff against).

        Args:
            current: compressed snapshot from IntelligenceCompressor.compress()
            force:   if True, suppress the significance gate (always report)
        """
        try:
            now_ms = int(time.time() * 1000)
            prev   = self._prev_snapshot

            if prev is None:
                # First snapshot — emit baseline
                report = self._baseline_report(current, now_ms)
                self._prev_snapshot = current
                self._total_reports += 1
                return report

            elapsed_secs = (now_ms - prev.get("_compressed_ts", now_ms)) / 1000.0

            changed, new_fields, removed = self._diff(prev, current)
            score = self._significance_score(changed, new_fields, removed)

            has_delta = force or (score >= MEANINGFUL_DELTA_THRESHOLD)

            if not has_delta:
                self._total_suppressed += 1

            report = {
                "module":              self.MODULE,
                "version":             self.VERSION,
                "delta_ts":            now_ms,
                "prev_ts":             prev.get("_compressed_ts", 0),
                "elapsed_secs":        round(elapsed_secs, 1),
                "changed_fields":      changed,
                "new_fields":          new_fields,
                "removed_fields":      removed,
                "significance_score":  round(score, 2),
                "has_meaningful_delta": has_delta,
                "summary":             self._summarize(changed, new_fields, removed, score),
                "suppressed_count":    self._total_suppressed,
            }

            # Update state regardless (always track latest)
            self._prev_snapshot = current
            self._total_reports += 1
            if has_delta:
                self._total_meaningful += 1

            return report

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] compute_delta error: {exc}")
            return {
                "module": self.MODULE,
                "error":  str(exc),
                "delta_ts": int(time.time() * 1000),
                "has_meaningful_delta": False,
            }

    def reset(self) -> None:
        """Clear state — forces next call to treat current as baseline."""
        self._prev_snapshot = None

    def stats(self) -> Dict[str, Any]:
        return {
            "module":             self.MODULE,
            "version":            self.VERSION,
            "total_reports":      self._total_reports,
            "total_suppressed":   self._total_suppressed,
            "total_meaningful":   self._total_meaningful,
            "has_baseline":       self._prev_snapshot is not None,
            "meaningful_ratio":   round(
                self._total_meaningful / max(self._total_reports, 1), 3
            ),
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _diff(
        self,
        prev: Dict[str, Any],
        curr: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
        """
        Three-way diff:
          changed     — fields present in both but meaningfully different
          new_fields  — fields in curr but not in prev
          removed     — fields in prev but not in curr

        Skips internal metadata fields (_checksum, _compressed_ts, etc.)
        """
        skip = {"_checksum", "_compressed_ts", "_schema_version", "_field_count"}

        prev_keys = {k for k in prev if k not in skip}
        curr_keys = {k for k in curr if k not in skip}

        new_fields: Dict[str, Any] = {
            k: curr[k] for k in (curr_keys - prev_keys)
        }
        removed: List[str] = list(prev_keys - curr_keys)

        changed: Dict[str, Any] = {}
        for k in prev_keys & curr_keys:
            pv = prev[k]
            cv = curr[k]

            if k in _ALWAYS_SIGNIFICANT:
                if pv != cv:
                    changed[k] = _field_delta(k, pv, cv)
                continue

            # Numeric comparison with threshold
            if isinstance(pv, (int, float)) and isinstance(cv, (int, float)):
                thresh = _FIELD_THRESHOLDS.get(k, 0.0)
                if abs(cv - pv) >= thresh:
                    changed[k] = _field_delta(k, pv, cv)
            elif pv != cv:
                changed[k] = _field_delta(k, pv, cv)

        return changed, new_fields, removed

    def _significance_score(
        self,
        changed: Dict[str, Any],
        new_fields: Dict[str, Any],
        removed: List[str],
    ) -> float:
        score = 0.0
        for field in changed:
            score += _SIGNIFICANCE_WEIGHTS.get(field, _DEFAULT_WEIGHT)
        for field in new_fields:
            score += _SIGNIFICANCE_WEIGHTS.get(field, _DEFAULT_WEIGHT) * 0.5
        score += len(removed) * 1.0
        return min(score, 100.0)

    def _summarize(
        self,
        changed: Dict[str, Any],
        new_fields: Dict[str, Any],
        removed: List[str],
        score: float,
    ) -> str:
        if not changed and not new_fields and not removed:
            return "No meaningful change detected"

        parts = []
        if "risk_halted" in changed:
            parts.append(f"RISK_HALTED→{changed['risk_halted']['curr']}")
        if "gate_open" in changed:
            parts.append(f"GATE→{changed['gate_open']['curr']}")
        if "rl_toxic" in changed:
            d = changed["rl_toxic"]
            parts.append(f"toxics {d['prev']}→{d['curr']}")
        if "iq_score" in changed:
            d = changed["iq_score"]
            parts.append(f"IQ {d['prev']}→{d['curr']}")
        if "pnl" in changed:
            d = changed["pnl"]
            parts.append(f"PnL {d['prev']}→{d['curr']}")
        if "consec_losses" in changed:
            d = changed["consec_losses"]
            parts.append(f"consec_loss {d['prev']}→{d['curr']}")
        if "regime" in changed:
            d = changed["regime"]
            parts.append(f"regime {d['prev']}→{d['curr']}")

        remaining = len(changed) - len(parts)
        if remaining > 0:
            parts.append(f"+{remaining} fields")

        summary = ", ".join(parts) if parts else f"{len(changed)} fields changed"
        return f"[score={score:.0f}] {summary}"

    def _baseline_report(
        self,
        current: Dict[str, Any],
        now_ms: int,
    ) -> Dict[str, Any]:
        return {
            "module":               self.MODULE,
            "version":              self.VERSION,
            "delta_ts":             now_ms,
            "prev_ts":              0,
            "elapsed_secs":         0.0,
            "changed_fields":       {},
            "new_fields":           {k: v for k, v in current.items()
                                     if not k.startswith("_")},
            "removed_fields":       [],
            "significance_score":   0.0,
            "has_meaningful_delta": True,   # first snapshot always emitted
            "summary":              "Baseline snapshot established",
            "suppressed_count":     0,
            "is_baseline":          True,
        }


# ── Field delta helper ────────────────────────────────────────────────────────

def _field_delta(field: str, prev: Any, curr: Any) -> Dict[str, Any]:
    """Compute structured delta entry for a single field."""
    entry: Dict[str, Any] = {"prev": prev, "curr": curr}
    if isinstance(prev, (int, float)) and isinstance(curr, (int, float)):
        abs_d = round(curr - prev, 4)
        rel_d = round((abs_d / prev * 100) if prev != 0 else 0.0, 2)
        entry["abs_delta"]     = abs_d
        entry["rel_delta_pct"] = rel_d
    return entry


# ── Module-level singleton ────────────────────────────────────────────────────
delta_reporter = DeltaReporter()
