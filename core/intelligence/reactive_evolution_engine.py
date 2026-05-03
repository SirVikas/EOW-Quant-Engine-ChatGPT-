"""
EOW Quant Engine — core/intelligence/reactive_evolution_engine.py
FTD-REA-001 / FTD-SNP-001: Reactive Evolution Engine (Sniper Mode Upgrade)

Real-time, loss-triggered micro-adaptation. Fires immediately after every
closed losing trade — no waiting for a full 5-min AIE cycle.

Six behaviours (v2 — Sniper Mode):
  1. MINI-AUDIT         Diagnose every SL hit as VOLATILITY_SLIP, FEE_TOXIC,
                        or NORMAL_SL.
  2. MICRO-ADJUST       Update per-symbol RSI bands and ATR multipliers based
                        on diagnosis. Changes are DNA-compatible and picked up
                        by the next signal for that symbol.
  3. ADAPTIVE AGGRESSION After volatility/slip loss, tighten SL (smaller loss
                        if it happens again) and widen TP (better RR).
  4. PROFIT-CENTRIC     Fee-toxic patterns are suppressed immediately. Goal is
                        net profit after expenses, not raw win count.
  5. CONSECUTIVE BRAKE  3 losses in a row on same symbol → brake RSI for 2h.
                        score_min raised to 0.60 to block low-quality re-entries.
  6. ATR VOLATILITY GATE Track slow EMA of ATR% per symbol. If current ATR >
                        2× rolling average → is_high_volatility() → block entry.
  7. FEEDBACK LOOP      Every adjustment is recorded with full before/after
                        state and forwarded to EvolutionTracker for audit trail.

Adjustment bounds prevent over-correction:
  - rsi_ob min 55 / rsi_os max 45  (still allows entries, just tighter)
  - atr_sl 0.6–2.0 / atr_tp 1.5–5.0
  - Max 5 consecutive adjustments per symbol before freeze
  - Win decay: after 3 wins, params nudge 10% back towards defaults

Change categories (FTD-SNP-001 reporting):
  FEE_TOXIC        → EXPENSE_REDUCTION
  VOLATILITY_SLIP  → CAPITAL_PROTECTION
  NORMAL_SL        → ENTRY_REFINEMENT

Design: singleton, stateless per call, per-symbol state in memory.
"""
from __future__ import annotations

import pathlib
import json
import time
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

from loguru import logger


# ── Parameter Defaults & Bounds ───────────────────────────────────────────────

RSI_OB_DEFAULT   = 70.0
RSI_OS_DEFAULT   = 30.0
ATR_SL_DEFAULT   = 1.0
ATR_TP_DEFAULT   = 2.0

RSI_OB_MIN       = 55.0   # never tighten entry past this
RSI_OS_MAX       = 45.0
ATR_SL_MIN       = 0.6
ATR_SL_MAX       = 2.0
ATR_TP_MIN       = 1.5
ATR_TP_MAX       = 5.0

MAX_CONSEC_ADJ   = 5      # freeze symbol params after this many adjustments in a row
DECAY_AFTER_WINS = 3      # wins needed to nudge params back towards defaults

FEE_TOXIC_RATIO          = 0.50   # fee > 50% of gross win → FEE_TOXIC
FEE_TOXIC_SUPPRESS_MIN   = 15     # suppress symbol for 15 minutes after fee-toxic loss

# Sniper Mode: consecutive loss brake
CONSEC_LOSS_BRAKE_THRESHOLD = 3   # 3 losses in a row → brake
CONSEC_LOSS_BRAKE_MINUTES   = 120 # brake RSI tighten + raise score_min for 2 hours
BRAKE_SCORE_MIN_OVERRIDE    = 0.60  # raised floor while braking

# Sniper Mode: fee throttle per symbol
FEE_THROTTLE_WINDOW    = 10       # last N trades for fee drag check
FEE_THROTTLE_RATIO     = 0.15     # fee > 15% of gross in last N trades → throttle
FEE_THROTTLE_SCORE_MIN = 0.55     # raised score_min when fee-dragging

# Sniper Mode: ATR volatility gate
ATR_EMA_ALPHA     = 0.02          # slow EMA alpha (≈50-period EMA)
ATR_SPIKE_MULT    = 2.0           # current ATR > 2× slow EMA → high volatility

