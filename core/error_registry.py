"""
EOW Quant Engine — Error Registry  (FTD-REF-025)
Centralized structured error tracking — every engine error becomes readable.

Error format:
  {
    "code":     "WS_001",        # unique code for this error type
    "type":     "WebSocket",     # category
    "message":  "No tick >30s",  # short description
    "reason":   "Market inactivity or connection drop",
    "severity": "WARNING",       # DEBUG / INFO / WARNING / ERROR / CRITICAL
    "auto_fix": "Ping sent",     # action the system took automatically
    "ts":       1718000000.0,    # epoch seconds
    "symbol":   "",              # optional: affected symbol
  }

Built-in error catalogue (FTD-REF-025 spec):
  WS   : WS_001 – WS_003
  DATA : DATA_001 – DATA_002
  STRAT: STRAT_001 – STRAT_002
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional

from loguru import logger


# ── Severity constants ────────────────────────────────────────────────────────
SEV_DEBUG    = "DEBUG"
SEV_INFO     = "INFO"
SEV_WARNING  = "WARNING"
SEV_ERROR    = "ERROR"
SEV_CRITICAL = "CRITICAL"

MAX_HISTORY  = 200   # maximum errors kept in memory

# ── Per-code log throttle (seconds between loguru emits) ─────────────────────
# Prevents high-frequency events (e.g. DATA_001 on every candle tick) from
# flooding the loguru output.  Records and counts are always incremented —
# only the loguru emit is suppressed while within the throttle window.
ERROR_THROTTLE: Dict[str, float] = {
    "DATA_001": 10.0,   # max 1 loguru line per 10 s  (FTD-REF-026)
}


# ── Built-in error catalogue ──────────────────────────────────────────────────
ERROR_CATALOGUE: Dict[str, dict] = {
    # WebSocket errors
    "WS_001": {
        "type":     "WebSocket",
        "message":  "No tick received for >30 seconds",
        "reason":   "Market inactivity or slow connection — stream may be delayed",
        "severity": SEV_WARNING,
        "auto_fix": "Ping sent to check connection",
    },
    "WS_002": {
        "type":     "WebSocket",
        "message":  "No tick received for >60 seconds",
        "reason":   "Connection likely dropped or stream stalled",
        "severity": SEV_ERROR,
        "auto_fix": "Force reconnect triggered",
    },
    "WS_003": {
        "type":     "WebSocket",
        "message":  "TCP reset received (WinError 10054 or connection reset by peer)",
        "reason":   "Binance server closed the TCP connection (routine reset)",
        "severity": SEV_WARNING,
        "auto_fix": "Connection reset ignored — reconnecting automatically",
    },
    # Data errors
    "DATA_001": {
        "type":     "Data",
        "message":  "Missing or insufficient candle data",
        "reason":   "Price buffer has fewer bars than strategy requires",
        "severity": SEV_INFO,
        "auto_fix": "Waiting for more candles before generating signals",
    },
    "DATA_002": {
        "type":     "Data",
        "message":  "Indicator value invalid or unstable",
        "reason":   "ADX/ATR computed from insufficient or malformed data",
        "severity": SEV_WARNING,
        "auto_fix": "Trade skipped — signal generation blocked",
    },
    # Strategy errors
    "STRAT_001": {
        "type":     "Strategy",
        "message":  "Regime classified as UNKNOWN",
        "reason":   "ADX in ambiguous range (15–20); not enough directional signal",
        "severity": SEV_INFO,
        "auto_fix": "Falling back to last valid regime with 70% confidence penalty",
    },
    "STRAT_002": {
        "type":     "Strategy",
        "message":  "Edge < 0 — strategy has negative expectancy for this regime",
        "reason":   "Recent trade history shows consistent losses in this regime",
        "severity": SEV_WARNING,
        "auto_fix": "Trade rejected — kill switch active until edge recovers",
    },
}


@dataclass
class ErrorRecord:
    code:     str
    type:     str
    message:  str
    reason:   str
    severity: str
    auto_fix: str
    ts:       float
    symbol:   str  = ""
    extra:    str  = ""   # any additional context


class ErrorRegistry:
    """
    Stateful centralized error store.
    Thread-safe for a single asyncio event loop.

    Usage:
      error_registry.log("WS_001")
      error_registry.log("WS_003", symbol="BTCUSDT", extra="errno=10054")
      recent = error_registry.recent(20)
    """

    def __init__(self, max_history: int = MAX_HISTORY):
        self._records:     Deque[ErrorRecord] = deque(maxlen=max_history)
        self._counts:      Dict[str, int]     = {}
        self._throttle_ts: Dict[str, float]   = {}  # FTD-REF-026: last loguru emit ts

    # ── Public ────────────────────────────────────────────────────────────────

    def log(
        self,
        code:    str,
        symbol:  str = "",
        extra:   str = "",
        *,
        # Allow callers to override catalogue fields for one-off custom errors
        type:     Optional[str] = None,
        message:  Optional[str] = None,
        reason:   Optional[str] = None,
        severity: Optional[str] = None,
        auto_fix: Optional[str] = None,
    ) -> ErrorRecord:
        """
        Log a structured error by code.
        Looks up the catalogue for default fields; caller can override any field.
        """
        cat  = ERROR_CATALOGUE.get(code, {})
        rec  = ErrorRecord(
            code     = code,
            type     = type     or cat.get("type",     "Unknown"),
            message  = message  or cat.get("message",  code),
            reason   = reason   or cat.get("reason",   ""),
            severity = severity or cat.get("severity", SEV_WARNING),
            auto_fix = auto_fix or cat.get("auto_fix", ""),
            ts       = time.time(),
            symbol   = symbol,
            extra    = extra,
        )
        self._records.append(rec)
        self._counts[code] = self._counts.get(code, 0) + 1

        # FTD-REF-026: throttle — skip loguru emit if within throttle window.
        # Counts and records are always updated so summaries remain accurate.
        _throttle_sec = ERROR_THROTTLE.get(code)
        _emit_log = True
        if _throttle_sec is not None:
            _last_ts = self._throttle_ts.get(code, 0.0)
            if rec.ts - _last_ts < _throttle_sec:
                _emit_log = False
            else:
                self._throttle_ts[code] = rec.ts

        # Log to loguru at appropriate level
        _logline = (
            f"[ERR-REG] [{rec.code}] {rec.message}"
            + (f" | sym={symbol}" if symbol else "")
            + (f" | {extra}"      if extra  else "")
            + (f" → {rec.auto_fix}" if rec.auto_fix else "")
        )
        if _emit_log:
            if rec.severity == SEV_CRITICAL:
                logger.critical(_logline)
            elif rec.severity == SEV_ERROR:
                logger.error(_logline)
            elif rec.severity == SEV_WARNING:
                logger.warning(_logline)
            elif rec.severity == SEV_INFO:
                logger.info(_logline)
            else:
                logger.debug(_logline)

        return rec

    def recent(self, n: int = 50) -> list:
        """Return the n most recent error records as dicts."""
        records = list(self._records)[-n:]
        return [self._to_dict(r) for r in reversed(records)]

    def counts(self) -> Dict[str, int]:
        """Return {error_code: occurrence_count} for all seen codes."""
        return dict(self._counts)

    def summary(self) -> dict:
        return {
            "total_errors":  sum(self._counts.values()),
            "unique_codes":  len(self._counts),
            "counts":        self.counts(),
            "recent_5":      self.recent(5),
            "catalogue_size": len(ERROR_CATALOGUE),
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    @staticmethod
    def _to_dict(r: ErrorRecord) -> dict:
        return {
            "code":     r.code,
            "type":     r.type,
            "message":  r.message,
            "reason":   r.reason,
            "severity": r.severity,
            "auto_fix": r.auto_fix,
            "ts":       r.ts,
            "symbol":   r.symbol,
            "extra":    r.extra,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
error_registry = ErrorRegistry()
