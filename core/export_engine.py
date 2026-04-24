"""
EOW Quant Engine — FTD-025A: System Export Engine (FINAL LAYER)

Purpose
-------
Convert the ENTIRE running system into ONE structured institutional report.
Produces a single ZIP containing:
  • full_system_report_<ts>.md  — full markdown (version-controllable)
  • full_system_report_<ts>.pdf — paginated PDF (client-ready)

Governance
----------
ONE LOGIC → ONE OWNER → MANY USERS
  OWNER:  core.export_engine.SystemExportEngine
  USERS:  main.py ( /api/report/full-system endpoint )
  FTD ID: 025A
  DEPENDS: utils.report_generator._PDFWriter  (re-used, not duplicated)

Report Sections (per master covering letter)
--------------------------------------------
 1. Executive Summary
 2. Performance
 3. Signal Pipeline
 4. Decision Trace
 5. Risk State
 6. Portfolio
 7. AI Brain
 8. Suggestions
 9. Auto-Tuning
10. Evolution
11. Capital
12. Audit
13. Alerts
14. Final Diagnosis
15. Action Checklist
"""
from __future__ import annotations

import io
import time
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from utils.report_generator import _PDFWriter


# ─────────────────────────────────────────────────────────────────────────────
# Data contract
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SystemSnapshot:
    """
    Caller-provided snapshot of all live subsystems. Every field is optional;
    missing data appears as "—" in the report (graceful degradation).

    main.py builds this snapshot by calling .summary() / .snapshot() /
    .export_state() on all running modules.
    """
    # 1. Executive / Performance
    session_stats:      Dict[str, Any] = None
    analytics:          Dict[str, Any] = None
    mode_info:          Dict[str, Any] = None

    # 2. Signal Pipeline & Decision Trace
    thoughts:           List[Dict[str, Any]] = None
    last_skip:          Dict[str, Any] = None
    trade_flow:         Dict[str, Any] = None      # TradeFlowMonitor.summary()

    # 3. Risk & Portfolio
    risk_snapshot:      Dict[str, Any] = None       # RiskController.snapshot()
    positions:          List[Dict[str, Any]] = None
    drawdown:           Dict[str, Any] = None       # drawdown_controller.summary()

    # 4. AI Brain & Evolution
    genome_state:       Dict[str, Any] = None       # genome.export_state()
    learning:           Dict[str, Any] = None       # learning_engine.summary()
    edge:               Dict[str, Any] = None       # edge_engine.summary()
    strategy_usage:     Dict[str, Any] = None       # strategy_engine.usage()
    regime:             Dict[str, Any] = None       # regime_ai latest

    # 5. Suggestions / Auto-Tuning
    ct_scan:            Dict[str, Any] = None       # ct_scan_engine.scan()
    dynamic_thresholds: Dict[str, Any] = None       # dynamic_threshold_provider.summary()
    streak:             Dict[str, Any] = None       # streak_engine.summary()
    capital_allocator:  Dict[str, Any] = None       # capital_allocator.summary()

    # 6. Audit / Alerts
    error_registry:     List[Dict[str, Any]] = None  # error_registry.recent(50)
    healer:             Dict[str, Any] = None        # healer.snapshot()
    halt_audit:         Dict[str, Any] = None

    # 7. Trades
    trades:             List[Dict[str, Any]] = None  # pnl_calc.trades

    # 8. Gate / Pipeline
    gate_status:        Dict[str, Any] = None        # global_gate_controller.snapshot()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_num(v: Any, places: int = 2, signed: bool = False, suffix: str = "") -> str:
    if v is None:
        return "—"
    try:
        f = float(v)
        if signed:
            return f"{f:+,.{places}f}{suffix}"
        return f"{f:,.{places}f}{suffix}"
    except (TypeError, ValueError):
        return str(v)


def _fmt_pct(v: Any, places: int = 2) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.{places}f}%"
    except (TypeError, ValueError):
        return str(v)


def _get(d: Optional[Dict[str, Any]], *keys, default: Any = None) -> Any:
    """Safely pluck nested keys: _get(snap.session_stats, 'total_trades')."""
    if d is None:
        return default
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur if cur is not None else default


# ─────────────────────────────────────────────────────────────────────────────
# Markdown Builder
# ─────────────────────────────────────────────────────────────────────────────

