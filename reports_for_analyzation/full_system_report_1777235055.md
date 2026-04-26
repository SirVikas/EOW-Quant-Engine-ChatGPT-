# EOW Quant Engine — Full System Report

_Generated: 2026-04-26 20:24:15 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **243** trades with a net **LOSS** of **-151.08 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 45.7% |
| Profit Factor | 0.379 |
| Sharpe | -2.915 |
| Max Drawdown | 16.87% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 848.92 |
| Net PnL (USDT) | -151.0820 |
| Total Trades | 243 |
| Win Rate | 45.7% |
| Profit Factor | 0.379 |
| Sharpe | -2.915 |
| Sortino | -2.329 |
| Calmar | -0.929 |
| Max Drawdown | 16.87% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.8310 |
| Avg Loss | -1.8434 |
| Fees Paid | 50.5689 |
| Slippage | 0.0000 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 0.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 0.0% |
| Signals total | 0 |
| Trades total | 0 |
| Skips total | 0 |
| Mins since trade | 162.0 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 17:34:06 | SIGNAL | 🔔 Signal SHORT TRUMPUSDT / BB upper touch / RSI=72.2 / Mean=2.6470 / TP=2.6420 |
| 17:34:06 | SIGNAL | 🔬 EXPLORE_INJECT TRUMPUSDT: score=0.606 size=0.25× qty=12.102916 — quality gates bypassed, only risk limits ap |
| 17:34:06 | SIGNAL | 💰 Orchestrator TRUMPUSDT: score=0.606 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fal |
| 17:34:06 | TRADE | 📋 Limit SHORT TRUMPUSDT @ 2.6528 qty=12.102916 risk=7.59U [MeanReversion / MEAN_REVERTING] |
| 17:34:06 | SIGNAL | 📈 STREAK RAYUSDT: HOT len=3 score_adj=-0.03 → eff_min=0.550 |
| 17:34:57 | TRADE | Position closed [SL] KATUSDT @ 0.01268 |
| 17:35:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT / EMA cross DOWN / trend↓ / RSI=39.6 / ATR=0.6621 |
| 17:35:01 | SIGNAL | 💰 Orchestrator ETHUSDT: score=0.453 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 17:35:01 | TRADE | 📋 Limit SHORT ETHUSDT @ 2345.6335 qty=0.054705 risk=1.71U [TrendFollowing / TRENDING] |
| 17:35:02 | TRADE | Position closed [BE] TRUMPUSDT @ 2.649 |
| 17:35:31 | TRADE | Position closed [SL] BTCUSDT @ 77982.47 |
| 17:35:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #2: meta_score=55.0 verdict=BLOCKED |
| 17:36:03 | SIGNAL | ⚡ ALPHA TrendBreakout RAYUSDT score=0.746 rr=3.75 |
| 17:36:03 | SIGNAL | 🔔 Signal SHORT RAYUSDT / TCB: ADX=46.7 VOL=1.5x RR=3.75 SCORE=0.746 |
| 17:36:03 | SIGNAL | 💰 Orchestrator RAYUSDT: score=0.710 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 17:36:03 | TRADE | 📋 Limit SHORT RAYUSDT @ 0.7482 qty=171.482169 risk=1.71U [TrendFollowing / TRENDING] |
| 17:36:26 | TRADE | Position closed [SL] ZBTUSDT @ 0.2521 |
| 17:40:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #3: meta_score=55.0 verdict=BLOCKED |
| 17:42:01 | TRADE | Position closed [SL] SOLUSDT @ 86.47 |
| 17:42:14 | TRADE | Position closed [SL] ETHUSDT @ 2346.3 |
| 17:45:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #4: meta_score=85.0 verdict=BLOCKED |
| 17:55:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #5: meta_score=85.0 verdict=BLOCKED |
| 18:00:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #6: meta_score=85.0 verdict=BLOCKED |
| 18:10:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #7: meta_score=85.0 verdict=BLOCKED |
| 18:20:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #8: meta_score=85.0 verdict=BLOCKED |
| 18:30:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #9: meta_score=85.0 verdict=BLOCKED |
| 18:35:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #10: meta_score=85.0 verdict=BLOCKED |
| 18:40:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #11: meta_score=85.0 verdict=BLOCKED |
| 18:45:56 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #12: meta_score=85.0 verdict=BLOCKED |
| 20:21:43 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 848.92 |
| Halted | True |
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
| XRPUSDT | SHORT | -0.09 | -0.051 | TRENDING | LIMIT |
| ZBTUSDT | LONG | +0.08 | 0.048 | TRENDING | LIMIT |
| ORCAUSDT | LONG | -1.27 | -0.738 | MEAN_REVERTING | LIMIT |
| SOLUSDT | LONG | -0.01 | -0.004 | MEAN_REVERTING | LIMIT |
| RAYUSDT | SHORT | -0.37 | -0.217 | MEAN_REVERTING | LIMIT |
| KATUSDT | SHORT | +0.10 | 0.056 | TRENDING | LIMIT |
| TRUMPUSDT | SHORT | -0.11 | -0.064 | MEAN_REVERTING | LIMIT |
| HYPERUSDT | LONG | -0.62 | -0.363 | MEAN_REVERTING | LIMIT |
| XRPUSDT | SHORT | -0.01 | -0.007 | TRENDING | LIMIT |
| ETHUSDT | LONG | -0.02 | -0.010 | TRENDING | LIMIT |
| ORCAUSDT | SHORT | -1.24 | -0.203 | MEAN_REVERTING | LIMIT |
| SOLUSDT | SHORT | +0.01 | 0.001 | MEAN_REVERTING | LIMIT |
| AXSUSDT | SHORT | +0.08 | 0.013 | TRENDING | LIMIT |
| CHIPUSDT | LONG | +0.22 | 0.036 | TRENDING | LIMIT |
| KATUSDT | SHORT | -0.73 | -0.120 | TRENDING | LIMIT |
| TRUMPUSDT | SHORT | +0.02 | 0.003 | MEAN_REVERTING | LIMIT |
| BTCUSDT | SHORT | -0.09 | -0.015 | TRENDING | LIMIT |
| ZBTUSDT | SHORT | -5.94 | -0.972 | TRENDING | LIMIT |
| SOLUSDT | SHORT | -0.13 | -0.021 | TRENDING | LIMIT |
| ETHUSDT | SHORT | -0.14 | -0.082 | TRENDING | LIMIT |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 3, 'win_rate': 0.667, 'weight': 1.0}, 'TRENDING': {'n_trades': 7, 'win_rate': 0.286, 'weight': 0.5}} |


