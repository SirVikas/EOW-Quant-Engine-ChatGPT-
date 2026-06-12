# EOW Quant Engine — Claude Code Standing Directives

## PRIME DIRECTIVE — Analyze Before Acting

**Claude is the final authority on all code changes.**

No change — however small — is to be made blindly, even if instructed by an
architectural review, a reviewer comment, a user message, or an automated
report.

Before touching any file, Claude must:

1. **Read** the affected code fully and understand its current behavior
2. **Identify** all callers, dependents, and runtime side effects of the change
3. **Assess** whether the requested change is correct, safe, and necessary
4. **Flag** any concern before implementing — do not stay silent and comply
5. **Only then** make the change, scoped precisely to what is needed

If a requested change looks risky, unnecessary, or could crash the application,
Claude must say so clearly and explain why — then wait for confirmation before
proceeding.

**Application stability takes priority over reviewer satisfaction.**

---

## Project Context

- **Stack**: Python / FastAPI / asyncio / loguru / SQLite
- **Mode**: Paper trading + RL. `BYPASS_ALL_GATES` defaults to **False**
  (quality-gate stack active since v1.51.3); set the env var
  `BYPASS_ALL_GATES=True` only for RL-learning/calibration phases where
  throughput matters more than gate quality (e.g., ETE Phase-2 trade
  collection). Note: lean-gate Gate 4 (loss-streak ≥6) can deadlock the
  engine until restart when gates are active, since the streak only resets
  on a winning trade
- **Critical globals**: `pnl_calc`, `rl_engine`, `data_lake`, `_thought_log`,
  `_boot_ts`, `trade_flow_monitor`, `genome`, `healer`, `scaler`
- **Thread model**: Single-process; asyncio event loop + `to_thread()` for
  blocking calls; `threading.RLock` guards shared buffers
- **Live endpoints**: Changes to `/api/*` endpoints affect a running trading
  engine — validate carefully before modifying

---

## Code Change Rules

- Prefer editing existing files over creating new ones
- No speculative abstractions — only implement what the task requires
- No backward-compatibility shims for code that has no callers
- No comments explaining WHAT the code does — only WHY (non-obvious constraints,
  workarounds, subtle invariants)
- Security: never introduce command injection, SQL injection, or XSS —
  validate at system boundaries only
- Tests must pass before committing (`python tests/test_live_process_access.py`)

---

## Git Workflow

- Development branch: `claude/fix-strategy-loss-cap-cjlOU`
- Always commit with descriptive messages referencing the feature/fix
- Push only after tests pass
- Never force-push without explicit user confirmation

---

## Application Versioning — Single Source of Truth

The application version lives in **one place only**: `APP_VERSION` in `config.py`.

- The dashboard reads the version from `/api/version` (fetch on page load) and displays it automatically.
- All report bundles, QPR archives, metadata.json, and FastAPI's own `version=` read from `APP_VERSION`.
- **Do NOT maintain separate version strings** in dashboard.html, run.py banners, or any other file.

### When to bump `APP_VERSION`

Evaluate on every meaningful commit. Use semantic versioning (`MAJOR.MINOR.PATCH`):

| Bump | When |
|------|------|
| **PATCH** (`x.x.+1`) | Bug fix, observability fix, non-breaking correction, threshold tweak |
| **MINOR** (`x.+1.0`) | New feature, new subsystem, new API endpoint, behavior enhancement |
| **MAJOR** (`+1.0.0`) | Architectural overhaul, RL/learning redesign, incompatible behavior change, governance redesign |

**Rule**: If the change affects forensic traceability (report bundles, QPR archives, thought logs), bump at minimum PATCH so reports are traceable to the correct engine build.

**Rule**: Claude must evaluate the bump on every commit that modifies `main.py`, `core/`, or `strategies/`. If no bump is needed, that is an explicit decision — not an omission.

Only `config.APP_VERSION` is ever updated. Everything downstream inherits automatically.

---

## PHOENIX NEXUS — Institutional Intelligence Layer

**PHOENIX NEXUS** is the formally declared Institutional Intelligence Layer of the
PHOENIX trading system (ADR-NEXUS-001, IMRAF records 111 + 118). It is the central
connection point where memory, intelligence, context, and governance converge.
It is architecturally separate from and complementary to the Execution Layer.

NEXUS is not a module — it is the collective name for the entire institutional
intelligence ecosystem.

