# EOW Quant Engine — Unified System Report v2

_Generated: 2026-04-26 03:00:58 UTC_  
_Engine: FTD-025B-URX-V2 — True Cause-Effect Narrative_

---

> **Design principle:** Data → Insight → Decision → Action  
> Every section answers WHY, not just WHAT.

## 1. Executive Snapshot

| Metric | Value |
|---|---|
| System State | ACTIVE |
| Trading Activity | ACTIVE |
| Profitability | LOSS (PF=0.37, net=$-137.43) |
| Key Problem | System operating normally |
| Immediate Action | Monitor — no immediate action required |

## 2. Signal → Trade Flow

| Metric | Value |
|---|---|
| Signals Generated (window) | 13 |
| Signals Passed → Traded | 0 |
| Signals Rejected | 6 |
| Rejection Rate | 100.0% |
| Mins Since Last Trade | 0.6 |
| Signals / hour | 13.0 |
| Trades / hour | 0.00 |

**Top Rejection Reasons:**
- SLEEP_MODE: 6 (100%)

## 3. Decision Intelligence

| Metric | Value |
|---|---|
| AI Decision | MONITOR — assess next candle |
| Mode | NORMAL |
| Tier | NORMAL |
| Score Min | 0.580 |
| AF State | NORMAL |

**WHY:**
- Profit factor 0.37 < 1.0 — system in drawdown recovery posture

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
| Net PnL | $-137.43 |
| Fees Paid | $45.77 |
| Capital Deployed | 9.2% |
| Capital Idle | 90.8% |
| Daily Risk Used | $0.00 |
| Daily Risk Remaining | $30.00 |
| Daily Cap | 3.0% |
| Missed Opportunity | None — system actively trading or recently traded |

## 6. Performance Reality

| Metric | Value |
|---|---|
| Expectancy / Trade | $0.00 |
| Fee Impact | 25.0% |
| Fee per Trade (avg) | $45.77 |
| Win Rate | 48.9% |
| Avg Win | +$1.24 |
| Avg Loss | $-3.20 |
| Total Trades | 0 |
| Total Net PnL | $-137.43 |

**Edge Consistency (strategy × regime):**
_Not enough trades to measure edge (need ≥20 per strategy-regime)._

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

**HIGH FEE DRAG (25% of gross)**
  Cause: Small-notional trades × maker/taker fee 0.1%
  Impact: Fees consuming $45.77 of gross turnover
  Fix: Increase MIN_NOTIONAL_USDT; reduce trade frequency

## 9. Root Cause Analysis

**PRIMARY CAUSE:**
**No critical root cause identified** — system operating normally.

**SECONDARY CAUSES:**
- Top skip reason `SLEEP_MODE` (6 times) blocking signal flow

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

```
Generated:       2026-04-26 03:00:58 UTC
Trades (total):  0  |  PF: 0.369  |  WR: 48.9%
Gate:            can_trade=True  reason=ALL_CLEAR
Tier:            NORMAL  score_min=0.58  vol_mult=1.0×
Idle:            0.6 min
Signals/hr:      13.0  Skips(window):   6
Top Errors:      none

```