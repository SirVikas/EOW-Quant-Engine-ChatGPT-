# 🧾 qFTD-092 — AUTONOMOUS MARKET INTELLIGENCE LAYER (AMIL) — DESIGN BLUEPRINT

**Ref:** FTD-092_AUTONOMOUS_MARKET_INTELLIGENCE_FRAMEWORK
**Status:** PRE-FTD DESIGN STUDY — *no production implementation in this deliverable*
**Engine build:** APP_VERSION 1.91.0 (documentation-only bump → 1.91.1; see §10)
**Author note:** Per FTD-092 "REQUIRED DELIVERABLES", the developer SHALL NOT
directly implement AMIL. This document delivers the eight required artifacts
(qFTD, Architecture Study, Feasibility, Risk Assessment, Component Mapping,
Migration Roadmap, Computational Cost, Integration Strategy) plus a
**non-invasive demonstration verifier** (`tests/verify_amil_blueprint.py`) that
exercises the *existing* modules read-only. Nothing in this deliverable wires
AMIL into the live trading path, removes governance, or changes a single trade
decision.

---

## 0. EXECUTIVE SUMMARY — WHAT AMIL ACTUALLY IS (AND IS NOT)

The forensic survey of the live codebase (main.py ≈ 970 KB + ~130 `core/`
packages) produced a single dominant finding that reframes the entire mission:

> **The EOW engine already reasons across most of the dimensions FTD-092 asks
> for. What it lacks is (a) a single consolidated market-state object, (b) a
> closed feedback loop from the Truth Engines to the decision, and (c) one
> explainable "why" record per decision. The intelligence exists; it is
> scattered and partially mute.**

Therefore AMIL is **not a new signal generator and not a new alpha source.** It
is an **orchestration + consolidation + explainability layer** that sits *above*
the existing single execution authority and *below* nothing — it never bypasses
a gate.

This framing is not optional editorializing — it is forced by the project's own
institutional record. CLAUDE.md (TRUTH ENGINE ROADMAP, Phase-2 result, v1.88.0)
documents that a 530–535 sample calibration found **no entry-component threshold
or reweighting with positive expectancy** — "the truth signal is NOT in the
entry components … the expectancy lever is the EXIT side + fees." Any AMIL design
that promises a magic "trade attractiveness score" which finds new entry alpha
would directly contradict a verified institutional finding and is rejected by
this study (see §3 Feasibility, §4 Risk R-1).

**What AMIL credibly delivers:**
1. **Consolidation** — one `MarketState` object replacing ~7 independently-called
   context modules, removing inconsistency and ordering hazards.
2. **Closed-loop intelligence** — wire the already-computed ETE/XTE/AAP/Economic
   Truth signals (today 100% reporting-only) into decision-time *advisory*
   inputs, behind observation-mode flags, calibrated before they ever gate.
3. **Explainability** — one auditable `DecisionRationale` record per
   accept/reject/size decision, satisfying the "explainable, auditable,
   reportable" mandate and feeding IMRAF.
4. **Allocation discipline** — a single, inspectable attractiveness→size mapping
   that *documents and unifies* the existing multiplier cascade rather than
   adding a sixth opaque multiplier.

**What AMIL must NOT claim:** that it creates edge by re-scoring entries. Its
honest edge contributions are exit-side truth, fee/cost discipline, and
inactivity discipline ("when to remain inactive") — the levers the data says are
real.

---

## 1. CURRENT-STATE ARCHITECTURE STUDY (GROUNDED IN CODE)

### 1.1 The decision spine that exists today

Every new trade flows through **one** execution authority:

```
core/orchestrator/execution_orchestrator.py:145  ExecutionOrchestrator
    run_cycle(TickContext) -> CycleResult         (the ONLY trade-approval entry)
```

`TickContext` (execution_orchestrator.py:89) is the existing decision payload:
`symbol, price, regime(str), strategy, ev, trade_score, volume_ratio, equity,
base_risk_usdt, upstream_mult, indicator_ok, data_fresh, history_score,
is_exploration`. It is constructed at **main.py:2572** and consumed at
**main.py:2587**. **This is AMIL's integration seam** (§8).

### 1.2 The 21-gate entry pipeline (main.py `on_tick`, ~lines 571–2850)

The signal→trade path is already a deep, sequential filter. Abbreviated:

