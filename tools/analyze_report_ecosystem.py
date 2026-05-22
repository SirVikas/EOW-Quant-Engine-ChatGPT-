"""
FTD-RTAG — Constitutional Report Taxonomy Alignment
& Report Ecosystem Governance CLI

Analyses the PHOENIX report registry and produces an institutional
report ecosystem governance assessment — no live engine required:

  1. Ecosystem health score (0–100)
  2. Registry health (schema violations, families, critical reports)
  3. Dependency graph health (cycle detection, dangling refs, topo order)
  4. Bundle coverage (orphaned reports, bundle compositions)
  5. Overlap risk (high-overlap reports, canonical metric violations)
  6. Metadata compliance (schema field coverage)
  7. Archive survivability (high-priority report count)
  8. Research-only recommendations (all auto_authorized=False)
  9. Hard constitutional reporting principles

IMPORTANT: All output is research-only. No production state is modified.
For live diagnostics use GET /api/learning-intelligence/report-ecosystem-governance

Usage:
    python tools/analyze_report_ecosystem.py
    python tools/analyze_report_ecosystem.py --json
    python tools/analyze_report_ecosystem.py --verbose
    python tools/analyze_report_ecosystem.py --families
    python tools/analyze_report_ecosystem.py --bundles
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE         = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
sys.path.insert(0, str(_PROJECT_ROOT))


# ── Formatters ────────────────────────────────────────────────────────────────

def _health_badge(tier: str) -> str:
    return {
        "HEALTHY":    "[ HEALTHY    ]",
        "ADEQUATE":   "[ ADEQUATE   ]",
        "VULNERABLE": "[!VULNERABLE ]",
        "CRITICAL":   "[!!CRITICAL  ]",
    }.get(tier, f"[{tier[:10]:^10}]")


def _overlap_badge(tier: str) -> str:
    return {
        "LOW":      "[LOW  ]",
        "MODERATE": "[MOD  ]",
        "HIGH":     "[HIGH ]",
    }.get(tier, f"[{tier[:5]:^5}]")


def _surv_badge(tier: str) -> str:
    return {
        "STRONG":   "[STRNG]",
        "ADEQUATE": "[ADEQ ]",
        "WEAK":     "[WEAK ]",
    }.get(tier, f"[{tier[:5]:^5}]")


def _bool_flag(v: bool) -> str:
    return "YES" if v else "no"


def _prio_badge(p: str) -> str:
    return {
        "CRITICAL": "[CRIT]", "HIGH": "[HIGH]",
        "MEDIUM":   "[MED ]", "LOW":  "[LOW ]",
    }.get(p, f"[{p[:4]:^4}]")


# ── Report printer ────────────────────────────────────────────────────────────

def _print_report(result: dict, verbose: bool = False,
                  show_families: bool = False, show_bundles: bool = False) -> None:
    W = 88
    print(f"\n{'='*W}")
    print("  FTD-RTAG — Constitutional Report Taxonomy Alignment")
    print("             & Report Ecosystem Governance")
    print(f"{'='*W}")

    if "error" in result:
        print(f"\n  ERROR: {result['error']}")
        print(f"\n{'='*W}\n")
        return

    total   = result.get("total_reports_registered", 0)
    score   = result.get("ecosystem_health_score", 0.0)
    tier    = result.get("ecosystem_health_tier", "?")

    print(f"\n  ── Ecosystem Status ──")
    print(f"  Health score:           {score:.1f}/100  {_health_badge(tier)}")
    print(f"  Reports registered:     {total}")

    # ── Registry Health ───────────────────────────────────────────────────────
    rh = result.get("registry_health", {})
    print(f"\n  ── Registry Health ──")
    print(f"  Total reports:          {rh.get('total_reports', 0)}")
    print(f"  Schema violations:      {rh.get('violations_count', 0)}"
          f"{'  ← CRITICAL' if rh.get('violations_count', 0) > 0 else ''}")
    print(f"  Families represented:   {rh.get('family_count', 0)}"
          f"  {rh.get('families_represented', [])}")
    print(f"  Critical-priority reports: {rh.get('critical_count', 0)}"
          f"  {rh.get('critical_reports', [])}")
    print(f"  Registry healthy:       {_bool_flag(rh.get('registry_healthy', False))}")

    if verbose and rh.get("schema_violations"):
        print(f"\n  Schema violations:")
        for v in rh["schema_violations"]:
            print(f"    ! {v}")

    # ── Dependency Graph Health ───────────────────────────────────────────────
    dh = result.get("dependency_health", {})
    print(f"\n  ── Dependency Graph Health ──")
    print(f"  Cycle-free:             {_bool_flag(dh.get('cycle_free', False))}")
    print(f"  Dangling refs:          {dh.get('dangling_count', 0)}")
    print(f"  Primitive reports:      {dh.get('primitive_count', 0)}"
          f"  {dh.get('primitive_reports', [])}")
    print(f"  Topological order:      {dh.get('topological_count', 0)} reports ordered")
    print(f"  Graph healthy:          {_bool_flag(dh.get('graph_healthy', False))}")
    if verbose:
        print(f"  Order: {dh.get('topological_order', [])}")

    # ── Bundle Coverage ───────────────────────────────────────────────────────
    bc = result.get("bundle_coverage", {})
    print(f"\n  ── Bundle Coverage ──")
    print(f"  Orphaned reports:       {bc.get('orphaned_count', 0)}"
          f"  {bc.get('orphaned_reports', [])}")
    print(f"  Coverage healthy:       {_bool_flag(bc.get('coverage_healthy', False))}")
    if bc.get("bundle_summary"):
        print(f"  {'Bundle':<25} {'Count':>6}")
        print(f"  {'-'*35}")
        for bname, cnt in bc["bundle_summary"].items():
            print(f"  {bname:<25} {cnt:>6}")

    # ── Overlap Risk ──────────────────────────────────────────────────────────
    ov = result.get("overlap_risk", {})
    print(f"\n  ── Overlap Risk ──")
    print(f"  Risk tier:              {_overlap_badge(ov.get('overlap_risk_tier','?'))}  {ov.get('overlap_risk_tier','?')}")
    print(f"  Total overlap decl.:    {ov.get('total_overlap_declarations', 0)}")
    print(f"  High-overlap reports:   {ov.get('high_overlap_count', 0)}"
          f"  {ov.get('high_overlap_reports', [])}")

    # ── Archive Survivability ─────────────────────────────────────────────────
    ar = result.get("archive_survivability", {})
    print(f"\n  ── Archive Survivability ──")
    print(f"  Survivability:          {_surv_badge(ar.get('survivability_tier','?'))}")
    print(f"  High-priority reports:  {ar.get('high_priority_count', 0)}")
    if verbose:
        print(f"  Reports: {ar.get('high_priority_reports', [])}")

    # ── Metadata Compliance ───────────────────────────────────────────────────
    mc = result.get("metadata_compliance", {})
    print(f"\n  ── Metadata Compliance ──")
    print(f"  Schema version:         {mc.get('schema_version', '?')}")
    print(f"  Required fields:        {mc.get('required_field_count', 0)}")
    print(f"  Compliance schema:      {'defined' if mc.get('compliance_schema_defined') else 'missing'}")

    # ── Family breakdown ──────────────────────────────────────────────────────
    if show_families:
        cov = result.get("coverage_summary", {})
        print(f"\n  ── Family Breakdown ──")
        for fam, cnt in cov.get("family_breakdown", {}).items():
            print(f"  {fam:<22} {cnt:>3} report(s)")

    # ── Bundle compositions ───────────────────────────────────────────────────
    if show_bundles:
        bc_full = result.get("bundle_compositions", {})
        print(f"\n  ── Bundle Compositions ──")
        for bname, comp in bc_full.items():
            print(f"  {bname:<25} {comp['report_count']:>3} reports  "
                  f"crit={comp['critical_count']}  families={comp['families']}")

    # ── Recommendations ───────────────────────────────────────────────────────
    recs = result.get("recommendations", [])
    print(f"\n  ── Recommendations ({len(recs)}) ──")
    for rec in recs:
        badge = _prio_badge(rec.get("priority", "?"))
        print(f"  {badge} [{rec.get('type', '?')}]")
        print(f"    {rec.get('summary', '')}")
        print(f"    Action: {rec.get('action_required','?')}  |  "
              f"Auto-authorized: {rec.get('auto_authorized','?')}")

    # ── Audit Entry ───────────────────────────────────────────────────────────
    ae = result.get("audit_entry", {})
    if ae:
        print(f"\n  ── Audit Entry ──")
        print(f"  Entry ID:              {ae.get('entry_id', '—')}")
        print(f"  Auto-authorized:       {'!!! YES' if ae.get('auto_authorized') else 'no (constitutional)'}")
        print(f"  Immutable:             {_bool_flag(ae.get('immutable', False))}")

    # ── Hard Constitutional Principles ────────────────────────────────────────
    if verbose:
        hp = result.get("reporting_hard_principles", {})
        print(f"\n  ── Hard Constitutional Reporting Principles ──")
        for principle, value in hp.items():
            print(f"  {principle:<50} {'YES' if value else 'no'}")

    print(f"\n{'='*W}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report ecosystem governance — FTD-RTAG constitutional taxonomy assessment"
    )
    parser.add_argument("--json",     action="store_true", dest="emit_json",
                        help="Emit raw JSON output")
    parser.add_argument("--verbose",  action="store_true",
                        help="Show schema violations, topo order, high-priority reports")
    parser.add_argument("--families", action="store_true",
                        help="Show per-family breakdown table")
    parser.add_argument("--bundles",  action="store_true",
                        help="Show bundle composition table")
    args = parser.parse_args()

    from core.export_bundle_manager import compute_report_ecosystem_governance
    result = compute_report_ecosystem_governance()

    if args.emit_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(
            result,
            verbose=args.verbose,
            show_families=args.families,
            show_bundles=args.bundles,
        )


if __name__ == "__main__":
    main()
