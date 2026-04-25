#!/usr/bin/env python3
"""
FTD-031C — Pipeline Break Forensic Probe

CLASSIFICATION: Diagnostic Tool (NOT core system)

ISOLATION RULES (FTD-031C mandatory):
  ✔ Manual trigger only — never auto-executed
  ✔ NOT part of main execution loop
  ✔ NOT imported by any core module
  ✔ Does NOT modify system state
  ✔ Does NOT affect latency or performance

USAGE:
  python tools/diagnostics/pipeline_break_forensics.py
  OR via /api/diagnostics/pipeline-break-forensics (disabled by default in cfg)

PURPOSE: debugging, pipeline break analysis, developer support
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.gating.gate_logger import gate_logger
from core.gating.global_gate_controller import global_gate_controller
from core.gating.safe_mode_engine import safe_mode_engine
from core.orchestrator.execution_orchestrator import TickContext, execution_orchestrator
from core.profit.scan_controller import scan_controller


def run_probe(cycles: int = 100) -> dict:
    """
    Run a controlled in-process probe of the Phase 6.6/7A gating stack.

    Returns evidence dict required by incident triage.
    Does NOT modify any system state — read-only diagnostic.
    """
    gate_reason_counts: Counter[str] = Counter()
    scan_reason_counts: Counter[str] = Counter()
    gate_open = 0
    gate_blocked = 0

    for _ in range(cycles):
        gc = execution_orchestrator.gate_check(
            symbol="BTCUSDT",
            strategy="TrendFollowing",
            indicator_ok=True,
            data_fresh=True,
        )
        if gc.allowed:
            gate_open += 1
        else:
            gate_blocked += 1
        gate_reason_counts[gc.reason] += 1

        gd = global_gate_controller.evaluate()
        sd = scan_controller.can_scan(gd)
        scan_reason_counts[sd.reason] += 1

    ctx = TickContext(
        symbol="BTCUSDT",
        price=100.0,
        regime="TRENDING",
        strategy="TrendFollowing",
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
        "gate_reason_counts": dict(gate_reason_counts),
        "scan_reason_counts": dict(scan_reason_counts),
        "gate_summary": global_gate_controller.summary(),
        "scan_summary": scan_controller.summary(),
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
    out = run_probe(100)
    print("=== PIPELINE BREAK FORENSICS ===")
    for k, v in out.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
