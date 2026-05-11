# EOW Quant Engine — Full System Report

_Generated: 2026-05-11 07:07:44 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **1156** trades with a net **LOSS** of **-316.58 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 23.8% |
| Profit Factor | 0.455 |
| Sharpe | -2.434 |
| Max Drawdown | 33.08% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 683.42 |
| Net PnL (USDT) | -316.5775 |
| Total Trades | 1156 |
| Win Rate | 23.8% |
| Profit Factor | 0.455 |
| Sharpe | -2.434 |
| Sortino | -2.492 |
| Calmar | -0.209 |
| Max Drawdown | 33.08% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.9609 |
| Avg Loss | -0.6593 |
| Fees Paid | 153.0279 |
| Slippage | 76.3204 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 629.00 |
| Trades / hour | 13.00 |
| Rejection Rate | 23.5% |
| Signals total | 629 |
| Trades total | 13 |
| Skips total | 4 |
| Mins since trade | 6.5 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 07:07:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:00 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 07:07:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=16.9 above_sma=False regime=TRENDING) |
| 07:07:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=45.2 above_sma=False regime=MEAN_REVERTING) |
| 07:07:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=24.7 above_sma=False regime=TRENDING) |
| 07:07:01 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:01 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:01 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=46.1 above_sma=False regime=TRENDING) |
| 07:07:01 | SIGNAL | ⚡ DTP LAYERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:01 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:01 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=35.9 above_sma=False regime=TRENDING) |
| 07:07:02 | SIGNAL | ⚡ DTP APTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:02 | SIGNAL | 📈 STREAK APTUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:02 | FILTER | ⚡ PAPER_SPEED APTUSDT: RSI filter blocked (rsi=18.2 above_sma=False regime=TRENDING) |
| 07:07:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=52.2 above_sma=False regime=MEAN_REVERTING) |
| 07:07:05 | SIGNAL | ⚡ DTP XLMUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:05 | SIGNAL | 📈 STREAK XLMUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:05 | FILTER | ⚡ PAPER_SPEED XLMUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 07:07:07 | SIGNAL | ⚡ DTP ASTERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:07 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:07 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=41.7 above_sma=False regime=TRENDING) |
| 07:07:40 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 683.42 |
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
| LUNCUSDT | LONG | -0.39 | -0.038 | MEAN_REVERTING | MARKET |
| LTCUSDT | SHORT | -0.36 | -0.035 | MEAN_REVERTING | MARKET |
| APTUSDT | SHORT | -0.44 | -0.042 | MEAN_REVERTING | MARKET |
| ETHUSDT | SHORT | -0.33 | -0.032 | MEAN_REVERTING | MARKET |
| BTCUSDT | SHORT | -0.26 | -0.074 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | -0.12 | -0.036 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.37 | -0.108 | MEAN_REVERTING | MARKET |
| UNIUSDT | SHORT | -0.40 | -0.117 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.37 | -0.108 | MEAN_REVERTING | MARKET |
| XLMUSDT | SHORT | -0.19 | -0.056 | MEAN_REVERTING | MARKET |
| ETHUSDT | SHORT | -0.28 | -0.080 | MEAN_REVERTING | MARKET |
| LTCUSDT | SHORT | -0.15 | -0.042 | MEAN_REVERTING | MARKET |
| SEIUSDT | LONG | -0.52 | -0.150 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | -0.40 | -0.117 | MEAN_REVERTING | MARKET |
| APTUSDT | LONG | -0.56 | -0.162 | MEAN_REVERTING | MARKET |
| XLMUSDT | LONG | -0.36 | -0.104 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.21 | -0.061 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.26 | -0.075 | MEAN_REVERTING | MARKET |
| ASTERUSDT | LONG | -0.19 | -0.056 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.54 | -0.157 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 20, 'win_rate': 0.0, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 20, 'edge': -0.3338, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 5561.8}} |


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
| CT-002 | CRITICAL | High fees (32.6% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (23.8% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 96.3205 |
| daily_risk_cap_usdt | None |
| daily_risk_remaining | None |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1778477063.02646 | DATA_001 | UNIUSDT | candles=1 |
| 1778477021.4971263 | WS_001 |  | gap=31.4s |


### Healer Events (recent)

| Action | OK | Detail |
|---|---|---|
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
| API_PING | True |  |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.455 (negative expectancy)
-   Detail — 1156 trades; win_rate=23.8%. Every trade destroys capital on average. Immediate action required.
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