| Stage | Module | Role |
|------|--------|------|
| 0a Global Gate | `core/global_gate.py` | system readiness (indicators, ws, data, deployability) |
| 0b Pre-Trade Gate | `core/gating/pre_trade_gate.py` | per-symbol safety |
| 1 Volume Sleep | `core/volume_filter.py` | thin-market suppression |
| 2 Sector Guard | `core/sector_guard.py` | ≤2 positions/sector |
| 3 Risk Engine | `core/risk_engine.py` | daily loss/trade/DD caps |
| 4 Market Structure | `core/market_structure.py` | block LOW_VOL_TRAP / FAKE_BREAKOUT |
| 5 RL Gate | `core/rl_engine.py` | block toxic (regime,hour,strategy) Q-context |
| 6 Lean Gate | `core/lean_gate.py` | SL dist, RR, fee%, loss-streak, DD |
| 7 Fee Gate | `core/execution_engine.py` | TP must cover round-trip fees |
| 8 Loss Cluster | `core/loss_cluster.py` | cluster → size cut / pause |
| 9 Exploration Guard | `core/exploration_guard.py` | daily exploration loss cap |
| 10 Profit Guard | `core/profit_guard.py` | gross/fee ≥ 5× |
| 11 Signal Filter | `core/signal_filter.py` | per-regime RR/conf floors |
| 12 Strategy Engine | `core/strategy_engine.py` | hard quality gate |
| 13 Adaptive Scorer | `core/adaptive_scorer.py` | 6-factor self-learning score |
| 14 Confidence Decay | `core/confidence_decay.py` | distance-to-profit decay |
| 15 RR Engine | `core/rr_engine.py` | enforce/adjust SL-TP |
| 16 Smart Fee Guard | `core/smart_fee_guard.py` | RR-aware fee tolerance |
| 17 EV Engine | `core/ev_engine.py` | block EV ≤ 0 |
| 18 EV Confidence | `core/ev_confidence.py` | EV tier → size mult |
| 19 Drawdown Ctrl | `core/drawdown_controller.py` | DD tier size mult |
| 20 Capital Recovery | `core/capital_recovery.py` | post-loss size restoration |
| 21 Capital Allocator | `core/capital_allocator.py` | final risk budget / qty |
| → Orchestrator | `execution_orchestrator.run_cycle` | rank→compete→concentrate→PTG→amplify |

**Implication for AMIL:** the engine is *not* under-gated. Adding more gates is
the wrong move (R-3). AMIL's job is to make this stack *coherent and
explainable*, not longer.

### 1.3 Market-context modules (scattered — no unified object)

The eight FTD-092 "dimensions" map to existing producers, but each is called
independently and packed into `TickContext` as a bare `regime` string:

| FTD-092 dimension | Existing producer(s) | Output today | Reaches decision? |
|---|---|---|---|
| Market structure | `market_structure.py` (`MarketStructureResult`: TREND/RANGE/FAKE_BREAKOUT/LOW_VOL_TRAP/UNKNOWN) | 5-label + `tradeable` bool | as a gate (4), not as context |
| Regime | `regime_detector.py` (3-label `RegimeState`), `regime_ai.py` (weighted + stability + `block_trade`) | label + confidence | regime **string** only into TickContext |
| Volatility | implicit in `regime_*` (ATR%, BB width, vol_ratio); explicit LOW_VOL_TRAP | ratios/flags | partial |
| Liquidity | `volume_filter.py` (on/off), `dynamic_thresholds.py` (vol multiplier) | ON/OFF + multiplier | as a gate (1) |
| Momentum | RSI/ADX inside scorers + `regime_ai` | factor scores | inside score (13) |
| Cost structure | `cost/cost_engine.py` (`NetEdgeResult`, verdict APPROVE/EXPLORE/REJECT), `cost_guard.py`, `smart_fee_guard.py` | net-edge + size_factor | gates 7/10/16 |
| Order-flow | `cvd_tracker.py` (`CVDState`: cvd, slope, imbalance) | directional pressure | **computed but NOT gated/consumed** |
| Inter-market / sector | `sector_guard.py` | concentration cap | gate 2 |

> **Finding F-1:** No `MarketState` object exists. Context is reconstructed
> per-tick across ~7 modules; `cvd_tracker` order-flow is computed but never
> consumed at decision time. This is the consolidation opportunity.

### 1.4 The feedback loops — one closed, one open

