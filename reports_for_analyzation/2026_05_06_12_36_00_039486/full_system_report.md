# EOW Quant Engine — Full System Report

_Generated: 2026-05-06 06:56:39 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **531** trades with a net **LOSS** of **-180.42 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 32.8% |
| Profit Factor | 0.512 |
| Sharpe | -2.113 |
| Max Drawdown | 19.74% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 819.58 |
| Net PnL (USDT) | -180.4189 |
| Total Trades | 531 |
| Win Rate | 32.8% |
| Profit Factor | 0.512 |
| Sharpe | -2.113 |
| Sortino | -2.018 |
| Calmar | -0.434 |
| Max Drawdown | 19.74% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0889 |
| Avg Loss | -1.0361 |
| Fees Paid | 81.9021 |
| Slippage | 22.9760 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 456.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 0.0% |
| Signals total | 456 |
| Trades total | 0 |
| Skips total | 0 |
| Mins since trade | 202.4 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 06:53:42 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:53:43 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:53:43 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=72.7 above_sma=True regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=25.4 above_sma=False regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.1290 rsi=45.4 |
| 06:55:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | SIGNAL | ⚡ ALPHA TrendBreakout TSTUSDT score=0.662 rr=5.00 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=14.8 above_sma=False regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=69.2 above_sma=True regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=64.5 above_sma=True regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=48.3 above_sma=False regime=MEAN_REVERTING) |
| 06:56:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:56:02 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:56:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2368.3400 rsi=60.3 |
| 06:56:11 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:56:11 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:56:11 | FILTER | ⚡ PAPER_SPEED bypass TRUMPUSDT: SLEEP_MODE(vol=59=9%_of_avg=669,min=10%[base=45%×0.20]) |
| 06:56:11 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3920 rsi=57.1 |
| 06:56:35 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 819.58 |
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
| DOGSUSDT | LONG | -1.32 | -0.106 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | -0.86 | -0.070 | MEAN_REVERTING | MARKET |
| TSTUSDT | SHORT | -0.79 | -0.192 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | +1.78 | 0.144 | MEAN_REVERTING | MARKET |
| TSTUSDT | SHORT | -0.64 | -0.052 | MEAN_REVERTING | MARKET |
| ICPUSDT | LONG | -0.53 | -0.043 | MEAN_REVERTING | MARKET |
| DOGSUSDT | SHORT | -1.27 | -0.102 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.65 | -0.052 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.47 | -0.038 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.63 | -0.152 | MEAN_REVERTING | MARKET |
| ICPUSDT | LONG | -0.47 | -0.038 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.56 | -0.045 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.53 | -0.128 | MEAN_REVERTING | MARKET |
| TONUSDT | SHORT | +1.39 | 0.339 | MEAN_REVERTING | MARKET |
| ICPUSDT | SHORT | +0.07 | 0.006 | MEAN_REVERTING | MARKET |
| TRUMPUSDT | SHORT | -0.78 | -0.063 | MEAN_REVERTING | MARKET |
| LUNCUSDT | SHORT | -0.93 | -0.227 | MEAN_REVERTING | MARKET |
| TRUMPUSDT | SHORT | -0.44 | -0.106 | MEAN_REVERTING | MARKET |
| TONUSDT | SHORT | -0.95 | -0.232 | MEAN_REVERTING | MARKET |
| LTCUSDT | SHORT | -0.23 | -0.056 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 10, 'win_rate': 0.2, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 10, 'edge': -0.3424, 'win_rate': 0.2, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 12218.9}} |


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
| CT-001 | CRITICAL | Low profit factor (0.51 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (31.2% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (32.8% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 74.0288 |
| daily_risk_cap_usdt | None |
| daily_risk_remaining | None |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1778046627.4474423 | WS_001 |  | gap=50.3s |


### Healer Events (recent)

| Action | OK | Detail |
|---|---|---|
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | False |  |
| WS_RECONNECT | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | True |  |
| WS_RECONNECT | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.512 (negative expectancy)
-   Detail — 531 trades; win_rate=32.8%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **Also noted (requires attention):**
-   - TRADE DRY-SPELL — 202 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.


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


