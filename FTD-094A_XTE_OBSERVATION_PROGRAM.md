# 🧾 FTD-094A — XTE OBSERVATION ACTIVATION & UNIFIED EXIT AUTHORITY PROGRAM

**Status:** IMPLEMENTED (observation-only, default-disabled) + architectural study
**Engine build:** APP_VERSION 1.91.3 → **1.92.0** (new subsystem + new endpoint → MINOR)
**Restriction posture:** evidence-generation only. No entry/signal/ETE/RL/gate/
sizing/SL/TP **behavior** change. The one runtime hook is inert while
`XTE_OBSERVE_ENABLED=False` (default).

This document is the program report for FTD-094A. Phase 1 → `EXIT_AUTHORITY_MAP.md`.
Phase 7 → `UNIFIED_EXIT_AUTHORITY_BLUEPRINT.md`. Phases 2–6 are below.

---

## PHASE 2 — XTE OBSERVATION ACTIVATION ✅

**Delivered:** `core/truth/xte_observer.py` (`XTEObserver`, singleton `xte_observer`).

- Wraps the existing, fully-built `exit_truth_engine` (CNFTD-094 proved it is
  dormant, not a stub) with **observation-only** plumbing.
- **No execution authority:** the class never writes `stop_loss`, `take_profit`,
  `qty`, never deregisters, never closes. The verifier asserts this (TEST 2).
- **Config (config.py):**
  - `XTE_OBSERVE_ENABLED: bool = False` — **default disabled, as mandated.**
  - `XTE_OBSERVE_ARCHIVE: str = "reports/xte_observations/xte_observations.jsonl"`.
- **Runtime hooks (main.py), both guarded by `if cfg.XTE_OBSERVE_ENABLED:` and
  exception-isolated (DOAE precedent):**
  - `observe(...)` at the open-position seam (~main.py:1061) — per-tick scoring.
  - `on_close(...)` in the close handler (~main.py:765) — one record per trade.
- When the flag is False the hooks cost a single boolean check; **trading behavior
  is byte-for-byte unchanged.**

---

## PHASE 3 — OPEN-POSITION SEAM (correctness report) ✅

Full rationale in `EXIT_AUTHORITY_MAP.md §4`. Summary:

- **Correct seam = open-position management tick.** XTE scores live position state
  and needs `closes/volumes/atr_pct/atr_ema/current_r/peak_r/side`, all available
  while the position is open (buffers from `mdp.candle_*_buffer(sym)`, `peak_r`
  from `OpenPosition`, `current_r` derived from entry/initial SL/price).
