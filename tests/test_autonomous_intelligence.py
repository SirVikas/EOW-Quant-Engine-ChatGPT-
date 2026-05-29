"""
FTD-AIL-001: Test Suite for Autonomous Intelligence Layer.
Tests: Finding creation, lineage ID format, rule_based_analyzer,
evidence_scoring_engine, findings_store CRUD, approval_gate transitions,
archive_store file creation.
"""
import asyncio
import re
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Helpers ───────────────────────────────────────────────────────────────────

def async_run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


LINEAGE_RE = re.compile(r"^AIL-\d{17}-[0-9a-f]{16}$")


# ── Finding dataclass + lineage ID ────────────────────────────────────────────

def test_finding_creation_and_lineage():
    from core.autonomous_intelligence.analysis.finding_generator import generate_findings
    rule_hit = {
        "rule": "GENOME_STARVATION",
        "category": "GENOME",
        "severity": "MEDIUM",
        "title": "Test finding",
        "evidence": [{"activated": 100, "executed": 5}],
        "confidence_score": 0.85,
        "sample_size": 100,
        "economic_impact_est": "MEDIUM",
        "risk_level": "MEDIUM",
        "recommendation": "Test recommendation",
        "source_reports": ["Genome Exposure Audit"],
    }
    findings = generate_findings([rule_hit])
    assert len(findings) == 1
    f = findings[0]
    assert LINEAGE_RE.match(f.lineage_id), f"Bad lineage ID format: {f.lineage_id}"
    assert f.status == "PENDING"
    assert f.title == "Test finding"
    assert f.category == "GENOME"
    assert f.severity == "MEDIUM"
    assert f.approved_at is None
    assert f.rejected_at is None
    print(f"  ✓ Finding created: {f.lineage_id}")


def test_lineage_id_format():
    from core.autonomous_intelligence.analysis.finding_generator import _make_lineage_id
    lid = _make_lineage_id({"test": "data"})
    assert LINEAGE_RE.match(lid), f"Bad lineage_id: {lid}"
    print(f"  ✓ lineage_id format correct: {lid}")


# ── Rule-Based Analyzer ───────────────────────────────────────────────────────

def test_genome_starvation_rule():
    from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze
    snapshots = {
        "Genome Exposure Audit": {
            "activated": 200, "executed": 5, "execution_rate": 0.025
        }
    }
    hits = analyze(snapshots)
    rules = [h["rule"] for h in hits]
    assert "GENOME_STARVATION" in rules, f"Expected GENOME_STARVATION, got {rules}"
    print("  ✓ GENOME_STARVATION rule fires correctly")


def test_cost_drag_critical_rule():
    from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze
    snapshots = {
        "Recovery Cycle Audit": {
            "by_strategy": {
                "MeanReversion": {"cost_drag_pct": 75, "trade_count": 50}
            }
        }
    }
    hits = analyze(snapshots)
    rules = [h["rule"] for h in hits]
    assert "COST_DRAG_CRITICAL" in rules, f"Expected COST_DRAG_CRITICAL, got {rules}"
    print("  ✓ COST_DRAG_CRITICAL rule fires correctly")


def test_loss_run_excessive_rule():
    from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze
    snapshots = {
        "Performance Status": {
            "avg_win_run": 0.1, "avg_loss_run": 0.8, "total_trades": 100,
            "win_rate": 0.4, "peak_r_trades": 400,
        }
    }
    hits = analyze(snapshots)
    rules = [h["rule"] for h in hits]
    assert "LOSS_RUN_EXCESSIVE" in rules, f"Expected LOSS_RUN_EXCESSIVE, got {rules}"
    print("  ✓ LOSS_RUN_EXCESSIVE rule fires correctly")


def test_no_promotions_rule():
    from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze
    snapshots = {
        "Promotion Watch": {"total_promoted": 0, "total_cycles": 150, "total_trades": 150}
    }
    hits = analyze(snapshots)
    rules = [h["rule"] for h in hits]
    assert "NO_PROMOTIONS" in rules, f"Expected NO_PROMOTIONS, got {rules}"
    print("  ✓ NO_PROMOTIONS rule fires correctly")


