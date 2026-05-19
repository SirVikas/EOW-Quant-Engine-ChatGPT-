# EOW Quant Engine — Performance Report

**Generated:** 2026-05-19 14:59 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **203 trades** with a net **LOSS** of **-64.09 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $935.90 USDT |
| Net PnL | -64.0950 USDT |
| Win Rate | 18.2% |
| Profit Factor | 0.329 |
| Sharpe Ratio | -6.259 |
| Sortino Ratio | -7.348 |
| Calmar Ratio | -1.241 |
| Max Drawdown | 6.41% |
| Risk of Ruin | 100.00% |
| Total Fees | 30.1463 USDT |
| Total Slippage | 22.6097 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -11.3390 USDT (before all costs)
- **Fees deducted:** -30.1463 USDT
- **Slippage deducted:** -22.6097 USDT
- **Net PnL (bankable):** -64.0950 USDT

### 2.2 Trade Statistics

- Avg win: +0.8506 USDT
- Avg loss: -0.5757 USDT
- Profit factor: 0.329

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-6.4%** | **-6.26** | **-7.35** | **6.4%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 14:20:46 | SIGNAL | 🎯 CONSISTENCY BTCUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 14:20:46 | SIGNAL | 💰 Orchestrator BTCUSDT: score=0.148 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.002454 |
| 14:20:46 | TRADE | ⚡ PAPER_SPEED market-fill override BTCUSDT: USE_LIMIT_ORDERS bypassed |
| 14:20:46 | TRADE | ✅ Opened LONG BTCUSDT qty=0.002454 risk=4.69U [MeanReversion \| MEAN_REVERTING] |
| 14:20:47 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=40.6 above_sma=False bands=[38.0,62.0] (rsi=40.6 above_sma=False regime=MEAN_REVERTING) |
| 14:20:47 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_CRASH_GUARD LONG: rsi=36.4<38.0 but prev=47.1≥40.0 (first-touch crash) (rsi=36.4 above_sma=False regime=MEAN_REVERTING) |
| 14:20:48 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=52.5 above_sma=False bands=[38.0,62.0] (rsi=52.5 above_sma=False regime=MEAN_REVERTING) |
| 14:20:49 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=50.0 above_sma=False bands=[38.0,62.0] (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 14:20:50 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI_LEVEL: rsi=40.3 above_sma=False bands=[38.0,62.0] (rsi=40.3 above_sma=False regime=MEAN_REVERTING) |
| 14:20:52 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=36.4 above_sma=False bands=[47.0,53.0] (rsi=36.4 above_sma=False regime=TRENDING) |
| 14:21:22 | TRADE | [TM] BTCUSDT TIME_EXIT @ 76365.9700 (Fast-fail: 0.6min r=-0.590<-0.45) |
| 14:21:22 | TRADE | Position closed [SL] BTCUSDT @ 76365.97 |
| 14:23:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:23:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_CRASH_GUARD LONG: rsi=34.1<38.0 but prev=40.6≥40.0 (first-touch crash) (rsi=34.1 above_sma=False regime=MEAN_REVERTING) |
| 14:23:00 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:23:00 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=46.4 above_sma=False bands=[38.0,62.0] (rsi=46.4 above_sma=False regime=MEAN_REVERTING) |
| 14:23:01 | SIGNAL | 📈 STREAK BCHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:23:01 | FILTER | ⚡ PAPER_SPEED BCHUSDT: RSI_LEVEL: rsi=40.7 above_sma=False bands=[38.0,62.0] (rsi=40.7 above_sma=False regime=MEAN_REVERTING) |
| 14:23:01 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:23:01 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI_CRASH_GUARD LONG: rsi=33.8<38.0 but prev=40.3≥40.0 (first-touch crash) (rsi=33.8 above_sma=False regime=MEAN_REVERTING) |
| 14:23:02 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:23:02 | SIGNAL | ⚡ ALPHA TrendBreakout LTCUSDT score=0.760 rr=5.00 |
| 14:23:02 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=28.8 above_sma=False bands=[47.0,53.0] (rsi=28.8 above_sma=False regime=TRENDING) |
| 14:23:03 | SIGNAL | 📈 STREAK FIDAUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:23:03 | SIGNAL | ⚡ PAPER_SPEED fallback FIDAUSDT: LONG entry=0.0199 rsi=16.0 |
| 14:23:03 | SIGNAL | 🔔 Signal LONG FIDAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:23:03 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) FIDAUSDT |
| 14:23:03 | SIGNAL | ⚡ LCC_OVERRIDE FIDAUSDT: state=PAUSED cl=3 [bypass=active, size not reduced] |
| 14:23:03 | SIGNAL | ⚠️ ALLOC_ZERO FIDAUSDT: score=0.192 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:23:03 | SIGNAL | 🎯 CONSISTENCY FIDAUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 14:23:03 | SIGNAL | 💰 Orchestrator FIDAUSDT: score=0.192 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=9409.988322 |
| 14:23:03 | TRADE | ⚡ PAPER_SPEED market-fill override FIDAUSDT: USE_LIMIT_ORDERS bypassed |
| 14:23:03 | TRADE | ✅ Opened LONG FIDAUSDT qty=9409.988322 risk=4.69U [MeanReversion \| MEAN_REVERTING] |
| 14:23:04 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:23:04 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: LONG entry=1.6110 rsi=31.2 |
| 14:23:04 | SIGNAL | 🔔 Signal LONG NEARUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:23:04 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) NEARUSDT |
| 14:23:04 | SIGNAL | ⚡ LCC_OVERRIDE NEARUSDT: state=PAUSED cl=3 [bypass=active, size not reduced] |
| 14:23:04 | SIGNAL | ⚠️ ALLOC_ZERO NEARUSDT: score=0.149 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:23:04 | SIGNAL | 🎯 CONSISTENCY NEARUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 14:23:04 | SIGNAL | 💰 Orchestrator NEARUSDT: score=0.149 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=116.412829 |
| 14:23:04 | TRADE | ⚡ PAPER_SPEED market-fill override NEARUSDT: USE_LIMIT_ORDERS bypassed |
| 14:23:04 | TRADE | ✅ Opened LONG NEARUSDT qty=116.412829 risk=4.69U [MeanReversion \| MEAN_REVERTING] |
| 14:23:04 | SIGNAL | 📈 STREAK AIGENSYNUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:23:05 | FILTER | ⚡ PAPER_SPEED AIGENSYNUSDT: RSI_LEVEL: rsi=38.5 above_sma=False bands=[38.0,62.0] (rsi=38.5 above_sma=False regime=MEAN_REVERTING) |
| 14:23:05 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:23:05 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=50.0 above_sma=False bands=[38.0,62.0] (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 14:24:20 | SIGNAL | 📈 STREAK AIGENSYNUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:24:20 | FILTER | ⚡ PAPER_SPEED AIGENSYNUSDT: RSI_LEVEL: rsi=26.2 above_sma=False bands=[47.0,53.0] (rsi=26.2 above_sma=False regime=TRENDING) |
| 14:24:20 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:24:20 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2100.1900 rsi=13.6 |
| 14:24:20 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:24:20 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ETHUSDT |
| 14:24:20 | SIGNAL | ⚡ LCC_OVERRIDE ETHUSDT: state=PAUSED cl=3 [bypass=active, size not reduced] |
| 14:24:20 | SIGNAL | ⚠️ ALLOC_ZERO ETHUSDT: score=0.111 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:24:20 | SIGNAL | 🎯 CONSISTENCY ETHUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 14:24:20 | SIGNAL | 💰 Orchestrator ETHUSDT: score=0.111 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.089297 |
| 14:24:20 | TRADE | ⚡ PAPER_SPEED market-fill override ETHUSDT: USE_LIMIT_ORDERS bypassed |
| 14:24:20 | TRADE | ✅ Opened LONG ETHUSDT qty=0.089297 risk=4.69U [MeanReversion \| MEAN_REVERTING] |
| 14:24:21 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:24:21 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=10.9 above_sma=False bands=[47.0,53.0] (rsi=10.9 above_sma=False regime=TRENDING) |
| 14:24:21 | SIGNAL | 📈 STREAK TONUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:24:21 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9790 rsi=14.0 |
| 14:24:21 | SIGNAL | 🔔 Signal LONG TONUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:24:21 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) TONUSDT |
| 14:24:21 | SIGNAL | ⚡ LCC_OVERRIDE TONUSDT: state=PAUSED cl=3 [bypass=active, size not reduced] |
| 14:24:21 | SIGNAL | ⚠️ ALLOC_ZERO TONUSDT: score=0.248 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:24:21 | SIGNAL | 🎯 CONSISTENCY TONUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 14:24:21 | SIGNAL | 💰 Orchestrator TONUSDT: score=0.248 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=94.765572 |
| 14:24:21 | TRADE | ⚡ PAPER_SPEED market-fill override TONUSDT: USE_LIMIT_ORDERS bypassed |
| 14:24:21 | TRADE | ✅ Opened LONG TONUSDT qty=94.765572 risk=4.69U [MeanReversion \| MEAN_REVERTING] |
| 14:24:22 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:24:22 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=40.7 above_sma=False bands=[38.0,62.0] (rsi=40.7 above_sma=False regime=MEAN_REVERTING) |
| 14:24:23 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:24:23 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: LONG entry=3.4510 rsi=15.8 |
| 14:24:23 | SIGNAL | 🔔 Signal LONG UNIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:24:24 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) UNIUSDT |
| 14:24:24 | SIGNAL | ⚡ LCC_OVERRIDE UNIUSDT: state=PAUSED cl=3 [bypass=active, size not reduced] |
| 14:24:24 | SIGNAL | ⚠️ ALLOC_ZERO UNIUSDT: score=0.068 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:24:24 | SIGNAL | 🎯 CONSISTENCY UNIUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 14:24:24 | SIGNAL | 💰 Orchestrator UNIUSDT: score=0.068 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=54.343978 |
| 14:24:24 | TRADE | ⚡ PAPER_SPEED market-fill override UNIUSDT: USE_LIMIT_ORDERS bypassed |
| 14:24:24 | TRADE | ✅ Opened LONG UNIUSDT qty=54.343978 risk=4.69U [MeanReversion \| MEAN_REVERTING] |
| 14:24:26 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:24:26 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=44.4 above_sma=False bands=[38.0,62.0] (rsi=44.4 above_sma=False regime=MEAN_REVERTING) |
| 14:24:27 | SIGNAL | 📈 STREAK BCHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:24:27 | FILTER | ⚡ PAPER_SPEED BCHUSDT: RSI_CRASH_GUARD LONG: rsi=26.5<38.0 but prev=40.7≥40.0 (first-touch crash) (rsi=26.5 above_sma=False regime=MEAN_REVERTING) |
| 14:24:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #208: meta_score=47.2 verdict=— |
| 14:26:02 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:26:02 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=41.4 above_sma=False bands=[38.0,62.0] (rsi=41.4 above_sma=False regime=MEAN_REVERTING) |
| 14:26:02 | SIGNAL | 📈 STREAK AIGENSYNUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:26:02 | SIGNAL | ⚡ PAPER_SPEED fallback AIGENSYNUSDT: LONG entry=0.0357 rsi=26.6 |
| 14:26:02 | SIGNAL | 🔔 Signal LONG AIGENSYNUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:26:02 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) AIGENSYNUSDT |
| 14:26:02 | SIGNAL | ⚡ LCC_OVERRIDE AIGENSYNUSDT: state=PAUSED cl=3 [bypass=active, size not reduced] |
| 14:26:02 | SIGNAL | ⚠️ ALLOC_ZERO AIGENSYNUSDT: score=0.150 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:26:02 | SIGNAL | 🎯 CONSISTENCY AIGENSYNUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 14:26:02 | SIGNAL | 💰 Orchestrator AIGENSYNUSDT: score=0.150 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=5253.251184 |
| 14:26:02 | TRADE | ⚡ PAPER_SPEED market-fill override AIGENSYNUSDT: USE_LIMIT_ORDERS bypassed |
| 14:26:02 | TRADE | ✅ Opened LONG AIGENSYNUSDT qty=5253.251184 risk=4.69U [MeanReversion \| MEAN_REVERTING] |
| 14:26:04 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:26:04 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=13.3 above_sma=False bands=[47.0,53.0] (rsi=13.3 above_sma=False regime=TRENDING) |
| 14:26:04 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:26:04 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=50.0 above_sma=False bands=[38.0,62.0] (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 14:26:13 | SIGNAL | 📈 STREAK BCHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 14:26:13 | SIGNAL | ⚡ PAPER_SPEED fallback BCHUSDT: LONG entry=380.1000 rsi=29.8 |
| 14:26:13 | SIGNAL | 🔔 Signal LONG BCHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:26:13 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BCHUSDT |
| 14:26:13 | SIGNAL | ⚡ LCC_OVERRIDE BCHUSDT: state=PAUSED cl=3 [bypass=active, size not reduced] |
| 14:26:13 | SIGNAL | ⚠️ ALLOC_ZERO BCHUSDT: score=0.191 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:26:13 | SIGNAL | 🎯 CONSISTENCY BCHUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 14:26:13 | SIGNAL | 💰 Orchestrator BCHUSDT: score=0.191 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.493399 |
| 14:26:13 | TRADE | ⚡ PAPER_SPEED market-fill override BCHUSDT: USE_LIMIT_ORDERS bypassed |
| 14:26:13 | TRADE | ✅ Opened LONG BCHUSDT qty=0.493399 risk=4.69U [MeanReversion \| MEAN_REVERTING] |
| 14:26:59 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:26:59 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:26:59 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=48.1 above_sma=False bands=[38.0,62.0] (rsi=48.1 above_sma=False regime=MEAN_REVERTING) |
| 14:26:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:26:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:26:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=76431.5800 rsi=22.6 |
| 14:26:59 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:26:59 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BTCUSDT |
| 14:26:59 | SIGNAL | ⚡ LCC_OVERRIDE BTCUSDT: state=PAUSED cl=3 [bypass=active, size not reduced] |
| 14:26:59 | SIGNAL | ⚠️ ALLOC_ZERO BTCUSDT: score=0.484 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:26:59 | SIGNAL | 🎯 CONSISTENCY BTCUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 14:26:59 | SIGNAL | 💰 Orchestrator BTCUSDT: score=0.484 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.002454 |
| 14:26:59 | TRADE | ⚡ PAPER_SPEED market-fill override BTCUSDT: USE_LIMIT_ORDERS bypassed |
| 14:26:59 | TRADE | ✅ Opened LONG BTCUSDT qty=0.002454 risk=4.69U [MeanReversion \| MEAN_REVERTING] |
| 14:27:02 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:27:02 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:27:02 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=57.1 above_sma=False bands=[38.0,62.0] (rsi=57.1 above_sma=False regime=MEAN_REVERTING) |
| 14:27:02 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:27:02 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:27:02 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=17.1 above_sma=False bands=[47.0,53.0] (rsi=17.1 above_sma=False regime=TRENDING) |
| 14:27:43 | TRADE | [TM] UNIUSDT BE: SL→3.4558 (R=1.57≥1.5 mode=TREND_FOLLOW → SL→BE) |
| 14:28:01 | TRADE | [TM] ETHUSDT BE: SL→2103.1303 (R=1.51≥1.5 mode=TREND_FOLLOW → SL→BE) |
| 14:28:10 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:28:10 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:28:10 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=45.9 above_sma=False bands=[38.0,62.0] (rsi=45.9 above_sma=False regime=MEAN_REVERTING) |
| 14:28:13 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:28:13 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:28:13 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=57.1 above_sma=True bands=[38.0,62.0] (rsi=57.1 above_sma=True regime=MEAN_REVERTING) |
| 14:28:17 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:28:17 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:28:17 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=31.1 above_sma=False bands=[47.0,53.0] (rsi=31.1 above_sma=False regime=TRENDING) |
| 14:29:15 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:29:15 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:29:15 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_CRASH_GUARD LONG: rsi=37.3<38.0 but prev=45.9≥40.0 (first-touch crash) (rsi=37.3 above_sma=False regime=MEAN_REVERTING) |
| 14:29:15 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:29:15 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:29:15 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=23.1 above_sma=False bands=[47.0,53.0] (rsi=23.1 above_sma=False regime=TRENDING) |
| 14:29:15 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:29:15 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:29:15 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=42.9 above_sma=False bands=[38.0,62.0] (rsi=42.9 above_sma=False regime=MEAN_REVERTING) |
| 14:29:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #209: meta_score=47.2 verdict=— |
| 14:30:17 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:30:17 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:30:17 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=23.5 above_sma=False bands=[47.0,53.0] (rsi=23.5 above_sma=False regime=TRENDING) |
| 14:30:27 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:30:27 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:30:27 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=38.9 above_sma=False bands=[38.0,62.0] (rsi=38.9 above_sma=False regime=MEAN_REVERTING) |
| 14:31:06 | TRADE | [TM] FIDAUSDT BE: SL→0.0200 (R=1.56≥1.5 mode=TREND_FOLLOW → SL→BE) |
| 14:31:29 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:31:29 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.430 |
| 14:31:29 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=57.1 above_sma=True bands=[38.0,62.0] (rsi=57.1 above_sma=True regime=MEAN_REVERTING) |
| 14:31:31 | TRADE | [TM] NEARUSDT TIME_EXIT @ 1.6110 (Stale: 8.5min r=0.000<0.15) |
| 14:31:32 | TRADE | Position closed [SL] NEARUSDT @ 1.611 |
| 14:33:07 | TRADE | [TM] TONUSDT TIME_EXIT @ 1.9790 (Stale: 8.8min r=0.000<0.15) |
| 14:33:07 | TRADE | Position closed [SL] TONUSDT @ 1.979 |
| 14:34:06 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 14:34:06 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI_LEVEL: rsi=24.0 above_sma=False bands=[47.0,53.0] (rsi=24.0 above_sma=False regime=TRENDING) |
| 14:34:06 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 14:34:06 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=39.6 above_sma=False bands=[38.0,62.0] (rsi=39.6 above_sma=False regime=MEAN_REVERTING) |
| 14:34:07 | SIGNAL | 📈 STREAK UUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 14:34:07 | FILTER | ⚡ PAPER_SPEED UUSDT: RSI_LEVEL: rsi=57.1 above_sma=True bands=[38.0,62.0] (rsi=57.1 above_sma=True regime=MEAN_REVERTING) |
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
| 14:35:24 | SIGNAL | 🔔 Signal LONG SPKUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:35:24 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) SPKUSDT |
| 14:35:24 | SIGNAL | ⚡ LCC_OVERRIDE SPKUSDT: state=REDUCING cl=3 [bypass=active, size not reduced] |
| 14:35:24 | SIGNAL | ⚠️ ALLOC_ZERO SPKUSDT: score=0.132 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 14:35:24 | SIGNAL | 💰 Orchestrator SPKUSDT: score=0.132 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=6670.280671 |
| 14:35:24 | TRADE | ⚡ PAPER_SPEED market-fill override SPKUSDT: USE_LIMIT_ORDERS bypassed |
| 14:35:24 | TRADE | ✅ Opened LONG SPKUSDT qty=6670.280671 risk=4.68U [MeanReversion \| MEAN_REVERTING] |
| 14:39:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #211: meta_score=46.9 verdict=— |
| 14:43:45 | TRADE | [TM] SPKUSDT TIME_EXIT @ 0.0281 (Stale: 8.3min r=0.141<0.15) |
| 14:43:45 | TRADE | Position closed [SL] SPKUSDT @ 0.028077 |
| 14:44:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #212: meta_score=46.8 verdict=— |
| 14:49:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #213: meta_score=46.8 verdict=— |
| 14:54:34 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #214: meta_score=46.8 verdict=— |

---
*EOW Quant Engine V4.0 — 2026-05-19 14:59 UTC*