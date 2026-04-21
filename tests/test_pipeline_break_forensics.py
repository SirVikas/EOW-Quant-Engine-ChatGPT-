from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

from scripts.pipeline_break_forensics import _db_snapshot, run_probe


def test_db_snapshot_missing(tmp_path: Path):
    out = _db_snapshot(tmp_path / "missing.db")
    assert out == {"db_exists": False}


def test_db_snapshot_reads_recent(tmp_path: Path):
    db = tmp_path / "eow.db"
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute("CREATE TABLE trades (trade_id TEXT, symbol TEXT, data TEXT, ts INTEGER)")
    cur.execute(
        "INSERT INTO trades VALUES (?, ?, ?, ?)",
        ("t1", "BTCUSDT", json.dumps({"strategy_id": "S1", "side": "LONG", "net_pnl": 1.2}), 10),
    )
    cur.execute(
        "INSERT INTO trades VALUES (?, ?, ?, ?)",
        ("t2", "ETHUSDT", json.dumps({"strategy_id": "S2", "side": "SHORT", "net_pnl": -0.3}), 20),
    )
    con.commit()
    con.close()

    out = _db_snapshot(db)
    assert out["db_exists"] is True
    assert out["trade_count"] == 2
    assert out["trade_ts_min"] == 10
    assert out["trade_ts_max"] == 20
    assert out["recent_trades"][0]["trade_id"] == "t2"


def test_run_probe_aggregates_gate_and_cycle():
    gate_seq = [
        SimpleNamespace(allowed=False, action="GATE_BLOCKED", reason="INDICATOR_NOT_READY"),
        SimpleNamespace(allowed=False, action="SCAN_BLOCKED", reason="NO_SCAN:SAFE_MODE"),
        SimpleNamespace(allowed=True, action="ALLOWED", reason="ALL_CLEAR"),
    ]

    class FakeOrchestrator:
        def __init__(self):
            self._i = 0

        def gate_check(self, **kwargs):
            r = gate_seq[self._i]
            self._i += 1
            return r

        def run_cycle(self, ctx):
            return SimpleNamespace(
                action="GATE_BLOCKED",
                execute=False,
                reason="INDICATOR_NOT_READY",
                gate_status={"can_trade": False},
            )

    runtime = {
        "execution_orchestrator": FakeOrchestrator(),
        "TickContext": lambda **kw: SimpleNamespace(**kw),
        "global_gate_controller": SimpleNamespace(summary=lambda: {"gate": "summary"}),
        "safe_mode_engine": SimpleNamespace(summary=lambda: {"safe": "summary"}),
        "gate_logger": SimpleNamespace(summary=lambda: {"log": "summary"}),
    }

    out = run_probe(cycles=3, symbol="BTCUSDT", strategy="TrendFollowing", runtime=runtime)
    assert out["gate_blocked"] == 2
    assert out["gate_open"] == 1
    assert out["gate_action_counts"] == {"GATE_BLOCKED": 1, "SCAN_BLOCKED": 1, "ALLOWED": 1}
    assert out["scan_reason_counts"] == {
        "NO_SCAN:GATE_BLOCKED": 1,
        "NO_SCAN:SAFE_MODE": 1,
        "SCAN_OK": 1,
    }
    assert out["sample_run_cycle"]["execute"] is False
