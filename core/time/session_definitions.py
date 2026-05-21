"""
EOW Quant Engine — Canonical Session Definitions

Single source of truth for all UTC trading session bucket boundaries.

ALL subsystems that classify a trade, signal, or Q-value by session MUST
import make_context, SESSION_BUCKETS_UTC, and get_session_integrity_block()
from here.  No inline hour-bucket logic is permitted anywhere else.

Timezone authority: UTC  (datetime.utcnow().hour at the call site in main.py)
Exchange timestamp: NOT used for session classification
OS local time:      NOT used for session classification

Verification: tests/test_session_integrity.py asserts every boundary and
              confirms no rogue inline bucket definitions exist in core/.
"""
from __future__ import annotations

# ── Canonical session boundaries (UTC, half-open intervals [start, end)) ──────
#
# Each bucket covers UTC hours in [start, end).
# Hour 0 → ASIA  (start inclusive), hour 24 cannot occur in practice.

SESSION_BUCKETS_UTC: dict[str, tuple[int, int]] = {
    "ASIA":   (0,  6),
    "LONDON": (6,  13),
    "NY":     (13, 19),
    "LATE":   (19, 24),
}

# ── Human-readable display windows (UTC and IST = UTC+5:30) ──────────────────

SESSION_DISPLAY: dict[str, dict[str, str]] = {
    "ASIA":   {"utc": "00:00–05:59", "ist": "05:30–11:29"},
    "LONDON": {"utc": "06:00–12:59", "ist": "11:30–18:29"},
    "NY":     {"utc": "13:00–18:59", "ist": "18:30–00:29"},
    "LATE":   {"utc": "19:00–23:59", "ist": "00:30–05:29"},
}

# ── Governance metadata ───────────────────────────────────────────────────────

SESSION_TIMEZONE_AUTHORITY   = "UTC"
SESSION_UTC_SOURCE           = "datetime.utcnow().hour"
SESSION_OS_LOCAL_USED        = False
SESSION_EXCHANGE_TS_USED     = False
SESSION_DEFINITION_VERSION   = "v1"


# ── Context key factory ───────────────────────────────────────────────────────

def make_context(regime: str, utc_hour: int, strategy: str) -> str:
    """
    Create a hashable context key: REGIME|SESSION|STRATEGY.
    Session bucket is resolved from utc_hour via SESSION_BUCKETS_UTC.
    """
    for name, (start, end) in SESSION_BUCKETS_UTC.items():
        if start <= utc_hour < end:
            return f"{regime}|{name}|{strategy}"
    return f"{regime}|LATE|{strategy}"  # utc_hour == 24 edge — cannot occur in practice


def get_session_label(utc_hour: int) -> str:
    """Return the canonical session name for a given UTC hour integer."""
    for name, (start, end) in SESSION_BUCKETS_UTC.items():
        if start <= utc_hour < end:
            return name
    return "LATE"


def get_session_integrity_block() -> dict:
    """
    Return a governance metadata dict for inclusion in LIO reports and report
    bundles.  Allows any reader to verify session attribution at report time.
    """
    return {
        "timezone_authority":         SESSION_TIMEZONE_AUTHORITY,
        "utc_hour_source":            SESSION_UTC_SOURCE,
        "os_local_time_used":         SESSION_OS_LOCAL_USED,
        "exchange_timestamp_used":    SESSION_EXCHANGE_TS_USED,
        "session_definition_version": SESSION_DEFINITION_VERSION,
        "buckets_utc": {
            name: {"start": start, "end_exclusive": end, "display": SESSION_DISPLAY[name]}
            for name, (start, end) in SESSION_BUCKETS_UTC.items()
        },
    }
