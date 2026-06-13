# 🧾 GAPS RESOLUTION — Response to Gaps_List 2026-06-13

**Status:** Gap triage + safe closure. Engine build **1.92.0 → 1.93.0**.
**Directive received:** "remove all gaps." **Honest response:** the 12 gaps fall
into three classes; ~half **cannot** and **must not** be closed in this session
without either (a) live data we cannot generate here, or (b) violating the
institutional safety mandate that CNFTD-094 and FTD-094A just established. The
PRIME DIRECTIVE (CLAUDE.md) requires me to flag this rather than comply blindly.

This document closes every gap that is **safe and possible now** and states
precisely why each remaining gap is **deferred or blocked**, with the path to
close it.

---

## 0. TRIAGE TABLE

| Gap | Class | Action this session |
|----|-------|---------------------|
| GAP-1 Dataset = 0 | **Data-blocked** | Cannot generate ≥500 live trades in an authoring session. Runbook + collection mechanism delivered (§GAP-2). |
| GAP-2 Observe default OFF | **Closeable (docs)** | ✅ Operator runbook + acceptance criteria below. (Default stays False — mandated.) |
| GAP-3 Exit authority not solved | **Safety-blocked** | Mapped (done). Solving = live SL/TP rewire → prohibited until coordinator (blueprint X1→X3). |
| GAP-4 Unified authority not built | **Safety-blocked** | Blueprint done; implementation is a separate, parity-gated FTD. |
| GAP-5 XTE decision-mute | **Intentional / blocked** | Required by mandate; XTE may not act pre-validation. |
| GAP-6 No calibration threshold | **Closeable (tooling)** | ✅ `calibration_curve()` — produces the curve from the archive. |
| GAP-7 No economic validation | **Closeable (tooling, bounded)** | ✅ `counterfactual_analysis()` bounded $/R estimate. |
| GAP-8 No counterfactual engine | **Closeable (tooling, bounded)** | ✅ advisory-vs-giveback counterfactual (summary-level). |
| GAP-9 AMIL still waiting | **Blocked (program)** | Knowledge→Decision requires validated signals; not yet earned. |
| GAP-10 Truth feedback loop missing | **Blocked** | Same doctrine — wiring Truth into decisions needs calibration first. |
| GAP-11 NEXUS/CORTEX/OBSX unanswered | **Closeable (docs)** | ✅ Strategic disposition below. |
| GAP-12 Control layer / "final boss" | **Closeable (answer) + blocked (impl)** | ✅ Answer below; implementation = the coordinator (blocked). |

**Closed now: GAP-2, 6, 7, 8, 11, 12-answer.**
**Blocked/deferred with stated path: GAP-1, 3, 4, 5, 9, 10, 12-impl.**

---

## 1. WHAT WAS BUILT THIS SESSION (safe, zero execution influence)

`core/truth/xte_validation.py` + `GET /api/truth/xte/validation` +
`tests/verify_xte_validation.py` (15/15 pass). All read-only over the observation
archive.

- **`calibration_curve()` [GAP-6]** — score-bucket → win-rate, avg exit_r, avg
  giveback, **expectancy ($)**. This *is* the calibration curve that answers
  "is score 80 good, 20 bad?" — empirically, once data exists.
- **`counterfactual_analysis()` [GAP-7/8]** — advisory-vs-realized-giveback
  alignment (protect precision/recall) + a **bounded upper-estimate of dollars**
  a protective exit could have saved, using empirical $/R from the trades.
- **`verdict()` [P2]** — gates on `MIN_SAMPLES=500`; returns INSUFFICIENT_DATA /
  CANDIDATE / REJECT with a recommendation.

**Honest limitation (stated in code):** the archive holds per-trade *summaries*,
not tick paths, so the counterfactual is summary-level and the $ figure is an
*upper bound* under disclosed assumptions. A path-accurate counterfactual needs
tick-level archival — a future enhancement, not claimed as done.

---

## GAP-2 — OPERATOR RUNBOOK (XTE observation enablement)

**When to enable:** during a dedicated XTE calibration phase, analogous to the
`BYPASS_ALL_GATES` learning-phase pattern — when collecting evidence matters more
than nothing-changes caution. It is safe to enable at any time (observe-only).

**How to enable:**
1. Set env `XTE_OBSERVE_ENABLED=True` (or config) and restart the engine.
2. Optionally set `XTE_OBSERVE_ARCHIVE` (default
   `reports/xte_observations/xte_observations.jsonl`).
3. Confirm via `GET /api/truth/xte/observation → status.observe_enabled == true`.

**Monitoring:** poll `GET /api/truth/xte/observation`
(`status.calibration_progress_pct`) and `GET /api/truth/xte/validation`.

**Acceptance criteria to advance past observation:**
- ≥ **500** closed managed positions archived, AND
- `verdict().status == "CANDIDATE"` (protect precision ≥ 50% AND bounded savings
  > 0), AND
- the Exit Coordinator shadow (blueprint X2) shows parity — **before** any acting
  role (X4). Win-rate alone is NOT sufficient; expectancy is the bar (per
  CLAUDE.md Phase-2 doctrine).

**Rollback:** `XTE_OBSERVE_ENABLED=False` → instant no-op. No live state depends
on it.

