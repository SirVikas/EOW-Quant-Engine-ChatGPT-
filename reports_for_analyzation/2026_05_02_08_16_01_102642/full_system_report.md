# EOW Quant Engine — Full System Report

_Generated: 2026-05-02 02:35:02 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **271** trades with a net **LOSS** of **-153.20 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 42.1% |
| Profit Factor | 0.378 |
| Sharpe | -2.795 |
| Max Drawdown | 17.08% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 846.80 |
| Net PnL (USDT) | -153.1955 |
| Total Trades | 271 |
| Win Rate | 42.1% |
| Profit Factor | 0.378 |
| Sharpe | -2.795 |
| Sortino | -2.309 |
| Calmar | -0.834 |
| Max Drawdown | 17.08% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.8176 |
| Avg Loss | -1.5695 |
| Fees Paid | 52.9106 |
| Slippage | 1.7563 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 711.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 100.0% |
| Signals total | 711 |
| Trades total | 0 |
| Skips total | 711 |
| Mins since trade | 269.0 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 02:34:05 | SIGNAL | 🔔 Signal SHORT PENGUUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:05 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:05 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:05 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: LONG entry=1.3854 |
| 02:34:05 | SIGNAL | 🔔 Signal LONG XRPUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:06 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:06 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:06 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=83.9500 |
| 02:34:06 | SIGNAL | 🔔 Signal LONG SOLUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:06 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:06 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:06 | FILTER | ⚡ PAPER_SPEED bypass TRXUSDT: SLEEP_MODE(vol=1689=7%_of_avg=22955,min=10%[base=45%×0.20]) |
| 02:34:06 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3270 |
| 02:34:06 | SIGNAL | 🔔 Signal LONG TRXUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:06 | SIGNAL | 🔄 AIE INVERSE → SHORT TRXUSDT |
| 02:34:07 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:07 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:07 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0430 |
| 02:34:07 | SIGNAL | 🔔 Signal SHORT BIOUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:07 | SIGNAL | 🔄 AIE INVERSE → LONG BIOUSDT |
| 02:34:07 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:07 | SIGNAL | 📈 STREAK ORCAUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:07 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=1.9740 |
| 02:34:07 | SIGNAL | 🔔 Signal SHORT ORCAUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:07 | SIGNAL | 🔄 AIE INVERSE → LONG ORCAUSDT |
| 02:34:15 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:15 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:15 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5420 |
| 02:34:15 | SIGNAL | 🔔 Signal LONG PENDLEUSDT / PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:15 | SIGNAL | 🔄 AIE INVERSE → SHORT PENDLEUSDT |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 846.80 |
| Halted | False |
| Graceful stop | False |
| Open positions | [{'position_id': '8fd18f21', 'symbol': 'UUSDT', 'side': 'LONG', 'entry_price': 0.9999, 'qty': 127.323115, 'stop_loss': 0.9988001200000001, 'take_profit': 1.00239975, 'entry_ts': 1777669276769, 'strategy_id': 'TrendFollowing_PAPER_SPEED', 'trailing_sl': True, 'peak_price': 1.0, 'initial_risk': 2.6523, 'initial_stop_loss': 0.9987001200000001, 'regime': 'TRENDING', 'order_type': 'MARKET', 'breakeven_armed': False, 'peak_r': 0.08334166750007896, 'ticks_since_peak': 1607}] |
| Daily PnL | — |
| Current Drawdown | 0.00% |
| DD State | — |
| DD Risk Multiplier | — |


## 6. Portfolio

| Symbol | Side | Qty | Entry | Stop | TP | Unrealised |
|---|---|---|---|---|---|---|
| UUSDT | LONG | 127.323115 | 0.0000 | 0.0000 | 0.0000 | +0.0000 |


### Recent Trades (last 20)

| Symbol | Side | Net PnL | R | Regime | Order |
|---|---|---|---|---|---|
| BIOUSDT | LONG | +0.73 | 0.069 | TRENDING | MARKET |
| PENGUUSDT | LONG | -0.08 | -0.007 | TRENDING | MARKET |
| PENDLEUSDT | LONG | +0.03 | 0.013 | TRENDING | MARKET |
| CHIPUSDT | SHORT | -0.04 | -0.023 | TRENDING | MARKET |
| MEGAUSDT | SHORT | -0.05 | -0.028 | TRENDING | MARKET |
| ORCAUSDT | LONG | +0.20 | 0.119 | MEAN_REVERTING | MARKET |
| SOLUSDT | SHORT | -0.09 | -0.051 | TRENDING | MARKET |
| ETHUSDT | LONG | -0.16 | -0.096 | TRENDING | MARKET |
| XRPUSDT | SHORT | -0.24 | -0.143 | TRENDING | MARKET |
| BTCUSDT | LONG | -0.17 | -0.099 | TRENDING | MARKET |
| MEGAUSDT | SHORT | -0.04 | -0.022 | MEAN_REVERTING | MARKET |
| CHIPUSDT | SHORT | -0.01 | -0.006 | TRENDING | MARKET |
| BNBUSDT | LONG | -0.08 | -0.045 | MEAN_REVERTING | MARKET |
| PENGUUSDT | SHORT | -0.05 | -0.030 | TRENDING | MARKET |
| ORCAUSDT | SHORT | -0.21 | -0.126 | TRENDING | MARKET |
| BTCUSDT | SHORT | -0.08 | -0.050 | TRENDING | MARKET |
| ETHUSDT | SHORT | -0.08 | -0.048 | TRENDING | MARKET |
| SOLUSDT | SHORT | -0.04 | -0.026 | TRENDING | MARKET |
| PENDLEUSDT | SHORT | -0.01 | -0.005 | TRENDING | MARKET |
| TRXUSDT | LONG | -0.10 | -0.009 | TRENDING | MARKET |


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
| regimes | {'TRENDING': {'n_trades': 24, 'win_rate': 0.083, 'weight': 0.5}, 'MEAN_REVERTING': {'n_trades': 4, 'win_rate': 0.25, 'weight': 1.0}} |


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
| strategies | {'TRENDING@TrendFollowing_PAPER_SPEED': {'n_trades': 20, 'edge': -0.0589, 'win_rate': 0.1, 'size_mult': 1.0, 'disabled': True, 'kill_age_s': 16138.5}, 'MEAN_REVERTING@MeanReversion_PAPER_SPEED': {'n_trades': 4, 'edge': -0.1794, 'win_rate': 0.25, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}, 'TRENDING@TrendFollowing_PAPER_SPEED_INV': {'n_trades': 4, 'edge': -0.0543, 'win_rate': 0.0, 'size_mult': 1.0, 'disabled': False, 'kill_age_s': None}} |


### Strategy Usage

| Strategy | Count/Stat |
|---|---|
| TrendFollowing | 0.8571 |
| MeanReversion | 0.1429 |
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
| CT-002 | CRITICAL | High fees (25.7% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.378 (negative expectancy)
-   Detail — 271 trades; win_rate=42.1%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **Also noted (requires attention):**
-   - TRADE DRY-SPELL — 269 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.


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


