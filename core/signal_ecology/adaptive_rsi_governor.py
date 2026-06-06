"""
FTD-057-PHOENIX Phase 1 — Adaptive RSI Governor

Replaces hardcoded RSI thresholds with regime-aware, survival-rate-calibrated
dynamic bands. Target: 10–25% signal survival rate (vs ~2.5% with hardcoded bands).

Governance rules:
  - Never hardens thresholds below minimum safety bounds
  - Every decision is logged with reason + band state
  - All telemetry is queryable via get_telemetry()
"""
from __future__ import annotations

import time
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

import json
from pathlib import Path

from loguru import logger

from config import cfg


# ── Persistence ────────────────────────────────────────────────────────────────
_BAND_PERSIST_PATH = Path("data/rsi_governor_bands.json")
_BAND_SAVE_INTERVAL = 60.0   # seconds between auto-saves

# ── Safety bounds — never cross these regardless of adaptive pressure ──────────
_MR_LONG_RSI_MIN   = 20.0   # MEAN_REVERTING long: RSI must be below this
_MR_SHORT_RSI_MAX  = 80.0   # MEAN_REVERTING short: RSI must be above this
_MR_PREV_MARGIN    = 3.0    # crash-guard: prev RSI must be within this margin of band
_TR_LONG_RSI_MAX   = 58.0   # TRENDING long pullback: RSI must be below this (relax limit)
_TR_SHORT_RSI_MIN  = 42.0   # TRENDING short bounce: RSI must be above this (relax limit)
# Tightening floors for TRENDING: prevent bands from squeezing to RSI≈50 territory.
# Below 44/above 56 would filter >95% of trend signals — a pathological outcome.
_TR_LONG_RSI_TIGHT_MIN  = 44.0   # TRENDING long_rsi never tightens below this
_TR_SHORT_RSI_TIGHT_MAX = 56.0   # TRENDING short_rsi never tightens above this

# Starting bands (same as hardcoded legacy)
_MR_LONG_RSI_START  = 30.0
_MR_SHORT_RSI_START = 70.0
_MR_PREV_LONG_START = 35.0
_MR_PREV_SHORT_START = 65.0
_TR_LONG_RSI_START  = 48.0
_TR_SHORT_RSI_START = 52.0

# Adaptation limits — max relaxation from start
_MR_MAX_RELAX = 8.0   # RSI band can widen by at most 8 points
_TR_MAX_RELAX = 10.0  # RSI band can widen by at most 10 points

# Multi-candle RSI persistence confirmation (MEAN_REVERTING only)
# Requires RSI to have been persistently in the extreme zone across recent candles,
# blocking first-touch crashes/spikes that clear on the very next candle.
# Buffer extends the zone slightly inward (e.g. long_band=30 → zone is below 35),
# allowing for minor RSI oscillation while still confirming sustained presence.
_MR_PERSIST_BUFFER    = 5.0   # zone = long_band + buffer (long) / short_band - buffer (short)
_MR_PERSIST_MIN_COUNT = 2     # at least this many of the history window must be in zone
_MR_PERSIST_WINDOW    = 3     # number of candles to check (including current)

# Target survival rate window
_TARGET_SURVIVAL_LO = 0.10   # 10% floor
_TARGET_SURVIVAL_HI = 0.25   # 25% ceiling

# Rolling window for survival rate calculation
_SURVIVAL_WINDOW = 100        # evaluations
_ADAPT_STEP      = 0.5        # adjustment step per adaptation pass
_ADAPT_INTERVAL  = 30.0       # seconds between adaptation passes


@dataclass
class RSIDecision:
    side: Optional[str]          # "LONG" | "SHORT" | None
    blocked: bool
    block_reason: str            # "" if not blocked
    rsi_val: float
    rsi_prev: float
    regime: str
    band_lo: float               # effective lower band used
    band_hi: float               # effective upper band used
    prev_lo: float
    prev_hi: float
    survival_rate: float         # current window survival rate
    ts: int = field(default_factory=lambda: int(time.time() * 1000))