class _MarkdownBuilder:
    def __init__(self):
        self._lines: List[str] = []

    def h1(self, text: str): self._lines.append(f"# {text}\n")
    def h2(self, text: str): self._lines.append(f"\n## {text}\n")
    def h3(self, text: str): self._lines.append(f"\n### {text}\n")
    def p(self,  text: str): self._lines.append(f"{text}\n")
    def blank(self):         self._lines.append("")

    def kv_table(self, rows: List[tuple]):
        self._lines.append("| Metric | Value |")
        self._lines.append("|---|---|")
        for k, v in rows:
            self._lines.append(f"| {k} | {v} |")
        self._lines.append("")

    def table(self, headers: List[str], rows: List[List[str]]):
        if not rows:
            self._lines.append("_(no data)_\n")
            return
        self._lines.append("| " + " | ".join(headers) + " |")
        self._lines.append("|" + "|".join(["---"] * len(headers)) + "|")
        for r in rows:
            self._lines.append("| " + " | ".join(str(c) for c in r) + " |")
        self._lines.append("")

    def bullet(self, text: str): self._lines.append(f"- {text}")

    def build(self) -> str:
        return "\n".join(self._lines) + "\n"


# ─────────────────────────────────────────────────────────────────────────────
# FTD-025A: System Export Engine
# ─────────────────────────────────────────────────────────────────────────────

