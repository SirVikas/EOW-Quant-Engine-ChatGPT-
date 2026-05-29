"""
FTD-AIL-001: Report Collector — direct engine object access, no HTTP overhead.
Collects snapshots from live engine globals and returns unified dict.
"""
from __future__ import annotations
import time
from typing import Any


def collect_all() -> dict[str, Any]:
    """
    Collect data from all registered engine sources.
    Imports globals lazily to avoid circular imports at module load.
    Returns mapping: label -> data dict.
    """
    snapshots: dict[str, Any] = {}
    ts = time.time()

    # ── Recovery Cycle Audit ─────────────────────────────────────────────────
    try:
        from core.performance.recovery_audit import get_recovery_cycle_audit  # type: ignore
        snapshots["Recovery Cycle Audit"] = get_recovery_cycle_audit()
    except Exception as exc:
        snapshots["Recovery Cycle Audit"] = {"error": str(exc), "_ts": ts}

    # ── Breakeven Impact Audit ────────────────────────────────────────────────
    try:
        from core.performance.breakeven_audit import get_breakeven_impact_audit  # type: ignore
        snapshots["Breakeven Impact Audit"] = get_breakeven_impact_audit()
    except Exception as exc:
        snapshots["Breakeven Impact Audit"] = {"error": str(exc), "_ts": ts}

    # ── Genome Exposure Audit ─────────────────────────────────────────────────
    try:
        from core.genome_engine import GenomeEngine  # type: ignore
        # Access the singleton directly via main globals if available
        import main as _main  # type: ignore
        g = getattr(_main, "genome", None)
        if g is not None:
            dna = getattr(g, "active_dna", {})
            activated = sum(v.get("activated", 0) for v in dna.values() if isinstance(v, dict))
            executed  = sum(v.get("executed", 0)  for v in dna.values() if isinstance(v, dict))
            snapshots["Genome Exposure Audit"] = {
                "active_strategies": list(dna.keys()),
                "activated": activated,
                "executed": executed,
                "execution_rate": executed / activated if activated else 0.0,
                "_ts": ts,
            }
        else:
            snapshots["Genome Exposure Audit"] = {"error": "genome not available", "_ts": ts}
    except Exception as exc:
        snapshots["Genome Exposure Audit"] = {"error": str(exc), "_ts": ts}

    # ── Promotion Watch ───────────────────────────────────────────────────────
    try:
        import main as _main  # type: ignore
        pc = getattr(_main, "pnl_calc", None)
        if pc is not None:
            trades = getattr(pc, "trades", [])
            promoted = sum(1 for t in trades if getattr(t, "be_triggered", False))
            snapshots["Promotion Watch"] = {
                "total_trades": len(trades),
                "total_promoted": promoted,
                "total_cycles": len(trades),
                "_ts": ts,
            }
        else:
            snapshots["Promotion Watch"] = {"error": "pnl_calc not available", "_ts": ts}
    except Exception as exc:
        snapshots["Promotion Watch"] = {"error": str(exc), "_ts": ts}

    # ── Alpha Confirmation ────────────────────────────────────────────────────
    try:
        from core.alpha_confirmation.alpha_confirmation_orchestrator import get_alpha_health  # type: ignore
        snapshots["Alpha Confirmation"] = get_alpha_health()
    except Exception as exc:
        snapshots["Alpha Confirmation"] = {"error": str(exc), "_ts": ts}

    # ── Equilibrium ──────────────────────────────────────────────────────────
    try:
        from core.adaptive_equilibrium.adaptive_equilibrium_orchestrator import get_equilibrium_health  # type: ignore
        snapshots["Equilibrium"] = get_equilibrium_health()
    except Exception as exc:
        snapshots["Equilibrium"] = {"error": str(exc), "_ts": ts}

    # ── Continuity ───────────────────────────────────────────────────────────
    try:
        from core.institutional_continuity.continuity_evolution_orchestrator import get_continuity_health  # type: ignore
        import main as _main  # type: ignore
        pc = getattr(_main, "pnl_calc", None)
        dl = getattr(_main, "data_lake", None)
        trades: list = []
        if pc:
            from dataclasses import asdict
            trades = [asdict(t) for t in getattr(pc, "trades", [])]
        if dl:
            from dataclasses import asdict as _asdict
            seen = {t.get("trade_id"): t for t in trades if t.get("trade_id")}
            for t in dl.get_trades(limit=500):
                if t.get("trade_id") not in seen:
                    seen[t["trade_id"]] = t
            trades = list(seen.values())
        snapshots["Continuity"] = get_continuity_health(trades)
    except Exception as exc:
        snapshots["Continuity"] = {"error": str(exc), "_ts": ts}

    # ── Observability ─────────────────────────────────────────────────────────
    try:
        from core.observability.orchestrator import obs_orchestrator  # type: ignore
        result = obs_orchestrator.latest_result
        if result is not None:
            snapshots["Observability"] = {
                "tick_id": result.tick_id,
                "anomaly_count": result.anomaly_count,
                "worst_severity": result.worst_severity,
                "_ts": ts,
            }
        else:
            snapshots["Observability"] = {"status": "no_data", "_ts": ts}
    except Exception as exc:
        snapshots["Observability"] = {"error": str(exc), "_ts": ts}

    # ── Auto Intelligence State ───────────────────────────────────────────────
    try:
        import main as _main  # type: ignore
        ai = getattr(_main, "_auto_intelligence", None)
        if ai is not None:
            snapshots["Auto Intelligence State"] = {
                "cycle_num": getattr(ai, "_cycle_num", 0),
                "last_action": getattr(ai, "_last_action", None),
                "_ts": ts,
            }
        else:
            snapshots["Auto Intelligence State"] = {"status": "not_initialized", "_ts": ts}
    except Exception as exc:
        snapshots["Auto Intelligence State"] = {"error": str(exc), "_ts": ts}

    # ── Performance Status ────────────────────────────────────────────────────
    try:
        import main as _main  # type: ignore
        pc = getattr(_main, "pnl_calc", None)
        if pc is not None:
            stats = getattr(pc, "session_stats", {})
            trades = getattr(pc, "trades", [])
            wins = [t for t in trades if getattr(t, "pnl", 0) > 0]
            losses = [t for t in trades if getattr(t, "pnl", 0) < 0]
            win_rmults = [getattr(t, "r_multiple", 0) for t in wins if getattr(t, "r_multiple", 0) > 0]
            loss_rmults = [abs(getattr(t, "r_multiple", 0)) for t in losses if getattr(t, "r_multiple", 0) < 0]
            avg_win_run  = sum(win_rmults) / len(win_rmults) if win_rmults else 0.0
            avg_loss_run = sum(loss_rmults) / len(loss_rmults) if loss_rmults else 0.0
            snapshots["Performance Status"] = {
                "win_rate": stats.get("win_rate", 0.0),
                "total_trades": len(trades),
                "avg_win_run": avg_win_run,
                "avg_loss_run": avg_loss_run,
                "peak_r_trades": len([t for t in trades if getattr(t, "r_multiple", 0) >= 1.0]),
                "_ts": ts,
            }
        else:
            snapshots["Performance Status"] = {"error": "pnl_calc not available", "_ts": ts}
    except Exception as exc:
        snapshots["Performance Status"] = {"error": str(exc), "_ts": ts}

    return snapshots
