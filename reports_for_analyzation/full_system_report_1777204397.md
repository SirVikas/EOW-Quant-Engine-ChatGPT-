# EOW Quant Engine — Full System Report

_Generated: 2026-04-26 11:53:17 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **152** trades with a net **LOSS** of **-136.21 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 49.3% |
| Profit Factor | 0.379 |
| Sharpe | -3.371 |
| Max Drawdown | 15.61% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 863.79 |
| Net PnL (USDT) | -136.2143 |
| Total Trades | 152 |
| Win Rate | 49.3% |
| Profit Factor | 0.379 |
| Sharpe | -3.371 |
| Sortino | -2.593 |
| Calmar | -1.447 |
| Max Drawdown | 15.61% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.1100 |
| Avg Loss | -2.8502 |
| Fees Paid | 46.4894 |
| Slippage | 0.0000 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 843.00 |
| Trades / hour | 13.00 |
| Rejection Rate | 0.0% |
| Signals total | 843 |
| Trades total | 13 |
| Skips total | 0 |
| Mins since trade | 1.4 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 11:49:59 | SIGNAL | ⚡ DTP RAYUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:49:59 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:49:59 | SIGNAL | ⚡ DTP AXSUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:49:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:49:59 | SIGNAL | ⚡ DTP ZBTUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:00 | SIGNAL | ⚡ DTP SAHARAUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:00 | SIGNAL | 🔔 Signal SHORT SAHARAUSDT / BB upper touch / RSI=65.9 / Mean=0.0242 / TP=0.0240 |
| 11:50:00 | SIGNAL | 💰 Orchestrator SAHARAUSDT: score=0.366 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fa |
| 11:50:00 | TRADE | 📋 Limit SHORT SAHARAUSDT @ 0.0243 qty=5323.984897 risk=1.73U [MeanReversion / MEAN_REVERTING] |
| 11:50:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:00 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:03 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:59 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:59 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:50:59 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:51:00 | SIGNAL | ⚡ DTP ZBTUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:51:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:51:01 | SIGNAL | ⚡ DTP RAYUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:51:01 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:51:02 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:51:02 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:51:05 | SIGNAL | ⚡ DTP AXSUSDT: tier=TIER_3 af=RELAX score_min=0.420 vol_mult=0.20× fee_tol=0.10 |
| 11:51:26 | TRADE | Position closed [TSL+] ENSOUSDT @ 1.076 |
| 11:51:31 | TRADE | Position closed [BE] HYPERUSDT @ 0.1272 |
| 11:51:56 | TRADE | Position closed [TSL+] SAHARAUSDT @ 0.02426 |
| 11:53:14 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #11: meta_score=85.0 verdict=BLOCKED |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 863.79 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': '57b7d92b', 'symbol': 'KATUSDT', 'side': 'SHORT', 'entry_price': 0.01275, 'qty': 10135.166238, 'stop_loss': 0.012848857142857143, 'take_profit': 0.012400357142857142, 'entry_ts': 1777204034308, 'strategy_id': 'ALPHA_PBE_v1', 'trailing_sl': True, 'peak_price': 0.01275, 'initial_risk': 1.7257, 'initial_stop_loss': 0.012848857142857143, 'regime': 'TRENDING', 'order_type': 'LIMIT', 'breakeven_armed': False, 'peak_r': 0.0, 'ticks_since_peak': 126}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| KATUSDT | SHORT | 10,135.166238 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| HYPERUSDT | SHORT | -0.02 | -0.003 | TRENDING | LIMIT |
| ORCAUSDT | LONG | +0.54 | 0.085 | TRENDING | LIMIT |
| ZBTUSDT | LONG | +0.10 | 0.016 | TRENDING | LIMIT |
| ENSOUSDT | SHORT | -0.66 | -0.103 | MEAN_REVERTING | LIMIT |
| ETHUSDT | SHORT | -0.05 | -0.007 | TRENDING | LIMIT |
| CHIPUSDT | LONG | +0.05 | 0.028 | MEAN_REVERTING | LIMIT |
| ENSOUSDT | LONG | +0.65 | 0.102 | TRENDING | LIMIT |
| HYPERUSDT | SHORT | +0.05 | 0.028 | MEAN_REVERTING | LIMIT |
| AXSUSDT | LONG | +0.26 | 0.046 | TRENDING | LIMIT |
| BTCUSDT | LONG | -0.05 | -0.008 | TRENDING | LIMIT |
| ETHUSDT | LONG | -0.08 | -0.006 | TRENDING | LIMIT |
| ENSOUSDT | LONG | -0.44 | -0.151 | TRENDING | LIMIT |
| TRUMPUSDT | SHORT | -0.05 | -0.032 | MEAN_REVERTING | LIMIT |
| ETHUSDT | LONG | -0.05 | -0.026 | TRENDING | LIMIT |
| AXSUSDT | SHORT | +0.02 | 0.012 | TRENDING | LIMIT |
| CHIPUSDT | LONG | -0.37 | -0.216 | TRENDING | LIMIT |
| RAYUSDT | SHORT | +0.34 | 0.197 | TRENDING | LIMIT |
| ENSOUSDT | SHORT | +0.70 | 0.408 | MEAN_REVERTING | LIMIT |
| HYPERUSDT | SHORT | -0.01 | -0.008 | TRENDING | LIMIT |
| SAHARAUSDT | SHORT | +0.25 | 0.147 | MEAN_REVERTING | LIMIT |


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
| regimes | {'MEAN_REVERTING': {'n_trades': 6, 'win_rate': 0.667, 'weight': 1.0}, 'TRENDING': {'n_trades': 11, 'win_rate': 0.364, 'weight': 0.5}} |


