# EOW Quant Engine — Unified System Report v2

_Generated: 2026-05-20 13:20:01 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | IDLE (225 min — activator tier=TIER_3) |
| Profitability | LOSS (PF=0.34, net=$-75.77) |
| Key Problem | Avg loss ($-0.54) is 0.6× avg win ($0.84); fees $38.41 consume 33.6% of gross |
| Immediate Action | Increase RR target to ≥2.0; reduce fee drag by raising min notional |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 421 |
| Signals Passed → Traded | 0 |
| Signals Rejected | 0 |
| Pass Rate | 0.0% |
| Reject Rate | 0.0% |
| Rejection Rate (window %) | 0.0% |
| Mins Since Last Trade | 224.6 |
| Signals / hour | 421.0 |
| Trades / hour | 0.00 |
| Execution Gap | 421 signal(s) → 0 trades |

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
- Profit factor 0.34 < 1.0 — system in drawdown recovery posture
- Win rate 18.1% below 45% — signal quality degraded
- Trade Activator TIER_3 — filters relaxed (score_min=0.400)
- Adaptive Filter RELAX — dry-spell triggered quality relaxation
- Idle 225 min — no qualifying setup across all pairs

**WHAT NEEDED:**
- Missing condition: None — all conditions met
- Next trigger: Signal passes all gates AND score ≥ 0.400

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
| Current Equity | $924.23 |
| Net PnL | $-75.77 |
| Fees Paid | $38.41 |
| Capital Deployed | 3.7% |
| Capital Idle | 96.3% |
| Daily Risk Used | $0.00 |
| Daily Risk Remaining | 5545.4% of equity |
| Daily Cap | 6.0% |
| Missed Opportunity | Signals available (421) but execution blocked by unknown gating |

## 6. Performance Reality

> **Note (FTD-025C):** Session trades = 0. Stats below are **HISTORICAL (lifetime)**, not current session.

| Metric | Value |
|---|---|
| Expectancy / Trade | $-0.29 |
| Fee Impact | 33.6% |
| Fee per Trade (avg) | $0.15 |
| Win Rate | 18.1% |
| Avg Win | +$0.84 |
| Avg Loss | $-0.54 |
| Total Trades | 259 |
| Total Net PnL | $-75.77 |

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

**NO TRADES EXECUTED (421 signal(s) blocked)**
  Cause: All signals rejected — dominant block: GATING
  Impact: Zero execution despite active signal flow
  Fix: Investigate GATING condition; check threshold configuration

**LOW PROFIT FACTOR (0.34)**
  Cause: Avg loss (-0.54) is 0.6× avg win (0.84)
  Impact: Expected loss per cycle on current RR structure
  Fix: Widen TP target; set rr_min ≥ 2.0; reject setups with RR < 2.0

**HIGH FEE DRAG (34% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $38.41 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**TRADE DRY-SPELL (225 min)**
  Cause: No signal clearing all quality gates
  Impact: Capital idle; Trade Activator relaxing filters
  Fix: Check Alpha Engine signal quality; inspect top rejection reasons

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
Reduce score_min (currently 0.40) or enable exploration trades

## 10. Action Plan

**IMMEDIATE (restart not required):**
- Increase rr_min 1.5 → 2.0 in config.py (reject RR < 2.0 entries)
- Reduce ACTIVATOR_T1_SCORE to 0.42 (allow borderline setups at TIER_1)
- Investigate top skip reasons — idle 225 min suggests systematic quality miss

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
- Cause:  NONE dominant block (421 → 0)
- Capital Idle:  96.3% (missed opportunity)
- Fix:    Signal passes all gates AND score ≥ 0.400

```
Generated:       2026-05-20 13:20:01 UTC
Trades (total):  259  |  PF: 0.344  |  WR: 18.1%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            TIER_3  score_min=0.4  vol_mult=0.2×
Idle:            224.6 min
Signals/hr:      421.0  Skips(window):   0
Top Errors:
  WS_002:gap=63.3s attempt=2: 1×
  WS_001:gap=60.7s attempt=1: 1×
  WS_001:gap=31.7s: 1×
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
| Trades Evaluated | 259 |

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
- Capital Idle: 96.3%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0

## 16. RL Intelligence (Contextual Bandit)

| Metric | Value |
|---|---|
| RL Phase | COLD_START (all trades via EXPLORE — no proven contexts yet) |
| Uptime | 224.5 min |
| Total Contexts Seen | 21 |
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
| MEAN_REVERTING|LONDON|MeanReversion | -0.4216 | -0.3366 | 21% | 216 | ⚠️ YES |
| MEAN_REVERTING|NY|MeanReversion | -0.2746 | -0.2018 | 16% | 294 | ⚠️ YES |
| MEAN_REVERTING|ASIA|MeanReversion | -0.1623 | -0.0762 | 19% | 210 | No |