# EOW Quant Engine — Unified System Report v2

_Generated: 2026-05-10 16:47:33 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | RECENT (5 min ago) |
| Profitability | LOSS (PF=0.46, net=$-294.35) |
| Key Problem | Avg loss ($-0.68) is 0.7× avg win ($0.97); fees $141.81 consume 32.5% of gross |
| Immediate Action | Increase RR target to ≥2.0; reduce fee drag by raising min notional |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 441 |
| Signals Passed → Traded | 8 |
| Signals Rejected | 0 |
| Pass Rate | 1.8% |
| Reject Rate | 0.0% |
| Rejection Rate (window %) | 0.0% |
| Mins Since Last Trade | 5.1 |
| Signals / hour | 441.0 |
| Trades / hour | 8.00 |
| Execution Gap | 433 signal(s) → 0 trades |
| Dominant Block | RL_TOXIC (5 rejection(s)) |

**Top Rejection Reasons:**
- RL_TOXIC: 5 (100%)

## 3. Decision Intelligence

| Metric | Value |
|---|---|
| AI Decision | MONITOR |
| Mode | NORMAL |
| Tier | TIER_1 |
| Score Min | 0.430 |
| AF State | RELAX |

**WHY:**
- Profit factor 0.46 < 1.0 — system in drawdown recovery posture
- Win rate 24.4% below 45% — signal quality degraded
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
| Current Equity | $1000.00 |
| Net PnL | $-294.35 |
| Fees Paid | $141.81 |
| Capital Deployed | 15.3% |
| Capital Idle | 84.7% |
| Daily Risk Used | $113.47 |
| Daily Risk Remaining | N/A |
| Daily Cap | 6.0% |
| Missed Opportunity | None — system actively trading or recently traded |

## 6. Performance Reality

| Metric | Value |
|---|---|
| Expectancy / Trade | $-0.28 |
| Fee Impact | 32.5% |
| Fee per Trade (avg) | $0.13 |
| Win Rate | 24.4% |
| Avg Win | +$0.97 |
| Avg Loss | $-0.68 |
| Total Trades | 1055 |
| Total Net PnL | $-294.35 |

**Edge Consistency (strategy × regime):**
- - MEAN_REVERTING@MeanReversion_PAPER_SPEED: edge=-0.213 wr=18% n=28 [DISABLED]

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

**RL_TOXIC BLOCK (5 rejection(s))**
  Cause: RL_TOXIC gating all signals in current window
  Impact: 5 trade opportunity(s) missed
  Fix: Review RL_TOXIC conditions and threshold settings

**LOW PROFIT FACTOR (0.46)**
  Cause: Avg loss (-0.68) is 0.7× avg win (0.97)
  Impact: Expected loss per cycle on current RR structure
  Fix: Widen TP target; set rr_min ≥ 2.0; reject setups with RR < 2.0

**HIGH FEE DRAG (33% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $141.81 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**CONTRADICTION DETECTED (1 found)**
  Cause: Logical inconsistencies: LOW_PF_MASKED
  Impact: Report accuracy degraded without truth correction
  Fix: Truth engine corrected data — report reflects resolved state

## 9. Root Cause Analysis

**PRIMARY CAUSE:**
**Negative expectancy (PF=0.46)** — avg loss 0.7× avg win. Signal pipeline functioning; structural problem is insufficient reward-to-risk.

**SECONDARY CAUSES:**
- Avg loss (-0.68) > avg win (0.97) across 1055 trades

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
- Capital Idle:  84.7%
- Fix:    Signal passes all gates AND score ≥ 0.430

```
Generated:       2026-05-10 16:47:33 UTC
Trades (total):  1055  |  PF: 0.461  |  WR: 24.4%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            TIER_1  score_min=0.43  vol_mult=0.5×
Idle:            5.1 min
Signals/hr:      441.0  Skips(window):   0
Top Errors:      none

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
| Trades Evaluated | 1055 |

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
- Capital Idle: 84.7%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0

## 16. RL Intelligence (Contextual Bandit)

| Metric | Value |
|---|---|
| RL Phase | EXPLOITING (100% exploitation — bandit locked onto alpha) |
| Uptime | 246.6 min |
| Total Contexts Seen | 20 |
| Profitable Contexts | 0% |
| Allowed / Blocked | 23 / 5 |
| Allow Rate | 82% |
| Explore Trades | 0 (0%) |
| Exploit Trades | 23 (100%) |
| Confidence ×1.25 Fires | 0 |
| Score Floor −0.05 Fires | 0 |
| Score Floor +0.05 Fires | 25 |

**Top Alpha Contexts (RL Exploiting):**

| Context | Q-Value | UCB Bonus | Win Rate | Trades | PnL |
|---|---|---|---|---|---|
| TRENDING|NY|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| TRENDING|NY|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|NY|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|NY|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| TRENDING|LATE|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |

**Near-Block Contexts (RL considering suppression):**

| Context | Q-Value | UCB Score | Win Rate | Trades | Near Block? |
|---|---|---|---|---|---|
| MEAN_REVERTING|LONDON|MeanReversion | -0.2492 | +0.3483 | 14% | 21 | No |
| MEAN_REVERTING|ASIA|MeanReversion | -0.2315 | +0.1679 | 17% | 47 | No |
| MEAN_REVERTING|NY|MeanReversion | -0.2223 | +0.1200 | 12% | 64 | No |