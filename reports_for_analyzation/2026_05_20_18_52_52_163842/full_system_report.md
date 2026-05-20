# EOW Quant Engine — Full System Report

_Generated: 2026-05-20 13:20:01 UTC_

_Mode: TIER 2: LIVE PAPER — VIRTUAL CAPITAL_  —  _Phase: FTD-025A_


## 1. Executive Summary

The engine closed **259** trades with a net **LOSS** of **-75.77 USDT**.

| Metric | Value |
|---|---|
| Win Rate | 18.1% |
| Profit Factor | 0.344 |
| Sharpe | -6.130 |
| Max Drawdown | 7.67% |
| Mode | TIER 2: LIVE PAPER — VIRTUAL CAPITAL |


## 2. Performance

| Metric | Value |
|---|---|
| Final Capital (USDT) | 924.23 |
| Net PnL (USDT) | -75.7687 |
| Total Trades | 259 |
| Win Rate | 18.1% |
| Profit Factor | 0.344 |
| Sharpe | -6.130 |
| Sortino | -7.239 |
| Calmar | -0.961 |
| Max Drawdown | 7.67% |
| Risk of Ruin | 100.00% |
| Avg Win | +0.8447 |
| Avg Loss | -0.5447 |
| Fees Paid | 38.4126 |
| Slippage | 28.8094 |
| Deployability | 55/100 (CONDITIONAL) |


## 3. Signal Pipeline

| Metric | Value |
|---|---|
| Signals / hour | 421.00 |
| Trades / hour | 0.00 |
| Rejection Rate | 0.0% |
| Signals total | 421 |
| Trades total | 0 |
| Skips total | 0 |
| Mins since trade | 224.6 |


## 4. Decision Trace (last 30 thoughts)

