# EOW Quant Engine — Bug Blueprint (Forensic Analysis)
# Date: 2026-05-01
# Branch: claude/fix-trade-issue-OUQLG

## ROOT CAUSE SUMMARY
Pipeline Break Forensics shows: 100/100 cycles blocked with reason `INDICATOR_NOT_READY | DATA_NOT_FRESH`
- `_ws_score: 100.0` (WS connected and healthy)
- `_deploy_score: 45.0` (exactly at GGL_DEPLOY_MIN_SCORE threshold)
- `_ind_ready: False` (indicators not ready)
- `_data_fresh: False` (data health blocked because indicators not ready)
- Safe mode is SAFE, can_trade=False

---

## BUG #1 — CRITICAL (PRIMARY TRADE BLOCKER)
### SMC_MIN_SCORE_RESUME (47.0) > BDE_MIN_SCORE / max warmup deploy score (45.0)
**File**: `config.py` line 332
**Problem**:
- Max achievable deploy score during warmup (no indicators, WS healthy):
  `ws×0.25 + risk×0.20 = 100×0.25 + 100×0.20 = 45.0`
- BDE_MIN_SCORE = 45.0 → gate OPENS at 45.0 (deploy_ok = True)
- SMC_MIN_SCORE_RESUME = 47.0 → safe mode CANNOT auto-recover via score (45 < 47)
- When gate is blocked AND score is 45.0, safe mode is permanently stuck:
  - Score-based recovery: 45.0 < 47.0 → FAILS
  - can_trade=True recovery: gate never passes → NEVER called
- RESULT: PERMANENT DEADLOCK — safe mode never exits during warmup
**Fix**: Lower SMC_MIN_SCORE_RESUME from 47.0 to 44.0 (below warmup max of 45.0)

---

## BUG #2 — CRITICAL (DASHBOARD BLIND)
### Missing `snapshot()` method on GlobalGateController
**File**: `core/gating/global_gate_controller.py`
**Problem**:
- `main.py` calls `global_gate_controller.snapshot()` in 6+ places
- The class only defines `summary()`, NOT `snapshot()`
- `_safe_v2` wrapper catches AttributeError → returns `{}` (empty dict)
- Result: Gate status panel in dashboard is ALWAYS EMPTY
- Operators have zero visibility into gate state — impossible to debug
**Fix**: Add `def snapshot(self) -> dict:` as alias for `summary()`

---

## BUG #3 — HIGH (INDICATOR WARMUP INCONSISTENCY)
### IV_RSI_MIN_CANDLES=15 vs IV_MIN_CANDLES=14 mismatch
**File**: `config.py` lines 307-308
**Problem**:
- `validate_symbol_buffers()` passes `n = len(candle_close_buf)` for ALL counts including RSI
- At exactly n=14: `candle_count(14>=14)` PASS but `rsi_warmup(14>=15)` FAIL
- `iv_result.ok = False` at n=14 — the configured system minimum
- BOOTING→LIVE via `iv_result.ok` requires n>=15, but config says min=14
- `_ind_ok_coarse = n >= 14` gives false sense of readiness at n=14
- RSI period=14 mathematically requires 15 candles (period + 1)
**Fix**: Set IV_MIN_CANDLES = 15 to match true RSI warmup requirement
         (all other periods also work at 14+1=15 candles)

---

## BUG #4 — HIGH (WRONG BUFFER FOR CANDLE COUNT)
### `indicator_guard.validate()` receives tick buffer length, not candle count
**File**: `main.py` line 518
**Problem**:
  ```python
  buf = list(mdp.price_buffer(sym))           # ← TICK prices (many per second)
  ...
  guard = indicator_guard.validate(
      symbol=sym, n_candles=len(buf), ...      # ← wrong: tick count, not candle count
  )
  ```
