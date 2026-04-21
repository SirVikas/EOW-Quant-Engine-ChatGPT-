#!/usr/bin/env python3
"""Pipeline break forensic probe for Phase 6.6/7A gating stack.

Runs a controlled in-process probe and emits machine-readable JSON so results
can be reviewed without committing generated snapshots to git.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gating.gate_logger import gate_logger
from core.orchestrator.execution_orchestrator import TickContext, execution_orchestrator
from core.gating.global_gate_controller import global_gate_controller
from core.gating.safe_mode_engine import safe_mode_engine


def _db_snapshot(db_path: Path) -> dict:
    if not db_path.exists():
        return {"db_exists": False}
    out: dict = {"db_exists": True, "db_path": str(db_path)}
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM trades")
        out["trade_count"] = cur.fetchone()[0]
        cur.execute("SELECT MIN(ts), MAX(ts) FROM trades")
        out["trade_ts_min"], out["trade_ts_max"] = cur.fetchone()
        cur.execute("SELECT trade_id, symbol, data, ts FROM trades ORDER BY ts DESC LIMIT 3")
        recent = []
        for trade_id, symbol, data, ts in cur.fetchall():
            payload = json.loads(data)
            recent.append(
                {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "ts": ts,
                    "strategy_id": payload.get("strategy_id"),
                    "side": payload.get("side"),
                    "net_pnl": payload.get("net_pnl"),
                }
            )
        out["recent_trades"] = recent
    finally:
        con.close()
    return out


def run_probe(cycles: int = 100, symbol: str = "BTCUSDT", strategy: str = "TrendFollowing") -> dict:
    gate_reason_counts: Counter[str] = Counter()
    scan_reason_counts: Counter[str] = Counter()  # Derived from gate_check action.
    gate_action_counts: Counter[str] = Counter()
    gate_open = 0
    gate_blocked = 0

    for _ in range(cycles):
        gc = execution_orchestrator.gate_check(
            symbol=symbol,
            strategy=strategy,
            indicator_ok=True,
            data_fresh=True,
        )
        gate_action_counts[gc.action] += 1
        if gc.allowed:
            gate_open += 1
            scan_reason_counts["SCAN_OK"] += 1
        else:
            gate_blocked += 1
            if gc.action == "SCAN_BLOCKED":
                scan_reason_counts[gc.reason] += 1
            else:
                scan_reason_counts["NO_SCAN:GATE_BLOCKED"] += 1
        gate_reason_counts[gc.reason] += 1

    ctx = TickContext(
        symbol=symbol,
        price=100.0,
        regime="TRENDING",
        strategy=strategy,
        ev=0.12,
        trade_score=0.73,
        volume_ratio=1.15,
        equity=1000.0,
        base_risk_usdt=10.0,
        upstream_mult=1.0,
        indicator_ok=True,
        data_fresh=True,
        is_exploration=False,
    )
    cycle = execution_orchestrator.run_cycle(ctx)

    return {
        "cycles": cycles,
        "gate_open": gate_open,
        "gate_blocked": gate_blocked,
        "gate_action_counts": dict(gate_action_counts),
        "gate_reason_counts": dict(gate_reason_counts),
        "scan_reason_counts": dict(scan_reason_counts),
        "gate_summary": global_gate_controller.summary(),
        "safe_mode_summary": safe_mode_engine.summary(),
        "gate_logger_summary": gate_logger.summary(),
        "sample_run_cycle": {
            "action": cycle.action,
            "execute": cycle.execute,
            "reason": cycle.reason,
            "gate_status": cycle.gate_status,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run gate/scan/execution forensic probe")
    parser.add_argument("--cycles", type=int, default=100, help="Number of pre-gate cycles")
    parser.add_argument("--symbol", default="BTCUSDT", help="Symbol for probe context")
    parser.add_argument("--strategy", default="TrendFollowing", help="Strategy for probe context")
    parser.add_argument("--include-db", action="store_true", help="Attach sqlite trade snapshot")
    parser.add_argument("--db-path", default="data/eow_lake.db", help="SQLite DB path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    out = run_probe(cycles=args.cycles, symbol=args.symbol, strategy=args.strategy)
    if args.include_db:
        out["db_snapshot"] = _db_snapshot(Path(args.db_path))

    if args.pretty:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(json.dumps(out, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