class AdaptiveRSIGovernor:
    """
    Regime-aware RSI filter with adaptive band widening to prevent signal starvation.
    Thread-safe — uses a single RLock.
    """

    def __init__(self):
        self._lock = threading.RLock()

        # Per-regime band state
        self._bands: Dict[str, Dict[str, float]] = {
            "MEAN_REVERTING": {
                "long_rsi":   _MR_LONG_RSI_START,
                "short_rsi":  _MR_SHORT_RSI_START,
                "prev_long":  _MR_PREV_LONG_START,
                "prev_short": _MR_PREV_SHORT_START,
            },
            "TRENDING": {
                "long_rsi":  _TR_LONG_RSI_START,
                "short_rsi": _TR_SHORT_RSI_START,
            },
            "UNKNOWN": {
                "long_rsi":  _TR_LONG_RSI_START,
                "short_rsi": _TR_SHORT_RSI_START,
            },
        }

        # Rolling survival tracking per regime
        self._windows: Dict[str, deque] = {
            "MEAN_REVERTING": deque(maxlen=_SURVIVAL_WINDOW),
            "TRENDING":       deque(maxlen=_SURVIVAL_WINDOW),
            "UNKNOWN":        deque(maxlen=_SURVIVAL_WINDOW),
        }

        self._last_adapt_ts: float = 0.0
        self._last_save_ts:  float = 0.0
        self._total_evaluated: int = 0
        self._total_passed:    int = 0

        # History for forensic telemetry
        self._decision_log: deque = deque(maxlen=500)
        self._adapt_log:    deque = deque(maxlen=100)

        # Restore learned bands from previous session so cold-start is instant
        self._load_bands()

    # ── Primary API ────────────────────────────────────────────────────────────

    def get_signal(
        self,
        regime: str,
        rsi_val: float,
        rsi_prev: float,
        above_sma: bool,
        symbol: str = "",
        rsi_history: Optional[List[float]] = None,
    ) -> RSIDecision:
        """
        Evaluate RSI against dynamic bands and return a decision.
        Also triggers periodic band adaptation.

        rsi_history: ordered list of recent RSI values (oldest→newest, current last).
        When provided (len≥2), enables multi-candle persistence check for
        MEAN_REVERTING regime — confirms RSI has been persistently in the extreme
        zone rather than arriving via a single-candle crash/spike.
        Falls back gracefully to crash-guard-only when None or too short.
        """
        with self._lock:
            self._maybe_adapt()

            regime_key = regime if regime in self._bands else "UNKNOWN"
            bands = self._bands[regime_key]
            sr = self._survival_rate(regime_key)

            side, blocked, reason = self._evaluate(
                regime_key, rsi_val, rsi_prev, above_sma, bands, rsi_history
            )

            passed = not blocked
            self._windows[regime_key].append(1 if passed else 0)
            self._total_evaluated += 1
            if passed:
                self._total_passed += 1

            dec = RSIDecision(
                side=side,
                blocked=blocked,
                block_reason=reason,
                rsi_val=rsi_val,
                rsi_prev=rsi_prev,
                regime=regime_key,
                band_lo=bands.get("long_rsi", 0),
                band_hi=bands.get("short_rsi", 100),
                prev_lo=bands.get("prev_long", 0),
                prev_hi=bands.get("prev_short", 100),
                survival_rate=sr,
            )
            self._decision_log.append({
                "ts": dec.ts, "symbol": symbol, "regime": regime_key,
                "side": side, "blocked": blocked, "reason": reason,
                "rsi": round(rsi_val, 2), "rsi_prev": round(rsi_prev, 2),
                "band_lo": bands.get("long_rsi"), "band_hi": bands.get("short_rsi"),
                "survival_rate": round(sr, 4),
            })
            return dec

    # ── Internal evaluation logic ──────────────────────────────────────────────

    def _evaluate(
        self,
        regime: str,
        rsi_val: float,
        rsi_prev: float,
        above_sma: bool,
        bands: Dict[str, float],
        rsi_history: Optional[List[float]] = None,
    ) -> Tuple[Optional[str], bool, str]:

        if regime == "MEAN_REVERTING":
            long_band  = bands["long_rsi"]
            short_band = bands["short_rsi"]
            prev_long  = bands["prev_long"]
            prev_short = bands["prev_short"]

            if above_sma and rsi_val > short_band:
                if rsi_prev > prev_short:
                    # Persistence check: require RSI to have been sustainably overbought,
                    # not just landed in the zone this candle after arriving from mid-range.
                    persist_block = self._check_persistence_short(
                        rsi_history, short_band
                    )
                    if persist_block:
                        return None, True, persist_block
                    return "SHORT", False, ""
                else:
                    return None, True, (
                        f"RSI_CRASH_GUARD SHORT: rsi={rsi_val:.1f}>{short_band:.1f} "
                        f"but prev={rsi_prev:.1f}≤{prev_short:.1f} (first-touch spike)"
                    )
            elif not above_sma and rsi_val < long_band:
                if rsi_prev < prev_long:
                    # Persistence check: require RSI to have been sustainably oversold,
                    # not just arrived via a single-candle crash.
                    persist_block = self._check_persistence_long(
                        rsi_history, long_band
                    )
                    if persist_block:
                        return None, True, persist_block
                    return "LONG", False, ""
                else:
                    return None, True, (
                        f"RSI_CRASH_GUARD LONG: rsi={rsi_val:.1f}<{long_band:.1f} "
                        f"but prev={rsi_prev:.1f}≥{prev_long:.1f} (first-touch crash)"
                    )
            else:
                return None, True, (
                    f"RSI_LEVEL: rsi={rsi_val:.1f} above_sma={above_sma} "
                    f"bands=[{long_band:.1f},{short_band:.1f}]"
                )

        else:  # TRENDING / UNKNOWN
            long_band  = bands["long_rsi"]
            short_band = bands["short_rsi"]

            if above_sma and rsi_val <= long_band:
                return "LONG", False, ""
            elif not above_sma and rsi_val >= short_band:
                return "SHORT", False, ""
            else:
                return None, True, (
                    f"RSI_LEVEL: rsi={rsi_val:.1f} above_sma={above_sma} "
                    f"bands=[{long_band:.1f},{short_band:.1f}]"
                )

    def _check_persistence_long(
        self, rsi_history: Optional[List[float]], long_band: float
    ) -> str:
        """
        Returns a block reason string if the LONG entry lacks multi-candle persistence.
        Returns "" (empty) if check passes or insufficient data (graceful degradation).
        The zone is long_band + _MR_PERSIST_BUFFER — slightly relaxed to allow for
        minor oscillation while the symbol remains in oversold territory.
        """
        if not rsi_history or len(rsi_history) < 2:
            return ""  # insufficient history — defer to crash guard only
        window = rsi_history[-_MR_PERSIST_WINDOW:]
        zone_ceiling = long_band + _MR_PERSIST_BUFFER
        in_zone = sum(1 for r in window if r < zone_ceiling)
        if in_zone >= _MR_PERSIST_MIN_COUNT:
            return ""
        return (
            f"RSI_PERSIST_LONG: only {in_zone}/{len(window)} candles below "
            f"{zone_ceiling:.1f} (need {_MR_PERSIST_MIN_COUNT}) — "
            f"history={[round(r,1) for r in window]}"
        )

    def _check_persistence_short(
        self, rsi_history: Optional[List[float]], short_band: float
    ) -> str:
        """
        Returns a block reason string if the SHORT entry lacks multi-candle persistence.
        Returns "" (empty) if check passes or insufficient data (graceful degradation).
        """
        if not rsi_history or len(rsi_history) < 2:
            return ""  # insufficient history — defer to crash guard only
        window = rsi_history[-_MR_PERSIST_WINDOW:]
        zone_floor = short_band - _MR_PERSIST_BUFFER
        in_zone = sum(1 for r in window if r > zone_floor)
        if in_zone >= _MR_PERSIST_MIN_COUNT:
            return ""
        return (
            f"RSI_PERSIST_SHORT: only {in_zone}/{len(window)} candles above "
            f"{zone_floor:.1f} (need {_MR_PERSIST_MIN_COUNT}) — "
            f"history={[round(r,1) for r in window]}"
        )

    # ── Band adaptation ────────────────────────────────────────────────────────

    def _maybe_adapt(self) -> None:
        now = time.time()
        if now - self._last_adapt_ts < _ADAPT_INTERVAL:
            return
        self._last_adapt_ts = now
        self._adapt_all_bands()

    def _adapt_all_bands(self) -> None:
        for regime_key in ("MEAN_REVERTING", "TRENDING", "UNKNOWN"):
            window = self._windows[regime_key]
            if len(window) < 20:
                continue

            sr = self._survival_rate(regime_key)
            old_bands = dict(self._bands[regime_key])

            if sr < _TARGET_SURVIVAL_LO:
                # Too restrictive — relax bands
                self._relax_bands(regime_key)
            elif sr > _TARGET_SURVIVAL_HI:
                # Too permissive — tighten back toward starting point
                self._tighten_bands(regime_key)
            else:
                continue

            new_bands = dict(self._bands[regime_key])
            entry = {
                "ts": int(time.time() * 1000),
                "regime": regime_key,
                "survival_rate": round(sr, 4),
                "action": "RELAX" if sr < _TARGET_SURVIVAL_LO else "TIGHTEN",
                "old_bands": old_bands,
                "new_bands": new_bands,
            }
            self._adapt_log.append(entry)
            logger.info(
                f"[FTD-057][RSI_GOV] {regime_key} adapt: sr={sr:.3f} "
                f"action={entry['action']} bands={new_bands}"
            )

        # Auto-save after any adaptation pass
        if time.time() - self._last_save_ts >= _BAND_SAVE_INTERVAL:
            self._save_bands()

    def _relax_bands(self, regime: str) -> None:
        b = self._bands[regime]
        if regime == "MEAN_REVERTING":
            # Widen toward center: raise long_band, lower short_band
            b["long_rsi"]   = min(b["long_rsi"]  + _ADAPT_STEP,
                                  _MR_LONG_RSI_START + _MR_MAX_RELAX)
            b["short_rsi"]  = max(b["short_rsi"] - _ADAPT_STEP,
                                  _MR_SHORT_RSI_START - _MR_MAX_RELAX)
            # Prev bands follow with 2-point gap
            b["prev_long"]  = b["long_rsi"]  + 2.0
            b["prev_short"] = b["short_rsi"] - 2.0
        else:
            # Widen: raise long_rsi, lower short_rsi (toward 50)
            b["long_rsi"]  = min(b["long_rsi"]  + _ADAPT_STEP, _TR_LONG_RSI_MAX)
            b["short_rsi"] = max(b["short_rsi"] - _ADAPT_STEP, _TR_SHORT_RSI_MIN)

    def _tighten_bands(self, regime: str) -> None:
        b = self._bands[regime]
        if regime == "MEAN_REVERTING":
            b["long_rsi"]   = max(b["long_rsi"]  - _ADAPT_STEP, _MR_LONG_RSI_MIN)
            b["short_rsi"]  = min(b["short_rsi"] + _ADAPT_STEP, _MR_SHORT_RSI_MAX)
            b["prev_long"]  = b["long_rsi"]  + 2.0
            b["prev_short"] = b["short_rsi"] - 2.0
        else:
            b["long_rsi"]  = max(b["long_rsi"]  - _ADAPT_STEP, _TR_LONG_RSI_TIGHT_MIN)
            b["short_rsi"] = min(b["short_rsi"] + _ADAPT_STEP, _TR_SHORT_RSI_TIGHT_MAX)

    # ── Survival rate ──────────────────────────────────────────────────────────

    def _survival_rate(self, regime: str) -> float:
        w = self._windows[regime]
        if not w:
            return 0.0
        return sum(w) / len(w)

    def global_survival_rate(self) -> float:
        if self._total_evaluated == 0:
            return 0.0
        return self._total_passed / self._total_evaluated

    # ── Telemetry / forensics ──────────────────────────────────────────────────

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            bands = {k: dict(v) for k, v in self._bands.items()}
            sr_by_regime = {
                k: round(self._survival_rate(k), 4)
                for k in self._windows
            }
            return {
                "module":              "AdaptiveRSIGovernor",
                "ftd":                 "057",
                "total_evaluated":     self._total_evaluated,
                "total_passed":        self._total_passed,
                "global_survival_rate": round(self.global_survival_rate(), 4),
                "survival_by_regime":  sr_by_regime,
                "bands":               bands,
                "recent_decisions":    list(self._decision_log)[-20:],
                "adapt_log":           list(self._adapt_log)[-20:],
                "ts":                  int(time.time() * 1000),
            }

    def band_state(self) -> Dict[str, Any]:
        with self._lock:
            return {k: dict(v) for k, v in self._bands.items()}

    def recent_decisions(self, n: int = 50) -> list:
        with self._lock:
            return list(self._decision_log)[-n:]

    # ── Band persistence ───────────────────────────────────────────────────────

    def _load_bands(self) -> None:
        if not _BAND_PERSIST_PATH.exists():
            return
        try:
            raw = json.loads(_BAND_PERSIST_PATH.read_text())
            for regime, vals in raw.items():
                if regime in self._bands and isinstance(vals, dict):
                    # Only restore keys that already exist for this regime
                    for k in self._bands[regime]:
                        if k in vals:
                            self._bands[regime][k] = float(vals[k])
            logger.info(f"[FTD-057][RSI_GOV] Restored bands from {_BAND_PERSIST_PATH}")
        except Exception as exc:
            logger.warning(f"[FTD-057][RSI_GOV] Band load failed (using defaults): {exc}")

    def _save_bands(self) -> None:
        try:
            _BAND_PERSIST_PATH.parent.mkdir(parents=True, exist_ok=True)
            _BAND_PERSIST_PATH.write_text(
                json.dumps({k: dict(v) for k, v in self._bands.items()}, indent=2)
            )
            self._last_save_ts = time.time()
        except Exception as exc:
            logger.warning(f"[FTD-057][RSI_GOV] Band save failed: {exc}")

    def save_bands(self) -> None:
        """Force save (call on engine shutdown)."""
        with self._lock:
            self._save_bands()

    def reset_bands(self) -> None:
        """Reset all bands to starting values (for testing/override)."""
        with self._lock:
            self._bands["MEAN_REVERTING"].update({
                "long_rsi": _MR_LONG_RSI_START, "short_rsi": _MR_SHORT_RSI_START,
                "prev_long": _MR_PREV_LONG_START, "prev_short": _MR_PREV_SHORT_START,
            })
            self._bands["TRENDING"].update({
                "long_rsi": _TR_LONG_RSI_START, "short_rsi": _TR_SHORT_RSI_START,
            })
            self._bands["UNKNOWN"].update({
                "long_rsi": _TR_LONG_RSI_START, "short_rsi": _TR_SHORT_RSI_START,
            })


# ── Singleton ──────────────────────────────────────────────────────────────────
adaptive_rsi_governor = AdaptiveRSIGovernor()