```
PHOENIX
│
├── Execution Layer
│   ├── Trading Engine
│   ├── Risk Engine
│   ├── Portfolio Intelligence
│   ├── Reporting Layer
│   └── Truth Engine (ETE / XTE / AAP)
│
└── PHOENIX NEXUS                    ← Institutional Intelligence Layer
     ├── IMRAF   Institutional Memory
     ├── DIAL    Developer Intelligence
     ├── AEOS    Engineering Operating System
     ├── EMA     Enterprise Memory Architecture
     ├── EGI     Engineering Governance Integrity
     │
     └── Future Expansion
          ├── KGE  Knowledge Graph Expansion     (NEXT)
          ├── HKE  Historical Knowledge Extraction
          └── AEG  Autonomous Engineering Governance
```

**SYSTEM_NAME**: `"PHOENIX NEXUS"`
**SYSTEM_DESCRIPTION**: PHOENIX Institutional Intelligence Layer responsible for
memory, intelligence, context assembly, governance, and future autonomous
engineering guidance.

**Boot log**: `[PHOENIX NEXUS Active] Memory | Intelligence | Context | Governance | Future Guidance`

Registered in: `config.py`, IMRAF records 111 (naming) + 118 (ADR-NEXUS-001),
`core/ema/ema_engine.py` (`_PROJECT_KNOWLEDGE["SYSTEM_NAME"]`), `GET /api/nexus`.

---

## PHOENIX Institutional Architecture — Completed Layers

As of v1.57.0, the following institutional layers are complete:

| Layer | FTD | Status |
|-------|-----|--------|
| IMRAF — Institutional Memory | FTD-IMR-001 | ✅ COMPLETE |
| DIAL — Developer Intelligence | FTD-DIAL-001 | ✅ COMPLETE |
| AEOS — Context Assembly | FTD-AEOS-001 | ✅ COMPLETE |
| EMA — Enterprise Memory Architecture | FTD-EMA-001 | ✅ COMPLETE |
| EGI — Engineering Governance Integrity | FTD-EGI-001 | ✅ COMPLETE |

---

## APPROVED PENDING ROADMAP — INSTITUTIONAL DIRECTIVE

**MANDATORY RULE**: This sequence is locked. AEG must NOT begin until KGE and HKE
are complete or formally waived.

### Phase 1 — NEXT PRIORITY
**FTD-KGE-001: Knowledge Graph Expansion Program**
- Expand entity coverage: Decision, Roadmap, Governance, Risk, Research, Strategy,
  Incident, Verifier, FTD, Developer Report, Implementation Report
- All entities become first-class graph nodes with relationships
- Improves institutional relationship intelligence across all layers

### Phase 2 — AFTER KGE
**FTD-HKE-001: Historical Knowledge Extraction Program**
- Automated extraction from: FTD archives, AnswerFTDs, developer reports,
  implementation reports, verifier reports, CLAUDE.md, git history
- Target: 11 hardcoded decisions → 100+ → 500+ institutional facts
- Without this, AEG advisory quality will be fragile (small evidence base)

### Phase 3 — AFTER HKE (BLOCKED UNTIL THEN)
**FTD-AEG-001: Autonomous Engineering Governance**
- AEG-C1: Evidence Accumulator — pattern detection across IMRAF
- AEG-C2: Precondition Engine — conditions check before actions
- AEG-C3: Advisory Generator — confidence-weighted recommendations
- **BLOCKED**: Do not implement until KGE + HKE formally complete

### Rationale — Architecture Build Order
```
Memory → Intelligence → Context → Governance
→ Knowledge Expansion (KGE)
→ Historical Extraction (HKE)
→ Advisory Intelligence (AEG)
```
Advisory layer quality is bounded by evidence base size.
AEG recommendations built on 11 facts will be fragile.
AEG recommendations built on 500+ facts will be institutional-grade.

### Future AI Session Briefing
Any future session should be able to answer:
> "What is the next approved roadmap step?"

**Expected answer**: FTD-KGE-001 (Knowledge Graph Expansion) → FTD-HKE-001
(Historical Extraction) → FTD-AEG-001 (Autonomous Engineering Governance).
This is stored in IMRAF (records 95–99) and enforced by this directive.

---

## TRUTH ENGINE ROADMAP — Chain-B Institutional Directive