**Closed loop (already live, decision-time):**
```
[close] learning_engine.record()  rl_engine.update()  adaptive_edge_engine.on_trade_closed()
[entry] learning_engine.get_regime_weight() → conf×weight   (main.py:1620)
        rl_engine.confidence_boost()        → conf×boost    (main.py:1623)
        rl_engine.should_trade()            → hard block     (main.py:2053)
        edge_engine size multiplier / state machine
```

**Open loop (computed but mute — reporting only):**
```
[close] ETE / XTE / AAP / Economic Truth / Signal-Truth / Strategy-Truth compute
        rich per-component scores  →  forensic JSON / reports
[entry] (ignored — ETE_GATE_ENABLED=False, XTE_FORCE_CLOSE_ENABLED=False)
```

> **Finding F-2:** The Truth Engine stack is 100% reporting-only. ETE scores
> every entry across 6 components and logs (main.py:2622) but never blocks; XTE
> emits advisory hints never applied; AAP records post-close snapshots for
> reports. **This is the single largest latent intelligence asset and AMIL's
> primary integration target — but only after calibration (see §3, R-1).**

### 1.5 Existing capital-sizing cascade

Sizing is already adaptive (not fixed-percentage), via a multiplier chain:

```
qty_base = equity·risk% / SL_dist           (utils/capital_scaler.py — quarter-Kelly, 0.5%–3.0%)
  × regime_weight        (learning_engine)
  × rl_boost             (rl_engine.confidence_boost, 0.85×–1.35×)
  × allocator band       (capital_allocator, 0.5×–2.0×)
  × dd tier              (drawdown_controller)
  × concentration_mult   (capital_concentrator via orchestrator, ELITE→2.0×)
  clamp(MIN_NOTIONAL, MAX_NOTIONAL)
```

> **Finding F-3:** FTD-092 Phase C ("size from understanding not fixed %") is
> *already substantially built*. The gap is not capability but **legibility** —
> six multipliers compound with no single record of "why this size". AMIL
> Phase C is therefore a *documentation/consolidation* of this cascade plus
> one rationale record, NOT a new sizing algorithm.

---

## 2. THE EIGHT FTD-092 DECISIONS → WHERE THEY LIVE TODAY

FTD-092 says AMIL must decide 8 things. Honest current-state mapping:

| # | AMIL decision | Already handled by | AMIL's actual contribution |
|---|---|---|---|
| 1 | Should a trade exist at all? | Gates 0–12, RL gate | Consolidate rationale; add ETE-advisory (post-calib) |
| 2 | Which trade is worth taking? | trade_ranker / competition / adaptive_scorer | Unify into one attractiveness view + explainability |
| 3 | When to enter? | confidence_decay, execution_drive_policy | Add market-state timing context (compression→expansion) |
| 4 | How much capital? | sizing cascade §1.5 | One legible attractiveness→size map + rationale |
| 5 | When to increase exposure? | capital_concentrator (ELITE band), scaling states | Make band logic market-state aware + explainable |
| 6 | When to reduce exposure? | drawdown_controller, loss_cluster, capital_recovery | Wire XTE giveback advisory (post-calib) |
| 7 | When to exit? | trade_manager, exit_attribution, XTE (advisory) | **Highest-value target** — exit-side is the real lever |
| 8 | When to remain inactive? | volume sleep, no-trade freeze, safe_mode | Promote to first-class "INACTIVE" market-state verdict |

**Strategic read:** decisions 1–5 are largely solved; AMIL adds legibility.
Decisions 6–8 (reduce / exit / stay flat) are where the *data-supported* edge
lives (CLAUDE.md: exit + fees + BE-scratch giveback). **AMIL should be
sequenced exit-side-first, not entry-side-first.**

---

## 3. FEASIBILITY ANALYSIS

### 3.1 Technically feasible — YES, as an advisory consolidation layer
All inputs already exist as Python objects produced each tick. Building a
`MarketState` dataclass and a `DecisionRationale` record is pure aggregation of
values already in scope at main.py:2572. No new data feeds, models, or external
dependencies are required for Phase A/B observation mode.

