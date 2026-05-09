# EOW Quant Engine — Full System Report

_Generated: 2026-05-09 15:46:35 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **846** trades with a net **LOSS** of **-251.38 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 26.6% |
| Profit Factor | 0.482 |
| Sharpe | -2.285 |
| Max Drawdown | 26.69% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 748.62 |
| Net PnL (USDT) | -251.3808 |
| Total Trades | 846 |
| Win Rate | 26.6% |
| Profit Factor | 0.482 |
| Sharpe | -2.285 |
| Sortino | -2.292 |
| Calmar | -0.281 |
| Max Drawdown | 26.69% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0395 |
| Avg Loss | -0.7814 |
| Fees Paid | 117.6628 |
| Slippage | 49.7966 |
| Deployability | 45/100 (NOT READY) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 782.00 |
| Trades / hour | 17.00 |
| Rejection Rate | 0.0% |
| Signals total | 782 |
| Trades total | 17 |
| Skips total | 0 |
| Mins since trade | 5.2 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 15:45:25 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:25 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 15:45:25 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:25 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=51.4 above_sma=True regime=TRENDING) |
| 15:45:25 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:25 | SIGNAL | ⚡ PAPER_SPEED fallback SAHARAUSDT: SHORT entry=0.0386 rsi=58.6 |
| 15:45:25 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:25 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=45.2 above_sma=False regime=MEAN_REVERTING) |
| 15:45:26 | SIGNAL | 📈 STREAK OPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:26 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=43.8 above_sma=False regime=MEAN_REVERTING) |
| 15:45:35 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:35 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=54.5 above_sma=True regime=TRENDING) |
| 15:45:36 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:36 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=36.7 above_sma=False regime=TRENDING) |
| 15:45:36 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:36 | FILTER | ⚡ PAPER_SPEED bypass STRKUSDT: SLEEP_MODE(vol=3441=1%_of_avg=565998,min=10%[base=45%×0.20]) |
| 15:45:36 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: SHORT entry=0.0530 rsi=75.0 |
| 15:45:38 | SIGNAL | 📈 STREAK TONUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:38 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=MEAN_REVERTING) |
| 15:45:40 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:40 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=26.1 above_sma=False regime=TRENDING) |
| 15:45:41 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:41 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=TRENDING) |
| 15:45:53 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |
| 15:46:08 | SYSTEM | 📦 Master Report Bundle downloaded → eow_bundle_1778341558.zip (846 trades, 936 KB) |
| 15:46:11 | SYSTEM | 🔬 Live Process Snapshot downloaded → eow_live_process_20260509_154611.zip (177 KB / logs=2000 rl_contexts=4 tr |
| 15:46:23 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:46:23 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.430 |
| 15:46:23 | SIGNAL | ⚡ ALPHA PullbackEntry UNIUSDT score=0.498 rr=5.00 |
| 15:46:23 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: LONG entry=3.6320 rsi=44.4 |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 748.62 |
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
| STRKUSDT | SHORT | -0.21 | -0.056 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.03 | -0.009 | MEAN_REVERTING | MARKET |
| SAHARAUSDT | SHORT | -0.78 | -0.206 | MEAN_REVERTING | MARKET |
| ARBUSDT | SHORT | -0.42 | -0.038 | MEAN_REVERTING | MARKET |
| ICPUSDT | SHORT | -0.00 | -0.000 | MEAN_REVERTING | MARKET |
| FILUSDT | SHORT | +0.65 | 0.058 | MEAN_REVERTING | MARKET |
| LTCUSDT | SHORT | +0.05 | 0.004 | MEAN_REVERTING | MARKET |
| ICPUSDT | LONG | -0.38 | -0.034 | MEAN_REVERTING | MARKET |
| NOTUSDT | LONG | -0.70 | -0.186 | MEAN_REVERTING | MARKET |
| ARBUSDT | LONG | -0.42 | -0.113 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.37 | -0.099 | MEAN_REVERTING | MARKET |
| ICPUSDT | SHORT | -0.38 | -0.100 | MEAN_REVERTING | MARKET |
| NEARUSDT | SHORT | -0.02 | -0.005 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | +0.18 | 0.048 | MEAN_REVERTING | MARKET |
| ICPUSDT | LONG | -0.42 | -0.112 | MEAN_REVERTING | MARKET |
| LTCUSDT | SHORT | -0.29 | -0.077 | MEAN_REVERTING | MARKET |
| ETHUSDT | SHORT | -0.34 | -0.089 | MEAN_REVERTING | MARKET |
| OPUSDT | LONG | -0.48 | -0.128 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.39 | -0.103 | MEAN_REVERTING | MARKET |
| FILUSDT | SHORT | -0.46 | -0.122 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 17, 'win_rate': 0.138, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 17, 'edge': -0.2464, 'win_rate': 0.176, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


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
| CT-001 | CRITICAL | Low profit factor (0.48 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (31.9% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (26.6% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 101.508 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.482 (negative expectancy)
-   Detail — 846 trades; win_rate=26.6%. Every trade destroys capital on average. Immediate action required.
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


