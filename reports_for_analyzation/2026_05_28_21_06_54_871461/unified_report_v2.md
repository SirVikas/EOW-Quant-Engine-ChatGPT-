# EOW Quant Engine — Unified System Report v2

_Generated: 2026-05-28 15:22:59 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | RECENT (5 min ago) |
| Profitability | LOSS (PF=0.48, net=$-254.55) |
| Key Problem | Avg loss ($-0.34) is 0.6× avg win ($0.56); fees $132.62 consume 34.3% of gross |
| Immediate Action | Increase RR target to ≥2.0; reduce fee drag by raising min notional |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 405 |
| Signals Passed → Traded | 7 |
| Signals Rejected | 6 |
| Pass Rate | 1.7% |
| Reject Rate | 1.5% |
| Rejection Rate (window %) | 46.2% |
| Mins Since Last Trade | 5.2 |
| Signals / hour | 405.0 |
| Trades / hour | 7.00 |
| Execution Gap | 398 signal(s) → 0 trades |
| Dominant Block | ECO_TOXIC (205 rejection(s)) |

**Top Rejection Reasons:**
- ECO_TOXIC: 205 (57%)
- SL_TOO_TIGHT: 137 (38%)
- RL_TOXIC: 11 (3%)
- RR_LOW: 5 (1%)

## 3. Decision Intelligence

| Metric | Value |
|---|---|
| AI Decision | MONITOR |
| Mode | NORMAL |
| Tier | TIER_1 |
| Score Min | 0.430 |
| AF State | RELAX |

**WHY:**
- Profit factor 0.48 < 1.0 — system in drawdown recovery posture
- Win rate 22.6% below 45% — signal quality degraded
- Trade Activator TIER_1 — filters relaxed (score_min=0.430)
- Adaptive Filter RELAX — dry-spell triggered quality relaxation

**WHAT NEEDED:**
- Missing condition: None — all conditions met
- Next trigger: Signal passes all gates AND score ≥ 0.430

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
| Current Equity | $745.45 |
| Net PnL | $-254.55 |
| Fees Paid | $132.62 |
| Capital Deployed | 12.2% |
| Capital Idle | 87.8% |
| Daily Risk Used | $1114.09 |
| Daily Risk Remaining | $0.00 |
| Daily Cap | 6.0% |
| Missed Opportunity | None — system actively trading or recently traded |

## 6. Performance Reality

| Metric | Value |
|---|---|
| Expectancy / Trade | $-0.14 |
| Fee Impact | 34.3% |
| Fee per Trade (avg) | $0.07 |
| Win Rate | 22.6% |
| Avg Win | +$0.56 |
| Avg Loss | $-0.34 |
| Total Trades | 1831 |
| Total Net PnL | $-254.55 |

**Edge Consistency (strategy × regime):**
- - TRENDING@ALPHA_TCB_v1: edge=-0.108 wr=22% n=50 [DISABLED]
- - TRENDING@ALPHA_PBE_v1: edge=-0.034 wr=22% n=50 [DISABLED]
- - MEAN_REVERTING@MR_BB_RSI_v1: edge=-0.070 wr=30% n=50 [DISABLED]
- - TRENDING@TF_EMA_RSI_v1: edge=-0.076 wr=26% n=35 [DISABLED]
- - MEAN_REVERTING@ALPHA_PBE_v1: edge=-0.077 wr=21% n=48 [DISABLED]

## 7. Learning Memory

| Metric | Value |
|---|---|
| Status | ACTIVE |
| Memory Records | 0 |
| Total Patterns | 105 |
| Formed Patterns | 0 |
| Negative (Permanent) | 0 |
| Negative (Temporary) | 0 |

_No patterns formed yet — learning engine requires more trades. Pattern formation begins once per-strategy samples accumulate. No strategies are banned; all remain eligible._

## 8. Alert Intelligence

**ECO_TOXIC BLOCK (205 rejection(s))**
  Cause: ECO_TOXIC gating all signals in current window
  Impact: 205 trade opportunity(s) missed
  Fix: Review ECO_TOXIC conditions and threshold settings

**LOW PROFIT FACTOR (0.48)**
  Cause: Avg loss (-0.34) is 0.6× avg win (0.56)
  Impact: Expected loss per cycle on current RR structure
  Fix: Widen TP target; set rr_min ≥ 2.0; reject setups with RR < 2.0

**HIGH FEE DRAG (34% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $132.62 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**RECURRING ERROR: WS_001 (17 times)**
  Cause: Repeated indicator quality failure
  Impact: Affected symbols blocked from evaluation
  Fix: Check ATR/ADX thresholds for affected symbol

**CONTRADICTION DETECTED (1 found)**
  Cause: Logical inconsistencies: LOW_PF_MASKED
  Impact: Report accuracy degraded without truth correction
  Fix: Truth engine corrected data — report reflects resolved state

## 9. Root Cause Analysis

**PRIMARY CAUSE:**
**Negative expectancy (PF=0.48)** — avg loss 0.6× avg win. Signal pipeline functioning; structural problem is insufficient reward-to-risk.

**SECONDARY CAUSES:**
- Avg loss (-0.34) > avg win (0.56) across 1831 trades

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
- Capital Idle:  87.8%
- Fix:    Signal passes all gates AND score ≥ 0.430

```
Generated:       2026-05-28 15:22:59 UTC
Trades (total):  1831  |  PF: 0.476  |  WR: 22.6%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            TIER_1  score_min=0.43  vol_mult=0.5×
Idle:            5.2 min
Signals/hr:      405.0  Skips(window):   6
Top Errors:
  WS_001:gap=31.9s: 2×
  WS_001:gap=32.9s: 2×
  WS_001:gap=31.8s: 1×
  WS_001:gap=30.7s: 1×
  WS_001:gap=35.1s: 1×
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
| Trades Evaluated | 1831 |

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
- Capital Idle: 87.8%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0

## 16. RL Intelligence (Contextual Bandit)

| Metric | Value |
|---|---|
| RL Phase | EXPLOITING (100% exploitation — bandit locked onto alpha) |
| Uptime | 1860.9 min |
| Total Contexts Seen | 23 |
| Profitable Contexts | 0% |
| Allowed / Blocked | 573 / 216 |
| Allow Rate | 73% |
| Explore Trades | 0 (0%) |
| Exploit Trades | 573 (100%) |
| Confidence ×1.25 Fires | 0 |
| Score Floor −0.05 Fires | 0 |
| Score Floor +0.05 Fires | 35 |

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
| MEAN_REVERTING|NY|MeanReversion | -0.1815 | -0.0124 | 19% | 525 | No |
| MEAN_REVERTING|LONDON|MeanReversion | -0.1501 | +0.0794 | 22% | 285 | No |
| MEAN_REVERTING|ASIA|MeanReversion | -0.1122 | +0.1021 | 18% | 327 | No |