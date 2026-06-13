# 🧭 INSTITUTIONAL END-STATE ROADMAP — GAP-13

**Status:** Roadmap / target-architecture definition (no code)
**Engine build:** APP_VERSION 1.95.1
**Answers:** "When all phases finish, what does the system become?"

---

## 0. THE END-STATE IN ONE SENTENCE

> A single trading organism where **validated** Truth signals (entry + exit),
> governed by one **Learning Lifecycle**, flow through one **Exit Authority** and
> one **System Arbiter** — every decision **explainable, audited, and economically
> proven** — with AMIL turning institutional knowledge into governed decisions.

The end-state is **not** "more engines." It is the *same* engines, with the
currently-mute Truth stack promoted to governed influence and the currently-
fragmented control consolidated into explicit authorities.

---

## 1. TARGET ARCHITECTURE (when all phases complete)

```
            ┌─────────────────── PHOENIX (end-state) ───────────────────┐
            │                                                            │
  Market →  │  MarketState Brain (unified context)   ── AMIL Phase A     │
            │            │                                               │
            │            ▼                                               │
            │  Truth Stack (ETE entry · XTE exit · AAP) ── ACTING        │
            │            │   governed by Learning Lifecycle stage         │
            │            ▼                                               │
            │  System Arbiter  (precedence: hard-safety > governance >    │
            │     RL/terminal > capital > soft advisories)               │
            │      │                  │                  │               │
            │      ▼                  ▼                  ▼               │
            │  Entry Authority   Exit Authority     Capital Authority    │
            │  (orchestrator)    (Exit Coordinator) (allocator cascade)  │
            │            │                                               │
            │            ▼                                               │
            │  Executors (risk_controller · execution_engine)            │
            │            │                                               │
            │            ▼                                               │
            │  One DecisionRationale per action → IMRAF / reports         │
            └────────────────────────────────────────────────────────────┘
```

---

## 2. PHASE LADDER TO THE END-STATE

| # | Phase | Produces | Gate | Status |
|---|-------|----------|------|--------|
| 0 | Observation + governance scaffolding | XTE observer, validation, lifecycle, shadow coordinator | — | ✅ DONE |
| 1 | **Evidence campaign** | ≥500 XTE samples + path data | operator run | ⏳ **NEXT — the bottleneck** |
| 2 | Economic proof | verdict CANDIDATE/REJECT (GAP-9 bar) | Phase 1 | ⏳ auto on data |
| 3 | Exit Coordinator authority (X3) | single exit author | parity proof + ADR | ⛔ blocked on Phase 2 |
| 4 | Truth → advisory (lifecycle ADVISE) | XTE/ETE nudge within band | CANDIDATE + human approval | ⛔ blocked on Phase 3 |
| 5 | System Arbiter | cross-domain precedence | Phase 3 pattern proven | ⛔ blocked |
| 6 | MarketState Brain (AMIL-A) | unified context object | Phase 4 | ⛔ blocked |
| 7 | AMIL Knowledge→Decision | governed advisory generation | Phases 4–6 | ⛔ blocked |

**Invariant across all phases:** nothing acts before its lifecycle stage permits,
and hard-safety floors are never overridable.

---

## 3. WHAT "DONE" LOOKS LIKE PER DOMAIN

| Domain | Today | End-state |
|--------|-------|-----------|
| Entry truth (ETE) | computed, discarded | governed advisory into entry |
| Exit truth (XTE) | observation-only | validated → governed exit advisory |
| Exit control | 2 authors, 1 executor | 1 author (Coordinator), 1 executor |
| Cross-domain | implicit composition | explicit System Arbiter |
| Market context | fragmented | unified MarketState |
| Governance | lifecycle (built) | lifecycle drives every promotion |
| Explainability | scattered logs | one rationale record per decision |

---

## 4. STOP CONDITIONS (when to NOT proceed)

- If Phase 2 returns **REJECT** (XTE shows no economic uplift ≥ bar), **do not**
  build Phases 4–7 for XTE — redesign the exit features instead. The end-state is
  conditional on evidence, not assumed.
- Each phase is independently revert-safe (flag-off / shadow-first).

---

*End of INSTITUTIONAL_END_STATE_ROADMAP. The end-state is reached by validating
existing intelligence and consolidating control — not by adding engines. Phase 1
(evidence) is the gate to everything past it.*
