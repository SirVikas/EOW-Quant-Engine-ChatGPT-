# EOW Quant Engine — Unified System Report v2

_Generated: 2026-05-27 02:17:55 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | IDLE (65 min — activator tier=TIER_3) |
| Profitability | LOSS (PF=0.41, net=$-232.63) |
| Key Problem | All signals blocked by ECO_TOXIC — no execution despite active signal flow |
| Immediate Action | Investigate ECO_TOXIC condition; check threshold and tier configuration |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 0 |
| Signals Passed → Traded | 0 |
| Signals Rejected | 0 |
| Pass Rate | 0.0% |
| Reject Rate | 0.0% |
| Rejection Rate (window %) | 0.0% |
| Mins Since Last Trade | 64.9 |
| Signals / hour | 0.0 |
| Trades / hour | 0.00 |
| Dominant Block | ECO_TOXIC (6 rejection(s)) |

**Top Rejection Reasons:**
- ECO_TOXIC: 6 (75%)
- RR_LOW: 1 (12%)
- SL_TOO_TIGHT: 1 (12%)

## 3. Decision Intelligence

| Metric | Value |
|---|---|
| AI Decision | MONITOR |
| Mode | NORMAL |
| Tier | TIER_3 |
| Score Min | 0.400 |
| AF State | RELAX |

**WHY:**
- No signals generated — no market setups detected in current window
- No signals to execute — Alpha Engine found no qualifying patterns
- Missing condition: Strategy entry criteria must be met for signal generation
- Profit factor 0.41 < 1.0 — system in drawdown recovery posture
- Win rate 20.4% below 45% — signal quality degraded
- Trade Activator TIER_3 — filters relaxed (score_min=0.400)
- Adaptive Filter RELAX — dry-spell triggered quality relaxation
- Idle 65 min — no qualifying setup across all pairs

**WHAT NEEDED:**
- Missing condition: Strategy entry criteria must be met for signal generation
- Next trigger: Strategy pattern match AND score ≥ 0.400 AND market regime compatible | NOTE: PF=0.41 < 1.0 — review RR structure before aggressive execution

**Alternative Action:**
Pause new entries; review strategy DNA and RR structure before resuming

## 4. Risk Engine Behavior

| Metric | Value |
|---|---|
| Risk State | ACTIVE |
| Size Reduced? | No |
| Trade Blocked? | No |
| Kill Switch? | No |
| Halt Reason | — |
| DD State | NORMAL |
| Current DD | 0.0% |
| Max DD (session) | 0.0% |
| Size Multiplier | 1.00× |
| Gate Reason | ALL_CLEAR |

## 5. Capital Efficiency

| Metric | Value |
|---|---|
| Current Equity | $767.37 |
| Net PnL | $-232.63 |
| Fees Paid | $113.42 |
| Capital Deployed | 11.9% |
| Capital Idle | 88.1% |
| Daily Risk Used | $122.84 |
| Daily Risk Remaining | $0.00 |
| Daily Cap | 6.0% |
| Missed Opportunity | 65 min idle at TIER_3 (score_min=0.4, vol_mult=0.2×) — no signal cleared all quality gates |

## 6. Performance Reality

> **Note (FTD-025C):** Session trades = 0. Stats below are **HISTORICAL (lifetime)**, not current session.

| Metric | Value |
|---|---|
| Expectancy / Trade | $-0.18 |
| Fee Impact | 32.8% |
| Fee per Trade (avg) | $0.09 |
| Win Rate | 20.4% |
| Avg Win | +$0.62 |
| Avg Loss | $-0.39 |
| Total Trades | 1284 |
| Total Net PnL | $-232.63 |

**Edge Consistency (strategy × regime):**
- - TRENDING@ALPHA_PBE_v1: edge=-0.228 wr=0% n=3 [NEGATIVE]
- - TRENDING@TF_EMA_RSI_v1: edge=-0.022 wr=33% n=3 [NEGATIVE]
- - MEAN_REVERTING@ALPHA_PBE_v1: edge=-0.161 wr=0% n=3 [NEGATIVE]
- - MEAN_REVERTING@MR_BB_RSI_v1: edge=-0.041 wr=25% n=4 [NEGATIVE]
- - TRENDING@ALPHA_TCB_v1: edge=-0.037 wr=25% n=8 [NEGATIVE]

## 7. Learning Memory

| Metric | Value |
|---|---|
| Status | ACTIVE |
| Memory Records | 0 |
| Total Patterns | 57 |
| Formed Patterns | 0 |
| Negative (Permanent) | 0 |
| Negative (Temporary) | 0 |

