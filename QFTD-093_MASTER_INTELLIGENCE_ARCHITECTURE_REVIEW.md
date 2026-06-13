# 🧾 qFTD-093 — MASTER INTELLIGENCE ARCHITECTURE REVIEW

**Ref:** QFTD-093_MASTER_INTELLIGENCE_ARCHITECTURE_REVIEW
**Status:** ECOSYSTEM AUDIT — *review/audit deliverable, no production code*
**Builds on:** FTD-092 (AMIL Blueprint) finding F-2 (Truth Stack is reporting-only)
**Engine build:** APP_VERSION 1.91.1 → 1.91.2 (documentation-only PATCH; see §9)
**Mandate (verbatim):** this is *not* a vision document and *not* a defense of
AMIL. The single required output is the **smallest, safest, highest-ROI path
that uses intelligence already present in the codebase.**

---

## 0. EXECUTIVE SUMMARY — THE ONE FINDING THAT MATTERS

A full ecosystem sweep (main.py = 21,307 lines; 130 `core/` packages; 945
`core/` files; 1,209 `.py` files total) confirms and sharpens FTD-092's thesis
into a single, decision-relevant statement:

> **The engine is a small, healthy, decision-influencing core wrapped in a vast
> reporting / governance / knowledge periphery. The richest predictive asset —
> the Truth Stack — is entirely open-loop. And its highest-value half, the
> *exit-side* Truth Engine (XTE), is not merely un-acted-upon: it is not even
> computed. It is hardcoded to `0.0`.**

Two numbers frame the whole audit:

- **~21 sequential gates + ~6 sizing multipliers** touch a live trade decision
  (FTD-092 §1.2, §1.5). This is the entire decision-influencing surface.
- **The other ~940 `core/` files** are introspection, memory, governance,
  observability, and reporting. CORTEX, NEXUS (KGE/HKE/AEG), OBSX, IMRAF, DIAL,
  AEOS, EMA, EGI — **none of them touch a trade decision.** Verified: zero
  references in the `on_tick` decision region (main.py ~571–2850) except a
  single 100-trade *recording* snapshot (DOAE, §3.4).

The institutional record (CLAUDE.md Phase-2, 530–535 samples) already proved the
**entry**-component signal is dead — no threshold or reweighting yields positive
expectancy. So the only data-supported lever is the **exit side**. And the exit
side is exactly the asset that is currently a stub.

**The highest-ROI path is therefore not to build a new layer, expand the
knowledge graph (KGE/HKE/AEG), or add governance. It is to start *computing* the
exit-side truth signal that the architecture already declares, in observation
mode, so its calibration data can accrue.** That is one `evaluate()` call per
trade close, behind the existing flag doctrine, with zero decision influence —
the smallest possible change that unlocks the only edge lever the data endorses.

---

## 1. ECOSYSTEM MAP — WHAT IS ACTUALLY WIRED TO A DECISION

The PHOENIX ecosystem (per CLAUDE.md) splits into an Execution Layer and the
PHOENIX NEXUS Institutional Intelligence Layer. The audit question is brutally
simple: *for each subsystem, does it change a trade?*

| Subsystem | Role | Touches a live trade decision? | Evidence |
|---|---|---|---|
| **Gate stack (0–21)** | entry filtering | **YES** — hard gates | main.py `on_tick` §FTD-092 1.2 |
| **Sizing cascade** | position size | **YES** — multipliers | FTD-092 §1.5 |
| **RL engine** | block toxic ctx + conf boost | **YES** | main.py:2053, 1623 |
| **Learning engine** | regime weight | **YES** | main.py:1620 |
| **Orchestrator** | rank→compete→size | **YES** — sole authority | execution_orchestrator.run_cycle |
| **ETE (Entry Truth)** | 6-component entry score | **NO** — computed every entry, logged, discarded | main.py:2626–2651, `gate_enabled=ETE_GATE_ENABLED=False` |
| **XTE (Exit Truth)** | exit-quality score | **NO** — **not even computed** (`=0.0`) | main.py:901 stub; main.py:150 import only |
| **AAP (Attribution)** | post-close snapshot | **NO** — reporting | main.py:894 |
| **regime_memory** | regime fit learning | **NO** — recorded, never read at decision | record main.py:770; read only in API `.summary()` 4882/10994 |
| **NEXUS** (KGE/HKE/AEG/DOAE/IMRAF/EMA) | institutional memory/knowledge | **NO** — background daemon + 100-trade recording | thread main.py:3923; DOAE main.py:745–759 |
| **CORTEX** (registry/dependency/conflict/blame/constitution/counterfactual) | code-governance introspection | **NO** — startup + `/api/cortex/*` | import main.py:159; built main.py:3928–3946 |
| **OBSX** | observability health | **NO** — version namespace + `/api` | config strings; endpoints main.py:15553/15582 |
| **Guardian / DIAL / AEOS / EGI** | governance / dev-intelligence | **NO** — advisory/reporting | guardian watch task main.py:3345 |