### 3.2 Edge feasibility — QUALIFIED, and honestly bounded
- **Entry reweighting: INFEASIBLE as an edge source.** CLAUDE.md Phase-2
  (530–535 samples, v1.88.0) proved no entry-component threshold/reweighting
  yields positive expectancy; `structure` was inverted, `regime` constant,
  `cost<40` near-certain-loss but small. AMIL must **not** be sold as fixing
  this. A composite "attractiveness" score may improve *win-probability
  ranking* (score IS monotonic with win-rate) but not *dollar expectancy* —
  exactly the prior trap. → **R-1.**
- **Exit / fee / giveback: FEASIBLE edge surface.** 46.5% of exits are BE
  scratches giving back peak_r ≈ 0.4–0.7; gross expectancy −$0.02 vs fees
  −$0.026. XTE advisory data is the designated vehicle. AMIL exit-side advisory
  has a real, data-identified target.
- **Inactivity discipline: FEASIBLE.** Avoiding negative-expectancy regimes/
  sessions (already partly done via RL gate + sleep) is a legitimate,
  low-risk capital-preservation lever.

### 3.3 Calibration gating — MANDATORY
Like ETE, every AMIL advisory output must run in **observation mode** (logged,
not acted on) until a ≥500-trade calibration demonstrates positive
out-of-sample expectancy for that specific lever. No AMIL signal gates or sizes
a live trade before its own calibration verdict. This mirrors the existing
`ETE_GATE_ENABLED=False` doctrine and is the project's proven safety pattern.

### 3.4 Explainability — FEASIBLE and required
Every input is a scalar/label with a known provenance module. A
`DecisionRationale` (per-decision list of `(factor, value, weight,
contribution, source_module)`) is straightforward and satisfies the
"no black-box" mandate. No opaque ML model is proposed; the attractiveness
function is a transparent weighted sum with logged components.

---

## 4. RISK ASSESSMENT

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R-1** | "Attractiveness score" recreates the disproven entry-reweighting trap; ranks win-rate not dollars | **HIGH** | Score is advisory-only + calibration-gated; expectancy (not win-rate) is the acceptance metric; document the Phase-2 finding inline |
| **R-2** | Adding a layer above the single execution authority creates a *second* implicit decision path | HIGH | AMIL never calls open_position / run_cycle; it only *annotates* TickContext and emits advisory multipliers ∈[1.0,1.0] in observation mode; orchestrator remains sole authority |
| **R-3** | More gates → more deadlock/no-trade surface (cf. lean-gate Gate-4 loss-streak deadlock in CLAUDE.md) | HIGH | AMIL adds **zero** new hard gates in Phases A–C; advisory only; INACTIVE verdict is observability, not a new block |
| **R-4** | Consolidation refactor breaks the 21-gate ordering / side effects | HIGH | Phase A builds `MarketState` *alongside* existing calls (read-only mirror), asserts parity in verifier, before any call-site is removed |
| **R-5** | Wiring ETE/XTE into decisions before calibration blocks valid trades | HIGH | Strictly behind `AMIL_*_ENABLED=False`; reuse ETE Phase-1→4 activation doctrine |
| **R-6** | Compute cost per tick rises (§7) | MED | Reuse already-computed values; no recomputation; budget < 1 ms/tick (§7) |
| **R-7** | Governance erosion (FTD-092 restriction) | HIGH | No governance/risk/truth/paper-safeguard removed; AMIL is purely additive + observational; verifier asserts gate count unchanged |
| **R-8** | Version/forensic traceability drift | LOW | APP_VERSION bump per CLAUDE.md; IMRAF record on acceptance |

**Governance restriction compliance (FTD-092 "MANDATORY RESTRICTIONS"):** this
blueprint removes no governance, no risk control, bypasses no truth attribution,
bypasses no paper-trading safeguard, and introduces no black-box. Confirmed.

---

## 5. COMPONENT MAPPING (AMIL → existing modules)

AMIL is proposed as a thin new package `core/amil/` whose components are
**adapters over existing engines**, not reimplementations:

```
core/amil/
  market_state.py        MarketState dataclass + MarketStateBuilder
                         └─ reads: regime_detector, regime_ai, market_structure,
                            cvd_tracker, volume_filter, dynamic_thresholds, cost_engine
  attractiveness.py      TradeAttractiveness (transparent weighted sum)
                         └─ reads: adaptive_scorer, ev_engine, ev_confidence,
                            edge_engine, cost_engine, rl_engine(boost), ETE(score)
  allocation_reasoner.py AllocationRationale (documents §1.5 cascade; no new math)
                         └─ reads: capital_scaler, capital_allocator,
                            drawdown_controller, capital_concentrator
  rationale.py           DecisionRationale record (factor,value,weight,contrib,source)
                         └─ writes: thought log + IMRAF (advisory)
  amil_engine.py         AMILEngine facade: build_state→score→reason (observation mode)
```

