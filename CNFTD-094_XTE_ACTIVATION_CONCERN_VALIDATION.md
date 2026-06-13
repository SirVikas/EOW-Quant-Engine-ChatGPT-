# 🧾 CNFTD-094 — XTE ACTIVATION CONCERN VALIDATION

**Ref:** CNFTD-094_XTE_ACTIVATION_CONCERN_VALIDATION
**Title:** Pre-Implementation Validation of XTE Activation Program
**Status:** VALIDATION-ONLY — *no production code, no execution influence, no gate/sizing/risk change*
**Posture:** Independent adversarial auditor. Objective = **disprove** QFTD-093's
assumptions wherever the evidence allows.
**Engine build:** APP_VERSION 1.91.2 → 1.91.3 (documentation-only PATCH; §Versioning)
**Reference docs:** FTD-092 (AMIL), QFTD-093 (Master Review), Ecosystem Audit v1.91.2,
Phase-2 Calibration (CLAUDE.md), Truth Stack findings.

---

## 0. HEADLINE VERDICT (read this first)

QFTD-093's *direction* (exit-side is the data-supported lever) survives scrutiny.
Its *three central factual claims do not.* The audit overstated the gap and
named the wrong integration seam.

| QFTD-093 claim | Validation verdict | Evidence |
|---|---|---|
| "XTE is a hardcoded stub / not even computed" | **PARTLY FALSE** — XTE is a **fully-implemented, dormant** engine; only the AAP *field* is `0.0` | `core/truth/exit_truth_engine.py` (243 lines, 5 sub-engines); `.summary()` wired at main.py:13790 |
| "Exit intelligence does not exist; giveback is the dormant lever" | **FALSE** — active, calibrated exit-quality control already runs in production | `risk_controller.py` trailing/BE/**giveback-ratchet**/speed-exit; `GIVEBACK_RATCHET_ENABLED=True` (config.py:277) |
| "Un-stub XTE at close (main.py:901)" is the smallest/safest move | **WRONG SEAM** — XTE scores *open-position* state; those inputs don't exist at close | XTE docstring + `evaluate()` signature needs live `closes/volumes/current_r` |
| "XTE is the highest-ROI implementation" | **NOT PROVEN** — true ROI is the *marginal* value of a composite score over already-active mechanical rules | §9 ranking |

**Net:** XTE activation is worth pursuing, but **only** as an *observation-mode
advisory wired into the open-position management loop*, scoped to measure whether
a composite score beats the rules the engine already runs. The QFTD-093
implementation recipe ("replace the 0.0 at close") is rejected as both
semantically wrong and technically impossible with the data available there.

---

## SECTION 1 — AUDIT FINDING VALIDATION (Assumption Validation Report)

**1. Is XTE truly inactive?**
**Inactive at runtime, but NOT a stub.** `core/truth/exit_truth_engine.py` is a
complete 243-line engine: five sub-scorers (trend persistence, volatility shift,
liquidity exhaustion, profit protection, risk escalation), weighted composite,
and an `XTEAdvisory` generator (tighten_tsl / trigger_be / scale_out / hold).
The singleton is imported (main.py:150) and its `.summary()` is exposed via an
API endpoint (main.py:13790). **But `exit_truth_engine.evaluate(...)` is never
called anywhere in production** (only in `tests/test_entry_exit_truth_engine.py`).
So the precise truth is: *the engine is built and dormant; only the AAP snapshot
field `exit_truth_score=0.0` (main.py:901) is a literal placeholder.* QFTD-093's
word "stub" is imprecise and overstated.

**2. Is XTE implemented elsewhere under another name?**
The *scoring abstraction* is not duplicated, but the *function* (exit-quality
management) is implemented mechanically in **two** other live systems:
- `core/risk_controller.py`: ATR trailing stop (`TRAIL_ATR_MULT=1.20`), breakeven
  arming (`BREAKEVEN_TRIGGER_R=0.40`, data-calibrated), **peak-proportional
  giveback ratchet** (`GIVEBACK_RATCHET_ENABLED=True`, `MIN_R=0.50`,
  `LOCK_FRACTION=0.50`), and velocity **speed-exit** (`SPEED_EXIT_TRIGGER_R=2.0`).