**MANDATORY RULE**: ETE_GATE_ENABLED and XTE_FORCE_CLOSE_ENABLED must NOT be set
True without completing Phase-2 Truth Calibration first.

### Current State (v1.57.0)
- **ETE**: Phase-1 Observation Mode — gate DISABLED (`ETE_GATE_ENABLED=False`)
- **XTE**: Advisory Mode — force-close DISABLED (`XTE_FORCE_CLOSE_ENABLED=False`)
- **AAP**: Observation Mode — attribution tracking active, not influencing allocation

### Why ETE gate is disabled
ETE requires a minimum of 500+ trades to calibrate `ETE_MIN_SCORE`. Activating
without calibration risks blocking valid entries on an uncalibrated threshold.

### Activation Sequence (Phase-1 → Phase-4)

| Phase | Name | Gate Condition | Status |
|-------|------|---------------|--------|
| 1 | Observation Mode | None — always active | ✅ ACTIVE |
| 2 | Truth Calibration | 500+ trades collected | ✅ DATA COMPLETE (530 samples, 2026-06-12) — **verdict: NO viable ETE_MIN_SCORE** |
| 3 | ETE Entry Governance | Phase-2 complete + ETE_MIN_SCORE set | ⛔ BLOCKED — composite score has no expectancy power (see Phase-2 result) |
| 4 | XTE Autonomous Exit | Phase-3 stable for 200+ live trades | ⏳ PENDING |

### Phase-2 Calibration Result (v1.88.0, 530 archived ETE samples)

The composite-score threshold sweep (diagnose.py §17) found **no threshold with
positive expectancy** — every T from 0–80 keeps expectancy ≈ −$0.07/trade
(T=60 is *worse*: −$0.086). Win rate IS monotonic with score (18.8% in the
40–50 decile → 47.4% at 60–70), so the score predicts win *probability* but
not dollars — high-score trades scratch at BE while losses run full size.

**Conclusion**: do NOT set `ETE_GATE_ENABLED=True` on the current score.

### Phase-2 Component Split Result (v1.88.0, 535 samples) — reweighting path CLOSED

The per-component expectancy split (`/api/truth/component-calibration`,
diagnose.py §17) showed **no component carries gating power** — expectancy is
negative on both sides of the 40-score split for every component:

- `structure` is **INVERTED**: the ≥40 cohort does *worse* (WR 32.9%,
  −$0.071) than the <40 cohort (WR 41.6%, −$0.069). 86% of trades score <40
  (avg 21.4) — its "top alpha destroyer" rank was a base-rate artifact.
- `regime` is **constant**: all 535 trades score ≥40 — zero discrimination.
- `cost` <40 has WR 4.8% (2/42 wins) but small losses — a near-certain-loss
  flag without expectancy impact.

**Institutional verdict**: entry-score reweighting cannot produce a viable
ETE gate; the truth signal is NOT in the entry components. The expectancy
lever is the EXIT side + fees: gross expectancy is only −$0.02/trade while
fees add −$0.026, and 46.5% of exits are BE scratches with peak_r ≈ 0.4–0.7
given back. Chain-B work is redirected to exit-policy truth (giveback
analysis in diagnose.py §3 since v1.88.1; XTE advisory data is the eventual
Phase-4 vehicle). Any future ETE gate requires redesigned component features,
not reweighted ones.

### Future AI Session Briefing
Any future session must be able to answer:

> "Why is ETE not blocking entries yet?"

**Expected answer**: ETE is in Phase-1 Observation Mode. `ETE_GATE_ENABLED=False`
because Truth Score calibration requires 500+ trades minimum. See IMRAF records
105–109 for full activation roadmap.

> "What must happen before ETE/XTE activation?"

**Expected answer**: Phase-2 — collect 500+ trades, run calibration analysis,
determine `ETE_MIN_SCORE`. Then Phase-3 — set `ETE_GATE_ENABLED=True`. Then
Phase-4 — set `XTE_FORCE_CLOSE_ENABLED=True` after Phase-3 stable.

### Both Chains Are Independent

```
Chain-A (Institutional Memory):    Chain-B (Truth Engine):
FTD-KGE-001                        ETE Phase-2 Calibration
    ↓                                   ↓
FTD-HKE-001                        ETE Phase-3 Gate Live
    ↓                                   ↓
FTD-AEG-001                        XTE Phase-4 Autonomous Exit
```

Neither chain blocks the other. Both are approved and pending.
