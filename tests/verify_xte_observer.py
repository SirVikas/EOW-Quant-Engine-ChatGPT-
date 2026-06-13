#!/usr/bin/env python3
"""
FTD-094A mandatory verifier — tests/verify_xte_observer.py

Confirms, with NO live engine, that:
  1. XTE executes (observe → score + advisory)
  2. The observation archive works (on_close writes; read back)
  3. Reports generate correctly (report_sections returns the 4 sections)
  4. Execution remains untouched (no SL/TP mutation; observe-flag default-off;
     force-close invariant preserved)

Exit code 0 = all checks pass.
"""
from __future__ import annotations

import os
import sys
import tempfile
from types import SimpleNamespace

# Repo root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import cfg
from core.truth.xte_observer import xte_observer, _current_r, _advisory_label

_PASS = 0
_FAIL = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  ✓  {label}")
    else:
        _FAIL += 1
        print(f"  ✗  {label}  {detail}")


def _fake_position(side="LONG", entry=100.0, sl=98.0, peak_r=1.2):
    return SimpleNamespace(
        symbol="TESTUSDT", side=side, entry_price=entry, stop_loss=sl,
        initial_stop_loss=sl, peak_r=peak_r, regime="TRENDING",
        entry_ts=1_000_000, take_profit=110.0, qty=1.0,
    )


def _fake_trade(side="LONG", r_multiple=0.6, peak_r=1.5, net_pnl=0.4):
    return SimpleNamespace(
        symbol="TESTUSDT", side=side, r_multiple=r_multiple, peak_r=peak_r,
        net_pnl=net_pnl, regime="TRENDING", entry_ts=1_000_000, exit_ts=1_300_000,
        atr_pct=0.85, exit_method="TRAILING_STOP",
    )


def main() -> int:
    print("\n══ FTD-094A — XTE OBSERVER VERIFIER ══\n")

    # Isolated temp archive so we never touch the real reports/ tree.
    tmp = tempfile.mkdtemp(prefix="xte_obs_")
    archive = os.path.join(tmp, "xte_observations.jsonl")
    cfg.XTE_OBSERVE_ARCHIVE = archive
    xte_observer.reset()

    # ── TEST 1 — XTE executes ────────────────────────────────────────────────
    print("── TEST 1 — XTE executes ──")
    closes = [100 + i * 0.1 for i in range(40)]
    volumes = [1000 + i for i in range(40)]
    pos = _fake_position()
    res = xte_observer.observe(pos, price=103.0, closes=closes, volumes=volumes,
                               atr_pct=0.9, atr_ema=0.8)
    check("observe() returns a result", res is not None)
    check("result carries a 0-100 score", res is not None and 0.0 <= res.score <= 100.0,
          f"score={getattr(res,'score',None)}")
    check("result carries an advisory", res is not None and hasattr(res, "advisory"))
    check("force_close invariant holds (False)", res is not None and res.force_close is False)
    check("_current_r LONG sign correct", round(_current_r("LONG", 100, 102, 98), 2) == 1.0)
    check("_current_r SHORT sign correct", round(_current_r("SHORT", 100, 98, 102), 2) == 1.0)
    check("_current_r zero-distance guarded", _current_r("LONG", 100, 102, 100) == 0.0)

    # ── TEST 2 — Execution remains untouched ─────────────────────────────────
    print("\n── TEST 2 — Execution remains untouched ──")
    sl_before, tp_before, qty_before = pos.stop_loss, pos.take_profit, pos.qty
    xte_observer.observe(pos, price=104.0, closes=closes, volumes=volumes,
                         atr_pct=1.0, atr_ema=0.8)
    check("observe() did not modify stop_loss", pos.stop_loss == sl_before)
    check("observe() did not modify take_profit", pos.take_profit == tp_before)
    check("observe() did not modify qty", pos.qty == qty_before)
    check("XTE_OBSERVE_ENABLED defaults to False", _default_flag_false())
    check("XTE_FORCE_CLOSE_ENABLED defaults to False", _force_close_default_false())

    # ── TEST 3 — Archive works ───────────────────────────────────────────────
    print("\n── TEST 3 — Observation archive works ──")
    rec = xte_observer.on_close("TESTUSDT", _fake_trade())
    check("on_close() returns a record", rec is not None)
    check("archive file created", os.path.exists(archive))
    rows = xte_observer.read_records()
    check("exactly one record archived", len(rows) == 1, f"got {len(rows)}")
    if rows:
        r = rows[0]
        for key in ("symbol", "regime", "duration_s", "exit_r", "peak_r",
                    "giveback_pct", "profit_capture", "xte_score_last",
                    "xte_advisory_last", "net_pnl"):
            check(f"record has '{key}'", key in r)
        check("giveback_pct computed (peak 1.5, exit 0.6 -> 60%)", r["giveback_pct"] == 60.0,
              f"got {r['giveback_pct']}")
        check("duration_s computed (300s)", r["duration_s"] == 300.0, f"got {r['duration_s']}")
        check("trajectory joined (xte_evals>0)", r["xte_evals"] > 0, f"got {r['xte_evals']}")

    # second close to exercise append + distribution
    pos2 = _fake_position(side="SHORT", entry=100.0, sl=102.0, peak_r=0.8)
    xte_observer.observe(pos2, price=99.0, closes=list(reversed(closes)), volumes=volumes,
                         atr_pct=0.7, atr_ema=0.9)
    xte_observer.on_close("TESTUSDT", _fake_trade(side="SHORT", r_multiple=0.05,
                                                  peak_r=0.8, net_pnl=-0.02))
    check("second record appended", len(xte_observer.read_records()) == 2)

    # ── TEST 4 — Reports generate ────────────────────────────────────────────
    print("\n── TEST 4 — Reports generate correctly ──")
    sections = xte_observer.report_sections()
    for sec in ("header", "score_distribution", "advisory_distribution",
                "giveback_analysis", "xte_vs_actual_exit"):
        check(f"report section '{sec}' present", sec in sections)
    check("header sample_count == 2", sections["header"]["sample_count"] == 2)
    check("giveback_analysis has avg_giveback_pct", "avg_giveback_pct" in sections["giveback_analysis"])
    check("xte_vs_actual_exit is non-empty", len(sections["xte_vs_actual_exit"]) > 0)

    # ── TEST 5 — summary + empty-archive resilience ──────────────────────────
    print("\n── TEST 5 — Summary + resilience ──")
    summ = xte_observer.summary()
    check("summary reports archive_samples == 2", summ["archive_samples"] == 2)
    check("summary exposes observe_enabled flag", "observe_enabled" in summ)
    # empty-archive path returns the no-data note without raising
    cfg.XTE_OBSERVE_ARCHIVE = os.path.join(tmp, "empty.jsonl")
    empty = xte_observer.report_sections()
    check("empty archive handled gracefully", empty["header"]["sample_count"] == 0 and "note" in empty)

    print("\n" + "═" * 60)
    if _FAIL == 0:
        print(f"  ALL {_PASS}/{_PASS} CHECKS PASSED ✓")
        print("  XTE Observer is observation-only and operational.")
        print("═" * 60 + "\n")
        return 0
    print(f"  {_FAIL} CHECK(S) FAILED ({_PASS} passed)")
    print("═" * 60 + "\n")
    return 1


def _default_flag_false() -> bool:
    from config import EngineConfig
    return EngineConfig().XTE_OBSERVE_ENABLED is False


def _force_close_default_false() -> bool:
    from config import EngineConfig
    return EngineConfig().XTE_FORCE_CLOSE_ENABLED is False


if __name__ == "__main__":
    sys.exit(main())
