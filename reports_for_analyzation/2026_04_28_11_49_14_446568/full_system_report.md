# EOW Quant Engine — Full System Report

_Generated: 2026-04-28 06:17:11 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **243** trades with a net **LOSS** of **-151.08 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 45.7% |
| Profit Factor | 0.379 |
| Sharpe | -2.915 |
| Max Drawdown | 16.87% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 848.92 |
| Net PnL (USDT) | -151.0820 |
| Total Trades | 243 |
| Win Rate | 45.7% |
| Profit Factor | 0.379 |
| Sharpe | -2.915 |
| Sortino | -2.329 |
| Calmar | -0.929 |
| Max Drawdown | 16.87% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.8310 |
| Avg Loss | -1.8434 |
| Fees Paid | 50.5689 |
| Slippage | 0.0000 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 83.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 0.0% |
| Signals total | 83 |
| Trades total | 0 |
| Skips total | 0 |
| Mins since trade | 5.8 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 06:11:40 | SYSTEM | ⚡ Mode switched to PAPER |
| 06:12:06 | FILTER | ⚡ PAPER_SPEED bypass ADAUSDT: SLEEP_MODE(vol=20=0%_of_avg=51380,min=10%[base=45%×0.20]) |
| 06:13:00 | FILTER | ⚡ PAPER_SPEED bypass SOLUSDT: SLEEP_MODE(vol=139=8%_of_avg=1742,min=10%[base=45%×0.20]) |
| 06:13:00 | SIGNAL | ⚡ ALPHA TrendBreakout ORCAUSDT score=0.638 rr=4.00 |
| 06:13:00 | SIGNAL | 🔔 Signal LONG ORCAUSDT / TCB: ADX=26.9 VOL=1.8x RR=4.00 SCORE=0.638 |
| 06:13:01 | FILTER | ⚡ PAPER_SPEED bypass ADAUSDT: SLEEP_MODE(vol=3995=8%_of_avg=49753,min=10%[base=45%×0.20]) |
| 06:14:00 | SIGNAL | ⚡ ALPHA PullbackEntry ETHUSDT score=0.493 rr=5.00 |
| 06:14:00 | SIGNAL | 🔔 Signal SHORT ETHUSDT / PBE: EMA_DIST=0.00% RSI=60.0 RR=5.00 SCORE=0.493 |
| 06:14:01 | SIGNAL | ⚡ ALPHA PullbackEntry LUNCUSDT score=0.604 rr=4.00 |
| 06:14:01 | SIGNAL | 🔔 Signal LONG LUNCUSDT / PBE: EMA_DIST=0.22% RSI=42.0 RR=4.00 SCORE=0.604 |
| 06:14:10 | FILTER | ⚡ PAPER_SPEED bypass ADAUSDT: SLEEP_MODE(vol=3799=8%_of_avg=48469,min=10%[base=45%×0.20]) |
| 06:15:00 | SIGNAL | ⚡ ALPHA TrendBreakout TRXUSDT score=0.703 rr=5.00 |
| 06:15:00 | SIGNAL | 🔔 Signal SHORT TRXUSDT / TCB: ADX=27.4 VOL=4.2x RR=5.00 SCORE=0.703 |
| 06:16:00 | SIGNAL | 🔔 Signal SHORT ETHUSDT / EMA cross DOWN / trend↓ / RSI=51.6 / ATR=0.7571 |
| 06:16:03 | FILTER | ⚡ PAPER_SPEED bypass ADAUSDT: SLEEP_MODE(vol=3762=8%_of_avg=46769,min=10%[base=45%×0.20]) |
| 06:16:25 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #1: meta_score=85.0 verdict=BLOCKED |
| 06:16:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:16:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:16:59 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:16:59 | SIGNAL | ⚡ DTP ZBTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:16:59 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:00 | SIGNAL | 🔔 Signal LONG LUNCUSDT / BB lower touch / RSI=29.7 / Mean=0.0001 / TP=0.0001 |
| 06:17:01 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:02 | SIGNAL | ⚡ DTP SUIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:02 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:03 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:03 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 848.92 |
| Halted | False |
| Graceful stop | False |
| Open positions | [] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

