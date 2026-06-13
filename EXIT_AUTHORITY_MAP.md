# 🗺️ EXIT_AUTHORITY_MAP — FTD-094A Phase 1

**Status:** Forensic map — descriptive, no code change
**Engine build:** APP_VERSION 1.92.0
**Scope:** every component capable of modifying a live position's stop-loss,
take-profit, breakeven, trailing stop, or forcing/extending/reducing an exit.

---

## 0. SUMMARY

Exit control today is **executed by one component but authored by several.**
`RiskController` is the *sole executor* — it is the only thing that calls
`_close_position()` and the only loop that enforces SL/TP at price. But the
*decisions* about where the stop sits and when to leave are authored by **two
independent systems** writing the same `OpenPosition.stop_loss` field with no
shared state:

1. `RiskController.on_price_update` — autonomous trailing / BE / giveback-ratchet
   / speed-exit logic.
2. `TradeManager.update` — returns advisory actions that **main.py glue** applies
   to the live position (MOVE_BE / TRAIL_SL / EXTEND_TP / VTP_EXIT / TIME_EXIT /
   FAST_FAIL).

They are reconciled only by **ad-hoc "tighten-only" guards** in the glue
(FTD-SL-GUARD, main.py:971–972, 977–978). `TradeManager` additionally keeps its
**own** `ManagedPosition.stop_loss/take_profit` copy (trade_manager.py:277) that
can diverge from the live `RiskController` copy — the documented hazard.

---

## 1. AUTHORITY INVENTORY

| # | Authority | File · entry point | Powers | Activation condition | Priority |
|---|---|---|---|---|---|
| A1 | **SL/TP hard enforcement** | `risk_controller.py:_close_position` (459); driven by `on_price_update` (~306–456) | force close at SL/TP | price crosses SL or TP | **Executor — terminal** |
| A2 | **ATR trailing stop** | `risk_controller.py:378` (LONG) / `:421` (SHORT) | raise/lower `pos.stop_loss` | `trailing_sl` & new peak; trail = 1.5× initial SL dist | tighten-only |
| A3 | **Breakeven arming** | `risk_controller.py:393` / `:432` | move `pos.stop_loss` to BE+lock | `peak_r ≥ BREAKEVEN_TRIGGER_R` (0.40) | tighten-only |
| A4 | **Giveback ratchet** | `risk_controller.py:404` / `:442` | ratchet `pos.stop_loss` up | `GIVEBACK_RATCHET_ENABLED` & `peak_r ≥ 0.50R` | tighten-only |
| A5 | **Speed-exit (velocity stall)** | `risk_controller.py:406` / `:444` → `_close_position("SPEED")` | force close | `peak_r ≥ SPEED_EXIT_TRIGGER_R` (2.0) & stalled ≥ 25 ticks | terminal |
| A6 | **Partial close** | `risk_controller.py:partial_close` (508) | realize 50%, keep remainder | invoked by glue on `PARTIAL_TP` | terminal (partial) |
| A7 | **Force / emergency close** | `risk_controller.py:force_close` (556), emergency (619) | force close | risk event / EMERGENCY watch | terminal |
| A8 | **TM — MOVE_BE** | `trade_manager.update` → glue `main.py:973` | set live `pos.stop_loss` | TM BE logic | tighten-only (guarded) |
| A9 | **TM — TRAIL_SL** | glue `main.py:979` | set live `pos.stop_loss` | TM trail logic | tighten-only (guarded) |
| A10 | **TM — EXTEND_TP (VTP)** | `trade_manager.py:277` (own copy) + glue `main.py:985` | raise/lower live `pos.take_profit` | `r_velocity ≥ accel`, once per trade | **widen (NOT guarded)** |
| A11 | **TM — VTP_EXIT** | glue `main.py:992` | `pos.stop_loss = price` → close next tick | velocity stall after partial | terminal |
| A12 | **TM — TIME_EXIT / FAST_FAIL** | glue `main.py:1052` | `pos.stop_loss = price` → close next tick | stale (>8 min, r<0.15R) / fast reversal | terminal |

---

## 2. ACTIVATION ORDER PER TICK (observed in `on_tick`)

```
on_tick(sym, price)
  │
  ├─ TradeManager.update(sym, price, atr)         (main.py:956)   → ManagementAction
  │     └─ glue applies: MOVE_BE/TRAIL_SL/EXTEND_TP/VTP_EXIT/TIME_EXIT/FAST_FAIL
  │        (A8–A12) to the LIVE position, tighten-only guards on SL writes
  │
  ├─ [FTD-094A] xte_observer.observe(...)          (main.py ~1061) OBSERVE-ONLY, no writes
  │
  └─ … entry pipeline (skipped while position open, main.py:1217) …

separately, on every price update:
  RiskController.on_price_update(sym, price)
     └─ A2/A3/A4 adjust pos.stop_loss (tighten-only), A5 speed-exit,
        A1 enforces SL/TP → _close_position (terminal)
```

