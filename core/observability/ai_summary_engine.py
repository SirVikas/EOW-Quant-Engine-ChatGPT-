"""
EOW Quant Engine — AI Summary Engine  (FTD-053-GAIA Phase 4)

Rule-based strategic intelligence synthesizer. Converts compressed snapshots,
delta reports, and anomaly events into structured, actionable narratives —
without calling any external AI API (pure rule-based synthesis).

Design principles:
  • RULE-BASED     — no external AI calls; deterministic and token-free
  • NARRATIVE-FIRST — output reads like expert analysis, not raw metrics
  • PRIORITY-GATED — summary priority drives sync and alert decisions
  • NON-THROWING   — all methods catch internally; never halts trading engine
  • ADDITIVE       — consumes Phase 1-3 outputs; produces Phase 4 narrative

Summary structure:
  {
    "headline":               str,   # one-line system state
    "priority":               str,   # CRITICAL / HIGH / ROUTINE / MONITORING
    "signal_strength":        float, # 0–100 (how actionable this summary is)
    "risk_narrative":         str,   # what risks are active
    "learning_narrative":     str,   # RL engine evolution
    "performance_narrative":  str,   # trading outcomes
    "regime_narrative":       str,   # market context
    "directives":             List[str],  # ordered action recommendations
    "directive_count":        int,
    "summary_ts":             int,   # epoch ms
    "anomaly_count":          int,
    "worst_severity":         str,
  }

Signal strength (0–100):
  Anomaly severity contribution (50%):
    CRITICAL ≥ 1  → 50 pts
    HIGH ≥ 1      → 35 pts
    MEDIUM ≥ 1    → 20 pts
    None          →  0 pts

  Delta significance contribution (30%):
    score ≥ 30    → 30 pts
    score ≥ 15    → 20 pts
    score ≥  5    → 10 pts
    no delta      →  0 pts

  IQ deviation contribution (20%):
    IQ < 20       → 20 pts (CRITICAL)
    IQ < 35       → 15 pts
    IQ < 50       → 10 pts
    IQ < 65       →  5 pts
    IQ ≥ 65       →  0 pts

Priority mapping:
  signal_strength ≥ 50  → CRITICAL
  signal_strength ≥ 30  → HIGH
  signal_strength ≥ 10  → ROUTINE
  signal_strength <  10  → MONITORING
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger

from core.observability.anomaly_detector import SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW


# ── Priority labels ───────────────────────────────────────────────────────────

PRI_CRITICAL   = "CRITICAL"
PRI_HIGH       = "HIGH"
PRI_ROUTINE    = "ROUTINE"
PRI_MONITORING = "MONITORING"

# ── Signal strength thresholds ────────────────────────────────────────────────

SS_CRITICAL_FLOOR = 50.0
SS_HIGH_FLOOR     = 30.0
SS_ROUTINE_FLOOR  = 10.0


# ── Directives catalog ────────────────────────────────────────────────────────
# Each directive: (trigger_condition_name, text)
# Applied in order; first matching conditions produce directives.

_DIRECTIVE_CATALOG = [
    ("risk_halted",        "Investigate risk controller halt — review drawdown and position state"),
    ("gate_closed",        "Trade gate is closed — check risk limits and session PnL"),
    ("toxic_critical",     "Multiple toxic RL contexts blocked — consider RL engine reset or session restart"),
    ("toxic_high",         "Elevated toxic contexts — monitor RL learning stability"),
    ("loss_streak_crit",   "Severe loss streak — verify strategy logic and market conditions"),
    ("loss_streak_high",   "Extended loss streak — review risk-per-trade and position sizing"),
    ("loss_streak_med",    "Loss streak detected — monitor next 3 trades before adjusting"),
    ("iq_critical",        "Intelligence score critically low — RL engine has insufficient learning data"),
    ("iq_high",            "Intelligence score low — allow more trades for learning acceleration"),
    ("allow_rate_crit",    "Allow rate critically low — loosen signal filter thresholds or check gate logic"),
    ("allow_rate_high",    "Allow rate below target — review signal quality thresholds"),
    ("confidence_decline", "RL confidence declining — reduce position size until trend reverses"),
    ("maturity_warming",   "RL engine still warming up — expect higher variance in decisions"),
    ("pf_weak",            "Profit factor below 1.0 — session is currently unprofitable"),
    ("wr_erosion",         "Win rate erosion in active regime — verify strategy-regime alignment"),
    ("regime_shift",       "Regime changed — allow RL engine to adapt before increasing trade frequency"),
]


@dataclass
class SummaryStats:
    total_summaries:  int   = 0
    critical_count:   int   = 0
    high_count:       int   = 0
    routine_count:    int   = 0
    monitoring_count: int   = 0
    last_summary_ts:  int   = 0
    last_priority:    str   = ""


class AISummaryEngine:
    """
    Rule-based strategic intelligence synthesizer.
    No external AI API dependencies — deterministic, token-free, audit-ready.
    """

    MODULE  = "AI_SUMMARY_ENGINE"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._stats            = SummaryStats()
        self._prev_regime:     Optional[str] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_summary(
        self,
        compressed:   Dict[str, Any],
        delta_report: Optional[Dict[str, Any]] = None,
        anomalies:    Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a full strategic intelligence summary.
        Never raises — returns {"error": ...} on unexpected failure.
        """
        try:
            anomalies    = anomalies or []
            delta_report = delta_report or {}
            now_ms       = int(time.time() * 1000)

            # ── Extract key values ─────────────────────────────────────────
            ctx = _extract(compressed)

            # ── Worst severity ─────────────────────────────────────────────
            worst = _worst_severity(anomalies)

            # ── Signal strength ────────────────────────────────────────────
            ss = self._signal_strength(anomalies, delta_report, ctx)

            # ── Priority ───────────────────────────────────────────────────
            priority = _priority_from_ss(ss)

            # ── Condition flags (drives headlines, narratives, directives) ─
            flags = _condition_flags(ctx, anomalies, delta_report, self._prev_regime)

            # ── Narrative sections ─────────────────────────────────────────
            headline             = self._headline(worst, flags, ctx)
            risk_narrative       = self._risk_narrative(ctx, flags)
            learning_narrative   = self._learning_narrative(ctx, flags)
            performance_narrative= self._performance_narrative(ctx, flags)
            regime_narrative     = self._regime_narrative(ctx, flags)
            directives           = self._directives(flags)

            # ── Update state ───────────────────────────────────────────────
            self._prev_regime = ctx.get("regime")
            self._update_stats(priority, now_ms)

            return {
                "module":                self.MODULE,
                "version":               self.VERSION,
                "summary_ts":            now_ms,
                "priority":              priority,
                "signal_strength":       round(ss, 1),
                "worst_severity":        worst,
                "anomaly_count":         len(anomalies),
                "headline":              headline,
                "risk_narrative":        risk_narrative,
                "learning_narrative":    learning_narrative,
                "performance_narrative": performance_narrative,
                "regime_narrative":      regime_narrative,
                "directives":            directives,
                "directive_count":       len(directives),
            }

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] generate_summary error: {exc}")
            return {
                "module":   self.MODULE,
                "error":    str(exc),
                "priority": PRI_MONITORING,
                "summary_ts": int(time.time() * 1000),
            }

    def stats(self) -> Dict[str, Any]:
        s = self._stats
        return {
            "module":           self.MODULE,
            "version":          self.VERSION,
            "total_summaries":  s.total_summaries,
            "critical_count":   s.critical_count,
            "high_count":       s.high_count,
            "routine_count":    s.routine_count,
            "monitoring_count": s.monitoring_count,
            "last_summary_ts":  s.last_summary_ts,
            "last_priority":    s.last_priority,
        }

    # ── Signal strength ───────────────────────────────────────────────────────

    def _signal_strength(
        self,
        anomalies:    List[Dict[str, Any]],
        delta_report: Dict[str, Any],
        ctx:          Dict[str, Any],
    ) -> float:
        score = 0.0

        # Anomaly severity contribution (50%)
        sevs = {a.get("severity") for a in anomalies}
        if SEV_CRITICAL in sevs:
            score += 50.0
        elif SEV_HIGH in sevs:
            score += 35.0
        elif SEV_MEDIUM in sevs:
            score += 20.0

        # Delta significance contribution (30%)
        delta_ss = float(delta_report.get("significance_score", 0))
        if delta_ss >= 30:
            score += 30.0
        elif delta_ss >= 15:
            score += 20.0
        elif delta_ss >= 5:
            score += 10.0

        # IQ deviation contribution (20%)
        iq = ctx.get("iq_score", 65.0)
        if iq < 20:
            score += 20.0
        elif iq < 35:
            score += 15.0
        elif iq < 50:
            score += 10.0
        elif iq < 65:
            score += 5.0

        return min(score, 100.0)

    # ── Headline ──────────────────────────────────────────────────────────────

    def _headline(
        self,
        worst: str,
        flags: Dict[str, bool],
        ctx:   Dict[str, Any],
    ) -> str:
        if flags.get("risk_halted"):
            return "CRITICAL: Trading engine halted by risk controller"
        if worst == SEV_CRITICAL:
            return "CRITICAL: Multiple severe conditions detected — immediate review required"
        if flags.get("gate_closed"):
            return "HIGH ALERT: Trade gate closed — new trades blocked"
        if flags.get("loss_streak_crit"):
            return f"HIGH ALERT: {ctx.get('consec_losses', 0)} consecutive losses — severe losing streak"
        if flags.get("toxic_critical"):
            return f"HIGH ALERT: {ctx.get('rl_toxic', 0)} toxic RL contexts blocked"
        if worst == SEV_HIGH:
            return "ALERT: Significant anomalies detected — performance degradation in progress"
        if flags.get("loss_streak_med"):
            return f"NOTICE: {ctx.get('consec_losses', 0)} consecutive losses — monitoring"
        if worst == SEV_MEDIUM:
            return "NOTICE: Mild anomalies detected — system operating within degraded parameters"
        if flags.get("regime_shift"):
            return f"INFO: Market regime changed to {ctx.get('regime', 'UNKNOWN')}"
        iq  = ctx.get("iq_score", 0)
        pnl = ctx.get("pnl", 0.0)
        return (
            f"STABLE: IQ={iq:.0f}/100 | PnL=${pnl:.2f} | "
            f"Regime={ctx.get('regime', 'UNKNOWN')} — system operating normally"
        )

    # ── Narratives ────────────────────────────────────────────────────────────

    def _risk_narrative(self, ctx: Dict, flags: Dict) -> str:
        parts = []

        if flags.get("risk_halted"):
            parts.append("Risk controller has HALTED the engine.")
        elif flags.get("gate_closed"):
            parts.append("Trade gate is CLOSED — no new positions permitted.")
        else:
            parts.append("Risk gate is OPEN.")

        cl = ctx.get("consec_losses", 0)
        if cl >= 5:
            parts.append(f"Severe loss streak: {cl} consecutive losses.")
        elif cl >= 3:
            parts.append(f"Loss streak: {cl} consecutive losses — monitoring.")
        elif cl > 0:
            parts.append(f"{cl} consecutive loss(es) — within normal variance.")

        toxic = ctx.get("rl_toxic", 0)
        if toxic >= 5:
            parts.append(f"{toxic} toxic RL contexts blocked — engine severely constrained.")
        elif toxic >= 1:
            parts.append(f"{toxic} toxic RL context(s) blocked.")
        else:
            parts.append("No toxic RL contexts.")

        ar = ctx.get("rl_allow_rate")
        if ar is not None:
            parts.append(f"Allow rate: {ar:.0%}.")

        return " ".join(parts)

    def _learning_narrative(self, ctx: Dict, flags: Dict) -> str:
        iq     = ctx.get("iq_score")
        mat    = ctx.get("rl_maturity_status", "UNKNOWN")
        conf   = ctx.get("rl_confidence_dir", "UNKNOWN")
        expl   = ctx.get("rl_explore_pressure", "UNKNOWN")
        toxic  = ctx.get("rl_toxic", 0)
        profit = ctx.get("rl_profitable_pct")

        parts = []

        if iq is not None:
            if iq >= 70:
                parts.append(f"Intelligence score STRONG at {iq:.0f}/100.")
            elif iq >= 50:
                parts.append(f"Intelligence score MODERATE at {iq:.0f}/100.")
            elif iq >= 35:
                parts.append(f"Intelligence score LOW at {iq:.0f}/100 — needs more trades.")
            else:
                parts.append(f"Intelligence score CRITICAL at {iq:.0f}/100 — insufficient learning data.")

        if mat:
            parts.append(f"RL maturity: {mat}.")
        if conf:
            parts.append(f"Confidence: {conf}.")
        if expl:
            parts.append(f"Exploration pressure: {expl}.")
        if profit is not None:
            parts.append(f"{profit:.0f}% of RL contexts are profitable.")
        if toxic > 0:
            parts.append(f"{toxic} context(s) blocked as toxic.")

        return " ".join(parts) if parts else "Insufficient RL data for learning narrative."

    def _performance_narrative(self, ctx: Dict, flags: Dict) -> str:
        pnl    = ctx.get("pnl")
        n      = ctx.get("n_trades", 0)
        pf     = ctx.get("profit_factor")
        wr     = ctx.get("win_rate")

        parts = []

        if pnl is not None:
            pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
            parts.append(f"Session PnL: {pnl_str}.")

        if n:
            parts.append(f"{n} trade(s) executed this session.")

        if pf is not None:
            if pf >= 2.0:
                parts.append(f"Profit factor EXCELLENT at {pf:.2f}.")
            elif pf >= 1.5:
                parts.append(f"Profit factor GOOD at {pf:.2f}.")
            elif pf >= 1.0:
                parts.append(f"Profit factor MARGINAL at {pf:.2f}.")
            else:
                parts.append(f"Profit factor BELOW 1.0 at {pf:.2f} — session net-negative.")

        if wr is not None:
            parts.append(f"Win rate: {wr:.0%}.")

        return " ".join(parts) if parts else "No performance data available."

    def _regime_narrative(self, ctx: Dict, flags: Dict) -> str:
        regime = ctx.get("regime", "UNKNOWN")
        parts  = [f"Active regime: {regime}."]

        wr_map = {
            "TRENDING":            ctx.get("le_trending_wr"),
            "MEAN_REVERTING":      ctx.get("le_mean_rev_wr"),
            "VOLATILITY_EXPANSION":ctx.get("le_vol_exp_wr"),
        }
        active_wr = wr_map.get(regime)
        if active_wr is not None:
            quality = (
                "STRONG" if active_wr >= 0.55 else
                "ACCEPTABLE" if active_wr >= 0.45 else
                "WEAK"
            )
            parts.append(f"{regime} win rate {quality} at {active_wr:.0%}.")

        if flags.get("regime_shift"):
            prev = flags.get("prev_regime", "UNKNOWN")
            parts.append(f"Regime recently changed from {prev} — RL adaptation in progress.")

        return " ".join(parts)

    # ── Directives ────────────────────────────────────────────────────────────

    def _directives(self, flags: Dict[str, Any]) -> List[str]:
        """
        Build ordered action list from active condition flags.
        CRITICAL directives always appear first.
        """
        result = []
        for key, text in _DIRECTIVE_CATALOG:
            if flags.get(key):
                result.append(text)
        return result

    # ── Internals ─────────────────────────────────────────────────────────────

    def _update_stats(self, priority: str, now_ms: int) -> None:
        s = self._stats
        s.total_summaries += 1
        s.last_summary_ts  = now_ms
        s.last_priority    = priority
        if priority == PRI_CRITICAL:
            s.critical_count += 1
        elif priority == PRI_HIGH:
            s.high_count += 1
        elif priority == PRI_ROUTINE:
            s.routine_count += 1
        else:
            s.monitoring_count += 1


