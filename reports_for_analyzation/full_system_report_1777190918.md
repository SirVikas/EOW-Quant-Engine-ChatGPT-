# EOW Quant Engine — Full System Report

_Generated: 2026-04-26 08:08:38 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **133** trades with a net **LOSS** of **-137.43 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 48.9% |
| Profit Factor | 0.369 |
| Sharpe | -3.649 |
| Max Drawdown | 15.61% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 862.57 |
| Net PnL (USDT) | -137.4297 |
| Total Trades | 133 |
| Win Rate | 48.9% |
| Profit Factor | 0.369 |
| Sharpe | -3.649 |
| Sortino | -2.810 |
| Calmar | -1.668 |
| Max Drawdown | 15.61% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.2352 |
| Avg Loss | -3.2017 |
| Fees Paid | 45.7650 |
| Slippage | 0.0000 |
| Deployability | 36/100 (NOT READY) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 15.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 100.0% |
| Signals total | 15 |
| Trades total | 0 |
| Skips total | 7 |
| Mins since trade | 1.0 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 08:07:43 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 08:07:43 | SYSTEM | Mode: PAPER / Capital: 1000.0 USDT |
| 08:07:43 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 08:07:44 | SYSTEM | 📂 DataLake replay: 133 trades → equity=862.57 USDT |
| 08:07:44 | SYSTEM | 📂 State restored: snapshot(862.57) validated vs replay(862.57) |
| 08:07:44 | SYSTEM | ⚡ Phase 4 Profit Engine online / rr_min=1.5 score_min=0.58 max_per_trade=5% daily_cap=3% |
| 08:07:44 | SYSTEM | 🧠 Phase 5 EV Engine online / ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 08:07:44 | SYSTEM | 🔓 Phase 5.1 Activation Layer online / activator_tiers=T1@10min T2@20min T3@30min / explore_rate=25% smart_fee_ |
| 08:07:44 | SYSTEM | Phase 6.6 Gate online / can_trade=True reason=BOOT_GRACE safe_mode=False |
| 08:07:44 | SYSTEM | All subsystems online. Scanning markets… |
| 08:07:44 | SYSTEM | ⚡ [FTD-031] Performance layer online / target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 08:07:50 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_eng |
| 08:07:57 | SYSTEM | ⚡ Mode switched to PAPER |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 862.57 |
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
| ORDIUSDT | SHORT | -0.27 | -0.042 | TRENDING | LIMIT |
| ZROUSDT | SHORT | -0.13 | -0.073 | TRENDING | LIMIT |
| ORDIUSDT | LONG | -0.18 | -0.103 | TRENDING | LIMIT |
| ETHUSDT | SHORT | -0.01 | -0.001 | MEAN_REVERTING | LIMIT |
| CHIPUSDT | LONG | +0.08 | 0.006 | TRENDING | LIMIT |
| CHIPUSDT | LONG | -0.41 | -0.033 | TRENDING | LIMIT |
| GUNUSDT | LONG | -0.10 | -0.008 | MEAN_REVERTING | LIMIT |
| AVAXUSDT | SHORT | -0.06 | -0.020 | MEAN_REVERTING | LIMIT |
| SPKUSDT | LONG | +0.03 | 0.005 | MEAN_REVERTING | LIMIT |
| ADAUSDT | SHORT | +0.01 | 0.002 | MEAN_REVERTING | LIMIT |
| ZAMAUSDT | SHORT | +0.05 | 0.008 | TRENDING | LIMIT |
| KATUSDT | SHORT | +0.08 | 0.013 | TRENDING | LIMIT |
| CHIPUSDT | SHORT | +0.02 | 0.004 | TRENDING | LIMIT |
| APEUSDT | SHORT | -0.54 | -0.084 | TRENDING | LIMIT |
| KATUSDT | SHORT | -0.19 | -0.031 | TRENDING | LIMIT |
| KATUSDT | SHORT | +0.04 | 0.026 | TRENDING | LIMIT |
| ORDIUSDT | SHORT | +0.02 | 0.003 | MEAN_REVERTING | LIMIT |
| API3USDT | LONG | +0.02 | 0.004 | MEAN_REVERTING | LIMIT |
| TRUMPUSDT | SHORT | +0.01 | 0.002 | MEAN_REVERTING | LIMIT |
| HYPERUSDT | SHORT | -0.02 | -0.003 | TRENDING | LIMIT |


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
| regimes | {} |


### Edge Engine

| Metric | Value |
|---|---|
| window_size | 50 |
| min_trades | 20 |
| edge_boost_at | 0.15 |
| edge_kill_at | 0.0 |
| boost_mult | 1.25 |
| strategies | {} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.0 |
| MeanReversion | 0.0 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 30 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.37 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (25.0% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (none dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


## 9. Auto-Tuning (Dynamic Thresholds)

| Metric | Value |
|---|---|
| score_min | 0.58 |
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
| Generation | 0 |
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
| daily_risk_cap | 0.03 |
| daily_risk_used | 0.0 |
| daily_risk_remaining | 0.03 |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1777190870.7376075 | STRAT_001 | HYPERUSDT | adx=25.2 conf=0.00 |


### Healer Events (recent)

| Action | OK | Detail |
|---|---|---|
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.369 (negative expectancy)
-   Detail — 133 trades; win_rate=48.9%. Every trade destroys capital on average. Immediate action required.
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