| Time | Level | Message |
|---|---|---|
| 13:18:57 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: CONTEXT_TOXIC: toxic_context avg=-0.3349 n=20 (rsi=23.0 above_sma=False regime=MEAN_REV |
| 13:18:58 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=32.8 above_sma=False bands=[52.0,48.0] (rsi=32.8 above_sma=False regime= |
| 13:18:58 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI_LEVEL: rsi=55.0 above_sma=True bands=[27.0,73.0] (rsi=55.0 above_sma=True regime=ME |
| 13:18:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=27.6 above_sma=False bands=[27.0,73.0] (rsi=27.6 above_sma=False regime= |
| 13:18:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=35.4 above_sma=False bands=[52.0,48.0] (rsi=35.4 above_sma=False regime |
| 13:18:58 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | SIGNAL | ⚡ ALPHA PullbackEntry NEARUSDT score=0.524 rr=5.00 |
| 13:18:58 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: LONG entry=1.6590 rsi=38.5 |
| 13:18:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:59 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=69.8 above_sma=True bands=[27.0,73.0] (rsi=69.8 above_sma=True regime=M |
| 13:19:57 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:57 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: LONG entry=1.6600 rsi=50.0 |
| 13:19:57 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:57 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=28.1 above_sma=False bands=[27.0,73.0] (rsi=28.1 above_sma=False regime= |
| 13:19:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: CONTEXT_TOXIC: toxic_context avg=-0.3349 n=20 (rsi=22.2 above_sma=False regime=MEAN_REV |
| 13:19:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:58 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=40.8 above_sma=False bands=[51.5,48.5] (rsi=40.8 above_sma=False regime |
| 13:19:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:58 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=63.4 above_sma=True bands=[27.0,73.0] (rsi=63.4 above_sma=True regime=M |
| 13:19:58 | SYSTEM | 🔬 Live Process Snapshot downloaded → eow_live_process_20260520_131958.zip (103 KB / logs=2000 rl_contexts=21 t |
| 13:20:00 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:20:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI_LEVEL: rsi=47.6 above_sma=True bands=[27.0,73.0] (rsi=47.6 above_sma=True regime=ME |
| 13:20:00 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:20:00 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=30.7 above_sma=False bands=[51.5,48.5] (rsi=30.7 above_sma=False regime= |


## 5. Risk State

| Metric | Value |
|---|---|
| Equity (USDT) | 924.23 |
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
| NEARUSDT | LONG | +0.09 | 0.019 | MEAN_REVERTING | MARKET |
| ONDOUSDT | LONG | -0.62 | -0.133 | MEAN_REVERTING | MARKET |
| NEARUSDT | LONG | -0.49 | -0.106 | MEAN_REVERTING | MARKET |
| BCHUSDT | LONG | -0.21 | -0.045 | MEAN_REVERTING | MARKET |
| NEARUSDT | LONG | -0.49 | -0.106 | MEAN_REVERTING | MARKET |
| INJUSDT | SHORT | -0.52 | -0.113 | MEAN_REVERTING | MARKET |
| TONUSDT | SHORT | -0.63 | -0.137 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.54 | -0.117 | MEAN_REVERTING | MARKET |
| BTCUSDT | SHORT | -0.35 | -0.076 | MEAN_REVERTING | MARKET |
| INJUSDT | LONG | -0.48 | -0.105 | MEAN_REVERTING | MARKET |
| BCHUSDT | LONG | -0.46 | -0.099 | MEAN_REVERTING | MARKET |
| ETHUSDT | SHORT | -0.25 | -0.054 | MEAN_REVERTING | MARKET |
| TONUSDT | SHORT | +1.04 | 0.226 | MEAN_REVERTING | MARKET |
| RONINUSDT | LONG | +0.27 | 0.058 | MEAN_REVERTING | MARKET |
| BCHUSDT | SHORT | +0.69 | 0.149 | MEAN_REVERTING | MARKET |
| INJUSDT | LONG | -0.52 | -0.113 | MEAN_REVERTING | MARKET |
| TONUSDT | LONG | -0.63 | -0.137 | MEAN_REVERTING | MARKET |
| BTCUSDT | LONG | -0.21 | -0.045 | MEAN_REVERTING | MARKET |
| ETHUSDT | LONG | +0.87 | 0.187 | MEAN_REVERTING | MARKET |
| ONDOUSDT | SHORT | -0.61 | -0.132 | MEAN_REVERTING | MARKET |


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
| CT-001 | CRITICAL | Low profit factor (0.34 < 1.0) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-002 | CRITICAL | High fees (33.6% of gross profit) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-003 | CRITICAL | Single strategy usage (none dominates) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |
| CT-004 | CRITICAL | Low win rate (18.1% < 40%) | Reduce trades + improve RR | Avoid small-notional trades to reduce fee drag |


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
| daily_risk_cap_usdt | 55.4539 |
| daily_risk_remaining | 55.4539 |
| score_bands | {'>0.90': '2.0x', '>0.80': '1.5x', '>0.70': '1.0x', '>0.60': '0.5x'} |
| module | CAPITAL_ALLOCATOR |
| phase | 4 |


## 12. Audit (Error Registry — last 50)

| Time | Code | Symbol | Extra |
|---|---|---|---|
| 1779275528.0257773 | WS_002 |  | gap=63.3s attempt=2 |
| 1779275463.4892564 | WS_001 |  | gap=60.7s attempt=1 |
| 1779275434.4891815 | WS_001 |  | gap=31.7s |


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

- **PRIMARY ISSUE:** SYSTEM IN LOSS — profit_factor=0.344 (negative expectancy)
-   Detail — 259 trades; win_rate=18.1%. Every trade destroys capital on average. Immediate action required.
-   Fix — Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **SECONDARY ISSUE:** RISK OF RUIN = 100.0% — CAPITAL IN DANGER
-   Detail — System controls active: DD state=NORMAL, risk_multiplier=1.00 (NOT yet reduced), halted=False.
-   Fix — Halve base_risk immediately. drawdown_controller auto-reduces sizing when risk_multiplier < 1.0. Activate DEFENSIVE mode. Do not add new positions until RoR drops below 50%.
- 
- **ACTIONABLE FIX (primary):** Widen RR target to ≥1.5R; tighten entry criteria; reduce trade frequency until PF recovers above 1.0. Review Section 3 (Signal Pipeline) and Section 8 (Suggestions).
- 
- **Also noted (requires attention):**
-   - TRADE DRY-SPELL — 225 min since last trade: Trade Activator should be auto-relaxing thresholds after 60 min.


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