def test_peak_r_insufficient_rule():
    from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze
    snapshots = {
        "Performance Status": {
            "avg_win_run": 0.1, "avg_loss_run": 0.2, "total_trades": 100,
            "win_rate": 0.55, "peak_r_trades": 50,
        }
    }
    hits = analyze(snapshots)
    rules = [h["rule"] for h in hits]
    assert "PEAK_R_INSUFFICIENT" in rules, f"Expected PEAK_R_INSUFFICIENT, got {rules}"
    print("  ✓ PEAK_R_INSUFFICIENT rule fires correctly")


def test_no_false_positives_on_healthy_data():
    from core.autonomous_intelligence.analysis.rule_based_analyzer import analyze
    snapshots = {
        "Genome Exposure Audit": {"activated": 100, "executed": 60, "execution_rate": 0.6},
        "Performance Status": {
            "avg_win_run": 0.5, "avg_loss_run": 1.0, "total_trades": 500,
            "win_rate": 0.6, "peak_r_trades": 500,
        },
        "Promotion Watch": {"total_promoted": 2, "total_cycles": 200, "total_trades": 200},
        "Breakeven Impact Audit": {"pct_wins_unprotected": 50, "total_wins": 300},
        "Recovery Cycle Audit": {
            "by_strategy": {"TrendFollowing": {"cost_drag_pct": 30, "trade_count": 100}},
            "boost_vs_normal_pnl_delta": 0.02,
        },
    }
    hits = analyze(snapshots)
    critical_rules = {h["rule"] for h in hits if h["severity"] in ("CRITICAL", "HIGH")}
    assert len(critical_rules) == 0, f"Unexpected HIGH/CRITICAL hits on healthy data: {critical_rules}"
    print("  ✓ No false positives on healthy data")


# ── Evidence Scoring Engine ───────────────────────────────────────────────────

def test_evidence_score_range():
    from core.autonomous_intelligence.analysis.finding_generator import generate_findings
    from core.autonomous_intelligence.governance.evidence_scoring_engine import score_finding

    rule_hit = {
        "rule": "COST_DRAG_CRITICAL",
        "category": "COST",
        "severity": "HIGH",
        "title": "Cost drag test",
        "evidence": [{"cost_drag_pct": 70}],
        "confidence_score": 0.9,
        "sample_size": 500,
        "economic_impact_est": "HIGH",
        "risk_level": "HIGH",
        "recommendation": "Test",
        "source_reports": ["Recovery Cycle Audit", "Performance Status"],
    }
    findings = generate_findings([rule_hit])
    score = score_finding(findings[0], collection_ts=time.time())
    assert 0 <= score <= 100, f"Score out of range: {score}"
    assert score > 50, f"Expected score > 50 for high-confidence finding, got {score}"
    print(f"  ✓ Evidence score in range: {score}/100")


def test_evidence_score_zero_sample():
    from core.autonomous_intelligence.analysis.finding_generator import generate_findings
    from core.autonomous_intelligence.governance.evidence_scoring_engine import score_finding

    rule_hit = {
        "rule": "TEST",
        "category": "SYSTEM",
        "severity": "INFO",
        "title": "Test",
        "evidence": [],
        "confidence_score": 0.0,
        "sample_size": 0,
        "economic_impact_est": "UNKNOWN",
        "risk_level": "LOW",
        "recommendation": "Test",
        "source_reports": [],
    }
    findings = generate_findings([rule_hit])
    score = score_finding(findings[0], collection_ts=time.time() - 30000)  # stale
    assert 0 <= score <= 100, f"Score out of range: {score}"
    print(f"  ✓ Zero-sample evidence score valid: {score}/100")


# ── Findings Store ────────────────────────────────────────────────────────────

