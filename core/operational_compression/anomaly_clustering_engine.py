"""
PRP-PHASEC.3 — Anomaly Clustering Engine.

Prevents operator attention fragmentation by clustering isolated warnings
from all subsystems into operationally meaningful anomaly clusters.

Clusters: GOVERNANCE, ARCHIVE, RENDERING, SURVIVABILITY, ALPHA,
          PROPAGATION, ECOLOGICAL.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Any, Dict, List


_SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _sev_tier(cluster_anomalies: list) -> str:
    if not cluster_anomalies:
        return "NONE"
    ranks = [_SEVERITY_RANK.get(a.get("severity", "LOW"), 3) for a in cluster_anomalies]
    return ["CRITICAL", "HIGH", "MEDIUM", "LOW"][min(ranks)]


def _anomaly(severity: str, domain: str, description: str, source: str) -> dict:
    return {
        "severity":    severity,
        "domain":      domain,
        "description": description,
        "source":      source,
    }


def cluster_anomalies() -> dict:
    """
    PRP-PHASEC.3 — Collect and cluster anomalies from all institutional systems.

    Converts N isolated warnings into K semantic clusters (K << N).
    Never suppresses anomalies; never inflates severity.

    Returns a self-contained dict; never raises.
    """
    clusters: Dict[str, List[dict]] = {
        "GOVERNANCE":    [],
        "ARCHIVE":       [],
        "RENDERING":     [],
        "SURVIVABILITY": [],
        "ALPHA":         [],
        "PROPAGATION":   [],
        "ECOLOGICAL":    [],
    }

    # ── Source 1: Phase-B Wiring Audit ────────────────────────────────────────
    try:
        from core.cross_prp_audit.cross_prp_audit_orchestrator import run_full_wiring_audit
        audit = run_full_wiring_audit()
        domain_scores = audit.get("domain_scores", {})
        auditor_errors = audit.get("auditor_errors", [])
        domain_reports = audit.get("domain_reports", {})

        # Constitution → GOVERNANCE
        const_s = domain_scores.get("constitution_score", 100)
        if const_s < 100:
            sev = "CRITICAL" if const_s < 60 else ("HIGH" if const_s < 80 else "MEDIUM")
            clusters["GOVERNANCE"].append(
                _anomaly(sev, "GOVERNANCE",
                         f"Endpoint constitution degraded ({const_s}/100)",
                         "endpoint_constitution_auditor")
            )
            cr = domain_reports.get("constitution", {})
            for violation in cr.get("orphan_reports", []):
                clusters["GOVERNANCE"].append(
                    _anomaly("HIGH", "GOVERNANCE",
                             f"Orphan report (no endpoint): {violation}",
                             "endpoint_constitution_auditor")
                )
            for dup in cr.get("duplicate_endpoints", []):
                clusters["GOVERNANCE"].append(
                    _anomaly("MEDIUM", "GOVERNANCE",
                             f"Duplicate endpoint: {dup}",
                             "endpoint_constitution_auditor")
                )

        # Propagation → PROPAGATION
        prop_s = domain_scores.get("propagation_score", 100)
        pr = domain_reports.get("propagation", {})
        for ghost in pr.get("ghost_reports", []):
            clusters["PROPAGATION"].append(
                _anomaly("HIGH", "PROPAGATION",
                         f"Ghost report (not in dashboard): {ghost}",
                         "report_propagation_auditor")
            )
        for orphan in pr.get("orphan_bundle_keys", []):
            clusters["PROPAGATION"].append(
                _anomaly("MEDIUM", "PROPAGATION",
                         f"Orphan bundle key: {orphan}",
                         "report_propagation_auditor")
            )
        if prop_s < 80:
            clusters["PROPAGATION"].append(
                _anomaly("HIGH" if prop_s < 60 else "MEDIUM", "PROPAGATION",
                         f"Report propagation health: {prop_s}/100",
                         "report_propagation_auditor")
            )

        # Archive → ARCHIVE
        arch_s = domain_scores.get("archive_score", 100)
        ar = domain_reports.get("archive", {})
        for chk in ar.get("continuity_checks", []):
            if chk.get("status") == "FAIL":
                clusters["ARCHIVE"].append(
                    _anomaly("HIGH", "ARCHIVE",
                             f"Archive check failed: {chk.get('check')} — {chk.get('detail', '')}",
                             "archive_continuity_auditor")
                )
        if not ar.get("determinism_verified", True):
            clusters["ARCHIVE"].append(
                _anomaly("CRITICAL", "ARCHIVE",
                         "Archive non-determinism detected",
                         "archive_continuity_auditor")
            )
        if not ar.get("bundle_reproducible", True):
            clusters["ARCHIVE"].append(
                _anomaly("HIGH", "ARCHIVE",
                         "Bundle reproducibility check failed",
                         "archive_continuity_auditor")
            )

        # Rendering → RENDERING
        rend_s = domain_scores.get("rendering_score", 100)
        rr = domain_reports.get("rendering", {})
        for chk in rr.get("render_checks", []):
            if chk.get("status") == "FAIL":
                clusters["RENDERING"].append(
                    _anomaly("MEDIUM", "RENDERING",
                             f"Render check failed: {chk.get('check')} — {chk.get('detail', '')}",
                             "rendering_consistency_auditor")
                )
        if not rr.get("auto_authorized_enforced", True):
            clusters["RENDERING"].append(
                _anomaly("CRITICAL", "RENDERING",
                         "auto_authorized enforcement broken in rendering layer",
                         "rendering_consistency_auditor")
            )

        # Dependency failures → SURVIVABILITY
        dep_s = domain_scores.get("dependency_score", 100)
        dr = domain_reports.get("dependency", {})
        for failed_mod in dr.get("failed_modules", []):
            clusters["SURVIVABILITY"].append(
                _anomaly("HIGH", "SURVIVABILITY",
                         f"Module import failure: {failed_mod}",
                         "dependency_survivability_auditor")
            )

        # Auditor errors → GOVERNANCE
        for err in auditor_errors:
            clusters["GOVERNANCE"].append(
                _anomaly("HIGH", "GOVERNANCE",
                         f"Auditor error: {err}",
                         "cross_prp_audit_orchestrator")
            )

    except Exception as exc:
        clusters["GOVERNANCE"].append(
            _anomaly("CRITICAL", "GOVERNANCE",
                     f"Wiring audit unavailable: {exc}",
                     "cross_prp_audit_orchestrator")
        )

    # ── Source 2: Signal Ecology — Ecological + Survivability + Alpha ─────────
    try:
        from core.signal_ecology.signal_density_engine import signal_density_engine
        t = signal_density_engine.get_telemetry()
        if t.get("is_starvation"):
            clusters["SURVIVABILITY"].append(
                _anomaly("CRITICAL", "SURVIVABILITY",
                         f"Signal starvation active (drought={t.get('drought_seconds', 0):.0f}s)",
                         "signal_density_engine")
            )
        elif t.get("is_drought"):
            clusters["ECOLOGICAL"].append(
                _anomaly("HIGH", "ECOLOGICAL",
                         f"Signal drought detected (drought={t.get('drought_seconds', 0):.0f}s)",
                         "signal_density_engine")
            )
        sr = t.get("survival_rate", 1.0)
        if sr < 0.05:
            clusters["ECOLOGICAL"].append(
                _anomaly("HIGH", "ECOLOGICAL",
                         f"Signal survival rate critically low: {sr:.2%}",
                         "signal_density_engine")
            )
    except Exception as exc:
        clusters["ECOLOGICAL"].append(
            _anomaly("MEDIUM", "ECOLOGICAL",
                     f"signal_density_engine unavailable: {exc}",
                     "signal_density_engine")
        )

    try:
        from core.signal_ecology.alpha_context_memory import alpha_context_memory
        t = alpha_context_memory.get_telemetry()
        total = t.get("total_contexts", 0)
        toxic = t.get("toxic_count", 0)
        if total > 0 and toxic / total >= 0.50:
            clusters["ALPHA"].append(
                _anomaly("HIGH", "ALPHA",
                         f"Toxic context majority: {toxic}/{total} ({toxic/total:.0%})",
                         "alpha_context_memory")
            )
        if total == 0:
            clusters["ALPHA"].append(
                _anomaly("LOW", "ALPHA",
                         "Alpha context memory empty — no trade history",
                         "alpha_context_memory")
            )
    except Exception as exc:
        clusters["ALPHA"].append(
            _anomaly("LOW", "ALPHA", f"alpha_context_memory unavailable: {exc}",
                     "alpha_context_memory")
        )

    try:
        from core.signal_ecology.exploration_recovery import exploration_recovery_governor
        t = exploration_recovery_governor.get_telemetry()
        cb = t.get("consecutive_blocks", 0)
        if cb >= 200:
            clusters["ECOLOGICAL"].append(
                _anomaly("CRITICAL", "ECOLOGICAL",
                         f"Consecutive blocks at collapse threshold: {cb}",
                         "exploration_recovery_governor")
            )
        elif cb >= 100:
            clusters["ECOLOGICAL"].append(
                _anomaly("HIGH", "ECOLOGICAL",
                         f"Consecutive blocks elevated: {cb}",
                         "exploration_recovery_governor")
            )
    except Exception:
        pass

    # ── Compute cluster-level summaries ───────────────────────────────────────
    cluster_summaries: List[dict] = []
    total_anomalies: int = 0
    critical_count: int = 0

    for cluster_name, anomaly_list in clusters.items():
        total_anomalies += len(anomaly_list)
        critical_count  += sum(1 for a in anomaly_list if a.get("severity") == "CRITICAL")
        cluster_summaries.append({
            "cluster":        cluster_name,
            "anomaly_count":  len(anomaly_list),
            "severity_tier":  _sev_tier(anomaly_list),
            "anomalies":      anomaly_list,
        })

    # Sort clusters: most severe first
    cluster_summaries.sort(
        key=lambda c: (_SEVERITY_RANK.get(c["severity_tier"], 3), -c["anomaly_count"])
    )

    # Overall anomaly tier
    if critical_count > 0:
        overall_tier = "CRITICAL"
    elif total_anomalies > 10:
        overall_tier = "HIGH"
    elif total_anomalies > 3:
        overall_tier = "MODERATE"
    elif total_anomalies > 0:
        overall_tier = "LOW"
    else:
        overall_tier = "NONE"

    return {
        "report":           "ANOMALY_CLUSTER_REPORT",
        "total_anomalies":  total_anomalies,
        "critical_count":   critical_count,
        "overall_tier":     overall_tier,
        "cluster_count":    len(cluster_summaries),
        "clusters":         cluster_summaries,
        "auto_authorized":  False,
        "generated_ts":     int(_time.time() * 1000),
    }
