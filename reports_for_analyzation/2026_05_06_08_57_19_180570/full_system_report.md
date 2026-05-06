# EOW Quant Engine — Full System Report

_Generated: 2026-05-06 03:24:48 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **525** trades with a net **LOSS** of **-177.16 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 33.0% |
| Profit Factor | 0.517 |
| Sharpe | -2.087 |
| Max Drawdown | 19.73% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 822.84 |
| Net PnL (USDT) | -177.1559 |
| Total Trades | 525 |
| Win Rate | 33.0% |
| Profit Factor | 0.517 |
| Sharpe | -2.087 |
| Sortino | -1.991 |
| Calmar | -0.431 |
| Max Drawdown | 19.73% |
| Risk of Ruin | 100.00% |
| Avg Win | +1.0948 |
| Avg Loss | -1.0413 |
| Fees Paid | 81.1122 |
| Slippage | 22.3836 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 138.00 |
| Trades / hour | 4.00 |
| Rejection Rate | 0.0% |
| Signals total | 138 |
| Trades total | 4 |
| Skips total | 0 |
| Mins since trade | 7.8 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 03:23:01 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=31.2 above_sma=True regime=MEAN_REVERTING) |
| 03:23:01 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:01 | SIGNAL | ⚡ ALPHA TrendBreakout TSTUSDT score=0.824 rr=5.00 |
| 03:23:01 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=30.1 above_sma=False regime=TRENDING) |
| 03:23:01 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:01 | SIGNAL | ⚡ ALPHA TrendBreakout DOGSUSDT score=0.872 rr=4.00 |
| 03:23:01 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=30.3 above_sma=False regime=TRENDING) |
| 03:23:02 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=58.9 above_sma=False regime=MEAN_REVERTING) |
| 03:23:19 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:19 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: SHORT entry=2.3900 rsi=64.3 |
| 03:23:19 | SIGNAL | 🔔 Signal SHORT TRUMPUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:23:19 | SIGNAL | 💰 Orchestrator TRUMPUSDT: score=0.396 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=Fal |
| 03:23:19 | TRADE | ⚡ PAPER_SPEED market-fill override TRUMPUSDT: USE_LIMIT_ORDERS bypassed |
| 03:23:19 | TRADE | ✅ Opened SHORT TRUMPUSDT qty=68.857253 risk=12.34U [MeanReversion / MEAN_REVERTING] |
| 03:23:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=75.4 above_sma=True regime=TRENDING) |
| 03:23:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=27.6 above_sma=False regime=TRENDING) |
| 03:23:59 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:59 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=35.3 above_sma=True regime=MEAN_REVERTING) |
| 03:23:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=51.0 above_sma=True regime=MEAN_REVERTING) |
| 03:23:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=62.4 above_sma=True regime=TRENDING) |
| 03:23:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=43.6 above_sma=False regime=MEAN_REVERTING) |
| 03:24:00 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:24:00 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=22.2 above_sma=False regime=TRENDING) |
| 03:24:44 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 822.84 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': '9361ccd8', 'symbol': 'ICPUSDT', 'side': 'SHORT', 'entry_price': 2.719, 'qty': 60.5255, 'stop_loss': 2.71360025, 'take_profit': 2.681681725, 'entry_ts': 1778037539047, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 2.699, 'initial_risk': 12.3427, 'initial_stop_loss': 2.72895154, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': True, 'peak_r': 2.0097391961444546, 'ticks_since_peak': 89}, {'position_id': 'aff5a092', 'symbol': 'TRUMPUSDT', 'side': 'SHORT', 'entry_price': 2.39, 'qty': 68.857253, 'stop_loss': 2.395736, 'take_profit': 2.36849, 'entry_ts': 1778037799801, 'strategy_id': 'MeanReversion_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 2.39, 'initial_risk': 12.3427, 'initial_stop_loss': 2.395736, 'regime': 'MEAN_REVERTING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.0, 'ticks_since_peak': 9}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| ICPUSDT | SHORT | 60.525500 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| TRUMPUSDT | SHORT | 68.857253 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| ONDOUSDT | LONG | -0.49 | -0.039 | MEAN_REVERTING | MARKET |
| LTCUSDT | SHORT | -0.41 | -0.033 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.27 | -0.044 | MEAN_REVERTING | MARKET |
| TSTUSDT | LONG | -0.70 | -0.115 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.17 | -0.014 | MEAN_REVERTING | MARKET |
| LTCUSDT | LONG | -0.20 | -0.016 | MEAN_REVERTING | MARKET |
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
| regimes | {'MEAN_REVERTING': {'n_trades': 4, 'win_rate': 0.25, 'weight': 1.0}} |


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
| strategies | {'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 4, 'edge': -0.0402, 'win_rate': 0.25, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


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
| CT-001 | CRITICAL | Low profit factor (0.52 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (31.4% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (MeanReversion dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (33.0% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| Generation | 360 |
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
| daily_risk_used | 57.5954 |
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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.517 (negative expectancy)
-   Detail — 525 trades; win_rate=33.0%. Every trade destroys capital on average. Immediate action required.
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


