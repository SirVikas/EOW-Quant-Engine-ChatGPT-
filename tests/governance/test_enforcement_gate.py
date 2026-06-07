"""Tests for FTD-EGI-001 Component 3 — Governance Enforcement Gate."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.governance.enforcement.gate import (
    GateResult,
    GateViolation,
    GovernanceEnforcementGate,
    run_gate_check,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

class _StubIMRAF:
    def __init__(self, verifier_records=None):
        self._verifier_records = verifier_records or []
        self._governance_records = []

    def record(self, category, title, data, subcategory="", tags=None):
        self._governance_records.append({"category": category, "title": title})
        return 1

    def query(self, category=None, limit=100):
        if category == "VERIFIER":
            return self._verifier_records
        return []


@pytest.fixture()
def gate_no_imraf(tmp_path):
    g = GovernanceEnforcementGate.__new__(GovernanceEnforcementGate)
    g._root = tmp_path
    g._imraf = None
    return g


@pytest.fixture()
def gate_with_imraf(tmp_path):
    stub = _StubIMRAF(verifier_records=[
        {"data": {"component": "ema"}, "category": "VERIFIER"},
    ])
    g = GovernanceEnforcementGate.__new__(GovernanceEnforcementGate)
    g._root = tmp_path
    g._imraf = stub
    return g


# ── GateViolation ─────────────────────────────────────────────────────────────

def test_gate_violation_defaults_blocking():
    v = GateViolation(rule="TEST", message="msg")
    assert v.blocking is True


def test_gate_violation_non_blocking():
    v = GateViolation(rule="TEST", message="msg", blocking=False)
    assert v.blocking is False


# ── GateResult ────────────────────────────────────────────────────────────────

def test_gate_result_passed():
    r = GateResult(passed=True)
    assert r.passed
    assert r.blocking_violations == []


def test_gate_result_summary_pass():
    r = GateResult(passed=True, checks_run=["check_a", "check_b"])
    assert "PASS" in r.summary()


def test_gate_result_summary_fail():
    r = GateResult(passed=False, violations=[GateViolation("R1", "msg")])
    assert "FAIL" in r.summary()
    assert "R1" in r.summary()


def test_gate_result_blocking_violations_filter():
    r = GateResult(
        passed=False,
        violations=[
            GateViolation("BLOCKING", "b", blocking=True),
            GateViolation("WARN", "w", blocking=False),
        ],
    )
    assert len(r.blocking_violations) == 1
    assert r.blocking_violations[0].rule == "BLOCKING"


# ── APP_VERSION check ─────────────────────────────────────────────────────────

def test_version_check_no_core_files(gate_no_imraf):
    """When no core files are staged, version check passes."""
    result = gate_no_imraf._check_app_version("fix typo", ["README.md"], "")
    assert result is None


def test_version_check_core_without_config(gate_no_imraf):
    """core/ staged but config.py not staged → violation."""
    result = gate_no_imraf._check_app_version(
        "FTD-IMR-001: improve query", ["core/imraf/engine.py"], ""
    )
    assert result is not None
    assert result.rule == "APP_VERSION_NOT_BUMPED"
    assert result.blocking is True


def test_version_check_core_with_config(gate_no_imraf):
    """config.py staged alongside core/ → no violation."""
    result = gate_no_imraf._check_app_version(
        "FTD-IMR-001: bump version", ["core/imraf/engine.py", "config.py"], ""
    )
    assert result is None


def test_version_check_no_version_bump_opt_out(gate_no_imraf):
    """Commit message opt-out phrase skips check."""
    result = gate_no_imraf._check_app_version(
        "docs: no version bump", ["core/imraf/engine.py"], ""
    )
    assert result is None


def test_version_check_main_py_triggers_check(gate_no_imraf):
    result = gate_no_imraf._check_app_version("fix main", ["main.py"], "")
    assert result is not None
    assert result.rule == "APP_VERSION_NOT_BUMPED"


# ── FTD reference check ───────────────────────────────────────────────────────

def test_ftd_check_in_commit_message(gate_no_imraf):
    result = gate_no_imraf._check_ftd_reference(
        "FTD-IMR-001: improve query speed", [], ""
    )
    assert result is None


def test_ftd_check_in_staged_file(gate_no_imraf, tmp_path):
    (tmp_path / "some_file.py").write_text("# FTD-EMA-001 compliance\npass\n")
    gate_no_imraf._root = tmp_path
    result = gate_no_imraf._check_ftd_reference("improve things", ["some_file.py"], "")
    assert result is None


def test_ftd_check_missing(gate_no_imraf):
    result = gate_no_imraf._check_ftd_reference("fix a bug", ["README.md"], "")
    assert result is not None
    assert result.rule == "NO_FTD_REFERENCE"
    assert result.blocking is False  # warning-level


def test_ftd_check_pattern_case_insensitive(gate_no_imraf):
    result = gate_no_imraf._check_ftd_reference("ftd-imr-001: something", [], "")
    assert result is None


# ── Verifier record check ─────────────────────────────────────────────────────

def test_verifier_check_no_imraf(gate_no_imraf):
    """Without IMRAF, verifier check skips rather than blocking."""
    result = gate_no_imraf._check_verifier_record("msg", ["core/ema/ema_engine.py"], "ema")
    assert result is None


def test_verifier_check_matching_record(gate_with_imraf):
    result = gate_with_imraf._check_verifier_record("msg", ["core/ema/engine.py"], "ema")
    assert result is None


def test_verifier_check_missing_record(gate_with_imraf):
    result = gate_with_imraf._check_verifier_record("msg", ["core/dial/dial_engine.py"], "dial")
    assert result is not None
    assert result.rule == "NO_VERIFIER_RECORD"
    assert result.blocking is False


# ── IMRAF availability check ──────────────────────────────────────────────────

def test_imraf_unavailable_violation(gate_no_imraf):
    result = gate_no_imraf._check_imraf_available("msg", [], "")
    assert result is not None
    assert result.rule == "IMRAF_UNAVAILABLE"
    assert result.blocking is False


def test_imraf_available_no_violation(gate_with_imraf):
    result = gate_with_imraf._check_imraf_available("msg", [], "")
    assert result is None


# ── Full gate.check() ─────────────────────────────────────────────────────────

def test_full_check_no_files(gate_no_imraf):
    result = gate_no_imraf.check(commit_message="docs update", staged_files=[], component="")
    assert isinstance(result, GateResult)


def test_full_check_bypass_converts_to_warnings(gate_no_imraf):
    result = gate_no_imraf.check(
        commit_message="broke everything",
        staged_files=["core/imraf/engine.py"],
        component="imraf",
        bypass=True,
    )
    assert result.passed is True  # bypass: violations become warnings
    assert len(result.warnings) > 0


def test_full_check_with_valid_commit(gate_with_imraf):
    result = gate_with_imraf.check(
        commit_message="FTD-EMA-001: bump version",
        staged_files=["core/ema/ema_engine.py", "config.py"],
        component="ema",
    )
    assert isinstance(result, GateResult)
    assert all(not v.blocking for v in result.violations)


def test_checks_run_populated(gate_no_imraf):
    result = gate_no_imraf.check(commit_message="x", staged_files=[], component="")
    assert len(result.checks_run) > 0


# ── _infer_component ──────────────────────────────────────────────────────────

def test_infer_component_empty():
    assert GovernanceEnforcementGate._infer_component([]) == ""


def test_infer_component_core_files():
    files = ["core/ema/ema_engine.py", "core/ema/__init__.py", "core/dial/dial_engine.py"]
    assert GovernanceEnforcementGate._infer_component(files) == "ema"


def test_infer_component_non_core():
    files = ["tests/test_main.py", "README.md"]
    assert GovernanceEnforcementGate._infer_component(files) == ""


# ── run_gate_check convenience function ───────────────────────────────────────

def test_run_gate_check_returns_gate_result():
    result = run_gate_check(
        commit_message="FTD-EGI-001: governance test",
        staged_files=[],
        component="governance",
        bypass=True,
        record=False,
    )
    assert isinstance(result, GateResult)
