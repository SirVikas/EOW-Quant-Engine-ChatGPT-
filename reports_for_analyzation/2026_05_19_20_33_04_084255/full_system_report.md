# EOW Quant Engine — Full System Report

_Generated: 2026-05-19 14:59:05 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **203** trades with a net **LOSS** of **-64.09 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 18.2% |
| Profit Factor | 0.329 |
| Sharpe | -6.259 |
| Max Drawdown | 6.41% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 935.90 |
| Net PnL (USDT) | -64.0950 |
| Total Trades | 203 |
| Win Rate | 18.2% |
| Profit Factor | 0.329 |
| Sharpe | -6.259 |
| Sortino | -7.348 |
| Calmar | -1.241 |
| Max Drawdown | 6.41% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.8506 |
| Avg Loss | -0.5757 |
| Fees Paid | 30.1463 |
| Slippage | 22.6097 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 163.00 |
| Trades / hour | 20.00 |
| Rejection Rate | 0.0% |
| Signals total | 163 |
| Trades total | 20 |
| Skips total | 0 |
| Mins since trade | 15.3 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 14:34:06 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=24.0 above_sma=False bands=[47.0,53.0] (rsi=24.0 above_sma=False regime= |
| 14:34:06 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 14:34:06 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=39.6 above_sma=False bands=[38.0,62.0] (rsi=39.6 above_sma=False regime= |
| 14:34:07 | SIGNAL | 📈 STREAK UUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 14:34:07 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=57.1 above_sma=True bands=[38.0,62.0] (rsi=57.1 above_sma=True regime=MEAN |
| 14:34:31 | TRADE | [TM] AIGENSYNUSDT TIME_EXIT @ 0.0357 (Stale: 8.5min r=0.089<0.15) |
| 14:34:31 | TRADE | Position closed [SL] AIGENSYNUSDT @ 0.03571 |
| 14:34:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #210: meta_score=46.8 verdict=— |
| 14:34:34 | TRADE | Position closed [TSL+] ETHUSDT @ 2104.23 |
| 14:34:41 | TRADE | Position closed [TSL+] UNIUSDT @ 3.457 |
| 14:34:45 | TRADE | [TM] BCHUSDT TIME_EXIT @ 380.2000 (Stale: 8.5min r=0.110<0.15) |
| 14:34:46 | TRADE | Position closed [SL] BCHUSDT @ 380.1 |
| 14:34:48 | TRADE | Position closed [SL] FIDAUSDT @ 0.01995 |
| 14:34:59 | TRADE | [TM] BTCUSDT TIME_EXIT @ 76258.4500 (Stale: 8.0min r=-0.944<0.15) |
| 14:34:59 | TRADE | Position closed [SL] BTCUSDT @ 76258.45 |
| 14:35:24 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:35:24 | SIGNAL | ⚡ PAPER_SPEED fallback SPKUSDT: LONG entry=0.0281 rsi=33.9 |
| 14:35:24 | SIGNAL | 🔔 Signal LONG SPKUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:35:24 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) SPKUSDT |
| 14:35:24 | SIGNAL | ⚡ LCC_OVERRIDE SPKUSDT: state=REDUCING cl=3 [bypass=active, size not reduced] |
| 14:35:24 | SIGNAL | ⚠️ ALLOC_ZERO SPKUSDT: score=0.132 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:35:24 | SIGNAL | 💰 Orchestrator SPKUSDT: score=0.132 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False |
| 14:35:24 | TRADE | ⚡ PAPER_SPEED market-fill override SPKUSDT: USE_LIMIT_ORDERS bypassed |
| 14:35:24 | TRADE | ✅ Opened LONG SPKUSDT qty=6670.280671 risk=4.68U [MeanReversion / MEAN_REVERTING] |
| 14:39:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #211: meta_score=46.9 verdict=— |
| 14:43:45 | TRADE | [TM] SPKUSDT TIME_EXIT @ 0.0281 (Stale: 8.3min r=0.141<0.15) |
| 14:43:45 | TRADE | Position closed [SL] SPKUSDT @ 0.028077 |
| 14:44:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #212: meta_score=46.8 verdict=— |
| 14:49:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #213: meta_score=46.8 verdict=— |
| 14:54:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #214: meta_score=46.8 verdict=— |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 935.91 |
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
| AIGENSYNUSDT | SHORT | -0.53 | -0.112 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.64 | -0.136 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | -0.48 | -0.102 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | -0.47 | -0.099 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.47 | -0.099 | MEAN_REVERTING | MARKET |
| SPKUSDT | LONG | -0.48 | -0.101 | MEAN_REVERTING | MARKET |
| AIGENSYNUSDT | SHORT | +0.73 | 0.155 | MEAN_REVERTING | MARKET |
| BCHUSDT | SHORT | +0.38 | 0.080 | MEAN_REVERTING | MARKET |
| FIDAUSDT | LONG | -0.64 | -0.136 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.64 | -0.136 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.53 | -0.113 | MEAN_REVERTING | MARKET |
| NEARUSDT | LONG | -0.26 | -0.056 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.26 | -0.056 | MEAN_REVERTING | MARKET |
| AIGENSYNUSDT | LONG | -0.21 | -0.045 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | +0.10 | 0.021 | MEAN_REVERTING | MARKET |
| UNIUSDT | LONG | +0.06 | 0.013 | MEAN_REVERTING | MARKET |
| BCHUSDT | LONG | -0.26 | -0.056 | MEAN_REVERTING | MARKET |
| FIDAUSDT | LONG | -0.07 | -0.016 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.69 | -0.147 | MEAN_REVERTING | MARKET |
| SPKUSDT | LONG | -0.20 | -0.043 | MEAN_REVERTING | MARKET |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 50, 'win_rate': 0.187, 'weight': 0.5}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 50, 'edge': -0.3417, 'win_rate': 0.16, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 55249.9}} |


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
| CT-001 | CRITICAL | Low profit factor (0.33 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (32.0% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (18.2% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


## 9. Auto-Tuning (Dynamic Thresholds)

| Metric | Value |
|---|---|
| score_min | 0.4 |
| volume_multiplier | 0.3 |
| fee_tolerance | 0.1 |
| dd_allowed | True |
| dd_size_mult | 1.0 |
| tier | TIER_2 |
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
| daily_risk_used | 250.3483 |
| daily_risk_cap_usdt | 56.1543 |
| daily_risk_remaining | 0.0 |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1779202403.6566942 | WS_001 |  | gap=30.8s |
| 1779201398.3262758 | WS_001 |  | gap=32.9s |
| 1779201169.369362 | WS_002 |  | gap=61.1s attempt=2 |
| 1779201153.9295292 | WS_001 |  | gap=45.7s |
| 1779200104.658934 | WS_001 |  | gap=33.1s |
| 1779199267.5389125 | WS_001 |  | gap=31.7s |
| 1779198430.4961507 | WS_001 |  | gap=31.2s |
| 1779197805.992712 | WS_001 |  | gap=31.3s |
| 1779196997.5553532 | WS_001 |  | gap=33.0s |
| 1779196146.5673118 | WS_001 |  | gap=33.7s |
| 1779195710.162169 | WS_001 |  | gap=31.6s |
| 1779195478.78584 | WS_001 |  | gap=33.9s |
| 1779194644.0227504 | WS_001 |  | gap=32.5s |
| 1779194233.7540019 | WS_001 |  | gap=31.6s |
| 1779194020.7216883 | WS_001 |  | gap=30.0s |
| 1779190672.4670017 | WS_001 |  | gap=62.4s attempt=1 |
| 1779190649.6993027 | WS_001 |  | gap=39.6s |
| 1779189416.1495912 | WS_001 |  | gap=31.4s |
| 1779188333.8319888 | WS_001 |  | gap=37.2s |


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
| API_PING | False |  |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.329 (negative expectancy)
-   Detail — 203 trades; win_rate=18.2%. Every trade destroys capital on average. Immediate action required.
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
| Memory Records | 76 |
| Total Patterns | 8 |
| Formed Patterns | 0 |
| Cycles Processed | 76 |
| Negative Memory (Permanent) | 1 |
| Negative Memory (Temporary) | 9 |


