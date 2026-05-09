# EOW Quant Engine — Full System Report

_Generated: 2026-05-09 02:28:29 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **757** trades with a net **LOSS** of **-228.64 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 28.3% |
| Profit Factor | 0.498 |
| Sharpe | -2.203 |
| Max Drawdown | 24.47% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 771.36 |
| Net PnL (USDT) | -228.6418 |
| Total Trades | 757 |
| Win Rate | 28.3% |
| Profit Factor | 0.498 |
| Sharpe | -2.203 |
| Sortino | -2.186 |
| Calmar | -0.311 |
| Max Drawdown | 24.47% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0619 |
| Avg Loss | -0.8396 |
| Fees Paid | 107.3995 |
| Slippage | 42.0991 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 196.00 |
| Trades / hour | 3.00 |
| Rejection Rate | 0.0% |
| Signals total | 196 |
| Trades total | 3 |
| Skips total | 0 |
| Mins since trade | 2.1 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 02:27:22 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=30.0 above_sma=False regime=TRENDING) |
| 02:27:23 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:23 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=53.8 above_sma=False regime=MEAN_REVERTING) |
| 02:27:24 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:24 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=35.0 above_sma=False regime=TRENDING) |
| 02:27:43 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |
| 02:27:55 | SYSTEM | 📦 Master Report Bundle downloaded → eow_bundle_1778293669.zip (757 trades, 868 KB) |
| 02:28:01 | SYSTEM | 🔬 Live Process Snapshot downloaded → eow_live_process_20260509_022801.zip (168 KB / logs=2000 rl_contexts=5 tr |
| 02:28:23 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:23 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 02:28:23 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:23 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=37.6 above_sma=False regime=TRENDING) |
| 02:28:23 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:23 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=17.6 above_sma=False regime=TRENDING) |
| 02:28:23 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:23 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=47.2 above_sma=False regime=MEAN_REVERTING) |
| 02:28:23 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:23 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=43.5 above_sma=False regime=TRENDING) |
| 02:28:23 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:23 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=46.5 above_sma=True regime=MEAN_REVERTING) |
| 02:28:23 | SIGNAL | 📈 STREAK OPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:23 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 02:28:23 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:23 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=53.8 above_sma=True regime=TRENDING) |
| 02:28:25 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:25 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=28.8 above_sma=False regime=TRENDING) |
| 02:28:25 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:25 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=42.2 above_sma=False regime=TRENDING) |
| 02:28:26 | SIGNAL | 📈 STREAK FILUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:28:26 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=51.6 above_sma=False regime=TRENDING) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 771.36 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': '0f5cfb3d', 'symbol': 'NILUSDT', 'side': 'LONG', 'entry_price': 0.07086, 'qty': 2178.285592, 'stop_loss': 0.07068965068, 'take_profit': 0.07168587330000001, 'entry_ts': 1778293570557, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 0.07102, 'initial_risk': 3.8588, 'initial_stop_loss': 0.07063976712, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.7265036900938245, 'ticks_since_peak': 0}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| NILUSDT | LONG | 2,178.285592 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| STRKUSDT | LONG | -0.77 | -0.198 | MEAN_REVERTING | MARKET |
| ETHUSDT | SHORT | +0.05 | 0.012 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.20 | -0.051 | MEAN_REVERTING | MARKET |
| DOGSUSDT | LONG | -0.60 | -0.155 | MEAN_REVERTING | MARKET |
| DYDXUSDT | SHORT | -0.49 | -0.126 | MEAN_REVERTING | MARKET |
| BTCUSDT | SHORT | -0.24 | -0.061 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.64 | -0.165 | MEAN_REVERTING | MARKET |
| DOGSUSDT | LONG | -0.60 | -0.155 | MEAN_REVERTING | MARKET |
| NILUSDT | LONG | +1.67 | 0.430 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.23 | -0.059 | MEAN_REVERTING | MARKET |
| NEARUSDT | LONG | -0.42 | -0.036 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.72 | -0.062 | MEAN_REVERTING | MARKET |
| ICPUSDT | LONG | -1.20 | -0.103 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.53 | -0.045 | MEAN_REVERTING | MARKET |
| BTCUSDT | SHORT | -0.08 | -0.021 | MEAN_REVERTING | MARKET |
| FILUSDT | LONG | -0.30 | -0.077 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.26 | -0.068 | MEAN_REVERTING | MARKET |
| NOTUSDT | LONG | -0.69 | -0.059 | MEAN_REVERTING | MARKET |
| NOTUSDT | LONG | -0.93 | -0.080 | MEAN_REVERTING | MARKET |
| NEARUSDT | LONG | -0.41 | -0.106 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 3, 'win_rate': 0.0, 'weight': 1.0}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 3, 'edge': -0.6744, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


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
| CT-001 | CRITICAL | Low profit factor (0.50 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (32.0% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (28.3% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| Generation | 300 |
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
| daily_risk_used | 30.9087 |
| daily_risk_cap_usdt | None |
| daily_risk_remaining | None |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1778292753.5521786 | WS_001 |  | gap=32.1s |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.498 (negative expectancy)
-   Detail — 757 trades; win_rate=28.3%. Every trade destroys capital on average. Immediate action required.
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


