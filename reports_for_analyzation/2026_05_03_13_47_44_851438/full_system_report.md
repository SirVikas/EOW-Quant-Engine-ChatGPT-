# EOW Quant Engine — Full System Report

_Generated: 2026-05-03 08:16:26 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **374** trades with a net **LOSS** of **-165.10 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 36.9% |
| Profit Factor | 0.386 |
| Sharpe | -2.544 |
| Max Drawdown | 18.65% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 834.90 |
| Net PnL (USDT) | -165.0988 |
| Total Trades | 374 |
| Win Rate | 36.9% |
| Profit Factor | 0.386 |
| Sharpe | -2.544 |
| Sortino | -2.203 |
| Calmar | -0.596 |
| Max Drawdown | 18.65% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.7523 |
| Avg Loss | -1.1395 |
| Fees Paid | 62.7503 |
| Slippage | 8.6122 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 31.00 |
| Trades / hour | 5.00 |
| Rejection Rate | 0.0% |
| Signals total | 31 |
| Trades total | 5 |
| Skips total | 0 |
| Mins since trade | 8.8 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 08:05:01 | SIGNAL | 💰 Orchestrator ORDIUSDT: score=0.589 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 08:05:01 | TRADE | ⚡ PAPER_SPEED market-fill override ORDIUSDT: USE_LIMIT_ORDERS bypassed |
| 08:05:01 | TRADE | ✅ Opened LONG ORDIUSDT qty=31.824354 risk=12.54U [TrendFollowing / TRENDING] |
| 08:05:03 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=22.2 above_sma=False regime=TRENDING) |
| 08:06:02 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=23.5 above_sma=False regime=TRENDING) |
| 08:06:23 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #4: meta_score=85.0 verdict=BLOCKED |
| 08:07:08 | SIGNAL | ⚡ ALPHA TrendBreakout BIOUSDT score=0.730 rr=5.00 |
| 08:07:08 | SIGNAL | 🔔 Signal SHORT BIOUSDT / TCB: ADX=51.7 VOL=1.3x RR=5.00 SCORE=0.730 |
| 08:07:08 | SIGNAL | 💰 Orchestrator BIOUSDT: score=0.745 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 08:07:08 | TRADE | ⚡ PAPER_SPEED market-fill override BIOUSDT: USE_LIMIT_ORDERS bypassed |
| 08:07:08 | TRADE | ✅ Opened SHORT BIOUSDT qty=3203.163945 risk=12.54U [TrendFollowing / TRENDING] |
| 08:07:40 | TRADE | Position closed [SL] ORDIUSDT @ 5.226 |
| 08:09:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 08:10:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=63.4 above_sma=True regime=MEAN_REVERTING) |
| 08:11:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=63.8 above_sma=True regime=MEAN_REVERTING) |
| 08:11:23 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #5: meta_score=85.0 verdict=BLOCKED |
| 08:12:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=63.4 above_sma=True regime=TRENDING) |
| 08:13:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 08:13:01 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=49.3 |
| 08:13:01 | SIGNAL | 🔔 Signal SHORT LUNCUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 08:13:01 | SIGNAL | 💰 Orchestrator LUNCUSDT: score=0.748 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 08:13:01 | TRADE | ⚡ PAPER_SPEED market-fill override LUNCUSDT: USE_LIMIT_ORDERS bypassed |
| 08:13:01 | TRADE | ✅ Opened SHORT LUNCUSDT qty=1947973.038450 risk=25.05U [TrendFollowing / TRENDING] |
| 08:13:02 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 08:13:02 | SIGNAL | ⚡ PAPER_SPEED fallback ORDIUSDT: LONG entry=5.1750 rsi=23.1 |
| 08:13:02 | SIGNAL | 🔔 Signal LONG ORDIUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 08:13:02 | SIGNAL | 💰 Orchestrator ORDIUSDT: score=0.585 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 08:13:02 | TRADE | ⚡ PAPER_SPEED market-fill override ORDIUSDT: USE_LIMIT_ORDERS bypassed |
| 08:13:02 | TRADE | ✅ Opened LONG ORDIUSDT qty=32.266715 risk=25.05U [MeanReversion / MEAN_REVERTING] |
| 08:16:23 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #6: meta_score=85.0 verdict=BLOCKED |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 834.90 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': '07ab5ece', 'symbol': 'BTCUSDT', 'side': 'LONG', 'entry_price': 78400.57, 'qty': 0.002119, 'stop_loss': 78149.688176, 'take_profit': 79027.77456, 'entry_ts': 1777794387600, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 78505.92, 'initial_risk': 12.4611, 'initial_stop_loss': 78149.688176, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.41991882201871533, 'ticks_since_peak': 1410}, {'position_id': '2986bc00', 'symbol': 'ETHUSDT', 'side': 'LONG', 'entry_price': 2311.35, 'qty': 0.071884, 'stop_loss': 2303.95368, 'take_profit': 2329.8408, 'entry_ts': 1777794390580, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 2312.67, 'initial_risk': 12.4611, 'initial_stop_loss': 2303.95368, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.17846712959961084, 'ticks_since_peak': 645}, {'position_id': '2626da3d', 'symbol': 'ORCAUSDT', 'side': 'SHORT', 'entry_price': 2.059, 'qty': 80.924811, 'stop_loss': 2.0638000000000005, 'take_profit': 2.0309999999999997, 'entry_ts': 1777795413333, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 2.047, 'initial_risk': 12.4968, 'initial_stop_loss': 2.0702000000000003, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 1.071428571428563, 'ticks_since_peak': 86}, {'position_id': '76588708', 'symbol': 'BIOUSDT', 'side': 'SHORT', 'entry_price': 0.0522, 'qty': 3203.163945, 'stop_loss': 0.0526, 'take_profit': 0.0497, 'entry_ts': 1777795628449, 'strategy_id': 'ALPHA_TCB_v1', 'trailing_sl': True, 'peak_price': 0.0521, 'initial_risk': 12.5404, 'initial_stop_loss': 0.0526, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.25000000000000866, 'ticks_since_peak': 415}, {'position_id': '8615da83', 'symbol': 'LUNCUSDT', 'side': 'SHORT', 'entry_price': 8.572e-05, 'qty': 1947973.03845, 'stop_loss': 8.649000000000002e-05, 'take_profit': 8.303999999999998e-05, 'entry_ts': 1777795981530, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 8.448e-05, 'initial_risk': 25.047, 'initial_stop_loss': 8.706000000000001e-05, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.9253731343283469, 'ticks_since_peak': 1317}, {'position_id': 'ae1c717f', 'symbol': 'ORDIUSDT', 'side': 'LONG', 'entry_price': 5.175, 'qty': 32.266715, 'stop_loss': 5.1730523999999996, 'take_profit': 5.253246, 'entry_ts': 1777795982464, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 5.22, 'initial_risk': 25.047, 'initial_stop_loss': 5.1437016, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 1.4377731769036168, 'ticks_since_peak': 1}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| BTCUSDT | LONG | 0.002119 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| ETHUSDT | LONG | 0.071884 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| ORCAUSDT | SHORT | 80.924811 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| BIOUSDT | SHORT | 3,203.163945 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| LUNCUSDT | SHORT | 1,947,973.038450 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| ORDIUSDT | LONG | 32.266715 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| PENDLEUSDT | SHORT | -0.12 | -0.010 | TRENDING | MARKET |
| WLFIUSDT | LONG | -1.15 | -0.092 | TRENDING | MARKET |
| MEGAUSDT | SHORT | -0.26 | -0.063 | TRENDING | MARKET |
| PENDLEUSDT | SHORT | -0.01 | -0.002 | TRENDING | MARKET |
| WLFIUSDT | LONG | -0.93 | -0.075 | TRENDING | LIMIT |
| MEGAUSDT | LONG | -0.46 | -0.037 | MEAN_REVERTING | LIMIT |
| PENDLEUSDT | SHORT | +0.53 | 0.128 | TRENDING | LIMIT |
| MEGAUSDT | SHORT | +1.18 | 0.094 | TRENDING | LIMIT |
| WLFIUSDT | LONG | -0.62 | -0.049 | TRENDING | LIMIT |
| MEGAUSDT | SHORT | -0.85 | -0.204 | TRENDING | LIMIT |
| PENDLEUSDT | LONG | -0.24 | -0.057 | TRENDING | LIMIT |
| MEGAUSDT | SHORT | +1.11 | 0.267 | TRENDING | LIMIT |
| WLFIUSDT | LONG | -2.41 | -0.579 | TRENDING | LIMIT |
| PENDLEUSDT | LONG | -0.31 | -0.074 | TRENDING | LIMIT |
| ORCAUSDT | LONG | -0.65 | -0.052 | MEAN_REVERTING | LIMIT |
| BIOUSDT | SHORT | +1.63 | 0.131 | MEAN_REVERTING | MARKET |
| ORCAUSDT | SHORT | +1.86 | 0.149 | TRENDING | MARKET |
| ORDIUSDT | LONG | -1.12 | -0.090 | TRENDING | MARKET |
| LUNCUSDT | LONG | +2.90 | 0.233 | MEAN_REVERTING | MARKET |
| ORDIUSDT | LONG | -1.12 | -0.090 | TRENDING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 2, 'win_rate': 1.0, 'weight': 1.0}, 'TRENDING': {'n_trades': 3, 'win_rate': 0.333, 'weight': 1.0}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 2, 'edge': 2.2685, 'win_rate': 1.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@TrendFollowing_PAPER_SPEED': {'n_trades': 2, 'edge': 0.3686, 'win_rate': 0.5, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@ALPHA_TCB_v1': {'n_trades': 1, 'edge': -1.1159, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.6 |
| MeanReversion | 0.4 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 25 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.39 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (27.5% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Low win rate (36.9% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 162.4382 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.386 (negative expectancy)
-   Detail — 374 trades; win_rate=36.9%. Every trade destroys capital on average. Immediate action required.
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