### Edge Engine

| Metric | Value |
|---|---|
| window_size | 50 |
| min_trades | 20 |
| edge_boost_at | 0.15 |
| edge_kill_at | 0.0 |
| boost_mult | 1.25 |
| strategies | {'MEAN_REVERTING@MR_BB_RSI_v1': {'n_trades': 6, 'edge': 0.0576, 'win_rate': 0.667, 'size_mult': 1.0, 'disabled': False}, 'TRENDING@ALPHA_TCB_v1': {'n_trades': 8, 'edge': 0.034, 'win_rate': 0.375, 'size_mult': 1.0, 'disabled': False}, 'TRENDING@ALPHA_PBE_v1': {'n_trades': 2, 'edge': -0.0302, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False}, 'TRENDING@TF_EMA_RSI_v1': {'n_trades': 1, 'edge': 0.0204, 'win_rate': 1.0, 'size_mult': 1.0, 'disabled': False}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.6471 |
| MeanReversion | 0.3529 |
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
| CT-002 | CRITICAL | High fees (25.4% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_used | 65.2476 |
| daily_risk_remaining | 0.0 |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1777200420.039725 | STRAT_001 | BNBUSDT | adx=15.4 conf=0.10 |
| 1777200359.883826 | STRAT_001 | BNBUSDT | adx=15.6 conf=0.10 |
| 1777200302.0873334 | STRAT_001 | BNBUSDT | adx=18.0 conf=0.10 |
| 1777200213.7852185 | STRAT_001 | KATUSDT | adx=15.9 conf=0.12 |
| 1777200212.5918438 | STRAT_001 | TRUMPUSDT | adx=16.9 conf=0.10 |
| 1777200210.7995884 | STRAT_001 | ENSOUSDT | adx=17.0 conf=0.12 |
| 1777200200.8271642 | STRAT_001 | BNBUSDT | adx=17.5 conf=0.10 |
| 1777200200.3055463 | STRAT_001 | SOLUSDT | adx=17.3 conf=0.10 |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.379 (negative expectancy)
-   Detail — 152 trades; win_rate=49.3%. Every trade destroys capital on average. Immediate action required.
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


