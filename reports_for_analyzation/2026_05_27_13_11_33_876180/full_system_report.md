# EOW Quant Engine — Full System Report

_Generated: 2026-05-27 02:17:55 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **1284** trades with a net **LOSS** of **-232.63 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 20.4% |
| Profit Factor | 0.412 |
| Sharpe | -4.425 |
| Max Drawdown | 23.26% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 767.37 |
| Net PnL (USDT) | -232.6342 |
| Total Trades | 1284 |
| Win Rate | 20.4% |
| Profit Factor | 0.412 |
| Sharpe | -4.425 |
| Sortino | -5.537 |
| Calmar | -0.196 |
| Max Drawdown | 23.26% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.6227 |
| Avg Loss | -0.3873 |
| Fees Paid | 113.4184 |
| Slippage | 71.8621 |
| Deployability | 25/100 (NOT READY) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 0.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 0.0% |
| Signals total | 0 |
| Trades total | 0 |
| Skips total | 0 |
| Mins since trade | 64.9 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 01:11:59 | SIGNAL | 💰 Orchestrator FETUSDT: score=0.499 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 01:11:59 | TRADE | 📋 Limit SHORT FETUSDT @ 0.2521 qty=182.746399 risk=3.84U [TrendFollowing / TRENDING] |
| 01:11:59 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP WLDUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP RENDERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:01 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:02 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:15 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:47 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:13:00 | TRADE | [TM] FETUSDT TIME_EXIT @ 0.2529 (Fast-fail: 1.0min r=-0.510<-0.45) |
| 01:13:00 | TRADE | Position closed [SL] FETUSDT @ 0.2529 |
| 01:13:04 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #13: meta_score=46.0 verdict=— |
| 01:14:06 | FILTER | ⚡ PAPER_SPEED bypass SPKUSDT: SLEEP_MODE(vol=4418=8%_of_avg=57843,min=10%[base=45%×0.20]) |
| 01:14:24 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=462=6%_of_avg=8077,min=10%[base=45%×0.20]) |
| 01:15:16 | FILTER | ⚡ PAPER_SPEED bypass SPKUSDT: SLEEP_MODE(vol=3662=6%_of_avg=57701,min=10%[base=45%×0.20]) |
| 01:18:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #14: meta_score=46.0 verdict=— |
| 01:23:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #15: meta_score=46.0 verdict=— |
| 01:28:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #16: meta_score=46.0 verdict=— |
| 01:33:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #17: meta_score=46.0 verdict=— |
| 01:38:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #18: meta_score=46.0 verdict=— |
| 01:43:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #19: meta_score=46.0 verdict=— |
| 01:48:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #20: meta_score=46.0 verdict=— |
| 01:53:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #21: meta_score=46.0 verdict=— |
| 01:58:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #22: meta_score=46.0 verdict=— |
| 02:03:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #23: meta_score=46.0 verdict=— |
| 02:08:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #24: meta_score=46.0 verdict=— |
| 02:13:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #25: meta_score=46.0 verdict=— |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 767.37 |
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
| FETUSDT | LONG | -0.18 | -0.016 | TRENDING | LIMIT |
| TONUSDT | SHORT | -0.13 | -0.033 | MEAN_REVERTING | LIMIT |
| RENDERUSDT | SHORT | +0.14 | 0.035 | MEAN_REVERTING | LIMIT |
| NEARUSDT | SHORT | -0.11 | -0.010 | TRENDING | LIMIT |
| ONDOUSDT | SHORT | +0.21 | 0.018 | TRENDING | LIMIT |
| WLDUSDT | SHORT | -0.03 | -0.008 | TRENDING | LIMIT |
| FETUSDT | SHORT | -0.03 | -0.008 | MEAN_REVERTING | LIMIT |
| RENDERUSDT | LONG | +0.37 | 0.097 | TRENDING | LIMIT |
| WLDUSDT | SHORT | -0.34 | -0.036 | TRENDING | LIMIT |
| OPGUSDT | SHORT | -0.09 | -0.010 | TRENDING | LIMIT |
| NEARUSDT | LONG | -0.14 | -0.037 | TRENDING | LIMIT |
| SPKUSDT | LONG | -0.03 | -0.008 | MEAN_REVERTING | LIMIT |
| ONDOUSDT | SHORT | -0.20 | -0.052 | MEAN_REVERTING | LIMIT |
| RENDERUSDT | LONG | -0.22 | -0.056 | TRENDING | LIMIT |
| ONDOUSDT | SHORT | -0.24 | -0.062 | MEAN_REVERTING | LIMIT |
| TONUSDT | LONG | -0.07 | -0.019 | TRENDING | LIMIT |
| OPGUSDT | SHORT | -0.15 | -0.040 | MEAN_REVERTING | LIMIT |
| ONDOUSDT | LONG | -0.19 | -0.049 | TRENDING | LIMIT |
| FETUSDT | LONG | +0.05 | 0.013 | TRENDING | LIMIT |
| FETUSDT | SHORT | -0.17 | -0.044 | TRENDING | LIMIT |


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
| regimes | {'TRENDING': {'n_trades': 14, 'win_rate': 0.217, 'weight': 0.5}, 'MEAN_REVERTING': {'n_trades': 7, 'win_rate': 0.122, 'weight': 0.5}} |


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
| strategies | {'TRENDING@ALPHA_PBE_v1': {'n_trades': 3, 'edge': -0.2276, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@TF_EMA_RSI_v1': {'n_trades': 3, 'edge': -0.022, 'win_rate': 0.333, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'MEAN_REVERTING@ALPHA_PBE_v1': {'n_trades': 3, 'edge': -0.1605, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'MEAN_REVERTING@MR_BB_RSI_v1': {'n_trades': 4, 'edge': -0.0409, 'win_rate': 0.25, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@ALPHA_TCB_v1': {'n_trades': 8, 'edge': -0.037, 'win_rate': 0.25, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.6667 |
| MeanReversion | 0.3333 |
| VolatilityExpansion | 0.0 |


## 8. Suggestions (CT-Scan)

| Metric | Value |
|---|---|
| Health | CRITICAL |
| Score | 25 |
| Action | — |

| Code | Severity | Message | Action |
|---|---|---|---|
| CT-001 | CRITICAL | Low profit factor (0.41 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (32.8% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Low win rate (20.4% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 122.8433 |
| daily_risk_cap_usdt | 46.0419 |
| daily_risk_remaining | 0.0 |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1779848242.0723464 | WS_002 |  | gap=60.3s attempt=31 |
| 1779848108.9121656 | WS_002 |  | gap=60.2s attempt=30 |
| 1779847987.2091491 | WS_002 |  | gap=60.2s attempt=29 |
| 1779847864.5583086 | WS_002 |  | gap=60.4s attempt=28 |
| 1779847737.2808092 | WS_002 |  | gap=60.3s attempt=27 |
| 1779847604.8154304 | WS_002 |  | gap=60.4s attempt=26 |
| 1779847477.0927775 | WS_002 |  | gap=60.3s attempt=25 |
| 1779847344.4946787 | WS_002 |  | gap=60.3s attempt=24 |
| 1779847222.8005254 | WS_002 |  | gap=60.4s attempt=23 |
| 1779847085.2254498 | WS_002 |  | gap=60.4s attempt=22 |
| 1779846953.3872988 | WS_002 |  | gap=60.3s attempt=21 |
| 1779846825.7673755 | WS_002 |  | gap=60.5s attempt=20 |
| 1779846695.0471506 | WS_002 |  | gap=60.2s attempt=19 |
| 1779846558.3813667 | WS_002 |  | gap=60.4s attempt=18 |
| 1779846427.5978365 | WS_002 |  | gap=60.3s attempt=17 |
| 1779846293.9315176 | WS_002 |  | gap=60.7s attempt=16 |
| 1779846158.8108666 | WS_002 |  | gap=60.3s attempt=15 |
| 1779846032.5318687 | WS_002 |  | gap=60.2s attempt=14 |
| 1779845896.513723 | WS_002 |  | gap=60.4s attempt=13 |
| 1779845765.0330157 | WS_002 |  | gap=60.4s attempt=12 |
| 1779845636.6556916 | WS_002 |  | gap=60.3s attempt=11 |
| 1779845500.940887 | WS_002 |  | gap=60.2s attempt=10 |
| 1779845366.113318 | WS_002 |  | gap=60.3s attempt=9 |
| 1779845232.3812752 | WS_002 |  | gap=60.2s attempt=8 |
| 1779845102.7263854 | WS_002 |  | gap=60.2s attempt=7 |
| 1779845008.578467 | WS_002 |  | gap=60.3s attempt=6 |
| 1779844931.7132473 | WS_002 |  | gap=60.2s attempt=5 |
| 1779844862.1266313 | WS_002 |  | gap=60.3s attempt=4 |
| 1779844797.173861 | WS_002 |  | gap=61.7s attempt=3 |
| 1779844733.2668786 | WS_002 |  | gap=61.8s attempt=2 |
| 1779844665.8285584 | WS_001 |  | gap=60.9s attempt=1 |
| 1779844635.2859657 | WS_001 |  | gap=30.3s |


### Healer Events (recent)

| Action | OK | Detail |
|---|---|---|
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | False |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | False |  |
| WS_RECONNECT | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | False |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | False |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | False |  |
| WS_RECONNECT | True |  |
| BALANCE_SYNC | True |  |
| WS_CHECK | False |  |
| API_PING | False |  |


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
-   Detail — 1284 closed trades exist but trade_flow_monitor reports 0 signals. This is a data-integrity gap in the signal pipeline tracker.
-   Fix — Verify on_tick calls trade_flow_monitor.record_signal() for every evaluated signal. Restart trade_flow_monitor if counter was reset.
- 
- **SECONDARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.412 (negative expectancy)
-   Detail — 1284 trades; win_rate=20.4%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **ACTIONABLE FIX (primary):** Verify on_tick calls trade_flow_monitor.record_signal() for every evaluated signal. Restart trade_flow_monitor if counter was reset.
- 
- **Also noted (requires attention):**
-   - RISK OF RUIN = 100.0% — CAPITAL IN DANGER: System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   - TRADE DRY-SPELL — 65 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.
-   - 32 ERRORS recorded in audit log: High error count may indicate WS connectivity or data quality issues.


## 15. Action Checklist

- [ ] Review Section 4 (Decision Trace) for last 30 thoughts.
- [ ] Archive this report under /reports/<date>/ for audit trail.

---

_End of report — FTD-025A Export Engine v1.0_


## 16. Learning Memory (FTD-030B)

| Metric | Value |
|---|---|
| Status | ACTIVE |
| Memory Records | 83 |
| Total Patterns | 57 |
| Formed Patterns | 0 |
| Cycles Processed | 21 |
| Negative Memory (Permanent) | 0 |
| Negative Memory (Temporary) | 48 |


