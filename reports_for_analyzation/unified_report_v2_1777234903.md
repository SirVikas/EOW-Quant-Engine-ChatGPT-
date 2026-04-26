# EOW Quant Engine — Unified System Report v2

_Generated: 2026-04-26 20:21:43 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | HALTED |
| Trading Activity | IDLE (159 min — activator tier=TIER_3) |
| Profitability | LOSS (PF=0.38, net=$-151.08) |
| Key Problem | System idle 159 min — no signal passing quality threshold |
| Immediate Action | Check Alpha Engine output; tier=TIER_3 score_min=0.42 |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 0 |
| Signals Passed → Traded | 0 |
| Signals Rejected | 0 |
| Pass Rate | 0.0% |
| Reject Rate | 0.0% |
| Rejection Rate (window %) | 0.0% |
| Mins Since Last Trade | 159.5 |
| Signals / hour | 0.0 |
| Trades / hour | 0.00 |

_No rejection reasons recorded in current window._

## 3. Decision Intelligence

| Metric | Value |
|---|---|
| AI Decision | MONITOR |
| Mode | NORMAL |
| Tier | TIER_3 |
| Score Min | 0.420 |
| AF State | RELAX |

**WHY:**
- No signals generated — no market setups detected in current window
- No signals to execute — Alpha Engine found no qualifying patterns
- Missing condition: Strategy entry criteria must be met for signal generation
- Profit factor 0.38 < 1.0 — system in drawdown recovery posture
- Trade Activator TIER_3 — filters relaxed (score_min=0.420)
- Adaptive Filter RELAX — dry-spell triggered quality relaxation
- Idle 159 min — no qualifying setup across all pairs

**WHAT NEEDED:**
- Missing condition: Strategy entry criteria must be met for signal generation
- Next trigger: Strategy pattern match AND score ≥ 0.420 AND market regime compatible

**Alternative Action:**
Consider forcing Alpha Engine scan cycle or manual signal injection

## 4. Risk Engine Behavior

| Metric | Value |
|---|---|
| Risk State | HALTED — — |
| Size Reduced? | No |
| Trade Blocked? | No |
| Kill Switch? | Yes |
| Halt Reason | — |
| DD State | NORMAL |
| Current DD | 0.0% |
| Max DD (session) | 0.0% |
| Size Multiplier | 1.00× |
| Gate Reason | ALL_CLEAR |

## 5. Capital Efficiency

| Metric | Value |
|---|---|
| Current Equity | $1000.00 |
| Net PnL | $-151.08 |
| Fees Paid | $50.57 |
| Capital Deployed | 10.1% |
| Capital Idle | 89.9% |
| Daily Risk Used | $59.62 |
| Daily Risk Remaining | $0.00 |
| Daily Cap | 3.0% |
| Missed Opportunity | 159 min idle at TIER_3 (score_min=0.42, vol_mult=0.2×) — no signal cleared all quality gates |

## 6. Performance Reality

> **Note (FTD-025C):** Session trades = 0. Stats below are **HISTORICAL (lifetime)**, not current session.

| Metric | Value |
|---|---|
| Expectancy / Trade | $0.00 |
| Fee Impact | 25.1% |
| Fee per Trade (avg) | $50.57 |
| Win Rate | 45.7% |
| Avg Win | +$0.83 |
| Avg Loss | $-1.84 |
| Total Trades | 0 |
| Total Net PnL | $-151.08 |

**Edge Consistency (strategy × regime):**
- - MEAN_REVERTING@MR_BB_RSI_v1: edge=-0.403 wr=67% n=3 [NEGATIVE]
- - TRENDING@ALPHA_PBE_v1: edge=+0.081 wr=100% n=1 [POSITIVE]
- - TRENDING@ALPHA_TCB_v1: edge=-1.485 wr=25% n=4 [NEGATIVE]
- - TRENDING@ALPHA_VSE_v1: edge=-0.726 wr=0% n=1 [NEGATIVE]
- - TRENDING@TF_EMA_RSI_v1: edge=-0.141 wr=0% n=1 [NEGATIVE]

## 7. Learning Memory

| Metric | Value |
|---|---|
| Status | UNKNOWN |
| Memory Records | 0 |
| Total Patterns | 0 |
| Formed Patterns | 0 |
| Negative (Permanent) | 0 |
| Negative (Temporary) | 0 |

