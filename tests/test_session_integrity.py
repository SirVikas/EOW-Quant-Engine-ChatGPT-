"""
Session Integrity Verifier — FTD-SESSION-HARDENING

Asserts:
  1. Every session bucket boundary in SESSION_BUCKETS_UTC is correct and
     covers all 24 UTC hours without gaps or overlaps.
  2. make_context() produces the expected session label for every UTC hour.
  3. get_session_integrity_block() returns well-formed governance metadata.
  4. No rogue inline bucket logic exists in core/ subsystems (regex scan).
  5. rl_engine imports make_context from the canonical authority, not locally.

Run: python -m pytest tests/test_session_integrity.py -v
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from core.time.session_definitions import (
    SESSION_BUCKETS_UTC,
    SESSION_DEFINITION_VERSION,
    SESSION_DISPLAY,
    SESSION_EXCHANGE_TS_USED,
    SESSION_OS_LOCAL_USED,
    SESSION_TIMEZONE_AUTHORITY,
    SESSION_UTC_SOURCE,
    get_session_integrity_block,
    get_session_label,
    make_context,
)

# ── 1. Bucket coverage ────────────────────────────────────────────────────────

def test_buckets_cover_all_24_hours():
    """Every integer hour 0–23 must map to exactly one session."""
    covered = set()
    for name, (start, end) in SESSION_BUCKETS_UTC.items():
        for h in range(start, end):
            assert h not in covered, f"Hour {h} mapped to multiple sessions"
            covered.add(h)
    assert covered == set(range(24)), f"Uncovered hours: {set(range(24)) - covered}"


def test_bucket_order_and_values():
    """Canonical boundaries must match the agreed values exactly."""
    expected = {"ASIA": (0, 6), "LONDON": (6, 13), "NY": (13, 19), "LATE": (19, 24)}
    assert SESSION_BUCKETS_UTC == expected, (
        f"Boundary mismatch.\nExpected: {expected}\nGot:      {SESSION_BUCKETS_UTC}"
    )


def test_display_windows_present_for_all_sessions():
    assert set(SESSION_DISPLAY.keys()) == set(SESSION_BUCKETS_UTC.keys())
    for name, disp in SESSION_DISPLAY.items():
        assert "utc" in disp and "ist" in disp, f"{name} missing utc/ist display strings"


# ── 2. make_context() per-hour correctness ───────────────────────────────────

@pytest.mark.parametrize("utc_hour,expected_session", [
    (0,  "ASIA"),  (1,  "ASIA"),  (5,  "ASIA"),
    (6,  "LONDON"),(7,  "LONDON"),(12, "LONDON"),
    (13, "NY"),    (14, "NY"),    (18, "NY"),
    (19, "LATE"),  (20, "LATE"),  (23, "LATE"),
])
def test_make_context_session_bucket(utc_hour: int, expected_session: str):
    key = make_context("MEAN_REVERTING", utc_hour, "MR_PAPER")
    parts = key.split("|")
    assert len(parts) == 3, f"Unexpected key format: {key}"
    assert parts[1] == expected_session, (
        f"Hour {utc_hour}: expected {expected_session}, got {parts[1]}"
    )


@pytest.mark.parametrize("utc_hour,expected_session", [
    (5,  "ASIA"),   (6,  "LONDON"),
    (12, "LONDON"), (13, "NY"),
    (18, "NY"),     (19, "LATE"),
])
def test_make_context_boundary_hours(utc_hour: int, expected_session: str):
    """Boundary hours (last of one session / first of next) must route correctly."""
    key = make_context("TRENDING", utc_hour, "TF_STRATEGY")
    assert f"|{expected_session}|" in key


def test_make_context_key_format():
    key = make_context("VOLATILITY_EXPANSION", 14, "VE_PAPER")
    assert key == "VOLATILITY_EXPANSION|NY|VE_PAPER"


def test_get_session_label_all_hours():
    for h in range(24):
        label = get_session_label(h)
        assert label in SESSION_BUCKETS_UTC, f"Hour {h} returned unknown label '{label}'"


# ── 3. Governance metadata block ─────────────────────────────────────────────

def test_session_integrity_block_structure():
    block = get_session_integrity_block()
    assert block["timezone_authority"]         == "UTC"
    assert block["utc_hour_source"]            == "datetime.utcnow().hour"
    assert block["os_local_time_used"]         is False
    assert block["exchange_timestamp_used"]    is False
    assert block["session_definition_version"] == "v1"
    assert set(block["buckets_utc"].keys())    == set(SESSION_BUCKETS_UTC.keys())


def test_session_integrity_block_bucket_detail():
    block = get_session_integrity_block()
    asia = block["buckets_utc"]["ASIA"]
    assert asia["start"] == 0
    assert asia["end_exclusive"] == 6
    assert "utc" in asia["display"]
    assert "ist" in asia["display"]


def test_governance_constants():
    assert SESSION_TIMEZONE_AUTHORITY  == "UTC"
    assert SESSION_UTC_SOURCE          == "datetime.utcnow().hour"
    assert SESSION_OS_LOCAL_USED       is False
    assert SESSION_EXCHANGE_TS_USED    is False
    assert SESSION_DEFINITION_VERSION  == "v1"


# ── 4. No rogue inline bucket logic in core/ ─────────────────────────────────

_ROGUE_PATTERN = re.compile(
    r'bucket\s*=\s*["\'](?:ASIA|LONDON|NY|LATE)["\']'
    r'|if\s+utc_hour\s*<\s*\d+\s*:\s*\n\s+bucket',
    re.MULTILINE,
)

_CORE_ROOT = Path(__file__).parent.parent / "core"
_CANONICAL_FILE = _CORE_ROOT / "time" / "session_definitions.py"


def _py_files_under_core():
    return [
        p for p in _CORE_ROOT.rglob("*.py")
        if p != _CANONICAL_FILE
    ]


def test_no_rogue_inline_bucket_logic():
    """
    No file in core/ (except session_definitions.py itself) should contain
    inline ASIA/LONDON/NY/LATE bucket assignment logic.
    """
    violations = []
    for path in _py_files_under_core():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if _ROGUE_PATTERN.search(text):
            violations.append(str(path.relative_to(_CORE_ROOT.parent)))
    assert not violations, (
        "Rogue inline session bucket logic found — migrate to "
        "core.time.session_definitions.make_context():\n"
        + "\n".join(f"  {v}" for v in violations)
    )


# ── 5. rl_engine imports make_context from canonical source ──────────────────

def test_rl_engine_imports_make_context_from_canonical():
    """rl_engine.py must import make_context from core.time.session_definitions."""
    rl_path = _CORE_ROOT / "rl_engine.py"
    source  = rl_path.read_text(encoding="utf-8")
    assert "from core.time.session_definitions import" in source, (
        "rl_engine.py does not import from core.time.session_definitions"
    )
    assert "make_context" in source.split("from core.time.session_definitions import")[1].split("\n")[0], (
        "rl_engine.py does not import make_context from the canonical authority"
    )


def test_rl_engine_does_not_define_make_context_locally():
    """rl_engine.py must not contain a local def make_context(...)."""
    rl_path = _CORE_ROOT / "rl_engine.py"
    source  = rl_path.read_text(encoding="utf-8")
    # Allow the import line; disallow a local function definition
    local_defs = [
        line for line in source.splitlines()
        if re.match(r"^def make_context\s*\(", line)
    ]
    assert not local_defs, (
        "rl_engine.py defines make_context() locally — remove it and "
        "use the import from core.time.session_definitions"
    )
