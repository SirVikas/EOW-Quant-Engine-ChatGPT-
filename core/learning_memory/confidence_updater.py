"""
FTD-030B — confidence_updater.py
Computes and updates pattern confidence using the hybrid formula.

Formula:
    confidence = success_rate × recency × regime_bonus

    success_rate = success / samples            (0.0 – 1.0 scaled to 0–100)
    recency      = 0.95^age_cycles              (half-life ≈ 14 cycles)
    regime_bonus = 1.1 if pattern seen in ≥2 distinct regimes, else 1.0

Output is clamped to [0.0, 100.0].
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.learning_memory.pattern_engine import Pattern

RECENCY_DECAY     = 0.95    # per-cycle decay factor
REGIME_BONUS      = 1.10    # multi-regime consistency bonus
MULTI_REGIME_MIN  = 2       # contexts must span at least 2 distinct regimes


def compute_confidence(pattern: "Pattern") -> float:
    """
    Compute confidence for a pattern using the locked hybrid formula.
    Returns a float in [0.0, 100.0].
    """
    if pattern.samples == 0:
        return 0.0

    success_rate = pattern.success / pattern.samples          # 0.0–1.0
    recency      = RECENCY_DECAY ** pattern.age_cycles        # decay over time
    regime_bonus = _regime_consistency_bonus(pattern.contexts)

    raw = success_rate * recency * regime_bonus * 100.0
    return max(0.0, min(100.0, round(raw, 2)))


def apply_rollback_penalty(current_confidence: float) -> float:
    """Reduce confidence by 30% on a rollback event (×0.70)."""
    return max(0.0, round(current_confidence * 0.70, 2))


def apply_time_decay(current_confidence: float, age_delta: int = 1) -> float:
    """Apply N cycles of time decay to an existing confidence value."""
    return max(0.0, round(current_confidence * (RECENCY_DECAY ** age_delta), 2))


# ── Internal helpers ──────────────────────────────────────────────────────────

def _regime_consistency_bonus(contexts: set) -> float:
    """Count distinct regime labels in the context signatures (format: 'REGIME:VOL')."""
    regimes = {ctx.split(":")[0] for ctx in contexts}
    return REGIME_BONUS if len(regimes) >= MULTI_REGIME_MIN else 1.0