_No patterns formed yet — learning engine requires more trades. Pattern formation begins once per-strategy samples accumulate. No strategies are banned; all remain eligible._

## 8. Alert Intelligence

**HALT ACTIVE**
  Cause: Risk kill-switch triggered
  Impact: Zero new trades until manually cleared
  Fix: Resolve halt condition; call /api/risk/resume

**HIGH FEE DRAG (25% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $50.57 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**TRADE DRY-SPELL (159 min)**
  Cause: No signal clearing all quality gates
  Impact: Capital idle; Trade Activator relaxing filters
  Fix: Check Alpha Engine signal quality; inspect top rejection reasons

**SESSION/HISTORICAL METRICS MIXED**
  Cause: Session trades=0 but historical stats displayed without label
  Impact: Performance section shows lifetime stats, not current session
  Fix: Performance stats below are HISTORICAL (lifetime), not current session

**RECURRING ERROR: STRAT_001 (5 times)**
  Cause: Repeated indicator quality failure
  Impact: Affected symbols blocked from evaluation
  Fix: Check ATR/ADX thresholds for affected symbol

## 9. Root Cause Analysis

**PRIMARY CAUSE:**
**Risk kill-switch active** — system halted, zero execution possible. Halt reason: unknown.

**SECONDARY CAUSES:**
_No significant secondary causes identified._

## 10. Action Plan

**IMMEDIATE (restart not required):**
- Investigate top skip reasons — idle 159 min suggests systematic quality miss

**SHORT TERM (next session):**
- Review Alpha Engine TrendBreakout RR — single trade data suggests poor setup quality
- Add session PF circuit breaker: if session_pf < 0.5 after ≥20 trades → pause 30 min
- Raise MIN_NOTIONAL_USDT to reduce fee drag per trade

**LONG TERM (strategy evolution):**
- Strategy DNA overhaul via genome evolution (Volatility Expansion showing 0 usage)
- Implement regime stability filter: require regime stable ≥ 3 consecutive candles before entry
- Build per-symbol expectancy tracking — remove symbols with PF < 0.8 after 20+ trades

## 11. Developer Export

**Developer Summary**

- Issue:  UNKNOWN
- Cause:  N/A dominant block
- Capital Idle:  89.9%
- Fix:    Strategy pattern match AND score ≥ 0.420 AND market regime compatible

```
Generated:       2026-04-26 20:21:43 UTC
Trades (total):  0  |  PF: 0.379  |  WR: 45.7%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            TIER_3  score_min=0.42  vol_mult=0.2×
Idle:            159.5 min
Signals/hr:      0.0  Skips(window):   0
Top Errors:
  WS_001:gap=32.6s: 1×
  STRAT_001:adx=16.2 conf=0.12: 1×
  STRAT_001:adx=16.6 conf=0.12: 1×
  DATA_002:ADX_UNSTABLE(5.0<5.0): 1×
  STRAT_001:adx=19.2 conf=0.12: 1×
```

## 12. Execution Analysis (FTD-033)

| Metric | Value |
|---|---|
| Signals Evaluated | 0 |
| Executed | 0 |
| Rejected | 0 |
| Execution Rate | 0.0% |
| Dominant Block | N/A |
| Top Rejection Reason | N/A |

**Rejection Breakdown:**
- None recorded

**Gate Status:**
- No gate data

## 13. Cost Analysis (FTD-033)

| Metric | Value |
|---|---|
| Avg Cost per Trade | 0.0000% |
| Total Fees Paid | 0.0000 USDT |
| Cost Impact | N/A |
| High-Cost Symbols | None |
| Trades Evaluated | 0 |

## 14. Net Edge Summary (FTD-033)

| Metric | Value |
|---|---|
| Signals Evaluated | 0 |
| With Positive Net Edge | 0.0% |
| Rejected Due to Cost | 0.0% |
| Avg Alpha Score | 0.0000 |
| Blacklisted Patterns | None |

**Strategy Net Edge:**
- No data

## 15. Developer Summary (FTD-033)

**FTD-033 Developer Summary**

- Issue: No execution / low execution rate
- Cause: N/A dominates rejections
- Capital Idle: 89.9%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0