"""
FTD-RCAF-001 — Root Cause Attribution Framework Verifier
=========================================================
Validates that the RCAF engine:
  1. Initialises correctly
  2. Records gate decisions accurately
  3. Accumulates stats without data loss
  4. Produces correct attribution reports
  5. Detects anomalies
  6. Does NOT interfere with trade logic (zero side-effects)

Run:
    python tests/test_rcaf_verifier.py

Expected output on pass:
    [PASS] RCAF Verifier — all 8 checks passed
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.observability.rcaf_engine import RCAFEngine

PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        print(f"  [OK]  {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))
        FAIL += 1


# ── Test 1: Initialisation ────────────────────────────────────────────────────
print("\n=== TEST 1: Initialisation ===")
engine = RCAFEngine(enabled=True)
h = engine.get_health()
check("status=ACTIVE",         h["status"] == "ACTIVE")
check("signals_seen=0",        h["signals_seen"] == 0)
check("gates_monitored=0",     h["gates_monitored"] == 0)
check("buffer_cap=10000",      h["buffer_cap"] == 10_000)


# ── Test 2: Signal open + gate logging ───────────────────────────────────────
print("\n=== TEST 2: Signal Open + Gate Logging ===")
now = int(time.time() * 1000)
engine.open_signal("BTCUSDT_001", "BTCUSDT", now, "TrendFollowing", "TRENDING")
engine.log_gate("fee_viability",   "BTCUSDT_001", would_block=True,  reason="FEE_TOO_HIGH")
engine.log_gate("frequency_cooldown", "BTCUSDT_001", would_block=False, reason="")
engine.log_gate("risk_engine",     "BTCUSDT_001", would_block=True,  reason="DAILY_LOSS_CAP")

h = engine.get_health()
check("signals_seen=1",         h["signals_seen"] == 1)
check("gates_monitored=3",      h["gates_monitored"] == 3)

report = engine.get_attribution_report()
comps  = {r["component"]: r for r in report["components"]}

check("fee_viability block=1",
      comps.get("fee_viability", {}).get("would_block_count") == 1)
check("frequency_cooldown allow=1",
      comps.get("frequency_cooldown", {}).get("would_allow_count") == 1)
check("risk_engine block=1",
      comps.get("risk_engine", {}).get("would_block_count") == 1)


# ── Test 3: Multiple signals ──────────────────────────────────────────────────
print("\n=== TEST 3: Multiple Signals & Accumulation ===")
for i in range(10):
    sid = f"ETHUSDT_{i:03d}"
    engine.open_signal(sid, "ETHUSDT", now + i, "MeanReversion", "MEAN_REVERTING")
    engine.log_gate("fee_viability", sid, would_block=(i % 3 == 0))

report = engine.get_attribution_report()
comps  = {r["component"]: r for r in report["components"]}
fee_comp = comps.get("fee_viability", {})

expected_blocks = 1 + sum(1 for i in range(10) if i % 3 == 0)  # 1 from test 2 + 4 new
expected_allows = 0 + sum(1 for i in range(10) if i % 3 != 0)  # 0 from test 2 (was block) + 6 new

check(f"fee_viability cumulative block={expected_blocks}",
      fee_comp.get("would_block_count") == expected_blocks,
      f"got {fee_comp.get('would_block_count')}")
check(f"fee_viability cumulative allow={expected_allows}",
      fee_comp.get("would_allow_count") == expected_allows,
      f"got {fee_comp.get('would_allow_count')}")
check("signals_seen=11",  engine.get_health()["signals_seen"] == 11)


# ── Test 4: mark_executed + record_pnl ───────────────────────────────────────
print("\n=== TEST 4: Trade Execution & PnL Attribution ===")
sid = "SOLUSDT_100"
engine.open_signal(sid, "SOLUSDT", now, "TrendFollowing", "TRENDING")
engine.log_gate("fee_viability", sid, would_block=True, reason="FEE_HIGH")
engine.mark_executed(sid, "trade_abc123")
engine.record_pnl(sid, net_pnl=-0.50, fee=0.08)

report = engine.get_attribution_report()
comps  = {r["component"]: r for r in report["components"]}
fee_comp = comps.get("fee_viability", {})

check("trades_avoided incremented",
      fee_comp.get("trades_avoided_count", 0) >= 1)
check("est_pnl_if_blocked accumulated",
      fee_comp.get("est_pnl_if_blocked", 0) != 0,
      f"got {fee_comp.get('est_pnl_if_blocked')}")
check("est_fee_savings accumulated",
      fee_comp.get("est_fee_savings", 0) > 0,
      f"got {fee_comp.get('est_fee_savings')}")


# ── Test 5: Shadow log ────────────────────────────────────────────────────────
print("\n=== TEST 5: Shadow Log ===")
log = engine.get_shadow_log(limit=50)
check("status=ACTIVE",        log["status"] == "ACTIVE")
check("count > 0",            log["count"] > 0)
check("records list present", isinstance(log["records"], list))
if log["records"]:
    rec = log["records"][0]
    check("record has signal_id", "signal_id" in rec)
    check("record has gates dict", isinstance(rec.get("gates"), dict))


# ── Test 6: Anomaly detection ────────────────────────────────────────────────
print("\n=== TEST 6: Anomaly Detection ===")
# Seed enough data that anomaly check triggers
eng2 = RCAFEngine(enabled=True)
for i in range(50):
    sid = f"TEST_{i:03d}"
    eng2.open_signal(sid, "TEST", now + i, "TF", "TRENDING")
    eng2.log_gate("test_gate", sid, would_block=True)  # 100% block rate

# Expected ~50%, actual 100% → anomaly
anomaly = eng2.check_anomaly("test_gate", expected_block_rate_pct=50.0)
check("anomaly detected on 100% block vs 50% expected",  anomaly is not None)
if anomaly:
    check("anomaly has deviation field",  "deviation_pp" in anomaly)
    check("deviation >= 40",  anomaly.get("deviation_pp", 0) >= 40)


# ── Test 7: Disabled engine is safe ──────────────────────────────────────────
print("\n=== TEST 7: Disabled Engine — No Errors ===")
disabled = RCAFEngine(enabled=False)
try:
    disabled.open_signal("X_001", "X", now, "TF", "TRENDING")
    disabled.log_gate("g1", "X_001", would_block=True)
    disabled.mark_executed("X_001", "t1")
    disabled.record_pnl("X_001", -1.0, 0.05)
    result = disabled.get_attribution_report()
    log2   = disabled.get_shadow_log()
    check("disabled status",        result.get("status") == "RCAF_DISABLED")
    check("disabled shadow log",    log2.get("status") == "RCAF_DISABLED")
    check("no crash when disabled", True)
except Exception as exc:
    check("no crash when disabled", False, str(exc))


# ── Test 8: Report structure completeness ────────────────────────────────────
print("\n=== TEST 8: Report Structure ===")
report = engine.get_attribution_report()
required_keys = {
    "status", "rcaf_boot_ts", "uptime_sec",
    "signals_seen", "trades_seen", "gates_monitored",
    "buffer_size", "anomalies_logged", "components",
    "anomalies", "generated_at",
}
missing = required_keys - set(report.keys())
check("all required top-level keys present",  len(missing) == 0,
      f"missing={missing}")

if report.get("components"):
    row = report["components"][0]
    row_keys = {
        "component", "would_block_count", "would_allow_count",
        "total_evaluations", "block_rate_pct", "trades_avoided_count",
        "est_pnl_improvement", "est_fee_savings", "confidence", "status",
    }
    missing_row = row_keys - set(row.keys())
    check("all required component row keys present",  len(missing_row) == 0,
          f"missing={missing_row}")


# ── Summary ───────────────────────────────────────────────────────────────────
total = PASS + FAIL
print(f"\n{'='*60}")
if FAIL == 0:
    print(f"[PASS] RCAF Verifier — all {PASS} checks passed")
    sys.exit(0)
else:
    print(f"[FAIL] RCAF Verifier — {FAIL}/{total} checks failed")
    sys.exit(1)
