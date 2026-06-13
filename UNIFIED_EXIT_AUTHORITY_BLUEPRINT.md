# 🏛️ UNIFIED_EXIT_AUTHORITY_BLUEPRINT — FTD-094A Phase 7

**Status:** Architectural study — *no implementation in this deliverable*
**Engine build:** APP_VERSION 1.92.0
**Companion:** EXIT_AUTHORITY_MAP.md (current-state forensic map)
**Mandate framing:** highest-priority architectural deliverable of FTD-094A; this
is design-only and does not authorize any exit-behavior change.

---

## 1. THE FOUR QUESTIONS (answered)

**Q1 — How many exit authorities exist?**
**Twelve writers across three files**, grouped into **two authoring sources** and
**one executor** (EXIT_AUTHORITY_MAP §1):
- Authoring source #1: `RiskController.on_price_update` (trailing A2, breakeven A3,
  giveback-ratchet A4, speed-exit A5).
- Authoring source #2: `TradeManager.update` → main.py glue (MOVE_BE A8, TRAIL_SL
  A9, EXTEND_TP A10, VTP_EXIT A11, TIME_EXIT/FAST_FAIL A12).
- Executor: `RiskController._close_position` (A1/A5/A6/A7) — the only terminal path.

**Q2 — Which authority wins conflicts?**
For **stop-loss**: "tightest wins" by convention — every SL writer is tighten-only
and the glue guards against the live value (main.py:971–978). For **take-profit**:
`EXTEND_TP` (A10) is the only writer and is **unguarded** (widens once per trade).
There is **no central arbiter**; resolution is emergent from per-writer guards, and
`TradeManager` holds a divergent internal copy (H-2). The de-facto winner of
*execution* is always `RiskController` because it alone owns `_close_position`.

**Q3 — Which authority should be supreme?**
**`RiskController` should be the supreme exit executor** (it already is, de facto),
and a **single Exit Coordinator should be the supreme exit *author*** — the one
place that decides the next `(stop_loss, take_profit, close?)` from all inputs.
`TradeManager`'s exit logic and `RiskController`'s autonomous trailing/BE/ratchet
should become *advisors into* that coordinator rather than independent writers.

**Q4 — Recommended future architecture.**
A thin **Exit Coordinator** seam that (a) collects exit intentions from all
advisors (RiskController rules, TradeManager, and — post-validation — XTE), (b)
resolves them through one explicit precedence policy, and (c) is the **only**
writer of live `stop_loss`/`take_profit` and the only caller of the executor.
This removes H-1…H-4 by construction.

---

## 2. TARGET ARCHITECTURE (advisory → arbiter → executor)

```
                ┌─────────────── EXIT ADVISORS (pure, no writes) ───────────────┐
                │  RiskRules (trailing/BE/ratchet/speed)                          │
                │  TradeManager (MOVE_BE/TRAIL_SL/EXTEND_TP/VTP/TIME/FAST)        │
                │  XTE (continuation conviction)   ← post-validation, advisory    │
                └───────────────────────────────────────────────────────────────┘
                                          │ ExitIntent[] (proposed sl/tp/close + reason + source)
                                          ▼
                          ┌──────────────────────────────────┐
                          │        EXIT COORDINATOR           │  ← SOLE AUTHOR
                          │  precedence policy + invariants:  │
                          │   • SL tighten-only (hard)        │
                          │   • TP widen needs explicit grant │
                          │   • terminal (close) > adjust     │
                          │   • one audit record per decision │
                          └──────────────────────────────────┘
                                          │ single resolved (sl, tp, close?)
                                          ▼
                          ┌──────────────────────────────────┐
                          │  RiskController._close_position    │  ← SOLE EXECUTOR
                          │  + the single live SL/TP writer    │
                          └──────────────────────────────────┘
```

**Invariants the coordinator enforces (today only conventions):**
- I-1: live `stop_loss` is monotonic in the protective direction (kills H-1).
- I-2: `take_profit` widening requires an explicit, logged grant (kills H-3).
- I-3: exactly one source of truth for SL/TP — no divergent copies (kills H-2).
- I-4: every exit decision emits one audit record `(field, old, new, source, reason)`.

---

## 3. MIGRATION ROADMAP (non-breaking, staged)

| Phase | Scope | Behavior change | Gate |
|------|------|-----------------|------|
| **X0 — Observe** | FTD-094A: XTE observation + this map/blueprint | **none** | ✅ shipped (flag-off) |
| **X1 — Audit shim** | read-only audit of every net SL/TP transition with category/provenance | **none** (logging only) | ✅ shipped as `core/exit_coordinator.py` shadow (flag-off). Note: provenance is by *category* via single-seam observation; exact per-writer source tagging remains a later instrumentation step |
| **X2 — Coordinator (shadow)** | `ExitCoordinatorShadow` validates the unified invariants (I-1 tighten-only, I-2 TP-widen-needs-grant) against live transitions and reports parity | **none** (parity assert) | ✅ shipped (flag-off, `EXIT_COORDINATOR_SHADOW_ENABLED`); endpoint `GET /api/exit/coordinator` |
| **X3 — Coordinator (authority)** | Flip the live writers to route through the coordinator; RiskController becomes sole executor behind it | behavior-neutral refactor (parity-proven) | X2 parity stable ≥ N trades |
| **X4 — Advisor admission** | Admit calibrated advisors (e.g. XTE post-Phase-6) into the coordinator's precedence policy | opt-in, per-advisor flag | per-advisor calibration + ADR |

**Sequencing rule:** no advisor (including XTE) may *act* until the coordinator
exists (X3) — otherwise admitting a third writer worsens H-1. XTE *observation*
(X0) is independent and safe today.

---

## 4. RISK ASSESSMENT

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R-1 | Refactor breaks the tighten-only SL behavior | HIGH | X2 shadow parity assert before X3; revert = stop routing |
| R-2 | Coordinator adds latency to the price loop | MED | O(1) resolution over ≤ a handful of intents; reuse computed values |
| R-3 | Hidden caller of `pos.stop_loss=` outside the map | MED | X1 audit shim catches any unmapped writer at runtime |
| R-4 | Over-engineering before evidence | MED | X0/X1 are logging-only; coordinator built only after provenance data justifies it |
| R-5 | XTE admitted before it earns it | HIGH | X4 gated on FTD-094A Phase-6 (≥500 samples + positive expectancy) + ADR |

---

## 5. RELATIONSHIP TO ENTRY AUTHORITY

Entries already have a sole authority — `ExecutionOrchestrator.run_cycle`
(FTD-092 §1.1). This blueprint gives exits the symmetric structure entries already
enjoy: **one author, one executor, one audit trail.** The two need not merge; they
are different lifecycle phases. The institutional pattern ("single authority +
observation→calibrate→advise→gate") is identical.

---

## 6. RECOMMENDATION

1. **Now (this FTD):** ship XTE observation (X0) — done, flag-off.
2. **Next (separate FTD):** X1 audit shim → X2 shadow coordinator. These are the
   genuinely high-impact, low-risk structural steps that retire H-1…H-4.
3. **Later (blocked):** X3 authority flip and X4 advisor admission, each behind
   parity proof / calibration + ADR.

**Do NOT** grant XTE — or any advisor — live exit authority before X3. The current
two-writer arrangement is the real architectural debt; XTE is a beneficiary of
fixing it, not a substitute for fixing it.

---

*End of UNIFIED_EXIT_AUTHORITY_BLUEPRINT. Design-only; implementation requires a
follow-on FTD per the staged roadmap above.*
