# EOW Quant Engine — Full System Report

_Generated: 2026-04-28 04:26:02 UTC_

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
| Deployability | 40/100 (NOT READY) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 30.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 100.0% |
| Signals total | 30 |
| Trades total | 0 |
| Skips total | 14 |
| Mins since trade | 1.7 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 04:24:24 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 04:24:24 | SYSTEM | Mode: PAPER / Capital: 1000.0 USDT |
| 04:24:24 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 04:24:25 | SYSTEM | 📂 DataLake replay: 243 trades → equity=848.92 USDT |
| 04:24:25 | SYSTEM | 📂 State restored: snapshot(848.92) validated vs replay(848.92) |
| 04:24:25 | SYSTEM | ⚡ Phase 4 Profit Engine online / rr_min=2.0 score_min=0.48 max_per_trade=5% daily_cap=6% |
| 04:24:25 | SYSTEM | 🧠 Phase 5 EV Engine online / ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 04:24:25 | SYSTEM | 🔓 Phase 5.1 Activation Layer online / activator_tiers=T1@5min T2@12min T3@25min / explore_rate=3% smart_fee_rr |
| 04:24:25 | SYSTEM | Phase 6.6 Gate online / can_trade=True reason=BOOT_GRACE safe_mode=False |
| 04:24:25 | SYSTEM | All subsystems online. Scanning markets… |
| 04:24:25 | SYSTEM | ⚡ [FTD-031] Performance layer online / target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 04:24:31 | SIGNAL | ⚡ ALPHA VolatilitySqueeze ETHUSDT score=0.744 rr=6.00 |
| 04:24:31 | SIGNAL | 🔔 Signal SHORT ETHUSDT / VSE: BB_WIDTH=0.37% SQUEEZE→EXPAND RR=6.00 SCORE=0.744 |
| 04:24:31 | SIGNAL | ⚡ ALPHA VolatilitySqueeze BTCUSDT score=0.593 rr=6.00 |
| 04:24:31 | SIGNAL | 🔔 Signal SHORT BTCUSDT / VSE: BB_WIDTH=0.24% SQUEEZE→EXPAND RR=6.00 SCORE=0.593 |
| 04:24:32 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_eng |
| 04:24:39 | SYSTEM | ⚡ Mode switched to PAPER |
| 04:24:41 | SIGNAL | ⚡ ALPHA VolatilitySqueeze AAVEUSDT score=0.607 rr=6.00 |
| 04:24:41 | SIGNAL | 🔔 Signal SHORT AAVEUSDT / VSE: BB_WIDTH=0.44% SQUEEZE→EXPAND RR=6.00 SCORE=0.607 |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 848.92 |
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
| ZBTUSDT | SHORT | -5.94 | -0.972 | TRENDING | LIMIT |
| AXSUSDT | SHORT | +0.08 | 0.013 | TRENDING | LIMIT |
| SOLUSDT | SHORT | +0.01 | 0.001 | MEAN_REVERTING | LIMIT |
| KATUSDT | SHORT | -0.73 | -0.120 | TRENDING | LIMIT |
| SOLUSDT | SHORT | -0.13 | -0.021 | TRENDING | LIMIT |
| CHIPUSDT | LONG | +0.22 | 0.036 | TRENDING | LIMIT |
| BTCUSDT | SHORT | -0.09 | -0.015 | TRENDING | LIMIT |
| TRUMPUSDT | SHORT | +0.02 | 0.003 | MEAN_REVERTING | LIMIT |
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
| regimes | {} |


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
| CT-001 | CRITICAL | Low profit factor (0.38 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (25.1% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (none dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.379 (negative expectancy)
-   Detail — 243 trades; win_rate=45.7%. Every trade destroys capital on average. Immediate action required.
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


