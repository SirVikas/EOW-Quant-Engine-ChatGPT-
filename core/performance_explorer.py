"""
EOW Quant Engine — Universal Performance Explorer (FTD)

Provides full-spectrum trade performance analysis with:
  - Preset time periods  : 1D / 3D / 7D / 20D / 60D / 100D / 180D / 365D / ALL
  - Custom multi-filters : date range, symbol, strategy, regime, side, RR, PnL
  - Auto-calculated summary panel : PnL, WR, PF, fees, drawdown, Sharpe
  - Visual data builders : equity curve, drawdown series, PnL histogram, R-dist
  - Multi-format export  : CSV, JSON, Markdown  (Excel/PDF via report_generator)
  - State import         : from eow_state_*.json or live PurePnLCalculator
  - Daily auto-backup + manual backup + restore
  - AI pattern learning  : winning/losing pattern extraction + actionable insights
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import statistics
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger


# ─────────────────────────────────────────────────────────────────────────────
# Part 1 — Trade Record
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TradeRecord:
    trade_id:      str
    symbol:        str
    side:          str
    strategy_id:   str
    regime:        str
    order_type:    str
    entry_price:   float
    exit_price:    float
    qty:           float
    gross_pnl:     float
    fee_entry:     float
    fee_exit:      float
    slippage_cost: float
    net_pnl:       float
    net_pnl_pct:   float
    r_multiple:    float
    entry_ts:      int
    exit_ts:       int
    mode:          str = "PAPER"

    @property
    def fees(self) -> float:
        return self.fee_entry + self.fee_exit

    @property
    def is_win(self) -> bool:
        return self.net_pnl > 0

    @property
    def exit_dt(self) -> datetime:
        return datetime.fromtimestamp(self.exit_ts / 1000, tz=timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# Part 2 — Preset System
# ─────────────────────────────────────────────────────────────────────────────

PRESETS: Dict[str, Optional[int]] = {
    "1D":   1,
    "3D":   3,
    "7D":   7,
    "20D":  20,
    "60D":  60,
    "100D": 100,
    "180D": 180,
    "365D": 365,
    "ALL":  None,
}


# ─────────────────────────────────────────────────────────────────────────────
# Part 3 — Filter Engine
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TradeFilter:
    """Multi-dimensional filter. All None fields are pass-through."""
    date_from:  Optional[datetime] = None
    date_to:    Optional[datetime] = None
    symbols:    Optional[List[str]] = None
    strategies: Optional[List[str]] = None
    regimes:    Optional[List[str]] = None
    sides:      Optional[List[str]] = None
    win_only:   bool = False
    loss_only:  bool = False
    rr_min:     Optional[float] = None
    rr_max:     Optional[float] = None
    pnl_min:    Optional[float] = None
    pnl_max:    Optional[float] = None

    def apply(self, trades: List[TradeRecord]) -> List[TradeRecord]:
        result = []
        for t in trades:
            if self.date_from and t.exit_dt < self.date_from:
                continue
            if self.date_to and t.exit_dt > self.date_to:
                continue
            if self.symbols and t.symbol not in self.symbols:
                continue
            if self.strategies and t.strategy_id not in self.strategies:
                continue
            if self.regimes and t.regime not in self.regimes:
                continue
            if self.sides and t.side not in self.sides:
                continue
            if self.win_only and not t.is_win:
                continue
            if self.loss_only and t.is_win:
                continue
            if self.rr_min is not None and t.r_multiple < self.rr_min:
                continue
            if self.rr_max is not None and t.r_multiple > self.rr_max:
                continue
            if self.pnl_min is not None and t.net_pnl < self.pnl_min:
                continue
            if self.pnl_max is not None and t.net_pnl > self.pnl_max:
                continue
            result.append(t)
        return result


def preset_filter(preset: str) -> TradeFilter:
    days = PRESETS.get(preset.upper())
    if days is None:
        return TradeFilter()
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    return TradeFilter(date_from=cutoff)


# ─────────────────────────────────────────────────────────────────────────────
# Part 4 — Summary Panel
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SummaryPanel:
    total_trades:   int
    wins:           int
    losses:         int
    win_rate:       float
    net_pnl:        float
    gross_pnl:      float
    total_fees:     float
    total_slippage: float
    profit_factor:  float
    avg_win:        float
    avg_loss:       float
    avg_rr:         float
    max_drawdown:   float
    sharpe:         float
    cost_pct:       float
    fee_drag:       float
    by_strategy:    Dict[str, Dict] = field(default_factory=dict)
    by_regime:      Dict[str, Dict] = field(default_factory=dict)
    by_symbol:      Dict[str, float] = field(default_factory=dict)


def _max_drawdown(equity_curve: List[float]) -> float:
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 4)


def _sharpe(pnl_list: List[float]) -> float:
    if len(pnl_list) < 2:
        return 0.0
    mean = statistics.mean(pnl_list)
    std  = statistics.stdev(pnl_list)
    if std == 0:
        return 0.0
    result = mean / std * math.sqrt(252)
    return 0.0 if (math.isnan(result) or math.isinf(result)) else round(result, 3)


def compute_summary(
    trades: List[TradeRecord],
    initial_capital: float = 1000.0,
) -> SummaryPanel:
    if not trades:
        return SummaryPanel(
            total_trades=0, wins=0, losses=0, win_rate=0.0, net_pnl=0.0,
            gross_pnl=0.0, total_fees=0.0, total_slippage=0.0,
            profit_factor=0.0, avg_win=0.0, avg_loss=0.0, avg_rr=0.0,
            max_drawdown=0.0, sharpe=0.0, cost_pct=0.0, fee_drag=0.0,
        )

    pnls       = [t.net_pnl for t in trades]
    wins       = [t.net_pnl for t in trades if t.is_win]
    losses     = [t.net_pnl for t in trades if not t.is_win]
    gross_wins = [t.gross_pnl for t in trades if t.gross_pnl > 0]
    gross_loss = [abs(t.gross_pnl) for t in trades if t.gross_pnl <= 0]

    total_net  = sum(pnls)
    total_fees = sum(t.fees for t in trades)
    total_slip = sum(t.slippage_cost for t in trades)
    gross_pnl  = sum(t.gross_pnl for t in trades)

    pf = (sum(gross_wins) / sum(gross_loss)) if gross_loss else (99.99 if gross_wins else 0.0)

    eq = initial_capital
    curve = [eq]
    for t in trades:
        eq += t.net_pnl
        curve.append(eq)

    gross_profit = sum(t.gross_pnl for t in trades if t.gross_pnl > 0)
    cost_pct = (total_fees / gross_profit * 100) if gross_profit > 0 else 0.0
    fee_drag = (total_fees / abs(total_net) * 100) if total_net != 0 else 0.0

    by_strat: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "wins": 0, "net_pnl": 0.0, "fees": 0.0})
    for t in trades:
        s = by_strat[t.strategy_id]
        s["count"]   += 1
        s["wins"]    += 1 if t.is_win else 0
        s["net_pnl"] += t.net_pnl
        s["fees"]    += t.fees
    for v in by_strat.values():
        v["win_rate"] = round(v["wins"] / v["count"] * 100, 1) if v["count"] else 0
        v["net_pnl"]  = round(v["net_pnl"], 4)
        v["fees"]     = round(v["fees"], 4)

    by_regime: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "wins": 0, "net_pnl": 0.0})
    for t in trades:
        r = by_regime[t.regime]
        r["count"]   += 1
        r["wins"]    += 1 if t.is_win else 0
        r["net_pnl"] += t.net_pnl
    for v in by_regime.values():
        v["win_rate"] = round(v["wins"] / v["count"] * 100, 1) if v["count"] else 0
        v["net_pnl"]  = round(v["net_pnl"], 4)

    sym_pnl: Dict[str, float] = defaultdict(float)
    for t in trades:
        sym_pnl[t.symbol] += t.net_pnl
    sym_sorted = dict(sorted(sym_pnl.items(), key=lambda x: x[1]))

    return SummaryPanel(
        total_trades   = len(trades),
        wins           = len(wins),
        losses         = len(losses),
        win_rate       = round(len(wins) / len(trades) * 100, 2),
        net_pnl        = round(total_net, 4),
        gross_pnl      = round(gross_pnl, 4),
        total_fees     = round(total_fees, 4),
        total_slippage = round(total_slip, 4),
        profit_factor  = round(pf, 3),
        avg_win        = round(statistics.mean(wins),   4) if wins   else 0.0,
        avg_loss       = round(statistics.mean(losses), 4) if losses else 0.0,
        avg_rr         = round(statistics.mean([t.r_multiple for t in trades]), 4),
        max_drawdown   = _max_drawdown(curve),
        sharpe         = _sharpe(pnls),
        cost_pct       = round(cost_pct, 2),
        fee_drag       = round(fee_drag, 2),
        by_strategy    = dict(by_strat),
        by_regime      = dict(by_regime),
        by_symbol      = {k: round(v, 4) for k, v in sym_sorted.items()},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Part 5 — Visual Data Builder
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VisualData:
    equity_curve:    List[Dict]
    drawdown_series: List[Dict]
    pnl_histogram:   List[Dict]
    win_loss_dist:   Dict
    rr_distribution: List[Dict]


def build_visual_data(
    trades: List[TradeRecord],
    initial_capital: float = 1000.0,
) -> VisualData:
    if not trades:
        return VisualData([], [], [], {}, [])

    eq = initial_capital
    peak = eq
    equity, dd_ser = [], []
    for t in trades:
        eq   += t.net_pnl
        peak  = max(peak, eq)
        dd    = (peak - eq) / peak * 100 if peak > 0 else 0.0
        equity.append({"ts": t.exit_ts, "equity": round(eq, 4), "symbol": t.symbol})
        dd_ser.append({"ts": t.exit_ts, "drawdown_pct": round(dd, 4)})

    pnls = [t.net_pnl for t in trades]
    mn, mx = min(pnls), max(pnls)
    if mx == mn:
        hist = [{"bucket_center": round(mn, 4), "count": len(pnls)}]
    else:
        n_b   = min(20, len(pnls))
        width = (mx - mn) / n_b
        bkts: Dict[int, int] = defaultdict(int)
        for p in pnls:
            bkts[min(int((p - mn) / width), n_b - 1)] += 1
        hist = [
            {"bucket_center": round(mn + (i + 0.5) * width, 4), "count": bkts[i]}
            for i in range(n_b)
        ]

    rrs = [t.r_multiple for t in trades]
    rmn, rmx = min(rrs), max(rrs)
    if rmx == rmn:
        rr_dist = [{"bucket_center": round(rmn, 4), "count": len(rrs)}]
    else:
        n_b = min(10, len(rrs))
        rw  = (rmx - rmn) / n_b
        rb: Dict[int, int] = defaultdict(int)
        for r in rrs:
            rb[min(int((r - rmn) / rw), n_b - 1)] += 1
        rr_dist = [
            {"bucket_center": round(rmn + (i + 0.5) * rw, 4), "count": rb[i]}
            for i in range(n_b)
        ]

    return VisualData(
        equity_curve    = equity,
        drawdown_series = dd_ser,
        pnl_histogram   = hist,
        win_loss_dist   = {
            "wins":      sum(1 for t in trades if t.net_pnl > 0),
            "losses":    sum(1 for t in trades if t.net_pnl < 0),
            "breakeven": sum(1 for t in trades if t.net_pnl == 0),
        },
        rr_distribution = rr_dist,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Part 6 — Export Engine
# ─────────────────────────────────────────────────────────────────────────────

class ExportEngine:

    _TRADE_FIELDS = [
        "trade_id", "symbol", "side", "strategy_id", "regime", "order_type",
        "entry_price", "exit_price", "qty", "gross_pnl", "fee_entry", "fee_exit",
        "slippage_cost", "net_pnl", "net_pnl_pct", "r_multiple", "entry_ts", "exit_ts",
    ]

    @staticmethod
    def to_csv(trades: List[TradeRecord]) -> str:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=ExportEngine._TRADE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for t in trades:
            writer.writerow(asdict(t))
        return buf.getvalue()

    @staticmethod
    def to_json(trades: List[TradeRecord], summary: SummaryPanel) -> str:
        return json.dumps(
            {
                "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "summary":     asdict(summary),
                "trades":      [asdict(t) for t in trades],
            },
            indent=2,
            default=str,
        )

    @staticmethod
    def to_markdown(
        trades:  List[TradeRecord],
        summary: SummaryPanel,
        preset:  str = "ALL",
    ) -> str:
        now = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
        lines = [
            "# Universal Performance Explorer",
            "",
            f"**Period:** `{preset}`  |  **Generated:** {now}",
            "",
            "---",
            "",
            "## Summary Panel",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| Total Trades | {summary.total_trades} |",
            f"| Wins / Losses | {summary.wins} / {summary.losses} |",
            f"| Win Rate | {summary.win_rate:.1f}% |",
            f"| Net PnL | {summary.net_pnl:+.4f} USDT |",
            f"| Gross PnL | {summary.gross_pnl:+.4f} USDT |",
            f"| Total Fees | {summary.total_fees:.4f} USDT |",
            f"| Fee Cost % | {summary.cost_pct:.1f}% of gross profit |",
            f"| Fee Drag | {summary.fee_drag:.1f}% of |net PnL| |",
            f"| Profit Factor | {summary.profit_factor:.3f} |",
            f"| Avg Win | {summary.avg_win:+.4f} USDT |",
            f"| Avg Loss | {summary.avg_loss:+.4f} USDT |",
            f"| Avg R-Multiple | {summary.avg_rr:+.4f} |",
            f"| Max Drawdown | {summary.max_drawdown:.2f}% |",
            f"| Sharpe | {summary.sharpe:.3f} |",
            "",
            "## Strategy Breakdown",
            "",
            "| Strategy | Trades | WR% | Net PnL | Fees |",
            "|---|---|---|---|---|",
        ]
        for strat, v in sorted(summary.by_strategy.items()):
            lines.append(
                f"| {strat} | {v['count']} | {v['win_rate']}% | "
                f"{v['net_pnl']:+.4f} | {v['fees']:.4f} |"
            )
        lines += [
            "",
            "## Regime Breakdown",
            "",
            "| Regime | Trades | WR% | Net PnL |",
            "|---|---|---|---|",
        ]
        for reg, v in sorted(summary.by_regime.items()):
            lines.append(
                f"| {reg} | {v['count']} | {v['win_rate']}% | {v['net_pnl']:+.4f} |"
            )
        lines += [
            "",
            "## Symbol PnL (worst → best)",
            "",
            "| Symbol | Net PnL |",
            "|---|---|",
        ]
        for sym, pnl in list(summary.by_symbol.items())[:30]:
            lines.append(f"| {sym} | {pnl:+.4f} |")
        lines += [
            "",
            "## Trade Table (last 50)",
            "",
            "| Date | Symbol | Side | Strategy | Net PnL | Fees | R |",
            "|---|---|---|---|---|---|---|",
        ]
        for t in trades[-50:]:
            dt = t.exit_dt.strftime("%Y-%m-%d %H:%M")
            lines.append(
                f"| {dt} | {t.symbol} | {t.side} | {t.strategy_id} | "
                f"{t.net_pnl:+.4f} | {t.fees:.4f} | {t.r_multiple:.3f} |"
            )
        lines += ["", "---", "*EOW Universal Performance Explorer*"]
        return "\n".join(lines)

    @staticmethod
    def save(content: "str | bytes", path: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        enc  = {} if isinstance(content, bytes) else {"encoding": "utf-8"}
        with open(path, mode, **enc) as f:
            f.write(content)
        logger.info(f"[UPE] Exported → {path}")
        return path


# ─────────────────────────────────────────────────────────────────────────────
# Part 7 — Import Engine
# ─────────────────────────────────────────────────────────────────────────────

def _raw_to_record(t: dict) -> Optional[TradeRecord]:
    try:
        symbol = t.get("symbol") or ""
        side   = t.get("side")   or ""
        if not symbol or not side:
            raise ValueError(f"Missing required fields: symbol={symbol!r} side={side!r}")
        return TradeRecord(
            trade_id      = t.get("trade_id", ""),
            symbol        = symbol,
            side          = side,
            strategy_id   = t.get("strategy_id", "unknown"),
            regime        = t.get("regime", "unknown"),
            order_type    = t.get("order_type", "LIMIT"),
            entry_price   = float(t.get("entry_price", 0)),
            exit_price    = float(t.get("exit_price", 0)),
            qty           = float(t.get("qty", 0)),
            gross_pnl     = float(t.get("gross_pnl", 0)),
            fee_entry     = float(t.get("fee_entry", 0)),
            fee_exit      = float(t.get("fee_exit", 0)),
            slippage_cost = float(t.get("slippage_cost", 0)),
            net_pnl       = float(t.get("net_pnl", 0)),
            net_pnl_pct   = float(t.get("net_pnl_pct", 0)),
            r_multiple    = float(t.get("r_multiple", 0)),
            entry_ts      = int(t.get("entry_ts", 0)),
            exit_ts       = int(t.get("exit_ts", 0)),
            mode          = t.get("mode", "PAPER"),
        )
    except Exception as exc:
        logger.warning(f"[UPE] Skipping malformed trade: {exc}")
        return None


def load_trades_from_state(path: str) -> List[TradeRecord]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = [r for t in data.get("trade_history", []) if (r := _raw_to_record(t))]
    logger.info(f"[UPE] Loaded {len(records)} trades from {path}")
    return records


def load_trades_from_pnl_calc(pnl_calc: Any) -> List[TradeRecord]:
    records = []
    for t in pnl_calc.trades:
        d = asdict(t) if hasattr(t, "__dataclass_fields__") else vars(t)
        if r := _raw_to_record(d):
            records.append(r)
    return records


# ─────────────────────────────────────────────────────────────────────────────
# Part 8 — Backup / Restore Manager
# ─────────────────────────────────────────────────────────────────────────────

class BackupManager:

    def __init__(self, backup_dir: str = "data/backups"):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup(self, trades: List[TradeRecord], label: str = "auto") -> str:
        ts   = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        path = os.path.join(self.backup_dir, f"upe_backup_{ts}_{label}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"backup_ts": ts, "label": label, "trade_count": len(trades),
                 "trades": [asdict(t) for t in trades]},
                f, indent=2, default=str,
            )
        logger.success(f"[UPE Backup] Saved {len(trades)} trades → {path}")
        return path

    def restore(self, path: str) -> List[TradeRecord]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = [r for t in data.get("trades", []) if (r := _raw_to_record(t))]
        logger.success(f"[UPE Backup] Restored {len(records)} trades from {path}")
        return records

    def list_backups(self) -> List[str]:
        try:
            files = sorted(
                [f for f in os.listdir(self.backup_dir) if f.startswith("upe_backup_")],
                reverse=True,
            )
            return [os.path.join(self.backup_dir, f) for f in files]
        except FileNotFoundError:
            return []

    def latest_backup(self) -> Optional[str]:
        bkps = self.list_backups()
        return bkps[0] if bkps else None

    def auto_backup_if_needed(self, trades: List[TradeRecord]) -> Optional[str]:
        today = time.strftime("%Y%m%d", time.gmtime())
        for b in self.list_backups():
            if today in b and "_auto" in b:
                return None
        return self.backup(trades, label="auto")


# ─────────────────────────────────────────────────────────────────────────────
# Part 9 — AI Pattern Engine
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PatternInsight:
    pattern_type: str
    description:  str
    severity:     str
    action:       str
    evidence:     Dict


def extract_insights(
    summary: SummaryPanel,
    trades:  List[TradeRecord],
) -> List[PatternInsight]:
    insights: List[PatternInsight] = []

    if summary.profit_factor < 1.0:
        rr = round(abs(summary.avg_win / summary.avg_loss), 3) if summary.avg_loss else 0
        insights.append(PatternInsight(
            pattern_type = "losing_pattern",
            description  = f"Negative expectancy: PF={summary.profit_factor:.3f}, RR={rr}",
            severity     = "CRITICAL",
            action       = "Widen RR target to ≥1.5R; tighten entry score threshold",
            evidence     = {
                "profit_factor": summary.profit_factor,
                "avg_win":       summary.avg_win,
                "avg_loss":      summary.avg_loss,
                "rr_ratio":      rr,
            },
        ))

    if summary.cost_pct > 15:
        insights.append(PatternInsight(
            pattern_type = "cost_pattern",
            description  = f"Fee drag = {summary.cost_pct:.1f}% of gross profit",
            severity     = "CRITICAL" if summary.cost_pct > 20 else "WARNING",
            action       = "Increase min trade size; reduce low-conviction trade frequency",
            evidence     = {
                "total_fees":        summary.total_fees,
                "gross_pnl":         summary.gross_pnl,
                "cost_pct":          summary.cost_pct,
                "avg_fee_per_trade": round(
                    summary.total_fees / summary.total_trades, 4
                ) if summary.total_trades else 0,
            },
        ))

    for strat, v in summary.by_strategy.items():
        if v["count"] >= 5 and v["net_pnl"] < -5:
            insights.append(PatternInsight(
                pattern_type = "losing_pattern",
                description  = f"{strat} destroying capital: PnL={v['net_pnl']:.2f} USDT",
                severity     = "CRITICAL" if v["net_pnl"] < -20 else "WARNING",
                action       = f"Disable {strat} until PF≥1.2 and WR≥55%",
                evidence     = dict(v, strategy=strat),
            ))

    for strat, v in summary.by_strategy.items():
        if v["count"] >= 3 and v["win_rate"] > 55 and v["net_pnl"] > 0:
            insights.append(PatternInsight(
                pattern_type = "winning_pattern",
                description  = f"{strat} is profitable: WR={v['win_rate']}%, PnL={v['net_pnl']:+.2f}",
                severity     = "INFO",
                action       = f"Scale up {strat} allocation",
                evidence     = dict(v, strategy=strat),
            ))

    for reg, v in summary.by_regime.items():
        if v["count"] >= 5 and v["net_pnl"] < -10:
            insights.append(PatternInsight(
                pattern_type = "losing_pattern",
                description  = f"Regime {reg} consistently unprofitable: PnL={v['net_pnl']:.2f}",
                severity     = "WARNING",
                action       = f"Raise score threshold in {reg} regime; reduce size",
                evidence     = dict(v, regime=reg),
            ))

    worst_syms = [(sym, pnl) for sym, pnl in summary.by_symbol.items() if pnl < -5][:5]
    if worst_syms:
        insights.append(PatternInsight(
            pattern_type = "losing_pattern",
            description  = f"Toxic symbols: {[s for s, _ in worst_syms]}",
            severity     = "WARNING",
            action       = "Blacklist or reduce weight for toxic symbols",
            evidence     = {sym: pnl for sym, pnl in worst_syms},
        ))

    return insights


# ─────────────────────────────────────────────────────────────────────────────
# Parts 10-13 — Universal Performance Explorer (main class)
# ─────────────────────────────────────────────────────────────────────────────

class PerformanceExplorer:
    """
    Universal Performance Explorer — main entry point.

    Quick start:
        upe = PerformanceExplorer.from_state_file("eow_state_1234.json")
        report = upe.explore(preset="7D")
        upe.save_report(report, formats=["md", "json", "csv"])
    """

    EXPORT_DIR = "reports/upe"
    BACKUP_DIR = "data/backups"

    def __init__(
        self,
        trades:          List[TradeRecord],
        initial_capital: float = 1000.0,
    ):
        self._trades          = trades
        self._initial_capital = initial_capital
        self._backup          = BackupManager(self.BACKUP_DIR)
        self._backup.auto_backup_if_needed(trades)

    # ── Constructors ──────────────────────────────────────────────────────────

    @classmethod
    def from_state_file(
        cls,
        path:            str,
        initial_capital: float = 1000.0,
    ) -> "PerformanceExplorer":
        return cls(load_trades_from_state(path), initial_capital)

    @classmethod
    def from_pnl_calc(
        cls,
        pnl_calc:        Any,
        initial_capital: float = 1000.0,
    ) -> "PerformanceExplorer":
        return cls(load_trades_from_pnl_calc(pnl_calc), initial_capital)

    # ── Core API ──────────────────────────────────────────────────────────────

    def explore(
        self,
        preset:        str = "ALL",
        custom_filter: Optional[TradeFilter] = None,
    ) -> Dict[str, Any]:
        flt     = custom_filter or preset_filter(preset)
        trades  = flt.apply(self._trades)
        summary = compute_summary(trades, self._initial_capital)
        visuals = build_visual_data(trades, self._initial_capital)
        insights = extract_insights(summary, trades)

        return {
            "preset":      preset,
            "filter":      asdict(flt) if custom_filter else {"preset": preset},
            "trade_count": len(trades),
            "summary":     asdict(summary),
            "visuals": {
                "equity_curve":    visuals.equity_curve[-200:],
                "drawdown_series": visuals.drawdown_series[-200:],
                "pnl_histogram":   visuals.pnl_histogram,
                "win_loss_dist":   visuals.win_loss_dist,
                "rr_distribution": visuals.rr_distribution,
            },
            "insights": [asdict(i) for i in insights],
            "trades":   [asdict(t) for t in trades],
        }

    def explore_all_presets(self) -> Dict[str, Dict]:
        return {p: self.explore(preset=p) for p in PRESETS}

    def get_trade_table(
        self,
        preset:        str = "ALL",
        custom_filter: Optional[TradeFilter] = None,
    ) -> List[Dict]:
        flt = custom_filter or preset_filter(preset)
        return [asdict(t) for t in flt.apply(self._trades)]

    def get_insights(self, preset: str = "ALL") -> List[Dict]:
        return self.explore(preset=preset)["insights"]

    # ── Export ────────────────────────────────────────────────────────────────

    def save_report(
        self,
        report:     Dict,
        output_dir: Optional[str] = None,
        formats:    List[str] = None,
    ) -> Dict[str, str]:
        if formats is None:
            formats = ["md", "json", "csv"]
        out_dir = output_dir or self.EXPORT_DIR
        preset  = report.get("preset", "ALL")
        ts_tag  = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        prefix  = f"upe_{preset}_{ts_tag}"

        trades  = [TradeRecord(**t) for t in report["trades"]]
        summary = SummaryPanel(**{
            k: v for k, v in report["summary"].items()
            if k in SummaryPanel.__dataclass_fields__
        })

        saved: Dict[str, str] = {}
        for fmt in formats:
            if fmt == "md":
                saved["md"] = ExportEngine.save(
                    ExportEngine.to_markdown(trades, summary, preset),
                    os.path.join(out_dir, f"{prefix}.md"),
                )
            elif fmt == "json":
                saved["json"] = ExportEngine.save(
                    ExportEngine.to_json(trades, summary),
                    os.path.join(out_dir, f"{prefix}.json"),
                )
            elif fmt == "csv":
                saved["csv"] = ExportEngine.save(
                    ExportEngine.to_csv(trades),
                    os.path.join(out_dir, f"{prefix}.csv"),
                )
        return saved

    # ── Backup / Restore ──────────────────────────────────────────────────────

    def manual_backup(self, label: str = "manual") -> str:
        return self._backup.backup(self._trades, label=label)

    def restore_from_backup(self, path: str) -> None:
        self._trades = self._backup.restore(path)

    def list_backups(self) -> List[str]:
        return self._backup.list_backups()
