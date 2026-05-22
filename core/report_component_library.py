"""
FTD-IREL: Institutional Report Component Library.

Componentized rendering primitives for the PHOENIX institutional reporting layer.
All components return structured dicts consumable by the renderer or serialized to JSON.

Severity tier → CSS class mapping:
  HEALTHY    → green
  ADEQUATE   → blue
  VULNERABLE → amber
  CRITICAL   → red
  LOCKDOWN   → red (with extra flag)
  UNKNOWN    → gray

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

from typing import Any, List

# ── Tier → CSS class mapping ──────────────────────────────────────────────────
_TIER_COLORS: dict = {
    "HEALTHY":    "color-green",
    "ADEQUATE":   "color-blue",
    "VULNERABLE": "color-amber",
    "CRITICAL":   "color-red",
    "LOCKDOWN":   "color-red",
    "UNKNOWN":    "color-gray",
}

# ── Family → CSS color class mapping ─────────────────────────────────────────
_FAMILY_COLORS: dict = {
    "ECONOMIC":        "color-green",
    "COGNITIVE":       "color-blue",
    "GOVERNANCE":      "color-purple",
    "EPISTEMIC":       "color-teal",
    "CONTINUITY":      "color-amber",
    "HUMAN_ALIGNMENT": "color-mint",
    "REPLAY":          "color-sky",
    "FORENSICS":       "color-gray",
}

_SEVERITY_COLORS: dict = {
    "CRITICAL": "color-red",
    "HIGH":     "color-amber",
    "MEDIUM":   "color-blue",
    "LOW":      "color-green",
    "NOTICE":   "color-teal",
    "INFO":     "color-gray",
}


# ── Helper primitives ─────────────────────────────────────────────────────────

def tier_color_class(tier: str) -> str:
    """Returns CSS color class string for a health tier."""
    return _TIER_COLORS.get(str(tier).upper(), "color-gray")


def family_color_class(family: str) -> str:
    """Returns CSS color class string for a report family."""
    return _FAMILY_COLORS.get(str(family).upper(), "color-gray")


def format_pct(value: float, already_pct: bool = True) -> str:
    """
    Safe percentage formatter.
    If already_pct=True, value is already 0–100; clamp before formatting.
    If already_pct=False, value is 0.0–1.0 fraction; multiply by 100 first.
    """
    try:
        v = float(value)
        if not already_pct:
            v = v * 100.0
        v = max(0.0, min(100.0, v))
        return f"{v:.1f}%"
    except Exception:
        return "0.0%"


def get_component_library_version() -> str:
    """Returns the component library version string."""
    return "1.0"


# ── Component constructors ────────────────────────────────────────────────────

def health_card(
    label: str,
    value: Any,
    tier: str = "UNKNOWN",
    sub: str = "",
    details: str = "",
) -> dict:
    """
    Single KPI card with tier-derived color.
    Used for primary health indicators in the executive and governance tabs.
    """
    t = str(tier).upper()
    return {
        "component_type": "health_card",
        "label":          str(label),
        "value":          value,
        "tier":           t,
        "sub":            str(sub),
        "details":        str(details),
        "color_class":    tier_color_class(t),
        "is_lockdown":    t == "LOCKDOWN",
    }


def metrics_table(headers: list, rows: list) -> dict:
    """
    Tabular metrics component.
    headers: list of column header strings.
    rows: list of lists (each inner list is a row of values).
    """
    return {
        "component_type": "metrics_table",
        "headers":        list(headers),
        "rows":           [list(r) for r in rows],
        "row_count":      len(rows),
        "col_count":      len(headers),
    }


def severity_badge(severity: str, label: str = "") -> dict:
    """Inline severity badge — renders as a colored pill."""
    s = str(severity).upper()
    return {
        "component_type": "severity_badge",
        "severity":       s,
        "label":          str(label) if label else s,
        "color_class":    _SEVERITY_COLORS.get(s, "color-gray"),
    }


def lineage_panel(
    snapshot_count: int,
    versions: list,
    latest_id: str = "",
) -> dict:
    """
    Snapshot lineage summary panel — shows count, version history,
    and latest snapshot anchor.
    """
    return {
        "component_type":   "lineage_panel",
        "snapshot_count":   int(snapshot_count),
        "versions":         list(versions),
        "version_count":    len(versions),
        "latest_id":        str(latest_id),
        "lineage_anchored": bool(latest_id),
    }


def recommendation_row(
    priority: str,
    rec_type: str,
    summary: str,
    auto_authorized: bool = False,
) -> dict:
    """
    Single recommendation row for the recommendations panel.
    auto_authorized is always overridden to False per constitutional requirement.
    """
    p = str(priority).upper()
    return {
        "component_type":  "recommendation_row",
        "priority":        p,
        "rec_type":        str(rec_type),
        "summary":         str(summary),
        "color_class":     _SEVERITY_COLORS.get(p, "color-gray"),
        # Constitutional: recommendations are never autonomously authorized
        "auto_authorized": False,
    }


def constitutional_warning(message: str, severity: str = "NOTICE") -> dict:
    """
    Constitutional governance warning block.
    Always renders with auto_authorized=False per hard principle.
    """
    s = str(severity).upper()
    return {
        "component_type":  "constitutional_warning",
        "message":         str(message),
        "severity":        s,
        "color_class":     _SEVERITY_COLORS.get(s, "color-teal"),
        "auto_authorized": False,
        "human_authority": True,
    }


def progress_bar(
    label: str,
    current: Any,
    target: Any,
    unit: str = "",
) -> dict:
    """
    Progress bar component. pct is clamped to 0–100.
    Handles zero-target safely.
    """
    try:
        c = float(current)
        t = float(target)
        pct = (c / t * 100.0) if t != 0 else 0.0
        pct = max(0.0, min(100.0, pct))
    except Exception:
        c, t, pct = 0.0, 0.0, 0.0

    return {
        "component_type": "progress_bar",
        "label":          str(label),
        "current":        c,
        "target":         t,
        "unit":           str(unit),
        "pct":            round(pct, 1),
        "pct_str":        f"{pct:.1f}%",
    }


def kpi_grid(kpis: list) -> dict:
    """
    Grid of KPI tiles.
    kpis: list of dicts with keys {label, value, sub}.
    Missing keys are filled with empty strings.
    """
    normalized = [
        {
            "label": str(k.get("label", "")),
            "value": k.get("value", "—"),
            "sub":   str(k.get("sub", "")),
        }
        for k in (kpis or [])
    ]
    return {
        "component_type": "kpi_grid",
        "kpis":           normalized,
        "kpi_count":      len(normalized),
    }


def evolution_trajectory(
    early: Any,
    mid: Any,
    late: Any,
    metric_name: str,
    unit: str = "",
) -> dict:
    """
    Three-point evolution trajectory component.
    Determines trend from early→late comparison:
      IMPROVING if late > early,
      DEGRADING  if late < early,
      FLAT       otherwise.
    """
    try:
        e, m, l = float(early), float(mid), float(late)
        if l > e:
            trend = "IMPROVING"
        elif l < e:
            trend = "DEGRADING"
        else:
            trend = "FLAT"
    except Exception:
        e, m, l = 0.0, 0.0, 0.0
        trend = "FLAT"

    return {
        "component_type": "evolution_trajectory",
        "metric_name":    str(metric_name),
        "unit":           str(unit),
        "early":          e,
        "mid":            m,
        "late":           l,
        "trend":          trend,
        "color_class":    "color-green" if trend == "IMPROVING" else (
                          "color-red" if trend == "DEGRADING" else "color-gray"
                          ),
    }


def dependency_chain_view(
    report_id: str,
    direct_deps: list,
    transitive_deps: list,
) -> dict:
    """
    Dependency chain visualization component for a single report.
    Separates direct dependencies from transitive (indirect) ones.
    """
    direct = list(direct_deps or [])
    trans  = [d for d in (transitive_deps or []) if d not in direct]
    return {
        "component_type":   "dependency_chain_view",
        "report_id":        str(report_id),
        "direct_deps":      direct,
        "transitive_deps":  trans,
        "direct_count":     len(direct),
        "transitive_count": len(trans),
        "total_dep_count":  len(direct) + len(trans),
        "is_primitive":     len(direct) == 0,
    }