def test_findings_store_save_load_update():
    import tempfile, os
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_findings.db"

        with patch("core.autonomous_intelligence.storage.findings_store._DB_PATH", db_path):
            from core.autonomous_intelligence.analysis.finding_generator import generate_findings
            from core.autonomous_intelligence.storage import findings_store

            rule_hit = {
                "rule": "GENOME_STARVATION",
                "category": "GENOME",
                "severity": "MEDIUM",
                "title": "Store test finding",
                "evidence": [{"activated": 50, "executed": 2}],
                "confidence_score": 0.8,
                "sample_size": 50,
                "economic_impact_est": "MEDIUM",
                "risk_level": "MEDIUM",
                "recommendation": "Test",
                "source_reports": ["Genome Exposure Audit"],
            }
            findings = generate_findings([rule_hit])
            f = findings[0]
            d = f.to_dict()
            d["evidence_score"] = 60

            async_run(findings_store.save_finding(d))

            loaded = async_run(findings_store.get_finding(f.lineage_id))
            assert loaded is not None
            assert loaded["lineage_id"] == f.lineage_id
            assert loaded["status"] == "PENDING"

            all_findings = async_run(findings_store.list_findings())
            assert any(x["lineage_id"] == f.lineage_id for x in all_findings)

            from datetime import datetime, timezone
            async_run(findings_store.update_status(
                f.lineage_id, "APPROVED",
                approved_at=datetime.now(timezone.utc).isoformat()
            ))
            updated = async_run(findings_store.get_finding(f.lineage_id))
            assert updated["status"] == "APPROVED"

    print("  ✓ Findings store: save/load/update cycle passed")


# ── Approval Gate ─────────────────────────────────────────────────────────────

def test_approval_gate_transitions():
    from core.autonomous_intelligence.governance.approval_gate import apply_decision

    finding = {"status": "PENDING"}

    apply_decision(finding, "NEEDS_MORE_EVIDENCE")
    assert finding["status"] == "NEEDS_MORE_EVIDENCE"

    apply_decision(finding, "APPROVED")
    assert finding["status"] == "APPROVED"
    assert finding.get("approved_at") is not None

    try:
        apply_decision(finding, "REJECTED")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("  ✓ Approval gate state transitions correct")


def test_approval_gate_reject():
    from core.autonomous_intelligence.governance.approval_gate import apply_decision

    finding = {"status": "PENDING"}
    apply_decision(finding, "REJECTED", reason="Not enough data")
    assert finding["status"] == "REJECTED"
    assert finding.get("rejected_at") is not None
    assert finding.get("rejection_reason") == "Not enough data"
    print("  ✓ Approval gate rejection with reason correct")


# ── Archive Store ─────────────────────────────────────────────────────────────

def test_archive_store_creates_file():
    from core.autonomous_intelligence.collector.snapshot_archiver import save_snapshot, _ARCHIVE_ROOT
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_root = Path(tmpdir) / "archive"
        with patch("core.autonomous_intelligence.collector.snapshot_archiver._ARCHIVE_ROOT", archive_root):
            data = {"test": "snapshot", "value": 42}
            lineage_id = save_snapshot("TestLabel", data)

        assert LINEAGE_RE.match(lineage_id), f"Bad lineage_id: {lineage_id}"
        # Verify file was created
        files = list(archive_root.rglob("*.json.gz"))
        assert len(files) == 1, f"Expected 1 archive file, got {len(files)}"

    print(f"  ✓ Archive store creates compressed file | lineage={lineage_id}")


# ── Run all tests ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_finding_creation_and_lineage,
        test_lineage_id_format,
        test_genome_starvation_rule,
        test_cost_drag_critical_rule,
        test_loss_run_excessive_rule,
        test_no_promotions_rule,
        test_peak_r_insufficient_rule,
        test_no_false_positives_on_healthy_data,
        test_evidence_score_range,
        test_evidence_score_zero_sample,
        test_findings_store_save_load_update,
        test_approval_gate_transitions,
        test_approval_gate_reject,
        test_archive_store_creates_file,
    ]

    passed = 0
    failed = 0
    for t in tests:
        name = t.__name__
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            import traceback; traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print(f"FTD-AIL-001 Test Suite: {passed} passed, {failed} failed")
    if failed:
        raise SystemExit(1)
