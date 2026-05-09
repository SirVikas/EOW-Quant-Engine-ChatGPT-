# EOW Quant Engine — Unified System Report v2

_Generated: 2026-05-09 01:26:54 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | IDLE (246 min — activator tier=TIER_3) |
| Profitability | LOSS (PF=0.50, net=$-226.62) |
| Key Problem | System idle 246 min — no signal passing quality threshold |
| Immediate Action | Check Alpha Engine output; tier=TIER_3 score_min=0.4 |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 702 |
| Signals Passed → Traded | 0 |
| Signals Rejected | 0 |
| Pass Rate | 0.0% |
| Reject Rate | 0.0% |
| Rejection Rate (window %) | 0.0% |
| Mins Since Last Trade | 246.0 |
| Signals / hour | 702.0 |
| Trades / hour | 0.00 |
| Execution Gap | 702 signal(s) → 0 trades |

_No rejection reasons recorded in current window._

## 3. Decision Intelligence

| Metric | Value |
|---|---|
| AI Decision | BLOCKED |
| Mode | NORMAL |
| Tier | TIER_3 |
| Score Min | 0.400 |
| AF State | RELAX |

**WHY:**
- Profit factor 0.50 < 1.0 — system in drawdown recovery posture
- Win rate 28.4% below 45% — signal quality degraded
- Trade Activator TIER_3 — filters relaxed (score_min=0.400)
- Adaptive Filter RELAX — dry-spell triggered quality relaxation
- Idle 246 min — no qualifying setup across all pairs

**WHAT NEEDED:**
- Missing condition: None — all conditions met
- Next trigger: Signal passes all gates AND score ≥ 0.400

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
| Net PnL | $-226.62 |
| Fees Paid | $107.03 |
| Capital Deployed | 12.0% |
| Capital Idle | 88.0% |
| Daily Risk Used | $0.00 |
| Daily Risk Remaining | N/A |
| Daily Cap | 6.0% |
| Missed Opportunity | Signals available (702) but execution blocked by unknown gating |

## 6. Performance Reality

> **Note (FTD-025C):** Session trades = 0. Stats below are **HISTORICAL (lifetime)**, not current session.

| Metric | Value |
|---|---|
| Expectancy / Trade | $0.00 |
| Fee Impact | 32.1% |
| Fee per Trade (avg) | $107.03 |
| Win Rate | 28.4% |
| Avg Win | +$1.06 |
| Avg Loss | $-0.84 |
| Total Trades | 0 |
| Total Net PnL | $-226.62 |

**Edge Consistency (strategy × regime):**
- - MEAN_REVERTING@MeanReversion_PAPER_SPEED: edge=-0.501 wr=0% n=7 [DISABLED]

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

**NO TRADES EXECUTED (702 signal(s) blocked)**
  Cause: All signals rejected — dominant block: GATING
  Impact: Zero execution despite active signal flow
  Fix: Investigate GATING condition; check threshold configuration

**HIGH FEE DRAG (32% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $107.03 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**TRADE DRY-SPELL (246 min)**
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
- Investigate top skip reasons — idle 246 min suggests systematic quality miss

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
- Cause:  NONE dominant block (702 → 0)
- Capital Idle:  88.0% (missed opportunity)
- Fix:    Signal passes all gates AND score ≥ 0.400

```
Generated:       2026-05-09 01:26:54 UTC
Trades (total):  0  |  PF: 0.501  |  WR: 28.4%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            TIER_3  score_min=0.4  vol_mult=0.2×
Idle:            246.0 min
Signals/hr:      702.0  Skips(window):   0
Top Errors:
  WS_001:gap=94.5s attempt=1: 1×
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
- Capital Idle: 88.0%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0

## 16. RL Intelligence (Contextual Bandit)

| Metric | Value |
|---|---|
| RL Phase | CONVERGING (40% exploration — alpha contexts emerging) |
| Uptime | 291.3 min |
| Total Contexts Seen | 10 |
| Profitable Contexts | 0% |
| Allowed / Blocked | 520 / 0 |
| Allow Rate | 100% |
| Explore Trades | 208 (40%) |
| Exploit Trades | 312 (60%) |
| Confidence ×1.25 Fires | 0 |
| Score Floor −0.05 Fires | 0 |
| Score Floor +0.05 Fires | 3 |

**Top Alpha Contexts (RL Exploiting):**

| Context | Q-Value | UCB Bonus | Win Rate | Trades | PnL |
|---|---|---|---|---|---|
| TRENDING|LATE|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|LATE|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|LATE|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| TRENDING|LATE|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| TRENDING|ASIA|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |

**Near-Block Contexts (RL considering suppression):**

| Context | Q-Value | UCB Score | Win Rate | Trades | Near Block? |
|---|---|---|---|---|---|
| MEAN_REVERTING|LATE|MeanReversion | -0.3878 | +1.0300 | 0% | 7 | No |