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
- **Mode**: Paper trading + RL (BYPASS_ALL_GATES=True by default)
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

