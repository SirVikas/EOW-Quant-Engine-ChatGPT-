# EOW Quant Engine — System State Snapshot (SSS)
**Generated**: 2026-05-01  
**Branch**: `claude/fix-globalgate-reference-yKaYF`  
**Resume Keyword**: `SSS-RESUME-EOW-v3`

---

## 🎯 Original Problem (Why This Session Started)

System was generating **105 signals per cycle** but executing **0 trades**.

**Root causes found and fixed:**
1. `BYPASS_ALL_GATES = False` → 38 sequential quality gates blocked all trades
2. EV bootstrap catch-22: no trades → no EV data → TradeRanker blocked → no trades (infinite loop)
3. Sub-tick SL distances: `MIN_ATR_PCT = 0.015%` too low → SL only 0.04% away → instantly stopped out
4. `TradeManager` hardcoded `self.be_r = 1.0` ignoring `cfg.BREAKEVEN_TRIGGER_R = 1.80` → winners killed too early
5. `MAX_TRADES_PER_HOUR = 6` was a hard cap preventing trades even when gates bypassed

---

## ✅ All Changes Made (Committed & Pushed)

### Batch 1 — EV Bootstrap Fix (PR #117, merged to main)
- `core/adaptive_edge_engine.py`: State machine deadlock fixed — no longer stays in BOOTING forever
- `core/ev_confidence_engine.py`: Bootstrap threshold reduced so EV engine activates with fewer trades

### Batch 2 — TradeRanker Bootstrap Fix (PR #118, merged to main)
- `core/trade_ranker.py`: `TR_MIN_RANK_SCORE` lowered `0.60 → 0.30` (bootstrap: max score without EV = 0.45, now passes)
- `core/adaptive_scorer.py`: Bootstrap deadlock resolved

### Batch 3 — SL Distance + BE Trigger Fix (PR #119, merged to main)
- `strategies/strategy_modules.py`: `MIN_ATR_PCT = 0.015 → 0.05` (SL now minimum 0.125% from entry)
- `strategies/alpha_engine.py`: Added `if atr / price * 100 < MIN_ATR_PCT: return None` to all 3 generators (TCB, PBE, VSE)
- `core/trade_manager.py`: `self.be_r = 1.0 → cfg.BREAKEVEN_TRIGGER_R` (was hardcoded, now reads 1.80)

### Batch 4 — LeanGate + BYPASS_ALL_GATES (current branch, pushed, PR #120 open)
- **`core/lean_gate.py`** (NEW FILE): 5-gate stateless safety checker — zero bootstrap dependency
  - Gate 1: SL distance ≥ 0.05% of entry
  - Gate 2: RR ratio ≥ 1.5
  - Gate 3: Round-trip fees < 25% of expected TP profit
  - Gate 4: Consecutive session losses < 6
  - Gate 5: Session drawdown < 12%
- **`config.py`**: `BYPASS_ALL_GATES: False → True`
- **`config.py`**: `MAX_TRADES_PER_HOUR: 6 → 1200` (paper-speed, from main merge)
- **`config.py`**: `MAX_TRADES_PER_DAY: 40 → 28800` (paper-speed, from main merge)
- **`main.py`**: `lean_gate` imported and wired unconditionally after `notional` is computed (~line 809), before old quality gates. Every lean gate skip is recorded to `trade_flow_monitor`.

---

## 📁 Critical File Map

| File | Role | State |
|---|---|---|
| `config.py` | All thresholds & flags | ✅ Modified (BYPASS=True, speed limits) |
| `core/lean_gate.py` | NEW: 5-gate safety check | ✅ Created & wired |
| `main.py` | Main trading loop + lean_gate wiring | ✅ Modified |
| `strategies/strategy_modules.py` | Signal generators (TF/MR/VE) | ✅ MIN_ATR_PCT=0.05 |
| `strategies/alpha_engine.py` | Alpha signal generators (TCB/PBE/VSE) | ✅ ATR guard added |
| `core/trade_manager.py` | BE/trail/partial TP lifecycle | ✅ be_r uses cfg |
| `core/trade_ranker.py` | Signal ranking (EV-weighted) | ✅ threshold=0.30 |
| `core/gating/global_gate_controller.py` | PRODUCTION gate (used by orchestrator) | ✅ No change needed |
| `core/global_gate.py` | LEGACY gate (NOT used by orchestrator) | ⚠️ Legacy — ignore |
| `core/genome_engine.py` | Genetic evolution every 50 trades | ✅ Working |
| `core/adaptive_edge_engine.py` | Per-strategy live perf tracker | ✅ Fixed batch1 |
| `core/candle_bootstrap.py` | Fetches 120 historical candles at boot | ✅ No change |
| `core/orchestrator/execution_orchestrator.py` | 6-stage pipeline | ✅ BYPASS=True skips all |

---

## ⚙️ Current Config Values (Key Parameters)

