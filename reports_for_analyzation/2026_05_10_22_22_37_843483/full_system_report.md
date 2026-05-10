# EOW Quant Engine — Full System Report

_Generated: 2026-05-10 16:47:36 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **1055** trades with a net **LOSS** of **-294.35 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 24.4% |
| Profit Factor | 0.461 |
| Sharpe | -2.382 |
| Max Drawdown | 30.91% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 705.65 |
| Net PnL (USDT) | -294.3460 |
| Total Trades | 1055 |
| Win Rate | 24.4% |
| Profit Factor | 0.461 |
| Sharpe | -2.382 |
| Sortino | -2.424 |
| Calmar | -0.227 |
| Max Drawdown | 30.91% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.9746 |
| Avg Loss | -0.6848 |
| Fees Paid | 141.8088 |
| Slippage | 67.9061 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 441.00 |
| Trades / hour | 8.00 |
| Rejection Rate | 0.0% |
| Signals total | 441 |
| Trades total | 8 |
| Skips total | 0 |
| Mins since trade | 5.1 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 16:44:00 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=81.4 above_sma=True regime=TRENDING) |
| 16:44:00 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0541 rsi=62.5 |
| 16:44:02 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=51.2 above_sma=True regime=MEAN_REVERTING) |
| 16:44:02 | SIGNAL | ⚡ ALPHA PullbackEntry LAYERUSDT score=0.573 rr=4.00 |
| 16:44:02 | SIGNAL | ⚡ PAPER_SPEED fallback LAYERUSDT: SHORT entry=0.1267 rsi=60.5 |
| 16:45:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=45.8 above_sma=False regime=TRENDING) |
| 16:45:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=78.6 above_sma=True regime=TRENDING) |
| 16:45:01 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=54.5 above_sma=True regime=MEAN_REVERTING) |
| 16:45:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=42.1 above_sma=False regime=TRENDING) |
| 16:45:03 | SIGNAL | ⚡ PAPER_SPEED fallback LAYERUSDT: SHORT entry=0.1266 rsi=52.6 |
| 16:45:03 | SIGNAL | ⚡ ALPHA PullbackEntry UNIUSDT score=0.540 rr=5.00 |
| 16:45:03 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: LONG entry=4.0480 rsi=39.8 |
| 16:45:08 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0541 rsi=57.1 |
| 16:45:59 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #49: meta_score=48.3 verdict=— |
| 16:46:01 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: LONG entry=4.0680 rsi=47.8 |
| 16:46:02 | SIGNAL | ⚡ ALPHA TrendBreakout TONUSDT score=0.879 rr=5.00 |
| 16:46:02 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=32.0 above_sma=False regime=TRENDING) |
| 16:46:02 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=46.5 above_sma=False regime=MEAN_REVERTING) |
| 16:46:02 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=48.3 above_sma=False regime=TRENDING) |
| 16:46:02 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=46.0 above_sma=True regime=MEAN_REVERTING) |
| 16:46:05 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=75.6 above_sma=True regime=TRENDING) |
| 16:46:06 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0540 rsi=57.1 |
| 16:47:09 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81281.8400 rsi=66.2 |
| 16:47:09 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=48.7 above_sma=True regime=MEAN_REVERTING) |
| 16:47:10 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=54.1 above_sma=True regime=MEAN_REVERTING) |
| 16:47:11 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=48.3 above_sma=False regime=TRENDING) |
| 16:47:14 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=55.0 above_sma=False regime=MEAN_REVERTING) |
| 16:47:14 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=83.1 above_sma=True regime=TRENDING) |
| 16:47:22 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=69.2 above_sma=False regime=MEAN_REVERTING) |
| 16:47:33 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 705.65 |
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
| LUNCUSDT | LONG | -0.01 | -0.004 | MEAN_REVERTING | MARKET |
| LAYERUSDT | LONG | +0.13 | 0.036 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.41 | -0.114 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.18 | -0.050 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | +0.32 | 0.090 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | -0.50 | -0.142 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | -0.51 | -0.144 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | -0.46 | -0.129 | MEAN_REVERTING | MARKET |
| BTCUSDT | SHORT | -0.15 | -0.042 | MEAN_REVERTING | MARKET |
| UNIUSDT | SHORT | -0.03 | -0.007 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | +0.14 | 0.039 | MEAN_REVERTING | MARKET |
| ONDOUSDT | SHORT | -0.37 | -0.104 | MEAN_REVERTING | MARKET |
| TONUSDT | SHORT | -0.02 | -0.007 | MEAN_REVERTING | MARKET |
| LAYERUSDT | LONG | -0.95 | -0.270 | MEAN_REVERTING | MARKET |
| BIOUSDT | SHORT | -0.20 | -0.056 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | -0.20 | -0.056 | MEAN_REVERTING | MARKET |
| UNIUSDT | SHORT | -0.41 | -0.115 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.33 | -0.095 | MEAN_REVERTING | MARKET |
| ONDOUSDT | SHORT | -0.03 | -0.009 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | +0.15 | 0.042 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 28, 'win_rate': 0.189, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 28, 'edge': -0.2127, 'win_rate': 0.179, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 3644.3}} |


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
| CT-001 | CRITICAL | Low profit factor (0.46 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (32.5% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (24.4% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 113.4664 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.461 (negative expectancy)
-   Detail — 1055 trades; win_rate=24.4%. Every trade destroys capital on average. Immediate action required.
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