**Conflict resolution that actually exists:** for SL, "tightest wins" — both A2–A4
(RiskController) and A8–A9 (TM glue) only ever move the stop in the protective
direction, and the glue guards explicitly compare against the *live* `pos.stop_loss`
before writing. For TP, **A10 (EXTEND_TP) is the lone widening writer and is NOT
guarded** — it can push TP out once per trade; no symmetric tightening exists.

---

## 3. CONFLICT / HAZARD REGISTER

| ID | Hazard | Evidence | Current mitigation |
|----|--------|----------|--------------------|
| H-1 | **Dual SL writers, no shared state** | RiskController (A2–A4) and TM-glue (A8–A9) both write `pos.stop_loss` | tighten-only guards (main.py:971–978) — *convention, not invariant* |
| H-2 | **TM internal copy diverges from live** | `trade_manager.py:277` mutates TM's own `pos.take_profit`; live copy updated only via returned action | FTD-SL-GUARD comment; relies on glue to propagate |
| H-3 | **EXTEND_TP unguarded widening** | `main.py:985` sets live TP with no floor/ceiling check vs RiskController | none explicit (once-per-trade flag only) |
| H-4 | **Terminal close via SL=price is implicit** | A11/A12 set `pos.stop_loss = price` and rely on RiskController firing next tick | works because A1 is sole executor; couples two modules by timing |
| H-5 | **No single audit of "who moved the stop"** | writes scattered across 3 files | partial via thought-log lines |

---

## 4. PHASE 3 — SEAM CORRECTNESS (why the open-position seam, not close)

**Chosen seam:** the open-position management region of `on_tick`
(after `TradeManager.update`, main.py ~1061), guarded by `XTE_OBSERVE_ENABLED`.

**Why correct:**
- XTE (`exit_truth_engine.evaluate`) scores **live open-position state** — it
  requires `closes[]`, `volumes[]`, `atr_pct`, `atr_ema`, `current_r`, `peak_r`,
  `side`. All exist *while the position is open*: `peak_r` on the `OpenPosition`,
  `current_r` derivable from entry/initial_stop_loss/price, candle buffers from
  `mdp.candle_*_buffer(sym)`, `atr_ema` from `reactive_evolution_engine._atr_ema`.
- The seam runs once per tick per open symbol — the exact cadence XTE was designed
  for ("scores open position state, outputs advisory hints", exit_truth_engine.py:3).
- It sits **after** all real exit writers (A8–A12) and **only reads**, so the
  observed score can be compared against what the live authorities actually did.

**Why close-time (the QFTD-093 main.py:901 suggestion) is incorrect:**
- At close there is **no open position** and **no live time-series** — `closes[]`/
  `volumes[]`/`current_r` describe a position that no longer exists. The XTE inputs
  are undefined.
- The `exit_truth_score=0.0` field at main.py:901 is an **AAP attribution field**,
  a post-hoc record slot — not an evaluation seam. Writing a "live" score there
  is semantically meaningless.
- Confirmed by CNFTD-094 §2/§3.

---

## 5. VISUAL AUTHORITY CHAIN

```
                         ┌──────────────────────────────────────────┐
                         │              on_tick(sym, price)          │
                         └──────────────────────────────────────────┘
                                            │
                ┌───────────────────────────┴───────────────────────┐
                ▼                                                     ▼
   ┌──────────────────────────┐                        ┌──────────────────────────┐
   │  TradeManager.update()    │  ManagementAction      │  [FTD-094A] xte_observer  │
   │  (authoring source #2)    │ ─────────────────►     │  .observe()  OBSERVE-ONLY │
   │  MOVE_BE/TRAIL_SL/        │      main.py glue      │  (no authority — reads)   │
   │  EXTEND_TP/VTP/TIME/FAST  │   (tighten-only SL)    └──────────────────────────┘
   └──────────────────────────┘            │
        │ own copy (TM)                     ▼  writes live pos.stop_loss / take_profit
        │ trade_manager.py:277      ┌──────────────────────────────┐
        └──── diverges (H-2) ─────► │       OpenPosition (live)     │ ◄────┐
                                    │   stop_loss / take_profit     │      │
                                    └──────────────────────────────┘      │
                                                  ▲                        │
                                                  │ writes (tighten-only)  │
                         ┌────────────────────────┴───────────────────────┘
                         │  RiskController.on_price_update  (authoring source #1)
                         │   A2 trailing · A3 breakeven · A4 giveback-ratchet · A5 speed-exit
                         │
                         ▼
                 ┌───────────────────────────────┐
                 │  RiskController._close_position │  ◄── SOLE EXECUTOR (A1/A5/A6/A7)
                 │   (terminal — books TradeRecord)│      force_close / emergency / partial
                 └───────────────────────────────┘
```

**Read:** two authoring sources, one executor, no unified arbiter. XTE observation
attaches as a pure read at the seam and changes none of the above.

---

*End of EXIT_AUTHORITY_MAP. See UNIFIED_EXIT_AUTHORITY_BLUEPRINT.md for the
recommended consolidation, and FTD-094A_XTE_OBSERVATION_PROGRAM.md for the
observation activation, telemetry, and dataset plan.*
