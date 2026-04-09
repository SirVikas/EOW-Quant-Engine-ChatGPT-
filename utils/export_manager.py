"""
EOW Quant Engine — Export Manager
One-click Full-State Export: strategy DNA + trade history + ratios → .json
Also handles re-import of tuned DNA.
"""
from __future__ import annotations
import json
import time
import os
from dataclasses import asdict
from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from core.pnl_calculator import PurePnLCalculator
    from core.genome_engine  import GenomeEngine
    from core.risk_controller import RiskController


class ExportManager:

    EXPORT_DIR = "data/exports"

    def __init__(
        self,
        pnl_calc:    "PurePnLCalculator",
        genome:      "GenomeEngine",
        risk_ctrl:   "RiskController",
    ):
        self.pnl_calc  = pnl_calc
        self.genome    = genome
        self.risk_ctrl = risk_ctrl
        os.makedirs(self.EXPORT_DIR, exist_ok=True)

    # ── Full State Export ────────────────────────────────────────────────────

    def export(self, label: str = "") -> str:
        """
        Generates a timestamped .json file with complete engine state.
        Returns the file path.
        """
        ts   = int(time.time() * 1000)
        slug = f"eow_state_{ts}" + (f"_{label}" if label else "")
        path = os.path.join(self.EXPORT_DIR, f"{slug}.json")

        stats  = self.pnl_calc.session_stats
        genome = self.genome.export_state()
        risk   = self.risk_ctrl.snapshot()

        # Compute alpha/beta vs BTC buy-and-hold (placeholder — real impl
        # would pull BTCUSDT equity from MarketDataProvider)
        alpha_beta = self.pnl_calc.alpha_beta([])

        payload = {
            "meta": {
                "export_ts":    ts,
                "label":        label or "full_state",
                "trade_mode":   "PAPER",   # from config at runtime
                "engine_ver":   "EOW_QUANT_ENGINE_v1.0",
            },
            "strategy_dna": {
                "active":       genome["active_dna"],
                "active_metrics": genome["active_metrics"],
            },
            "trade_history": [
                {**asdict(t), "ts_human": _ms_to_iso(t.exit_ts)}
                for t in self.pnl_calc.trades
            ],
            "session_stats":  stats,
            "portfolio_ratios": {
                "alpha":        alpha_beta["alpha"],
                "beta":         alpha_beta["beta"],
                "sharpe_ratio": stats.get("sharpe_ratio", 0),
                "max_drawdown": stats.get("max_drawdown_pct", 0),
                "profit_factor":stats.get("profit_factor", 0),
            },
            "risk_snapshot":  risk,
            "genome_log":     genome["recent_genomes"],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        logger.success(f"[EXPORT] 📦 State exported → {path}")
        return path

    # ── DNA Re-import ────────────────────────────────────────────────────────

    def import_dna(self, path: str) -> dict:
        """
        Load a previously exported state file and extract strategy DNA.
        Returns the active DNA dict for re-injection into the Genome Engine.
        """
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        dna = payload.get("strategy_dna", {}).get("active", {})
        logger.info(f"[EXPORT] 📥 Imported DNA from {path}: {list(dna.keys())}")
        return dna

    # ── Latest Export Path ───────────────────────────────────────────────────

    def latest_export_path(self) -> str | None:
        files = sorted(
            [f for f in os.listdir(self.EXPORT_DIR) if f.endswith(".json")],
            reverse=True,
        )
        return os.path.join(self.EXPORT_DIR, files[0]) if files else None


def _ms_to_iso(ts_ms: int) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
