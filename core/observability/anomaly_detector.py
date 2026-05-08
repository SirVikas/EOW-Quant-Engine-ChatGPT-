"""
EOW Quant Engine — Anomaly Detector  (FTD-053-GAIA Phase 2)

Monitors compressed intelligence snapshots for anomalous conditions and
classifies each finding by severity: CRITICAL / HIGH / MEDIUM / LOW.

Design principles:
  • ANOMALY-FIRST  — surfaces WHAT MATTERS, not just what changed
  • SEVERITY-GATED — only HIGH/CRITICAL anomalies trigger urgent action
  • NON-THROWING   — all methods catch internally; never halts trading engine
  • STATEFUL       — tracks anomaly history to detect trend-based patterns
  • BOUNDED MEMORY — anomaly log capped at MAX_HISTORY entries

Severity levels:
  CRITICAL — requires immediate attention; trading may be impaired
  HIGH     — significant degradation trend; action likely needed soon
  MEDIUM   — concerning drift; worth monitoring
  LOW      — minor deviation from healthy baseline; informational only

Anomaly categories:
  RISK_STATE       — halted flag, gate closed
  TOXIC_SPIKE      — sudden increase in toxic RL contexts
  LOSS_STREAK      — consecutive losses exceeding threshold
  IQ_REGRESSION    — intelligence score drop
  ALLOW_COLLAPSE   — trade allow rate below safe floor
  WIN_RATE_EROSION — regime win rate falling below healthy band
  CONFIDENCE_FLIP  — RL confidence direction reversal
  REGIME_SHIFT     — market regime change (informational)
  MATURITY_STALL   — RL learning maturity not progressing

Anomaly event structure:
  {
    "anomaly_id":    str,        # short deterministic ID
    "severity":      str,        # CRITICAL | HIGH | MEDIUM | LOW
    "category":      str,
    "description":   str,        # human-readable
    "metric":        str,        # field name that triggered
    "current_value": Any,
    "threshold":     Any,        # what boundary was crossed
    "delta":         Any,        # change from previous (if available)
    "ts":            int,        # epoch ms
  }
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger


# ── Severity constants ────────────────────────────────────────────────────────

SEV_CRITICAL = "CRITICAL"
SEV_HIGH     = "HIGH"
SEV_MEDIUM   = "MEDIUM"
SEV_LOW      = "LOW"

_SEV_ORDER = {SEV_CRITICAL: 4, SEV_HIGH: 3, SEV_MEDIUM: 2, SEV_LOW: 1}

# ── Detection thresholds ──────────────────────────────────────────────────────

# Consecutive losses
CONSEC_LOSS_CRITICAL  = 7
CONSEC_LOSS_HIGH      = 5
CONSEC_LOSS_MEDIUM    = 3

# IQ score thresholds (absolute, not relative)
IQ_CRITICAL_FLOOR     = 20.0   # IQ below 20 → CRITICAL
IQ_HIGH_FLOOR         = 35.0   # IQ below 35 → HIGH
IQ_MEDIUM_FLOOR       = 50.0   # IQ below 50 → MEDIUM

# IQ drop thresholds (session-relative)
IQ_DROP_HIGH          = 20.0   # ≥ 20pt drop → HIGH
IQ_DROP_MEDIUM        = 10.0   # ≥ 10pt drop → MEDIUM

# Allow rate thresholds
ALLOW_CRITICAL_FLOOR  = 0.30   # < 30% allow rate → CRITICAL
ALLOW_HIGH_FLOOR      = 0.50   # < 50% → HIGH
ALLOW_MEDIUM_FLOOR    = 0.65   # < 65% → MEDIUM

# Win rate thresholds (per regime)
WR_HIGH_FLOOR         = 0.35   # < 35% win rate → HIGH
WR_MEDIUM_FLOOR       = 0.42   # < 42% → MEDIUM

# Toxic context thresholds
TOXIC_CRITICAL        = 5      # ≥ 5 toxic contexts → CRITICAL
TOXIC_HIGH            = 3      # ≥ 3 → HIGH
TOXIC_MEDIUM          = 1      # ≥ 1 → MEDIUM

# Max stored anomaly history entries
MAX_HISTORY           = 200


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class AnomalyEvent:
    anomaly_id:    str
    severity:      str
    category:      str
    description:   str
    metric:        str
    current_value: Any
    threshold:     Any
    delta:         Any
    ts:            int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_id":    self.anomaly_id,
            "severity":      self.severity,
            "category":      self.category,
            "description":   self.description,
            "metric":        self.metric,
            "current_value": self.current_value,
            "threshold":     self.threshold,
            "delta":         self.delta,
            "ts":            self.ts,
        }


@dataclass
class DetectorStats:
    total_scans:      int = 0
    total_anomalies:  int = 0
    critical_count:   int = 0
    high_count:       int = 0
    medium_count:     int = 0
    low_count:        int = 0
    last_scan_ts:     int = 0


class AnomalyDetector:
    """
    Rule-based anomaly detector over compressed intelligence snapshots.
    Stateful: tracks session-level peak IQ to detect regressions.
    """

    MODULE  = "ANOMALY_DETECTOR"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._stats         = DetectorStats()
        self._history:  List[AnomalyEvent] = []
        self._peak_iq:  float = 0.0       # session peak IQ (for regression detection)
        self._prev_snapshot: Optional[Dict[str, Any]] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def scan(
        self,
        snapshot: Dict[str, Any],
        delta_report: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scan a compressed snapshot for anomalies.
        Optionally uses the delta report for trend-aware detection.

        Returns a list of anomaly event dicts, sorted by severity descending.
        Empty list = no anomalies detected.
        Never raises.
        """
        try:
            now_ms = int(time.time() * 1000)
            events: List[AnomalyEvent] = []

            # ── Risk state ─────────────────────────────────────────────────
            events.extend(self._check_risk_state(snapshot, now_ms))

            # ── Toxic contexts ─────────────────────────────────────────────
            events.extend(self._check_toxics(snapshot, now_ms))

            # ── Consecutive losses ─────────────────────────────────────────
            events.extend(self._check_loss_streak(snapshot, now_ms))

            # ── IQ regression ──────────────────────────────────────────────
            events.extend(self._check_iq(snapshot, now_ms))

            # ── Allow rate collapse ────────────────────────────────────────
            events.extend(self._check_allow_rate(snapshot, now_ms))

            # ── Win rate erosion per regime ────────────────────────────────
            events.extend(self._check_win_rates(snapshot, now_ms))

            # ── Confidence direction flip ──────────────────────────────────
            events.extend(self._check_confidence_flip(snapshot, now_ms))

            # ── Regime shift ───────────────────────────────────────────────
            events.extend(self._check_regime_shift(snapshot, now_ms))

            # Sort by severity descending
            events.sort(key=lambda e: _SEV_ORDER.get(e.severity, 0), reverse=True)

            # Update state
            self._stats.total_scans  += 1
            self._stats.last_scan_ts  = now_ms
            self._store_events(events)
            self._prev_snapshot = snapshot

            return [e.to_dict() for e in events]

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] scan error: {exc}")
            return []

    def get_active_summary(self) -> Dict[str, Any]:
        """
        Returns a severity-bucketed summary of recent anomalies.
        Considers the last 10 anomaly events.
        """
        try:
            recent = self._history[-10:] if self._history else []
            buckets: Dict[str, List[str]] = {
                SEV_CRITICAL: [],
                SEV_HIGH: [],
                SEV_MEDIUM: [],
                SEV_LOW: [],
            }
            for ev in recent:
                buckets.get(ev.severity, []).append(ev.description)

            worst = SEV_LOW
            for sev in (SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW):
                if buckets[sev]:
                    worst = sev
                    break

            return {
                "module":           self.MODULE,
                "version":          self.VERSION,
                "worst_severity":   worst if any(buckets.values()) else "NONE",
                "anomaly_counts":   {k: len(v) for k, v in buckets.items()},
                "recent_critical":  buckets[SEV_CRITICAL][:3],
                "recent_high":      buckets[SEV_HIGH][:3],
                "total_anomalies":  self._stats.total_anomalies,
                "total_scans":      self._stats.total_scans,
            }
        except Exception as exc:
            return {"module": self.MODULE, "error": str(exc)}

    def stats(self) -> Dict[str, Any]:
        s = self._stats
        return {
            "module":          self.MODULE,
            "version":         self.VERSION,
            "total_scans":     s.total_scans,
            "total_anomalies": s.total_anomalies,
            "critical_count":  s.critical_count,
            "high_count":      s.high_count,
            "medium_count":    s.medium_count,
            "low_count":       s.low_count,
            "peak_iq":         self._peak_iq,
            "last_scan_ts":    s.last_scan_ts,
        }

    def get_history(self, limit: int = 50, min_severity: str = SEV_LOW) -> List[Dict[str, Any]]:
        """Return recent anomaly history filtered by minimum severity."""
        min_order = _SEV_ORDER.get(min_severity, 0)
        filtered = [
            e.to_dict() for e in reversed(self._history)
            if _SEV_ORDER.get(e.severity, 0) >= min_order
        ]
        return filtered[:limit]

    # ── Detection rules ───────────────────────────────────────────────────────

    def _check_risk_state(self, snap: Dict, ts: int) -> List[AnomalyEvent]:
        events = []

        if snap.get("risk_halted") is True:
            events.append(_make_event(
                severity=SEV_CRITICAL,
                category="RISK_STATE",
                description="Trading engine is HALTED by risk controller",
                metric="risk_halted",
                current_value=True,
                threshold=False,
                delta=None,
                ts=ts,
            ))

        if snap.get("gate_open") is False:
            events.append(_make_event(
                severity=SEV_HIGH,
                category="RISK_STATE",
                description="Trade gate is CLOSED — no new trades permitted",
                metric="gate_open",
                current_value=False,
                threshold=True,
                delta=None,
                ts=ts,
            ))

        return events

    def _check_toxics(self, snap: Dict, ts: int) -> List[AnomalyEvent]:
        n_toxic = snap.get("rl_toxic")
        if n_toxic is None:
            return []

        prev_toxic = (self._prev_snapshot or {}).get("rl_toxic", 0)
        delta = n_toxic - prev_toxic if prev_toxic is not None else None

        if n_toxic >= TOXIC_CRITICAL:
            sev = SEV_CRITICAL
            desc = f"{n_toxic} toxic RL contexts blocked — engine severely degraded"
        elif n_toxic >= TOXIC_HIGH:
            sev = SEV_HIGH
            desc = f"{n_toxic} toxic RL contexts — significant learning degradation"
        elif n_toxic >= TOXIC_MEDIUM:
            sev = SEV_MEDIUM
            desc = f"{n_toxic} toxic RL context detected"
        else:
            return []

        return [_make_event(
            severity=sev, category="TOXIC_SPIKE",
            description=desc, metric="rl_toxic",
            current_value=n_toxic, threshold=TOXIC_MEDIUM,
            delta=delta, ts=ts,
        )]

    def _check_loss_streak(self, snap: Dict, ts: int) -> List[AnomalyEvent]:
        cl = snap.get("consec_losses")
        if cl is None:
            return []

        prev_cl = (self._prev_snapshot or {}).get("consec_losses", 0)
        delta = cl - prev_cl if prev_cl is not None else None

        if cl >= CONSEC_LOSS_CRITICAL:
            sev = SEV_CRITICAL
            desc = f"{cl} consecutive losses — risk controls may need review"
        elif cl >= CONSEC_LOSS_HIGH:
            sev = SEV_HIGH
            desc = f"{cl} consecutive losses — significant losing streak"
        elif cl >= CONSEC_LOSS_MEDIUM:
            sev = SEV_MEDIUM
            desc = f"{cl} consecutive losses"
        else:
            return []

        return [_make_event(
            severity=sev, category="LOSS_STREAK",
            description=desc, metric="consec_losses",
            current_value=cl, threshold=CONSEC_LOSS_MEDIUM,
            delta=delta, ts=ts,
        )]

    def _check_iq(self, snap: Dict, ts: int) -> List[AnomalyEvent]:
        iq = snap.get("iq_score")
        if iq is None:
            return []

        # Update session peak
        if iq > self._peak_iq:
            self._peak_iq = iq

        events = []
        prev_iq = (self._prev_snapshot or {}).get("iq_score", iq)
        delta = iq - prev_iq

        # Absolute floor checks
        if iq < IQ_CRITICAL_FLOOR:
            events.append(_make_event(
                severity=SEV_CRITICAL, category="IQ_REGRESSION",
                description=f"Intelligence score critically low: {iq:.0f}/100",
                metric="iq_score", current_value=iq,
                threshold=IQ_CRITICAL_FLOOR, delta=round(delta, 1), ts=ts,
            ))
        elif iq < IQ_HIGH_FLOOR:
            events.append(_make_event(
                severity=SEV_HIGH, category="IQ_REGRESSION",
                description=f"Intelligence score low: {iq:.0f}/100",
                metric="iq_score", current_value=iq,
                threshold=IQ_HIGH_FLOOR, delta=round(delta, 1), ts=ts,
            ))
        elif iq < IQ_MEDIUM_FLOOR:
            events.append(_make_event(
                severity=SEV_MEDIUM, category="IQ_REGRESSION",
                description=f"Intelligence score below target: {iq:.0f}/100",
                metric="iq_score", current_value=iq,
                threshold=IQ_MEDIUM_FLOOR, delta=round(delta, 1), ts=ts,
            ))

        # Relative drop from session peak
        if self._peak_iq > 0 and events == []:
            drop = self._peak_iq - iq
            if drop >= IQ_DROP_HIGH:
                events.append(_make_event(
                    severity=SEV_HIGH, category="IQ_REGRESSION",
                    description=f"IQ dropped {drop:.0f}pts from session peak {self._peak_iq:.0f}",
                    metric="iq_score", current_value=iq,
                    threshold=self._peak_iq - IQ_DROP_HIGH, delta=round(delta, 1), ts=ts,
                ))
            elif drop >= IQ_DROP_MEDIUM:
                events.append(_make_event(
                    severity=SEV_MEDIUM, category="IQ_REGRESSION",
                    description=f"IQ dropped {drop:.0f}pts from session peak {self._peak_iq:.0f}",
                    metric="iq_score", current_value=iq,
                    threshold=self._peak_iq - IQ_DROP_MEDIUM, delta=round(delta, 1), ts=ts,
                ))

        return events

    def _check_allow_rate(self, snap: Dict, ts: int) -> List[AnomalyEvent]:
        ar = snap.get("rl_allow_rate")
        if ar is None:
            return []

        prev_ar = (self._prev_snapshot or {}).get("rl_allow_rate", ar)
        delta = round(ar - prev_ar, 3) if prev_ar is not None else None

        if ar < ALLOW_CRITICAL_FLOOR:
            sev, thresh, desc = SEV_CRITICAL, ALLOW_CRITICAL_FLOOR, f"Allow rate critically low: {ar:.0%}"
        elif ar < ALLOW_HIGH_FLOOR:
            sev, thresh, desc = SEV_HIGH, ALLOW_HIGH_FLOOR, f"Allow rate low: {ar:.0%}"
        elif ar < ALLOW_MEDIUM_FLOOR:
            sev, thresh, desc = SEV_MEDIUM, ALLOW_MEDIUM_FLOOR, f"Allow rate below target: {ar:.0%}"
        else:
            return []

        return [_make_event(
            severity=sev, category="ALLOW_COLLAPSE",
            description=desc, metric="rl_allow_rate",
            current_value=ar, threshold=thresh, delta=delta, ts=ts,
        )]

    def _check_win_rates(self, snap: Dict, ts: int) -> List[AnomalyEvent]:
        events = []
        regime_fields = [
            ("le_trending_wr",  "TRENDING"),
            ("le_mean_rev_wr",  "MEAN_REVERTING"),
            ("le_vol_exp_wr",   "VOLATILITY_EXPANSION"),
        ]
        for field, regime in regime_fields:
            wr = snap.get(field)
            if wr is None:
                continue
            if wr < WR_HIGH_FLOOR:
                events.append(_make_event(
                    severity=SEV_HIGH, category="WIN_RATE_EROSION",
                    description=f"{regime} win rate dangerously low: {wr:.0%}",
                    metric=field, current_value=wr,
                    threshold=WR_HIGH_FLOOR, delta=None, ts=ts,
                ))
            elif wr < WR_MEDIUM_FLOOR:
                events.append(_make_event(
                    severity=SEV_MEDIUM, category="WIN_RATE_EROSION",
                    description=f"{regime} win rate below target: {wr:.0%}",
                    metric=field, current_value=wr,
                    threshold=WR_MEDIUM_FLOOR, delta=None, ts=ts,
                ))
        return events

    def _check_confidence_flip(self, snap: Dict, ts: int) -> List[AnomalyEvent]:
        curr_dir = snap.get("rl_confidence_dir")
        if curr_dir is None or self._prev_snapshot is None:
            return []

        prev_dir = self._prev_snapshot.get("rl_confidence_dir")
        if prev_dir == "GROWING" and curr_dir == "DECLINING":
            return [_make_event(
                severity=SEV_HIGH, category="CONFIDENCE_FLIP",
                description=f"RL confidence direction flipped: GROWING → DECLINING",
                metric="rl_confidence_dir",
                current_value=curr_dir, threshold="GROWING",
                delta=f"{prev_dir}→{curr_dir}", ts=ts,
            )]
        if prev_dir in ("GROWING", "NEUTRAL") and curr_dir == "DECLINING":
            return [_make_event(
                severity=SEV_MEDIUM, category="CONFIDENCE_FLIP",
                description=f"RL confidence direction: {prev_dir} → DECLINING",
                metric="rl_confidence_dir",
                current_value=curr_dir, threshold="NEUTRAL",
                delta=f"{prev_dir}→{curr_dir}", ts=ts,
            )]
        return []

    def _check_regime_shift(self, snap: Dict, ts: int) -> List[AnomalyEvent]:
        curr_regime = snap.get("regime")
        if curr_regime is None or self._prev_snapshot is None:
            return []
        prev_regime = self._prev_snapshot.get("regime")
        if prev_regime and prev_regime != curr_regime:
            return [_make_event(
                severity=SEV_LOW, category="REGIME_SHIFT",
                description=f"Market regime changed: {prev_regime} → {curr_regime}",
                metric="regime",
                current_value=curr_regime, threshold=prev_regime,
                delta=f"{prev_regime}→{curr_regime}", ts=ts,
            )]
        return []

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _store_events(self, events: List[AnomalyEvent]) -> None:
        for ev in events:
            self._history.append(ev)
            sev = ev.severity
            self._stats.total_anomalies += 1
            if sev == SEV_CRITICAL:
                self._stats.critical_count += 1
            elif sev == SEV_HIGH:
                self._stats.high_count += 1
            elif sev == SEV_MEDIUM:
                self._stats.medium_count += 1
            else:
                self._stats.low_count += 1

        # Trim history to cap
        if len(self._history) > MAX_HISTORY:
            self._history = self._history[-MAX_HISTORY:]


# ── Event factory ─────────────────────────────────────────────────────────────

def _make_event(
    severity: str,
    category: str,
    description: str,
    metric: str,
    current_value: Any,
    threshold: Any,
    delta: Any,
    ts: int,
) -> AnomalyEvent:
    """Build an AnomalyEvent with a deterministic short ID."""
    raw_id = f"{category}:{metric}:{threshold}:{ts // 60_000}"   # 1-minute granularity
    anomaly_id = hashlib.sha256(raw_id.encode()).hexdigest()[:8]
    return AnomalyEvent(
        anomaly_id=anomaly_id,
        severity=severity,
        category=category,
        description=description,
        metric=metric,
        current_value=current_value,
        threshold=threshold,
        delta=delta,
        ts=ts,
    )


# ── Module-level singleton ────────────────────────────────────────────────────
anomaly_detector = AnomalyDetector()