_(no data)_


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| XRPUSDT | SHORT | -0.09 | -0.051 | TRENDING | LIMIT |
| ZBTUSDT | LONG | +0.08 | 0.048 | TRENDING | LIMIT |
| ORCAUSDT | LONG | -1.27 | -0.738 | MEAN_REVERTING | LIMIT |
| SOLUSDT | LONG | -0.01 | -0.004 | MEAN_REVERTING | LIMIT |
| RAYUSDT | SHORT | -0.37 | -0.217 | MEAN_REVERTING | LIMIT |
| KATUSDT | SHORT | +0.10 | 0.056 | TRENDING | LIMIT |
| TRUMPUSDT | SHORT | -0.11 | -0.064 | MEAN_REVERTING | LIMIT |
| HYPERUSDT | LONG | -0.62 | -0.363 | MEAN_REVERTING | LIMIT |
| XRPUSDT | SHORT | -0.01 | -0.007 | TRENDING | LIMIT |
| ETHUSDT | LONG | -0.02 | -0.010 | TRENDING | LIMIT |
| ORCAUSDT | SHORT | -1.24 | -0.203 | MEAN_REVERTING | LIMIT |
| ZBTUSDT | SHORT | -5.94 | -0.972 | TRENDING | LIMIT |
| AXSUSDT | SHORT | +0.08 | 0.013 | TRENDING | LIMIT |
| SOLUSDT | SHORT | +0.01 | 0.001 | MEAN_REVERTING | LIMIT |
| KATUSDT | SHORT | -0.73 | -0.120 | TRENDING | LIMIT |
| SOLUSDT | SHORT | -0.13 | -0.021 | TRENDING | LIMIT |
| CHIPUSDT | LONG | +0.22 | 0.036 | TRENDING | LIMIT |
| BTCUSDT | SHORT | -0.09 | -0.015 | TRENDING | LIMIT |
| TRUMPUSDT | SHORT | +0.02 | 0.003 | MEAN_REVERTING | LIMIT |
| ETHUSDT | SHORT | -0.14 | -0.082 | TRENDING | LIMIT |


## 7. AI Brain


### AI Decision (FTD-023)

| Metric | Value |
|---|---|
| Mode | NORMAL |
| Decision | MONITOR — assess next candle |
| Module | AI_BRAIN |
| Phase | 023 |


### Regime

| Metric | Value |
|---|---|
| Current | — |
| Confidence | — |
| Stable ticks | — |


### Learning Engine

| Metric | Value |
|---|---|
| window_size | 50 |
| min_samples | 5 |
| thresholds | {'wr_high': 0.55, 'wr_low': 0.45, 'weight_at_low': 0.8} |
| regimes | {} |


### Edge Engine

| Metric | Value |
|---|---|
| window_size | 50 |
| min_trades | 20 |
| emergency_min_trades | 5 |
| emergency_kill_at | -0.3 |
| edge_boost_at | 0.15 |
| edge_kill_at | 0.0 |
| boost_mult | 1.25 |
| strategies | {} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.0 |
| MeanReversion | 0.0 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 30 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.38 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (25.1% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (none dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


## 9. Auto-Tuning (Dynamic Thresholds)

| Metric | Value |
|---|---|
| score_min | 0.43 |
| volume_multiplier | 0.5 |
| fee_tolerance | 0.1 |
| dd_allowed | True |
| dd_size_mult | 1.0 |
| tier | TIER_1 |
| af_state | RELAX |
| module | DYNAMIC_THRESHOLD_PROVIDER |
| phase | 5.2 |


### Streak State

| Metric | Value |
|---|---|
| win_streak_min | 3 |
| loss_streak_min | 3 |
| hot_score_adj | -0.03 |
| cold_score_adj | 0.05 |
| module | STREAK_INTELLIGENCE_ENGINE |
| phase | 6 |


## 10. Evolution (Genome)

| Metric | Value |
|---|---|
| Generation | 60 |
| Fitness | — |
| Active DNA count | 3 |
| Last mutation | — |


### Active DNA (summary)

| Strategy | Keys |
|---|---|
| TrendFollowing | ['strategy', 'ema_fast', 'ema_slow', 'ema_trend', 'rsi_period'] |
| MeanReversion | ['strategy', 'bb_period', 'bb_std', 'rsi_period', 'rsi_ob'] |
| VolatilityExpansion | ['strategy', 'lookback', 'atr_period', 'atr_sl', 'atr_tp'] |


## 11. Capital Allocation

| Metric | Value |
|---|---|
| max_capital_pct | 0.05 |
| daily_risk_cap | 0.06 |
| daily_risk_used | 0.0 |
| daily_risk_cap_usdt | None |
| daily_risk_remaining | None |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

_(no data)_


### Healer Events (recent)

| Action | OK | Detail |
|---|---|---|
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |


## 13. Alerts

| Metric | Value |
|---|---|
| Gate: can_trade | — |
| Gate: safe_mode | — |
| Gate: reason | — |
| Halt active | False |
| Halt reason | — |
| Halt since | — |


## 14. Final Diagnosis

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.379 (negative expectancy)
-   Detail — 243 trades; win_rate=45.7%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).


## 15. Action Checklist

- [ ] Review Section 4 (Decision Trace) for last 30 thoughts.
- [ ] Archive this report under /reports/<date>/ for audit trail.

---

_End of report — FTD-025A Export Engine v1.0_


## 16. Learning Memory (FTD-030B)

| Metric | Value |
|---|---|
| Status | ACTIVE |
| Memory Records | 0 |
| Total Patterns | 0 |
| Formed Patterns | 0 |
| Cycles Processed | 0 |
| Negative Memory (Permanent) | 0 |
| Negative Memory (Temporary) | 0 |