# ── Context extraction ────────────────────────────────────────────────────────

def _extract(compressed: Dict[str, Any]) -> Dict[str, Any]:
    """Pull all known fields from a compressed snapshot into a flat ctx dict."""
    return {
        "pnl":               compressed.get("pnl"),
        "n_trades":          compressed.get("n_trades", 0),
        "profit_factor":     compressed.get("profit_factor"),
        "win_rate":          compressed.get("win_rate"),
        "iq_score":          compressed.get("iq_score"),
        "rl_toxic":          compressed.get("rl_toxic", 0),
        "consec_losses":     compressed.get("consec_losses", 0),
        "rl_allow_rate":     compressed.get("rl_allow_rate"),
        "rl_maturity_status":compressed.get("rl_maturity_status"),
        "rl_confidence_dir": compressed.get("rl_confidence_dir"),
        "rl_explore_pressure":compressed.get("rl_explore_pressure"),
        "rl_profitable_pct": compressed.get("rl_profitable_pct"),
        "rl_maturity_pct":   compressed.get("rl_maturity_pct"),
        "risk_halted":       compressed.get("risk_halted", False),
        "gate_open":         compressed.get("gate_open", True),
        "regime":            compressed.get("regime"),
        "le_trending_wr":    compressed.get("le_trending_wr"),
        "le_mean_rev_wr":    compressed.get("le_mean_rev_wr"),
        "le_vol_exp_wr":     compressed.get("le_vol_exp_wr"),
        "daily_trades":      compressed.get("daily_trades", 0),
    }


