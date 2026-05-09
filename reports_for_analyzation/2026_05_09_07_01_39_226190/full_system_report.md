# EOW Quant Engine — Full System Report

_Generated: 2026-05-09 01:26:58 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **754** trades with a net **LOSS** of **-226.62 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 28.4% |
| Profit Factor | 0.501 |
| Sharpe | -2.188 |
| Max Drawdown | 24.27% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 773.38 |
| Net PnL (USDT) | -226.6186 |
| Total Trades | 754 |
| Win Rate | 28.4% |
| Profit Factor | 0.501 |
| Sharpe | -2.188 |
| Sortino | -2.170 |
| Calmar | -0.312 |
| Max Drawdown | 24.27% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0619 |
| Avg Loss | -0.8405 |
| Fees Paid | 107.0292 |
| Slippage | 41.8213 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 702.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 0.0% |
| Signals total | 702 |
| Trades total | 0 |
| Skips total | 0 |
| Mins since trade | 246.1 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 01:26:10 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:10 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:10 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.5510 rsi=46.3 |
| 01:26:10 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:10 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:10 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=79.1 above_sma=True regime=TRENDING) |
| 01:26:10 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:10 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:10 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=80259.5500 rsi=52.1 |
| 01:26:11 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:11 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:11 | SIGNAL | ⚡ ALPHA PullbackEntry STRKUSDT score=0.496 rr=5.00 |
| 01:26:11 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: LONG entry=0.0556 rsi=61.1 |
| 01:26:12 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:12 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:12 | FILTER | ⚡ PAPER_SPEED bypass NEARUSDT: SLEEP_MODE(vol=280=2%_of_avg=11331,min=10%[base=45%×0.20]) |
| 01:26:12 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=TRENDING) |
| 01:26:12 | SIGNAL | ⚡ DTP NILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:12 | SIGNAL | 📈 STREAK NILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:12 | SIGNAL | ⚡ PAPER_SPEED fallback NILUSDT: SHORT entry=0.0709 rsi=43.4 |
| 01:26:13 | SIGNAL | ⚡ DTP JTOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:13 | SIGNAL | 📈 STREAK JTOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:13 | FILTER | ⚡ PAPER_SPEED JTOUSDT: RSI filter blocked (rsi=63.2 above_sma=True regime=TRENDING) |
| 01:26:15 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:15 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:15 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=72.7 above_sma=True regime=TRENDING) |
| 01:26:27 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:27 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:27 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=49.5 above_sma=True regime=MEAN_REVERTING) |
| 01:26:54 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 773.38 |
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
| DOGSUSDT | SHORT | -0.80 | -0.205 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.36 | -0.091 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.04 | -0.010 | MEAN_REVERTING | MARKET |
| STRKUSDT | LONG | -0.77 | -0.198 | MEAN_REVERTING | MARKET |
| ETHUSDT | SHORT | +0.05 | 0.012 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.20 | -0.051 | MEAN_REVERTING | MARKET |
| DOGSUSDT | LONG | -0.60 | -0.155 | MEAN_REVERTING | MARKET |
| DYDXUSDT | SHORT | -0.49 | -0.126 | MEAN_REVERTING | MARKET |
| BTCUSDT | SHORT | -0.24 | -0.061 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.64 | -0.165 | MEAN_REVERTING | MARKET |
| DOGSUSDT | LONG | -0.60 | -0.155 | MEAN_REVERTING | MARKET |
| NILUSDT | LONG | +1.67 | 0.430 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.23 | -0.059 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.53 | -0.045 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.72 | -0.062 | MEAN_REVERTING | MARKET |
| NEARUSDT | LONG | -0.42 | -0.036 | MEAN_REVERTING | MARKET |
| ICPUSDT | LONG | -1.20 | -0.103 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.26 | -0.068 | MEAN_REVERTING | MARKET |
| FILUSDT | LONG | -0.30 | -0.077 | MEAN_REVERTING | MARKET |
| BTCUSDT | SHORT | -0.08 | -0.021 | MEAN_REVERTING | MARKET |


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
| recency_decay | 0.93 |
| thresholds | {'wr_high': 0.55, 'wr_low': 0.45, 'weight_at_low': 0.8} |
| regimes | {'MEAN_REVERTING': {'n_trades': 7, 'win_rate': 0.0, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 7, 'edge': -0.501, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 16668.4}} |


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
| CT-002 | CRITICAL | High fees (32.1% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (28.4% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 0.0 |
| daily_risk_cap_usdt | None |
| daily_risk_remaining | None |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1778289518.9541292 | WS_001 |  | gap=94.5s attempt=1 |
| 1778289459.5782008 | WS_001 |  | gap=35.1s |


### Healer Events (recent)

| Action | OK | Detail |
|---|---|---|
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | True |  |
| WS_RECONNECT | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| WS_RECONNECT | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | True |  |
| WS_RECONNECT | True |  |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.501 (negative expectancy)
-   Detail — 754 trades; win_rate=28.4%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **Also noted (requires attention):**
-   - TRADE DRY-SPELL — 246 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.


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


