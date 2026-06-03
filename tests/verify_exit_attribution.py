"""
FTD-PHOENIX-EXIT-ATTR-001 — Exit Attribution Layer Verifier
============================================================
Validates that exit attribution is correctly resolved and persisted for all
canonical exit methods before deployment.

Run: python tests/verify_exit_attribution.py
All assertions must pass (exit code 0) before the build is deployable.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exit_attribution import (
    resolve_exit_method,
    compute_exit_attribution_report,
    CLOSE_TAG_MAP,
    FAST_FAIL, TIME_EXIT, STOP_LOSS, TAKE_PROFIT,
    TRAILING_STOP, BREAK_EVEN, VTP_EXIT, SPEED_EXIT,
    EMERGENCY, MANUAL, UNKNOWN,
)

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

_failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {name}{suffix}")
    if not condition:
        _failures.append(f"{name}: {detail}")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Canonical constants are defined
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 1: Canonical Constants ──")

for method in [FAST_FAIL, TIME_EXIT, STOP_LOSS, TAKE_PROFIT,
               TRAILING_STOP, BREAK_EVEN, VTP_EXIT, SPEED_EXIT,
               EMERGENCY, MANUAL, UNKNOWN]:
    check(f"Constant '{method}' is a non-empty string", isinstance(method, str) and len(method) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — CLOSE_TAG_MAP covers all risk_controller tags
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 2: CLOSE_TAG_MAP coverage ──")

for tag, expected in [
    ("SL",        STOP_LOSS),
    ("TP",        TAKE_PROFIT),
    ("TSL+",      TRAILING_STOP),
    ("BE",        BREAK_EVEN),
    ("SPEED",     SPEED_EXIT),
    ("EMERGENCY", EMERGENCY),
]:
    check(
        f"CLOSE_TAG_MAP['{tag}'] == '{expected}'",
        CLOSE_TAG_MAP.get(tag) == expected,
        f"got {CLOSE_TAG_MAP.get(tag)}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — resolve_exit_method priority logic
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 3: resolve_exit_method ──")

# Pending attr takes priority over close_tag
m, r = resolve_exit_method("SL", {"exit_method": FAST_FAIL, "exit_reason": "Fast-fail 1.5min r=-0.40"})
check("Pending FAST_FAIL attr overrides SL close_tag", m == FAST_FAIL, f"got {m}")
check("exit_reason preserved from pending attr", "Fast-fail" in r, f"got '{r}'")

m2, r2 = resolve_exit_method("SL", {"exit_method": TIME_EXIT, "exit_reason": "Stale 9.0min r=0.10"})
check("Pending TIME_EXIT attr overrides SL close_tag", m2 == TIME_EXIT, f"got {m2}")

# No pending attr — use close_tag
m3, _ = resolve_exit_method("TP", None)
check("No pending attr: TP → TAKE_PROFIT", m3 == TAKE_PROFIT, f"got {m3}")

m4, _ = resolve_exit_method("TSL+", None)
check("No pending attr: TSL+ → TRAILING_STOP", m4 == TRAILING_STOP, f"got {m4}")

m5, _ = resolve_exit_method("BE", None)
check("No pending attr: BE → BREAK_EVEN", m5 == BREAK_EVEN, f"got {m5}")

m6, _ = resolve_exit_method("EMERGENCY", None)
check("No pending attr: EMERGENCY → EMERGENCY", m6 == EMERGENCY, f"got {m6}")

# Unknown close_tag
m7, _ = resolve_exit_method("WEIRD_TAG", None)
check("Unknown close_tag → UNKNOWN", m7 == UNKNOWN, f"got {m7}")

# None inputs → UNKNOWN
m8, _ = resolve_exit_method(None, None)
check("None close_tag + None attr → UNKNOWN", m8 == UNKNOWN, f"got {m8}")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 — compute_exit_attribution_report
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 4: compute_exit_attribution_report ──")

_sample_trades = [
    {"exit_method": FAST_FAIL,     "net_pnl": -8.0,  "gross_pnl": -7.5,  "r_multiple": -0.40, "fee_entry": 0.3, "fee_exit": 0.2},
    {"exit_method": FAST_FAIL,     "net_pnl": -6.0,  "gross_pnl": -5.5,  "r_multiple": -0.38, "fee_entry": 0.3, "fee_exit": 0.2},
    {"exit_method": TIME_EXIT,     "net_pnl": -3.0,  "gross_pnl": -2.0,  "r_multiple": -0.12, "fee_entry": 0.5, "fee_exit": 0.5},
    {"exit_method": TAKE_PROFIT,   "net_pnl": 15.0,  "gross_pnl": 16.0,  "r_multiple": 1.50,  "fee_entry": 0.5, "fee_exit": 0.5},
    {"exit_method": TAKE_PROFIT,   "net_pnl": 12.0,  "gross_pnl": 13.0,  "r_multiple": 1.20,  "fee_entry": 0.5, "fee_exit": 0.5},
    {"exit_method": STOP_LOSS,     "net_pnl": -10.0, "gross_pnl": -9.5,  "r_multiple": -1.00, "fee_entry": 0.3, "fee_exit": 0.2},
    {"exit_method": TRAILING_STOP, "net_pnl": 8.0,   "gross_pnl": 9.0,   "r_multiple": 0.80,  "fee_entry": 0.5, "fee_exit": 0.5},
    {"exit_method": UNKNOWN,       "net_pnl": -1.0,  "gross_pnl": -0.5,  "r_multiple": -0.10, "fee_entry": 0.3, "fee_exit": 0.2},
]

report = compute_exit_attribution_report(_sample_trades)

check("Report has 'total_trades'", "total_trades" in report, f"keys={list(report.keys())}")
check("total_trades == 8", report["total_trades"] == 8, f"got {report['total_trades']}")
check("Report has 'breakdown'", "breakdown" in report)
check("Report has 'top_destroyer'", "top_destroyer" in report)
check("Report has 'top_alpha'", "top_alpha" in report)
check("Breakdown includes FAST_FAIL", FAST_FAIL in report["breakdown"])
check("Breakdown includes TAKE_PROFIT", TAKE_PROFIT in report["breakdown"])
check("Breakdown includes UNKNOWN", UNKNOWN in report["breakdown"])

ff = report["breakdown"][FAST_FAIL]
check("FAST_FAIL count == 2", ff["count"] == 2, f"got {ff['count']}")
check("FAST_FAIL win_rate == 0.0", ff["win_rate"] == 0.0, f"got {ff['win_rate']}")

tp = report["breakdown"][TAKE_PROFIT]
check("TAKE_PROFIT count == 2", tp["count"] == 2, f"got {tp['count']}")
check("TAKE_PROFIT win_rate == 100.0", tp["win_rate"] == 100.0, f"got {tp['win_rate']}")

# top_alpha should be TAKE_PROFIT (highest net_pnl sum = 27.0)
check(
    "top_alpha is TAKE_PROFIT",
    report["top_alpha"] == TAKE_PROFIT,
    f"got {report['top_alpha']}",
)
# top_destroyer should be FAST_FAIL (lowest net_pnl sum = -14.0; two trades at -8 and -6)
check(
    "top_destroyer is FAST_FAIL",
    report["top_destroyer"] == FAST_FAIL,
    f"got {report['top_destroyer']}",
)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — TradeRecord has exit_method and exit_reason fields
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 5: TradeRecord Exit Attribution Fields ──")

from core.pnl_calculator import TradeRecord

tr = TradeRecord(
    trade_id="test-001", symbol="BTCUSDT", side="BUY",
    entry_price=50000.0, exit_price=51000.0, qty=0.01,
    entry_ts=1000000, exit_ts=1001000,
)
check("TradeRecord.exit_method defaults to 'UNKNOWN'", tr.exit_method == "UNKNOWN", f"got '{tr.exit_method}'")
check("TradeRecord.exit_reason defaults to ''", tr.exit_reason == "", f"got '{tr.exit_reason}'")

tr.exit_method = FAST_FAIL
tr.exit_reason = "Fast-fail: 1.5min r=-0.40<-0.35"
check("TradeRecord.exit_method is writable", tr.exit_method == FAST_FAIL)
check("TradeRecord.exit_reason is writable", "Fast-fail" in tr.exit_reason)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 6 — Empty trade list is handled gracefully
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 6: Edge Cases ──")

empty_report = compute_exit_attribution_report([])
check("Empty trades returns total_trades=0", empty_report["total_trades"] == 0)
check("Empty trades breakdown is empty dict", empty_report["breakdown"] == {})

# Trades with no exit_method field → UNKNOWN bucket
trades_no_attr = [{"net_pnl": 5.0, "gross_pnl": 6.0, "r_multiple": 0.5, "fee_entry": 0.5, "fee_exit": 0.5}]
report_no_attr = compute_exit_attribution_report(trades_no_attr)
check("Trade with no exit_method → UNKNOWN bucket", UNKNOWN in report_no_attr["breakdown"])


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "═" * 60)
if _failures:
    print(f"\n{FAIL}  {len(_failures)} assertion(s) failed:\n")
    for f in _failures:
        print(f"  • {f}")
    print()
    sys.exit(1)
else:
    total_checks = sum(
        1 for line in open(__file__).readlines() if line.strip().startswith("check(")
    )
    print(f"\n{PASS}  All {total_checks} checks passed — FTD-PHOENIX-EXIT-ATTR-001 verified.\n")
    sys.exit(0)
