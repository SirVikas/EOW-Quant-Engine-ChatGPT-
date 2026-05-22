# EOW Quant Engine — Unified System Report v2

_Generated: 2026-05-22 19:21:36 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | BLOCKED (None — signals present, no execution) |
| Profitability | LOSS (PF=0.40, net=$-129.74) |
| Key Problem | Avg loss ($-0.59) is 0.6× avg win ($0.96); fees $66.01 consume 33.7% of gross |
| Immediate Action | Increase RR target to ≥2.0; reduce fee drag by raising min notional |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 30 |
| Signals Passed → Traded | 0 |
| Signals Rejected | 0 |
| Pass Rate | 0.0% |
| Reject Rate | 0.0% |
| Rejection Rate (window %) | 0.0% |
| Mins Since Last Trade | 3.2 |
| Signals / hour | 30.0 |
| Trades / hour | 0.00 |
| Execution Gap | 30 signal(s) → 0 trades |

_No rejection reasons recorded in current window._

## 3. Decision Intelligence

| Metric | Value |
|---|---|
| AI Decision | BLOCKED |
| Mode | NORMAL |
| Tier | NORMAL |
| Score Min | 0.480 |
| AF State | NORMAL |

**WHY:**
- Profit factor 0.40 < 1.0 — system in drawdown recovery posture
- Win rate 19.5% below 45% — signal quality degraded

**WHAT NEEDED:**
- Missing condition: None — all conditions met
- Next trigger: Signal passes all gates AND score ≥ 0.480

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
| Current Equity | $870.26 |
| Net PnL | $-129.74 |
| Fees Paid | $66.01 |
| Capital Deployed | 6.4% |
| Capital Idle | 93.6% |
| Daily Risk Used | $0.00 |
| Daily Risk Remaining | 5221.6% of equity |
| Daily Cap | 6.0% |
| Missed Opportunity | Signals available (30) but execution blocked by unknown gating |

## 6. Performance Reality

> **Note (FTD-025C):** Session trades = 0. Stats below are **HISTORICAL (lifetime)**, not current session.

| Metric | Value |
|---|---|
| Expectancy / Trade | $-0.29 |
| Fee Impact | 33.7% |
| Fee per Trade (avg) | $0.15 |
| Win Rate | 19.5% |
| Avg Win | +$0.96 |
| Avg Loss | $-0.59 |
| Total Trades | 451 |
| Total Net PnL | $-129.74 |

**Edge Consistency (strategy × regime):**
_Not enough trades to measure edge (need ≥20 per strategy-regime)._

## 7. Learning Memory

| Metric | Value |
|---|---|
| Status | ACTIVE |
| Memory Records | 0 |
| Total Patterns | 0 |
| Formed Patterns | 0 |
| Negative (Permanent) | 0 |
| Negative (Temporary) | 0 |

_No patterns formed yet — learning engine requires more trades. Pattern formation begins once per-strategy samples accumulate. No strategies are banned; all remain eligible._

## 8. Alert Intelligence

**NO TRADES EXECUTED (30 signal(s) blocked)**
  Cause: All signals rejected — dominant block: GATING
  Impact: Zero execution despite active signal flow
  Fix: Investigate GATING condition; check threshold configuration

**LOW PROFIT FACTOR (0.40)**
  Cause: Avg loss (-0.59) is 0.6× avg win (0.96)
  Impact: Expected loss per cycle on current RR structure
  Fix: Widen TP target; set rr_min ≥ 2.0; reject setups with RR < 2.0

**HIGH FEE DRAG (34% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $66.01 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**CONTRADICTION DETECTED (2 found)**
  Cause: Logical inconsistencies: SIGNALS_NO_TRADES, LOW_PF_MASKED
  Impact: Report accuracy degraded without truth correction
  Fix: Truth engine corrected data — report reflects resolved state

## 9. Root Cause Analysis

**PRIMARY CAUSE (FTD-034):**
NO_EXECUTION — All signals blocked — 0 trades executed

**DETAIL:**
Signals generated but blocked by PRE_TRADE_GATE

**FIX:**
Reduce score_min (currently 0.48) or enable exploration trades

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

- Issue:  NO_EXECUTION
- Cause:  NONE dominant block (30 → 0)
- Capital Idle:  93.6% (missed opportunity)
- Fix:    Signal passes all gates AND score ≥ 0.480

```
Generated:       2026-05-22 19:21:36 UTC
Trades (total):  451  |  PF: 0.395  |  WR: 19.5%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            NORMAL  score_min=0.48  vol_mult=1.0×
Idle:            3.2 min
Signals/hr:      30.0  Skips(window):   0
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
| Trades Evaluated | 451 |

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
- Capital Idle: 93.6%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0

## 16. RL Intelligence (Contextual Bandit)

| Metric | Value |
|---|---|
| RL Phase | COLD_START (all trades via EXPLORE — no proven contexts yet) |
| Uptime | 3.1 min |
| Total Contexts Seen | 22 |
| Profitable Contexts | 0% |
| Allowed / Blocked | 0 / 0 |
| Allow Rate | 0% |
| Explore Trades | 0 (0%) |
| Exploit Trades | 0 (100%) |
| Confidence ×1.25 Fires | 0 |
| Score Floor −0.05 Fires | 0 |
| Score Floor +0.05 Fires | 0 |

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
| MEAN_REVERTING|ASIA|MeanReversion | -0.5215 | -0.4422 | 18% | 248 | ⚠️ YES |
| MEAN_REVERTING|LONDON|MeanReversion | -0.4216 | -0.3366 | 21% | 216 | ⚠️ YES |
| MEAN_REVERTING|LATE|MeanReversion | -0.3185 | -0.2449 | 17% | 288 | ⚠️ YES |