# Adjustment step sizes
RSI_TIGHTEN_STEP  = 3.0   # rsi_ob reduced / rsi_os raised by this on EARLY_ENTRY
ATR_SL_STEP       = 0.10  # atr_sl reduced by this on VOLATILITY_SLIP
ATR_TP_STEP       = 0.15  # atr_tp raised  by this on VOLATILITY_SLIP
ATR_SL_STEP_SMALL = 0.05  # smaller step for NORMAL_SL
ATR_TP_STEP_SMALL = 0.08

# Category labels for reporting
_CATEGORY = {
    "FEE_TOXIC":       "EXPENSE_REDUCTION",
    "VOLATILITY_SLIP": "CAPITAL_PROTECTION",
    "NORMAL_SL":       "ENTRY_REFINEMENT",
}

REACTIVE_REPORT_PATH = pathlib.Path("reports/auto_intelligence/reactive_adjustments.json")


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class ReactiveAdjustment:
    ts:           int
    ts_fmt:       str
    symbol:       str
    strategy_id:  str
    trade_pnl:    float
    r_multiple:   float
    diagnosis:    str    # VOLATILITY_SLIP | FEE_TOXIC | NORMAL_SL
    category:     str    # CAPITAL_PROTECTION | EXPENSE_REDUCTION | ENTRY_REFINEMENT
    changes:      Dict[str, Any] = field(default_factory=dict)
    note:         str = ""


# ── Engine ────────────────────────────────────────────────────────────────────

