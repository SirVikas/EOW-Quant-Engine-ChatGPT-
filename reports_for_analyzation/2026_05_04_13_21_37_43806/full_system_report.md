# EOW Quant Engine — Full System Report

_Generated: 2026-05-04 07:49:52 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **458** trades with a net **LOSS** of **-167.03 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 35.1% |
| Profit Factor | 0.500 |
| Sharpe | -2.154 |
| Max Drawdown | 19.16% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 832.97 |
| Net PnL (USDT) | -167.0325 |
| Total Trades | 458 |
| Win Rate | 35.1% |
| Profit Factor | 0.500 |
| Sharpe | -2.154 |
| Sortino | -1.988 |
| Calmar | -0.480 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0356 |
| Avg Loss | -1.1238 |
| Fees Paid | 73.1255 |
| Slippage | 16.3936 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 418.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 0.0% |
| Signals total | 418 |
| Trades total | 0 |
| Skips total | 0 |
| Mins since trade | 85.9 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 07:48:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=62.2 above_sma=True regime=MEAN_REVERTING) |
| 07:48:02 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:48:02 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:48:02 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=76.5 above_sma=True regime=TRENDING) |
| 07:48:05 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:48:05 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:48:05 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 07:49:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=79876.4600 rsi=61.2 |
| 07:49:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | SIGNAL | ⚡ ALPHA TrendBreakout DASHUSDT score=0.658 rr=5.00 |
| 07:49:00 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=75.2 above_sma=True regime=TRENDING) |
| 07:49:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2368.4500 rsi=55.4 |
| 07:49:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | SIGNAL | ⚡ ALPHA TrendBreakout LUNCUSDT score=0.632 rr=5.00 |
| 07:49:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=32.6 |
| 07:49:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=59.6 above_sma=True regime=MEAN_REVERTING) |
| 07:49:06 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:06 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:06 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0604 rsi=57.9 |
| 07:49:42 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:42 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:42 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 832.97 |
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
| LUNCUSDT | LONG | -1.55 | -0.369 | TRENDING | MARKET |
| LUNCUSDT | LONG | -0.67 | -0.053 | TRENDING | MARKET |
| BIOUSDT | LONG | -3.73 | -0.298 | TRENDING | MARKET |
| LUNCUSDT | SHORT | -0.51 | -0.122 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.50 | -0.119 | TRENDING | MARKET |
| BIOUSDT | SHORT | -0.79 | -0.064 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.41 | -0.033 | MEAN_REVERTING | MARKET |
| PARTIUSDT | LONG | -0.57 | -0.137 | MEAN_REVERTING | MARKET |
| DASHUSDT | LONG | +1.36 | 0.328 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | -0.01 | -0.000 | MEAN_REVERTING | MARKET |
| BIOUSDT | SHORT | -0.79 | -0.190 | MEAN_REVERTING | MARKET |
| TSTUSDT | SHORT | +0.84 | 0.067 | MEAN_REVERTING | MARKET |
| PARTIUSDT | LONG | -1.26 | -0.303 | MEAN_REVERTING | MARKET |
| TSTUSDT | SHORT | +7.13 | 1.720 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | +0.60 | 0.146 | MEAN_REVERTING | MARKET |
| BIOUSDT | SHORT | -1.07 | -0.042 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.23 | -0.009 | MEAN_REVERTING | MARKET |
| TSTUSDT | LONG | -1.87 | -0.075 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.21 | -0.044 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.29 | -0.069 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 15, 'win_rate': 0.267, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 15, 'edge': 0.1626, 'win_rate': 0.267, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


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
| CT-001 | CRITICAL | Low profit factor (0.50 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (30.4% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (35.1% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 158.9059 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.500 (negative expectancy)
-   Detail — 458 trades; win_rate=35.1%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **Also noted (requires attention):**
-   - TRADE DRY-SPELL — 86 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.


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


