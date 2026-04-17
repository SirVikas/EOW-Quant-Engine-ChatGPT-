"""
EOW Quant Engine — Guardian Logic (Autonomous Safety Veto)

Institutional-grade safety layer operating in two modes:

  Proactive  — Validates every user aggression change BEFORE applying it.
               If the requested level would push projected Risk-of-Ruin above
               ROR_VETO_THRESHOLD (1%), the change is blocked and the reason
               is broadcast to the dashboard.

  Reactive   — Called every heal cycle.  If live RoR drifts above 2× threshold
               or current drawdown breaches MDD_VETO_THRESHOLD (12%), the
               Guardian autonomously downgrades aggression and activates
               safe-mode until conditions recover.

Design principle: "Nidar (Fearless) but Never Reckless."
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from loguru import logger


# ── Aggression Profiles ───────────────────────────────────────────────────────
# Each level maps to a concrete set of risk parameters applied to cfg at runtime.
AGGRESSION_PROFILES: dict[int, dict] = {
    1: {
        "name":              "Conservative",
        "emoji":             "🛡",
        "description":       "Capital preservation mode. Minimum position size. Best for drawdown recovery.",
        "max_risk_per_trade": 0.005,
        "kelly_fraction":    0.15,
        "atr_mult_sl":       2.5,
        "atr_mult_tp":       4.5,
    },
    2: {
        "name":              "Balanced",
        "emoji":             "⚖",
        "description":       "Default engine settings. Optimal risk-adjusted returns. Recommended baseline.",
        "max_risk_per_trade": 0.015,
        "kelly_fraction":    0.25,
        "atr_mult_sl":       2.0,
        "atr_mult_tp":       3.0,
    },
    3: {
        "name":              "Aggressive",
        "emoji":             "⚡",
        "description":       "Higher position size. Requires Deployability ≥ 70 and win-rate ≥ 55%.",
        "max_risk_per_trade": 0.025,
        "kelly_fraction":    0.35,
        "atr_mult_sl":       1.8,
        "atr_mult_tp":       2.8,
    },
    4: {
        "name":              "DHURANDHAR",
        "emoji":             "🔥",
        "description":       "Maximum aggression. Guardian continuously monitors. Only activate with proven edge and Deployability ≥ 85.",
        "max_risk_per_trade": 0.040,
        "kelly_fraction":    0.50,
        "atr_mult_sl":       1.5,
        "atr_mult_tp":       2.5,
    },
}

# Safety thresholds
ROR_VETO_THRESHOLD   = 1.0    # % — block if projected RoR exceeds this
ROR_REACTIVE_MULT    = 2.0    # reactive veto at 2× threshold (2%)
MDD_VETO_THRESHOLD   = 12.0   # % — block aggression increase if MDD ≥ this
MDD_EMERGENCY_LEVEL  = 10.0   # % — force downgrade to Conservative if MDD ≥ this

# Grace window: after a MANUAL aggression change, suppress reactive auto-downgrade
# for this many minutes so the system has time to prove itself.
MANUAL_GRACE_MINUTES = 30


# ── Data ──────────────────────────────────────────────────────────────────────

@dataclass
class VetoEvent:
    ts:              int   = field(default_factory=lambda: int(time.time() * 1000))
    reason:          str   = ""
    requested_level: int   = 0
    reverted_to:     int   = 0
    ror_at_veto:     float = 0.0
    mdd_at_veto:     float = 0.0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _estimate_ror(win_rate: float, avg_r_win: float, avg_r_loss: float,
                  account_units: int = 20) -> float:
    """Gambler's-ruin RoR estimate (mirrors analytics.risk_of_ruin)."""
    if win_rate >= 1.0:
        return 0.0
    if win_rate <= 0.0:
        return 100.0
    if avg_r_win <= 0 or avg_r_loss <= 0:
        return 100.0
    p = win_rate
    q = 1.0 - p
    edge = p * avg_r_win - q * avg_r_loss
    if edge <= 0:
        return 100.0
    total = p * avg_r_win + q * avg_r_loss
    edge_ratio = edge / total
    base = (1.0 - edge_ratio) / (1.0 + edge_ratio)
    if base <= 0:
        return 0.0
    return round(min(base ** account_units * 100.0, 100.0), 4)


# ── GuardianLogic ─────────────────────────────────────────────────────────────

