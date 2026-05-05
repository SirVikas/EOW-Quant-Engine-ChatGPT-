# EOW Quant Engine — Full System Report

_Generated: 2026-05-05 08:25:46 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **502** trades with a net **LOSS** of **-175.30 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 33.9% |
| Profit Factor | 0.506 |
| Sharpe | -2.130 |
| Max Drawdown | 19.77% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 824.70 |
| Net PnL (USDT) | -175.2988 |
| Total Trades | 502 |
| Win Rate | 33.9% |
| Profit Factor | 0.506 |
| Sharpe | -2.130 |
| Sortino | -2.004 |
| Calmar | -0.445 |
| Max Drawdown | 19.77% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0561 |
| Avg Loss | -1.0688 |
| Fees Paid | 78.2685 |
| Slippage | 20.2508 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 336.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 100.0% |
| Signals total | 336 |
| Trades total | 0 |
| Skips total | 4 |
| Mins since trade | 226.9 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 08:22:59 | FILTER | ⏸ HOUR_GATE BTCUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:22:59 | FILTER | ⏸ HOUR_GATE TONUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:22:59 | FILTER | ⏸ HOUR_GATE ETHUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:22:59 | FILTER | ⏸ HOUR_GATE TSTUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:00 | FILTER | ⏸ HOUR_GATE BIOUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:01 | FILTER | ⏸ HOUR_GATE LUNCUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:01 | FILTER | ⏸ HOUR_GATE ONDOUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:02 | FILTER | ⏸ HOUR_GATE DASHUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:02 | FILTER | ⏸ HOUR_GATE LTCUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:27 | FILTER | ⏸ HOUR_GATE UNIUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:59 | FILTER | ⏸ HOUR_GATE LUNCUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:59 | FILTER | ⏸ HOUR_GATE TSTUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:59 | FILTER | ⏸ HOUR_GATE ONDOUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:59 | FILTER | ⏸ HOUR_GATE BIOUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:59 | FILTER | ⏸ HOUR_GATE TONUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:23:59 | FILTER | ⏸ HOUR_GATE BTCUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:00 | FILTER | ⏸ HOUR_GATE ETHUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:01 | FILTER | ⏸ HOUR_GATE LTCUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:05 | FILTER | ⏸ HOUR_GATE DASHUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:19 | FILTER | ⏸ HOUR_GATE UNIUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:59 | FILTER | ⏸ HOUR_GATE DASHUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:59 | FILTER | ⏸ HOUR_GATE TSTUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:59 | FILTER | ⏸ HOUR_GATE BTCUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:59 | FILTER | ⏸ HOUR_GATE BIOUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:59 | FILTER | ⏸ HOUR_GATE TONUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:59 | FILTER | ⏸ HOUR_GATE ETHUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:24:59 | FILTER | ⏸ HOUR_GATE UNIUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:25:01 | FILTER | ⏸ HOUR_GATE LTCUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:25:01 | FILTER | ⏸ HOUR_GATE LUNCUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |
| 08:25:01 | FILTER | ⏸ HOUR_GATE ONDOUSDT: 08h UTC BLOCKED — next open: 10h UTC / golden hours (positive PnL): 07h 10h 14h UTC |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 824.70 |
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
| LUNCUSDT | SHORT | -0.53 | -0.129 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | +1.51 | 0.368 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | -0.53 | -0.130 | MEAN_REVERTING | MARKET |
| BIOUSDT | SHORT | -0.53 | -0.130 | MEAN_REVERTING | MARKET |
| LTCUSDT | LONG | -0.32 | -0.078 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | -0.43 | -0.104 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.22 | -0.054 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | +0.15 | 0.036 | MEAN_REVERTING | MARKET |
| DASHUSDT | LONG | -0.44 | -0.107 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | +0.17 | 0.040 | MEAN_REVERTING | MARKET |
| TSTUSDT | SHORT | +8.23 | 2.009 | MEAN_REVERTING | MARKET |
| LTCUSDT | LONG | -0.20 | -0.049 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | -0.59 | -0.030 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.23 | -0.012 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | +0.68 | 0.165 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.17 | -0.009 | MEAN_REVERTING | MARKET |
| DASHUSDT | SHORT | -0.48 | -0.029 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.59 | -0.036 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | -0.57 | -0.139 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.84 | -0.204 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 29, 'win_rate': 0.241, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 29, 'edge': 0.0225, 'win_rate': 0.241, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.0 |
| MeanReversion | 1.0 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 10 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.51 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (30.9% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (33.9% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


## 9. Auto-Tuning (Dynamic Thresholds)

| Metric | Value |
|---|---|
| score_min | 0.4 |
| volume_multiplier | 0.2 |
| fee_tolerance | 0.1 |
| dd_allowed | True |
| dd_size_mult | 1.0 |
| tier | TIER_3 |
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
| Generation | 500 |
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
| daily_risk_used | 232.5306 |
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
| API_PING | True |  |
| BALANCE_SYNC | True |  |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.506 (negative expectancy)
-   Detail — 502 trades; win_rate=33.9%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **Also noted (requires attention):**
-   - TRADE DRY-SPELL — 227 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.


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


