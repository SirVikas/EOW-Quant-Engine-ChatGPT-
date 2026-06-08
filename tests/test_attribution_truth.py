"""
FTD-NEXUS-100-PERCENT-001 Phase 3 — Attribution Truth Infrastructure Tests
"""
import pytest


def test_doae_record_snapshot_accumulation():
    from core.nexus.doae.doae_engine import doae
    initial = doae._conn.execute("SELECT COUNT(*) FROM trade_snapshots").fetchone()[0]
    snap_id = doae.record_snapshot(
        win_rate=0.55, profit_factor=1.3, avg_pnl=0.05, total_pnl=100.0, trades_count=100
    )
    after = doae._conn.execute("SELECT COUNT(*) FROM trade_snapshots").fetchone()[0]
    assert snap_id is not None
    assert after > initial


def test_doae_multiple_snapshots_accumulate():
    from core.nexus.doae.doae_engine import doae
    before = doae._conn.execute("SELECT COUNT(*) FROM trade_snapshots").fetchone()[0]
    doae.record_snapshot(win_rate=0.52, profit_factor=1.2, avg_pnl=0.03, total_pnl=80.0, trades_count=200)
    doae.record_snapshot(win_rate=0.58, profit_factor=1.4, avg_pnl=0.07, total_pnl=200.0, trades_count=300)
    after = doae._conn.execute("SELECT COUNT(*) FROM trade_snapshots").fetchone()[0]
    assert after >= before + 2


def test_doae_compute_attribution_from_raw():
    from core.nexus.doae.doae_engine import doae
    pre = {"win_rate": 0.50, "profit_factor": 1.2, "avg_pnl": 0.0, "total_pnl": 0.0, "trades_count": 50}
    post = {"win_rate": 0.58, "profit_factor": 1.5, "avg_pnl": 0.05, "total_pnl": 500.0, "trades_count": 150}
    result = doae.compute_attribution_from_raw("FTD-TEST-001", pre, post)
    assert "impact_score" in result
    assert result["impact_score"] > 0


def test_doae_confidence_scales_with_trades():
    from core.nexus.doae.doae_engine import doae
    pre = {"win_rate": 0.50, "profit_factor": 1.2, "avg_pnl": 0.0, "total_pnl": 0.0, "trades_count": 50}
    post_low = {"win_rate": 0.55, "profit_factor": 1.3, "avg_pnl": 0.03, "total_pnl": 50.0, "trades_count": 10}
    post_high = {"win_rate": 0.55, "profit_factor": 1.3, "avg_pnl": 0.03, "total_pnl": 50.0, "trades_count": 200}
    res_low = doae.compute_attribution_from_raw("FTD-CONF-LOW", pre, post_low)
    res_high = doae.compute_attribution_from_raw("FTD-CONF-HIGH", pre, post_high)
    assert res_low["confidence"] == "LOW"
    assert res_high["confidence"] == "HIGH"


def test_doae_generate_evidence_report_has_both_lists():
    from core.nexus.doae.doae_engine import doae
    report = doae.generate_evidence_report()
    assert "top_positive" in report
    assert "top_negative" in report
    assert "summary" in report
    assert report["summary"]["total_attributed"] > 0


def test_doae_snapshot_stats_accurate():
    from core.nexus.doae.doae_engine import doae
    count = doae._conn.execute("SELECT COUNT(*) FROM trade_snapshots").fetchone()[0]
    assert count >= 1


def test_doae_run_all_attributions_returns_list():
    from core.nexus.doae.doae_engine import doae
    result = doae.run_all_attributions()
    assert isinstance(result, list)


def test_doae_evidence_report_sorted_descending():
    from core.nexus.doae.doae_engine import doae
    report = doae.generate_evidence_report()
    top = report["top_positive"]
    if len(top) >= 2:
        assert top[0]["impact_score"] >= top[1]["impact_score"]
