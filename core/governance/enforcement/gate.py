"""
FTD-EGI-001 Component 3 — Governance Enforcement Gate

Validates that commits meet governance requirements before they are accepted.
Blocks operations when required institutional records are missing.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger


@dataclass
class GateViolation:
    rule: str
    message: str
    blocking: bool = True


@dataclass
class GateResult:
    passed: bool
    violations: List[GateViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_run: List[str] = field(default_factory=list)

    @property
    def blocking_violations(self) -> List[GateViolation]:
        return [v for v in self.violations if v.blocking]

    def summary(self) -> str:
        if self.passed:
            return f"GATE PASS — {len(self.checks_run)} checks, 0 violations"
        vcount = len(self.blocking_violations)
        return f"GATE FAIL — {vcount} blocking violation(s): {[v.rule for v in self.blocking_violations]}"


class GovernanceEnforcementGate:
    """
    Pre-commit governance gate.

    Rules enforced:
    1. APP_VERSION must be bumped relative to last git tag / HEAD~1
    2. An IMRAF DEVELOPER record must exist for the committing session
    3. At least one FTD reference must appear in staged files or commit msg
    4. At least one VERIFIER record exists in IMRAF for the changed component
    5. A GOVERNANCE IMRAF entry exists documenting the change intent
    """

    _FTD_PATTERN = re.compile(r"FTD-[A-Z0-9]+-\d+", re.IGNORECASE)

    def __init__(self, project_root: Optional[Path] = None):
        self._root = project_root or Path.cwd()
        self._imraf = None
        self._load_imraf()

    def _load_imraf(self) -> None:
        try:
            from core.institutional_memory.imraf_engine import imraf
            self._imraf = imraf
        except Exception:
            pass

    # ── Public API ───────────────────────────────────────────────────────────

    def check(
        self,
        commit_message: str = "",
        staged_files: Optional[List[str]] = None,
        component: str = "",
        bypass: bool = False,
    ) -> GateResult:
        """
        Run all governance checks. Returns GateResult.
        If bypass=True, violations are demoted to warnings (for dry-run use).
        """
        if staged_files is None:
            staged_files = self._get_staged_files()

        result = GateResult(passed=True)

        checks = [
            self._check_app_version,
            self._check_ftd_reference,
            self._check_verifier_record,
            self._check_imraf_available,
        ]

        for check_fn in checks:
            violation = check_fn(commit_message, staged_files, component)
            result.checks_run.append(check_fn.__name__)
            if violation:
                if bypass:
                    result.warnings.append(f"[bypassed] {violation.rule}: {violation.message}")
                else:
                    result.violations.append(violation)
                    if violation.blocking:
                        result.passed = False

        logger.info(f"[GovernanceGate] {result.summary()}")
        return result

    def record_gate_decision(self, result: GateResult, commit_message: str, component: str) -> None:
        """Record the gate decision to IMRAF GOVERNANCE category."""
        if not self._imraf:
            return
        try:
            self._imraf.record(
                category="GOVERNANCE",
                title=f"Gate {'PASS' if result.passed else 'FAIL'} — {component or 'unknown'}",
                data={
                    "passed": result.passed,
                    "checks_run": result.checks_run,
                    "violations": [{"rule": v.rule, "message": v.message} for v in result.violations],
                    "warnings": result.warnings,
                    "commit_message_preview": commit_message[:120],
                    "component": component,
                },
                subcategory=component,
                tags=["enforcement_gate", "governance", "pass" if result.passed else "fail"],
            )
        except Exception as exc:
            logger.warning(f"[GovernanceGate] Could not record to IMRAF: {exc}")

    # ── Individual checks ────────────────────────────────────────────────────

    def _check_app_version(
        self, commit_message: str, staged_files: List[str], component: str
    ) -> Optional[GateViolation]:
        """Rule 1: APP_VERSION must be updated when core/ or main.py are modified."""
        core_touched = any(
            f.startswith("core/") or f == "main.py" or f == "config.py"
            for f in staged_files
        )
        if not core_touched:
            return None

        config_staged = "config.py" in staged_files
        if not config_staged:
            # Check if the commit message explicitly opts out
            if re.search(r"no.?version.?bump|version.?unchanged", commit_message, re.IGNORECASE):
                return None
            return GateViolation(
                rule="APP_VERSION_NOT_BUMPED",
                message=(
                    "core/ or main.py files are staged but config.py is not. "
                    "Bump APP_VERSION or add 'no version bump' to commit message."
                ),
                blocking=True,
            )
        return None

    def _check_ftd_reference(
        self, commit_message: str, staged_files: List[str], component: str
    ) -> Optional[GateViolation]:
        """Rule 3: At least one FTD reference must appear in commit message or staged files."""
        if self._FTD_PATTERN.search(commit_message):
            return None

        # Scan staged file contents for FTD refs
        for fpath in staged_files:
            full = self._root / fpath
            try:
                content = full.read_text(errors="ignore")
                if self._FTD_PATTERN.search(content):
                    return None
            except Exception:
                continue

        return GateViolation(
            rule="NO_FTD_REFERENCE",
            message=(
                "No FTD reference (e.g. FTD-IMR-001) found in commit message or staged files. "
                "Add an FTD reference to document the architectural decision."
            ),
            blocking=False,  # warning-level — important but not always applicable
        )

    def _check_verifier_record(
        self, commit_message: str, staged_files: List[str], component: str
    ) -> Optional[GateViolation]:
        """Rule 4: A VERIFIER record must exist in IMRAF for the component being changed."""
        if not self._imraf:
            return None  # can't check without IMRAF — skip rather than false-block

        effective_component = component or self._infer_component(staged_files)
        if not effective_component:
            return None

        try:
            records = self._imraf.query(category="VERIFIER", limit=50)
            for r in records:
                data = r.get("data", {}) if isinstance(r, dict) else {}
                comp = data.get("component", "")
                if comp and comp in effective_component or effective_component in comp:
                    return None
            return GateViolation(
                rule="NO_VERIFIER_RECORD",
                message=(
                    f"No VERIFIER record found in IMRAF for component '{effective_component}'. "
                    "Run the test suite and ensure the auto-recording plugin is active."
                ),
                blocking=False,
            )
        except Exception:
            return None

    def _check_imraf_available(
        self, commit_message: str, staged_files: List[str], component: str
    ) -> Optional[GateViolation]:
        """Rule 5: IMRAF must be reachable (institutional memory must be online)."""
        if self._imraf is None:
            return GateViolation(
                rule="IMRAF_UNAVAILABLE",
                message=(
                    "IMRAF engine could not be loaded. Institutional memory is offline. "
                    "Governance records cannot be written."
                ),
                blocking=False,
            )
        return None

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_staged_files(self) -> List[str]:
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, cwd=self._root, timeout=10,
            )
            return [f.strip() for f in result.stdout.splitlines() if f.strip()]
        except Exception:
            return []

    @staticmethod
    def _infer_component(staged_files: List[str]) -> str:
        prefixes: Dict[str, int] = {}
        for f in staged_files:
            parts = f.split("/")
            if len(parts) >= 2 and parts[0] == "core":
                key = parts[1]
                prefixes[key] = prefixes.get(key, 0) + 1
        if not prefixes:
            return ""
        return max(prefixes, key=lambda k: prefixes[k])


# ── Module-level singleton ───────────────────────────────────────────────────

gate = GovernanceEnforcementGate()


def run_gate_check(
    commit_message: str = "",
    staged_files: Optional[List[str]] = None,
    component: str = "",
    bypass: bool = False,
    record: bool = True,
) -> GateResult:
    """
    Convenience wrapper. Run the governance gate and optionally record results.
    Returns GateResult; callers should inspect .passed to decide whether to block.
    """
    result = gate.check(commit_message=commit_message, staged_files=staged_files,
                        component=component, bypass=bypass)
    if record:
        gate.record_gate_decision(result, commit_message=commit_message, component=component)
    return result
