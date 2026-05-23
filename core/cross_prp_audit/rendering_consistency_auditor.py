"""
PRP-PHASEB.5 — Institutional Rendering Consistency Audit.

Verifies that render_report_bundle() produces structurally valid, consistent
output across all supported modes when called with empty bundle data.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Any, Dict, List


def _score_tier(score: int) -> str:
    if score >= 80:
        return "HEALTHY"
    if score >= 60:
        return "ADEQUATE"
    if score >= 40:
        return "WEAK"
    return "CRITICAL"


def audit_rendering_consistency() -> dict:
    """
    PRP-PHASEB.5 — Exercise render_report_bundle() across all four modes and
    verify structural guarantees (keys, auto_authorized, section counts, parity).

    Returns a self-contained dict; never raises.
    """
    render_checks: List[Dict[str, Any]] = []
    points: int = 0
    total_points: int = 12  # one per numbered check

    def _pass(check: str, detail: str = "") -> None:
        nonlocal points
        render_checks.append({"check": check, "status": "PASS", "detail": detail})
        points += 1

    def _fail(check: str, detail: str = "") -> None:
        render_checks.append({"check": check, "status": "FAIL", "detail": detail})

    # ── Collect per-mode results ───────────────────────────────────────────────
    mode_results: Dict[str, Dict[str, Any]] = {
        "json":          {"mode": "json",          "status": "UNKNOWN", "error": "", "content_length": 0},
        "html":          {"mode": "html",          "status": "UNKNOWN", "error": "", "content_length": 0},
        "markdown":      {"mode": "markdown",      "status": "UNKNOWN", "error": "", "content_length": 0},
        "executive_html": {"mode": "executive_html", "status": "UNKNOWN", "error": "", "content_length": 0},
    }

    json_result: Any = None
    html_result: Any = None
    md_result: Any = None

    try:
        from core.institutional_report_renderer import render_report_bundle  # lazy
    except Exception as import_exc:
        # All checks fail if the renderer cannot be imported.
        for check_name in [
            "json_returns_dict", "json_required_keys", "json_auto_authorized_false",
            "json_section_count_matches", "json_section_count_gte_20",
            "html_returns_nonempty_str", "html_contains_auto_authorized",
            "markdown_returns_nonempty_str", "markdown_starts_with_hash",
            "html_markdown_name_parity", "no_mode_raises", "executive_html_works",
        ]:
            _fail(check_name, f"render_report_bundle import failed: {import_exc}")
        return _build_result(
            render_checks, mode_results, False, 0, {}, 0, total_points,
        )

    # ── JSON mode ────────────────────────────────────────────────────────────
    try:
        json_result = render_report_bundle({}, mode="json", app_version="audit_test")
        mode_results["json"]["status"] = "OK"
        mode_results["json"]["content_length"] = len(str(json_result))
    except Exception as exc:
        mode_results["json"]["status"] = "ERROR"
        mode_results["json"]["error"] = str(exc)
        json_result = None

    # Check 1: JSON mode returns dict
    if isinstance(json_result, dict):
        _pass("json_returns_dict", "render_report_bundle() with mode=json returned dict")
    else:
        _fail("json_returns_dict", f"Got type={type(json_result).__name__}")

    # Check 2: JSON mode has required keys
    _required_json_keys = {
        "render_mode", "sections", "section_count", "auto_authorized", "generated_at_ms"
    }
    if isinstance(json_result, dict):
        present = _required_json_keys.issubset(json_result.keys())
        if present:
            _pass("json_required_keys", f"All required keys present: {sorted(_required_json_keys)}")
        else:
            missing = _required_json_keys - json_result.keys()
            _fail("json_required_keys", f"Missing: {sorted(missing)}")
    else:
        _fail("json_required_keys", "Skipped — json_result is not a dict")

    # Check 3: JSON mode auto_authorized is False
    auto_authorized_enforced: bool = False
    if isinstance(json_result, dict):
        if json_result.get("auto_authorized") is False:
            auto_authorized_enforced = True
            _pass("json_auto_authorized_false", "auto_authorized=False confirmed in JSON mode")
        else:
            _fail(
                "json_auto_authorized_false",
                f"auto_authorized={json_result.get('auto_authorized')}",
            )
    else:
        _fail("json_auto_authorized_false", "Skipped — json_result is not a dict")

    # Check 4: JSON mode section_count == len(sections)
    section_count_json: int = 0
    if isinstance(json_result, dict):
        sc = json_result.get("section_count", -1)
        sections = json_result.get("sections", [])
        section_count_json = sc if isinstance(sc, int) and sc >= 0 else len(sections)
        if isinstance(sections, list) and sc == len(sections):
            _pass("json_section_count_matches", f"section_count={sc} == len(sections)={len(sections)}")
        else:
            _fail(
                "json_section_count_matches",
                f"section_count={sc}, len(sections)={len(sections) if isinstance(sections, list) else 'N/A'}",
            )
    else:
        _fail("json_section_count_matches", "Skipped — json_result is not a dict")

    # Check 5: JSON mode section_count >= 20
    if isinstance(json_result, dict):
        sc = json_result.get("section_count", 0)
        if isinstance(sc, int) and sc >= 20:
            _pass("json_section_count_gte_20", f"section_count={sc} >= 20")
        else:
            _fail("json_section_count_gte_20", f"section_count={sc} < 20")
    else:
        _fail("json_section_count_gte_20", "Skipped — json_result is not a dict")

    # ── HTML mode ────────────────────────────────────────────────────────────
    try:
        html_result = render_report_bundle({}, mode="html", app_version="audit_test")
        mode_results["html"]["status"] = "OK"
        mode_results["html"]["content_length"] = len(html_result) if isinstance(html_result, str) else 0
    except Exception as exc:
        mode_results["html"]["status"] = "ERROR"
        mode_results["html"]["error"] = str(exc)
        html_result = None

    # Check 6: HTML mode returns non-empty str
    if isinstance(html_result, str) and len(html_result) > 0:
        _pass("html_returns_nonempty_str", f"HTML string length={len(html_result)}")
    else:
        _fail("html_returns_nonempty_str", f"Got type={type(html_result).__name__}, len={len(html_result) if isinstance(html_result, str) else 'N/A'}")

    # Check 7: HTML mode contains "auto_authorized" text
    if isinstance(html_result, str) and "auto_authorized" in html_result:
        auto_authorized_enforced = auto_authorized_enforced and True
        _pass("html_contains_auto_authorized", "HTML output contains 'auto_authorized'")
    else:
        auto_authorized_enforced = False
        _fail("html_contains_auto_authorized", "String 'auto_authorized' not found in HTML output")

    # ── Markdown mode ─────────────────────────────────────────────────────────
    try:
        md_result = render_report_bundle({}, mode="markdown", app_version="audit_test")
        mode_results["markdown"]["status"] = "OK"
        mode_results["markdown"]["content_length"] = len(md_result) if isinstance(md_result, str) else 0
    except Exception as exc:
        mode_results["markdown"]["status"] = "ERROR"
        mode_results["markdown"]["error"] = str(exc)
        md_result = None

    # Check 8: Markdown mode returns non-empty str
    if isinstance(md_result, str) and len(md_result) > 0:
        _pass("markdown_returns_nonempty_str", f"Markdown string length={len(md_result)}")
    else:
        _fail("markdown_returns_nonempty_str", f"Got type={type(md_result).__name__}")

    # Check 9: Markdown mode starts with "#"
    if isinstance(md_result, str) and md_result.lstrip().startswith("#"):
        _pass("markdown_starts_with_hash", "Markdown output starts with '#'")
    else:
        first_chars = repr(md_result[:20]) if isinstance(md_result, str) else "N/A"
        _fail("markdown_starts_with_hash", f"First chars: {first_chars}")

    # Check 10: HTML and markdown parity — spot-check 3 report names
    _spot_names = ["SUMMARY", "ECOLOGY", "RL"]
    html_has_summary   = isinstance(html_result, str) and "SUMMARY"  in html_result.upper()
    html_has_ecology   = isinstance(html_result, str) and "ECOLOGY"  in html_result.upper()
    md_has_summary     = isinstance(md_result,   str) and "SUMMARY"  in md_result.upper()

    parity_checks: Dict[str, bool] = {
        "html_has_summary":      html_has_summary,
        "markdown_has_summary":  md_has_summary,
        "html_has_ecology":      html_has_ecology,
    }

    if html_has_summary and md_has_summary and html_has_ecology:
        _pass(
            "html_markdown_name_parity",
            "SUMMARY, ECOLOGY found in HTML; SUMMARY found in Markdown",
        )
    else:
        _fail(
            "html_markdown_name_parity",
            f"html_summary={html_has_summary}, md_summary={md_has_summary}, html_ecology={html_has_ecology}",
        )

    # Check 11: No mode raises exception with empty bundle data
    # (We already ran all modes; status=OK means no exception was raised.)
    modes_errored = [m for m, r in mode_results.items() if r["status"] == "ERROR" and m != "executive_html"]
    if not modes_errored:
        _pass("no_mode_raises", "json/html/markdown all completed without exception")
    else:
        _fail("no_mode_raises", f"Modes that raised: {modes_errored}")

    # Check 12: executive_html mode works without exception
    try:
        exec_result = render_report_bundle(
            {}, mode="executive_html", app_version="audit_test"
        )
        mode_results["executive_html"]["status"] = "OK"
        mode_results["executive_html"]["content_length"] = (
            len(exec_result) if isinstance(exec_result, str) else 0
        )
        if isinstance(exec_result, str):
            _pass("executive_html_works", f"executive_html string length={len(exec_result)}")
        else:
            _fail("executive_html_works", f"Got type={type(exec_result).__name__}")
    except Exception as exc:
        mode_results["executive_html"]["status"] = "ERROR"
        mode_results["executive_html"]["error"] = str(exc)
        _fail("executive_html_works", str(exc))

    # ── Score ─────────────────────────────────────────────────────────────────
    rendering_score = min(100, round(points / total_points * 100))

    return _build_result(
        render_checks,
        mode_results,
        auto_authorized_enforced,
        section_count_json,
        parity_checks,
        rendering_score,
        total_points,
    )


def _build_result(
    render_checks: List[Dict[str, Any]],
    mode_results: Dict[str, Dict[str, Any]],
    auto_authorized_enforced: bool,
    section_count_json: int,
    parity_checks: Dict[str, bool],
    rendering_score: int,
    total_points: int,
) -> dict:
    def _score_tier(score: int) -> str:
        if score >= 80:
            return "HEALTHY"
        if score >= 60:
            return "ADEQUATE"
        if score >= 40:
            return "WEAK"
        return "CRITICAL"

    return {
        "report":                  "INSTITUTIONAL_RENDERING_AUDIT",
        "mode_results":            mode_results,
        "render_checks":           render_checks,
        "auto_authorized_enforced": auto_authorized_enforced,
        "section_count_json":      section_count_json,
        "parity_checks":           parity_checks,
        "rendering_score":         rendering_score,
        "rendering_tier":          _score_tier(rendering_score),
        "auto_authorized":         False,
        "generated_ts":            int(_time.time() * 1000),
    }