| AMIL component | Consumes (existing) | Produces | Mode |
|---|---|---|---|
| MarketStateBuilder | 7 context modules §1.3 | `MarketState` (unified label set incl. INACTIVE) | observe |
| TradeAttractiveness | scorers + EV + edge + cost + ETE | 0–1 score + component breakdown | observe |
| AllocationReasoner | sizing cascade §1.5 | size rationale (mirrors current qty) | observe |
| DecisionRationale | all above + final orchestrator result | one auditable record/decision | observe→report |
| AMILEngine | facade | advisory bundle attached to TickContext | observe |

**No existing module is modified in Phases A–C** beyond the optional, additive
attachment of an `amil` advisory field to `TickContext` (default `None`).

---

## 6. MIGRATION ROADMAP (phased, ETE-doctrine-aligned)

| Phase | Scope | Gate condition | Live impact |
|------|------|---------------|-------------|
| **A — Observation** | Build `core/amil/`, `MarketState`, `DecisionRationale`; compute alongside live path; log only | none | **zero** — pure shadow compute |
| **B — Attractiveness shadow** | Compute attractiveness + allocation rationale every decision; record vs actual outcome | A complete | **zero** — logged, never acted |
| **B-cal — Calibration** | Collect ≥500 decisions; measure per-lever out-of-sample expectancy (entry-rank, exit-advisory, inactivity) | ≥500 samples | zero |
| **C — Advisory exit-side** | If (and only if) B-cal shows positive expectancy on exit/giveback, enable XTE-style advisory into trade_manager behind `AMIL_EXIT_ADVISORY_ENABLED=False`→test | B-cal positive on exit lever | opt-in, advisory |
| **D — Allocation legibility live** | Replace scattered context calls with `MarketStateBuilder` after verifier parity proof (R-4) | A+verifier parity | behavior-neutral refactor |
| **E — Governed gating (BLOCKED)** | Any AMIL signal that *blocks/sizes* a trade. Requires per-lever calibration + explicit IMRAF ADR | per-lever calib + ADR | **BLOCKED until then** |

> Sequencing mirrors the locked ETE Phase-1→4 doctrine and the project's
> "observe → calibrate → advise → gate" safety ladder. Entry-side gating (E) is
> the *last and most restricted* step precisely because the data says it is the
> weakest lever.

---

## 7. COMPUTATIONAL COST ASSESSMENT

**Principle:** AMIL reuses values already computed each tick; it does not
recompute indicators, regimes, EV, or costs.

| Operation | Cost | Notes |
|---|---|---|
| MarketState assembly | O(1), ~µs | dataclass packing of existing scalars |
| Attractiveness (weighted sum, ~8 terms) | O(1), ~µs | no model inference |
| AllocationReasoner | O(1) | reads cascade results already produced |
| DecisionRationale record | O(k), k≈10 factors | one list build |
| IMRAF advisory write (Phase C+) | async / batched | reuse `imraf_engine.record`; off hot path via `to_thread` |
| **Per-tick added latency (A/B)** | **< 1 ms target** | dominated by logging, not math |

**Memory:** one `MarketState` + one `DecisionRationale` per decision; bounded
ring buffer for calibration (≤ a few MB for 500–1000 samples). No new threads;
no new sockets. The existing single-process asyncio model (CLAUDE.md thread
model) is preserved; any persistence uses `to_thread()` like existing blocking
calls. This fits comfortably within the qFTD-031 latency doctrine.

---

## 8. INTEGRATION STRATEGY

### 8.1 The seam
```
main.py:2572  _orch_ctx = TickContext(...)          # existing
main.py:2587  _cycle = execution_orchestrator.run_cycle(_orch_ctx)   # existing — SOLE authority
```
AMIL attaches **before** 2587, purely additively:
```
amil_bundle = amil_engine.observe(_orch_ctx, market_inputs)   # NEW, observation mode
# amil_bundle: MarketState + attractiveness + allocation rationale + DecisionRationale
# In observation mode it returns advisory multipliers == 1.0 and only logs/records.
_orch_ctx.amil = amil_bundle        # optional field, default None — orchestrator ignores it
```
The orchestrator is **unchanged** and remains the only thing that can open a
position. AMIL cannot execute, size, or block in Phases A–C; it can only
annotate and record.