- `indicator_guard` expects n_candles = number of closed 1-min candles
- Gets tick count (can be 1000s) instead
- `MIN_CANDLES=30` check in indicator_guard is satisfied by ticks, not actual candles
- "INSUFFICIENT_CANDLES" protection in indicator_guard is effectively disabled
**Fix**: Change to `n_candles=_n_candles` (already computed: `len(mdp.candle_close_buffer(sym))`)

---

## BUG #5 — MEDIUM (RECOVERY THROTTLE INTERFERENCE)
### BOOTING grace calls to check_recovery() poison the throttle timer
**File**: `core/gating/global_gate_controller.py` line 159
**Problem**:
- During BOOTING, `self._sme.check_recovery(deploy_score=100.0, can_trade=True)` called on EVERY evaluate()
- `check_recovery()` sets `_last_resume_check = now` each call
- After BOOTING→LIVE: if safe mode activates and gate IMMEDIATELY passes on next tick,
  recovery is THROTTLED by SMC_RESUME_AFTER_MIN (5 min) because `_last_resume_check` was just set
- This delays post-warmup trading by up to 5 minutes unnecessarily
**Fix**: In `check_recovery()`, skip throttle when `can_trade=True` (immediate recovery path)
         OR reset `_last_resume_check = 0.0` in `activate()` so next recovery is unthrottled

---

## BUG #6 — MEDIUM (DUPLICATE SAFE MODE ACTIVATION)
### Safe mode activated twice on gate failure (double logging)
**Files**: 
- `core/gating/global_gate_controller.py` line 206: `self._sme.activate(reason)`
- `core/orchestrator/execution_orchestrator.py` gate_check(): also calls `self._sme.activate(reason)`
**Problem**:
- Both share the same `safe_mode_engine` singleton
- Every gate failure activates safe mode twice: once in evaluate(), once in gate_check()
- Results in duplicate `[SAFE-MODE-ENGINE] SAFE MODE ACTIVATED` log entries
- History buffer fills up with duplicate events
**Fix**: Remove the redundant activation from orchestrator gate_check()
         (GlobalGateController is the authoritative activator)

---

## BUG #7 — LOW (STALE COMMENT)
### HSV_MIN_CANDLES_BOOT comment says "aligned with IV_MIN_CANDLES" but 20 ≠ 14
**File**: `config.py` line 344
**Problem**:
- `HSV_MIN_CANDLES_BOOT: int = 20  # FTD-REF-055: 30→20 — aligned with IV_MIN_CANDLES`
- IV_MIN_CANDLES was reduced to 14 but HSV_MIN_CANDLES_BOOT is still 20
- Comment is misleading — they are NOT aligned
**Fix**: Update comment to reflect actual value and rationale

---

## FIX ORDER (by criticality):
1. Bug #1 — config.py: SMC_MIN_SCORE_RESUME 47.0 → 44.0
2. Bug #2 — core/gating/global_gate_controller.py: add snapshot() method
3. Bug #3 — config.py: IV_MIN_CANDLES 14 → 15
4. Bug #4 — main.py: indicator_guard n_candles uses tick buffer → use candle buffer
5. Bug #5 — core/gating/safe_mode_engine.py: reset _last_resume_check on activate()
6. Bug #6 — core/orchestrator/execution_orchestrator.py: remove duplicate safe mode activation
7. Bug #7 — config.py: fix stale comment

---

## STATUS TRACKING:
- [x] Bug #1 Fixed — config.py: SMC_MIN_SCORE_RESUME 47.0 → 44.0
- [x] Bug #2 Fixed — core/gating/global_gate_controller.py: added snapshot() method
- [x] Bug #3 Fixed — config.py: IV_MIN_CANDLES 14 → 15
- [x] Bug #4 Fixed — main.py line 518: n_candles=len(buf) → n_candles=_n_candles
- [x] Bug #5 Fixed — core/gating/safe_mode_engine.py: reset _last_resume_check=0 on activate()
- [x] Bug #6 Fixed — core/orchestrator/execution_orchestrator.py: removed duplicate sme.activate()
- [x] Bug #7 Fixed — config.py: updated HSV_MIN_CANDLES_BOOT stale comment
