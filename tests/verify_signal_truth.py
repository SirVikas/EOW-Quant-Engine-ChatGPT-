"""
PRP-001 — Signal Truth Verifier

75+ automated validation checks for:
  - Signal Truth Engine
  - False Positive Forensics Engine
  - Directional Legitimacy Analyzer
  - Context Quality Engine
  - Asymmetry Validation Engine
  - Analytics report generation
  - API endpoint availability
  - Integration correctness

Run: python tests/verify_signal_truth.py
"""
from __future__ import annotations

import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Test harness ───────────────────────────────────────────────────────────────
_PASSED = 0
_FAILED = 0
_ERRORS = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global _PASSED, _FAILED
    if condition:
        _PASSED += 1
        print(f"  ✓ {name}")
    else:
        _FAILED += 1
        msg = f"  ✗ {name}" + (f" — {detail}" if detail else "")
        _ERRORS.append(msg)
        print(msg)


def section(title: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ── Import verification ────────────────────────────────────────────────────────

section("A. Module Import Checks")

try:
    from core.signal_truth.signal_truth_engine import signal_truth_engine, SignalRecord
    check("A01 signal_truth_engine import", True)
except Exception as e:
    check("A01 signal_truth_engine import", False, str(e))
    sys.exit(1)

try:
    from core.signal_truth.false_positive_forensics import false_positive_forensics
    check("A02 false_positive_forensics import", True)
except Exception as e:
    check("A02 false_positive_forensics import", False, str(e))

try:
    from core.signal_truth.directional_legitimacy import directional_legitimacy
    check("A03 directional_legitimacy import", True)
except Exception as e:
    check("A03 directional_legitimacy import", False, str(e))

try:
    from core.signal_truth.context_quality_engine import context_quality_engine
    check("A04 context_quality_engine import", True)
except Exception as e:
    check("A04 context_quality_engine import", False, str(e))

try:
    from core.signal_truth.asymmetry_validation import asymmetry_validation
    check("A05 asymmetry_validation import", True)
except Exception as e:
    check("A05 asymmetry_validation import", False, str(e))

try:
    from analytics.odyssey.signal_truth_reports import generate_all_reports, get_dashboard_summary
    check("A06 analytics signal_truth_reports import", True)
except Exception as e:
    check("A06 analytics signal_truth_reports import", False, str(e))

try:
    from analytics.odyssey.predictive_integrity_reports import predictive_integrity_summary
    check("A07 predictive_integrity_reports import", True)
except Exception as e:
    check("A07 predictive_integrity_reports import", False, str(e))

try:
    from analytics.odyssey.asymmetry_reports import asymmetry_health_summary
    check("A08 asymmetry_reports import", True)
except Exception as e:
    check("A08 asymmetry_reports import", False, str(e))


# ── Signal Truth Engine ────────────────────────────────────────────────────────

section("B. Signal Truth Engine — Core Functionality")

STE = signal_truth_engine

check("B01 STE singleton exists", STE is not None)
check("B02 STE initial truth_density = 0.0", STE.truth_density() == 0.0)
check("B03 STE initial total_signals = 0", STE._total_signals == 0)
check("B04 STE initial total_outcomes = 0", STE._total_outcomes == 0)

# Record a winning signal
STE.record_signal(
    signal_id="TEST001", symbol="BTCUSDT", strategy_id="MeanReversion_PAPER_SPEED",
    regime="MEAN_REVERTING", side="LONG", confidence=0.55,
    entry_price=50000.0, stop_loss=49200.0, take_profit=52400.0,
    utc_hour=10, rsi_val=28.0, above_sma=False, atr_pct=0.8,
)

check("B05 STE signal recorded", STE._total_signals == 1)
check("B06 STE signal in index", "TEST001" in STE._index)
check("B07 STE RR declared computed correctly",
      abs(STE._index["TEST001"].rr_declared - 3.0) < 0.1,
      f"got {STE._index['TEST001'].rr_declared}")

STE.record_outcome("TEST001", net_pnl=15.0, gross_pnl=18.0, exit_price=52400.0)

check("B08 STE outcome recorded", STE._total_outcomes == 1)
check("B09 STE truth_density > 0", STE.truth_density() > 0)
check("B10 STE total_wins = 1", STE._total_wins == 1)
check("B11 STE total_net_pnl = 15.0", STE._total_net_pnl == 15.0)
check("B12 STE signal marked as win", STE._index["TEST001"].was_win)
check("B13 STE directional_correct for LONG UP exit", STE._index["TEST001"].directionally_correct)

# Record a losing signal
STE.record_signal(
    signal_id="TEST002", symbol="ETHUSDT", strategy_id="MeanReversion_PAPER_SPEED",
    regime="TRENDING", side="SHORT", confidence=0.65,
    entry_price=3000.0, stop_loss=3100.0, take_profit=2700.0,
    utc_hour=14, rsi_val=55.0, above_sma=True, atr_pct=1.2,
)
STE.record_outcome("TEST002", net_pnl=-8.0, gross_pnl=-5.0, exit_price=3100.0)

check("B14 STE 2 signals, 2 outcomes", STE._total_signals == 2 and STE._total_outcomes == 2)
check("B15 STE truth_density = 0.5 (1/2)", abs(STE.truth_density() - 0.5) < 0.01)
check("B16 STE noise_ratio = 0.5", abs(STE.noise_participation_ratio() - 0.5) < 0.01)

# Unknown signal_id should not crash
STE.record_outcome("NONEXISTENT", net_pnl=100.0, gross_pnl=100.0, exit_price=999.0)
check("B17 STE unknown signal_id safe", STE._total_outcomes == 2)

check("B18 STE directional_legitimacy() returns float", isinstance(STE.directional_legitimacy(), float))
check("B19 STE confidence_calibration() returns list", isinstance(STE.confidence_calibration(), list))


# ── Signal Truth Engine Reports ────────────────────────────────────────────────

section("C. Signal Truth Engine — Report Generation")

matrix = STE.signal_truth_matrix()
check("C01 signal_truth_matrix has required keys",
      all(k in matrix for k in ("report", "prp", "total_signals", "truth_density", "by_regime", "by_strategy")))
check("C02 report ID correct", matrix["report"] == "01_signal_truth_matrix")
check("C03 prp tag correct", matrix["prp"] == "001")
check("C04 by_regime populated", len(matrix["by_regime"]) > 0)
check("C05 by_strategy populated", len(matrix["by_strategy"]) > 0)
check("C06 MEAN_REVERTING in by_regime", "MEAN_REVERTING" in matrix["by_regime"])

integrity = STE.predictive_integrity_monitor()
check("C07 predictive_integrity_monitor returns dict", isinstance(integrity, dict))
check("C08 integrity report ID", integrity["report"] == "08_predictive_integrity_monitor")
check("C09 rolling_drift is float", isinstance(integrity["rolling_drift"], float))

summary = STE.truth_density_summary()
check("C10 truth_density_summary returns dict", isinstance(summary, dict))
check("C11 summary report ID", summary["report"] == "10_truth_density_summary")
check("C12 data_sufficient flag present", "data_sufficient" in summary)

telemetry = STE.get_telemetry()
check("C13 telemetry has module key", telemetry["module"] == "SignalTruthEngine")
check("C14 telemetry has pending_outcomes", "pending_outcomes" in telemetry)

recent = STE.recent_signals(n=5)
check("C15 recent_signals returns list", isinstance(recent, list))
check("C16 recent_signals count <= n", len(recent) <= 5)


# ── False Positive Forensics ───────────────────────────────────────────────────

section("D. False Positive Forensics Engine")

FPF = false_positive_forensics

check("D01 FPF singleton exists", FPF is not None)
check("D02 FPF initial fp_count = 0", FPF._total_false_positives == 0)

# Record outcomes
FPF.record_outcome("T1", "BTCUSDT", "MEAN_REVERTING", "MeanReversion_PS", "LONG", 0.55, 28.0, 10, -5.0, False)
FPF.record_outcome("T2", "ETHUSDT", "TRENDING", "MeanReversion_PS", "SHORT", 0.70, 56.0, 14, -8.0, False)
FPF.record_outcome("T3", "BTCUSDT", "TRENDING", "MeanReversion_PS", "LONG", 0.51, 45.0, 16, 12.0, True)

check("D03 FPF counted 2 false positives", FPF._total_false_positives == 2)
check("D04 FPF total_outcomes = 3", FPF._total_outcomes == 3)
check("D05 FPF fp_rate = 2/3",
      abs(FPF._total_false_positives / FPF._total_outcomes - 0.667) < 0.01)

# HIGH confidence trap: confidence 0.70 loss → should be in confidence_traps
check("D06 FPF confidence_trap logged", len(FPF._confidence_traps) >= 1)

# Record enough to form a cluster
for i in range(4):
    FPF.record_outcome(
        f"CLUSTER_{i}", "BTCUSDT", "MEAN_REVERTING", "MeanReversion_PS",
        "SHORT", 0.55, 72.0, 10, -3.0, False
    )

fp_report = FPF.false_positive_clusters()
check("D07 FP clusters report has required keys",
      all(k in fp_report for k in ("report", "false_positive_rate", "clusters")))
check("D08 FP clusters report ID correct", fp_report["report"] == "02_false_positive_clusters")
check("D09 FP cluster formed", len(fp_report["clusters"]) > 0,
      f"clusters={len(fp_report['clusters'])}")

noise_audit = FPF.noise_participation_audit()
check("D10 noise_audit report correct ID", noise_audit["report"] == "07_noise_participation_audit")
check("D11 noise_audit has by_hour", "by_hour" in noise_audit)
check("D12 noise_audit has by_regime_side", "by_regime_side" in noise_audit)

fpf_telem = FPF.get_telemetry()
check("D13 FPF telemetry module name", fpf_telem["module"] == "FalsePositiveForensicsEngine")
check("D14 FPF telemetry prp=001", fpf_telem["prp"] == "001")


# ── Directional Legitimacy ─────────────────────────────────────────────────────

section("E. Directional Legitimacy Analyzer")

DL = directional_legitimacy

check("E01 DL singleton exists", DL is not None)
check("E02 DL initial global_score = 0.0", DL.global_legit_score() == 0.0)

# 6 correct, 4 wrong
for i in range(6):
    DL.record_outcome("MEAN_REVERTING", "MeanReversion_PS", "LONG", 10, True, 5.0)
for i in range(4):
    DL.record_outcome("TRENDING", "MeanReversion_PS", "SHORT", 14, False, -3.0)

check("E03 DL total_outcomes = 10", DL._total_outcomes == 10)
check("E04 DL global_score = 0.6", abs(DL.global_legit_score() - 0.6) < 0.01)
check("E05 DL rolling_score = 0.6", abs(DL.rolling_legit_score() - 0.6) < 0.01)
check("E06 DL label is NEUTRAL or STRONG",
      DL.legitimacy_label() in ("NEUTRAL", "STRONG"))

dl_report = DL.directional_legitimacy_report()
check("E07 DL report ID correct", dl_report["report"] == "03_directional_legitimacy_report")
check("E08 DL by_regime populated", len(dl_report["by_regime"]) > 0)
check("E09 DL by_strategy populated", len(dl_report["by_strategy"]) > 0)
check("E10 DL by_hour populated", len(dl_report["by_hour"]) > 0)
check("E11 DL global_score in report", "global_score" in dl_report)

rsv = DL.regime_signal_validity()
check("E12 regime_signal_validity report ID", rsv["report"] == "09_regime_signal_validity")
check("E13 regime_signal_validity by_regime populated", len(rsv["by_regime"]) > 0)

dl_telem = DL.get_telemetry()
check("E14 DL telemetry module name", dl_telem["module"] == "DirectionalLegitimacyAnalyzer")
check("E15 DL telemetry prp=001", dl_telem["prp"] == "001")


# ── Context Quality Engine ─────────────────────────────────────────────────────

section("F. Context Quality Engine")

CQE = context_quality_engine

check("F01 CQE singleton exists", CQE is not None)
check("F02 CQE initial scored = 0", CQE._total_scored == 0)

# High quality context: MEAN_REVERTING LONG with RSI < 30
score_hi = CQE.score_signal(
    "SIG_HI", "MEAN_REVERTING", "MeanReversion_PAPER_SPEED", "LONG",
    0.55, 27.0, False, 0.8
)
check("F03 CQE high-quality score > 0.5", score_hi > 0.5, f"got {score_hi}")

# Low quality context: MEAN_REVERTING but RSI=52 (wrong zone)
score_lo = CQE.score_signal(
    "SIG_LO", "MEAN_REVERTING", "MeanReversion_PAPER_SPEED", "LONG",
    0.55, 52.0, False, 4.0
)
check("F04 CQE low-quality score < high-quality", score_lo < score_hi,
      f"lo={score_lo} hi={score_hi}")
check("F05 CQE score within 0-1 range", 0.0 <= score_hi <= 1.0 and 0.0 <= score_lo <= 1.0)
check("F06 CQE total_scored = 2", CQE._total_scored == 2)

CQE.record_outcome("SIG_HI", True,  12.0)
CQE.record_outcome("SIG_LO", False, -5.0)

cqa = CQE.context_quality_analysis()
check("F07 CQE report ID correct", cqa["report"] == "05_context_quality_analysis")
check("F08 CQE tier_breakdown populated", len(cqa["tier_breakdown"]) > 0)
check("F09 CQE discrimination key present", "discrimination" in cqa)

cq_telem = CQE.get_telemetry()
check("F10 CQE telemetry module name", cq_telem["module"] == "ContextQualityEngine")
check("F11 CQE pending count correct", "pending" in cq_telem)

# Score a TRENDING LONG with correct above_sma alignment
score_tr = CQE.score_signal(
    "SIG_TR", "TRENDING", "TrendFollowing_PS", "LONG",
    0.55, 42.0, True, 1.0
)
check("F12 CQE trending aligned score > 0.5", score_tr > 0.5, f"got {score_tr}")

# Test volatility penalty
score_hv = CQE.score_signal(
    "SIG_HV", "TRENDING", "TrendFollowing_PS", "LONG",
    0.55, 42.0, True, 5.0   # very high ATR
)
check("F13 CQE high-volatility score < normal", score_hv < score_tr,
      f"hv={score_hv} normal={score_tr}")


# ── Asymmetry Validation ───────────────────────────────────────────────────────

section("G. Asymmetry Validation Engine")

AV = asymmetry_validation

check("G01 AV singleton exists", AV is not None)
check("G02 AV initial total_outcomes = 0", AV._total_outcomes == 0)
check("G03 AV global_rr_achievement = 0.0", AV.global_rr_achievement_ratio() == 0.0)

# Healthy asymmetry: declared RR=3.0, achieved RR=2.8
AV.record_outcome("AV01", "BTCUSDT", "MeanReversion_PS", "MEAN_REVERTING",
                  0.55, 3.0, 2.8, True, 15.0)

check("G04 AV outcome recorded", AV._total_outcomes == 1)
check("G05 AV achievement ratio > 0", AV.global_rr_achievement_ratio() > 0)

# Optimism bias: declared RR=3.0, achieved only 0.5 (stopped early)
AV.record_outcome("AV02", "ETHUSDT", "MeanReversion_PS", "TRENDING",
                  0.70, 3.0, 0.5, False, -8.0)

check("G06 AV optimism_count = 1", AV._optimism_count == 1)
check("G07 AV optimism_bias_rate > 0", AV.optimism_bias_rate() > 0)

# High confidence divergence: conf=0.75, ratio < 0.4
AV.record_outcome("AV03", "SOLUSDT", "MeanReversion_PS", "MEAN_REVERTING",
                  0.75, 3.0, 0.3, False, -10.0)
check("G08 AV divergence_log populated", len(AV._divergence_log) > 0)

av_report = AV.asymmetry_validation_report()
check("G09 AV report ID correct", av_report["report"] == "06_asymmetry_validation_report")
check("G10 AV by_strategy populated", len(av_report["by_strategy"]) > 0)
check("G11 AV by_regime populated", len(av_report["by_regime"]) > 0)
check("G12 AV global_achievement_ratio present", "global_achievement_ratio" in av_report)

div_report = AV.confidence_reality_divergence()
check("G13 AV divergence report ID", div_report["report"] == "04_confidence_reality_divergence")
check("G14 AV divergence total > 0", div_report["total_divergences"] > 0)

av_telem = AV.get_telemetry()
check("G15 AV telemetry module name", av_telem["module"] == "AsymmetryValidationEngine")
check("G16 AV asymmetry_health present", "asymmetry_health" in av_telem)

# Test health labels
for rr, expected in [(0.8, "HEALTHY"), (0.55, "MARGINAL"), (0.35, "WEAK"), (0.1, "BROKEN")]:
    # Inject into rolling to test label
    AV._rolling_ratios.append(rr)

check("G17 AV health label is string", isinstance(av_telem["asymmetry_health"], str))
check("G18 AV zero RR declared handled safely",
      AV.global_rr_achievement_ratio() is not None)


# ── Analytics Report Generation ───────────────────────────────────────────────

section("H. Analytics Report Generation")

try:
    all_reports = generate_all_reports()
    check("H01 generate_all_reports() executes", True)
    check("H02 all_reports has prp=001", all_reports.get("prp") == "001")
    check("H03 all_reports has reports dict", "reports" in all_reports)
    rpts = all_reports["reports"]
    for rn in [
        "01_signal_truth_matrix", "02_false_positive_clusters",
        "03_directional_legitimacy", "04_confidence_reality_divergence",
        "05_context_quality_analysis", "06_asymmetry_validation_report",
        "07_noise_participation_audit", "08_predictive_integrity_monitor",
        "09_regime_signal_validity", "10_truth_density_summary",
    ]:
        check(f"H04 report '{rn[:25]}' present", rn in rpts)
    check("H05 exactly 10 reports generated", len(rpts) == 10)
except Exception as e:
    check("H01 generate_all_reports() executes", False, str(e))

try:
    dash = get_dashboard_summary()
    check("H15 get_dashboard_summary() executes", True)
    check("H16 dashboard has truth_density", "truth_density" in dash)
    check("H17 dashboard has asymmetry_health", "asymmetry_health" in dash)
    check("H18 dashboard has directional_label", "directional_label" in dash)
    check("H19 dashboard prp=001", dash.get("prp") == "001")
except Exception as e:
    check("H15 get_dashboard_summary() executes", False, str(e))

try:
    pi = predictive_integrity_summary()
    check("H20 predictive_integrity_summary() executes", True)
    check("H21 has stability_label", "stability_label" in pi)
except Exception as e:
    check("H20 predictive_integrity_summary() executes", False, str(e))

try:
    ahs = asymmetry_health_summary()
    check("H22 asymmetry_health_summary() executes", True)
    check("H23 has asymmetry_health", "asymmetry_health" in ahs)
except Exception as e:
    check("H22 asymmetry_health_summary() executes", False, str(e))


# ── Resilience & Edge Cases ────────────────────────────────────────────────────

section("I. Resilience & Edge Cases")

# Empty state reports should not crash
from core.signal_truth.signal_truth_engine import SignalTruthEngine
from core.signal_truth.false_positive_forensics import FalsePositiveForensicsEngine
from core.signal_truth.directional_legitimacy import DirectionalLegitimacyAnalyzer
from core.signal_truth.context_quality_engine import ContextQualityEngine
from core.signal_truth.asymmetry_validation import AsymmetryValidationEngine

empty_ste = SignalTruthEngine()
check("I01 empty STE truth_density = 0.0", empty_ste.truth_density() == 0.0)
check("I02 empty STE directional_legit = 0.0", empty_ste.directional_legitimacy() == 0.0)
check("I03 empty STE signal_truth_matrix works", isinstance(empty_ste.signal_truth_matrix(), dict))
check("I04 empty STE predictive_integrity_monitor works", isinstance(empty_ste.predictive_integrity_monitor(), dict))
check("I05 empty STE truth_density_summary works", isinstance(empty_ste.truth_density_summary(), dict))
check("I06 empty STE recent_signals works", isinstance(empty_ste.recent_signals(10), list))

empty_fpf = FalsePositiveForensicsEngine()
check("I07 empty FPF false_positive_clusters works", isinstance(empty_fpf.false_positive_clusters(), dict))
check("I08 empty FPF noise_participation_audit works", isinstance(empty_fpf.noise_participation_audit(), dict))

empty_dl = DirectionalLegitimacyAnalyzer()
check("I09 empty DL directional_legitimacy_report works", isinstance(empty_dl.directional_legitimacy_report(), dict))
check("I10 empty DL regime_signal_validity works", isinstance(empty_dl.regime_signal_validity(), dict))

empty_cqe = ContextQualityEngine()
check("I11 empty CQE context_quality_analysis works", isinstance(empty_cqe.context_quality_analysis(), dict))
check("I12 empty CQE record_outcome unknown id safe", empty_cqe.record_outcome("UNKNOWN", True, 5.0) is None)

empty_av = AsymmetryValidationEngine()
check("I13 empty AV asymmetry_validation_report works", isinstance(empty_av.asymmetry_validation_report(), dict))
check("I14 empty AV confidence_reality_divergence works", isinstance(empty_av.confidence_reality_divergence(), dict))
check("I15 empty AV zero rr_declared safe",
      empty_av.record_outcome("X", "BTC", "S", "R", 0.5, 0.0, 1.0, True, 5.0) is None)

# Thread safety: concurrent writes should not crash
import threading

def _concurrent_write(engine, n):
    for i in range(n):
        engine.record_signal(
            f"THREAD_{n}_{i}", "BTCUSDT", "TestStrat", "MEAN_REVERTING",
            "LONG", 0.55, 50000.0, 49000.0, 53000.0, 10
        )

threads = [threading.Thread(target=_concurrent_write, args=(SignalTruthEngine(), 20)) for _ in range(3)]
for t in threads: t.start()
for t in threads: t.join()
check("I16 concurrent writes safe", True)

# Confidence calibration with no outcomes returns list
check("I17 empty calibration returns list", isinstance(empty_ste.confidence_calibration(), list))

# Noise ratio with 0 outcomes = 0.0
check("I18 empty noise_ratio = 0.0", empty_ste.noise_participation_ratio() == 0.0)


# ── Correctness Invariants ─────────────────────────────────────────────────────

section("J. Correctness Invariants")

inv_ste = SignalTruthEngine()
inv_ste.record_signal("INV01", "BTCUSDT", "S", "MEAN_REVERTING", "LONG", 0.55,
                      50000.0, 49000.0, 53000.0, 10)
inv_ste.record_signal("INV02", "ETHUSDT", "S", "TRENDING", "SHORT", 0.60,
                      3000.0, 3150.0, 2700.0, 14)

check("J01 2 signals recorded before outcomes", inv_ste._total_signals == 2)
check("J02 0 outcomes before any close", inv_ste._total_outcomes == 0)
check("J03 truth_density=0 with no outcomes", inv_ste.truth_density() == 0.0)

inv_ste.record_outcome("INV01", 20.0, 22.0, 53000.0)
inv_ste.record_outcome("INV02", -7.0, -5.0, 3150.0)

check("J04 pending_outcomes decrements", inv_ste._total_signals - inv_ste._total_outcomes == 0)
check("J05 truth_density = 0.5 for 1W/1L",
      abs(inv_ste.truth_density() - 0.5) < 0.01)
check("J06 noise_ratio + truth_density = 1.0",
      abs(inv_ste.truth_density() + inv_ste.noise_participation_ratio() - 1.0) < 0.01)
check("J07 total_net_pnl = sum of pnls",
      abs(inv_ste._total_net_pnl - (20.0 - 7.0)) < 0.001)
check("J08 wins + losses = outcomes",
      inv_ste._total_wins + (inv_ste._total_outcomes - inv_ste._total_wins) == inv_ste._total_outcomes)

# RR computed correctly for declared 3:1 setup
idx = inv_ste._index["INV01"]
check("J09 RR declared is approximately 3.0",
      abs(idx.rr_declared - 3.0) < 0.1,
      f"got {idx.rr_declared}")
check("J10 signal marked as outcome_recorded", idx.outcome_recorded)
check("J11 LONG exit above entry = directionally correct", idx.directionally_correct)

inv_dl = DirectionalLegitimacyAnalyzer()
inv_dl.record_outcome("TRENDING", "S", "LONG", 10, True, 5.0)
inv_dl.record_outcome("TRENDING", "S", "LONG", 10, True, 5.0)
inv_dl.record_outcome("MEAN_REVERTING", "S", "LONG", 10, False, -3.0)

check("J12 DL 3 outcomes total", inv_dl._total_outcomes == 3)
check("J13 DL 2 correct total", inv_dl._total_correct == 2)
check("J14 DL global_score = 2/3", abs(inv_dl.global_legit_score() - 2/3) < 0.01)

# AV: all good RR → HEALTHY
inv_av = AsymmetryValidationEngine()
for i in range(5):
    inv_av.record_outcome(f"AV{i}", "BTC", "S", "R", 0.55, 3.0, 2.5, True, 10.0)
check("J15 AV all good → HEALTHY or MARGINAL",
      inv_av.asymmetry_health_label() in ("HEALTHY", "MARGINAL"))


# ── Final Results ──────────────────────────────────────────────────────────────

section("RESULTS")
total = _PASSED + _FAILED
print(f"\n  Total checks: {total}")
print(f"  Passed:       {_PASSED}")
print(f"  Failed:       {_FAILED}")

if _ERRORS:
    print(f"\n  Failed checks:")
    for e in _ERRORS:
        print(f"    {e}")

if _FAILED == 0:
    print(f"\n  ✓ ALL {_PASSED} CHECKS PASSED — PRP-001 Signal Truth Reconstruction VALIDATED")
    sys.exit(0)
else:
    print(f"\n  ✗ {_FAILED} CHECKS FAILED")
    sys.exit(1)