class SystemExportEngine:
    """
    FTD-025A — Convert full system state → one structured report (MD + PDF).

    Single owner of the 15-section institutional report. Downstream
    (main.py) calls build_full_report(snapshot) and receives a ZIP.
    """

    PHASE = "25A"
    MODULE = "SYSTEM_EXPORT_ENGINE"

    # ── Public API ────────────────────────────────────────────────────────────

    def build_full_report(self, snapshot: SystemSnapshot) -> bytes:
        """Return a ZIP (bytes) containing .md and .pdf of the full report."""
        ts = int(time.time())
        md_bytes = self._build_markdown(snapshot).encode("utf-8")
        pdf_bytes = self._build_pdf(snapshot)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"full_system_report_{ts}.md",  md_bytes)
            zf.writestr(f"full_system_report_{ts}.pdf", pdf_bytes)
        return buf.getvalue()

    def build_markdown_only(self, snapshot: SystemSnapshot) -> str:
        """For tests / CI — no zip, no pdf."""
        return self._build_markdown(snapshot)

    def summary(self) -> Dict[str, Any]:
        return {"module": self.MODULE, "phase": self.PHASE,
                "sections": 15, "formats": ["md", "pdf"]}

    # ── Markdown (15 sections) ────────────────────────────────────────────────

    def _build_markdown(self, s: SystemSnapshot) -> str:
        md = _MarkdownBuilder()
        now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        md.h1("EOW Quant Engine — Full System Report")
        md.p(f"_Generated: {now}_")
        mode = _get(s.mode_info, "label", default="—")
        md.p(f"_Mode: {mode}_  —  _Phase: FTD-025A_")

        self._section_1_executive(md, s)
        self._section_2_performance(md, s)
        self._section_3_signal_pipeline(md, s)
        self._section_4_decision_trace(md, s)
        self._section_5_risk_state(md, s)
        self._section_6_portfolio(md, s)
        self._section_7_ai_brain(md, s)
        self._section_8_suggestions(md, s)
        self._section_9_auto_tuning(md, s)
        self._section_10_evolution(md, s)
        self._section_11_capital(md, s)
        self._section_12_audit(md, s)
        self._section_13_alerts(md, s)
        self._section_14_final_diagnosis(md, s)
        self._section_15_action_checklist(md, s)

        return md.build()

    # ── Section 1: Executive Summary ──────────────────────────────────────────

    def _section_1_executive(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("1. Executive Summary")
        ss = s.session_stats or {}
        total_net = ss.get("total_net_pnl", 0.0)
        direction = "PROFIT" if total_net >= 0 else "LOSS"
        total_tr  = ss.get("total_trades", 0)
        win_rate  = ss.get("win_rate", 0.0)
        pf        = ss.get("profit_factor", 0.0)
        sharpe    = ss.get("sharpe_ratio", 0.0)
        max_dd    = ss.get("max_drawdown_pct", 0.0)

        md.p(
            f"The engine closed **{total_tr}** trades with a net **{direction}** "
            f"of **{_fmt_num(total_net, 2, signed=True)} USDT**."
        )
        md.kv_table([
            ("Win Rate",       _fmt_pct(win_rate, 1)),
            ("Profit Factor",  _fmt_num(pf, 3)),
            ("Sharpe",         _fmt_num(sharpe, 3)),
            ("Max Drawdown",   _fmt_pct(max_dd, 2)),
            ("Mode",           _get(s.mode_info, "label", default="—")),
        ])

    # ── Section 2: Performance ────────────────────────────────────────────────

    def _section_2_performance(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("2. Performance")
        ss = s.session_stats or {}
        an = s.analytics     or {}
        md.kv_table([
            ("Final Capital (USDT)",   _fmt_num(ss.get("capital"), 2)),
            ("Net PnL (USDT)",         _fmt_num(ss.get("total_net_pnl"), 4, signed=True)),
            ("Total Trades",           str(ss.get("total_trades", 0))),
            ("Win Rate",               _fmt_pct(ss.get("win_rate", 0), 1)),
            ("Profit Factor",          _fmt_num(ss.get("profit_factor"), 3)),
            ("Sharpe",                 _fmt_num(ss.get("sharpe_ratio"), 3)),
            ("Sortino",                _fmt_num(an.get("sortino_ratio"), 3)),
            ("Calmar",                 _fmt_num(an.get("calmar_ratio"), 3)),
            ("Max Drawdown",           _fmt_pct(ss.get("max_drawdown_pct", 0), 2)),
            ("Risk of Ruin",           _fmt_pct(an.get("risk_of_ruin_pct", 0), 2)),
            ("Avg Win",                _fmt_num(ss.get("avg_win_usdt"),   4, signed=True)),
            ("Avg Loss",               _fmt_num(ss.get("avg_loss_usdt"),  4, signed=True)),
            ("Fees Paid",              _fmt_num(ss.get("total_fees_paid"),     4)),
            ("Slippage",               _fmt_num(ss.get("total_slippage"),      4)),
            ("Deployability",
                f"{_get(an, 'deployability', 'score', default=0)}/100 "
                f"({_get(an, 'deployability', 'tier', default='—')})"),
        ])

    # ── Section 3: Signal Pipeline ────────────────────────────────────────────

    def _section_3_signal_pipeline(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("3. Signal Pipeline")
        tf = s.trade_flow or {}
        md.kv_table([
            ("Signals / hour",    _fmt_num(tf.get("signals_per_hour"), 2)),
            ("Trades / hour",     _fmt_num(tf.get("trades_per_hour"),  2)),
            ("Rejection Rate",    _fmt_pct(tf.get("rejection_rate", 0) * 100, 1)),
            ("Signals total",     str(tf.get("total_signals", 0))),
            ("Trades total",      str(tf.get("total_trades",  0))),
            ("Skips total",       str(tf.get("total_skips",   0))),
            ("Mins since trade",  _fmt_num(tf.get("minutes_since_last_trade"), 1)),
        ])

    # ── Section 4: Decision Trace ────────────────────────────────────────────

    def _section_4_decision_trace(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("4. Decision Trace (last 30 thoughts)")
        thoughts = (s.thoughts or [])[-30:]
        rows: List[List[str]] = []
        for t in thoughts:
            ts_s = time.strftime(
                "%H:%M:%S",
                time.gmtime(t.get("ts", int(time.time() * 1000)) / 1000),
            )
            rows.append([
                ts_s,
                t.get("level", ""),
                (t.get("msg", "") or "").replace("|", "/")[:110],
            ])
        md.table(["Time", "Level", "Message"], rows)

        if s.last_skip:
            md.h3("Last Skip")
            md.kv_table([(k, str(v)) for k, v in s.last_skip.items()])

    # ── Section 5: Risk State ────────────────────────────────────────────────

    def _section_5_risk_state(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("5. Risk State")
        rs = s.risk_snapshot or {}
        dd = s.drawdown      or {}
        md.kv_table([
            ("Equity (USDT)",        _fmt_num(rs.get("equity"), 2)),
            ("Halted",               str(rs.get("halted", False))),
            ("Graceful stop",        str(rs.get("graceful_stop", False))),
            ("Open positions",       str(rs.get("open_positions", 0))),
            ("Daily PnL",            _fmt_num(rs.get("daily_pnl"), 2, signed=True)),
            ("Current Drawdown",     _fmt_pct(dd.get("current_pct", 0), 2)),
            ("DD State",             _get(dd, "state", default="—")),
            ("DD Risk Multiplier",   _fmt_num(dd.get("risk_multiplier"), 3)),
        ])

    # ── Section 6: Portfolio ─────────────────────────────────────────────────

    def _section_6_portfolio(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("6. Portfolio")
        positions = s.positions or []
        rows = [[
            p.get("symbol", ""),
            p.get("side", ""),
            _fmt_num(p.get("qty"), 6),
            _fmt_num(p.get("entry_px"), 4),
            _fmt_num(p.get("stop"),  4),
            _fmt_num(p.get("tp"),    4),
            _fmt_num(p.get("unrealised"), 4, signed=True),
        ] for p in positions]
        md.table(
            ["Symbol", "Side", "Qty", "Entry", "Stop", "TP", "Unrealised"],
            rows,
        )
        md.h3("Recent Trades (last 20)")
        trades = (s.trades or [])[-20:]
        tr_rows = [[
            t.get("symbol", ""),
            t.get("side", ""),
            _fmt_num(t.get("net_pnl"),   2, signed=True),
            _fmt_num(t.get("r_multiple"), 3),
            t.get("regime", ""),
            t.get("order_type", ""),
        ] for t in trades]
        md.table(
            ["Symbol", "Side", "Net PnL", "R", "Regime", "Order"],
            tr_rows,
        )

    # ── Section 7: AI Brain ──────────────────────────────────────────────────

    def _section_7_ai_brain(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("7. AI Brain")
        md.h3("Regime")
        reg = s.regime or {}
        md.kv_table([
            ("Current",      str(reg.get("current", "—"))),
            ("Confidence",   _fmt_num(reg.get("confidence"), 3)),
            ("Stable ticks", str(reg.get("stable_ticks", "—"))),
        ])
        md.h3("Learning Engine")
        lr = s.learning or {}
        md.kv_table([(k, str(v)) for k, v in lr.items()])

        md.h3("Edge Engine")
        eg = s.edge or {}
        md.kv_table([(k, str(v)) for k, v in eg.items()])

        md.h3("Strategy Usage")
        usage = s.strategy_usage or {}
        u_rows = [[k, str(v)] for k, v in usage.items()]
        md.table(["Strategy", "Count/Stat"], u_rows)

    # ── Section 8: Suggestions ───────────────────────────────────────────────

    def _section_8_suggestions(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("8. Suggestions (CT-Scan)")
        ct = s.ct_scan or {}
        findings = ct.get("findings") or ct.get("suggestions") or []
        if not findings:
            md.p("_No suggestions issued._")
            return
        rows = [[
            str(f.get("code", "")),
            str(f.get("severity", "")),
            str(f.get("message", ""))[:100],
            str(f.get("action", ""))[:80],
        ] for f in findings]
        md.table(["Code", "Severity", "Message", "Action"], rows)

    # ── Section 9: Auto-Tuning ───────────────────────────────────────────────

    def _section_9_auto_tuning(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("9. Auto-Tuning (Dynamic Thresholds)")
        dt = s.dynamic_thresholds or {}
        md.kv_table([(k, str(v)) for k, v in dt.items()])

        md.h3("Streak State")
        st = s.streak or {}
        md.kv_table([(k, str(v)) for k, v in st.items()])

    # ── Section 10: Evolution ────────────────────────────────────────────────

    def _section_10_evolution(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("10. Evolution (Genome)")
        gen = s.genome_state or {}
        md.kv_table([
            ("Generation",       str(gen.get("generation", "—"))),
            ("Fitness",          _fmt_num(gen.get("fitness"), 4)),
            ("Active DNA count", str(len(gen.get("active_dna", {}) or {}))),
            ("Last mutation",    str(gen.get("last_mutation_ts", "—"))),
        ])
        md.h3("Active DNA (summary)")
        dna = gen.get("active_dna") or {}
        rows = [[str(k), str(list(v.keys())[:5]) if isinstance(v, dict) else str(v)[:60]]
                for k, v in dna.items()]
        md.table(["Strategy", "Keys"], rows)

    # ── Section 11: Capital ──────────────────────────────────────────────────

    def _section_11_capital(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("11. Capital Allocation")
        ca = s.capital_allocator or {}
        md.kv_table([(k, str(v)) for k, v in ca.items()])

    # ── Section 12: Audit ────────────────────────────────────────────────────

    def _section_12_audit(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("12. Audit (Error Registry — last 50)")
        errs = s.error_registry or []
        rows = [[
            str(e.get("ts", "")),
            str(e.get("code", "")),
            str(e.get("symbol", "")),
            str(e.get("extra", ""))[:100],
        ] for e in errs[-50:]]
        md.table(["Time", "Code", "Symbol", "Extra"], rows)

        md.h3("Healer Events (recent)")
        heal = s.healer or {}
        evs = heal.get("recent_events") or []
        md.table(
            ["Action", "OK", "Detail"],
            [[str(e.get("action", "")), str(e.get("ok", "")),
              str(e.get("detail", ""))[:80]] for e in evs[:20]],
        )

    # ── Section 13: Alerts ───────────────────────────────────────────────────

    def _section_13_alerts(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("13. Alerts")
        gs   = s.gate_status or {}
        halt = s.halt_audit  or {}
        md.kv_table([
            ("Gate: can_trade",   str(gs.get("can_trade", "—"))),
            ("Gate: safe_mode",   str(gs.get("safe_mode", "—"))),
            ("Gate: reason",      str(gs.get("reason", "—"))),
            ("Halt active",       str(halt.get("active", False))),
            ("Halt reason",       str(halt.get("reason", "—"))),
            ("Halt since",        str(halt.get("since", "—"))),
        ])

    # ── Section 14: Final Diagnosis ──────────────────────────────────────────

    def _section_14_final_diagnosis(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("14. Final Diagnosis")
        verdicts = self._diagnose(s)
        for v in verdicts:
            md.bullet(v)
        md.blank()

    # ── Section 15: Action Checklist ─────────────────────────────────────────

    def _section_15_action_checklist(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("15. Action Checklist")
        actions = self._action_items(s)
        for a in actions:
            md.bullet(f"[ ] {a}")
        md.blank()
        md.p("---")
        md.p("_End of report — FTD-025A Export Engine v1.0_")

    # ── Diagnostic logic (sections 14 & 15) ──────────────────────────────────

    def _diagnose(self, s: SystemSnapshot) -> List[str]:
        out: List[str] = []
        ss = s.session_stats or {}
        tf = s.trade_flow    or {}
        dd = s.drawdown      or {}
        gs = s.gate_status   or {}

        n_tr = ss.get("total_trades", 0)
        if n_tr == 0:
            out.append("**No trades executed** — possible causes: safe-mode, "
                       "PTG blocking, ranker threshold, or signal engine dry.")
        else:
            pf = ss.get("profit_factor", 0.0)
            out.append(f"System has processed {n_tr} trades; profit_factor={pf:.2f}.")

        if tf.get("minutes_since_last_trade", 0) > 60:
            out.append("**Trade dry-spell > 60 min** — Trade Activator should be "
                       "relaxing thresholds; verify T1/T2 scores are below base.")

        if not gs.get("can_trade", True):
            out.append(f"**Gate is blocking** trades: {gs.get('reason', '?')}.")
        if gs.get("safe_mode", False):
            out.append(f"**SAFE_MODE active** — cause: {gs.get('reason', '?')}.")

        if dd.get("state") and dd["state"] != "NORMAL":
            out.append(f"Drawdown state = **{dd['state']}** "
                       f"(risk_mult={dd.get('risk_multiplier', 1.0)}).")

        errs = s.error_registry or []
        if len(errs) > 20:
            out.append(f"**{len(errs)} errors** recorded — inspect Section 12.")

        if not out:
            out.append("All green — no anomalies detected in this snapshot.")
        return out

    def _action_items(self, s: SystemSnapshot) -> List[str]:
        out: List[str] = []
        ss = s.session_stats or {}
        gs = s.gate_status   or {}
        dd = s.drawdown      or {}
        tf = s.trade_flow    or {}

        if ss.get("total_trades", 0) == 0:
            out.append("Inspect PreTradeGate + ScanController logs for block reasons.")
            out.append("Confirm ACTIVATOR_T1_SCORE < MIN_TRADE_SCORE (qFTD-011 fix).")
        if gs.get("safe_mode", False):
            out.append("Resolve SAFE_MODE cause, then call POST /api/resume.")
        if dd.get("state") in ("WARNING", "CRITICAL"):
            out.append("Review drawdown_controller state; consider reducing base_risk.")
        if tf.get("rejection_rate", 0) > 0.85:
            out.append("Rejection rate > 85% — tune adaptive filter / scoring.")

        out.append("Review Section 4 (Decision Trace) for last 30 thoughts.")
        out.append("Archive this report under /reports/<date>/ for audit trail.")
        return out

    # ── PDF (same 15 sections, paginated) ─────────────────────────────────────

    def _build_pdf(self, s: SystemSnapshot) -> bytes:
        pdf = _PDFWriter()
        now = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

        pdf.title("EOW Quant Engine — Full System Report")
        pdf.body(f"Generated: {now}   Mode: {_get(s.mode_info, 'label', default='—')}   "
                 f"Phase: FTD-025A", size=9)
        pdf.blank()

        # 1. Executive
        pdf.h2("1. Executive Summary")
        ss = s.session_stats or {}
        for label, val in [
            ("Total Trades",   str(ss.get("total_trades", 0))),
            ("Net PnL (USDT)", _fmt_num(ss.get("total_net_pnl"), 4, signed=True)),
            ("Win Rate",       _fmt_pct(ss.get("win_rate", 0), 1)),
            ("Profit Factor",  _fmt_num(ss.get("profit_factor"), 3)),
            ("Sharpe",         _fmt_num(ss.get("sharpe_ratio"), 3)),
            ("Max Drawdown",   _fmt_pct(ss.get("max_drawdown_pct", 0), 2)),
        ]:
            pdf.kv(label, val)

        # 2. Performance
        pdf.h2("2. Performance")
        an = s.analytics or {}
        for label, val in [
            ("Final Capital",     _fmt_num(ss.get("capital"), 2)),
            ("Sortino",           _fmt_num(an.get("sortino_ratio"), 3)),
            ("Calmar",            _fmt_num(an.get("calmar_ratio"),  3)),
            ("Risk of Ruin",      _fmt_pct(an.get("risk_of_ruin_pct", 0), 2)),
            ("Deployability",
                f"{_get(an, 'deployability', 'score', default=0)}/100 "
                f"({_get(an, 'deployability', 'tier', default='—')})"),
            ("Fees Paid",         _fmt_num(ss.get("total_fees_paid"), 4)),
            ("Slippage",          _fmt_num(ss.get("total_slippage"),  4)),
        ]:
            pdf.kv(label, val)

        # 3. Signal Pipeline
        pdf.h2("3. Signal Pipeline")
        tf = s.trade_flow or {}
        for label, val in [
            ("Signals / hour",   _fmt_num(tf.get("signals_per_hour"), 2)),
            ("Trades / hour",    _fmt_num(tf.get("trades_per_hour"),  2)),
            ("Rejection Rate",   _fmt_pct(tf.get("rejection_rate", 0) * 100, 1)),
            ("Mins since trade", _fmt_num(tf.get("minutes_since_last_trade"), 1)),
        ]:
            pdf.kv(label, val)

        # 4. Decision Trace
        pdf.new_page()
        pdf.h2("4. Decision Trace (last 30 thoughts)")
        cols   = ["Time", "Level", "Message"]
        widths = [60, 60, 350]
        pdf.table_header(cols, widths)
        for t in (s.thoughts or [])[-30:]:
            ts_s = time.strftime(
                "%H:%M:%S",
                time.gmtime(t.get("ts", int(time.time() * 1000)) / 1000),
            )
            pdf.table_row([
                ts_s,
                (t.get("level", "") or "")[:8],
                (t.get("msg", "") or "")[:70],
            ], widths)

        # 5. Risk State
        pdf.new_page()
        pdf.h2("5. Risk State")
        rs = s.risk_snapshot or {}
        dd = s.drawdown      or {}
        for label, val in [
            ("Equity",             _fmt_num(rs.get("equity"), 2)),
            ("Halted",             str(rs.get("halted", False))),
            ("Open Positions",     str(rs.get("open_positions", 0))),
            ("Daily PnL",          _fmt_num(rs.get("daily_pnl"), 2, signed=True)),
            ("Current Drawdown",   _fmt_pct(dd.get("current_pct", 0), 2)),
            ("DD State",           str(dd.get("state", "—"))),
            ("DD Risk Multiplier", _fmt_num(dd.get("risk_multiplier"), 3)),
        ]:
            pdf.kv(label, val)

        # 6. Portfolio
        pdf.h2("6. Portfolio — Recent Trades (last 20)")
        cols   = ["Symbol", "Side", "Net PnL", "R", "Regime"]
        widths = [75, 55, 80, 70, 95]
        pdf.table_header(cols, widths)
        for t in (s.trades or [])[-20:]:
            pdf.table_row([
                t.get("symbol", "")[:10],
                t.get("side",   "")[:5],
                _fmt_num(t.get("net_pnl"),   2, signed=True),
                _fmt_num(t.get("r_multiple"), 3),
                (t.get("regime", "") or "")[:10],
            ], widths)

        # 7. AI Brain
        pdf.new_page()
        pdf.h2("7. AI Brain — Regime & Learning")
        reg = s.regime or {}
        pdf.kv("Regime",       str(reg.get("current", "—")))
        pdf.kv("Confidence",   _fmt_num(reg.get("confidence"), 3))
        pdf.kv("Stable ticks", str(reg.get("stable_ticks", "—")))
        pdf.blank()
        pdf.body("Learning engine summary:")
        for k, v in (s.learning or {}).items():
            pdf.kv(str(k), str(v))

        # 8. Suggestions
        pdf.h2("8. Suggestions (CT-Scan)")
        ct = s.ct_scan or {}
        findings = ct.get("findings") or ct.get("suggestions") or []
        if not findings:
            pdf.body("No suggestions issued.")
        else:
            for f in findings[:20]:
                pdf.kv(str(f.get("code", "")) + " / " + str(f.get("severity", "")),
                       str(f.get("message", ""))[:80])

        # 9. Auto-Tuning
        pdf.new_page()
        pdf.h2("9. Auto-Tuning (Dynamic Thresholds)")
        for k, v in (s.dynamic_thresholds or {}).items():
            pdf.kv(str(k), str(v))
        pdf.blank()
        pdf.body("Streak state:")
        for k, v in (s.streak or {}).items():
            pdf.kv(str(k), str(v))

        # 10. Evolution
        pdf.h2("10. Evolution (Genome)")
        gen = s.genome_state or {}
        pdf.kv("Generation",    str(gen.get("generation", "—")))
        pdf.kv("Fitness",       _fmt_num(gen.get("fitness"), 4))
        pdf.kv("Active DNA",    str(len(gen.get("active_dna", {}) or {})))

        # 11. Capital
        pdf.h2("11. Capital Allocation")
        for k, v in (s.capital_allocator or {}).items():
            pdf.kv(str(k), str(v))

        # 12. Audit
        pdf.new_page()
        pdf.h2("12. Audit (Error Registry, last 25)")
        cols   = ["Time", "Code", "Symbol", "Extra"]
        widths = [80, 85, 80, 230]
        pdf.table_header(cols, widths)
        for e in (s.error_registry or [])[-25:]:
            pdf.table_row([
                str(e.get("ts", ""))[:12],
                str(e.get("code", ""))[:12],
                str(e.get("symbol", ""))[:10],
                str(e.get("extra", ""))[:40],
            ], widths)

        # 13. Alerts
        pdf.h2("13. Alerts")
        gs = s.gate_status or {}
        halt = s.halt_audit or {}
        pdf.kv("Gate can_trade", str(gs.get("can_trade", "—")))
        pdf.kv("Gate safe_mode", str(gs.get("safe_mode", "—")))
        pdf.kv("Gate reason",    str(gs.get("reason", "—")))
        pdf.kv("Halt active",    str(halt.get("active", False)))
        pdf.kv("Halt reason",    str(halt.get("reason", "—")))

        # 14. Final Diagnosis
        pdf.new_page()
        pdf.h2("14. Final Diagnosis")
        for v in self._diagnose(s):
            pdf.body(f"• {v}", size=10)

        # 15. Action Checklist
        pdf.h2("15. Action Checklist")
        for a in self._action_items(s):
            pdf.body(f"[ ] {a}", size=10)

        pdf.blank(2)
        pdf.body("— End of report (FTD-025A Export Engine v1.0) —", size=9)

        return pdf.build()


# Singleton (convenience, same pattern as other engines)
system_export_engine = SystemExportEngine()
