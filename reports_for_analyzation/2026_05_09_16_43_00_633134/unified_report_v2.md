# EOW Quant Engine — Unified System Report v2

_Generated: 2026-05-09 11:08:05 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | IDLE (71 min — activator tier=TIER_3) |
| Profitability | LOSS (PF=0.49, net=$-241.18) |
| Key Problem | All signals blocked by RL_TOXIC — no execution despite active signal flow |
| Immediate Action | Investigate RL_TOXIC condition; check threshold and tier configuration |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 886 |
| Signals Passed → Traded | 0 |
| Signals Rejected | 24 |
| Pass Rate | 0.0% |
| Reject Rate | 2.7% |
| Rejection Rate (window %) | 100.0% |
| Mins Since Last Trade | 71.3 |
| Signals / hour | 886.0 |
| Trades / hour | 0.00 |
| Execution Gap | 886 signal(s) → 0 trades |
| Dominant Block | RL_TOXIC (28 rejection(s)) |

**Top Rejection Reasons:**
- RL_TOXIC: 28 (100%)

## 3. Decision Intelligence

| Metric | Value |
|---|---|
| AI Decision | BLOCKED |
| Mode | NORMAL |
| Tier | TIER_3 |
| Score Min | 0.400 |
| AF State | RELAX |

**WHY:**
- Signals rejected due to RL_TOXIC gating condition
- Execution blocked by RL_TOXIC — signals exist but cannot proceed to order
- Missing condition: RL_TOXIC condition must be cleared for trade execution
- Profit factor 0.49 < 1.0 — system in drawdown recovery posture
- Win rate 27.2% below 45% — signal quality degraded
- Trade Activator TIER_3 — filters relaxed (score_min=0.400)
- Adaptive Filter RELAX — dry-spell triggered quality relaxation
- Idle 71 min — no qualifying setup across all pairs

**WHAT NEEDED:**
- Missing condition: RL_TOXIC condition must be cleared for trade execution
- Next trigger: Signal passes RL_TOXIC check AND score ≥ 0.400 AND risk gate CLEAR

**Alternative Action:**
Consider forcing Alpha Engine scan cycle or manual signal injection

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
| Net PnL | $-241.18 |
| Fees Paid | $111.87 |
| Capital Deployed | 12.9% |
| Capital Idle | 87.1% |
| Daily Risk Used | $110.56 |
| Daily Risk Remaining | N/A |
| Daily Cap | 6.0% |
| Missed Opportunity | Signals available (886) but execution blocked by RL_TOXIC |

## 6. Performance Reality

> **Note (FTD-025C):** Session trades = 0. Stats below are **HISTORICAL (lifetime)**, not current session.

| Metric | Value |
|---|---|
| Expectancy / Trade | $0.00 |
| Fee Impact | 31.7% |
| Fee per Trade (avg) | $111.87 |
| Win Rate | 27.2% |
| Avg Win | +$1.06 |
| Avg Loss | $-0.81 |
| Total Trades | 0 |
| Total Net PnL | $-241.18 |

**Edge Consistency (strategy × regime):**
- - MEAN_REVERTING@MeanReversion_PAPER_SPEED: edge=-0.247 wr=10% n=21 [DISABLED]

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

**NO TRADES EXECUTED (886 signal(s) blocked)**
  Cause: All signals rejected — dominant block: RL_TOXIC
  Impact: Zero execution despite active signal flow
  Fix: Investigate RL_TOXIC condition; check threshold configuration

**RL_TOXIC BLOCK (28 rejection(s))**
  Cause: RL_TOXIC gating all signals in current window
  Impact: 28 trade opportunity(s) missed
  Fix: Review RL_TOXIC conditions and threshold settings

**HIGH FEE DRAG (32% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $111.87 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**TRADE DRY-SPELL (71 min)**
  Cause: No signal clearing all quality gates
  Impact: Capital idle; Trade Activator relaxing filters
  Fix: Check Alpha Engine signal quality; inspect top rejection reasons

**SESSION/HISTORICAL METRICS MIXED**
  Cause: Session trades=0 but historical stats displayed without label
  Impact: Performance section shows lifetime stats, not current session
  Fix: Performance stats below are HISTORICAL (lifetime), not current session

## 9. Root Cause Analysis

**PRIMARY CAUSE (FTD-034):**
NO_EXECUTION — All signals blocked — 0 trades executed

**DETAIL:**
Signals generated but blocked by PRE_TRADE_GATE

**FIX:**
Reduce score_min (currently 0.40) or enable exploration trades

## 10. Action Plan

**IMMEDIATE (restart not required):**
- No immediate action required — maintain current configuration

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

- Issue:  NO_EXECUTION
- Cause:  RL_TOXIC dominant block (886 → 0)
- Capital Idle:  87.1% (missed opportunity)
- Fix:    Signal passes RL_TOXIC check AND score ≥ 0.400 AND risk gate CLEAR

```
Generated:       2026-05-09 11:08:05 UTC
Trades (total):  0  |  PF: 0.487  |  WR: 27.2%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            TIER_3  score_min=0.4  vol_mult=0.2×
Idle:            71.3 min
Signals/hr:      886.0  Skips(window):   24
Top Errors:
  WS_001:gap=31.0s: 1×
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
- Capital Idle: 87.1%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0

## 16. RL Intelligence (Contextual Bandit)

| Metric | Value |
|---|---|
| RL Phase | EXPLOITING (81% exploitation — bandit locked onto alpha) |
| Uptime | 173.6 min |
| Total Contexts Seen | 4 |
| Profitable Contexts | 0% |
| Allowed / Blocked | 21 / 28 |
| Allow Rate | 43% |
| Explore Trades | 4 (19%) |
| Exploit Trades | 17 (81%) |
| Confidence ×1.25 Fires | 0 |
| Score Floor −0.05 Fires | 0 |
| Score Floor +0.05 Fires | 10 |

**Top Alpha Contexts (RL Exploiting):**

| Context | Q-Value | UCB Bonus | Win Rate | Trades | PnL |
|---|---|---|---|---|---|
| TRENDING|LONDON|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| TRENDING|LONDON|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|LONDON|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| MEAN_REVERTING|LONDON|MeanReversion | ▼0.3163 | +0.6457 | 10% | 21 | $-5.190 |

**Near-Block Contexts (RL considering suppression):**

| Context | Q-Value | UCB Score | Win Rate | Trades | Near Block? |
|---|---|---|---|---|---|
| MEAN_REVERTING|LONDON|MeanReversion | -0.3163 | +0.3295 | 10% | 21 | No |