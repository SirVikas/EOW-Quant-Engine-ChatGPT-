# EOW Quant Engine — Full System Report

_Generated: 2026-05-06 01:05:53 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **514** trades with a net **LOSS** of **-174.60 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 33.3% |
| Profit Factor | 0.516 |
| Sharpe | -2.081 |
| Max Drawdown | 19.73% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 825.40 |
| Net PnL (USDT) | -174.5977 |
| Total Trades | 514 |
| Win Rate | 33.3% |
| Profit Factor | 0.516 |
| Sharpe | -2.081 |
| Sortino | -1.980 |
| Calmar | -0.434 |
| Max Drawdown | 19.73% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0890 |
| Avg Loss | -1.0520 |
| Fees Paid | 79.6628 |
| Slippage | 21.2966 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 479.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 0.0% |
| Signals total | 479 |
| Trades total | 0 |
| Skips total | 0 |
| Mins since trade | 601.3 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 01:04:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=51.3 above_sma=False regime=MEAN_REVERTING) |
| 01:04:58 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:58 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:58 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=93.1 above_sma=True regime=TRENDING) |
| 01:04:58 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:58 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:58 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=45.7 above_sma=False regime=MEAN_REVERTING) |
| 01:04:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=33.0 above_sma=False regime=TRENDING) |
| 01:04:59 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:59 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:59 | SIGNAL | ⚡ ALPHA TrendBreakout DOGSUSDT score=0.731 rr=4.00 |
| 01:04:59 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=89.8 above_sma=True regime=TRENDING) |
| 01:05:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:05:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:05:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81148.3000 rsi=77.2 |
| 01:05:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:05:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:05:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:05:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=68.4 above_sma=True regime=TRENDING) |
| 01:05:02 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:05:02 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:05:02 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: LONG entry=0.3201 rsi=58.2 |
| 01:05:02 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:05:02 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:05:02 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=56.3300 rsi=68.6 |
| 01:05:02 | SIGNAL | 🔔 Signal SHORT LTCUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 825.40 |
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
| BTCUSDT | LONG | -0.23 | -0.012 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | -0.59 | -0.030 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.17 | -0.009 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | +0.68 | 0.165 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.59 | -0.036 | MEAN_REVERTING | MARKET |
| DASHUSDT | SHORT | -0.48 | -0.029 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.84 | -0.204 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | -0.57 | -0.139 | MEAN_REVERTING | MARKET |
| DOGSUSDT | LONG | +6.70 | 0.541 | MEAN_REVERTING | MARKET |
| BIOUSDT | LONG | -0.54 | -0.044 | MEAN_REVERTING | MARKET |
| ETHUSDT | SHORT | -0.23 | -0.018 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.49 | -0.039 | MEAN_REVERTING | MARKET |
| LTCUSDT | SHORT | -0.41 | -0.033 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.27 | -0.044 | MEAN_REVERTING | MARKET |
| TSTUSDT | LONG | -0.70 | -0.115 | MEAN_REVERTING | MARKET |
| DOGSUSDT | LONG | -1.32 | -0.106 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | -0.86 | -0.070 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.17 | -0.014 | MEAN_REVERTING | MARKET |
| LTCUSDT | LONG | -0.20 | -0.016 | MEAN_REVERTING | MARKET |
| TSTUSDT | SHORT | -0.79 | -0.192 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 5, 'win_rate': 0.0, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 5, 'edge': -0.6701, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 36077.5}} |


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
| CT-001 | CRITICAL | Low profit factor (0.52 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (31.3% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (33.3% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 0.0 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.516 (negative expectancy)
-   Detail — 514 trades; win_rate=33.3%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **Also noted (requires attention):**
-   - TRADE DRY-SPELL — 601 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.


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


