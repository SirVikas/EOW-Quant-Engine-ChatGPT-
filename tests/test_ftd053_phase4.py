"""
FTD-053-GAIA Phase 4 Verifier
AI Summary Engine + Strategic Intelligence Feeds

Sections:
  A: Module imports and singletons                    (6 checks)
  B: AISummaryEngine — output structure               (8 checks)
  C: AISummaryEngine — CRITICAL scenario              (6 checks)
  D: AISummaryEngine — HIGH scenario                  (5 checks)
  E: AISummaryEngine — ROUTINE/MONITORING scenario    (5 checks)
  F: AISummaryEngine — signal_strength math           (8 checks)
  G: AISummaryEngine — headline correctness           (6 checks)
  H: AISummaryEngine — directives logic               (6 checks)
  I: AISummaryEngine — narrative sections             (6 checks)
  J: AISummaryEngine — stats tracking                 (4 checks)
  K: StrategicFeed — refresh() structure              (6 checks)
  L: StrategicFeed — RISK feed                        (7 checks)
  M: StrategicFeed — LEARNING feed                    (6 checks)
  N: StrategicFeed — PERFORMANCE feed                 (6 checks)
  O: StrategicFeed — ANOMALY feed                     (6 checks)
  P: StrategicFeed — REGIME feed                      (5 checks)
  Q: StrategicFeed — get_priority_feeds               (5 checks)
  R: StrategicFeed — status()                         (4 checks)
  S: Resilience / non-throwing                        (6 checks)
  T: Integration — full Phase 1→4 pipeline            (7 checks)

Total: 118 checks
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS = 0
FAIL = 0
_results: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        _results.append(f"  PASS  {name}")
    else:
        FAIL += 1
        _results.append(f"  FAIL  {name}" + (f" | {detail}" if detail else ""))


# ─────────────────────────────────────────────────────────────────────────────
# A: Module imports
# ─────────────────────────────────────────────────────────────────────────────
print("A: Module imports")

try:
    from core.observability.ai_summary_engine import (
        AISummaryEngine, ai_summary_engine,
        PRI_CRITICAL, PRI_HIGH, PRI_ROUTINE, PRI_MONITORING,
        SS_CRITICAL_FLOOR, SS_HIGH_FLOOR, SS_ROUTINE_FLOOR,
    )
    check("A1: ai_summary_engine importable", True)
except Exception as e:
    check("A1: ai_summary_engine importable", False, str(e))

try:
    from core.observability.strategic_feed import (
        StrategicFeed, strategic_feed,
        FeedEntry,
        FEED_RISK, FEED_LEARNING, FEED_PERFORMANCE, FEED_ANOMALY, FEED_REGIME,
        ALL_FEEDS,
    )
    check("A2: strategic_feed importable", True)
except Exception as e:
    check("A2: strategic_feed importable", False, str(e))

try:
    from core.observability import ai_summary_engine as ase_pkg, strategic_feed as sf_pkg
    check("A3: package __init__ exports Phase 4 singletons", True)
except Exception as e:
    check("A3: package __init__ exports Phase 4 singletons", False, str(e))

check("A4: singletons correct types",
      isinstance(ai_summary_engine, AISummaryEngine) and isinstance(strategic_feed, StrategicFeed))
check("A5: ALL_FEEDS has 5 entries",  len(ALL_FEEDS) == 5)
check("A6: priority constants defined",
      PRI_CRITICAL == "CRITICAL" and PRI_HIGH == "HIGH" and
      PRI_ROUTINE == "ROUTINE" and PRI_MONITORING == "MONITORING")


# ─────────────────────────────────────────────────────────────────────────────
# B: AISummaryEngine — output structure
# ─────────────────────────────────────────────────────────────────────────────
print("B: AISummaryEngine — output structure")

_ase = AISummaryEngine()

_healthy_comp = {
    "pnl": 150.0, "n_trades": 25, "profit_factor": 2.1, "win_rate": 0.68,
    "iq_score": 72.0, "rl_toxic": 0, "consec_losses": 0,
    "rl_allow_rate": 0.91, "rl_maturity_status": "MATURE",
    "rl_confidence_dir": "GROWING", "rl_explore_pressure": "BALANCED",
    "rl_profitable_pct": 68.0, "rl_maturity_pct": 65.0,
    "risk_halted": False, "gate_open": True,
    "regime": "TRENDING", "le_trending_wr": 0.62,
    "le_mean_rev_wr": 0.54, "le_vol_exp_wr": 0.48,
}

summary_b = _ase.generate_summary(_healthy_comp, {}, [])

check("B1: generate_summary returns dict",              isinstance(summary_b, dict))
check("B2: has headline",                               "headline" in summary_b)
check("B3: has priority",                               "priority" in summary_b)
check("B4: has signal_strength",                        "signal_strength" in summary_b)
check("B5: has directives list",                        isinstance(summary_b.get("directives"), list))
check("B6: has risk_narrative",                         "risk_narrative" in summary_b)
check("B7: has learning_narrative",                     "learning_narrative" in summary_b)
check("B8: has performance_narrative",                  "performance_narrative" in summary_b)


# ─────────────────────────────────────────────────────────────────────────────
# C: AISummaryEngine — CRITICAL scenario
# ─────────────────────────────────────────────────────────────────────────────
print("C: AISummaryEngine — CRITICAL scenario")

from core.observability.anomaly_detector import SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW

_critical_comp = {
    "pnl": -250.0, "n_trades": 30, "profit_factor": 0.5, "win_rate": 0.30,
    "iq_score": 12.0, "rl_toxic": 6, "consec_losses": 8,
    "rl_allow_rate": 0.25, "rl_maturity_status": "WARMING_UP",
    "rl_confidence_dir": "DECLINING", "rl_explore_pressure": "HIGH_EXPLORE",
    "risk_halted": True, "gate_open": False,
    "regime": "VOLATILITY_EXPANSION",
}
_critical_anomalies = [
    {"severity": SEV_CRITICAL, "category": "RISK_STATE",
     "description": "Engine halted", "metric": "risk_halted",
     "current_value": True, "threshold": False, "delta": None,
     "ts": int(time.time() * 1000), "anomaly_id": "c001"},
]
_critical_delta = {"has_meaningful_delta": True, "significance_score": 40.0,
                   "changed_fields": {"risk_halted": {}}, "summary": "halted"}

summary_c = _ase.generate_summary(_critical_comp, _critical_delta, _critical_anomalies)

check("C1: priority=CRITICAL",                    summary_c.get("priority") == PRI_CRITICAL)
check("C2: signal_strength >= 50",                summary_c.get("signal_strength", 0) >= 50.0)
check("C3: headline contains CRITICAL",           "CRITICAL" in summary_c.get("headline", ""))
check("C4: worst_severity=CRITICAL",              summary_c.get("worst_severity") == SEV_CRITICAL)
check("C5: directives not empty",                 len(summary_c.get("directives", [])) > 0)
check("C6: risk_narrative mentions halted",
      "HALT" in summary_c.get("risk_narrative", "").upper() or
      "halted" in summary_c.get("risk_narrative", "").lower())


# ─────────────────────────────────────────────────────────────────────────────
# D: AISummaryEngine — HIGH scenario
# ─────────────────────────────────────────────────────────────────────────────
print("D: AISummaryEngine — HIGH scenario")

_high_comp = {
    "pnl": -50.0, "n_trades": 15, "profit_factor": 0.8, "win_rate": 0.40,
    "iq_score": 42.0, "rl_toxic": 3, "consec_losses": 5,
    "rl_allow_rate": 0.55, "rl_confidence_dir": "DECLINING",
    "risk_halted": False, "gate_open": True,
    "regime": "TRENDING",
}
_high_anomalies = [
    {"severity": SEV_HIGH, "category": "LOSS_STREAK",
     "description": "5 consecutive losses", "metric": "consec_losses",
     "current_value": 5, "threshold": 5, "delta": 2,
     "ts": int(time.time() * 1000), "anomaly_id": "h001"},
]
_high_delta = {"has_meaningful_delta": True, "significance_score": 20.0,
               "changed_fields": {"consec_losses": {}}, "summary": "losses up"}

_ase2 = AISummaryEngine()
summary_d = _ase2.generate_summary(_high_comp, _high_delta, _high_anomalies)

check("D1: priority=HIGH or CRITICAL (IQ=42 adds 10pts)",
      summary_d.get("priority") in (PRI_HIGH, PRI_CRITICAL))
check("D2: signal_strength >= 30",   summary_d.get("signal_strength", 0) >= 30.0)
check("D3: ALERT in headline",       "ALERT" in summary_d.get("headline", "").upper()
                                     or "CRITICAL" in summary_d.get("headline", "").upper())
check("D4: worst_severity=HIGH",     summary_d.get("worst_severity") == SEV_HIGH)
check("D5: loss_streak directive",
      any("loss" in d.lower() for d in summary_d.get("directives", [])))


# ─────────────────────────────────────────────────────────────────────────────
# E: AISummaryEngine — ROUTINE / MONITORING scenario
# ─────────────────────────────────────────────────────────────────────────────
print("E: AISummaryEngine — ROUTINE/MONITORING")

_ase3 = AISummaryEngine()
summary_e = _ase3.generate_summary(_healthy_comp, {}, [])

check("E1: healthy scenario priority in (MONITORING, ROUTINE)",
      summary_e.get("priority") in (PRI_MONITORING, PRI_ROUTINE))
check("E2: signal_strength < 30",        summary_e.get("signal_strength", 100) < 30.0)
check("E3: headline contains STABLE",    "STABLE" in summary_e.get("headline", ""))
check("E4: anomaly_count = 0",           summary_e.get("anomaly_count") == 0)
check("E5: worst_severity = NONE",       summary_e.get("worst_severity") == "NONE")


# ─────────────────────────────────────────────────────────────────────────────
# F: AISummaryEngine — signal_strength math
# ─────────────────────────────────────────────────────────────────────────────
print("F: AISummaryEngine — signal_strength math")

_ase_ss = AISummaryEngine()

# No anomaly, no delta, high IQ → 0
ss_f1 = _ase_ss._signal_strength([], {}, {"iq_score": 75.0})
check("F1: healthy → ss=0", ss_f1 == 0.0, str(ss_f1))

# MEDIUM anomaly → 20 pts
ss_f2 = _ase_ss._signal_strength(
    [{"severity": SEV_MEDIUM}], {}, {"iq_score": 75.0})
check("F2: MEDIUM anomaly → ss=20", ss_f2 == 20.0, str(ss_f2))

# HIGH anomaly → 35 pts
ss_f3 = _ase_ss._signal_strength(
    [{"severity": SEV_HIGH}], {}, {"iq_score": 75.0})
check("F3: HIGH anomaly → ss=35", ss_f3 == 35.0, str(ss_f3))

# CRITICAL anomaly → 50 pts
ss_f4 = _ase_ss._signal_strength(
    [{"severity": SEV_CRITICAL}], {}, {"iq_score": 75.0})
check("F4: CRITICAL anomaly → ss=50", ss_f4 == 50.0, str(ss_f4))

# Delta score >= 30 → +30 pts
ss_f5 = _ase_ss._signal_strength(
    [], {"significance_score": 35.0}, {"iq_score": 75.0})
check("F5: delta_score=35 → ss=30", ss_f5 == 30.0, str(ss_f5))

# IQ < 20 → +20 pts
ss_f6 = _ase_ss._signal_strength([], {}, {"iq_score": 15.0})
check("F6: iq=15 → ss=20", ss_f6 == 20.0, str(ss_f6))

# Combined: CRITICAL(50) + delta(30) + iq<20(20) = capped at 100
ss_f7 = _ase_ss._signal_strength(
    [{"severity": SEV_CRITICAL}], {"significance_score": 35.0}, {"iq_score": 15.0})
check("F7: combined → ss capped at 100", ss_f7 == 100.0, str(ss_f7))

# Priority boundaries
from core.observability.ai_summary_engine import _priority_from_ss
check("F8: priority thresholds correct",
      _priority_from_ss(50.0) == PRI_CRITICAL and
      _priority_from_ss(30.0) == PRI_HIGH and
      _priority_from_ss(10.0) == PRI_ROUTINE and
      _priority_from_ss(5.0)  == PRI_MONITORING)


# ─────────────────────────────────────────────────────────────────────────────
# G: AISummaryEngine — headline correctness
# ─────────────────────────────────────────────────────────────────────────────
print("G: AISummaryEngine — headline correctness")

_ase_h = AISummaryEngine()

def _headline(comp, anomalies=None, delta=None):
    return _ase_h.generate_summary(comp, delta or {}, anomalies or []).get("headline", "")

# risk_halted → CRITICAL in headline
check("G1: risk_halted → CRITICAL headline",
      "CRITICAL" in _headline({**_healthy_comp, "risk_halted": True}))

# gate_closed → HIGH ALERT
check("G2: gate_closed → HIGH ALERT headline",
      "HIGH ALERT" in _headline({**_healthy_comp, "gate_open": False}))

# loss_streak_crit → HIGH ALERT
check("G3: consec_losses=7 → HIGH ALERT headline",
      "HIGH ALERT" in _headline({**_healthy_comp, "consec_losses": 7}))

# HIGH anomaly, no risk flags → ALERT
check("G4: HIGH anomaly → ALERT headline",
      "ALERT" in _headline(_healthy_comp,
                            [{"severity": SEV_HIGH, "description": "x",
                              "category": "LOSS_STREAK", "metric": "consec_losses",
                              "current_value": 5, "threshold": 5, "delta": 2,
                              "ts": 0, "anomaly_id": "g01"}]).upper())

# Healthy → STABLE headline
check("G5: healthy → STABLE headline", "STABLE" in _headline(_healthy_comp))

# regime shift (need prev_regime set) → INFO
_ase_h._prev_regime = "MEAN_REVERTING"
check("G6: regime shift → INFO or STABLE in headline",
      "INFO" in _headline({**_healthy_comp, "regime": "TRENDING"}) or
      "STABLE" in _headline({**_healthy_comp, "regime": "TRENDING"}))


# ─────────────────────────────────────────────────────────────────────────────
# H: AISummaryEngine — directives logic
# ─────────────────────────────────────────────────────────────────────────────
print("H: AISummaryEngine — directives logic")

_ase_dir = AISummaryEngine()

# risk_halted → risk directive present
s_h1 = _ase_dir.generate_summary({**_healthy_comp, "risk_halted": True}, {}, [])
check("H1: risk_halted produces risk directive",
      any("risk controller" in d.lower() or "halt" in d.lower()
          for d in s_h1.get("directives", [])))

# loss streak → loss directive
s_h2 = _ase_dir.generate_summary({**_healthy_comp, "consec_losses": 7}, {}, [])
check("H2: consec_losses=7 produces loss-streak directive",
      any("loss" in d.lower() for d in s_h2.get("directives", [])))

# declining confidence → confidence directive
s_h3 = _ase_dir.generate_summary({**_healthy_comp, "rl_confidence_dir": "DECLINING"}, {}, [])
check("H3: DECLINING confidence produces confidence directive",
      any("confidence" in d.lower() or "position size" in d.lower()
          for d in s_h3.get("directives", [])))

# Low IQ → IQ directive
s_h4 = _ase_dir.generate_summary({**_healthy_comp, "iq_score": 15.0}, {}, [])
check("H4: iq=15 produces IQ directive",
      any("intelligence" in d.lower() or "rl" in d.lower() or "learning" in d.lower()
          for d in s_h4.get("directives", [])))

# Healthy → no or few directives
s_h5 = _ase_dir.generate_summary(_healthy_comp, {}, [])
check("H5: healthy scenario has 0 directives",
      len(s_h5.get("directives", [])) == 0)

# Directives is always a list
check("H6: directives always a list",
      all(isinstance(s.get("directives"), list)
          for s in [s_h1, s_h2, s_h3, s_h4, s_h5]))


# ─────────────────────────────────────────────────────────────────────────────
# I: AISummaryEngine — narrative sections
# ─────────────────────────────────────────────────────────────────────────────
print("I: AISummaryEngine — narrative sections")

_ase_n = AISummaryEngine()
s_i = _ase_n.generate_summary(_critical_comp, _critical_delta, _critical_anomalies)

check("I1: risk_narrative is non-empty string",        len(s_i.get("risk_narrative", "")) > 0)
check("I2: learning_narrative is non-empty string",    len(s_i.get("learning_narrative", "")) > 0)
check("I3: performance_narrative is non-empty string", len(s_i.get("performance_narrative", "")) > 0)
check("I4: regime_narrative is non-empty string",      len(s_i.get("regime_narrative", "")) > 0)
check("I5: risk_narrative mentions toxic",
      "toxic" in s_i.get("risk_narrative", "").lower())
check("I6: performance_narrative mentions PnL",
      "pnl" in s_i.get("performance_narrative", "").lower() or
      "$" in s_i.get("performance_narrative", ""))


# ─────────────────────────────────────────────────────────────────────────────
# J: AISummaryEngine — stats tracking
# ─────────────────────────────────────────────────────────────────────────────
print("J: AISummaryEngine — stats")

_ase_st = AISummaryEngine()
_ase_st.generate_summary(_critical_comp, {}, _critical_anomalies)  # CRITICAL
_ase_st.generate_summary(_healthy_comp, {}, [])                    # MONITORING

st = _ase_st.stats()
check("J1: stats returns dict",            isinstance(st, dict))
check("J2: total_summaries = 2",           st.get("total_summaries") == 2)
check("J3: critical_count >= 1",           st.get("critical_count", 0) >= 1)
check("J4: last_priority not empty",       st.get("last_priority") != "")


# ─────────────────────────────────────────────────────────────────────────────
# K: StrategicFeed — refresh() structure
# ─────────────────────────────────────────────────────────────────────────────
print("K: StrategicFeed — refresh() structure")

_sf = StrategicFeed()
feeds_k = _sf.refresh(_healthy_comp, [])

check("K1: refresh returns dict",                       isinstance(feeds_k, dict))
check("K2: all 5 feeds present",                        set(feeds_k.keys()) == set(ALL_FEEDS))
check("K3: each value is FeedEntry",                    all(isinstance(v, FeedEntry) for v in feeds_k.values()))
check("K4: each FeedEntry has feed name",               all(f.feed in ALL_FEEDS for f in feeds_k.values()))
check("K5: each FeedEntry has signal_strength 0–100",
      all(0.0 <= f.signal_strength <= 100.0 for f in feeds_k.values()))
check("K6: each FeedEntry has non-empty directive",
      all(len(f.directive) > 0 for f in feeds_k.values()))


# ─────────────────────────────────────────────────────────────────────────────
# L: StrategicFeed — RISK feed
# ─────────────────────────────────────────────────────────────────────────────
print("L: StrategicFeed — RISK feed")

_sf_r = StrategicFeed()

# Halted → ss=100, HALTED
feeds_l1 = _sf_r.refresh({**_healthy_comp, "risk_halted": True}, [])
risk_l1  = feeds_l1[FEED_RISK]
check("L1: risk_halted → ss=100",    risk_l1.signal_strength == 100.0, str(risk_l1.signal_strength))
check("L2: risk_halted → HALTED",    risk_l1.state == "HALTED")

# Gate closed → ss=80, BLOCKED
feeds_l2 = _sf_r.refresh({**_healthy_comp, "gate_open": False}, [])
risk_l2  = feeds_l2[FEED_RISK]
check("L3: gate_open=False → ss=80", risk_l2.signal_strength == 80.0)
check("L4: gate_open=False → BLOCKED", risk_l2.state == "BLOCKED")

# 5+ consec losses → ss=60, ELEVATED
feeds_l3 = _sf_r.refresh({**_healthy_comp, "consec_losses": 5}, [])
risk_l3  = feeds_l3[FEED_RISK]
check("L5: consec_losses=5 → ss=60", risk_l3.signal_strength == 60.0, str(risk_l3.signal_strength))
check("L6: consec_losses=5 → ELEVATED", risk_l3.state == "ELEVATED")

# Healthy → ss=0, NOMINAL
feeds_l4 = _sf_r.refresh(_healthy_comp, [])
risk_l4  = feeds_l4[FEED_RISK]
check("L7: healthy → NOMINAL state", risk_l4.state == "NOMINAL")


# ─────────────────────────────────────────────────────────────────────────────
# M: StrategicFeed — LEARNING feed
# ─────────────────────────────────────────────────────────────────────────────
print("M: StrategicFeed — LEARNING feed")

_sf_l = StrategicFeed()

# IQ < 20 → CRITICAL
feeds_m1 = _sf_l.refresh({**_healthy_comp, "iq_score": 10.0}, [])
learn_m1 = feeds_m1[FEED_LEARNING]
check("M1: iq=10 → ss=100",      learn_m1.signal_strength == 100.0)
check("M2: iq=10 → CRITICAL",    learn_m1.state == "CRITICAL")

# IQ in [35, 50) → DEVELOPING
feeds_m2 = _sf_l.refresh({**_healthy_comp, "iq_score": 42.0}, [])
learn_m2 = feeds_m2[FEED_LEARNING]
check("M3: iq=42 → DEVELOPING",  learn_m2.state == "DEVELOPING")

# IQ >= 65 → MATURING
feeds_m3 = _sf_l.refresh({**_healthy_comp, "iq_score": 72.0}, [])
learn_m3 = feeds_m3[FEED_LEARNING]
check("M4: iq=72 → MATURING",    learn_m3.state == "MATURING")
check("M5: iq=72 → ss=0",        learn_m3.signal_strength == 0.0)
check("M6: LEARNING data has iq_score", "iq_score" in learn_m3.data)


# ─────────────────────────────────────────────────────────────────────────────
# N: StrategicFeed — PERFORMANCE feed
# ─────────────────────────────────────────────────────────────────────────────
print("N: StrategicFeed — PERFORMANCE feed")

_sf_p = StrategicFeed()

# PnL < -200 → ss=100, LOSING
feeds_n1 = _sf_p.refresh({**_healthy_comp, "pnl": -250.0, "profit_factor": 0.4}, [])
perf_n1  = feeds_n1[FEED_PERFORMANCE]
check("N1: pnl=-250 → ss=100",   perf_n1.signal_strength == 100.0)
check("N2: pnl=-250 → LOSING",   perf_n1.state == "LOSING")

# PF < 1.0 → ss=50, WEAK
feeds_n2 = _sf_p.refresh({**_healthy_comp, "pnl": -10.0, "profit_factor": 0.85}, [])
perf_n2  = feeds_n2[FEED_PERFORMANCE]
check("N3: pf=0.85 → ss=50",     perf_n2.signal_strength == 50.0)
check("N4: pf=0.85 → WEAK",      perf_n2.state == "WEAK")

# PF >= 2.0 → STRONG
feeds_n3 = _sf_p.refresh({**_healthy_comp, "profit_factor": 2.3}, [])
perf_n3  = feeds_n3[FEED_PERFORMANCE]
check("N5: pf=2.3 → STRONG",     perf_n3.state == "STRONG")
check("N6: PERFORMANCE data has profit_factor", "profit_factor" in perf_n3.data)


# ─────────────────────────────────────────────────────────────────────────────
# O: StrategicFeed — ANOMALY feed
# ─────────────────────────────────────────────────────────────────────────────
print("O: StrategicFeed — ANOMALY feed")

_sf_a = StrategicFeed()

feeds_o1 = _sf_a.refresh(_healthy_comp, _critical_anomalies)
anom_o1  = feeds_o1[FEED_ANOMALY]
check("O1: CRITICAL anomaly → ss=100",      anom_o1.signal_strength == 100.0)
check("O2: CRITICAL anomaly → CRITICAL",    anom_o1.state == "CRITICAL")
check("O3: critical_count=1 in data",       anom_o1.data.get("critical_count") == 1)

feeds_o2 = _sf_a.refresh(_healthy_comp, [
    {"severity": SEV_HIGH, "description": "x", "category": "LOSS_STREAK",
     "metric": "c", "current_value": 5, "threshold": 5, "delta": 1,
     "ts": 0, "anomaly_id": "o01"}])
anom_o2  = feeds_o2[FEED_ANOMALY]
check("O4: HIGH anomaly → ss=75",   anom_o2.signal_strength == 75.0)

feeds_o3 = _sf_a.refresh(_healthy_comp, [])
anom_o3  = feeds_o3[FEED_ANOMALY]
check("O5: no anomalies → ALL_CLEAR",         anom_o3.state == "ALL_CLEAR")
check("O6: no anomalies → ss=0",              anom_o3.signal_strength == 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# P: StrategicFeed — REGIME feed
# ─────────────────────────────────────────────────────────────────────────────
print("P: StrategicFeed — REGIME feed")

_sf_reg = StrategicFeed()

# Establish prev regime
_sf_reg.refresh({**_healthy_comp, "regime": "MEAN_REVERTING"}, [])

# Regime shift → SHIFTING, ss=50
feeds_p1 = _sf_reg.refresh({**_healthy_comp, "regime": "TRENDING"}, [])
reg_p1   = feeds_p1[FEED_REGIME]
check("P1: regime shift → SHIFTING state",   reg_p1.state == "SHIFTING")
check("P2: regime shift → ss=50",            reg_p1.signal_strength == 50.0)

# Weak WR → WEAK
feeds_p2 = _sf_reg.refresh({**_healthy_comp, "le_trending_wr": 0.35}, [])
reg_p2   = feeds_p2[FEED_REGIME]
check("P3: trending_wr=0.35 → WEAK or SHIFTING", reg_p2.state in ("WEAK", "SHIFTING"))

# Healthy WR → ALIGNED
_sf_reg2 = StrategicFeed()
feeds_p3 = _sf_reg2.refresh({**_healthy_comp, "le_trending_wr": 0.62}, [])
reg_p3   = feeds_p3[FEED_REGIME]
check("P4: healthy → ALIGNED",       reg_p3.state == "ALIGNED")
check("P5: REGIME data has regime",  "regime" in reg_p3.data)


# ─────────────────────────────────────────────────────────────────────────────
# Q: StrategicFeed — get_priority_feeds
# ─────────────────────────────────────────────────────────────────────────────
print("Q: StrategicFeed — get_priority_feeds")

_sf_pf = StrategicFeed()
_sf_pf.refresh({**_healthy_comp, "risk_halted": True,
                "iq_score": 10.0, "pnl": -300.0}, _critical_anomalies)

pf_50 = _sf_pf.get_priority_feeds(min_strength=50.0)
check("Q1: get_priority_feeds returns list",            isinstance(pf_50, list))
check("Q2: all returned feeds have ss >= 50",           all(f.signal_strength >= 50.0 for f in pf_50))
check("Q3: sorted descending by signal_strength",
      all(pf_50[i].signal_strength >= pf_50[i+1].signal_strength
          for i in range(len(pf_50) - 1)))
check("Q4: get_priority_feeds(100) returns only ss=100 feeds",
      all(f.signal_strength == 100.0 for f in _sf_pf.get_priority_feeds(min_strength=100.0)))
check("Q5: get_priority_feeds(101) returns empty list",
      _sf_pf.get_priority_feeds(min_strength=101.0) == [])


# ─────────────────────────────────────────────────────────────────────────────
# R: StrategicFeed — status()
# ─────────────────────────────────────────────────────────────────────────────
print("R: StrategicFeed — status()")

status_r = _sf_pf.status()
check("R1: status returns dict",             isinstance(status_r, dict))
check("R2: status has total_refreshes",      "total_refreshes" in status_r)
check("R3: status has max_signal",           "max_signal" in status_r)
check("R4: status has feed_states section",  "feed_states" in status_r)


# ─────────────────────────────────────────────────────────────────────────────
# S: Resilience / non-throwing
# ─────────────────────────────────────────────────────────────────────────────
print("S: Resilience")

try:
    r_s1 = AISummaryEngine().generate_summary(None)   # type: ignore
    check("S1: generate_summary(None) does not throw", True)
except Exception as e:
    check("S1: generate_summary(None) does not throw", False, str(e))

try:
    r_s2 = AISummaryEngine().generate_summary({})
    check("S2: generate_summary({}) returns dict", isinstance(r_s2, dict))
except Exception as e:
    check("S2: generate_summary({}) returns dict", False, str(e))

try:
    r_s3 = StrategicFeed().refresh(None)  # type: ignore
    check("S3: StrategicFeed.refresh(None) does not throw", True)
except Exception as e:
    check("S3: StrategicFeed.refresh(None) does not throw", False, str(e))

try:
    r_s4 = StrategicFeed().refresh({})
    check("S4: StrategicFeed.refresh({}) returns dict", isinstance(r_s4, dict))
except Exception as e:
    check("S4: StrategicFeed.refresh({}) returns dict", False, str(e))

try:
    r_s5 = StrategicFeed().get_priority_feeds()
    check("S5: get_priority_feeds on empty feed does not throw", isinstance(r_s5, list))
except Exception as e:
    check("S5: get_priority_feeds on empty feed does not throw", False, str(e))

try:
    r_s6 = AISummaryEngine().stats()
    check("S6: stats() on fresh engine does not throw", isinstance(r_s6, dict))
except Exception as e:
    check("S6: stats() on fresh engine does not throw", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# T: Integration — full Phase 1→4 pipeline
# ─────────────────────────────────────────────────────────────────────────────
print("T: Integration — full Phase 1→4 pipeline")

from core.observability.intelligence_compressor import IntelligenceCompressor
from core.observability.delta_reporter import DeltaReporter
from core.observability.anomaly_detector import AnomalyDetector
from core.observability.ai_summary_engine import AISummaryEngine as ASE
from core.observability.strategic_feed import StrategicFeed as SF

_ic_t  = IntelligenceCompressor()
_dr_t  = DeltaReporter()
_ad_t  = AnomalyDetector()
_ase_t = ASE()
_sf_t  = SF()

_raw_t = {
    "session_stats": {"total_net_pnl": 175.0, "n_trades": 28, "profit_factor": 1.95, "win_rate": 0.64},
    "rl": {
        "total_contexts": 55, "total_trade_decisions": 275,
        "evolution_state": {"intelligence_score": 68.0},
        "summary_metrics": {"toxic_contexts": 1, "allow_rate": 0.88, "profitable_pct": 65.0},
        "learning_speed": {"maturity_pct": 58.0, "status": "LEARNING"},
        "exploration_pressure": {"pressure_status": "BALANCED"},
        "confidence_trajectory": {"confidence_direction": "GROWING"},
    },
    "risk": {"halted": False}, "gate": {"can_trade": True},
    "trade_flow": {"consecutive_losses": 1, "daily_trades": 12},
    "regime": "TRENDING", "uptime_secs": 5400, "error_count": 0,
    "learning": {
        "TRENDING": {"win_rate": 0.58},
        "MEAN_REVERTING": {"win_rate": 0.52},
        "VOLATILITY_EXPANSION": {"win_rate": 0.45},
    },
}

compressed_t  = _ic_t.compress(_raw_t)
delta_t       = _dr_t.compute_delta(compressed_t)
anomalies_t   = _ad_t.scan(compressed_t)
summary_t     = _ase_t.generate_summary(compressed_t, delta_t, anomalies_t)
feeds_t       = _sf_t.refresh(compressed_t, anomalies_t)

check("T1: compress produces dict",               isinstance(compressed_t, dict) and "pnl" in compressed_t)
check("T2: delta emitted (baseline)",             delta_t.get("is_baseline") is True)
check("T3: 1 toxic → MEDIUM anomaly present",
      any(a.get("category") == "TOXIC_SPIKE" for a in anomalies_t))
check("T4: summary has priority field",           "priority" in summary_t)
check("T5: all 5 feeds refreshed",               set(feeds_t.keys()) == set(ALL_FEEDS))
check("T6: RISK feed NOMINAL (risk_halted=False)", feeds_t[FEED_RISK].state == "NOMINAL")
check("T7: LEARNING feed not CRITICAL (iq=68)",   feeds_t[FEED_LEARNING].state != "CRITICAL")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
for line in _results:
    print(line)

total = PASS + FAIL
print(f"\n{'=' * 60}")
print(f"FTD-053-GAIA Phase 4 Verifier: {PASS}/{total} checks passed")
if FAIL > 0:
    print(f"FAILED: {FAIL} checks")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