- **Close-time (QFTD-093's main.py:901) is wrong:** at close there is no open
  position and no live series; the `0.0` there is an AAP attribution slot, not an
  evaluation seam. Confirmed by CNFTD-094.

---

## PHASE 4 — TELEMETRY CAPTURE ✅

**Storage:** JSONL append at `cfg.XTE_OBSERVE_ARCHIVE`
(`reports/xte_observations/xte_observations.jsonl`), matching the house
`reports/<subsystem>/*.jsonl` convention (e.g. learning_memory, memory_store).
One record per closed managed position; per-tick scores are accumulated in memory
(a `_Trajectory`) and **summarized at close** — bounded storage, no per-tick rows.

**Record schema (per closed position):**

| Field | Meaning |
|---|---|
| `ts` | record write time (ms) |
| `symbol`, `regime` | context |
| `duration_s` | entry→exit seconds |
| `exit_r` | realized R-multiple |
| `peak_r` | max R seen (live + trajectory) |
| `giveback_pct` | `(peak_r − exit_r)/peak_r × 100` |
| `profit_capture` | `exit_r / peak_r` |
| `volatility_atr_pct` | ATR% at entry |
| `net_pnl`, `won` | realized outcome |
| `exit_method` | actual exit (TRAILING_STOP/BE/SPEED/…) |
| `xte_evals` | ticks XTE scored this position |
| `xte_score_last/avg/peak/min` | XTE trajectory stats |
| `xte_advisory_last` | last advisory label (HOLD/TIGHTEN/BREAKEVEN/SCALE_OUT) |
| `xte_advisory_transitions` | advisory changes during the hold |

This joins **what XTE said** (score/advisory trajectory) to **what actually
happened** (exit_r, giveback, outcome) — the core of the validation dataset.

---

## PHASE 5 — PHOENIX REPORTING INTEGRATION ✅

**Endpoint:** `GET /api/truth/xte/observation` (read-only), consistent with the
`/api/truth/*` family. Returns `{status, report}`.

**Report sections (`xte_observer.report_sections()`):**
1. **XTE Score Distribution** — histogram of avg score by 10-pt bucket.
2. **Advisory Distribution** — counts by last advisory label.
3. **Giveback Analysis** — avg giveback %, winners' giveback, avg profit-capture,
   BE-scratch rate.
4. **XTE vs Actual Exit Comparison** — per score-bucket avg `exit_r`, win-rate,
   avg giveback (does the live score track realized dollars?).

`status` (`xte_observer.summary()`) exposes `archive_samples`,
`calibration_progress_pct` (target 500), and `observe_enabled`.

---

## PHASE 6 — VALIDATION DATASET (specification + mechanism) ⏳

**Mechanism delivered; data accrual is an operational runtime step** (cannot be
generated in a static authoring session — it requires a live/paper engine run).

- **Dataset =** the JSONL archive from Phase 4 (one row per managed position with
  XTE trajectory + realized outcome) — exactly the fields the FTD lists (xte_score,
  actual exit outcome, giveback, profit capture, duration, regime).
- **Collection protocol:** set `XTE_OBSERVE_ENABLED=True` for a calibration phase;
  let ≥ 500 managed positions close; monitor progress via
  `GET /api/truth/xte/observation → status.calibration_progress_pct`.
- **Acceptance bar (per CNFTD-094):** advancement past observation requires ≥ 500
  samples **and** positive out-of-sample *expectancy* (not just win-rate) for any
  XTE-driven lever — and, per the blueprint, the Exit Coordinator (X3) must exist
  before XTE may *act*.

> Honest status: Phases 2–5 are code-complete and verified; Phase 6 is wired and
> ready but **0 samples** until an operator runs with the flag on. This FTD does
> not (and cannot) itself produce the 500-position dataset.

---

## MANDATORY VERIFIER ✅

`tests/verify_xte_observer.py` — **40/40 checks pass**. Confirms:
1. **XTE executes** — `observe()` returns a 0–100 score + advisory; `current_r`
   sign/zero-guard correct.
2. **Execution untouched** — `observe()` mutates no `stop_loss`/`take_profit`/`qty`;
   `XTE_OBSERVE_ENABLED` and `XTE_FORCE_CLOSE_ENABLED` default False.
3. **Archive works** — `on_close()` writes; read-back; giveback/duration computed
   correctly; trajectory joined.
4. **Reports generate** — all four sections present; empty-archive handled.

Run isolated against a temp archive — never touches the real `reports/` tree.
The mandated `tests/test_live_process_access.py` also still passes (59/59).

---

## SUCCESS CRITERIA — STATUS

| # | Criterion | Status |
|---|-----------|--------|
| 1 | XTE actively observing | ✅ capability shipped; **active when flag on** (default off, per mandate) |
| 2 | Trading behavior unchanged | ✅ inert while disabled; hooks guarded + exception-isolated; tests green |
| 3 | 500+ managed positions collected | ⏳ mechanism ready; requires operator runtime collection |
| 4 | Exit authority map completed | ✅ `EXIT_AUTHORITY_MAP.md` |
| 5 | Unified Exit Authority blueprint | ✅ `UNIFIED_EXIT_AUTHORITY_BLUEPRINT.md` |

Criteria 1, 2, 4, 5 complete; 3 is an operational follow-on (flip the flag, run).

---

## MANDATORY RESTRICTIONS — COMPLIANCE

No modification to entry logic, signal generation, ETE, RL, gates, sizing, or
SL/TP **behavior**. The only execution-path edits are two flag-guarded,
exception-isolated observation hooks that are no-ops by default, plus one
read-only API endpoint and one new observation-only module. Confirmed.

---

## VERSIONING

- **APP_VERSION 1.91.3 → 1.92.0** — new subsystem (`core/truth/xte_observer.py`)
  + new API endpoint (`/api/truth/xte/observation`) → **MINOR** per CLAUDE.md.
- **IMRAF (on approval):** record FTD-094A under `decisions`/`roadmap` — *"XTE
  observation activated (flag-off); exit authority mapped (2 authors / 1 executor,
  hazards H-1…H-5); Unified Exit Coordinator is the recommended next structural
  step (X1→X2→X3); XTE may not act before the coordinator exists and Phase-6
  calibration passes."*

---

*End of FTD-094A program report.*
