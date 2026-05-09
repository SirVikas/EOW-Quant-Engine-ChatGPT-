# EOW Quant Engine — Full System Report

_Generated: 2026-05-09 11:08:05 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **798** trades with a net **LOSS** of **-241.18 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 27.2% |
| Profit Factor | 0.487 |
| Sharpe | -2.261 |
| Max Drawdown | 25.69% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 758.82 |
| Net PnL (USDT) | -241.1789 |
| Total Trades | 798 |
| Win Rate | 27.2% |
| Profit Factor | 0.487 |
| Sharpe | -2.261 |
| Sortino | -2.259 |
| Calmar | -0.296 |
| Max Drawdown | 25.69% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0558 |
| Avg Loss | -0.8094 |
| Fees Paid | 111.8658 |
| Slippage | 45.4488 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 886.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 100.0% |
| Signals total | 886 |
| Trades total | 0 |
| Skips total | 24 |
| Mins since trade | 71.3 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 11:07:02 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=40.0 above_sma=False regime=TRENDING) |
| 11:07:03 | SIGNAL | ⚡ DTP ASTERUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:03 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:03 | FILTER | ⚡ PAPER_SPEED bypass ASTERUSDT: SLEEP_MODE(vol=83=0%_of_avg=30838,min=10%[base=45%×0.20]) |
| 11:07:03 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=42.9 above_sma=True regime=MEAN_REVERTING) |
| 11:07:06 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:06 | SIGNAL | 📈 STREAK FILUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:06 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=56.3 above_sma=True regime=MEAN_REVERTING) |
| 11:07:08 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:08 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:08 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=56.5 above_sma=True regime=MEAN_REVERTING) |
| 11:07:08 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:08 | SIGNAL | 📈 STREAK OPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:08 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=44.8 above_sma=False regime=TRENDING) |
| 11:07:12 | SIGNAL | ⚡ DTP ARBUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:12 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:12 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=63.6 above_sma=True regime=MEAN_REVERTING) |
| 11:08:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:08:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:08:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 11:08:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:08:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:08:01 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=71.0 above_sma=True regime=TRENDING) |
| 11:08:01 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:08:01 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:08:01 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=30.8 above_sma=False regime=TRENDING) |
| 11:08:02 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:08:02 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:08:02 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=48.7 above_sma=True regime=MEAN_REVERTING) |
| 11:08:02 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 758.82 |
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
| NOTUSDT | LONG | -0.21 | -0.019 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.03 | -0.003 | MEAN_REVERTING | MARKET |
| ICPUSDT | LONG | -0.01 | -0.001 | MEAN_REVERTING | MARKET |
| NOTUSDT | LONG | -0.68 | -0.177 | MEAN_REVERTING | MARKET |
| NOTUSDT | LONG | -0.91 | -0.239 | MEAN_REVERTING | MARKET |
| NEARUSDT | SHORT | -0.21 | -0.056 | MEAN_REVERTING | MARKET |
| OPUSDT | SHORT | -0.40 | -0.104 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | -0.01 | -0.002 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.24 | -0.063 | MEAN_REVERTING | MARKET |
| ICPUSDT | SHORT | -0.42 | -0.109 | MEAN_REVERTING | MARKET |
| GALAUSDT | LONG | +1.60 | 0.420 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.03 | -0.009 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.20 | -0.054 | MEAN_REVERTING | MARKET |
| LTCUSDT | LONG | -0.60 | -0.158 | MEAN_REVERTING | MARKET |
| OPUSDT | LONG | +0.06 | 0.017 | MEAN_REVERTING | MARKET |
| NEARUSDT | LONG | -0.21 | -0.056 | MEAN_REVERTING | MARKET |
| OPUSDT | LONG | -0.58 | -0.153 | MEAN_REVERTING | MARKET |
| STRKUSDT | LONG | -0.74 | -0.195 | MEAN_REVERTING | MARKET |
| ASTERUSDT | SHORT | -0.43 | -0.113 | MEAN_REVERTING | MARKET |
| ICPUSDT | LONG | -0.50 | -0.133 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 21, 'win_rate': 0.109, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 21, 'edge': -0.2472, 'win_rate': 0.095, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 4963.4}} |


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
| CT-001 | CRITICAL | Low profit factor (0.49 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (31.7% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (27.2% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 110.5604 |
| daily_risk_cap_usdt | None |
| daily_risk_remaining | None |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1778314503.597024 | WS_001 |  | gap=31.0s |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.487 (negative expectancy)
-   Detail — 798 trades; win_rate=27.2%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **Also noted (requires attention):**
-   - TRADE DRY-SPELL — 71 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.


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