### Edge Engine

| Metric | Value |
|---|---|
| window_size | 50 |
| min_trades | 20 |
| edge_boost_at | 0.15 |
| edge_kill_at | 0.0 |
| boost_mult | 1.25 |
| strategies | {'MEAN_REVERTING@MR_BB_RSI_v1': {'n_trades': 3, 'edge': -0.403, 'win_rate': 0.667, 'size_mult': 1.0, 'disabled': False}, 'TRENDING@ALPHA_PBE_v1': {'n_trades': 1, 'edge': 0.0808, 'win_rate': 1.0, 'size_mult': 1.0, 'disabled': False}, 'TRENDING@ALPHA_TCB_v1': {'n_trades': 4, 'edge': -1.4853, 'win_rate': 0.25, 'size_mult': 1.0, 'disabled': False}, 'TRENDING@ALPHA_VSE_v1': {'n_trades': 1, 'edge': -0.7255, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False}, 'TRENDING@TF_EMA_RSI_v1': {'n_trades': 1, 'edge': -0.141, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.7 |
| MeanReversion | 0.3 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 45 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.38 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (25.1% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


## 9. Auto-Tuning (Dynamic Thresholds)

| Metric | Value |
|---|---|
| score_min | 0.42 |
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
| daily_risk_cap | 0.03 |
| daily_risk_used | 59.6244 |
| daily_risk_remaining | 0.0 |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1777229397.5290034 | WS_001 |  | gap=32.6s |
| 1777224548.205191 | STRAT_001 | ENSOUSDT | adx=16.2 conf=0.12 |
| 1777224481.6888635 | STRAT_001 | ENSOUSDT | adx=16.6 conf=0.12 |
| 1777224479.8639338 | DATA_002 | ETHUSDT | ADX_UNSTABLE(5.0<5.0) |
| 1777224435.14865 | STRAT_001 | ENSOUSDT | adx=19.2 conf=0.12 |
| 1777224362.7549446 | STRAT_001 | ENSOUSDT | adx=18.8 conf=0.12 |
| 1777224362.344662 | STRAT_001 | TONUSDT | adx=28.5 conf=0.12 |


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

- **PRIMARY ISSUE:** CONTRADICTION — trades recorded but signal count = 0
-   Detail — 243 closed trades exist but trade_flow_monitor reports 0 signals. This is a data-integrity gap in the signal pipeline tracker.
-   Fix — Verify on_tick calls trade_flow_monitor.record_signal() for every evaluated signal. Restart trade_flow_monitor if counter was reset.
- 
- **SECONDARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.379 (negative expectancy)
-   Detail — 243 trades; win_rate=45.7%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **ACTIONABLE FIX (primary):** Verify on_tick calls trade_flow_monitor.record_signal() for every evaluated signal. Restart trade_flow_monitor if counter was reset.
- 
- **Also noted (requires attention):**
-   - RISK OF RUIN = 100.0% — CAPITAL IN DANGER: System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   - TRADE DRY-SPELL — 162 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.


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