- `trade_manager.update()` (consumed at main.py:956): emits `MOVE_BE`, `TRAIL_SL`,
  `EXTEND_TP`, `VTP_EXIT` actions.

**3. Is any exit-quality intelligence already present?** **YES, substantial.** The
giveback/BE-scratch lever QFTD-093 called dormant is already addressed
mechanically and the parameters were calibrated from real trade data (the
comments at config.py:260 cite "avg winning trade = 0.09R").

**4. Is any exit-scoring mechanism already operating?** **No *score*, but yes a
*rule cascade*.** The distinction matters: production decides exits via
thresholded R-multiples and ATR ratios, not via a 0–100 composite. XTE's only
novel contribution would be the *composite-score framing* and its multi-factor
advisory — whose marginal value over the existing rules is unproven.

**5. Hidden dependencies not surfaced by the audit?** **YES, two:**
- (a) `CORTEX module_registry` formally registers XTE (`core/cortex/module_registry.py:390`)
  — so the governance/introspection layer already "knows about" XTE as a tracked
  module (documentation dependency, not runtime).
- (b) A **consumer config already exists**: `XTE_ADVISORY_TSL_SCORE=35.0`
  (config.py:788) — a threshold built to act on XTE's advisory, currently dead
  because `evaluate()` is never called. Activation must reconcile with it.
- (c) **Coordination hazard**: risk_controller and trade_manager *both* arm
  BE/trail the same position; the code already carries an `FTD-SL-GUARD` warning
  (main.py:959–964) that one can drag the other's SL backward. **XTE would be a
  THIRD exit voice entering an already-delicate two-writer arrangement.**

> **Deliverable (Assumption Validation):** XTE is *dormant, fully-built*, not a
> stub. Exit intelligence already exists and is calibrated. The audit's framing
> ("missing lever") is rejected; the accurate framing is "an unused alternative
> *scoring* of an already-managed function."

---

## SECTION 2 — DATA SUFFICIENCY REVIEW

`evaluate()` requires **open-position, per-tick** inputs: `closes[]`, `volumes[]`,
`atr_pct`, `atr_ema`, `current_r`, `peak_r`, `side`.

| Field | Available now? | Where |
|---|---|---|
| peak_r | ✅ live + persisted | risk_controller pos.peak_r; TradeRecord.peak_r (v1.38.6+) |
| current_r | ✅ derivable live | (price−entry)/entry_risk during management |
| atr_pct | ✅ live | regime_det.state(sym).atr_pct (main.py:954) |
| atr_ema | ⚠️ partial | `reactive_evolution_engine._atr_ema` exists (used by ETE), must be threaded into the exit seam |
| closes[] / volumes[] | ⚠️ exist but not in exit seam | rolling buffers live in the entry path; not currently passed to `trade_manager.update`/`risk_controller.update` |
| exit_r / realized_pnl / duration / regime / cost / slippage | ✅ at close | TradeRecord (risk_controller.py:470–483, 502) |
| attribution outputs | ✅ | exit_attribution.py (exit_method/exit_reason), AAP snapshot |

