"""
PRP-PHASEC.1 — Executive Compression Engine.

Converts 30+ institutional reports into a single executive operational view.
Output is economically honest, governance honest, and survivability honest —
"beautiful lies" are explicitly prohibited by PHASEC doctrine.

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
        return "DEGRADED"
    return "CRITICAL"


def generate_executive_compression() -> dict:
    """
    PRP-PHASEC.1 — Generate an executive-level compression of the full
    institutional intelligence ecosystem.

    Synthesises:
      - Ecosystem health (from institutional_health_score_engine)
      - Top risk extraction (from anomaly_clustering_engine)
      - Alpha condition (from signal ecology)
      - Governance state (from governance_compression_layer)
      - Survivability highlights (from signal ecology)
      - Report coverage (from dashboard_orchestrator)

    Returns EXECUTIVE_COMPRESSION_REPORT; never raises.
    """
    top_risks: List[str] = []
    survivability_highlights: List[str] = []
    critical_anomalies: List[dict] = []
    summary_lines: List[str] = []
    ecosystem_health_score: int = 0
    ecosystem_health_tier: str = "UNKNOWN"
    alpha_condition: str = "UNKNOWN"
    governance_state: str = "UNKNOWN"

    # ── Sub-module 1: Ecosystem Health ────────────────────────────────────────
    try:
        from core.operational_compression.institutional_health_score_engine import (
            compute_institutional_health,
        )
        health = compute_institutional_health()
        ecosystem_health_score = health.get("composite_score", 0)
        ecosystem_health_tier  = health.get("composite_tier", "UNKNOWN")
        domain_scores          = health.get("domain_scores", {})

        # Surface weak domains as top risks
        for domain, score in sorted(domain_scores.items(),
                                    key=lambda x: x[1]):
            if score < 60:
                top_risks.append(
                    f"{domain.upper().replace('_', ' ')} at risk: score={score}/100"
                )
            elif score < 80:
                top_risks.append(
                    f"{domain.upper().replace('_', ' ')} adequate but below target: {score}/100"
                )
        top_risks = top_risks[:5]  # cap at 5 executive risks

    except Exception as exc:
        top_risks.append(f"Health engine unavailable: {exc}")

    # ── Sub-module 2: Anomaly Cluster ─────────────────────────────────────────
    try:
        from core.operational_compression.anomaly_clustering_engine import cluster_anomalies
        anomaly_report = cluster_anomalies()
        total_anomalies = anomaly_report.get("total_anomalies", 0)
        overall_tier    = anomaly_report.get("overall_tier", "NONE")

        for cluster in anomaly_report.get("clusters", []):
            for a in cluster.get("anomalies", []):
                if a.get("severity") == "CRITICAL":
                    critical_anomalies.append(a)

        if overall_tier == "CRITICAL":
            top_risks.insert(0, f"CRITICAL anomaly cluster detected: {total_anomalies} anomalies")
        elif total_anomalies > 0:
            survivability_highlights.append(
                f"{total_anomalies} anomalies across {anomaly_report.get('cluster_count', 0)} domains"
            )

    except Exception as exc:
        survivability_highlights.append(f"Anomaly engine unavailable: {exc}")
        total_anomalies = 0
        overall_tier    = "UNKNOWN"

    # ── Sub-module 3: Signal Ecology ──────────────────────────────────────────
    try:
        from core.signal_ecology.signal_density_engine import signal_density_engine
        t = signal_density_engine.get_telemetry()
        sr = t.get("survival_rate", 0.0)
        if t.get("is_starvation"):
            alpha_condition = "STARVATION"
            top_risks.insert(0, f"Signal STARVATION — survival={sr:.0%}")
        elif t.get("is_drought"):
            alpha_condition = "DROUGHT"
            top_risks.append(f"Signal drought — survival={sr:.0%}")
        elif sr >= 0.30:
            alpha_condition = "HEALTHY"
            survivability_highlights.append(f"Signal survival healthy: {sr:.0%}")
        else:
            alpha_condition = "WEAK"
            survivability_highlights.append(f"Signal survival weak: {sr:.0%}")

    except Exception as exc:
        alpha_condition = "UNAVAILABLE"
        survivability_highlights.append(f"Signal ecology unavailable: {exc}")

    # ── Sub-module 4: Alpha Memory ─────────────────────────────────────────────
    try:
        from core.signal_ecology.alpha_context_memory import alpha_context_memory
        t = alpha_context_memory.get_telemetry()
        total   = t.get("total_contexts", 0)
        profit  = t.get("profitable_count", 0)
        toxic   = t.get("toxic_count", 0)

        if total == 0:
            survivability_highlights.append("Alpha context memory empty — no history")
        elif profit > toxic:
            survivability_highlights.append(
                f"Alpha positive: {profit} profitable vs {toxic} toxic contexts"
            )
        elif toxic > profit:
            top_risks.append(
                f"Toxic alpha concentration: {toxic} toxic > {profit} profitable contexts"
            )
    except Exception:
        pass

    # ── Sub-module 5: Governance ───────────────────────────────────────────────
    try:
        from core.operational_compression.governance_compression_layer import compress_governance
        gov = compress_governance()
        gov_score = gov.get("governance_health_score", 0)
        gov_tier  = gov.get("governance_health_tier", "UNKNOWN")
        governance_state = gov_tier

        if gov.get("human_intervention_required"):
            top_risks.insert(0, "HUMAN INTERVENTION REQUIRED (governance)")
        if gov.get("constitutional_violations_count", 0) > 0:
            top_risks.append(
                f"{gov['constitutional_violations_count']} constitutional violation(s)"
            )
        if gov.get("doctrinal_instability"):
            top_risks.append("Doctrinal instability detected")
        if gov_score >= 80:
            survivability_highlights.append(f"Governance healthy: {gov_score}/100")

    except Exception as exc:
        governance_state = "UNAVAILABLE"
        survivability_highlights.append(f"Governance engine unavailable: {exc}")
        gov_score = 0

    # ── Sub-module 6: Report Coverage ────────────────────────────────────────
    report_coverage: Dict[str, Any] = {}
    try:
        from core.dashboard_orchestrator import build_dashboard_structure
        dash = build_dashboard_structure({})
        total_r     = dash.get("total_reports", 0)
        populated_r = dash.get("populated_reports", 0)
        coverage    = dash.get("coverage_pct", 0.0)
        report_coverage = {
            "total":     total_r,
            "populated": populated_r,
            "coverage":  round(coverage, 1),
        }
        if coverage < 50.0:
            top_risks.append(f"Report coverage critically low: {coverage:.0f}%")
        elif coverage >= 80.0:
            survivability_highlights.append(f"Report ecosystem {coverage:.0f}% populated")
    except Exception as exc:
        report_coverage = {"error": str(exc)}

    # ── Executive summary lines (10 max) ─────────────────────────────────────
    summary_lines.append(
        f"ECOSYSTEM: {ecosystem_health_tier} ({ecosystem_health_score}/100)"
    )
    summary_lines.append(f"SIGNAL: {alpha_condition}")
    summary_lines.append(f"GOVERNANCE: {governance_state}")
    summary_lines.append(f"ANOMALIES: {total_anomalies} total | tier={overall_tier}")

    if top_risks:
        summary_lines.append(f"TOP RISK: {top_risks[0]}")
    if critical_anomalies:
        summary_lines.append(
            f"CRITICAL ANOMALIES: {len(critical_anomalies)} requiring attention"
        )
    if survivability_highlights:
        summary_lines.append(f"HIGHLIGHT: {survivability_highlights[0]}")

    coverage_pct = report_coverage.get("coverage", 0.0)
    summary_lines.append(
        f"COVERAGE: {report_coverage.get('populated', 0)}/{report_coverage.get('total', 0)} "
        f"reports ({coverage_pct}%)"
    )
    summary_lines.append("AUTHORITY: ASSESSMENT ONLY — no deployment/scaling/capital authority")

    return {
        "report":                  "EXECUTIVE_COMPRESSION_REPORT",
        "ecosystem_health_score":  ecosystem_health_score,
        "ecosystem_health_tier":   ecosystem_health_tier,
        "alpha_condition":         alpha_condition,
        "governance_state":        governance_state,
        "top_risks":               top_risks[:5],
        "top_risk_count":          min(5, len(top_risks)),
        "survivability_highlights": survivability_highlights[:5],
        "critical_anomalies":      critical_anomalies[:10],
        "critical_anomaly_count":  len(critical_anomalies),
        "total_anomaly_count":     total_anomalies,
        "anomaly_tier":            overall_tier,
        "report_coverage":         report_coverage,
        "summary_lines":           summary_lines,
        "auto_authorized":         False,
        "assessment_only":         True,
        "generated_ts":            int(_time.time() * 1000),
    }
