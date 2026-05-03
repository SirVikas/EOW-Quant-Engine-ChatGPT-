# EOW Quant Engine — Full System Report

_Generated: 2026-05-03 10:57:41 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **392** trades with a net **LOSS** of **-174.49 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 36.2% |
| Profit Factor | 0.394 |
| Sharpe | -2.594 |
| Max Drawdown | 19.16% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 825.51 |
| Net PnL (USDT) | -174.4909 |
| Total Trades | 392 |
| Win Rate | 36.2% |
| Profit Factor | 0.394 |
| Sharpe | -2.594 |
| Sortino | -2.267 |
| Calmar | -0.585 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.7976 |
| Avg Loss | -1.1510 |
| Fees Paid | 64.9516 |
| Slippage | 10.2632 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 32.00 |
| Trades / hour | 1.00 |
| Rejection Rate | 0.0% |
| Signals total | 32 |
| Trades total | 1 |
| Skips total | 0 |
| Mins since trade | 3.6 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 10:52:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=35.7 above_sma=False regime=TRENDING) |
| 10:52:07 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=52.6 above_sma=True regime=MEAN_REVERTING) |
| 10:52:25 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=30.3 above_sma=False regime=TRENDING) |
| 10:53:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=29.4 above_sma=False regime=TRENDING) |
| 10:53:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=45.5 above_sma=False regime=MEAN_REVERTING) |
| 10:53:02 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=34.3 above_sma=False regime=TRENDING) |
| 10:53:05 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2312.5700 rsi=38.9 |
| 10:53:05 | SIGNAL | 🔔 Signal SHORT ETHUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 10:53:05 | SIGNAL | 💰 Orchestrator ETHUSDT: score=0.370 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 10:53:05 | TRADE | ⚡ PAPER_SPEED market-fill override ETHUSDT: USE_LIMIT_ORDERS bypassed |
| 10:53:05 | TRADE | ✅ Opened SHORT ETHUSDT qty=0.071448 risk=12.39U [TrendFollowing / TRENDING] |
| 10:54:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 10:54:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=29.4 above_sma=False regime=TRENDING) |
| 10:54:03 | TRADE | Position closed [SL] LUNCUSDT @ 8.332e-05 |
| 10:54:11 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=MEAN_REVERTING) |
| 10:54:22 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0780 rsi=48.5 |
| 10:54:22 | SIGNAL | 🔔 Signal SHORT ORCAUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 10:54:22 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.400 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 10:54:22 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 10:54:22 | TRADE | ✅ Opened SHORT ORCAUSDT qty=79.452275 risk=12.38U [TrendFollowing / TRENDING] |
| 10:55:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=33.3 above_sma=False regime=TRENDING) |
| 10:55:24 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=61.9 above_sma=True regime=MEAN_REVERTING) |
| 10:56:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=21.7 above_sma=False regime=TRENDING) |
| 10:56:02 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=61.9 above_sma=True regime=MEAN_REVERTING) |
| 10:57:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=23.0 above_sma=False regime=TRENDING) |
| 10:57:12 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0543 rsi=61.9 |
| 10:57:12 | SIGNAL | 🔔 Signal LONG BIOUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 10:57:12 | SIGNAL | 💰 Orchestrator BIOUSDT: score=0.428 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 10:57:12 | TRADE | ⚡ PAPER_SPEED market-fill override BIOUSDT: USE_LIMIT_ORDERS bypassed |
| 10:57:12 | TRADE | ✅ Opened LONG BIOUSDT qty=3040.549314 risk=12.38U [TrendFollowing / TRENDING] |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 825.51 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': '098b8cfa', 'symbol': 'BABYUSDT', 'side': 'SHORT', 'entry_price': 0.02494, 'qty': 6625.006415, 'stop_loss': 0.024803811, 'take_profit': 0.023588252, 'entry_ts': 1777805330569, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 0.02379, 'initial_risk': 12.3921, 'initial_stop_loss': 0.025615874, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 1.701500575551067, 'ticks_since_peak': 632}, {'position_id': '954e4e9d', 'symbol': 'ORDIUSDT', 'side': 'SHORT', 'entry_price': 4.98, 'qty': 33.178245, 'stop_loss': 4.99486016, 'take_profit': 4.9385664, 'entry_ts': 1777805338137, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 4.97, 'initial_risk': 12.3921, 'initial_stop_loss': 4.996573440000001, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.6033750386160374, 'ticks_since_peak': 174}, {'position_id': '390b11f0', 'symbol': 'ETHUSDT', 'side': 'SHORT', 'entry_price': 2312.57, 'qty': 0.071448, 'stop_loss': 2319.970224, 'take_profit': 2294.06944, 'entry_ts': 1777805585529, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 2311.9, 'initial_risk': 12.3921, 'initial_stop_loss': 2319.970224, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.09053779993687686, 'ticks_since_peak': 24}, {'position_id': '56cceeeb', 'symbol': 'ORCAUSDT', 'side': 'SHORT', 'entry_price': 2.078, 'qty': 79.452275, 'stop_loss': 2.0871432, 'take_profit': 2.055142, 'entry_ts': 1777805662359, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 2.074, 'initial_risk': 12.3826, 'initial_stop_loss': 2.0871432, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.43748359436521084, 'ticks_since_peak': 37}, {'position_id': 'd86babb3', 'symbol': 'BIOUSDT', 'side': 'LONG', 'entry_price': 0.0543, 'qty': 3040.549314, 'stop_loss': 0.054100527999999995, 'take_profit': 0.05529912, 'entry_ts': 1777805832862, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 0.0547, 'initial_risk': 12.3826, 'initial_stop_loss': 0.053900352, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 1.00088077508206, 'ticks_since_peak': 28}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| BABYUSDT | SHORT | 6,625.006415 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| ORDIUSDT | SHORT | 33.178245 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| ETHUSDT | SHORT | 0.071448 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| ORCAUSDT | SHORT | 79.452275 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| BIOUSDT | LONG | 3,040.549314 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| ORDIUSDT | LONG | -1.12 | -0.090 | TRENDING | MARKET |
| ORDIUSDT | LONG | -1.12 | -0.090 | TRENDING | MARKET |
| BIOUSDT | SHORT | -1.52 | -0.121 | TRENDING | MARKET |
| LUNCUSDT | SHORT | +5.38 | 0.215 | TRENDING | MARKET |
| ORDIUSDT | LONG | +1.38 | 0.055 | MEAN_REVERTING | MARKET |
| ORDIUSDT | SHORT | -1.13 | -0.045 | TRENDING | MARKET |
| BIOUSDT | SHORT | +1.68 | 0.067 | TRENDING | MARKET |
| ETHUSDT | SHORT | -0.77 | -0.061 | TRENDING | MARKET |
| BABYUSDT | LONG | -4.75 | -0.377 | TRENDING | MARKET |
| LUNCUSDT | SHORT | -1.14 | -0.091 | TRENDING | MARKET |
| ORCAUSDT | LONG | +1.00 | 0.079 | MEAN_REVERTING | MARKET |
| BIOUSDT | SHORT | -1.21 | -0.097 | TRENDING | MARKET |
| ORDIUSDT | SHORT | -1.27 | -0.101 | TRENDING | MARKET |
| BABYUSDT | LONG | -2.32 | -0.185 | TRENDING | MARKET |
| BIOUSDT | SHORT | -0.76 | -0.182 | TRENDING | MARKET |
| ORDIUSDT | LONG | -0.61 | -0.146 | TRENDING | MARKET |
| LUNCUSDT | SHORT | -1.21 | -0.290 | MEAN_REVERTING | MARKET |
| BIOUSDT | SHORT | -0.75 | -0.181 | MEAN_REVERTING | MARKET |
| ORDIUSDT | LONG | -0.76 | -0.061 | TRENDING | MARKET |
| LUNCUSDT | SHORT | -0.63 | -0.051 | TRENDING | MARKET |


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
| regimes | {'TRENDING': {'n_trades': 1, 'win_rate': 0.0, 'weight': 1.0}} |


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
| strategies | {'TRENDING@TrendFollowing_PAPER_SPEED': {'n_trades': 1, 'edge': -0.6292, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 1.0 |
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
| CT-001 | CRITICAL | Low profit factor (0.39 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (27.1% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (TrendFollowing dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (36.2% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| Generation | 120 |
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
| daily_risk_used | 74.3336 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.394 (negative expectancy)
-   Detail — 392 trades; win_rate=36.2%. Every trade destroys capital on average. Immediate action required.
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