### 8.2 Flags (config.py, ETE-style, all observation-safe defaults)
```python
AMIL_ENABLED:               bool  = False   # master shadow-compute switch
AMIL_EXIT_ADVISORY_ENABLED: bool  = False   # Phase C — post exit-calibration only
AMIL_GATE_ENABLED:          bool  = False   # Phase E — BLOCKED until per-lever calibration + ADR
```
Mirrors `ETE_GATE_ENABLED` / `XTE_FORCE_CLOSE_ENABLED` semantics exactly.

### 8.3 Observability
- Thought-log lines (`_thought(... , "AMIL")`) for each shadow decision.
- `GET /api/amil` (future) surfacing latest `MarketState` + `DecisionRationale`
  — read-only, consistent with `GET /api/nexus`, `GET /api/truth/*`.
- IMRAF advisory records for calibration milestones.

### 8.4 Rollback
Because every phase ≤ D is additive/observational, rollback is "set
`AMIL_ENABLED=False`" or revert the `core/amil/` package — no live decision
depends on it.

---

## 9. MANDATORY VERIFIER (delivered)

`tests/verify_amil_blueprint.py` — a standalone, **read-only** verifier that
demonstrates the five FTD-092-required capabilities against the *real* existing
modules, without touching the live trading path:

1. **Market-state detection** — assembles a unified `MarketState` from the
   actual `regime_detector` / `market_structure` / `cvd_tracker` outputs on a
   synthetic candle series, including the new first-class `INACTIVE` verdict.
2. **Decision reasoning** — produces a `DecisionRationale` listing each factor,
   its value, weight, contribution, and **source module**.
3. **Attractiveness scoring** — computes a transparent weighted-sum score and
   prints the component breakdown (no black-box).
4. **Capital-allocation reasoning** — shows the §1.5 multiplier cascade as an
   explainable size rationale for a sample decision.
5. **Explainability output** — emits a human-readable rationale block proving
   every number is traceable to a source.

The verifier **asserts AMIL is non-invasive**: it imports the existing engine
modules read-only, opens no position, and confirms the design adds zero hard
gates. Exit code 0 = all demonstrations pass.

> Note: the verifier demonstrates the *blueprint concepts* using lightweight
> in-file reference structures (since `core/amil/` is intentionally not built in
> this design phase) wired to real `core/` modules. It is the proof-of-concept
> the FTD requires "before any production integration", not a production unit.

---

## 10. VERSIONING & INSTITUTIONAL RECORD

- **APP_VERSION:** documentation + verifier deliverable → **PATCH bump 1.91.0 →
  1.91.1** (CLAUDE.md rule: forensic-traceable artifacts warrant ≥ PATCH; no
  `main.py`/`core/`/`strategies/` behavior changes here, so PATCH is correct).
- **IMRAF:** on FTD-092 approval, record this blueprint under category
  `decisions`/`roadmap` with the Phase-A→E sequence and the R-1 entry-edge
  caveat, so future sessions can answer *"what is AMIL and why is it exit-side
  first?"*.

---

## 11. OPEN QUESTIONS FOR APPROVER (qFTD)

1. **Sequencing:** Approve **exit-side-first** AMIL (Phases C targets XTE
   giveback) over entry-side, given the Phase-2 expectancy finding? *(Recommended:
   yes.)*
2. **Scope of Phase A:** Build `core/amil/` as a real shadow package now, or keep
   it verifier-only until KGE/HKE land (CLAUDE.md roadmap lists KGE next)?
3. **MarketState authority:** Is consolidating the 7 context modules into one
   `MarketStateBuilder` (Phase D, behavior-neutral) approved, or should the
   scattered calls remain for now?
4. **Calibration bar:** Confirm ≥500 out-of-sample decisions + positive
   expectancy (not win-rate) as the gate to advance any lever past observation.
5. **Roadmap placement:** Does AMIL slot *after* KGE/HKE (Chain-A) or run as an
   independent Chain-C, analogous to the independent Chain-A/Chain-B model?

---

*End of qFTD-092 / AMIL Design Blueprint. No production AMIL code is included by
design. Implementation begins only after approval of this study.*
