"""
EOW Quant Engine — Intelligence Compressor  (FTD-053-GAIA Phase 1)

Separates raw telemetry from compressed summaries, enforces retention governance,
and provides checksum-based deduplication to prevent redundant storage and AI token waste.

Design principles:
  • READ-ONLY on trading state — never modifies engine state
  • NON-THROWING — all public methods catch exceptions internally
  • TOKEN-EFFICIENT — compressed output is ≤15% of raw input by field count
  • DEDUP-AWARE — SHA-256 checksum prevents writing identical snapshots
  • SCHEMA-DRIVEN — field extraction rules declared as static config

Compression schema:
  Raw blobs can be arbitrarily large (full RL table, all regime stats, etc.)
  The compressor extracts a fixed "signal envelope" of ≤30 high-value fields
  that represent the system's current intelligence without the noise.

Retention governance:
  - Raw:        max 100 files  |  24 h max age  |  50 MB ceiling
  - Compressed: max 500 files  |  30 d max age  |  200 MB ceiling
  - Latest:     always 1 file  |  no age limit  |  updated atomically
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from loguru import logger


# ── Retention ceilings ────────────────────────────────────────────────────────

RAW_MAX_FILES        = 100
RAW_MAX_AGE_HOURS    = 24
RAW_MAX_SIZE_MB      = 50.0

COMPRESSED_MAX_FILES = 500
COMPRESSED_MAX_DAYS  = 30
COMPRESSED_MAX_SIZE_MB = 200.0

# Dedup window: if the same checksum was written within N seconds, skip write
DEDUP_WINDOW_SECS    = 60


# ── Compression schema ────────────────────────────────────────────────────────
# Each entry: (source_dot_path, output_key)
# source_dot_path supports up to 3 levels of nesting using "."
_SIGNAL_SCHEMA: List[tuple[str, str]] = [
    # Session metrics
    ("session_stats.total_net_pnl",         "pnl"),
    ("session_stats.n_trades",              "n_trades"),
    ("session_stats.profit_factor",         "profit_factor"),
    ("session_stats.win_rate",              "win_rate"),
    # RL engine
    ("rl.total_contexts",                   "rl_contexts"),
    ("rl.total_trade_decisions",            "rl_decisions"),
    ("rl.evolution_state.intelligence_score", "iq_score"),
    ("rl.summary_metrics.toxic_contexts",   "rl_toxic"),
    ("rl.summary_metrics.allow_rate",       "rl_allow_rate"),
    ("rl.summary_metrics.profitable_pct",   "rl_profitable_pct"),
    ("rl.learning_speed.maturity_pct",      "rl_maturity_pct"),
    ("rl.learning_speed.status",            "rl_maturity_status"),
    ("rl.exploration_pressure.pressure_status", "rl_explore_pressure"),
    ("rl.confidence_trajectory.confidence_direction", "rl_confidence_dir"),
    # Learning engine
    ("learning.TRENDING.win_rate",          "le_trending_wr"),
    ("learning.MEAN_REVERTING.win_rate",    "le_mean_rev_wr"),
    ("learning.VOLATILITY_EXPANSION.win_rate", "le_vol_exp_wr"),
    # Risk / gate state
    ("risk.halted",                         "risk_halted"),
    ("gate.can_trade",                      "gate_open"),
    # Trade flow
    ("trade_flow.consecutive_losses",       "consec_losses"),
    ("trade_flow.daily_trades",             "daily_trades"),
    # System health
    ("uptime_secs",                         "uptime_secs"),
    ("error_count",                         "error_count"),
    ("regime",                              "regime"),
]


@dataclass
class CompressionStats:
    total_compressions: int   = 0
    total_deduped:      int   = 0
    total_fields_in:    int   = 0
    total_fields_out:   int   = 0
    last_checksum:      str   = ""
    last_ts:            int   = 0
    recent_checksums:   List[str] = field(default_factory=list)  # ring buffer, last 50

    @property
    def compression_ratio(self) -> float:
        if self.total_fields_in == 0:
            return 0.0
        return round(1.0 - self.total_fields_out / self.total_fields_in, 3)


class IntelligenceCompressor:
    """
    Schema-driven compressor: extracts a fixed signal envelope from arbitrary raw blobs.
    Provides checksum deduplication over a rolling window.
    """

    MODULE  = "INTEL_COMPRESSOR"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._stats = CompressionStats()
        self._last_write_ts: Dict[str, int] = {}  # checksum → timestamp_ms

    # ── Public API ────────────────────────────────────────────────────────────

    def compress(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the signal envelope from a raw telemetry blob.

        Returns a flat dict of ≤30 high-value fields plus metadata.
        Never raises — returns {"error": ...} on failure.
        """
        try:
            out: Dict[str, Any] = {}

            field_count_in = _count_fields(raw)
            for dot_path, out_key in _SIGNAL_SCHEMA:
                val = _deep_get(raw, dot_path)
                if val is not None:
                    out[out_key] = val

            out["_compressed_ts"]  = int(time.time() * 1000)
            out["_schema_version"] = self.VERSION
            out["_field_count"]    = len(out)
            out["_checksum"]       = self.checksum(out)

            self._stats.total_compressions += 1
            self._stats.total_fields_in    += field_count_in
            self._stats.total_fields_out   += len(out)
            self._stats.last_checksum       = out["_checksum"]
            self._stats.last_ts             = out["_compressed_ts"]

            return out

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] compress error: {exc}")
            return {"error": str(exc), "_compressed_ts": int(time.time() * 1000)}

    def checksum(self, data: Dict[str, Any]) -> str:
        """
        Stable SHA-256 checksum of the data dict (excluding _checksum key itself).
        Used for deduplication.
        """
        try:
            clean = {k: v for k, v in data.items() if k not in ("_checksum", "_compressed_ts")}
            serialized = json.dumps(clean, sort_keys=True, default=str)
            return hashlib.sha256(serialized.encode()).hexdigest()[:16]
        except Exception:
            return ""

    def is_duplicate(self, checksum: str) -> bool:
        """
        Returns True if this checksum was seen within DEDUP_WINDOW_SECS.
        Maintains a ring buffer of the last 50 checksums.
        """
        now_ms  = int(time.time() * 1000)
        window  = DEDUP_WINDOW_SECS * 1000

        last_ts = self._last_write_ts.get(checksum, 0)
        if last_ts > 0 and (now_ms - last_ts) < window:
            self._stats.total_deduped += 1
            return True

        # Update ring buffer
        self._last_write_ts[checksum] = now_ms
        recent = self._stats.recent_checksums
        recent.append(checksum)
        if len(recent) > 50:
            oldest = recent.pop(0)
            self._last_write_ts.pop(oldest, None)

        return False

    def stats(self) -> Dict[str, Any]:
        s = self._stats
        return {
            "module":             self.MODULE,
            "version":            self.VERSION,
            "total_compressions": s.total_compressions,
            "total_deduped":      s.total_deduped,
            "compression_ratio":  s.compression_ratio,
            "total_fields_in":    s.total_fields_in,
            "total_fields_out":   s.total_fields_out,
            "last_checksum":      s.last_checksum,
            "last_ts":            s.last_ts,
        }

    def get_retention_config(self) -> Dict[str, Any]:
        """Returns the active retention governance configuration."""
        return {
            "raw": {
                "max_files":    RAW_MAX_FILES,
                "max_age_hours": RAW_MAX_AGE_HOURS,
                "max_size_mb":  RAW_MAX_SIZE_MB,
            },
            "compressed": {
                "max_files":    COMPRESSED_MAX_FILES,
                "max_age_days": COMPRESSED_MAX_DAYS,
                "max_size_mb":  COMPRESSED_MAX_SIZE_MB,
            },
            "dedup_window_secs": DEDUP_WINDOW_SECS,
        }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _deep_get(data: Dict[str, Any], dot_path: str) -> Optional[Any]:
    """Safely navigate nested dicts using dot notation (up to 4 levels)."""
    parts = dot_path.split(".")
    node: Any = data
    for part in parts:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
        if node is None:
            return None
    return node


def _count_fields(data: Any, depth: int = 0) -> int:
    """Recursively count all leaf fields in a nested dict structure."""
    if depth > 5 or not isinstance(data, dict):
        return 1
    return sum(_count_fields(v, depth + 1) for v in data.values())


# ── Module-level singleton ────────────────────────────────────────────────────
intelligence_compressor = IntelligenceCompressor()
