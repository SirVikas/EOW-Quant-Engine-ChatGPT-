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

    # 9. AI Brain (FTD-027: must produce concrete decisions, not empty state)
    ai_brain_state:     Dict[str, Any] = None        # ai_brain.get_state()

    # 10. Learning Memory (FTD-030B)
    learning_memory:    Dict[str, Any] = None        # learning_memory_orchestrator.summary()


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
        self._section_16_learning_memory(md, s)

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

        # FTD-027: show concrete AI Brain decision — not empty state
        brain = getattr(s, "ai_brain_state", None) or {}
        md.h3("AI Decision (FTD-023)")
        md.kv_table([
            ("Mode",     str(brain.get("mode",     "—"))),
            ("Decision", str(brain.get("decision", "—"))),
            ("Module",   str(brain.get("module",   "AI_BRAIN"))),
            ("Phase",    str(brain.get("phase",    "023"))),
        ])

        md.h3("Regime")
        reg = s.regime or brain.get("regime") or {}
        md.kv_table([
            ("Current",      str(reg.get("current",      "—"))),
            ("Confidence",   _fmt_num(reg.get("confidence"), 3)),
            ("Stable ticks", str(reg.get("stable_ticks", "—"))),
        ])
        md.h3("Learning Engine")
        lr = s.learning or brain.get("learning") or {}
        md.kv_table([(k, str(v)) for k, v in lr.items()])

        md.h3("Edge Engine")
        eg = s.edge or brain.get("edge") or {}
        md.kv_table([(k, str(v)) for k, v in eg.items()])

        md.h3("Strategy Usage")
        usage = s.strategy_usage or {}
        u_rows = [[k, str(v)] for k, v in usage.items()]
        md.table(["Strategy", "Count/Stat"], u_rows)

    # ── Section 8: Suggestions ───────────────────────────────────────────────

    def _section_8_suggestions(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("8. Suggestions (CT-Scan)")
        ct = s.ct_scan or {}

        # Summary row (health + score) — works with both enriched and raw ct_scan format
        health = ct.get("health", ct.get("system_health", "—"))
        score  = ct.get("score", "—")
        action = ct.get("action", "—")
        md.kv_table([
            ("Health", str(health)),
            ("Score",  str(score)),
            ("Action", str(action)[:120]),
        ])

        # FTD-027: findings come from suggestion_engine (enriched) or fall back to
        # converting raw ct_scan 'issues' strings → dicts
        findings = ct.get("findings") or ct.get("suggestions") or []
        if not findings:
            issues = ct.get("issues", [])
            for i, iss in enumerate(issues, 1):
                sev = "CRITICAL" if health == "CRITICAL" else "HIGH" if health == "WARNING" else "MEDIUM"
                findings.append({"code": f"CT-{i:03d}", "severity": sev,
                                  "message": str(iss), "action": action})

        if not findings:
            md.p("_No issues detected — system is healthy._")
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

    # ── Section 16: Learning Memory (FTD-030B) ───────────────────────────────

    def _section_16_learning_memory(self, md: _MarkdownBuilder, s: SystemSnapshot):
        md.h2("16. Learning Memory (FTD-030B)")
        lm = s.learning_memory or {}

        if not lm:
            md.p("_Learning memory data not available._")
            return

        enabled        = lm.get("enabled", False)
        total_records  = lm.get("total_records", 0)
        formed         = lm.get("formed_patterns", 0)
        total_patterns = lm.get("total_patterns", 0)
        cycle_count    = lm.get("cycle_count", 0)
        neg_mem        = lm.get("negative_memory", {})

        md.kv_table([
            ("Status",           "ACTIVE" if enabled else "DISABLED"),
            ("Memory Records",   str(total_records)),
            ("Total Patterns",   str(total_patterns)),
            ("Formed Patterns",  str(formed)),
            ("Cycles Processed", str(cycle_count)),
            ("Negative Memory (Permanent)", str(neg_mem.get("permanent", 0))),
            ("Negative Memory (Temporary)", str(neg_mem.get("temporary", 0))),
        ])

        top_patterns = lm.get("top_patterns", [])
        if top_patterns:
            md.h3("Top Patterns (by Confidence)")
            rows = []
            for p in top_patterns[:5]:
                key = p.get("key", {})
                rows.append([
                    p.get("pattern_id", "—"),
                    key.get("parameter", "—"),
                    key.get("direction", "—"),
                    f"{key.get('regime','—')}/{key.get('volatility','—')}",
                    str(p.get("samples", 0)),
                    f"{p.get('confidence', 0):.1f}",
                ])
            md.table(
                ["Pattern ID", "Parameter", "Direction", "Regime/Volatility",
                 "Samples", "Confidence"],
                rows,
            )

        md.blank()

    # ── Diagnostic logic (sections 14 & 15) ──────────────────────────────────

    def _diagnose(self, s: SystemSnapshot) -> List[str]:
        """
        FTD-027: Structured diagnosis — Primary Issue, Secondary Issue, Actionable Fix.
        Checks: signal/trade contradiction, loss state, gate blocking, risk of ruin
        control, drawdown state, dry spell, error flood.
        """
        ss = s.session_stats or {}
        tf = s.trade_flow    or {}
        dd = s.drawdown      or {}
        gs = s.gate_status   or {}
        an = s.analytics     or {}

        n_tr    = ss.get("total_trades", 0)
        pf      = ss.get("profit_factor", 0.0)
        wr      = ss.get("win_rate", 0.0)
        n_sig   = tf.get("total_signals", 0)
        ror_pct = float(an.get("risk_of_ruin_pct", 0.0) or 0.0)
        dd_state = str(dd.get("state", "NORMAL")).upper()
        dd_mult  = float(dd.get("risk_multiplier", 1.0) or 1.0)
        dry_min  = float(tf.get("minutes_since_last_trade", 0) or 0.0)
        errs     = s.error_registry or []

        # Priority queue: (priority_int, title, detail, fix)
        issues: List[tuple] = []

        # 1. Trade-signal data contradiction (highest priority — data integrity)
        if n_tr > 0 and n_sig == 0:
            issues.append((0,
                "CONTRADICTION — trades recorded but signal count = 0",
                (f"{n_tr} closed trades exist but trade_flow_monitor reports 0 signals. "
                 "This is a data-integrity gap in the signal pipeline tracker."),
                ("Verify on_tick calls trade_flow_monitor.record_signal() for every "
                 "evaluated signal. Restart trade_flow_monitor if counter was reset."),
            ))

        # 2. System in loss OR no trades
        if n_tr == 0:
            gate_reason = gs.get("reason", "unknown")
            issues.append((1,
                "NO TRADES EXECUTED — signal pipeline silent",
                (f"0 closed trades. Gate can_trade={gs.get('can_trade', '?')}, "
                 f"safe_mode={gs.get('safe_mode', False)}, reason='{gate_reason}'."),
                ("Check PreTradeGate + ScanController logs. Confirm ACTIVATOR_T1 < "
                 "MIN_TRADE_SCORE in config.py. If gate blocked, resolve cause and "
                 "call POST /api/resume."),
            ))
        elif pf < 1.0:
            issues.append((1,
                f"SYSTEM IN LOSS — profit_factor={pf:.3f} (negative expectancy)",
                (f"{n_tr} trades; win_rate={wr:.1f}%. Every trade destroys capital "
                 f"on average. Immediate action required."),
                ("Widen RR target to ≥1.5R; tighten entry criteria; reduce "
                 "trade frequency until PF recovers above 1.0. Review Section 3 "
                 "(Signal Pipeline) and Section 8 (Suggestions)."),
            ))

        # 3. Gate blocking
        if not gs.get("can_trade", True):
            issues.append((2,
                f"GATE BLOCKED — can_trade=False",
                (f"reason='{gs.get('reason', 'unknown')}', "
                 f"safe_mode={gs.get('safe_mode', False)}, "
                 f"halt={gs.get('halted', False)}."),
                ("Identify blocking condition (daily loss limit / safe mode / halt). "
                 "Fix root cause then call POST /api/resume."),
            ))

        # 4. Risk of ruin — show system control response
        if ror_pct >= 95.0:
            ctrl_applied = (f"risk_multiplier={dd_mult:.2f} "
                            f"({'reduced' if dd_mult < 1.0 else 'NOT yet reduced'})")
            issues.append((2,
                f"RISK OF RUIN = {ror_pct:.1f}% — CAPITAL IN DANGER",
                (f"System controls active: DD state={dd_state}, {ctrl_applied}, "
                 f"halted={gs.get('halted', False)}."),
                ("Halve base_risk immediately. drawdown_controller auto-reduces "
                 "sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. "
                 "Do not add new positions until RoR drops below 50%."),
            ))
        elif ror_pct >= 50.0:
            issues.append((3,
                f"ELEVATED RISK OF RUIN = {ror_pct:.1f}%",
                f"DD state={dd_state}, risk_multiplier={dd_mult:.2f}.",
                ("Monitor closely. drawdown_controller will deepen size reduction "
                 "as drawdown progresses. Consider reducing base_risk by 25%."),
            ))

        # 5. Drawdown state
        if dd_state in ("WARNING", "CRITICAL"):
            dd_cur = _fmt_pct(dd.get("current_pct", 0), 2)
            issues.append((3,
                f"DRAWDOWN {dd_state} at {dd_cur}",
                (f"risk_multiplier={dd_mult:.2f} — system auto-reduces size by "
                 f"{(1.0 - dd_mult) * 100:.0f}%."),
                "Allow drawdown_controller to manage recovery; avoid manual risk overrides.",
            ))

        # 6. Trade dry spell
        if dry_min > 60:
            issues.append((4,
                f"TRADE DRY-SPELL — {dry_min:.0f} min since last trade",
                "Trade Activator should be auto-relaxing thresholds after 60 min.",
                ("Verify ACTIVATOR_T1/T2 < MIN_TRADE_SCORE in config.py. "
                 "Check adaptive_filter state and volume_filter thresholds."),
            ))

        # 7. Error flood
        if len(errs) > 20:
            issues.append((5,
                f"{len(errs)} ERRORS recorded in audit log",
                "High error count may indicate WS connectivity or data quality issues.",
                "Inspect Section 12 (Audit) for error codes; verify WebSocket health.",
            ))

        # Sort by priority (0 = most critical)
        issues.sort(key=lambda x: x[0])

        out: List[str] = []
        if not issues:
            out.append("**PRIMARY ISSUE:** None — all systems green.")
            out.append("**SECONDARY ISSUE:** None.")
            out.append("**ACTIONABLE FIX:** Continue normal operation. "
                       "Re-export in 1 hour for trend comparison.")
            return out

        pri = issues[0]
        out.append(f"**PRIMARY ISSUE:** {pri[1]}")
        out.append(f"  Detail — {pri[2]}")
        out.append(f"  Fix — {pri[3]}")
        out.append("")

        if len(issues) > 1:
            sec = issues[1]
            out.append(f"**SECONDARY ISSUE:** {sec[1]}")
            out.append(f"  Detail — {sec[2]}")
            out.append(f"  Fix — {sec[3]}")
        else:
            out.append("**SECONDARY ISSUE:** None identified beyond primary.")

        out.append("")
        out.append(f"**ACTIONABLE FIX (primary):** {pri[3]}")

        # Surface all remaining issues so nothing critical is hidden
        remaining = issues[2:]
        if remaining:
            out.append("")
            out.append("**Also noted (requires attention):**")
            for iss in remaining:
                out.append(f"  - {iss[1]}: {iss[2][:120]}")

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

        # 7. AI Brain — FTD-027: show concrete decision
        pdf.new_page()
        pdf.h2("7. AI Brain — Decision & Regime")
        brain = getattr(s, "ai_brain_state", None) or {}
        pdf.kv("Mode",          str(brain.get("mode",     "—")))
        pdf.kv("Decision",      str(brain.get("decision", "—")))
        pdf.blank()
        reg = s.regime or brain.get("regime") or {}
        pdf.kv("Regime",        str(reg.get("current",      "—")))
        pdf.kv("Confidence",    _fmt_num(reg.get("confidence"), 3))
        pdf.kv("Stable ticks",  str(reg.get("stable_ticks",  "—")))
        pdf.blank()
        pdf.body("Learning engine summary:")
        for k, v in (s.learning or brain.get("learning") or {}).items():
            pdf.kv(str(k), str(v))

        # 8. Suggestions — FTD-027: findings from enriched suggestion_engine output
        pdf.h2("8. Suggestions (CT-Scan)")
        ct = s.ct_scan or {}
        health_pdf = ct.get("health", ct.get("system_health", "—"))
        score_pdf  = ct.get("score", "—")
        pdf.kv("Health", str(health_pdf))
        pdf.kv("Score",  str(score_pdf))
        findings = ct.get("findings") or ct.get("suggestions") or []
        if not findings:
            issues_raw = ct.get("issues", [])
            for i, iss in enumerate(issues_raw, 1):
                sev = "CRITICAL" if health_pdf == "CRITICAL" else "WARNING"
                findings.append({"code": f"CT-{i:03d}", "severity": sev,
                                  "message": str(iss), "action": ct.get("action", "")})
        if not findings:
            pdf.body("No issues detected — system is healthy.")
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
