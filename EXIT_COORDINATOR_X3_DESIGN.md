# 🏛️ EXIT COORDINATOR — X3 DESIGN (Single Exit Authority)

**Status:** DESIGN ONLY — *no acting code, no live exit change in this deliverable*
**Engine build:** APP_VERSION 1.99.x
**Approved by:** evidence gate (see §1) + board Option-2 audit pass + final-authority sign-off
**Companions:** `EXIT_AUTHORITY_MAP.md` (current writers), `UNIFIED_EXIT_AUTHORITY_BLUEPRINT.md`
(X0–X4 roadmap), `core/exit_coordinator.py` (X1/X2 shadow, already shipped).

---

## 1. EVIDENCE BASIS (why X3 design is now justified)

Historical backtest on real DataLake trades+candles, after five successive
de-biasing passes:

| Pass | Result |
|------|--------|
| Look-ahead removed (next-bar exit) | edge held |
| Denominator artifact removed (R/trade, not %) | 2752% → +0.367R |
| Subset → population (per OBSERVED trade) | +0.367 → **+0.235R/observed** |
| Walk-forward (both time halves) | +0.342 / +0.260 → consistent |
| **Duration/observability stratified** | **broad_based=True**; every major bucket positive (2-5: +0.285, 5-20: +0.329, <2: +0.030), no class >60% |

The signal converged to a small, stable, broad, positive number — the signature
of a real effect. **This justifies DESIGNING the authority, not granting it.**
Everything is retrospective; forward confirmation (§6) is a hard precondition to
X3 *acting*.

---

## 2. WHAT X3 IS

X3 makes the **Exit Coordinator the single AUTHOR** of every live `stop_loss` /
`take_profit` / close decision. `RiskController._close_position` remains the single
EXECUTOR. The ~12 current writers (EXIT_AUTHORITY_MAP §1) become **advisors** that
propose typed intents; the coordinator arbitrates by one explicit policy and emits
one decision + one audit record. This retires hazards H-1…H-5 (two-writer SL
contention, divergent TM copy, unguarded TP widen) by construction.

```
ADVISORS (pure, no writes)              ARBITER (sole author)         EXECUTOR
  RiskRules  (trail/BE/ratchet/speed) ┐
  TradeManager (MOVE_BE/TRAIL/EXTEND) ├─ ExitIntent[] ─► ExitCoordinator ─► RiskController
  XTE (continuation conviction)*      ┘   precedence + invariants        ._close_position
  *only when lifecycle stage >= ADVISE                + 1 audit record
```

---

## 3. INTERFACES (design)

### 3.1 ExitIntent (proposed, not applied)
```
ExitIntent(
  source:   str        # "risk_rules" | "trade_manager" | "xte" | "emergency"
  kind:     str        # "SET_SL" | "SET_TP" | "CLOSE" | "PARTIAL" | "HOLD"
  value:    float      # proposed sl/tp price (or fraction for PARTIAL)
  reason:   str
  priority: int        # from the precedence tier (§4)
  lifecycle_stage: str # advisor's current LearningLifecycle stage (gates XTE)
)
```

### 3.2 Advisor adapters (wrap existing logic — no reimplementation)
- `RiskRulesAdvisor` — emits the trailing/BE/giveback-ratchet/speed-exit intents
  currently computed in `risk_controller.on_price_update` (A2–A5).
- `TradeManagerAdvisor` — wraps `trade_manager.update()` actions (A8–A12).
- `XTEAdvisor` — emits a tighten/scale/hold intent from `exit_truth_engine`, **but
  only contributes when `learning_lifecycle` stage for "XTE" ≥ ADVISE.** Below that
  it returns HOLD (no influence).

### 3.3 ExitCoordinator.resolve(intents) -> ExitDecision
Pure function: takes all intents for a position, applies §4 precedence + §5
invariants, returns one `ExitDecision(sl, tp, close, partial, rationale[])`.

---

## 4. PRECEDENCE POLICY (hard → soft)
1. **Emergency / hard safety** (risk_engine caps, force_close) — non-overridable.
2. **Terminal exits** (speed-exit, VTP/TIME/FAST close) — beat adjustments.
3. **Protective SL moves** (trail/BE/ratchet, TM MOVE_BE/TRAIL) — tighten-only.
4. **TP changes** — widen requires an explicit grant (I-2).
5. **XTE advisory** (post-ADVISE) — may *nudge* within the protective band only;
   never loosens, never overrides tiers 1–2.

---

## 5. INVARIANTS (coordinator enforces; shadow already checks)
- **I-1** live `stop_loss` monotonic protective, except terminal close-pending.
- **I-2** `take_profit` widening needs an explicit logged grant.
- **I-3** one source of truth for SL/TP — no divergent copies (kills H-2).
- **I-4** one audit record per decision `(source, kind, old, new, reason)`.

`core/exit_coordinator.py` (shadow) already validates I-1/I-2 against live
transitions; X3 promotes it from observer to author.

---

## 6. MIGRATION & GATES (each step reversible)

| Step | Scope | Gate | Live impact |
|------|-------|------|-------------|
| X3-a | Build `ExitIntent`, advisor adapters, `resolve()` — **shadow**: log resolved decision vs what live writers did | — | none |
| X3-b | **Parity proof**: shadow `resolve()` matches live SL/TP for ≥ N trades (no divergence) | X3-a | none |
| X3-c | **Forward XTE confirmation** (§7) — live forward slice agrees with backtest +0.235R | forward data | none |
| X3-d | Flip writers to route through coordinator (RiskController sole executor behind it) | X3-b parity + **ADR** | behavior-neutral refactor |
| X3-e | Admit XTE as an *acting* advisor (tier 5) | XTE lifecycle ≥ ADVISE + X3-d + ADR | opt-in, advisory band only |

**Hard rule:** X3-d/X3-e (anything that changes a live exit) require BOTH parity
proof AND a recorded ADR. Backtest evidence alone is insufficient.

---

## 7. FORWARD CONFIRMATION (mandatory before XTE acts)

Backtest is retrospective. Before XTE influences a live exit:
1. Run the forward observation campaign (`start_xte_campaign.bat`).
2. Periodically run `tools/xte_forward_check.py` — compares the forward (live)
   archive against the backtest backfill archive.
3. **Confirm** when forward `+R/observed` ≥ ~0.10 AND forward `broad_based=True`
   AND forward n ≥ 300. If forward materially disagrees with backtest → HALT,
   do not advance (the backtest was regime-specific).

This is the one gate a backtest can never satisfy; it is non-negotiable.

---

## 8. LIFECYCLE PROMOTION (governance, human-gated)

Per `learning_lifecycle`, XTE advances OBSERVE→VALIDATE→APPROVE automatically on
evidence, but entering **ADVISE** (acting) is human-recorded:
```
learning_lifecycle.approve("XTE", "ADVISE", approver="<name>",
                           note="backtest +0.235R broad_based + forward-confirmed")
```
Record this ONLY after §7 forward confirmation — not on backtest alone.

---

## 9. ROLLBACK
Every step ≤ X3-c is shadow/observation (revert = ignore). X3-d routes through one
seam — rollback = stop routing (writers revert to direct). X3-e = flip XTE advisor
off. No step is one-way.

---

## 10. WHAT THIS DELIVERABLE IS / ISN'T
- **IS:** the design for the single exit authority + the gates to reach it.
- **ISN'T:** acting code. Nothing here changes a live trade. Implementation of
  X3-a starts on approval of this design; X3-d/e remain blocked behind parity +
  forward confirmation + ADR.

---

*End of EXIT_COORDINATOR_X3_DESIGN. Design-only; acting authority is gated.*