**Finding M-1.** The decision-influencing surface is ~21 gates + ~6 multipliers.
**Everything in the NEXUS layer and the entire Truth Stack is decision-mute.**
The periphery is not broken — it is *correctly* isolated from execution — but it
is also where ~99% of the file count and ongoing roadmap effort (KGE→HKE→AEG)
is being spent, for **zero marginal decision ROI**.

---

## 2. THE OPEN-LOOP INTELLIGENCE INVENTORY (DORMANT ASSETS, RANKED)

These are signals already produced (or declared) by the live code that *could*
influence a decision but currently do not. Ranked by data-supported ROI:

| Rank | Dormant asset | Current state | Cost to activate (observation) | Data-supported edge? |
|---|---|---|---|---|
| **1** | **XTE exit-truth score** | **stub `0.0`** — not computed at close | one `evaluate()` per close | **YES** — exit/giveback is the only positive lever (CLAUDE.md Phase-2) |
| 2 | **Giveback / BE-scratch** | analyzed in diagnose.py §3 only | already captured (`peak_r` v1.38.6+) | **YES** — 46.5% of exits scratch, peak_r 0.4–0.7 given back |
| 3 | ETE entry-truth score | computed every entry, discarded | already computed | **NO** — Phase-2 proved no entry expectancy |
| 4 | regime_memory fit-score | recorded, read only in API | already recorded | UNTESTED — no calibration run |
| 5 | cvd_tracker order-flow | computed, never consumed (FTD-092 F-1) | already computed | UNTESTED |
| 6 | NEXUS KGE/HKE/AEG | roadmap-pending knowledge | large (new subsystems) | **NO** decision edge — knowledge/advisory only |

**Finding M-2.** The two highest-ROI dormant assets (XTE, giveback) are the
cheapest to operationalize because the engine *already* declares XTE and already
captures `peak_r`. The most expensive roadmap items (KGE/HKE/AEG, ranks far
below) carry **no decision edge at all** — they improve institutional memory and
future advisory quality, not trade outcomes.

---

## 3. SUBSYSTEM-BY-SUBSYSTEM AUDIT (the periphery, verified)

### 3.1 Truth Stack — the buried treasure
- **ETE** runs a real 6-dimension `entry_truth_engine.evaluate(...)` on *every*
  entry (main.py:2626) with `gate_enabled=cfg.ETE_GATE_ENABLED` (=False,
  config.py:785). The score is emitted only to `_thought(... "TRUTH")` and
  stashed in `_pending_ete_results` to be attached to the AAP snapshot at close
  (main.py:892–907). It never reaches `risk_ctrl.get_trade_decision` (the very
  next call, main.py:2653). **Open-loop, confirmed.**
- **XTE** is imported (main.py:150) but the attribution snapshot hardcodes
  `exit_truth_score=0.0  # XTE not yet evaluated at close in Phase 1`
  (main.py:901). **The exit-truth signal does not exist yet at runtime.** This
  is the single most consequential finding of the audit: the lever the data
  says is real is not being measured.
- **AAP** records `AttributionSnapshot` at close (main.py:894) — pure reporting.

### 3.2 NEXUS — Institutional Intelligence Layer
Runs in a **background daemon thread** `nexus-enrichment` (main.py:3923–3925),
off the hot path. Its only decision-region touchpoint is **DOAE**: every 100
trades it records a performance snapshot inside a `try/except: pass`
(main.py:745–759). This is *recording*, not influence — if it threw, the trade
is unaffected. KGE/HKE/AEG are roadmap-pending (CLAUDE.md) and currently produce
no runtime decision input.

### 3.3 CORTEX — code-governance introspection
Imported at main.py:159 (`cortex_module_registry`, `cortex_dependency_mapper`,
`conflict_engine`, `influence_matrix`, `blame_engine`, `constitution_registry`,
`counterfactual_engine`). Actual usage is at **startup** (build dependency graph
+ influence matrix + constitution summary, main.py:3928–3946) and via
`/api/cortex/*` endpoints. **Zero references in the `on_tick` decision region.**
CORTEX reasons about the *codebase*, not the *market*.