---

## GAP-11 — NEXUS / CORTEX / OBSX STRATEGIC DISPOSITION

The audit found these decision-mute. The strategic answer (retire / merge /
activate):

| System | Role today | Disposition | Rationale |
|--------|-----------|-------------|-----------|
| **NEXUS** (IMRAF/DIAL/AEOS/EMA/EGI + KGE/HKE/AEG) | institutional memory/knowledge, background daemon | **KEEP — institutional memory; do NOT wire to decisions** | Its value is forensic/governance, not trade ROI (QFTD-093). Continue Chain-A roadmap on its own track. |
| **CORTEX** (registry/dependency/conflict/blame/constitution/counterfactual) | code-governance introspection | **KEEP as developer/governance tooling; do NOT activate in trade path** | Reasons about the *codebase*, not the market. Should update its registry when XTE activates (already catalogs XTE). |
| **OBSX** | observability/health namespace + API | **KEEP as observability; no decision role** | Health/reporting only; no trade-ROI hook intended. |

**Net:** none should be *activated* into the decision path or *retired*. They are
correctly-scoped support layers. The only cross-link: CORTEX's module registry
should reflect XTE's lifecycle changes. No merge warranted.

---

## GAP-12 — CONTROL LAYER / "FINAL BOSS" ANSWER

> "Risk says Exit, XTE says Hold, Trade Manager says Trail, Ratchet says
> Tighten — who is the final boss?"

**Answer today (factual):** the **final boss of *execution* is
`RiskController._close_position`** — it is the sole component that actually closes
a position. The **final boss of *authoring* does not exist**: SL/TP are authored
by two independent sources (RiskController's own rules + TradeManager via main.py
glue), reconciled only by ad-hoc tighten-only guards. XTE is *not* in this
contest — it has no authority (observe-only).

**Answer going forward (designed):** the **Exit Coordinator**
(`UNIFIED_EXIT_AUTHORITY_BLUEPRINT.md`) becomes the single author; RiskController
remains the single executor; advisors (RiskRules, TradeManager, and — only after
validation — XTE) propose, the coordinator arbitrates with explicit precedence
(terminal > tighten; widen needs a grant), one audit record per decision.

**Why not build it now:** it rewires live SL/TP control — explicitly prohibited by
FTD-094A's restrictions and gated behind parity proof (X2). It is the
highest-value *next* structural FTD, not a same-session change.

---

## 2. WHY THE BLOCKED GAPS ARE NOT "REMOVED" (and the path to remove them)

| Gap | Why blocked | Path to close |
|----|-------------|---------------|
| GAP-1 | No live market data / engine run here; 500 trades take real runtime | Operator enables observation (GAP-2 runbook); accrues live |
| GAP-3/4/12-impl | Would rewire live exit SL/TP authority — prohibited by FTD-094A; risk of the H-1…H-5 hazards worsening | Blueprint X1 (audit shim) → X2 (shadow parity) → X3 (authority) — a dedicated FTD |
| GAP-5/9/10 | Giving XTE/Truth decision influence before calibration violates the proven observe→calibrate→advise→gate ladder (CLAUDE.md Phase-2) | After GAP-1 data + CANDIDATE verdict + coordinator (X3) |
| GAP-7/8 (exact $) | True path-accurate counterfactual needs tick-level archival not currently stored | Add tick-path archival (future) — bounded estimate delivered now |

**This is not foot-dragging.** Each blocked item is blocked by an *explicit
institutional safety rule* this very work-stream authored. Removing them by force
now would contradict CNFTD-094's verdict and risk the live engine — exactly what
the PRIME DIRECTIVE forbids.

---

## 3. REVISED PRIORITY LADDER (aligned to the gaps list)

| Pri | Step | Status | Blocked by |
|----|------|--------|-----------|
| **P1** | Enable observation, collect ≥500 | ⏳ operator action | runbook ready (GAP-2) |
| **P2** | XTE validation report | ✅ tooling shipped | data (auto-fills) |
| **P3** | Counterfactual (summary-level) | ✅ shipped; path-accurate later | tick archival |
| **P4** | Unified Exit Authority (X1→X3) | 📐 blueprint ready | dedicated FTD + parity |
| **P5** | Truth feedback loop | ⛔ blocked | P1–P4 + ADR |
| **P6** | AMIL Phase-1 | ⛔ blocked | P5 |

---

## 4. ONE-LINE STATUS

Foundation (engine + observer) was complete; this session added the **validation
+ calibration + counterfactual analysis layer** (P2/P3) and the **operator/
governance answers** (GAP-2/11/12). The remaining gaps are **gated by live data
and by the safety doctrine** — they require an operator collection run and a
dedicated, parity-proven Exit-Coordinator FTD, not a same-session force-removal.

---

## DECISION REQUIRED FROM APPROVER

Two items need your explicit call (they override safety defaults — I will not do
them unprompted):

1. **Enable `XTE_OBSERVE_ENABLED=True`** for a calibration phase? (Safe, observe-only.)
2. **Authorize a separate FTD to build the Exit Coordinator** (X1→X3, rewires live
   exit authoring behind parity proof)? This is the only path to "solve" GAP-3/4/12.

*End of GAPS_RESOLUTION_FTD-094A.*
