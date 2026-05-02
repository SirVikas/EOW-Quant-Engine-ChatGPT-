# EOW Quant Engine — Full System Report

_Generated: 2026-05-02 03:28:47 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **288** trades with a net **LOSS** of **-156.21 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 40.3% |
| Profit Factor | 0.374 |
| Sharpe | -2.764 |
| Max Drawdown | 17.37% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 843.79 |
| Net PnL (USDT) | -156.2127 |
| Total Trades | 288 |
| Win Rate | 40.3% |
| Profit Factor | 0.374 |
| Sharpe | -2.764 |
| Sortino | -2.318 |
| Calmar | -0.787 |
| Max Drawdown | 17.37% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.8060 |
| Avg Loss | -1.4518 |
| Fees Paid | 54.5353 |
| Slippage | 2.9748 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 59.00 |
| Trades / hour | 17.00 |
| Rejection Rate | 69.6% |
| Signals total | 59 |
| Trades total | 17 |
| Skips total | 39 |
| Mins since trade | 6.4 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 03:18:01 | SIGNAL | 🔔 Signal LONG MEGAUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:18:01 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:18:01 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:18:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: SHORT entry=1.5320 |
| 03:18:01 | SIGNAL | 🔔 Signal SHORT PENDLEUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:18:31 | TRADE | Position closed [TSL+] ORCAUSDT @ 1.967 |
| 03:19:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78289.0500 |
| 03:19:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:19:00 | SIGNAL | 💰 Orchestrator BTCUSDT: score=0.213 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 03:19:00 | TRADE | ⚡ PAPER_SPEED market-fill override BTCUSDT: USE_LIMIT_ORDERS bypassed |
| 03:19:00 | TRADE | ✅ Opened SHORT BTCUSDT qty=0.001618 risk=1.69U [TrendFollowing / TRENDING] |
| 03:19:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0664 |
| 03:19:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:19:00 | SIGNAL | 💰 Orchestrator CHIPUSDT: score=0.348 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 03:19:00 | TRADE | ⚡ PAPER_SPEED market-fill override CHIPUSDT: USE_LIMIT_ORDERS bypassed |
| 03:19:00 | TRADE | ✅ Opened LONG CHIPUSDT qty=1908.256753 risk=1.69U [TrendFollowing / TRENDING] |
| 03:19:01 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1534 |
| 03:19:01 | SIGNAL | 🔔 Signal LONG MEGAUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:19:01 | SIGNAL | 💰 Orchestrator MEGAUSDT: score=0.248 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 03:19:01 | TRADE | ⚡ PAPER_SPEED market-fill override MEGAUSDT: USE_LIMIT_ORDERS bypassed |
| 03:19:01 | TRADE | ✅ Opened LONG MEGAUSDT qty=825.733477 risk=1.69U [TrendFollowing / TRENDING] |
| 03:19:02 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=615.8200 |
| 03:19:02 | SIGNAL | 🔔 Signal SHORT BNBUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:19:02 | SIGNAL | 💰 Orchestrator BNBUSDT: score=0.229 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 03:19:02 | TRADE | ⚡ PAPER_SPEED market-fill override BNBUSDT: USE_LIMIT_ORDERS bypassed |
| 03:19:02 | TRADE | ✅ Opened SHORT BNBUSDT qty=0.205662 risk=1.69U [MeanReversion / MEAN_REVERTING] |
| 03:19:47 | TRADE | Position closed [BE] CHIPUSDT @ 0.06646 |
| 03:21:51 | TRADE | Position closed [SL] MEGAUSDT @ 0.15312 |
| 03:22:22 | TRADE | Position closed [SL] ETHUSDT @ 2304.17 |
| 03:22:38 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #4: meta_score=55.0 verdict=BLOCKED |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 843.79 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': 'a8913de9', 'symbol': 'TRXUSDT', 'side': 'LONG', 'entry_price': 0.3271, 'qty': 388.323724, 'stop_loss': 0.32635327999999997, 'take_profit': 0.3297168, 'entry_ts': 1777690968329, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 0.3273, 'initial_risk': 10.5851, 'initial_stop_loss': 0.32605328, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.1910730663405474, 'ticks_since_peak': 258}, {'position_id': 'ca90bd2f', 'symbol': 'BTCUSDT', 'side': 'SHORT', 'entry_price': 78289.05, 'qty': 0.001618, 'stop_loss': 78539.57496, 'take_profit': 77662.73760000001, 'entry_ts': 1777691940488, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 78289.05, 'initial_risk': 1.6887, 'initial_stop_loss': 78539.57496, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.0, 'ticks_since_peak': 2413}, {'position_id': '67875e56', 'symbol': 'BNBUSDT', 'side': 'SHORT', 'entry_price': 615.82, 'qty': 0.205662, 'stop_loss': 617.7906240000001, 'take_profit': 610.89344, 'entry_ts': 1777691942554, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 615.82, 'initial_risk': 1.6887, 'initial_stop_loss': 617.7906240000001, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.0, 'ticks_since_peak': 491}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| TRXUSDT | LONG | 388.323724 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| BTCUSDT | SHORT | 0.001618 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| BNBUSDT | SHORT | 0.205662 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| PENGUUSDT | SHORT | -0.05 | -0.030 | TRENDING | MARKET |
| PENDLEUSDT | SHORT | -0.01 | -0.005 | TRENDING | MARKET |
| SOLUSDT | SHORT | -0.04 | -0.026 | TRENDING | MARKET |
| ETHUSDT | LONG | -0.15 | -0.014 | TRENDING | MARKET |
| BTCUSDT | SHORT | -0.16 | -0.015 | TRENDING | MARKET |
| CHIPUSDT | SHORT | -0.76 | -0.071 | MEAN_REVERTING | MARKET |
| MEGAUSDT | SHORT | +0.08 | 0.008 | TRENDING | MARKET |
| BNBUSDT | SHORT | -0.13 | -0.013 | TRENDING | MARKET |
| SOLUSDT | SHORT | -0.06 | -0.005 | MEAN_REVERTING | MARKET |
| BTCUSDT | SHORT | -0.16 | -0.096 | MEAN_REVERTING | MARKET |
| PENDLEUSDT | SHORT | -0.34 | -0.032 | TRENDING | MARKET |
| XRPUSDT | SHORT | -0.09 | -0.008 | TRENDING | MARKET |
| BNBUSDT | SHORT | -0.07 | -0.040 | MEAN_REVERTING | MARKET |
| CHIPUSDT | SHORT | -0.00 | -0.003 | TRENDING | MARKET |
| MEGAUSDT | SHORT | -0.80 | -0.475 | TRENDING | MARKET |
| SOLUSDT | SHORT | -0.03 | -0.017 | TRENDING | MARKET |
| ORCAUSDT | SHORT | +0.21 | 0.020 | TRENDING | MARKET |
| CHIPUSDT | LONG | -0.01 | -0.003 | TRENDING | MARKET |
| MEGAUSDT | LONG | -0.39 | -0.232 | TRENDING | MARKET |
| ETHUSDT | LONG | -0.16 | -0.015 | TRENDING | MARKET |


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
| regimes | {'TRENDING': {'n_trades': 13, 'win_rate': 0.154, 'weight': 0.5}, 'MEAN_REVERTING': {'n_trades': 4, 'win_rate': 0.0, 'weight': 1.0}} |


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
| strategies | {'TRENDING@TrendFollowing_PAPER_SPEED': {'n_trades': 11, 'edge': -0.1062, 'win_rate': 0.182, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 4, 'edge': -0.2602, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@ALPHA_PBE_v1': {'n_trades': 2, 'edge': -0.4043, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.7647 |
| MeanReversion | 0.2353 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 45 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.37 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (25.9% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| Generation | 480 |
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
| daily_risk_used | 131.6328 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.374 (negative expectancy)
-   Detail — 288 trades; win_rate=40.3%. Every trade destroys capital on average. Immediate action required.
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


