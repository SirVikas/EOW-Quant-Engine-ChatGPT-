"""
EOW Quant Engine — Strategic Feed  (FTD-053-GAIA Phase 4)

Categorized intelligence streams that aggregate Phase 1-3 observability
data into themed, prioritized feeds for monitoring, alerting, and sync.

Five feeds — each with a signal strength (0–100), state label, directive,
and data snapshot. Feeds are refreshed atomically on each call to refresh().

Feeds:
  RISK        — engine halt, gate state, loss streak, toxic contexts
  LEARNING    — RL intelligence score, maturity, confidence, explore pressure
  PERFORMANCE — PnL, trade count, profit factor, win rate
  ANOMALY     — active anomalies by severity bucket
  REGIME      — market regime, per-regime win rates

Signal strength rules (per feed):
  RISK:
    100  — engine halted
     80  — gate closed
     60  — 5+ consecutive losses OR 5+ toxic contexts
     40  — 3-4 consecutive losses OR 3 toxic contexts
     20  — 1-2 consecutive losses OR 1-2 toxic contexts OR allow rate < 0.65
      0  — no risk conditions

  LEARNING:
    100  — IQ < 20
     75  — IQ in [20, 35)
     50  — IQ in [35, 50)
     25  — IQ in [50, 65) OR confidence DECLINING
      0  — IQ ≥ 65 AND confidence not DECLINING

  PERFORMANCE:
    100  — PnL < −$200
     75  — PnL < −$100 OR profit_factor < 0.7
     50  — PnL < 0 OR profit_factor < 1.0
     25  — profit_factor < 1.3
      0  — profit_factor ≥ 1.3

  ANOMALY:
    100  — any CRITICAL anomaly
     75  — any HIGH anomaly
     50  — any MEDIUM anomaly
     25  — any LOW anomaly
      0  — no anomalies

  REGIME:
     50  — recent regime shift
     30  — active regime win rate < 42%
     15  — active regime win rate in [42%, 50%)
      0  — active regime win rate ≥ 50%

Feed state labels:
  RISK:        HALTED / BLOCKED / ELEVATED / NOMINAL
  LEARNING:    CRITICAL / STRUGGLING / DEVELOPING / STABLE / MATURING
  PERFORMANCE: LOSING / WEAK / MARGINAL / GOOD / STRONG
  ANOMALY:     CRITICAL / HIGH / MEDIUM / LOW / ALL_CLEAR
  REGIME:      SHIFTING / WEAK / NEUTRAL / ALIGNED
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger

from core.observability.anomaly_detector import SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW


# ── Feed names ────────────────────────────────────────────────────────────────

FEED_RISK        = "RISK"
FEED_LEARNING    = "LEARNING"
FEED_PERFORMANCE = "PERFORMANCE"
FEED_ANOMALY     = "ANOMALY"
FEED_REGIME      = "REGIME"

ALL_FEEDS = (FEED_RISK, FEED_LEARNING, FEED_PERFORMANCE, FEED_ANOMALY, FEED_REGIME)


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class FeedEntry:
    feed:           str
    signal_strength: float          # 0–100
    state:          str
    directive:      str
    data:           Dict[str, Any]
    ts:             int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feed":            self.feed,
            "signal_strength": self.signal_strength,
            "state":           self.state,
            "directive":       self.directive,
            "data":            self.data,
            "ts":              self.ts,
        }


@dataclass
class FeedStats:
    total_refreshes: int = 0
    last_refresh_ts: int = 0


class StrategicFeed:
    """
    Themed intelligence streams. Refresh on every compressed snapshot.
    Each feed independently scored — consumed by sync engine for priority routing.
    """

    MODULE  = "STRATEGIC_FEED"
    VERSION = "1.0"

    def __init__(self) -> None:
        self._feeds:  Dict[str, FeedEntry] = {}
        self._stats   = FeedStats()
        self._prev_regime: Optional[str] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(
        self,
        compressed:   Dict[str, Any],
        anomalies:    Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, FeedEntry]:
        """
        Refresh all five feeds from the latest compressed snapshot + anomalies.
        Returns a dict of feed_name → FeedEntry.
        Never raises.
        """
        try:
            anomalies = anomalies or []
            now_ms    = int(time.time() * 1000)

            feeds: Dict[str, FeedEntry] = {
                FEED_RISK:        self._build_risk_feed(compressed, now_ms),
                FEED_LEARNING:    self._build_learning_feed(compressed, now_ms),
                FEED_PERFORMANCE: self._build_performance_feed(compressed, now_ms),
                FEED_ANOMALY:     self._build_anomaly_feed(anomalies, now_ms),
                FEED_REGIME:      self._build_regime_feed(compressed, now_ms),
            }

            self._feeds               = feeds
            self._prev_regime         = compressed.get("regime")
            self._stats.total_refreshes += 1
            self._stats.last_refresh_ts  = now_ms

            return feeds

        except Exception as exc:
            logger.warning(f"[{self.MODULE}] refresh error: {exc}")
            return {}

    def get_feed(self, feed_name: str) -> Optional[FeedEntry]:
        """Return the current state of a named feed. None if not yet refreshed."""
        return self._feeds.get(feed_name)

    def get_priority_feeds(self, min_strength: float = 50.0) -> List[FeedEntry]:
        """
        Return feeds with signal_strength ≥ min_strength, sorted descending.
        Used by sync engine to determine what needs immediate upload.
        """
        try:
            return sorted(
                [f for f in self._feeds.values() if f.signal_strength >= min_strength],
                key=lambda f: f.signal_strength,
                reverse=True,
            )
        except Exception:
            return []

    def get_all_feeds(self) -> List[Dict[str, Any]]:
        """Return all current feeds as serializable dicts."""
        return [f.to_dict() for f in self._feeds.values()]

    def max_signal_strength(self) -> float:
        """Highest signal strength across all feeds."""
        if not self._feeds:
            return 0.0
        return max(f.signal_strength for f in self._feeds.values())

    def status(self) -> Dict[str, Any]:
        s = self._stats
        return {
            "module":          self.MODULE,
            "version":         self.VERSION,
            "total_refreshes": s.total_refreshes,
            "last_refresh_ts": s.last_refresh_ts,
            "feeds_active":    len(self._feeds),
            "max_signal":      self.max_signal_strength(),
            "feed_states": {
                name: {"state": f.state, "strength": f.signal_strength}
                for name, f in self._feeds.items()
            },
        }

    # ── Feed builders ─────────────────────────────────────────────────────────

    def _build_risk_feed(self, c: Dict, ts: int) -> FeedEntry:
        halted  = bool(c.get("risk_halted"))
        gate    = c.get("gate_open", True)
        cl      = int(c.get("consec_losses", 0) or 0)
        toxic   = int(c.get("rl_toxic", 0) or 0)
        ar      = float(c.get("rl_allow_rate", 1.0) or 1.0)

        if halted:
            ss, state = 100.0, "HALTED"
            directive = "Halt active — investigate risk controller and review session drawdown"
        elif not gate:
            ss, state = 80.0, "BLOCKED"
            directive = "Gate is closed — check daily loss limits and exposure caps"
        elif cl >= 5 or toxic >= 5:
            ss, state = 60.0, "ELEVATED"
            directive = "Elevated risk conditions — reduce trade frequency and review strategy"
        elif cl >= 3 or toxic >= 3:
            ss, state = 40.0, "ELEVATED"
            directive = "Monitor loss streak and toxic context accumulation"
        elif cl >= 1 or toxic >= 1 or ar < 0.65:
            ss, state = 20.0, "NOMINAL"
            directive = "Minor risk signals — continue normal operations with heightened awareness"
        else:
            ss, state = 0.0, "NOMINAL"
            directive = "No active risk conditions"

        return FeedEntry(
            feed=FEED_RISK, signal_strength=ss, state=state,
            directive=directive, ts=ts,
            data={
                "risk_halted":   halted,
                "gate_open":     gate,
                "consec_losses": cl,
                "rl_toxic":      toxic,
                "rl_allow_rate": ar,
            },
        )

    def _build_learning_feed(self, c: Dict, ts: int) -> FeedEntry:
        iq   = float(c.get("iq_score", 0) or 0)
        mat  = c.get("rl_maturity_status", "UNKNOWN") or "UNKNOWN"
        conf = c.get("rl_confidence_dir", "UNKNOWN") or "UNKNOWN"
        expl = c.get("rl_explore_pressure", "UNKNOWN") or "UNKNOWN"
        pct  = float(c.get("rl_maturity_pct", 0) or 0)

        if iq < 20:
            ss, state = 100.0, "CRITICAL"
            directive = "IQ critically low — insufficient learning data; avoid parameter changes"
        elif iq < 35:
            ss, state = 75.0, "STRUGGLING"
            directive = "IQ low — allow engine to accumulate more trades before tuning"
        elif iq < 50:
            ss, state = 50.0, "DEVELOPING"
            directive = "IQ developing — monitor trend; avoid aggressive config changes"
        elif iq < 65 or "DECLINING" in conf:
            ss, state = 25.0, "STABLE"
            directive = "IQ moderate — continue observation; confidence may need attention"
        else:
            ss, state = 0.0, "MATURING"
            directive = "RL engine performing well — no learning intervention needed"

        return FeedEntry(
            feed=FEED_LEARNING, signal_strength=ss, state=state,
            directive=directive, ts=ts,
            data={
                "iq_score":           iq,
                "rl_maturity_status": mat,
                "rl_confidence_dir":  conf,
                "rl_explore_pressure": expl,
                "rl_maturity_pct":    pct,
            },
        )

    def _build_performance_feed(self, c: Dict, ts: int) -> FeedEntry:
        pnl = c.get("pnl")
        pf  = c.get("profit_factor")
        wr  = c.get("win_rate")
        n   = int(c.get("n_trades", 0) or 0)

        # Compute signal strength
        ss = 0.0
        if pnl is not None and pnl < -200:
            ss = 100.0
        elif (pnl is not None and pnl < -100) or (pf is not None and pf < 0.7):
            ss = 75.0
        elif (pnl is not None and pnl < 0) or (pf is not None and pf < 1.0):
            ss = 50.0
        elif pf is not None and pf < 1.3:
            ss = 25.0

        if ss >= 75:
            state, directive = "LOSING", "Session significantly negative — review strategy suitability for current regime"
        elif ss >= 50:
            state, directive = "WEAK", "Performance below target — monitor closely and consider reducing size"
        elif ss >= 25:
            state, directive = "MARGINAL", "Performance marginal — profitable but watch profit factor trend"
        elif n == 0:
            state, directive = "GOOD", "No trades yet this session"
        elif pf is not None and pf >= 2.0:
            state, directive = "STRONG", "Excellent performance — strategy well-aligned with regime"
        else:
            state, directive = "GOOD", "Performance within acceptable range"

        return FeedEntry(
            feed=FEED_PERFORMANCE, signal_strength=ss, state=state,
            directive=directive, ts=ts,
            data={
                "pnl":           pnl,
                "n_trades":      n,
                "profit_factor": pf,
                "win_rate":      wr,
            },
        )

    def _build_anomaly_feed(self, anomalies: List[Dict], ts: int) -> FeedEntry:
        sev_order = {SEV_CRITICAL: 4, SEV_HIGH: 3, SEV_MEDIUM: 2, SEV_LOW: 1}

        counts = {SEV_CRITICAL: 0, SEV_HIGH: 0, SEV_MEDIUM: 0, SEV_LOW: 0}
        for a in anomalies:
            sev = a.get("severity", SEV_LOW)
            counts[sev] = counts.get(sev, 0) + 1

        if counts[SEV_CRITICAL] > 0:
            ss, state = 100.0, "CRITICAL"
            directive = f"{counts[SEV_CRITICAL]} CRITICAL anomaly(ies) active — immediate attention required"
        elif counts[SEV_HIGH] > 0:
            ss, state = 75.0, "HIGH"
            directive = f"{counts[SEV_HIGH]} HIGH anomaly(ies) — performance significantly degraded"
        elif counts[SEV_MEDIUM] > 0:
            ss, state = 50.0, "MEDIUM"
            directive = f"{counts[SEV_MEDIUM]} MEDIUM anomaly(ies) — concerning trend detected"
        elif counts[SEV_LOW] > 0:
            ss, state = 25.0, "LOW"
            directive = f"{counts[SEV_LOW]} LOW anomaly(ies) — informational, no action needed"
        else:
            ss, state = 0.0, "ALL_CLEAR"
            directive = "No active anomalies — system operating normally"

        # Top anomaly descriptions (up to 3)
        top = [a.get("description", "") for a in anomalies if a.get("severity") in (SEV_CRITICAL, SEV_HIGH)][:3]

        return FeedEntry(
            feed=FEED_ANOMALY, signal_strength=ss, state=state,
            directive=directive, ts=ts,
            data={
                "total":          len(anomalies),
                "critical_count": counts[SEV_CRITICAL],
                "high_count":     counts[SEV_HIGH],
                "medium_count":   counts[SEV_MEDIUM],
                "low_count":      counts[SEV_LOW],
                "top_alerts":     top,
            },
        )

    def _build_regime_feed(self, c: Dict, ts: int) -> FeedEntry:
        regime     = c.get("regime", "UNKNOWN")
        prev_r     = self._prev_regime
        shifted    = bool(prev_r and prev_r != regime)

        wr_map = {
            "TRENDING":             c.get("le_trending_wr"),
            "MEAN_REVERTING":       c.get("le_mean_rev_wr"),
            "VOLATILITY_EXPANSION": c.get("le_vol_exp_wr"),
        }
        active_wr = wr_map.get(regime)

        if shifted:
            ss, state = 50.0, "SHIFTING"
            directive = f"Regime changed {prev_r}→{regime} — allow RL engine to adapt before scaling"
        elif active_wr is not None and active_wr < 0.42:
            ss, state = 30.0, "WEAK"
            directive = f"{regime} win rate weak at {active_wr:.0%} — reduce frequency or review strategy fit"
        elif active_wr is not None and active_wr < 0.50:
            ss, state = 15.0, "NEUTRAL"
            directive = f"{regime} win rate moderate at {active_wr:.0%} — monitor trend"
        else:
            ss, state = 0.0, "ALIGNED"
            directive = f"{regime} regime performing well — continue current strategy mix"

        return FeedEntry(
            feed=FEED_REGIME, signal_strength=ss, state=state,
            directive=directive, ts=ts,
            data={
                "regime":           regime,
                "prev_regime":      prev_r,
                "regime_shifted":   shifted,
                "le_trending_wr":   c.get("le_trending_wr"),
                "le_mean_rev_wr":   c.get("le_mean_rev_wr"),
                "le_vol_exp_wr":    c.get("le_vol_exp_wr"),
                "active_regime_wr": active_wr,
            },
        )


# ── Module-level singleton ────────────────────────────────────────────────────
strategic_feed = StrategicFeed()
