"""
FTD-EGI-001 Component 2 — Verifier Auto-Recording Engine

A pytest plugin that automatically records every test run into IMRAF.
No manual action required. Every pytest execution creates a VERIFIER record.

Registration: conftest.py at project root imports this plugin.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from loguru import logger


class IMRAFVerifierPlugin:
    """
    Pytest plugin that hooks into session start/finish and records
    verifier results into IMRAF automatically.
    """

    def __init__(self):
        self._start_ts: int = 0
        self._results: Dict[str, Any] = {}
        self._imraf = None
        self._load_imraf()

    def _load_imraf(self) -> None:
        try:
            from core.institutional_memory.imraf_engine import imraf
            self._imraf = imraf
        except Exception:
            pass  # degraded — plugin still runs, just doesn't record

    # ── pytest hooks ─────────────────────────────────────────────────────────

    def pytest_sessionstart(self, session) -> None:
        self._start_ts = int(time.time() * 1000)
        self._results = {
            "passed": [], "failed": [], "errors": [], "skipped": [],
        }

    def pytest_runtest_logreport(self, report) -> None:
        if report.when != "call":
            return
        node_id = report.nodeid
        if report.passed:
            self._results["passed"].append(node_id)
        elif report.failed:
            self._results["failed"].append(node_id)
        else:
            self._results["skipped"].append(node_id)

    def pytest_sessionfinish(self, session, exitstatus) -> None:
        if not self._imraf:
            return

        elapsed_ms  = int(time.time() * 1000) - self._start_ts
        passed      = len(self._results["passed"])
        failed      = len(self._results["failed"])
        total       = passed + failed + len(self._results["skipped"])
        pass_rate   = round(passed / max(total, 1) * 100, 1)
        confidence  = "HIGH" if pass_rate >= 95 else "MEDIUM" if pass_rate >= 80 else "LOW"

        # Determine component from test paths
        all_nodeids = (
            self._results["passed"] + self._results["failed"] + self._results["skipped"]
        )
        component = _infer_component(all_nodeids)

        try:
            from config import APP_VERSION
        except Exception:
            APP_VERSION = "unknown"

        try:
            self._imraf.record(
                category    = "VERIFIER",
                title       = f"pytest run — {component} — {passed}/{total} passed",
                data        = {
                    "verifier_name":      f"pytest:{component}",
                    "passed_tests":       passed,
                    "failed_tests":       failed,
                    "skipped_tests":      len(self._results["skipped"]),
                    "total_tests":        total,
                    "pass_rate":          pass_rate,
                    "coverage":           0.0,   # filled by coverage.py if enabled
                    "confidence":         confidence,
                    "duration_ms":        elapsed_ms,
                    "component":          component,
                    "version":            APP_VERSION,
                    "historical_failures": self._results["failed"][:10],
                    "exit_status":        exitstatus,
                },
                subcategory = component,
                tags        = ["verifier", "auto_recorded", confidence.lower(), component],
            )
            logger.info(
                f"[AutoRecord] Verifier result recorded — {passed}/{total} passed "
                f"({pass_rate}%) | confidence={confidence} | component={component}"
            )
        except Exception as exc:
            logger.error(f"[AutoRecord] Failed to record verifier result: {exc}")


def _infer_component(nodeids: List[str]) -> str:
    """Infer the primary component being tested from node IDs."""
    if not nodeids:
        return "general"
    # Count path prefixes
    prefixes: Dict[str, int] = {}
    for nid in nodeids:
        parts = nid.split("/")
        if len(parts) >= 2:
            prefix = parts[1] if parts[0] == "tests" else parts[0]
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
    if not prefixes:
        return "general"
    return max(prefixes, key=lambda k: prefixes[k])


# ── Standalone recording function (callable without pytest) ──────────────────

def record_verifier_run(
    verifier_name: str,
    passed: int,
    failed: int,
    component: str = "",
    coverage: float = 0.0,
    notes: str = "",
    historical_failures: Optional[List[str]] = None,
) -> int:
    """
    Manually record a verifier result into IMRAF.
    Use when pytest plugin is not active (e.g., CI pipelines, manual runs).
    Returns IMRAF record ID, -1 on failure.
    """
    try:
        from core.institutional_memory.imraf_engine import imraf
        total     = passed + failed
        pass_rate = round(passed / max(total, 1) * 100, 1)
        confidence = "HIGH" if pass_rate >= 95 else "MEDIUM" if pass_rate >= 80 else "LOW"
        try:
            from config import APP_VERSION
        except Exception:
            APP_VERSION = "unknown"

        return imraf.record(
            category    = "VERIFIER",
            title       = f"{verifier_name} — {passed}/{total} passed",
            data        = {
                "verifier_name":      verifier_name,
                "passed_tests":       passed,
                "failed_tests":       failed,
                "total_tests":        total,
                "pass_rate":          pass_rate,
                "coverage":           coverage,
                "confidence":         confidence,
                "component":          component,
                "version":            APP_VERSION,
                "historical_failures": historical_failures or [],
                "notes":              notes,
            },
            subcategory = component,
            tags        = ["verifier", "manual", confidence.lower(), component],
        )
    except Exception as exc:
        logger.error(f"[AutoRecord] record_verifier_run failed: {exc}")
        return -1