**1. Sufficient?** For an **open-position advisory** (XTE's actual design): *almost*
— peak_r/current_r/atr_pct are live; the gap is **plumbing `closes[]`, `volumes[]`,
`atr_ema` into the management tick**, not missing data. For "compute at close"
(QFTD-093): **insufficient and ill-posed** — the time-series inputs describe a
live position and are meaningless post-close.
**2. Missing:** the rolling candle/volume buffers at the management seam.
**3. Materially improving telemetry:** `ticks_since_peak` (already tracked for
speed-exit), realized giveback ratio (peak_r − exit_r), and per-tick MFE/MAE —
cheap, mostly already captured.
**4. Can XTE be computed accurately today?** Only after a *read-only plumbing*
change to pass the candle buffers to the exit seam. As-is, it cannot run with
correct inputs.

> **Deliverable (Data Sufficiency):** Data is sufficient **for an open-position
> advisory** after a small read-only wiring of existing buffers. It is **not**
> sufficient or meaningful "at close." Reject the close-time computation.

---

## SECTION 3 — XTE DEFINITION CHALLENGE (Formal Specification)

The code already commits to a definition: **"High score = hold/let run; low score
= tighten/scale-out."** That is interpretation **(D) Risk-adjusted Exit Quality /
(E) Composite Exit Intelligence** — a *position-continuation conviction* score,
NOT a profit-capture grade.

- **What XTE SHOULD represent:** the probability-weighted attractiveness of
  *continuing to hold* an open position vs protecting gains — a forward-looking
  hold/tighten/scale advisory over the live position state.
- **What XTE must NOT represent:** (a) a *post-hoc* "did we exit well?" grade
  (that is AAP/attribution's job, §5); (b) an *entry* alpha signal (Phase-2
  proved no entry-component expectancy); (c) a *force-close authority* (Phase-1
  is advisory; `XTE_FORCE_CLOSE_ENABLED=False`).
- **Highest future value:** (D) — risk-adjusted continuation quality — because it
  composes the one lever the data supports (giveback/exit timing) into a single
  inspectable signal that can be *compared against* the existing mechanical rules
  before ever being trusted.

> **Deliverable (Specification):** XTE = a 0–100 *open-position continuation
> conviction* score with a tighten/BE/scale/hold advisory; observation-only;
> compared against, not layered blindly on, the existing ratchet/BE/speed rules.

---

## SECTION 4 — OBSERVATION MODE SAFETY REVIEW (Safety Assessment)

**1. Activatable without affecting execution?** **Yes** — if and only if it runs
*after* the existing exit-management writes and only *logs* its advisory, never
mutating `pos.stop_loss`/`take_profit`. The `force_close=False` invariant is
hard-coded in the engine (exit_truth_engine.py:206).
**2. Fully isolated?** Achievable, but **not automatic**: the existing two-writer
SL coordination (FTD-SL-GUARD) means any future *acting* XTE is high-risk.
Observation isolation is safe; acting isolation is not.
**3. Hidden side-effects?** Two to guard: (a) `XTE_ADVISORY_TSL_SCORE=35.0`
already exists — ensure no dormant consumer reads it once XTE produces output;
(b) `summary()` mutates `_last_result` state — fine single-threaded, but the
exit seam runs in the asyncio loop, so keep it synchronous and cheap.
**4. Performance degradation?** Negligible: `evaluate()` is O(n) over short
buffers (~µs), but it runs **per managed position per tick**, not once per trade —
higher call frequency than ETE. Still < 1 ms/tick; must reuse existing buffers,
not recompute ATR.
**5. Storage impact?** If every per-tick score is archived, volume could be large
(N positions × ticks). **Mitigation:** archive only on advisory *transitions* or
at close (one XTE summary per trade), not every tick.

> **Deliverable (Safety):** Observation mode is safe under three constraints:
> (i) runs after existing exit writes and never mutates SL/TP; (ii) bounded
> storage (transition/close snapshots only); (iii) leaves `XTE_ADVISORY_TSL_SCORE`
> with no live consumer. Any *acting* mode is NOT safe until the two-writer exit
> coordination is unified (§8).

---

## SECTION 5 — TRUTH STACK RELATIONSHIP REVIEW (Integration Report)

The Truth Stack today: **ETE** (entry, computed-then-discarded), **XTE** (exit,
dormant), **AAP / alpha_attribution** (post-close attribution), **exit_attribution**
(canonical exit-method tagging), **performance_attribution**.

**1. Where does XTE belong?** Squarely inside the Truth Stack, as the exit-time
counterpart to ETE — but operationally it belongs in the **open-position
management loop**, not the close handler.
**2. Part of Truth Stack?** Yes — it shares the `core/truth/` package and the
`force_close=False` advisory doctrine.
**3. Independent?** Functionally independent of ETE (different inputs, different
lifecycle phase) but governed by the same observation→calibrate→advise→gate
ladder.
**4. Does XTE duplicate existing functionality?** **Partial overlap, not
duplication:** `exit_attribution` answers *"how did we exit?"* (descriptive,
post-hoc); XTE answers *"should we still be holding?"* (predictive, live). AAP
answers *"what did the exit contribute?"* (attribution). They are complementary
lenses — but the risk_controller/trade_manager mechanical rules **do** overlap
XTE's *action* surface (tighten/BE/scale).
**5. Can existing Truth assets already provide equivalent intelligence?** **No for
the live continuation signal** (nothing else scores an open position predictively);
**Yes for the retrospective exit grade** (exit_attribution + AAP + diagnose.py §3
giveback already cover "did we exit well?"). This is the key scoping line: build
XTE only for the *predictive live* role; do **not** rebuild the retrospective role.

> **Deliverable (Truth Stack Mapping):** XTE = live predictive exit-continuation
> member of the Truth Stack; retrospective exit-quality is already owned by
> attribution + diagnostics and must not be duplicated.

---

## SECTION 6 — PHOENIX RELATIONSHIP REVIEW (Compatibility Report)

**1. Archived?** Yes — XTE summaries should join the existing Truth/AAP forensic
archive (one record per trade, not per tick).
**2. Reportable?** Yes — surface via the existing `GET /api/truth/*` family,
consistent with ETE/AAP, and via `exit_truth_engine.summary()` already wired at
main.py:13790.
**3. Future institutional reports?** Yes — XTE observation deltas (score vs actual
giveback/outcome) are exactly the calibration evidence a future FTD needs;
record milestones to IMRAF.
**4. Reporting architecture implications:** minimal — reuse Truth archive +
existing endpoint; the only new artifact is a per-trade XTE summary field. No new
report bundle, no new schema beyond an additive field. Per CLAUDE.md single-
source versioning, any such change is ≥ PATCH.

> **Deliverable (PHOENIX Mapping):** XTE is reportable/archivable through existing
> Truth/AAP infrastructure with one additive per-trade field. No new reporting
> subsystem required.

---

## SECTION 7 — CORTEX / NEXUS / OBSX REVIEW (Architectural Relationship Report)

**1. Is "decision-mute" fully correct?** **Yes for execution influence** — none of
the three reads into the trade-decision or exit path (verified: zero refs in
on_tick except DOAE's 100-trade recording). **But QFTD-093 understated one
indirect link:** `CORTEX module_registry` *catalogs* XTE
(core/cortex/module_registry.py:390) — CORTEX has documentary awareness of XTE,
which means activation should update CORTEX's registry/constitution records.
**2. Indirect influences missed?** Only the registry/governance cataloging above;
no runtime decision influence missed.
**3. Could XTE activation benefit these systems?** Marginally — XTE observation
data enriches NEXUS/IMRAF institutional memory and gives CORTEX a live truth
signal to reason about. Benefit is to *knowledge*, not *trades*.
**4. Does XTE belong under one of them?** **No.** XTE belongs in the Execution
Layer's Truth Stack (`core/truth/`), not NEXUS/CORTEX/OBSX. Those are
introspection/memory/observability; XTE is a live market-state scorer.

> **Deliverable (CORTEX/NEXUS/OBSX):** Conclusion "decision-mute" holds; add the
> caveat that CORTEX registry catalogs XTE and must be updated on activation. XTE
> stays in the Truth Stack, not the intelligence periphery.

---

## SECTION 8 — CONTROL LAYER REVIEW (Control Layer Assessment)

**1. Does a supreme control layer exist?** **Partially.** For **entries**, yes —
`ExecutionOrchestrator.run_cycle` is the documented sole trade-approval authority
(FTD-092 §1.1). For **exits**, **NO single authority exists**: exit decisions are
split across `risk_controller` (trailing/BE/ratchet/speed) and `trade_manager`
(MOVE_BE/TRAIL_SL/EXTEND_TP/VTP_EXIT), which both write the same `pos.stop_loss`
with a documented anti-collision guard (FTD-SL-GUARD, main.py:959–964).
**2. Where?** Entry authority: `core/orchestrator/execution_orchestrator.py`.
Exit authority: **fragmented** across risk_controller + trade_manager + main.py
glue.
**3. Should one exist?** **Yes — and this is the real architectural finding of
this validation.** The genuine gap is not "no XTE score"; it is **no unified
exit-control authority.** Two writers already contend; XTE would make three.
**4. Who governs Truth / Risk / Capital / RL / Execution / Future Intelligence?**
Today: Risk → risk_engine + risk_controller; Capital → capital_allocator/scaler/
concentrator; RL → rl_engine; Execution(entry) → orchestrator; Truth →
reporting-only (no governor); Future Intelligence → none. **There is no single
arbiter that composes these at exit time.**

> **Deliverable (Control Layer):** Entry has a sole authority; exit does not. The
> correct home for XTE's *advisory* is to **feed a (future) unified exit
> coordinator**, not to act as an independent third writer. Activating XTE as an
> autonomous exit voice without first consolidating exit control would worsen the
> existing two-writer hazard. **This reframes the priority: a thin exit-control
> seam may precede XTE *acting* (though not XTE *observing*).**

---

## SECTION 9 — ROI VALIDATION (ROI Ranking Matrix)

Challenge: is XTE truly highest-ROI? Scored 1 (low) – 5 (high). "Time to evidence"
= how fast a positive/negative verdict can be reached.

| Initiative | Impact | Risk (lower=better) | Complexity (lower=better) | Dev cost (lower=better) | Time-to-evidence | Net |
|---|---|---|---|---|---|---|
| **XTE observation (corrected: live seam)** | 3 | 4 (low risk) | 3 | 3 | 4 (≥500 managed pos, fast) | **HIGH** |
| Truth Feedback Loop (ETE→decision) | 2 | 2 | 2 | 2 | 3 | LOW — Phase-2 says entry edge absent |
| MarketState consolidation (FTD-092) | 2 | 3 | 2 | 2 | 2 | MED — legibility, not edge |
| Allocation intelligence | 2 | 2 | 2 | 2 | 2 | LOW |
| Unified exit-control seam | 4 | 3 | 2 | 2 | 3 | **HIGH** — fixes real two-writer gap |
| NEXUS/CORTEX/OBSX upgrades | 1 | 4 | varies | high | 1 | LOW (no trade ROI) |
| Reporting intelligence | 1 | 5 | 2 | 2 | 4 | LOW (no trade ROI) |

**Finding:** XTE *observation* is high-ROI **for evidence generation** (cheap, low
risk, fast verdict) — but its *trade-impact* ROI is unproven and gated on beating
the already-active ratchet/BE/speed rules. The **unified exit-control seam** ranks
*equal or higher* on impact because it addresses a concrete existing hazard.
QFTD-093's "highest-ROI" is defensible **only** in the narrow sense of "cheapest
path to exit-side evidence," not "biggest guaranteed trade improvement."

> **Deliverable (ROI Matrix):** XTE-observation and exit-control-consolidation are
> the two top initiatives. XTE wins on *time-to-evidence*; exit-control wins on
> *structural impact*. They are complementary and should be sequenced
> exit-control-aware.

---

## SECTION 10 — IMPLEMENTATION AUTHORIZATION TEST

**Q1 — Should XTE activation proceed?**
**Conditional GO** — for *observation mode only*, with the seam corrected.

**Q2 — If yes, why?**
The engine exists, is low-cost to run, and is the cheapest, fastest way to
generate the exit-side calibration evidence the institution has repeatedly said
it needs (CLAUDE.md Phase-4). Observation cannot affect a trade.

**Q3 — If no, why (the caveats that must bound the GO)?**
Because the audit's premise is partly wrong: exit intelligence already exists and
is calibrated, so XTE must prove *marginal* value, not fill a void; and because
acting on XTE before unifying exit control would worsen a documented two-writer
SL hazard.

**Q4 — Prerequisite work remaining:**
1. Plumb existing rolling `closes[]`/`volumes[]`/`atr_ema` into the open-position
   management seam (read-only).
2. Reconcile XTE advisory semantics with risk_controller (ratchet/BE/speed) and
   trade_manager (MOVE_BE/TRAIL_SL) so the observation log records *XTE-said* vs
   *engine-did*.
3. Decide storage cadence (per-transition / per-close, NOT per-tick).
4. Confirm `XTE_ADVISORY_TSL_SCORE=35.0` stays consumer-less in observation.

**Q5 — Approved implementation scope (FTD-094):**
- Call `exit_truth_engine.evaluate(...)` in the open-position management tick
  (near main.py:956 / risk_controller.update), behind a **new flag
  `XTE_OBSERVE_ENABLED` (default False)**.
- Log score + advisory + the action the existing engine actually took.
- Archive one XTE summary per trade (reuse Truth/AAP archive); surface via
  existing `/api/truth/*` and the already-wired `summary()` (main.py:13790).
- Collect ≥500 managed-position samples → expectancy/giveback comparison vs
  current rules. **Zero execution influence.**

**Q6 — Prohibited scope:**
- ❌ Computing XTE "at close" / replacing main.py:901 `0.0` (wrong seam, ill-posed).
- ❌ Any `pos.stop_loss`/`take_profit` mutation from XTE.
- ❌ Any force-close; `XTE_FORCE_CLOSE_ENABLED` stays False.
- ❌ Wiring `XTE_ADVISORY_TSL_SCORE` to a live consumer.
- ❌ Adding XTE as a third autonomous exit writer (requires exit-control
  unification first — separate, later FTD).
- ❌ Any entry-side use of XTE.
- ❌ Touching gates, sizing, risk caps, or RL.

---

## REQUIRED DELIVERABLES — INDEX

1. **Assumption Validation Report** → §1 (XTE dormant-not-stub; exit intel already live)
2. **XTE Specification** → §3 (live continuation-conviction score, observation-only)
3. **Data Sufficiency Analysis** → §2 (sufficient for live seam after buffer plumbing; not at close)
4. **Truth Stack Mapping** → §5 (predictive-live member; no retrospective duplication)
5. **PHOENIX Mapping** → §6 (reportable via existing Truth/AAP; one additive field)
6. **CORTEX/NEXUS/OBSX Review** → §7 (decision-mute holds; CORTEX registry caveat)
7. **Control Layer Assessment** → §8 (entry authority exists; exit authority fragmented — the real gap)
8. **ROI Ranking Matrix** → §9 (XTE-observation + exit-control consolidation top the list)
9. **Go / No-Go Decision** → §10 (Conditional GO, observation-only, corrected seam)
10. **Recommended FTD-094 Scope** → §10 Q5/Q6

---

## VERSIONING & INSTITUTIONAL RECORD

- **APP_VERSION:** validation document only → **PATCH 1.91.2 → 1.91.3** (CLAUDE.md:
  forensic-traceable artifact warrants ≥ PATCH; no `main.py`/`core/`/`strategies/`
  behavior change in this deliverable).
- **IMRAF:** record CNFTD-094 under `decisions` with the corrected verdict —
  *"XTE is dormant, not a stub; exit intelligence already runs (giveback ratchet/
  BE/speed-exit); approved scope = observation-only XTE in the open-position seam;
  the real structural gap is the absence of a unified exit-control authority."*

---

## MANDATORY RESTRICTIONS — COMPLIANCE

This deliverable implements no XTE, modifies no production logic, creates no
execution influence, and alters no gate, sizing, or risk control. Validation-only.
Confirmed.

*End of CNFTD-094. Implementation begins only after approval of the corrected,
observation-only FTD-094 scope defined in §10.*
