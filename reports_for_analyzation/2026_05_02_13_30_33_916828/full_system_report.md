# EOW Quant Engine — Full System Report

_Generated: 2026-05-02 07:58:46 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **357** trades with a net **LOSS** of **-165.57 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 37.0% |
| Profit Factor | 0.364 |
| Sharpe | -2.626 |
| Max Drawdown | 18.29% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 834.43 |
| Net PnL (USDT) | -165.5718 |
| Total Trades | 357 |
| Win Rate | 37.0% |
| Profit Factor | 0.364 |
| Sharpe | -2.626 |
| Sortino | -2.265 |
| Calmar | -0.639 |
| Max Drawdown | 18.29% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.7167 |
| Avg Loss | -1.1563 |
| Fees Paid | 61.2534 |
| Slippage | 8.0134 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 187.00 |
| Trades / hour | 10.00 |
| Rejection Rate | 86.5% |
| Signals total | 187 |
| Trades total | 10 |
| Skips total | 64 |
| Mins since trade | 24.9 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 07:57:02 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0102 rsi=48.4 |
| 07:57:02 | SIGNAL | 🔔 Signal LONG PENGUUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:57:09 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:57:09 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:57:09 | SIGNAL | ⚡ ALPHA PullbackEntry WLFIUSDT score=0.666 rr=5.00 |
| 07:57:09 | SIGNAL | 🔔 Signal SHORT WLFIUSDT / PBE: EMA_DIST=0.05% RSI=57.1 RR=5.00 SCORE=0.666 |
| 07:58:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=45.9 above_sma=True regime=MEAN_REVERTING) |
| 07:58:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:00 | SIGNAL | ⚡ ALPHA PullbackEntry MEGAUSDT score=0.509 rr=5.00 |
| 07:58:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT / PBE: EMA_DIST=0.02% RSI=42.9 RR=5.00 SCORE=0.509 |
| 07:58:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:00 | FILTER | ⚡ PAPER_SPEED XRPUSDT: RSI filter blocked (rsi=16.7 above_sma=False regime=TRENDING) |
| 07:58:03 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:03 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:03 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: SHORT entry=0.0102 rsi=42.9 |
| 07:58:03 | SIGNAL | 🔔 Signal SHORT PENGUUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:58:07 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:07 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:07 | FILTER | ⚡ PAPER_SPEED bypass PENDLEUSDT: SLEEP_MODE(vol=0=0%_of_avg=2401,min=10%[base=45%×0.20]) |
| 07:58:07 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5300 rsi=52.9 |
| 07:58:07 | SIGNAL | 🔔 Signal LONG PENDLEUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:58:12 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:12 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:12 | FILTER | ⚡ PAPER_SPEED bypass WLFIUSDT: SLEEP_MODE(vol=14366=7%_of_avg=193081,min=10%[base=45%×0.20]) |
| 07:58:12 | SIGNAL | ⚡ PAPER_SPEED fallback WLFIUSDT: SHORT entry=0.0538 rsi=57.1 |
| 07:58:12 | SIGNAL | 🔔 Signal SHORT WLFIUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 834.43 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': 'f8318533', 'symbol': 'SOLUSDT', 'side': 'LONG', 'entry_price': 83.79, 'qty': 1.997023, 'stop_loss': 83.58187199999998, 'take_profit': 84.46032000000001, 'entry_ts': 1777706199977, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 83.82, 'initial_risk': 12.5498, 'initial_stop_loss': 83.521872, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.11188686000711018, 'ticks_since_peak': 1908}, {'position_id': 'e76b1a9a', 'symbol': 'TRXUSDT', 'side': 'LONG', 'entry_price': 0.329, 'qty': 508.603465, 'stop_loss': 0.32794720000000005, 'take_profit': 0.33163200000000004, 'entry_ts': 1777706200625, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 0.329, 'initial_risk': 12.5498, 'initial_stop_loss': 0.32794720000000005, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.0, 'ticks_since_peak': 1065}, {'position_id': '0ae2820a', 'symbol': 'BNBUSDT', 'side': 'LONG', 'entry_price': 616.01, 'qty': 0.271636, 'stop_loss': 614.1387679999999, 'take_profit': 620.93808, 'entry_ts': 1777706201920, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 616.05, 'initial_risk': 12.5498, 'initial_stop_loss': 614.038768, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.020291878378579434, 'ticks_since_peak': 1860}, {'position_id': '51c6e867', 'symbol': 'BTCUSDT', 'side': 'LONG', 'entry_price': 78323.23, 'qty': 0.001066, 'stop_loss': 78078.96566400003, 'take_profit': 78949.81584, 'entry_ts': 1777706881171, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 78324.7, 'initial_risk': 4.1741, 'initial_stop_loss': 78072.595664, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.005865118177587399, 'ticks_since_peak': 5243}, {'position_id': '0f923211', 'symbol': 'ETHUSDT', 'side': 'LONG', 'entry_price': 2305.48, 'qty': 0.03621, 'stop_loss': 2298.112464, 'take_profit': 2323.92384, 'entry_ts': 1777707001174, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 2305.49, 'initial_risk': 4.1741, 'initial_stop_loss': 2298.102464, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.0013554661068090458, 'ticks_since_peak': 3102}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| SOLUSDT | LONG | 1.997023 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| TRXUSDT | LONG | 508.603465 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| BNBUSDT | LONG | 0.271636 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| BTCUSDT | LONG | 0.001066 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| ETHUSDT | LONG | 0.036210 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| BTCUSDT | LONG | -0.10 | -0.025 | TRENDING | MARKET |
| TRXUSDT | LONG | -0.14 | -0.034 | TRENDING | MARKET |
| CHIPUSDT | LONG | +0.02 | 0.004 | TRENDING | MARKET |
| MEGAUSDT | LONG | -0.26 | -0.061 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.20 | -0.049 | TRENDING | MARKET |
| ORCAUSDT | SHORT | -0.58 | -0.139 | TRENDING | MARKET |
| CHIPUSDT | LONG | +0.04 | 0.010 | TRENDING | MARKET |
| PENDLEUSDT | LONG | +0.20 | 0.048 | TRENDING | MARKET |
| BNBUSDT | LONG | -0.18 | -0.042 | MEAN_REVERTING | MARKET |
| MEGAUSDT | SHORT | -0.08 | -0.019 | TRENDING | MARKET |
| MEGAUSDT | SHORT | -0.09 | -0.007 | TRENDING | MARKET |
| PENGUUSDT | LONG | -0.07 | -0.006 | TRENDING | MARKET |
| CHIPUSDT | LONG | +0.02 | 0.001 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.22 | -0.017 | TRENDING | MARKET |
| PENDLEUSDT | SHORT | -0.12 | -0.010 | TRENDING | MARKET |
| ETHUSDT | LONG | -0.21 | -0.016 | TRENDING | MARKET |
| WLFIUSDT | LONG | -1.15 | -0.092 | TRENDING | MARKET |
| PENDLEUSDT | SHORT | -0.01 | -0.002 | TRENDING | MARKET |
| XRPUSDT | LONG | -0.11 | -0.009 | TRENDING | MARKET |
| MEGAUSDT | SHORT | -0.26 | -0.063 | TRENDING | MARKET |


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
| regimes | {'TRENDING': {'n_trades': 9, 'win_rate': 0.0, 'weight': 0.5}, 'MEAN_REVERTING': {'n_trades': 1, 'win_rate': 1.0, 'weight': 1.0}} |


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
| strategies | {'TRENDING@TrendFollowing_PAPER_SPEED': {'n_trades': 8, 'edge': -0.2791, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 1, 'edge': 0.0157, 'win_rate': 1.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@ALPHA_PBE_v1': {'n_trades': 1, 'edge': -0.0075, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.9 |
| MeanReversion | 0.1 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 25 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.36 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (27.0% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Low win rate (37.0% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


## 9. Auto-Tuning (Dynamic Thresholds)

| Metric | Value |
|---|---|
| score_min | 0.4 |
| volume_multiplier | 0.3 |
| fee_tolerance | 0.1 |
| dd_allowed | True |
| dd_size_mult | 1.0 |
| tier | TIER_2 |
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
| daily_risk_used | 154.7397 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.364 (negative expectancy)
-   Detail — 357 trades; win_rate=37.0%. Every trade destroys capital on average. Immediate action required.
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