### 3.4 OBSX — observability
No `core/obsx` package exists; OBSX is a versioned namespace (`OBSX_VERSION`,
`OBSX_NAME`, `OBSX_COMPONENTS`) surfaced through `/api` endpoints
(main.py:15553, 15582) and the boot declaration (main.py:3855–3871). Health/
observability reporting only.

### 3.5 Governance (Guardian / EGI / DIAL / AEOS / EMA)
Guardian runs a reactive watch task (main.py:3345–3365) that can adjust
aggression profile — advisory/parametric, not a per-tick gate. The rest are
memory/governance/reporting layers with no decision-path hook.

**Finding M-3.** The periphery is architecturally clean: it is *deliberately*
isolated from execution, which is correct and safe. But that same isolation
means no amount of further periphery investment (KGE/HKE/AEG, more governance)
moves a single trade. The ROI of the roadmap's next three phases, measured in
*trade outcomes*, is zero by construction.

---

## 4. THE SMALLEST / SAFEST / HIGHEST-ROI PATH (the deliverable)

Per the mandate, one ranked recommendation using only intelligence already
present. Each step is strictly observation-mode and reversible by a flag.

### ✅ STEP 1 (DO THIS) — Compute XTE at close, observation-only
**Change:** replace the hardcoded `exit_truth_score=0.0` (main.py:901) with a
real `exit_truth_engine.evaluate(...)` call at trade close, fed the data already
in scope at that point (`peak_r`, `r_multiple`, exit reason, regime, fees,
giveback). Write the result into the AAP snapshot. **Behind a flag**
(`XTE_OBSERVE_ENABLED`, default-respecting the existing
`XTE_FORCE_CLOSE_ENABLED=False` doctrine). **No exit is forced, no decision
changes.**

- **Why highest ROI:** it is the *only* path that begins measuring the *only*
  lever the institutional data endorses (exit/giveback). Without it, the
  Phase-4 XTE roadmap can never calibrate — there is no data.
- **Why smallest:** one `evaluate()` call at an existing call site; the inputs
  already exist (`peak_r` since v1.38.6). No new module, thread, feed, or gate.
- **Why safest:** computed at close (no entry latency), flag-gated, observation
  only, `try/except`-isolatable exactly like DOAE. Rollback = flip the flag.
- **Cost:** O(1) per close, off the entry hot path. < 1 ms.

### ✅ STEP 2 (DO THIS NEXT) — Promote giveback to a calibrated metric
Surface the diagnose.py §3 giveback / BE-scratch analysis as a standing
calibration counter (reuse `peak_r`), so that after ≥500 closes the exit lever
has an out-of-sample expectancy verdict — the same bar CLAUDE.md set for ETE.
No new data; this is wiring existing diagnostics into a persistent counter.

### ⚠️ STEP 3 (OPTIONAL, LOW-COST) — Calibrate regime_memory fit-score
It is already recorded (main.py:770) but never tested as a decision input. A
read-only offline calibration (does fit-score predict expectancy?) costs nothing
at runtime and either promotes it to a future advisory or formally closes it.

### ⛔ DO NOT — Expand the periphery for decision ROI
KGE / HKE / AEG, additional governance layers, and entry-score reweighting
(disproven, CLAUDE.md Phase-2) must **not** be justified as trade-outcome
improvements. They are legitimate *institutional-memory* work, but they are
**out of scope for the highest-ROI-edge mandate** and should not be sequenced
ahead of Steps 1–2.

> **Bottom line:** the cheapest, safest line in the entire codebase between
> "intelligence we already have" and "a real edge lever" is **un-stubbing
> XTE**. Everything else is either disproven (entry), decision-mute (NEXUS/
> CORTEX/OBSX), or untested (regime_memory, cvd).

---

## 5. RISK ASSESSMENT

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R-1** | Computing XTE at close adds latency / can throw | LOW | At close, not entry; `try/except` isolate like DOAE; < 1 ms |
| **R-2** | Observation XTE drifts toward acting before calibration | HIGH | Strict flag (`XTE_FORCE_CLOSE_ENABLED=False` unchanged); Step 1 only *records* a score; gating stays Phase-4 / BLOCKED |
| **R-3** | Giveback counter mis-measures (legacy trades lack peak_r) | LOW | Count only `peak_r>0` trades (already the diagnose.py §3 convention) |
| **R-4** | Recommendation read as "stop institutional-memory work" | MED | Explicitly scoped: KGE/HKE/AEG remain valid Chain-A memory work; this audit ranks *decision-edge* ROI only, not memory value |
| **R-5** | Entry-reweighting revived under a new name | HIGH | Reaffirm CLAUDE.md Phase-2 verdict; no entry-component lever is approved |

