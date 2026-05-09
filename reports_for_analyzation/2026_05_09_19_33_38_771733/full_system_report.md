# EOW Quant Engine — Full System Report

_Generated: 2026-05-09 13:58:37 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **823** trades with a net **LOSS** of **-246.25 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 26.9% |
| Profit Factor | 0.486 |
| Sharpe | -2.270 |
| Max Drawdown | 26.19% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 753.75 |
| Net PnL (USDT) | -246.2477 |
| Total Trades | 823 |
| Win Rate | 26.9% |
| Profit Factor | 0.486 |
| Sharpe | -2.270 |
| Sortino | -2.273 |
| Calmar | -0.288 |
| Max Drawdown | 26.19% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0523 |
| Avg Loss | -0.7954 |
| Fees Paid | 114.8958 |
| Slippage | 47.7213 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 742.00 |
| Trades / hour | 16.00 |
| Rejection Rate | 15.8% |
| Signals total | 742 |
| Trades total | 16 |
| Skips total | 3 |
| Mins since trade | 1.6 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 13:57:25 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 13:58:00 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=53.8 above_sma=False regime=MEAN_REVERTING) |
| 13:58:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.0600 rsi=60.0 |
| 13:58:00 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=23.9 above_sma=False regime=TRENDING) |
| 13:58:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=51.9 above_sma=True regime=TRENDING) |
| 13:58:00 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | SIGNAL | ⚡ ALPHA PullbackEntry STRKUSDT score=0.538 rr=5.00 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=MEAN_REVERTING) |
| 13:58:00 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 13:58:00 | SIGNAL | 📈 STREAK FILUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:01 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 13:58:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=62.8 above_sma=False regime=MEAN_REVERTING) |
| 13:58:01 | SIGNAL | 📈 STREAK TONUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:01 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=41.9 above_sma=False regime=TRENDING) |
| 13:58:02 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:02 | FILTER | ⚡ PAPER_SPEED bypass ARBUSDT: SLEEP_MODE(vol=11646=5%_of_avg=255387,min=10%[base=45%×0.20]) |
| 13:58:02 | SIGNAL | ⚡ PAPER_SPEED fallback ARBUSDT: SHORT entry=0.1414 rsi=84.6 |
| 13:58:02 | SIGNAL | 📈 STREAK OPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:02 | SIGNAL | ⚡ ALPHA PullbackEntry OPUSDT score=0.536 rr=5.00 |
| 13:58:02 | SIGNAL | ⚡ PAPER_SPEED fallback OPUSDT: SHORT entry=0.1647 rsi=59.1 |
| 13:58:19 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:19 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI_CRASH_GUARD blocked SHORT (rsi=72.9 prev=50.7≤65, need prev>65 — first-touch spike, |
| 13:58:28 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #27: meta_score=50.2 verdict=— |
| 13:58:35 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 753.75 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': 'b689c206', 'symbol': 'NEARUSDT', 'side': 'SHORT', 'entry_price': 1.57, 'qty': 96.100455, 'stop_loss': 1.572652, 'take_profit': 1.55587, 'entry_ts': 1778334854135, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 1.567, 'initial_risk': 3.7719, 'initial_stop_loss': 1.573768, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.7961783439490762, 'ticks_since_peak': 20}, {'position_id': '7eb02416', 'symbol': 'NOTUSDT', 'side': 'SHORT', 'entry_price': 0.000629, 'qty': 239869.180805, 'stop_loss': 0.0006281194, 'take_profit': 0.000620650025, 'entry_ts': 1778334959636, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 0.000626, 'initial_risk': 3.7719, 'initial_stop_loss': 0.00063122666, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': True, 'peak_r': 1.3473094230820928, 'ticks_since_peak': 262}, {'position_id': '2eb6506e', 'symbol': 'BTCUSDT', 'side': 'SHORT', 'entry_price': 80377.9, 'qty': 0.001877, 'stop_loss': 80570.80696, 'take_profit': 79654.49889999999, 'entry_ts': 1778335021268, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 80377.89, 'initial_risk': 3.7719, 'initial_stop_loss': 80570.80696, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 5.183846137413041e-05, 'ticks_since_peak': 285}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| NEARUSDT | SHORT | 96.100455 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| NOTUSDT | SHORT | 239,869.180805 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| BTCUSDT | SHORT | 0.001877 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| ONDOUSDT | LONG | -0.03 | -0.001 | MEAN_REVERTING | MARKET |
| ARBUSDT | SHORT | +0.64 | 0.028 | MEAN_REVERTING | MARKET |
| NOTUSDT | LONG | -0.46 | -0.020 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | -0.21 | -0.009 | MEAN_REVERTING | MARKET |
| BTCUSDT | SHORT | -0.24 | -0.010 | MEAN_REVERTING | MARKET |
| FILUSDT | SHORT | -0.09 | -0.004 | MEAN_REVERTING | MARKET |
| ETHUSDT | SHORT | -0.20 | -0.009 | MEAN_REVERTING | MARKET |
| LTCUSDT | LONG | -0.19 | -0.049 | MEAN_REVERTING | MARKET |
| OPUSDT | LONG | -0.39 | -0.104 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.45 | -0.120 | MEAN_REVERTING | MARKET |
| SAHARAUSDT | SHORT | -2.16 | -0.569 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | -0.38 | -0.100 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.19 | -0.051 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.19 | -0.051 | MEAN_REVERTING | MARKET |
| ICPUSDT | LONG | -0.00 | -0.000 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | -0.46 | -0.122 | MEAN_REVERTING | MARKET |
| SAHARAUSDT | SHORT | +1.54 | 0.407 | MEAN_REVERTING | MARKET |
| STRKUSDT | LONG | -0.49 | -0.128 | MEAN_REVERTING | MARKET |
| SAHARAUSDT | LONG | -1.04 | -0.275 | MEAN_REVERTING | MARKET |
| ASTERUSDT | LONG | -0.64 | -0.169 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 25, 'win_rate': 0.126, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 25, 'edge': -0.2028, 'win_rate': 0.16, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 1587.2}} |


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
| CT-001 | CRITICAL | Low profit factor (0.49 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (31.8% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (26.9% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 276.9549 |
| daily_risk_cap_usdt | None |
| daily_risk_remaining | None |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1778327037.7023463 | WS_001 |  | gap=30.8s |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.486 (negative expectancy)
-   Detail — 823 trades; win_rate=26.9%. Every trade destroys capital on average. Immediate action required.
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