_No patterns formed yet — learning engine requires more trades. Pattern formation begins once per-strategy samples accumulate. No strategies are banned; all remain eligible._

## 8. Alert Intelligence

**ECO_TOXIC BLOCK (6 rejection(s))**
  Cause: ECO_TOXIC gating all signals in current window
  Impact: 6 trade opportunity(s) missed
  Fix: Review ECO_TOXIC conditions and threshold settings

**LOW PROFIT FACTOR (0.41)**
  Cause: Avg loss (-0.39) is 0.6× avg win (0.62)
  Impact: Expected loss per cycle on current RR structure
  Fix: Widen TP target; set rr_min ≥ 2.0; reject setups with RR < 2.0

**HIGH FEE DRAG (33% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $113.42 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**TRADE DRY-SPELL (65 min)**
  Cause: No signal clearing all quality gates
  Impact: Capital idle; Trade Activator relaxing filters
  Fix: Check Alpha Engine signal quality; inspect top rejection reasons

**RECURRING ERROR: WS_002 (20 times)**
  Cause: Repeated indicator quality failure
  Impact: Affected symbols blocked from evaluation
  Fix: Check ATR/ADX thresholds for affected symbol

**CONTRADICTION DETECTED (2 found)**
  Cause: Logical inconsistencies: GATING_BLOCK_INVISIBLE, LOW_PF_MASKED
  Impact: Report accuracy degraded without truth correction
  Fix: Truth engine corrected data — report reflects resolved state

## 9. Root Cause Analysis

**PRIMARY CAUSE:**
**Negative expectancy (PF=0.41)** — avg loss 0.6× avg win. Signal pipeline functioning; structural problem is insufficient reward-to-risk.

**SECONDARY CAUSES:**
- Avg loss (-0.39) > avg win (0.62) across 1284 trades

## 10. Action Plan

**IMMEDIATE (restart not required):**
- Increase rr_min 1.5 → 2.0 in config.py (reject RR < 2.0 entries)
- Reduce ACTIVATOR_T1_SCORE to 0.42 (allow borderline setups at TIER_1)

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
- Capital Idle:  88.1%
- Fix:    Strategy pattern match AND score ≥ 0.400 AND market regime compatible | NOTE: PF=0.41 < 1.0 — review RR structure before aggressive execution

```
Generated:       2026-05-27 02:17:55 UTC
Trades (total):  1284  |  PF: 0.412  |  WR: 20.4%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            TIER_3  score_min=0.4  vol_mult=0.2×
Idle:            64.9 min
Signals/hr:      0.0  Skips(window):   0
Top Errors:
  WS_002:gap=60.3s attempt=31: 1×
  WS_002:gap=60.2s attempt=30: 1×
  WS_002:gap=60.2s attempt=29: 1×
  WS_002:gap=60.4s attempt=28: 1×
  WS_002:gap=60.3s attempt=27: 1×
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
| Trades Evaluated | 1284 |

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
- Capital Idle: 88.1%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0

## 16. RL Intelligence (Contextual Bandit)

| Metric | Value |
|---|---|
| RL Phase | EXPLOITING (100% exploitation — bandit locked onto alpha) |
| Uptime | 129.9 min |
| Total Contexts Seen | 22 |
| Profitable Contexts | 0% |
| Allowed / Blocked | 17 / 6 |
| Allow Rate | 74% |
| Explore Trades | 0 (0%) |
| Exploit Trades | 17 (100%) |
| Confidence ×1.25 Fires | 0 |
| Score Floor −0.05 Fires | 0 |
| Score Floor +0.05 Fires | 0 |

**Top Alpha Contexts (RL Exploiting):**

| Context | Q-Value | UCB Bonus | Win Rate | Trades | PnL |
|---|---|---|---|---|---|
| TRENDING|NY|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|NY|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|NY|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| TRENDING|LATE|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|LATE|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |

**Near-Block Contexts (RL considering suppression):**

| Context | Q-Value | UCB Score | Win Rate | Trades | Near Block? |
|---|---|---|---|---|---|
| MEAN_REVERTING|LONDON|MeanReversion | -0.2044 | -0.0323 | 21% | 238 | No |
| TRENDING|NY|TrendFollowing | -0.1838 | +0.0074 | 22% | 193 | No |
| MEAN_REVERTING|NY|MeanReversion | -0.1678 | -0.0482 | 19% | 493 | No |