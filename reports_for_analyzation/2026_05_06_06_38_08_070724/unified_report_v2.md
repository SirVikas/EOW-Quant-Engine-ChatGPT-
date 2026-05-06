# EOW Quant Engine — Unified System Report v2

_Generated: 2026-05-06 01:05:53 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | IDLE (601 min — activator tier=TIER_3) |
| Profitability | LOSS (PF=0.52, net=$-174.60) |
| Key Problem | System idle 601 min — no signal passing quality threshold |
| Immediate Action | Check Alpha Engine output; tier=TIER_3 score_min=0.4 |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 479 |
| Signals Passed → Traded | 0 |
| Signals Rejected | 0 |
| Pass Rate | 0.0% |
| Reject Rate | 0.0% |
| Rejection Rate (window %) | 0.0% |
| Mins Since Last Trade | 601.3 |
| Signals / hour | 479.0 |
| Trades / hour | 0.00 |
| Execution Gap | 479 signal(s) → 0 trades |

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
- Profit factor 0.52 < 1.0 — system in drawdown recovery posture
- Win rate 33.3% below 45% — signal quality degraded
- Trade Activator TIER_3 — filters relaxed (score_min=0.400)
- Adaptive Filter RELAX — dry-spell triggered quality relaxation
- Idle 601 min — no qualifying setup across all pairs

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
| Net PnL | $-174.60 |
| Fees Paid | $79.66 |
| Capital Deployed | 9.5% |
| Capital Idle | 90.5% |
| Daily Risk Used | $0.00 |
| Daily Risk Remaining | N/A |
| Daily Cap | 6.0% |
| Missed Opportunity | Signals available (479) but execution blocked by unknown gating |

## 6. Performance Reality

> **Note (FTD-025C):** Session trades = 0. Stats below are **HISTORICAL (lifetime)**, not current session.

| Metric | Value |
|---|---|
| Expectancy / Trade | $0.00 |
| Fee Impact | 31.3% |
| Fee per Trade (avg) | $79.66 |
| Win Rate | 33.3% |
| Avg Win | +$1.09 |
| Avg Loss | $-1.05 |
| Total Trades | 0 |
| Total Net PnL | $-174.60 |

**Edge Consistency (strategy × regime):**
- - MEAN_REVERTING@MeanReversion_PAPER_SPEED: edge=-0.670 wr=0% n=5 [DISABLED]

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

**NO TRADES EXECUTED (479 signal(s) blocked)**
  Cause: All signals rejected — dominant block: GATING
  Impact: Zero execution despite active signal flow
  Fix: Investigate GATING condition; check threshold configuration

**HIGH FEE DRAG (31% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $79.66 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**TRADE DRY-SPELL (601 min)**
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
- Investigate top skip reasons — idle 601 min suggests systematic quality miss

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
- Cause:  NONE dominant block (479 → 0)
- Capital Idle:  90.5% (missed opportunity)
- Fix:    Signal passes all gates AND score ≥ 0.400

```
Generated:       2026-05-06 01:05:53 UTC
Trades (total):  0  |  PF: 0.516  |  WR: 33.3%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            TIER_3  score_min=0.4  vol_mult=0.2×
Idle:            601.3 min
Signals/hr:      479.0  Skips(window):   0
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
- Capital Idle: 90.5%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0

## 16. RL Intelligence (Contextual Bandit)

| Metric | Value |
|---|---|
| RL Phase | LEARNING (65% exploration — Q-values still forming) |
| Uptime | 617.0 min |
| Total Contexts Seen | 14 |
| Profitable Contexts | 0% |
| Allowed / Blocked | 650 / 0 |
| Allow Rate | 100% |
| Explore Trades | 420 (65%) |
| Exploit Trades | 230 (35%) |
| Confidence ×1.25 Fires | 0 |
| Score Floor −0.05 Fires | 0 |
| Score Floor +0.05 Fires | 0 |

**Top Alpha Contexts (RL Exploiting):**

| Context | Q-Value | UCB Bonus | Win Rate | Trades | PnL |
|---|---|---|---|---|---|
| TRENDING|NY|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|NY|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| TRENDING|NY|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|NY|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| MEAN_REVERTING|LATE|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |

**Near-Block Contexts (RL considering suppression):**

| Context | Q-Value | UCB Score | Win Rate | Trades | Near Block? |
|---|---|---|---|---|---|
| MEAN_REVERTING|NY|MeanReversion | -0.2610 | +1.4462 | 0% | 5 | No |