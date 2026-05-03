# EOW Quant Engine — Full System Report

_Generated: 2026-05-03 16:26:26 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **441** trades with a net **LOSS** of **-168.47 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 35.6% |
| Profit Factor | 0.482 |
| Sharpe | -2.237 |
| Max Drawdown | 19.16% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 831.53 |
| Net PnL (USDT) | -168.4658 |
| Total Trades | 441 |
| Win Rate | 35.6% |
| Profit Factor | 0.482 |
| Sharpe | -2.237 |
| Sortino | -2.040 |
| Calmar | -0.502 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.9988 |
| Avg Loss | -1.1453 |
| Fees Paid | 71.0665 |
| Slippage | 14.8493 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 147.00 |
| Trades / hour | 2.00 |
| Rejection Rate | 95.5% |
| Signals total | 147 |
| Trades total | 2 |
| Skips total | 42 |
| Mins since trade | 29.8 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 16:23:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:23:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78622.3200 rsi=51.2 |
| 16:23:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:23:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:23:02 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=35.5 above_sma=False regime=MEAN_REVERTING) |
| 16:23:06 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:23:06 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=49.5 above_sma=False regime=MEAN_REVERTING) |
| 16:24:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:24:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=53.7 above_sma=False regime=MEAN_REVERTING) |
| 16:24:02 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:24:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=55.6 above_sma=False regime=MEAN_REVERTING) |
| 16:24:03 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:24:03 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2325.3200 rsi=46.9 |
| 16:24:03 | SIGNAL | 🔔 Signal SHORT ETHUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:25:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:25:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78653.5000 rsi=60.0 |
| 16:25:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:25:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:25:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=53.5 above_sma=False regime=MEAN_REVERTING) |
| 16:25:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:25:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=65.2 above_sma=False regime=MEAN_REVERTING) |
| 16:26:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:26:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=62.2 above_sma=True regime=TRENDING) |
| 16:26:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:26:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=60.9 above_sma=True regime=MEAN_REVERTING) |
| 16:26:04 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:26:04 | SIGNAL | 🔔 Signal SHORT LUNCUSDT / BB upper touch / RSI=73.2 / Mean=0.0001 / TP=0.0001 |
| 16:26:04 | SIGNAL | 💰 Orchestrator LUNCUSDT: score=0.288 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fals |
| 16:26:04 | TRADE | ⚡ PAPER_SPEED market-fill override LUNCUSDT: USE_LIMIT_ORDERS bypassed |
| 16:26:04 | TRADE | ✅ Opened SHORT LUNCUSDT qty=1970693.861373 risk=4.16U [MeanReversion / MEAN_REVERTING] |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 831.53 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': '59ecaef3', 'symbol': 'BIOUSDT', 'side': 'LONG', 'entry_price': 0.0601, 'qty': 2400.305123, 'stop_loss': 0.058367857142857145, 'take_profit': 0.06702857142857144, 'entry_ts': 1777824180881, 'strategy_id': 'ALPHA_PBE_v1', 'trailing_sl': True, 'peak_price': 0.0606, 'initial_risk': 4.1577, 'initial_stop_loss': 0.058367857142857145, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.28865979381443346, 'ticks_since_peak': 918}, {'position_id': '2c6bf5af', 'symbol': 'LUNCUSDT', 'side': 'SHORT', 'entry_price': 8.439e-05, 'qty': 1970693.861373, 'stop_loss': 8.452329230769231e-05, 'take_profit': 8.394947368421053e-05, 'entry_ts': 1777825564123, 'strategy_id': 'MR_BB_RSI_v1', 'trailing_sl': True, 'peak_price': 8.439e-05, 'initial_risk': 4.1577, 'initial_stop_loss': 8.452329230769231e-05, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.0, 'ticks_since_peak': 56}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| BIOUSDT | LONG | 2,400.305123 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| LUNCUSDT | SHORT | 1,970,693.861373 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| BIOUSDT | LONG | -0.83 | -0.196 | TRENDING | MARKET |
| ORCAUSDT | SHORT | +0.37 | 0.088 | TRENDING | MARKET |
| ORDIUSDT | SHORT | -0.95 | -0.224 | TRENDING | MARKET |
| BIOUSDT | LONG | -0.84 | -0.199 | MEAN_REVERTING | MARKET |
| ORDIUSDT | SHORT | -0.91 | -0.216 | TRENDING | MARKET |
| ORCAUSDT | SHORT | -0.15 | -0.037 | TRENDING | MARKET |
| BIOUSDT | LONG | +4.63 | 1.098 | MEAN_REVERTING | MARKET |
| ORDIUSDT | SHORT | -0.40 | -0.096 | MEAN_REVERTING | MARKET |
| ORCAUSDT | LONG | -0.48 | -0.114 | TRENDING | MARKET |
| ETHUSDT | SHORT | -0.78 | -0.184 | TRENDING | MARKET |
| BIOUSDT | SHORT | -2.92 | -0.690 | MEAN_REVERTING | MARKET |
| ORDIUSDT | LONG | -0.10 | -0.024 | TRENDING | MARKET |
| ORCAUSDT | SHORT | -0.81 | -0.192 | TRENDING | MARKET |
| ORCAUSDT | SHORT | -0.56 | -0.133 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | -1.28 | -0.304 | TRENDING | MARKET |
| ORCAUSDT | LONG | -0.72 | -0.171 | TRENDING | MARKET |
| ORDIUSDT | SHORT | -0.70 | -0.166 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -1.55 | -0.369 | TRENDING | MARKET |
| LUNCUSDT | LONG | -0.67 | -0.053 | TRENDING | MARKET |
| BIOUSDT | LONG | -3.73 | -0.298 | TRENDING | MARKET |


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
| regimes | {'TRENDING': {'n_trades': 2, 'win_rate': 0.0, 'weight': 1.0}} |


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
| strategies | {'TRENDING@ALPHA_PBE_v1': {'n_trades': 1, 'edge': -0.6669, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@ALPHA_TCB_v1': {'n_trades': 1, 'edge': -3.7315, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


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
| CT-001 | CRITICAL | Low profit factor (0.48 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (29.7% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (TrendFollowing dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (35.6% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 33.3934 |
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
-   Detail — 441 trades; win_rate=35.6%. Every trade destroys capital on average. Immediate action required.
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