```python
INITIAL_CAPITAL        = 1000.0       # USDT (actual equity ~849 USDT)
MAX_RISK_PER_TRADE     = 0.022        # 2.2% per trade
KELLY_FRACTION         = 0.25         # quarter-Kelly sizing
MAX_LEVERAGE_CAP       = 3.0          # hard cap
TAKER_FEE              = 0.0004       # 0.04%

ATR_MULT_SL            = 2.5          # SL = entry ± 2.5×ATR
ATR_MULT_TP            = 10.0         # TP = entry ± 10×ATR → RR=4.0×
MIN_RR_RATIO           = 2.0          # quality gate (raw RR=4.0 clears easily)

BREAKEVEN_TRIGGER_R    = 1.80         # move SL to BE after 1.80R profit
SPEED_EXIT_TRIGGER_R   = 2.50         # exit on stall after 2.5R captured
PARTIAL_TP_R           = 3.0          # book 50% at 3.0R

BYPASS_ALL_GATES       = True         # ← KEY FIX: bypasses 38 inline gates
TR_MIN_RANK_SCORE      = 0.30         # ← was 0.60, lowered for bootstrap
MAX_TRADES_PER_HOUR    = 1200         # paper-speed mode
MAX_TRADES_PER_DAY     = 28800        # paper-speed mode

# LeanGate thresholds (in core/lean_gate.py)
MIN_SL_DIST_PCT        = 0.05         # SL must be ≥ 0.05% from entry
MIN_RR (lean)          = 1.5          # lean gate RR check
MAX_FEE_RATIO          = 0.25         # fees < 25% of TP profit
MAX_CONSEC_LOSSES      = 6            # pause after 6 consecutive losses
MAX_DAILY_DD_PCT       = 12.0         # hard stop at 12% session drawdown

# Strategy signal filters
MIN_ATR_PCT            = 0.05         # ← was 0.015, raised (strategy_modules.py)
```

---

## 🔄 Self-Evolving System — Status

| Component | What it does | Status |
|---|---|---|
| **GenomeEngine** | Mutates EMA/RSI/ATR DNA, backtests, promotes winner every 50 trades | ✅ Active — was starved (0 trades), now will get data |
| **RegimeDetector** | Switches TrendFollowing/MeanReversion/VolatilityExpansion per market regime | ✅ Working |
| **AdaptiveEdgeEngine** | Adjusts position size per strategy based on live win rate / PF | ✅ Fixed (batch1) |
| **AdaptiveScorer** | Confidence scoring adapts to outcomes | ✅ Fixed (batch2) |
| **EV Engine** | Expected value per strategy (needs 10+ trades) | ✅ Bootstrap fixed |
| **TradeRanker** | Ranks signals: EV(55%) + score(20%) + regime(15%) + hist(10%) | ✅ Threshold=0.30 |

---

## 📊 Last Known Performance (Before Fixes)

From `reports_for_analyzation/2026_04_27_13_46_31_994779/report_1D.json`:
```
Trades:         110
Win rate:       41.82%
Net PnL:        -13.65 USDT
Profit Factor:  0.616        ← losing (< 1.0)
Avg win:        +0.26 USDT
Avg loss:       -0.40 USDT
Fee drag:       35.19%       ← major problem (sub-tick SLs caused tiny trades)
```

**Root cause of losses**: `MIN_ATR_PCT=0.015%` → SL only 0.04% away → closed immediately on noise. Fixed in batch3.

---

## ⏱️ First Trade Time Estimate (After Fixes)

```
App start → System Ready:     ~30-60 seconds
  (CandleBootstrapper pre-loads 120 historical candles for ALL symbols)

System Ready → First Signal:  0 to 30 minutes
  (depends on market — EMA crossover, BB touch, or breakout needed)

Total realistic:              2-15 minutes in active market sessions
```

---

## 🔁 Git State

```
Branch:   claude/fix-globalgate-reference-yKaYF
Remote:   origin/claude/fix-globalgate-reference-yKaYF  ← PUSHED ✅
PR #120:  Open — "Replace 38-gate pipeline with LeanGate + BYPASS_ALL_GATES=True"
          Status: Conflict resolved (config.py merge done), ready to merge
```

---

## ❌ What Was NOT Done (Pending / Optional)

1. **Execution Orchestrator rebuild** — `core/orchestrator/execution_orchestrator.py` could be simplified to a direct-execute path (BYPASS_ALL_GATES already handles this effectively, so lower priority)
2. **Live trade verification** — No actual session run after the fixes; need to start app and confirm trades flow in logs
3. **Performance tuning post-fix** — Once trades start, monitor win rate and avg R. If PF < 1.0 persists, review ATR_MULT settings or MIN_ATR_PCT
4. **10 USDT/minute target** — Mathematically impossible on ~849 USDT capital (would require 1697% daily return). Realistic: 0.5–3% per day = 4–25 USDT/day

---

## 🚀 Resume Prompt for New Chat

Copy-paste this EXACTLY to start a new chat:

```
SSS-RESUME-EOW-v3

Context: EOW Quant Engine (FastAPI, Binance Futures paper trading, Python).
Read SYSTEM_STATE_SNAPSHOT.md in the project root for full context.

Current branch: claude/fix-globalgate-reference-yKaYF
PR #120 is open and conflict-resolved.

Summary of what's done:
- BYPASS_ALL_GATES=True in config.py (unblocks 38-gate pipeline deadlock)
- core/lean_gate.py (NEW): 5 stateless safety gates, wired into main.py at line ~809
- MIN_ATR_PCT raised 0.015→0.05 in strategy_modules.py (fixes sub-tick SL problem)
- alpha_engine.py: ATR% guard added to all 3 generators
- trade_manager.py: be_r now reads cfg.BREAKEVEN_TRIGGER_R (was hardcoded 1.0)
- TR_MIN_RANK_SCORE lowered 0.60→0.30 (bootstrap deadlock fix)
- MAX_TRADES_PER_HOUR=1200, MAX_TRADES_PER_DAY=28800 (paper-speed)

Next task: [DESCRIBE WHAT YOU WANT TO DO NEXT]
```

---

*SSS generated at session end. All committed changes are on branch `claude/fix-globalgate-reference-yKaYF` and pushed to remote.*
