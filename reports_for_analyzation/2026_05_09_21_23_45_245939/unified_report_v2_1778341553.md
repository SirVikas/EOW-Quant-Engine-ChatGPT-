# EOW Quant Engine — Unified System Report v2

_Generated: 2026-05-09 15:45:53 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Truth → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | ACTIVE |
| Profitability | LOSS (PF=0.48, net=$-251.38) |
| Key Problem | System operating normally |
| Immediate Action | Monitor — no immediate action required |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 789 |
| Signals Passed → Traded | 17 |
| Signals Rejected | 0 |
| Pass Rate | 2.2% |
| Reject Rate | 0.0% |
| Rejection Rate (window %) | 0.0% |
| Mins Since Last Trade | 4.6 |
| Signals / hour | 789.0 |
| Trades / hour | 17.00 |
| Execution Gap | 772 signal(s) → 0 trades |

_No rejection reasons recorded in current window._

## 3. Decision Intelligence

| Metric | Value |
|---|---|
| AI Decision | MONITOR |
| Mode | NORMAL |
| Tier | NORMAL |
| Score Min | 0.480 |
| AF State | NORMAL |

**WHY:**
- Profit factor 0.48 < 1.0 — system in drawdown recovery posture
- Win rate 26.6% below 45% — signal quality degraded

**WHAT NEEDED:**
- Missing condition: None — all conditions met
- Next trigger: Signal passes all gates AND score ≥ 0.480

**Alternative Action:**
Continue monitoring — system will execute on next qualifying setup

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
| Net PnL | $-251.38 |
| Fees Paid | $117.66 |
| Capital Deployed | 13.4% |
| Capital Idle | 86.6% |
| Daily Risk Used | $101.51 |
| Daily Risk Remaining | N/A |
| Daily Cap | 6.0% |
| Missed Opportunity | None — system actively trading or recently traded |

## 6. Performance Reality

| Metric | Value |
|---|---|
| Expectancy / Trade | $0.00 |
| Fee Impact | 31.9% |
| Fee per Trade (avg) | $117.66 |
| Win Rate | 26.6% |
| Avg Win | +$1.04 |
| Avg Loss | $-0.78 |
| Total Trades | 0 |
| Total Net PnL | $-251.38 |

**Edge Consistency (strategy × regime):**
- - MEAN_REVERTING@MeanReversion_PAPER_SPEED: edge=-0.246 wr=18% n=17 [NEGATIVE]

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

**HIGH FEE DRAG (32% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $117.66 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

**SESSION/HISTORICAL METRICS MIXED**
  Cause: Session trades=0 but historical stats displayed without label
  Impact: Performance section shows lifetime stats, not current session
  Fix: Performance stats below are HISTORICAL (lifetime), not current session

## 9. Root Cause Analysis

**PRIMARY CAUSE:**
**Unresolved contradictions detected**: LOW_PF_MASKED, SESSION_HISTORICAL_MIX. System state requires investigation.

**SECONDARY CAUSES:**
_No significant secondary causes identified._

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

- Issue:  UNKNOWN
- Cause:  N/A dominant block
- Capital Idle:  86.6%
- Fix:    Signal passes all gates AND score ≥ 0.480

```
Generated:       2026-05-09 15:45:53 UTC
Trades (total):  0  |  PF: 0.482  |  WR: 26.6%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            NORMAL  score_min=0.48  vol_mult=1.0×
Idle:            4.6 min
Signals/hr:      789.0  Skips(window):   0
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
- Capital Idle: 86.6%
- Net Edge Coverage: 0.0% of signals have positive edge after costs
- Execution Rate: 0.0%
- Fix:
  - Improve RR — fewer signals have positive net edge after costs
  - Widen TP targets to ≥1.5R to recover profit factor above 1.0

## 16. RL Intelligence (Contextual Bandit)

| Metric | Value |
|---|---|
| RL Phase | CONVERGING (24% exploration — alpha contexts emerging) |
| Uptime | 61.2 min |
| Total Contexts Seen | 4 |
| Profitable Contexts | 0% |
| Allowed / Blocked | 17 / 0 |
| Allow Rate | 100% |
| Explore Trades | 4 (24%) |
| Exploit Trades | 13 (76%) |
| Confidence ×1.25 Fires | 0 |
| Score Floor −0.05 Fires | 0 |
| Score Floor +0.05 Fires | 7 |

**Top Alpha Contexts (RL Exploiting):**

| Context | Q-Value | UCB Bonus | Win Rate | Trades | PnL |
|---|---|---|---|---|---|
| TRENDING|NY|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| TRENDING|NY|MeanReversion | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| VOLATILITY_EXPANSION|NY|TrendFollowing | ▼0.0000 | +inf | 0% | 0 | $+0.000 |
| MEAN_REVERTING|NY|MeanReversion | ▼0.3115 | +0.6124 | 18% | 17 | $-4.189 |

**Near-Block Contexts (RL considering suppression):**

| Context | Q-Value | UCB Score | Win Rate | Trades | Near Block? |
|---|---|---|---|---|---|
| MEAN_REVERTING|NY|MeanReversion | -0.3115 | +0.3008 | 18% | 17 | No |