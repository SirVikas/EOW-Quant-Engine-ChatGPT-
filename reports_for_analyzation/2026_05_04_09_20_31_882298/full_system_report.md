# EOW Quant Engine — Full System Report

_Generated: 2026-05-04 03:48:46 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **443** trades with a net **LOSS** of **-169.47 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 35.4% |
| Profit Factor | 0.481 |
| Sharpe | -2.245 |
| Max Drawdown | 19.16% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 830.53 |
| Net PnL (USDT) | -169.4709 |
| Total Trades | 443 |
| Win Rate | 35.4% |
| Profit Factor | 0.481 |
| Sharpe | -2.245 |
| Sortino | -2.050 |
| Calmar | -0.503 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.9988 |
| Avg Loss | -1.1408 |
| Fees Paid | 71.2660 |
| Slippage | 14.9989 |
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
| Mins since trade | 26.7 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 03:22:10 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 03:22:11 | SYSTEM | Mode: PAPER / Capital: 1000.0 USDT |
| 03:22:11 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 03:22:13 | SYSTEM | 📂 DataLake replay: 443 trades → equity=830.53 USDT |
| 03:22:13 | SYSTEM | 📂 State restored: snapshot(830.53) validated vs replay(830.53) |
| 03:22:13 | SYSTEM | ⚡ Phase 4 Profit Engine online / rr_min=2.0 score_min=0.48 max_per_trade=5% daily_cap=6% |
| 03:22:13 | SYSTEM | 🧠 Phase 5 EV Engine online / ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 03:22:13 | SYSTEM | 🔓 Phase 5.1 Activation Layer online / activator_tiers=T1@5min T2@12min T3@25min / explore_rate=3% smart_fee_rr |
| 03:22:13 | SYSTEM | Phase 6.6 Gate online / can_trade=True reason=BYPASS_ALL_GATES safe_mode=False |
| 03:22:13 | SYSTEM | All subsystems online. Scanning markets… |
| 03:22:13 | SYSTEM | ⚡ [FTD-031] Performance layer online / target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 03:22:23 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_eng |
| 03:22:31 | SYSTEM | ⚡ Mode switched to PAPER |
| 03:27:13 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #1: meta_score=58.4 verdict=BLOCKED |
| 03:32:13 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #2: meta_score=58.4 verdict=BLOCKED |
| 03:37:13 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #3: meta_score=58.4 verdict=BLOCKED |
| 03:47:13 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #4: meta_score=58.4 verdict=BLOCKED |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 830.53 |
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
| LUNCUSDT | SHORT | -0.51 | -0.122 | MEAN_REVERTING | MARKET |
| LUNCUSDT | LONG | -0.50 | -0.119 | TRENDING | MARKET |


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
| Score | 10 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.48 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (29.6% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (none dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (35.4% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| Generation | 480 |
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

- **PRIMARY ISSUE:** CONTRADICTION — trades recorded but signal count = 0
-   Detail — 443 closed trades exist but trade_flow_monitor reports 0 signals. This is a data-integrity gap in the signal pipeline tracker.
-   Fix — Verify on_tick calls trade_flow_monitor.record_signal() for every evaluated signal. Restart trade_flow_monitor if counter was reset.
- 
- **SECONDARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.481 (negative expectancy)
-   Detail — 443 trades; win_rate=35.4%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **ACTIONABLE FIX (primary):** Verify on_tick calls trade_flow_monitor.record_signal() for every evaluated signal. Restart trade_flow_monitor if counter was reset.
- 
- **Also noted (requires attention):**
-   - RISK OF RUIN = 100.0% — CAPITAL IN DANGER: System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.


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


