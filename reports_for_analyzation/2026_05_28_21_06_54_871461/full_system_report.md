# EOW Quant Engine — Full System Report

_Generated: 2026-05-28 15:22:59 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **1831** trades with a net **LOSS** of **-254.55 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 22.6% |
| Profit Factor | 0.476 |
| Sharpe | -3.567 |
| Max Drawdown | 25.50% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 745.45 |
| Net PnL (USDT) | -254.5513 |
| Total Trades | 1831 |
| Win Rate | 22.6% |
| Profit Factor | 0.476 |
| Sharpe | -3.567 |
| Sortino | -4.692 |
| Calmar | -0.137 |
| Max Drawdown | 25.50% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.5595 |
| Avg Loss | -0.3425 |
| Fees Paid | 132.6213 |
| Slippage | 71.8621 |
| Deployability | 45/100 (NOT READY) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 405.00 |
| Trades / hour | 7.00 |
| Rejection Rate | 46.2% |
| Signals total | 405 |
| Trades total | 7 |
| Skips total | 6 |
| Mins since trade | 5.2 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 15:19:18 | SIGNAL | ⚡ LCC_OVERRIDE FILUSDT: state=REDUCING cl=3 [bypass=active, size not reduced] |
| 15:19:18 | SIGNAL | 🧮 EV FILUSDT: ev=-0.0097 p_win=14.3% n=14 |
| 15:19:19 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK FETUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK RENDERUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | ⚡ ALPHA PullbackEntry NEARUSDT score=0.573 rr=5.00 |
| 15:19:19 | SIGNAL | ⚡ DISABLED_OVERRIDE NEARUSDT: ALPHA_PBE_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioriti |
| 15:19:19 | SIGNAL | 🔔 Signal SHORT NEARUSDT / PBE: EMA_DIST=0.08% RSI=57.4 RR=5.00 SCORE=0.573 |
| 15:19:19 | SIGNAL | ⚡ LCC_OVERRIDE NEARUSDT: state=REDUCING cl=3 [bypass=active, size not reduced] |
| 15:19:19 | SIGNAL | 🧮 EV NEARUSDT: ev=-0.1384 p_win=10.0% n=10 |
| 15:19:21 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:22 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:24 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:10 | TRADE | [TM] ALTUSDT BE: SL→0.0069 (R=1.63≥1.5 mode=TREND_FOLLOW → SL→BE) |
| 15:20:21 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:21 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:21 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:21 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:21 | SIGNAL | 📈 STREAK FILUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:22 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:23 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:24 | SIGNAL | 📈 STREAK RENDERUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:24 | SIGNAL | 📈 STREAK FETUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:25 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:26 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:26 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=475=5%_of_avg=9120,min=10%[base=45%×0.20]) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 745.45 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': 'f90a676a', 'symbol': 'ALTUSDT', 'side': 'SHORT', 'entry_price': 0.0069, 'qty': 21584.789609, 'stop_loss': 0.006902396097800001, 'take_profit': 0.006774285714285716, 'entry_ts': 1779980893076, 'strategy_id': 'ALPHA_PBE_v1', 'trailing_sl': True, 'peak_price': 0.00688, 'initial_risk': 3.7288, 'initial_stop_loss': 0.006931714285714286, 'regime': 'MEAN_REVERTING', 'order_type': 'LIMIT', 'breakeven_armed': False, 'peak_r': 0.6306306306306274, 'ticks_since_peak': 16}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| ALTUSDT | SHORT | 21,584.789609 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| FILUSDT | LONG | -0.17 | -0.046 | MEAN_REVERTING | LIMIT |
| FETUSDT | SHORT | -0.21 | -0.057 | TRENDING | LIMIT |
| RENDERUSDT | SHORT | -0.33 | -0.089 | TRENDING | LIMIT |
| ETHUSDT | SHORT | -0.16 | -0.042 | TRENDING | LIMIT |
| BTCUSDT | SHORT | -0.14 | -0.037 | TRENDING | LIMIT |
| SEIUSDT | SHORT | -0.32 | -0.085 | TRENDING | LIMIT |
| RENDERUSDT | SHORT | -0.41 | -0.109 | TRENDING | LIMIT |
| ALTUSDT | SHORT | +0.61 | 0.163 | TRENDING | LIMIT |
| ICPUSDT | SHORT | -0.55 | -0.148 | TRENDING | LIMIT |
| ONDOUSDT | SHORT | -0.97 | -0.260 | MEAN_REVERTING | LIMIT |
| NEARUSDT | LONG | -0.16 | -0.043 | TRENDING | LIMIT |
| ETHUSDT | LONG | -0.09 | -0.023 | TRENDING | LIMIT |
| BTCUSDT | LONG | -0.18 | -0.048 | TRENDING | LIMIT |
| FETUSDT | LONG | +0.31 | 0.084 | TRENDING | LIMIT |
| WLDUSDT | SHORT | +0.59 | 0.157 | TRENDING | LIMIT |
| TONUSDT | SHORT | +0.11 | 0.030 | MEAN_REVERTING | LIMIT |
| NEARUSDT | SHORT | +0.08 | 0.022 | TRENDING | LIMIT |
| WLDUSDT | SHORT | -0.38 | -0.069 | TRENDING | LIMIT |
| WLDUSDT | SHORT | -0.16 | -0.043 | TRENDING | LIMIT |
| TONUSDT | SHORT | -0.15 | -0.039 | MEAN_REVERTING | LIMIT |


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
| regimes | {'TRENDING': {'n_trades': 50, 'win_rate': 0.261, 'weight': 0.5}, 'MEAN_REVERTING': {'n_trades': 50, 'win_rate': 0.285, 'weight': 0.5}} |


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
| strategies | {'TRENDING@ALPHA_TCB_v1': {'n_trades': 50, 'edge': -0.1085, 'win_rate': 0.22, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 27829.8}, 'TRENDING@ALPHA_PBE_v1': {'n_trades': 50, 'edge': -0.0339, 'win_rate': 0.22, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 60016.0}, 'MEAN_REVERTING@MR_BB_RSI_v1': {'n_trades': 50, 'edge': -0.0695, 'win_rate': 0.3, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 90099.5}, 'TRENDING@TF_EMA_RSI_v1': {'n_trades': 35, 'edge': -0.0764, 'win_rate': 0.257, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 54057.1}, 'MEAN_REVERTING@ALPHA_PBE_v1': {'n_trades': 48, 'edge': -0.0766, 'win_rate': 0.208, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 37621.9}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.8067 |
| MeanReversion | 0.1933 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 25 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.48 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (34.2% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Low win rate (22.6% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 1114.0879 |
| daily_risk_cap_usdt | 44.7269 |
| daily_risk_remaining | 0.0 |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1779981676.2252898 | WS_001 |  | gap=31.8s |
| 1779981233.6141164 | WS_001 |  | gap=30.7s |
| 1779981005.051614 | WS_001 |  | gap=35.1s |
| 1779980779.7020514 | WS_001 |  | gap=33.5s |
| 1779979943.4282575 | WS_002 |  | gap=62.6s attempt=37 |
| 1779979915.4100826 | WS_001 |  | gap=34.6s |
| 1779979467.7836246 | WS_001 |  | gap=32.8s |
| 1779979253.6637394 | WS_001 |  | gap=31.1s |
| 1779979041.5753741 | WS_002 |  | gap=62.7s attempt=36 |
| 1779979012.51104 | WS_001 |  | gap=33.6s |
| 1779978576.5419416 | WS_001 |  | gap=31.9s |
| 1779978357.6443334 | WS_002 |  | gap=63.6s attempt=35 |
| 1779978327.1262205 | WS_001 |  | gap=33.1s |
| 1779978109.1986513 | WS_001 |  | gap=31.6s |
| 1779977878.46414 | WS_001 |  | gap=32.9s |
| 1779977654.5043435 | WS_001 |  | gap=31.9s |
| 1779977415.9181132 | WS_001 |  | gap=32.9s |
| 1779977201.152343 | WS_001 |  | gap=32.6s |
| 1779976754.9569259 | WS_001 |  | gap=32.2s |
| 1779976524.7539935 | WS_001 |  | gap=35.3s |
| 1779976057.0644639 | WS_002 |  | gap=67.3s attempt=34 |
| 1779976035.0027933 | WS_001 |  | gap=45.2s |
| 1779975813.7489822 | WS_002 |  | gap=60.9s attempt=33 |
| 1779975785.277855 | WS_001 |  | gap=32.5s |
| 1779975714.1171756 | WS_001 |  | gap=35.6s |
| 1779975482.8453526 | WS_002 |  | gap=63.7s attempt=32 |
| 1779975452.2195313 | WS_001 |  | gap=33.0s |
| 1779975230.5046868 | WS_002 |  | gap=62.1s attempt=31 |
| 1779975206.368461 | WS_001 |  | gap=38.0s |
| 1779974923.6346567 | WS_002 |  | gap=62.7s attempt=30 |
| 1779974898.7808306 | WS_001 |  | gap=37.8s |
| 1779974643.1064763 | WS_002 |  | gap=61.3s attempt=29 |
| 1779974614.8916154 | WS_001 |  | gap=33.1s |
| 1779974360.2006762 | WS_002 |  | gap=67.5s attempt=28 |
| 1779974329.0104167 | WS_001 |  | gap=36.4s |
| 1779974069.0052 | WS_001 |  | gap=32.7s |
| 1779973814.3408234 | WS_002 |  | gap=61.0s attempt=27 |
| 1779973784.3360317 | WS_001 |  | gap=31.0s |
| 1779973563.2066398 | WS_002 |  | gap=61.9s attempt=26 |
| 1779973539.638436 | WS_001 |  | gap=38.3s |
| 1779973093.2309186 | WS_002 |  | gap=66.1s attempt=25 |
| 1779973059.2182746 | WS_001 |  | gap=32.1s |
| 1779972778.053333 | WS_002 |  | gap=74.1s attempt=24 |
| 1779972748.9086323 | WS_001 |  | gap=45.0s |
| 1779972521.635112 | WS_002 |  | gap=60.3s attempt=23 |
| 1779972496.0411484 | WS_001 |  | gap=34.7s |
| 1779972282.0021672 | WS_001 |  | gap=31.6s |
| 1779972009.1653118 | WS_001 |  | gap=32.9s |
| 1779971750.1312115 | WS_002 |  | gap=65.4s attempt=22 |
| 1779971717.6584728 | WS_001 |  | gap=32.9s |


### Healer Events (recent)

| Action | OK | Detail |
|---|---|---|
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | True |  |
| API_PING | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.476 (negative expectancy)
-   Detail — 1831 trades; win_rate=22.6%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **Also noted (requires attention):**
-   - 50 ERRORS recorded in audit log: High error count may indicate WS connectivity or data quality issues.


## 15. Action Checklist

- [ ] Review Section 4 (Decision Trace) for last 30 thoughts.
- [ ] Archive this report under /reports/<date>/ for audit trail.

---

_End of report — FTD-025A Export Engine v1.0_


## 16. Learning Memory (FTD-030B)

| Metric | Value |
|---|---|
| Status | ACTIVE |
| Memory Records | 539 |
| Total Patterns | 105 |
| Formed Patterns | 0 |
| Cycles Processed | 538 |
| Negative Memory (Permanent) | 3 |
| Negative Memory (Temporary) | 13 |