def _condition_flags(
    ctx:        Dict[str, Any],
    anomalies:  List[Dict[str, Any]],
    delta:      Dict[str, Any],
    prev_regime:Optional[str],
) -> Dict[str, Any]:
    """Derive boolean condition flags used by headline, narratives, directives."""
    sev_set = {a.get("severity") for a in anomalies}
    cats    = {a.get("category") for a in anomalies}

    cl     = ctx.get("consec_losses", 0)
    toxic  = ctx.get("rl_toxic", 0)
    ar     = ctx.get("rl_allow_rate", 1.0) or 1.0
    iq     = ctx.get("iq_score", 65.0) or 65.0
    pf     = ctx.get("profit_factor", 1.0) or 1.0
    regime = ctx.get("regime")
    conf   = ctx.get("rl_confidence_dir", "")
    mat    = ctx.get("rl_maturity_status", "")

    # Win rate erosion: check if any regime WR anomaly present
    wr_flags = {a.get("category") for a in anomalies if a.get("category") == "WIN_RATE_EROSION"}

    return {
        "risk_halted":       bool(ctx.get("risk_halted")),
        "gate_closed":       ctx.get("gate_open") is False,
        "toxic_critical":    toxic >= 5,
        "toxic_high":        3 <= toxic < 5,
        "loss_streak_crit":  cl >= 7,
        "loss_streak_high":  5 <= cl < 7,
        "loss_streak_med":   3 <= cl < 5,
        "iq_critical":       iq < 20,
        "iq_high":           20 <= iq < 35,
        "allow_rate_crit":   ar < 0.30,
        "allow_rate_high":   0.30 <= ar < 0.50,
        "confidence_decline":"DECLINING" in (conf or ""),
        "maturity_warming":  "WARMING" in (mat or ""),
        "pf_weak":           pf < 1.0,
        "wr_erosion":        bool(wr_flags),
        "regime_shift":      bool(regime and prev_regime and regime != prev_regime),
        "prev_regime":       prev_regime,
    }


def _worst_severity(anomalies: List[Dict[str, Any]]) -> str:
    _order = {SEV_CRITICAL: 4, SEV_HIGH: 3, SEV_MEDIUM: 2, SEV_LOW: 1}
    if not anomalies:
        return "NONE"
    return max(
        (a.get("severity", SEV_LOW) for a in anomalies),
        key=lambda s: _order.get(s, 0),
        default="NONE",
    )


def _priority_from_ss(ss: float) -> str:
    if ss >= SS_CRITICAL_FLOOR:
        return PRI_CRITICAL
    if ss >= SS_HIGH_FLOOR:
        return PRI_HIGH
    if ss >= SS_ROUTINE_FLOOR:
        return PRI_ROUTINE
    return PRI_MONITORING


# ── Module-level singleton ────────────────────────────────────────────────────
ai_summary_engine = AISummaryEngine()