class GuardianLogic:
    """
    Two-mode autonomous safety layer.

    Usage:
        guardian = GuardianLogic()
        ok, msg = guardian.validate_and_apply(requested_level, win_rate, mdd, r_win, r_loss, cfg)
        alert   = guardian.reactive_check(win_rate, mdd, r_win, r_loss, cfg)
    """

    def __init__(self):
        self._level:              int          = 2        # Balanced by default
        self._safe_mode:          bool         = False
        self._last_msg:           str          = ""
        self._veto_log:           List[VetoEvent] = []
        # Timestamp (ms) of the last MANUAL aggression change by the user.
        # Reactive auto-downgrade is suppressed for MANUAL_GRACE_MINUTES after this.
        self._manual_change_ts:   int          = 0

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def level(self) -> int:
        return self._level

    @property
    def profile(self) -> dict:
        return AGGRESSION_PROFILES[self._level]

    @property
    def safe_mode(self) -> bool:
        return self._safe_mode

    # ── Internal ──────────────────────────────────────────────────────────────

    def _record_veto(self, reason: str, requested: int, reverted_to: int,
                     ror: float = 0.0, mdd: float = 0.0) -> VetoEvent:
        ev = VetoEvent(reason=reason, requested_level=requested,
                       reverted_to=reverted_to, ror_at_veto=ror, mdd_at_veto=mdd)
        self._veto_log.append(ev)
        self._veto_log = self._veto_log[-100:]
        self._last_msg = reason
        logger.warning(f"[GUARDIAN] {reason}")
        return ev

    def _apply_profile(self, level: int, cfg_obj) -> None:
        """Write profile risk parameters to the live cfg singleton."""
        p = AGGRESSION_PROFILES[level]
        cfg_obj.MAX_RISK_PER_TRADE = p["max_risk_per_trade"]
        cfg_obj.KELLY_FRACTION     = p["kelly_fraction"]
        cfg_obj.ATR_MULT_SL        = p["atr_mult_sl"]
        cfg_obj.ATR_MULT_TP        = p["atr_mult_tp"]

    def _project_ror(self, level: int, win_rate: float,
                     avg_r_win: float, avg_r_loss: float) -> float:
        """Project RoR for a candidate aggression level."""
        if win_rate <= 0:
            return 0.0
        new_risk = AGGRESSION_PROFILES[level]["max_risk_per_trade"]
        baseline = 0.015   # Balanced baseline
        scale    = new_risk / baseline
        # R-multiples scale with position size
        adj_win  = max(avg_r_win  * scale, 0.01)
        adj_loss = max(avg_r_loss * scale, 0.01)
        return _estimate_ror(win_rate, adj_win, adj_loss)

    # ── Public API ────────────────────────────────────────────────────────────

    def validate_and_apply(
        self,
        requested_level: int,
        win_rate_pct: float,
        mdd_pct: float,
        avg_r_win: float,
        avg_r_loss: float,
        cfg_obj,
    ) -> tuple[bool, str]:
        """
        Validate a requested aggression change and apply it if safe.

        Returns (allowed: bool, message: str).
        """
        if requested_level not in AGGRESSION_PROFILES:
            return False, f"Invalid aggression level {requested_level} — must be 1-4."

        win_rate = win_rate_pct / 100.0
        p_name   = AGGRESSION_PROFILES[requested_level]["name"]
        p_emoji  = AGGRESSION_PROFILES[requested_level]["emoji"]

        # Veto 1 — projected RoR
        projected_ror = self._project_ror(requested_level, win_rate, avg_r_win, avg_r_loss)
        if projected_ror > ROR_VETO_THRESHOLD:
            reason = (
                f"Guardian Veto: {p_emoji} {p_name} would push Risk-of-Ruin to "
                f"{projected_ror:.2f}% (limit: {ROR_VETO_THRESHOLD}%). "
                f"Improve win-rate or reduce losses before escalating. "
                f"Staying at {AGGRESSION_PROFILES[self._level]['name']}."
            )
            self._record_veto(reason, requested_level, self._level, projected_ror, mdd_pct)
            return False, reason

        # Veto 2 — current drawdown blocks upward moves
        if mdd_pct >= MDD_VETO_THRESHOLD and requested_level > self._level:
            reason = (
                f"Guardian Veto: Current drawdown {mdd_pct:.1f}% ≥ {MDD_VETO_THRESHOLD}%. "
                f"Cannot escalate aggression during active drawdown. "
                f"Wait for equity recovery before switching to {p_name}."
            )
            self._record_veto(reason, requested_level, self._level, projected_ror, mdd_pct)
            return False, reason

        # ── Approved — apply the change ───────────────────────────────────────
        old_name    = AGGRESSION_PROFILES[self._level]["name"]
        self._apply_profile(requested_level, cfg_obj)
        self._level          = requested_level
        self._safe_mode      = False
        self._manual_change_ts = int(time.time() * 1000)   # start grace window
        p = AGGRESSION_PROFILES[requested_level]
        msg = (
            f"Guardian approved: {p['emoji']} {p['name']} activated "
            f"(was {old_name}). Risk/trade: {p['max_risk_per_trade']*100:.1f}%, "
            f"Kelly: {p['kelly_fraction']*100:.0f}%, "
            f"Projected RoR: {projected_ror:.4f}%."
        )
        self._last_msg = msg
        logger.info(f"[GUARDIAN] {msg}")
        return True, msg

    def reactive_check(
        self,
        win_rate_pct: float,
        mdd_pct: float,
        avg_r_win: float,
        avg_r_loss: float,
        cfg_obj,
    ) -> Optional[str]:
        """
        Periodic safety check — called every heal cycle.
        If live RoR or MDD has drifted into danger, auto-downgrade aggression.
        Returns an alert message if Guardian intervened, None otherwise.
        """
        win_rate = win_rate_pct / 100.0
        if win_rate <= 0 or self._level <= 1:
            return None

        live_ror = self._project_ror(self._level, win_rate, avg_r_win, avg_r_loss)

        # Respect the manual grace window: if the user just set an aggression level,
        # give the system MANUAL_GRACE_MINUTES to prove itself before auto-downgrading.
        grace_elapsed_s = (int(time.time() * 1000) - self._manual_change_ts) / 1000
        in_grace = grace_elapsed_s < MANUAL_GRACE_MINUTES * 60
        if in_grace:
            remaining_min = (MANUAL_GRACE_MINUTES * 60 - grace_elapsed_s) / 60
            logger.debug(
                f"[GUARDIAN] Grace window active — {remaining_min:.1f} min remaining, "
                "skipping reactive check."
            )
            return None

        needs_downgrade = (
            (live_ror > ROR_VETO_THRESHOLD * ROR_REACTIVE_MULT and self._level >= 3)
            or (mdd_pct >= MDD_VETO_THRESHOLD and self._level >= 3)
        )

        if needs_downgrade:
            safe_level = 1 if mdd_pct >= MDD_EMERGENCY_LEVEL else 2
            old_name   = AGGRESSION_PROFILES[self._level]["name"]
            self._apply_profile(safe_level, cfg_obj)
            reason = (
                f"Guardian AUTO-DOWNGRADE: {old_name} → "
                f"{AGGRESSION_PROFILES[safe_level]['emoji']} {AGGRESSION_PROFILES[safe_level]['name']}. "
                f"Live RoR {live_ror:.2f}% or MDD {mdd_pct:.1f}% breached safety thresholds."
            )
            self._record_veto(reason, self._level, safe_level, live_ror, mdd_pct)
            self._level     = safe_level
            self._safe_mode = True
            return reason

        # Clear safe-mode when metrics have recovered
        if self._safe_mode and live_ror < 0.3 and mdd_pct < 5.0:
            self._safe_mode = False
            msg = "Guardian: Safe-mode cleared — risk metrics have recovered to normal range."
            self._last_msg = msg
            logger.info(f"[GUARDIAN] {msg}")
            return msg

        return None

    def snapshot(self) -> dict:
        """Full state snapshot for the dashboard API."""
        p = AGGRESSION_PROFILES[self._level]
        vetoes = [v for v in self._veto_log if v.reverted_to != v.requested_level]
        grace_elapsed_s  = (int(time.time() * 1000) - self._manual_change_ts) / 1000
        grace_remaining_s = max(0.0, MANUAL_GRACE_MINUTES * 60 - grace_elapsed_s)
        return {
            "level":             self._level,
            "profile_name":      p["name"],
            "profile_emoji":     p["emoji"],
            "safe_mode":         self._safe_mode,
            "last_message":      self._last_msg,
            "veto_count":        len(vetoes),
            "grace_remaining_s": round(grace_remaining_s, 0),
            "last_veto":     {
                "ts":          vetoes[-1].ts,
                "reason":      vetoes[-1].reason,
                "reverted_to": vetoes[-1].reverted_to,
                "ror_at_veto": vetoes[-1].ror_at_veto,
            } if vetoes else None,
            "all_profiles":  AGGRESSION_PROFILES,
            "ts":            int(time.time() * 1000),
        }