**Governance compliance:** this audit recommends **removing nothing** — no
governance, no gate, no truth attribution, no paper-trading safeguard. Step 1 is
purely additive + observational and preserves the single-execution-authority and
flag-doctrine invariants.

---

## 6. WHAT FTD-092 (AMIL) GOT RIGHT, AND WHERE THIS AUDIT DIVERGES

FTD-092 correctly identified the open-loop Truth Stack (F-2) and correctly
sequenced AMIL **exit-side-first**. This master review **sharpens** that into the
minimal first move and adds one finding FTD-092 did not surface:

- **AMIL proposed a new `core/amil/` consolidation + explainability layer.**
  That is a larger build than the mandate ("smallest path") wants as a *first*
  step. The consolidation (MarketState) and explainability (DecisionRationale)
  are valuable but are **Phase D/legibility** work, not the highest-ROI edge.
- **The edge bottleneck is narrower than "wire the Truth Stack":** XTE is not
  open-loop, it is **un-computed**. You cannot wire a signal that does not exist.
  Step 1 (un-stub XTE) is the precondition for *any* exit-side AMIL phase.

So this audit is **consistent with FTD-092** but reorders: *un-stub XTE and
collect exit calibration data first; build the AMIL consolidation/explainability
layer only after the exit lever has a positive-expectancy verdict.*

---

## 7. EVIDENCE LEDGER (every claim is code-anchored)

| Claim | Anchor |
|---|---|
| 21,307-line main.py; 130 `core/` dirs; 945 `core/` files; 1,209 `.py` | repo scan |
| ETE evaluated every entry, gate off, logged only | main.py:2626–2651; config.py:785 |
| ETE score preserved to close for AAP | main.py:892–907 |
| **XTE hardcoded `exit_truth_score=0.0`** | **main.py:901** |
| XTE imported but unused at runtime | main.py:150 |
| `XTE_FORCE_CLOSE_ENABLED` default False | config.py:787 |
| regime_memory recorded at close, read only in API | main.py:770; 4882; 10994 |
| DOAE 100-trade recording snapshot, swallowed | main.py:745–759 |
| NEXUS background daemon thread | main.py:3923–3925 |
| CORTEX import + startup build + `/api/cortex/*` | main.py:159; 3928–3946 |
| OBSX = version namespace + `/api` only | main.py:15553; 15582; 3855–3871 |
| peak_r captured v1.38.6+; giveback in diagnose.py §3 | CLAUDE.md; main.py:6719–6744 |
| Entry-component reweighting disproven (530–535 samples) | CLAUDE.md Phase-2 |

---

## 8. OPEN QUESTIONS FOR APPROVER

1. **Approve Step 1 (un-stub XTE at close, observation-only) as the single
   highest-ROI first move?** *(Recommended: yes.)*
2. Confirm the calibration bar for the exit lever = **≥500 closes + positive
   out-of-sample expectancy** (mirrors ETE doctrine)?
3. Confirm that KGE/HKE/AEG and further governance remain **Chain-A memory
   work**, explicitly *not* sequenced ahead of Steps 1–2 on edge grounds?
4. Should regime_memory and cvd_tracker get a one-time offline calibration
   (Step 3) to either promote or formally close them as dormant loops?

---

## 9. VERSIONING & INSTITUTIONAL RECORD

- **APP_VERSION:** documentation-only audit deliverable → **PATCH 1.91.1 →
  1.91.2** (CLAUDE.md: forensic-traceable artifacts warrant ≥ PATCH; no
  `main.py`/`core/`/`strategies/` behavior change in this deliverable).
- **IMRAF:** on approval, record QFTD-093 under `decisions`/`roadmap` with the
  core verdict — *"highest-ROI edge move is un-stubbing XTE (main.py:901); the
  NEXUS/CORTEX/OBSX periphery is decision-mute by design and carries no trade
  ROI"* — so future sessions can answer *"where is the real edge lever?"*.

---

*End of qFTD-093 / Master Intelligence Architecture Review. No production code
is included by design. The recommended first implementation step is the
single-line-class un-stubbing of XTE at close, observation-mode, pending
approval.*
