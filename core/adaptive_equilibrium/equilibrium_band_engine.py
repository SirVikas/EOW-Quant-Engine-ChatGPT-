"""
F.5 Equilibrium Band Engine.

Detects whether the system's rolling PnL is operating within statistical
equilibrium bands (3-sigma around a rolling mean).  Excursions outside the band
signal non-stationarity — the system has shifted into a new regime.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

_BAND_WINDOW = 20
_SIGMA       = 2.5


def compute_equilibrium_band(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < _BAND_WINDOW:
            return _no_data(ts_ms, n)

        pnls = [float(t.get("pnl", 0)) for t in trades]

        # Build equilibrium band from first half, test second half
        half = max(_BAND_WINDOW, n // 2)
        ref  = pnls[:half]
        test = pnls[half:]

        ref_mean = sum(ref) / len(ref)
        ref_std  = (sum((p - ref_mean) ** 2 for p in ref) / len(ref)) ** 0.5

        upper = ref_mean + _SIGMA * ref_std
        lower = ref_mean - _SIGMA * ref_std

        # Rolling cumulative PnL deviation from band
        test_cum = 0.0
        excursions = 0
        max_excursion = 0.0
        for p in test:
            test_cum += p
            if test_cum > upper or test_cum < lower:
                excursions += 1
                max_excursion = max(max_excursion, abs(test_cum - ref_mean))

        excursion_ratio = excursions / len(test) if test else 0.0
        band_width      = upper - lower
        deviation       = abs(test_cum - ref_mean)
        sigma_units     = deviation / ref_std if ref_std > 1e-9 else 0.0

        state = (
            "IN_BAND"         if sigma_units < 1.0 else
            "APPROACHING"     if sigma_units < 2.0 else
            "OUTSIDE_BAND"    if sigma_units < 4.0 else
            "FAR_OUTSIDE"
        )

        payload = f"EQ-F5|{ts_ms}|{round(sigma_units, 4)}|{excursions}"
        lineage_id = "EQ-F5-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":             "F.5_EQUILIBRIUM_BAND",
            "lineage_id":         lineage_id,
            "trade_count":        n,
            "ref_mean":           round(ref_mean, 4),
            "ref_std":            round(ref_std, 4),
            "band_upper":         round(upper, 4),
            "band_lower":         round(lower, 4),
            "band_width":         round(band_width, 4),
            "current_deviation":  round(deviation, 4),
            "sigma_units":        round(sigma_units, 4),
            "excursions":         excursions,
            "excursion_ratio":    round(excursion_ratio, 4),
            "max_excursion":      round(max_excursion, 4),
            "state":              state,
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "lineage_preserved":  True,
        }
    except Exception as exc:
        return {
            "engine": "F.5_EQUILIBRIUM_BAND", "state": "FAR_OUTSIDE",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "lineage_preserved": True,
        }


def _no_data(ts_ms: int, n: int) -> dict:
    return {
        "engine": "F.5_EQUILIBRIUM_BAND", "state": "IN_BAND",
        "trade_count": n, "insufficient_data": True,
        "diagnostic_only": True, "auto_authorized": False, "lineage_preserved": True,
    }
