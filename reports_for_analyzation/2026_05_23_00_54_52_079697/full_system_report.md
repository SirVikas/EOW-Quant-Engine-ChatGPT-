# EOW Quant Engine — Full System Report

_Generated: 2026-05-22 19:21:36 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **451** trades with a net **LOSS** of **-129.74 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 19.5% |
| Profit Factor | 0.395 |
| Sharpe | -5.141 |
| Max Drawdown | 13.26% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 870.26 |
| Net PnL (USDT) | -129.7385 |
| Total Trades | 451 |
| Win Rate | 19.5% |
| Profit Factor | 0.395 |
| Sharpe | -5.141 |
| Sortino | -6.309 |
| Calmar | -0.547 |
| Max Drawdown | 13.26% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.9640 |
| Avg Loss | -0.5911 |
| Fees Paid | 66.0134 |
| Slippage | 49.5100 |
| Deployability | 47/100 (NOT READY) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 30.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 0.0% |
| Signals total | 30 |
| Trades total | 0 |
| Skips total | 0 |
| Mins since trade | 3.2 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 19:18:40 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=29.1 above_sma=False bands=[48.0,52.0] (rsi=29.1 above_sma=False regime |
| 19:18:40 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V18.0\eow_quant_engine_FINAL_v2.2\eow_quant_engine\data\exports\optimi |
| 19:18:40 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI_LEVEL: rsi=49.4 above_sma=False bands=[30.0,70.0] (rsi=49.4 above_sma=False regi |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=47.8 above_sma=False bands=[48.0,52.0] (rsi=47.8 above_sma=False regime |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED ALLOUSDT: RSI_LEVEL: rsi=35.1 above_sma=False bands=[48.0,52.0] (rsi=35.1 above_sma=False regime |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI_LEVEL: rsi=41.7 above_sma=False bands=[30.0,70.0] (rsi=41.7 above_sma=False regime= |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED FETUSDT: RSI_LEVEL: rsi=32.5 above_sma=False bands=[48.0,52.0] (rsi=32.5 above_sma=False regime= |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=27.8 above_sma=False bands=[48.0,52.0] (rsi=27.8 above_sma=False regime |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=42.9 above_sma=False bands=[30.0,70.0] (rsi=42.9 above_sma=False regime= |
| 19:18:45 | FILTER | ⚡ PAPER_SPEED WLDUSDT: RSI_LEVEL: rsi=28.8 above_sma=False bands=[48.0,52.0] (rsi=28.8 above_sma=False regime= |
| 19:18:45 | FILTER | ⚡ PAPER_SPEED FIDAUSDT: RSI_LEVEL: rsi=37.4 above_sma=False bands=[48.0,52.0] (rsi=37.4 above_sma=False regime |
| 19:18:46 | FILTER | ⚡ PAPER_SPEED INJUSDT: RSI_LEVEL: rsi=48.5 above_sma=False bands=[30.0,70.0] (rsi=48.5 above_sma=False regime= |
| 19:18:47 | SYSTEM | ⚡ Mode switched to PAPER |
| 19:18:47 | FILTER | ⚡ PAPER_SPEED ALTUSDT: RSI_LEVEL: rsi=34.8 above_sma=False bands=[48.0,52.0] (rsi=34.8 above_sma=False regime= |
| 19:18:47 | SIGNAL | ⚡ PAPER_SPEED fallback UUSDT: SHORT entry=1.0007 rsi=100.0 |
| 19:20:00 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=31.9 above_sma=False bands=[48.0,52.0] (rsi=31.9 above_sma=False regime |
| 19:20:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=45.6 above_sma=False bands=[48.0,52.0] (rsi=45.6 above_sma=False regime= |
| 19:20:01 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=25.8 above_sma=False bands=[48.0,52.0] (rsi=25.8 above_sma=False regime |
| 19:20:01 | FILTER | ⚡ PAPER_SPEED WLDUSDT: RSI_LEVEL: rsi=35.4 above_sma=False bands=[48.0,52.0] (rsi=35.4 above_sma=False regime= |
| 19:20:01 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: SHORT entry=0.3954 rsi=54.5 |
| 19:20:01 | FILTER | ⚡ PAPER_SPEED INJUSDT: RSI_LEVEL: rsi=42.9 above_sma=False bands=[30.0,70.0] (rsi=42.9 above_sma=False regime= |
| 19:20:02 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI_LEVEL: rsi=55.8 above_sma=False bands=[30.0,70.0] (rsi=55.8 above_sma=False regi |
| 19:20:02 | FILTER | ⚡ PAPER_SPEED FETUSDT: RSI_LEVEL: rsi=47.1 above_sma=False bands=[48.0,52.0] (rsi=47.1 above_sma=False regime= |
| 19:20:02 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=49.3 above_sma=False bands=[30.0,70.0] (rsi=49.3 above_sma=False regime= |
| 19:20:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI_LEVEL: rsi=54.5 above_sma=False bands=[30.0,70.0] (rsi=54.5 above_sma=False regime= |
| 19:20:07 | FILTER | ⚡ PAPER_SPEED ALTUSDT: RSI_LEVEL: rsi=39.1 above_sma=False bands=[48.0,52.0] (rsi=39.1 above_sma=False regime= |
| 19:20:07 | FILTER | ⚡ PAPER_SPEED FIDAUSDT: RSI_LEVEL: rsi=38.8 above_sma=False bands=[48.0,52.0] (rsi=38.8 above_sma=False regime |
| 19:20:10 | FILTER | ⚡ PAPER_SPEED GENIUSUSDT: RSI_LEVEL: rsi=43.3 above_sma=False bands=[48.0,52.0] (rsi=43.3 above_sma=False regi |
| 19:20:11 | FILTER | ⚡ PAPER_SPEED ALLOUSDT: RSI_LEVEL: rsi=37.8 above_sma=False bands=[48.0,52.0] (rsi=37.8 above_sma=False regime |
| 19:20:19 | SIGNAL | ⚡ PAPER_SPEED fallback UUSDT: SHORT entry=1.0007 rsi=100.0 |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 870.26 |
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
| NEARUSDT | SHORT | +0.63 | 0.144 | MEAN_REVERTING | MARKET |
| WLDUSDT | SHORT | +2.27 | 0.524 | MEAN_REVERTING | MARKET |
| FIDAUSDT | SHORT | -0.69 | -0.159 | MEAN_REVERTING | MARKET |
| SPKUSDT | LONG | -0.44 | -0.102 | MEAN_REVERTING | MARKET |
| UUSDT | LONG | -0.24 | -0.056 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.46 | -0.104 | MEAN_REVERTING | MARKET |
| FETUSDT | LONG | -0.58 | -0.132 | MEAN_REVERTING | MARKET |
| ALLOUSDT | SHORT | -1.11 | -0.256 | MEAN_REVERTING | MARKET |
| GENIUSUSDT | LONG | -1.26 | -0.289 | MEAN_REVERTING | MARKET |
| EDENUSDT | LONG | +1.88 | 0.434 | MEAN_REVERTING | MARKET |
| ALTUSDT | SHORT | -0.62 | -0.144 | MEAN_REVERTING | MARKET |
| ALTUSDT | LONG | +2.63 | 0.605 | MEAN_REVERTING | MARKET |
| EDENUSDT | SHORT | -1.36 | -0.313 | MEAN_REVERTING | MARKET |
| FIDAUSDT | LONG | -1.73 | -0.398 | MEAN_REVERTING | MARKET |
| SAHARAUSDT | SHORT | +0.51 | 0.117 | MEAN_REVERTING | MARKET |
| EDENUSDT | LONG | -0.50 | -0.114 | MEAN_REVERTING | MARKET |
| NEARUSDT | SHORT | +1.82 | 0.419 | MEAN_REVERTING | MARKET |
| ALTUSDT | LONG | -0.63 | -0.144 | MEAN_REVERTING | MARKET |
| ALTUSDT | LONG | -0.63 | -0.145 | MEAN_REVERTING | MARKET |
| NEARUSDT | LONG | -0.08 | -0.019 | MEAN_REVERTING | MARKET |


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
| Score | 10 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.40 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (33.7% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (none dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (19.5% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


## 9. Auto-Tuning (Dynamic Thresholds)

| Metric | Value |
|---|---|
| score_min | 0.48 |
| volume_multiplier | 1.0 |
| fee_tolerance | 0.1 |
| dd_allowed | True |
| dd_size_mult | 1.0 |
| tier | NORMAL |
| af_state | NORMAL |
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
| daily_risk_cap_usdt | 52.2157 |
| daily_risk_remaining | 52.2157 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.395 (negative expectancy)
-   Detail — 451 trades; win_rate=19.5%. Every trade destroys capital on average. Immediate action required.
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