class ReactiveEvolutionEngine:
    """
    FTD-REA-001 / FTD-SNP-001 — Loss-triggered per-symbol micro-adaptation.
    Called from on_tick after every closed trade.
    """

    MODULE = "REACTIVE_EVOLUTION"

    def __init__(self):
        # per-symbol param state
        self._overrides:   Dict[str, Dict[str, Any]] = {}
        # per-symbol recent trade fee records for fee throttle: list of (gross_pnl, fee)
        self._fee_log:     Dict[str, List[tuple]] = {}
        # per-symbol slow ATR EMA for volatility gate
        self._atr_ema:     Dict[str, float] = {}
        # full ordered adjustment log
        self._adjustments: List[Dict[str, Any]] = []

        logger.info(
            f"[REA-001] Reactive Evolution Engine online | "
            f"rsi_step={RSI_TIGHTEN_STEP} atr_sl_step={ATR_SL_STEP} "
            f"fee_toxic_thr={FEE_TOXIC_RATIO:.0%} max_adj={MAX_CONSEC_ADJ} "
            f"decay_after={DECAY_AFTER_WINS} wins | "
            f"sniper: brake_at={CONSEC_LOSS_BRAKE_THRESHOLD}L/{CONSEC_LOSS_BRAKE_MINUTES}min "
            f"fee_throttle={FEE_THROTTLE_RATIO:.0%}/{FEE_THROTTLE_WINDOW}t "
            f"atr_spike={ATR_SPIKE_MULT}×EMA"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def on_trade_closed(
        self,
        symbol:       str,
        strategy_id:  str,
        net_pnl:      float,
        r_multiple:   float,
        gross_pnl:    float,
        fee_total:    float,
        atr_pct:      float,
        side:         str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Main entry point — call after every trade close.
        On wins: decay params toward defaults.
        On losses: diagnose and micro-adjust.
        Returns the adjustment dict if anything changed, else None.
        """
        # Always record fee data and update ATR EMA (wins and losses both matter)
        self._record_fee(symbol, gross_pnl, fee_total)
        self._update_atr_ema(symbol, atr_pct)

        if net_pnl >= 0:
            self._decay_on_win(symbol)
            return None

        # Track consecutive losses for brake
        state = self._ensure_state(symbol)
        state["consecutive_losses"] = state.get("consecutive_losses", 0) + 1
        state["wins_since_adj"] = 0   # reset win counter on loss

        diagnosis = self._diagnose(
            r_multiple=r_multiple,
            gross_pnl=gross_pnl,
            fee_total=fee_total,
        )

        adj = self._apply(
            symbol=symbol,
            strategy_id=strategy_id,
            net_pnl=net_pnl,
            r_multiple=r_multiple,
            diagnosis=diagnosis,
            fee_total=fee_total,
            gross_pnl=gross_pnl,
        )

        if adj is not None:
            adj_dict = asdict(adj)
            self._adjustments.append(adj_dict)
            self._persist()
            # forward to evolution tracker audit trail
            try:
                from core.intelligence.evolution_tracker import evolution_tracker
                evolution_tracker.record_reactive_adjustment(adj_dict)
            except Exception:
                pass

        return asdict(adj) if adj is not None else None

    def get_overrides(self, symbol: str) -> Dict[str, float]:
        """
        Returns DNA-compatible param overrides for this symbol.
        Keys match strategy __init__ params: rsi_ob, rsi_os, atr_sl, atr_tp.
        Returns {} if symbol is suppressed or has no active overrides.
        """
        state = self._overrides.get(symbol)
        if not state:
            return {}
        if state.get("suppressed_until", 0) > time.time():
            return {}
        if state.get("brake_until", 0) > time.time():
            # During brake: tighten RSI entries so only strong signals pass
            return {
                "rsi_ob": max(RSI_OB_MIN, state.get("rsi_ob", RSI_OB_DEFAULT) - RSI_TIGHTEN_STEP),
                "rsi_os": min(RSI_OS_MAX, state.get("rsi_os", RSI_OS_DEFAULT) + RSI_TIGHTEN_STEP),
                "atr_sl": state.get("atr_sl", ATR_SL_DEFAULT),
                "atr_tp": state.get("atr_tp", ATR_TP_DEFAULT),
            }
        # Only return params that differ from defaults (avoid polluting clean symbols)
        out = {}
        for k, default in (
            ("rsi_ob", RSI_OB_DEFAULT),
            ("rsi_os", RSI_OS_DEFAULT),
            ("atr_sl", ATR_SL_DEFAULT),
            ("atr_tp", ATR_TP_DEFAULT),
        ):
            if abs(state.get(k, default) - default) > 0.001:
                out[k] = state[k]
        return out

    def get_score_min_override(self, symbol: str) -> Optional[float]:
        """
        Returns a raised score_min floor if the symbol is fee-dragging or
        in consecutive-loss-brake mode. Returns None if no override applies.
        """
        state = self._overrides.get(symbol, {})
        overrides = []

        # Consecutive loss brake
        if state.get("brake_until", 0) > time.time():
            overrides.append(BRAKE_SCORE_MIN_OVERRIDE)

        # Fee throttle: check last FEE_THROTTLE_WINDOW trades for this symbol
        fee_records = self._fee_log.get(symbol, [])
        if len(fee_records) >= FEE_THROTTLE_WINDOW:
            recent = fee_records[-FEE_THROTTLE_WINDOW:]
            total_gross = sum(abs(g) for g, _ in recent if g > 0)
            total_fee   = sum(f for _, f in recent if f > 0)
            if total_gross > 1e-6 and total_fee / total_gross > FEE_THROTTLE_RATIO:
                overrides.append(FEE_THROTTLE_SCORE_MIN)
                logger.debug(
                    f"[REA-001] FEE_THROTTLE {symbol} "
                    f"fee_pct={total_fee/total_gross:.1%} → score_min={FEE_THROTTLE_SCORE_MIN}"
                )

        return max(overrides) if overrides else None

    def is_suppressed(self, symbol: str) -> bool:
        state = self._overrides.get(symbol, {})
        return state.get("suppressed_until", 0) > time.time()

    def is_high_volatility(self, symbol: str, current_atr_pct: float) -> bool:
        """
        Returns True if current ATR% is more than ATR_SPIKE_MULT × slow EMA.
        Used as ATR volatility gate in main.py to block spiky entries.
        """
        if current_atr_pct <= 0:
            return False
        ema = self._atr_ema.get(symbol, 0.0)
        if ema <= 0:
            return False
        spike = current_atr_pct > ema * ATR_SPIKE_MULT
        if spike:
            logger.debug(
                f"[REA-001] ATR_SPIKE {symbol}: cur={current_atr_pct:.4f}% "
                f"ema={ema:.4f}% ratio={current_atr_pct/ema:.1f}×"
            )
        return spike

    def get_fee_efficiency(self, recent_trades: List[Any]) -> Dict[str, Any]:
        """
        Compute fee efficiency stats for a list of closed trades.
        Each trade must have .net_pnl and optionally .fee_entry/.fee_exit.
        Used by /api/evolution-status for reporting.
        """
        if not recent_trades:
            return {"status": "NO_DATA"}

        total_gross = 0.0
        total_fees  = 0.0
        total_net   = 0.0
        fee_toxic_count = 0

        for t in recent_trades:
            net  = getattr(t, "net_pnl", 0.0)
            fee  = (getattr(t, "fee_entry", 0.0) + getattr(t, "fee_exit", 0.0))
            gross = net + fee
            total_gross += abs(gross) if gross > 0 else 0.0
            total_fees  += fee
            total_net   += net
            if gross > 1e-6 and fee / gross > FEE_TOXIC_RATIO:
                fee_toxic_count += 1

        fee_pct = total_fees / max(total_gross, 1e-6) * 100
        return {
            "total_gross_pnl":  round(total_gross, 4),
            "total_fees":       round(total_fees, 4),
            "total_net_pnl":    round(total_net, 4),
            "fee_pct_of_gross": round(fee_pct, 2),
            "fee_toxic_trades": fee_toxic_count,
            "fee_status":       "CRITICAL" if fee_pct > 30 else ("WARNING" if fee_pct > 15 else "OK"),
            "throttle_active":  fee_pct > FEE_THROTTLE_RATIO * 100,
        }

    def summary(self) -> Dict[str, Any]:
        now = time.time()
        suppressed = [s for s, st in self._overrides.items()
                      if st.get("suppressed_until", 0) > now]
        braked     = [s for s, st in self._overrides.items()
                      if st.get("brake_until", 0) > now]
        active     = {s: st for s, st in self._overrides.items()
                      if st.get("suppressed_until", 0) <= now and s in self._overrides}

        # Aggregate adjustments by category
        by_category: Dict[str, int] = {}
        by_diagnosis: Dict[str, int] = {}
        for adj in self._adjustments:
            cat  = adj.get("category", "UNKNOWN")
            diag = adj.get("diagnosis", "UNKNOWN")
            by_category[cat]   = by_category.get(cat, 0) + 1
            by_diagnosis[diag] = by_diagnosis.get(diag, 0) + 1

        return {
            "module":             self.MODULE,
            "total_adjustments":  len(self._adjustments),
            "symbols_tracked":    len(self._overrides),
            "suppressed_symbols": suppressed,
            "braked_symbols":     braked,
            "active_overrides":   {s: self.get_overrides(s) for s in active},
            "adjustments_by_category":  by_category,
            "adjustments_by_diagnosis": by_diagnosis,
            "atr_ema_tracked":    len(self._atr_ema),
            "recent_adjustments": self._adjustments[-10:],
            "snapshot_ts":        int(time.time() * 1000),
        }

    # ── Diagnosis ─────────────────────────────────────────────────────────────

    def _diagnose(
        self,
        r_multiple: float,
        gross_pnl:  float,
        fee_total:  float,
    ) -> str:
        # Fee toxic: we won on price but fees wiped it out
        if gross_pnl > 1e-6 and fee_total / max(gross_pnl, 1e-9) > FEE_TOXIC_RATIO:
            return "FEE_TOXIC"
        # Volatility spike: price blew through SL (r_multiple worse than -1.05)
        if r_multiple < -1.05:
            return "VOLATILITY_SLIP"
        # Normal SL
        return "NORMAL_SL"

    # ── Apply Adjustment ──────────────────────────────────────────────────────

    def _apply(
        self,
        symbol:      str,
        strategy_id: str,
        net_pnl:     float,
        r_multiple:  float,
        diagnosis:   str,
        fee_total:   float,
        gross_pnl:   float,
    ) -> Optional[ReactiveAdjustment]:

        state = self._ensure_state(symbol)
        n_adj = state.get("consecutive_adjustments", 0)
        changes: Dict[str, Any] = {}
        note = ""

        # ── Consecutive loss brake (FTD-SNP-001) ─────────────────────────────
        consec_losses = state.get("consecutive_losses", 0)
        if consec_losses >= CONSEC_LOSS_BRAKE_THRESHOLD and state.get("brake_until", 0) <= time.time():
            brake_ts = time.time() + CONSEC_LOSS_BRAKE_MINUTES * 60
            state["brake_until"] = brake_ts
            logger.warning(
                f"[REA-001] CONSEC_BRAKE {symbol}: {consec_losses} consecutive losses "
                f"→ brake active for {CONSEC_LOSS_BRAKE_MINUTES}min "
                f"score_min→{BRAKE_SCORE_MIN_OVERRIDE}"
            )

        if diagnosis == "FEE_TOXIC":
            # Suppress symbol immediately — no point trading until we reassess
            suppress_ts = time.time() + FEE_TOXIC_SUPPRESS_MIN * 60
            state["suppressed_until"] = suppress_ts
            changes["suppressed_until"] = suppress_ts
            fee_ratio = fee_total / max(gross_pnl, 1e-9)
            note = (
                f"Symbol suppressed for {FEE_TOXIC_SUPPRESS_MIN} min. "
                f"Fee ratio {fee_ratio:.1%} exceeds {FEE_TOXIC_RATIO:.0%} threshold. "
                f"Profit-centric: avoiding high-fee, low-gain pattern."
            )
            logger.warning(
                f"[REA-001] FEE_TOXIC {symbol} suppressed {FEE_TOXIC_SUPPRESS_MIN}min "
                f"fee_ratio={fee_ratio:.1%}"
            )

        elif diagnosis == "VOLATILITY_SLIP" and n_adj < MAX_CONSEC_ADJ:
            # Tighten SL (smaller loss if it happens again) + widen TP (better RR)
            old_sl, old_tp = state["atr_sl"], state["atr_tp"]
            state["atr_sl"] = round(max(ATR_SL_MIN, state["atr_sl"] - ATR_SL_STEP), 3)
            state["atr_tp"] = round(min(ATR_TP_MAX, state["atr_tp"] + ATR_TP_STEP), 3)
            changes = {
                "atr_sl": {"from": old_sl, "to": state["atr_sl"]},
                "atr_tp": {"from": old_tp, "to": state["atr_tp"]},
            }
            new_rr = round(state["atr_tp"] / max(state["atr_sl"], 1e-9), 2)
            note = (
                f"Adaptive aggression: SL tightened {old_sl}→{state['atr_sl']} "
                f"TP widened {old_tp}→{state['atr_tp']} "
                f"→ RR ratio now {new_rr}x. "
                f"r_multiple was {r_multiple:.2f} (SL slip/volatility spike)."
            )
            state["consecutive_adjustments"] = n_adj + 1
            logger.info(
                f"[REA-001] VOLATILITY_SLIP {symbol} "
                f"atr_sl {old_sl}→{state['atr_sl']} "
                f"atr_tp {old_tp}→{state['atr_tp']} RR={new_rr}"
            )

        elif diagnosis == "NORMAL_SL" and n_adj < MAX_CONSEC_ADJ:
            # Micro-adjustment: small SL tighten + small TP widen
            old_sl, old_tp = state["atr_sl"], state["atr_tp"]
            state["atr_sl"] = round(max(ATR_SL_MIN, state["atr_sl"] - ATR_SL_STEP_SMALL), 3)
            state["atr_tp"] = round(min(ATR_TP_MAX, state["atr_tp"] + ATR_TP_STEP_SMALL), 3)
            changes = {
                "atr_sl": {"from": old_sl, "to": state["atr_sl"]},
                "atr_tp": {"from": old_tp, "to": state["atr_tp"]},
            }
            new_rr = round(state["atr_tp"] / max(state["atr_sl"], 1e-9), 2)
            note = (
                f"Micro-adjustment: sl {old_sl}→{state['atr_sl']} "
                f"tp {old_tp}→{state['atr_tp']} RR={new_rr}x."
            )
            state["consecutive_adjustments"] = n_adj + 1
            logger.debug(
                f"[REA-001] NORMAL_SL {symbol} micro-adj "
                f"atr_sl {old_sl}→{state['atr_sl']} RR={new_rr}"
            )

        else:
            # MAX_CONSEC_ADJ reached — freeze to avoid thrashing
            if n_adj >= MAX_CONSEC_ADJ:
                logger.debug(
                    f"[REA-001] {symbol} MAX_CONSEC_ADJ={MAX_CONSEC_ADJ} reached — "
                    f"params frozen until next win"
                )
            return None

        state["last_adjusted_ts"] = int(time.time() * 1000)
        category = _CATEGORY.get(diagnosis, "ENTRY_REFINEMENT")

        return ReactiveAdjustment(
            ts=int(time.time() * 1000),
            ts_fmt=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            symbol=symbol,
            strategy_id=strategy_id,
            trade_pnl=round(net_pnl, 4),
            r_multiple=round(r_multiple, 4),
            diagnosis=diagnosis,
            category=category,
            changes=changes,
            note=note,
        )

    # ── Win Decay ─────────────────────────────────────────────────────────────

    def _decay_on_win(self, symbol: str) -> None:
        """After wins, nudge params back 10% toward defaults to avoid permanent restriction."""
        state = self._overrides.get(symbol)
        if not state:
            return

        state["consecutive_losses"] = 0  # reset loss streak on win
        state["consecutive_adjustments"] = max(0, state.get("consecutive_adjustments", 0) - 1)
        wins = state.get("wins_since_adj", 0) + 1
        state["wins_since_adj"] = wins

        if wins >= DECAY_AFTER_WINS:
            changed = []
            old_ob, old_os = state["rsi_ob"], state["rsi_os"]
            old_sl, old_tp = state["atr_sl"], state["atr_tp"]

            state["rsi_ob"] = round(min(RSI_OB_DEFAULT, state["rsi_ob"] + 1.0), 1)
            state["rsi_os"] = round(max(RSI_OS_DEFAULT, state["rsi_os"] - 1.0), 1)
            state["atr_sl"] = round(min(ATR_SL_DEFAULT, state["atr_sl"] + 0.05), 3)
            state["atr_tp"] = round(max(ATR_TP_DEFAULT, state["atr_tp"] - 0.05), 3)
            state["wins_since_adj"] = 0

            if any([
                abs(state["rsi_ob"] - old_ob) > 0.01,
                abs(state["rsi_os"] - old_os) > 0.01,
                abs(state["atr_sl"] - old_sl) > 0.001,
                abs(state["atr_tp"] - old_tp) > 0.001,
            ]):
                logger.debug(
                    f"[REA-001] DECAY {symbol} after {wins} wins — "
                    f"rsi_ob {old_ob}→{state['rsi_ob']} "
                    f"rsi_os {old_os}→{state['rsi_os']} "
                    f"atr_sl {old_sl}→{state['atr_sl']} "
                    f"atr_tp {old_tp}→{state['atr_tp']}"
                )

    # ── ATR EMA Tracker ───────────────────────────────────────────────────────

    def _update_atr_ema(self, symbol: str, atr_pct: float) -> None:
        """Update slow EMA of ATR% for volatility gate."""
        if atr_pct <= 0:
            return
        current = self._atr_ema.get(symbol, 0.0)
        if current <= 0:
            self._atr_ema[symbol] = atr_pct
        else:
            self._atr_ema[symbol] = round(
                ATR_EMA_ALPHA * atr_pct + (1 - ATR_EMA_ALPHA) * current, 6
            )

    # ── Fee Log ───────────────────────────────────────────────────────────────

    def _record_fee(self, symbol: str, gross_pnl: float, fee_total: float) -> None:
        """Track recent (gross_pnl, fee) pairs per symbol for fee throttle check."""
        if symbol not in self._fee_log:
            self._fee_log[symbol] = []
        self._fee_log[symbol].append((gross_pnl, fee_total))
        # Keep only last FEE_THROTTLE_WINDOW * 2 entries (cheap cap)
        if len(self._fee_log[symbol]) > FEE_THROTTLE_WINDOW * 2:
            self._fee_log[symbol] = self._fee_log[symbol][-FEE_THROTTLE_WINDOW:]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _ensure_state(self, symbol: str) -> Dict[str, Any]:
        if symbol not in self._overrides:
            self._overrides[symbol] = {
                "rsi_ob":                  RSI_OB_DEFAULT,
                "rsi_os":                  RSI_OS_DEFAULT,
                "atr_sl":                  ATR_SL_DEFAULT,
                "atr_tp":                  ATR_TP_DEFAULT,
                "consecutive_adjustments": 0,
                "consecutive_losses":      0,
                "wins_since_adj":          0,
                "suppressed_until":        0,
                "brake_until":             0,
                "last_adjusted_ts":        0,
            }
        return self._overrides[symbol]

    def _persist(self) -> None:
        try:
            REACTIVE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            REACTIVE_REPORT_PATH.write_text(
                json.dumps(self.summary(), indent=2, default=str)
            )
        except Exception:
            pass


# ── Module-level singleton ────────────────────────────────────────────────────
reactive_evolution_engine = ReactiveEvolutionEngine()
