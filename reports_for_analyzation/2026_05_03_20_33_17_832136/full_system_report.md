# EOW Quant Engine — Full System Report

_Generated: 2026-05-03 14:55:36 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **432** trades with a net **LOSS** of **-158.78 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 36.1% |
| Profit Factor | 0.496 |
| Sharpe | -2.135 |
| Max Drawdown | 19.16% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 841.22 |
| Net PnL (USDT) | -158.7847 |
| Total Trades | 432 |
| Win Rate | 36.1% |
| Profit Factor | 0.496 |
| Sharpe | -2.135 |
| Sortino | -1.943 |
| Calmar | -0.483 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0033 |
| Avg Loss | -1.1424 |
| Fees Paid | 69.9263 |
| Slippage | 13.9942 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 97.00 |
| Trades / hour | 5.00 |
| Rejection Rate | 66.7% |
| Signals total | 97 |
| Trades total | 5 |
| Skips total | 10 |
| Mins since trade | 3.7 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 14:28:11 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:28:11 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=50.7 above_sma=True regime=MEAN_REVERTING) |
| 14:29:02 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:29:02 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=50.7 above_sma=True regime=MEAN_REVERTING) |
| 14:30:07 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:30:07 | SIGNAL | ⚡ PAPER_SPEED fallback ORDIUSDT: LONG entry=5.0550 rsi=46.4 |
| 14:30:07 | SIGNAL | 🔔 Signal LONG ORDIUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:07 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORDIUSDT |
| 14:30:07 | SIGNAL | 💰 Orchestrator ORDIUSDT: score=0.146 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 14:30:07 | TRADE | ⚡ PAPER_SPEED market-fill override ORDIUSDT: USE_LIMIT_ORDERS bypassed |
| 14:30:07 | TRADE | ✅ Opened LONG ORDIUSDT qty=33.453178 risk=4.23U [TrendFollowing / TRENDING] |
| 14:34:39 | TRADE | Position closed [SL] ORCAUSDT @ 2.063 |
| 14:40:11 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:40:11 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0630 rsi=40.0 |
| 14:40:11 | SIGNAL | 🔔 Signal SHORT ORCAUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:40:11 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.624 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 14:40:11 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 14:40:11 | TRADE | ✅ Opened SHORT ORCAUSDT qty=81.924086 risk=4.23U [TrendFollowing / TRENDING] |
| 14:43:40 | TRADE | Position closed [SL] ORCAUSDT @ 2.07 |
| 14:49:02 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:49:02 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0720 rsi=75.0 |
| 14:49:02 | SIGNAL | 🔔 Signal SHORT ORCAUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:49:02 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.156 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 14:49:02 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 14:49:02 | TRADE | ✅ Opened SHORT ORCAUSDT qty=81.490006 risk=4.22U [MeanReversion / MEAN_REVERTING] |
| 14:49:44 | TRADE | Position closed [SL] BIOUSDT @ 0.0577 |
| 14:51:55 | TRADE | Position closed [SL] ORDIUSDT @ 5.059 |
| 14:55:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 14:55:01 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.540 |
| 14:55:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=TRENDING) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 841.22 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': 'e617cf7e', 'symbol': 'BTCUSDT', 'side': 'LONG', 'entry_price': 78668.42, 'qty': 0.002142, 'stop_loss': 78501.16158399999, 'take_profit': 79297.76736, 'entry_ts': 1777809361002, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 78878.77, 'initial_risk': 12.6366, 'initial_stop_loss': 78416.68105599999, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.8355878381693544, 'ticks_since_peak': 39756}, {'position_id': '5b1c5b29', 'symbol': 'LUNCUSDT', 'side': 'SHORT', 'entry_price': 8.504e-05, 'qty': 1981283.861742, 'stop_loss': 8.476517857142856e-05, 'take_profit': 8.033285714285713e-05, 'entry_ts': 1777809661520, 'strategy_id': 'ALPHA_TCB_v1', 'trailing_sl': True, 'peak_price': 8.3e-05, 'initial_risk': 12.6366, 'initial_stop_loss': 8.621678571428571e-05, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 1.7335356600910525, 'ticks_since_peak': 7093}, {'position_id': 'cae59430', 'symbol': 'BABYUSDT', 'side': 'SHORT', 'entry_price': 0.02201, 'qty': 2488.062027, 'stop_loss': 0.022762321428571427, 'take_profit': 0.01861714285714286, 'entry_ts': 1777813381246, 'strategy_id': 'ALPHA_TCB_v1', 'trailing_sl': True, 'peak_price': 0.02149, 'initial_risk': 4.2208, 'initial_stop_loss': 0.022858214285714284, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.6130526315789471, 'ticks_since_peak': 7111}, {'position_id': '4b329bf7', 'symbol': 'ETHUSDT', 'side': 'SHORT', 'entry_price': 2322.87, 'qty': 0.0728, 'stop_loss': 2330.303184, 'take_profit': 2304.2870399999997, 'entry_ts': 1777818182560, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 2322.87, 'initial_risk': 4.2276, 'initial_stop_loss': 2330.303184, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.0, 'ticks_since_peak': 4083}, {'position_id': '0f15c3d6', 'symbol': 'ORCAUSDT', 'side': 'SHORT', 'entry_price': 2.072, 'qty': 81.490006, 'stop_loss': 2.0759455999999994, 'take_profit': 2.055424, 'entry_ts': 1777819742940, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 2.066, 'initial_risk': 4.2212, 'initial_stop_loss': 2.0786303999999998, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.9049227799228547, 'ticks_since_peak': 20}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| BTCUSDT | LONG | 0.002142 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| LUNCUSDT | SHORT | 1,981,283.861742 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| BABYUSDT | SHORT | 2,488.062027 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| ETHUSDT | SHORT | 0.072800 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| ORCAUSDT | SHORT | 81.490006 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| ORDIUSDT | LONG | -0.40 | -0.095 | TRENDING | MARKET |
| ORCAUSDT | LONG | -0.40 | -0.094 | TRENDING | MARKET |
| BIOUSDT | LONG | -1.29 | -0.308 | TRENDING | MARKET |
| ORDIUSDT | SHORT | +0.54 | 0.129 | TRENDING | MARKET |
| BABYUSDT | SHORT | +7.86 | 1.867 | MEAN_REVERTING | MARKET |
| ORCAUSDT | SHORT | -0.12 | -0.028 | TRENDING | MARKET |
| BIOUSDT | LONG | -1.14 | -0.273 | TRENDING | MARKET |
| BIOUSDT | LONG | -0.83 | -0.196 | TRENDING | MARKET |
| ORCAUSDT | SHORT | +0.37 | 0.088 | TRENDING | MARKET |
| ORDIUSDT | SHORT | -0.95 | -0.224 | TRENDING | MARKET |
| BIOUSDT | LONG | -0.84 | -0.199 | MEAN_REVERTING | MARKET |
| ORDIUSDT | SHORT | -0.91 | -0.216 | TRENDING | MARKET |
| ORDIUSDT | SHORT | -0.40 | -0.096 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.38 | -0.091 | TRENDING | MARKET |
| ORCAUSDT | SHORT | -0.15 | -0.037 | TRENDING | MARKET |
| BIOUSDT | LONG | +4.63 | 1.098 | MEAN_REVERTING | MARKET |
| ORCAUSDT | LONG | -0.48 | -0.114 | TRENDING | MARKET |
| ORCAUSDT | SHORT | -0.81 | -0.192 | TRENDING | MARKET |
| BIOUSDT | SHORT | -2.92 | -0.690 | MEAN_REVERTING | MARKET |
| ORDIUSDT | LONG | -0.10 | -0.024 | TRENDING | MARKET |


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
| regimes | {'TRENDING': {'n_trades': 23, 'win_rate': 0.217, 'weight': 0.5}, 'MEAN_REVERTING': {'n_trades': 6, 'win_rate': 0.333, 'weight': 0.5}} |


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
| strategies | {'TRENDING@TrendFollowing_PAPER_SPEED': {'n_trades': 19, 'edge': -0.5665, 'win_rate': 0.211, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 10097.6}, 'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 4, 'edge': 2.1722, 'win_rate': 0.5, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@ALPHA_TCB_v1': {'n_trades': 3, 'edge': -0.1942, 'win_rate': 0.333, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@TF_EMA_RSI_v1': {'n_trades': 1, 'edge': -0.8292, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'MEAN_REVERTING@MR_BB_RSI_v1': {'n_trades': 1, 'edge': -0.8393, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'MEAN_REVERTING@ALPHA_PBE_v1': {'n_trades': 1, 'edge': -0.4029, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.7931 |
| MeanReversion | 0.2069 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 25 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.50 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (30.6% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Low win rate (36.1% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 219.306 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.496 (negative expectancy)
-   Detail — 432 trades; win_rate=36.1%. Every trade destroys capital on average. Immediate action required.
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


