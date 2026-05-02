# EOW Quant Engine — Full System Report

_Generated: 2026-05-02 05:42:05 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **324** trades with a net **LOSS** of **-160.93 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 38.6% |
| Profit Factor | 0.369 |
| Sharpe | -2.681 |
| Max Drawdown | 17.84% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 839.07 |
| Net PnL (USDT) | -160.9276 |
| Total Trades | 324 |
| Win Rate | 38.6% |
| Profit Factor | 0.369 |
| Sharpe | -2.681 |
| Sortino | -2.282 |
| Calmar | -0.702 |
| Max Drawdown | 17.84% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.7535 |
| Avg Loss | -1.2820 |
| Fees Paid | 57.3651 |
| Slippage | 5.0972 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 198.00 |
| Trades / hour | 17.00 |
| Rejection Rate | 5.6% |
| Signals total | 198 |
| Trades total | 17 |
| Skips total | 1 |
| Mins since trade | 8.5 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 05:30:01 | TRADE | ✅ Opened SHORT XRPUSDT qty=91.060921 risk=1.68U [TrendFollowing / TRENDING] |
| 05:30:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78110.6400 |
| 05:30:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:01 | SIGNAL | 💰 Orchestrator BTCUSDT: score=0.506 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 05:30:01 | TRADE | ⚡ PAPER_SPEED market-fill override BTCUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:01 | TRADE | ✅ Opened SHORT BTCUSDT qty=0.001613 risk=1.68U [TrendFollowing / TRENDING] |
| 05:30:02 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:02 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1519 |
| 05:30:02 | SIGNAL | 🔔 Signal SHORT MEGAUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:02 | SIGNAL | 💰 Orchestrator MEGAUSDT: score=0.231 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 05:30:02 | TRADE | ⚡ PAPER_SPEED market-fill override MEGAUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:02 | TRADE | ✅ Opened SHORT MEGAUSDT qty=829.319806 risk=1.68U [TrendFollowing / TRENDING] |
| 05:30:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2299.8900 |
| 05:30:02 | SIGNAL | 🔔 Signal LONG ETHUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:02 | SIGNAL | 💰 Orchestrator ETHUSDT: score=0.264 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 05:30:02 | TRADE | ⚡ PAPER_SPEED market-fill override ETHUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:02 | TRADE | ✅ Opened LONG ETHUSDT qty=0.054774 risk=1.68U [TrendFollowing / TRENDING] |
| 05:30:17 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:17 | FILTER | ⚡ PAPER_SPEED bypass ORCAUSDT: SLEEP_MODE(vol=256=5%_of_avg=5158,min=10%[base=45%×0.20]) |
| 05:30:17 | SIGNAL | 🔔 Signal LONG ORCAUSDT / EMA cross UP / trend↑ / RSI=57.1 / ATR=0.0076 |
| 05:30:17 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.332 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 05:30:17 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:17 | TRADE | ✅ Opened LONG ORCAUSDT qty=64.901431 risk=1.68U [TrendFollowing / TRENDING] |
| 05:31:05 | TRADE | Position closed [TSL+] PENDLEUSDT @ 1.533 |
| 05:31:29 | TRADE | Position closed [SL] ETHUSDT @ 2300.28 |
| 05:31:41 | TRADE | Position closed [TSL+] ORCAUSDT @ 1.946 |
| 05:32:27 | TRADE | Position closed [SL] MEGAUSDT @ 0.152 |
| 05:33:37 | TRADE | Position closed [SL] CHIPUSDT @ 0.06532 |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 839.07 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': '05ae9845', 'symbol': 'SOLUSDT', 'side': 'LONG', 'entry_price': 83.65, 'qty': 0.754081, 'stop_loss': 83.66231999999997, 'take_profit': 84.31920000000001, 'entry_ts': 1777697762979, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 83.72, 'initial_risk': 1.6821, 'initial_stop_loss': 83.38232, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.2615062761506035, 'ticks_since_peak': 148}, {'position_id': '780ce632', 'symbol': 'TRXUSDT', 'side': 'LONG', 'entry_price': 0.3285, 'qty': 383.481517, 'stop_loss': 0.32744880000000004, 'take_profit': 0.33112800000000003, 'entry_ts': 1777699801009, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 0.3285, 'initial_risk': 1.6796, 'initial_stop_loss': 0.32744880000000004, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.0, 'ticks_since_peak': 375}, {'position_id': '2cb7a276', 'symbol': 'XRPUSDT', 'side': 'SHORT', 'entry_price': 1.3834, 'qty': 91.060921, 'stop_loss': 1.38772688, 'take_profit': 1.3723328, 'entry_ts': 1777699801220, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 1.3833, 'initial_risk': 1.6796, 'initial_stop_loss': 1.38782688, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.022589272806127225, 'ticks_since_peak': 143}, {'position_id': 'afb7007a', 'symbol': 'BTCUSDT', 'side': 'SHORT', 'entry_price': 78110.64, 'qty': 0.001613, 'stop_loss': 78360.594048, 'take_profit': 77485.75488, 'entry_ts': 1777699801535, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 78110.64, 'initial_risk': 1.6796, 'initial_stop_loss': 78360.594048, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.0, 'ticks_since_peak': 2478}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| SOLUSDT | LONG | 0.754081 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| TRXUSDT | LONG | 383.481517 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| XRPUSDT | SHORT | 91.060921 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| BTCUSDT | SHORT | 0.001613 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| SOLUSDT | SHORT | -0.06 | -0.005 | MEAN_REVERTING | MARKET |
| TRXUSDT | LONG | -0.02 | -0.002 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.58 | -0.345 | TRENDING | MARKET |
| ORCAUSDT | SHORT | +0.07 | 0.045 | TRENDING | MARKET |
| CHIPUSDT | LONG | -0.00 | -0.001 | MEAN_REVERTING | MARKET |
| MEGAUSDT | SHORT | -0.22 | -0.133 | TRENDING | MARKET |
| BTCUSDT | SHORT | -0.08 | -0.047 | TRENDING | MARKET |
| PENDLEUSDT | LONG | -0.29 | -0.174 | TRENDING | MARKET |
| MEGAUSDT | SHORT | -0.02 | -0.013 | TRENDING | MARKET |
| ORCAUSDT | SHORT | -0.32 | -0.189 | TRENDING | MARKET |
| CHIPUSDT | SHORT | +0.01 | 0.005 | MEAN_REVERTING | MARKET |
| BNBUSDT | LONG | -0.07 | -0.040 | MEAN_REVERTING | MARKET |
| TRXUSDT | LONG | +0.03 | 0.016 | TRENDING | MARKET |
| XRPUSDT | SHORT | -0.04 | -0.025 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.29 | -0.172 | MEAN_REVERTING | MARKET |
| PENDLEUSDT | SHORT | +0.12 | 0.069 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.16 | -0.092 | TRENDING | MARKET |
| ORCAUSDT | LONG | +0.15 | 0.088 | TRENDING | MARKET |
| MEGAUSDT | SHORT | -0.26 | -0.154 | TRENDING | MARKET |
| CHIPUSDT | SHORT | -0.60 | -0.359 | MEAN_REVERTING | MARKET |


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
| regimes | {'TRENDING': {'n_trades': 22, 'win_rate': 0.318, 'weight': 0.5}, 'MEAN_REVERTING': {'n_trades': 14, 'win_rate': 0.143, 'weight': 0.5}} |


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
| strategies | {'TRENDING@TrendFollowing_PAPER_SPEED': {'n_trades': 21, 'edge': -0.1519, 'win_rate': 0.286, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 636.3}, 'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 13, 'edge': -0.1293, 'win_rate': 0.077, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'MEAN_REVERTING@MR_BB_RSI_v1': {'n_trades': 1, 'edge': 0.0083, 'win_rate': 1.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@TF_EMA_RSI_v1': {'n_trades': 1, 'edge': 0.1479, 'win_rate': 1.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.6111 |
| MeanReversion | 0.3889 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 25 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.37 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (26.3% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Low win rate (38.6% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 155.9575 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.369 (negative expectancy)
-   Detail — 324 trades; win_rate=38.6%. Every trade destroys capital on average. Immediate action required.
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


