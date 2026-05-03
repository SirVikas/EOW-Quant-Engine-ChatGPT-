# EOW Quant Engine — Performance Report

**Generated:** 2026-05-03 14:55 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **432 trades** with a net **LOSS** of **-158.78 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $841.22 USDT |
| Net PnL | -158.7847 USDT |
| Win Rate | 36.1% |
| Profit Factor | 0.496 |
| Sharpe Ratio | -2.135 |
| Sortino Ratio | -1.943 |
| Calmar Ratio | -0.483 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Total Fees | 69.9263 USDT |
| Total Slippage | 13.9942 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -74.8642 USDT (before all costs)
- **Fees deducted:** -69.9263 USDT
- **Slippage deducted:** -13.9942 USDT
- **Net PnL (bankable):** -158.7847 USDT

### 2.2 Trade Statistics

- Avg win: +1.0033 USDT
- Avg loss: -1.1424 USDT
- Profit factor: 0.496

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-15.9%** | **-2.13** | **-1.94** | **19.2%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 14:11:05 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:11:05 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0562 rsi=47.8 |
| 14:11:05 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:11:16 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:11:16 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=52.5 above_sma=True regime=MEAN_REVERTING) |
| 14:12:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:12:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=56.2 above_sma=True regime=MEAN_REVERTING) |
| 14:12:02 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:12:02 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=55.4 above_sma=True regime=MEAN_REVERTING) |
| 14:12:03 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:12:03 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=55.0 above_sma=True regime=MEAN_REVERTING) |
| 14:12:13 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:12:13 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0562 rsi=50.0 |
| 14:12:13 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:12:13 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BIOUSDT |
| 14:13:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:13:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=59.4 above_sma=True regime=MEAN_REVERTING) |
| 14:13:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:13:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0562 rsi=50.0 |
| 14:13:01 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:13:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BIOUSDT |
| 14:13:10 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:13:10 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=52.5 above_sma=True regime=MEAN_REVERTING) |
| 14:13:13 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:13:13 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=52.4 above_sma=True regime=MEAN_REVERTING) |
| 14:14:01 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:14:01 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=59.4 above_sma=True regime=MEAN_REVERTING) |
| 14:14:04 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:14:04 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2325.5600 rsi=68.9 |
| 14:14:04 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:14:04 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:14:04 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0564 rsi=52.2 |
| 14:14:04 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:14:04 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BIOUSDT |
| 14:14:07 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:14:07 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0690 rsi=54.5 |
| 14:14:07 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:14:07 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORCAUSDT |
| 14:15:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:15:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=66.5 above_sma=True regime=TRENDING) |
| 14:15:02 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:15:02 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0565 rsi=52.2 |
| 14:15:02 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:15:02 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BIOUSDT |
| 14:15:02 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:15:02 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=56.7 above_sma=True regime=MEAN_REVERTING) |
| 14:15:26 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:15:26 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0670 rsi=55.8 |
| 14:15:26 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:15:26 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORCAUSDT |
| 14:16:01 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:16:01 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0670 rsi=57.1 |
| 14:16:01 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:16:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORCAUSDT |
| 14:16:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:16:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=64.0 above_sma=True regime=TRENDING) |
| 14:16:03 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:16:03 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0565 rsi=52.2 |
| 14:16:03 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:16:03 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BIOUSDT |
| 14:16:06 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:16:06 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=62.7 above_sma=True regime=MEAN_REVERTING) |
| 14:17:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:17:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2326.5400 rsi=60.7 |
| 14:17:01 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:17:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ETHUSDT |
| 14:17:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:17:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0565 rsi=54.5 |
| 14:17:01 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:17:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BIOUSDT |
| 14:17:02 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:17:02 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=MEAN_REVERTING) |
| 14:17:04 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:17:04 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0650 rsi=53.5 |
| 14:17:04 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:17:04 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORCAUSDT |
| 14:18:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:18:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2324.8400 rsi=41.1 |
| 14:18:01 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:18:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ETHUSDT |
| 14:18:01 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:18:01 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=63.6 above_sma=True regime=MEAN_REVERTING) |
| 14:18:02 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:18:02 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0670 rsi=59.5 |
| 14:18:02 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:18:02 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORCAUSDT |
| 14:18:03 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:18:03 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0562 rsi=50.0 |
| 14:18:03 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:18:03 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BIOUSDT |
| 14:19:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:19:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0561 rsi=48.0 |
| 14:19:01 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:19:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BIOUSDT |
| 14:19:01 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:19:01 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0650 rsi=56.8 |
| 14:19:01 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:19:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORCAUSDT |
| 14:19:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:19:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2323.9200 rsi=42.7 |
| 14:19:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:19:03 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:19:03 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=62.7 above_sma=True regime=MEAN_REVERTING) |
| 14:20:00 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:20:00 | FILTER | ⚡ PAPER_SPEED bypass ORDIUSDT: SLEEP_MODE(vol=91=8%_of_avg=1180,min=10%[base=45%×0.20]) |
| 14:20:01 | SIGNAL | ⚡ PAPER_SPEED fallback ORDIUSDT: SHORT entry=5.0570 rsi=65.8 |
| 14:20:01 | SIGNAL | 🔔 Signal SHORT ORDIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:20:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:20:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0562 rsi=31.6 |
| 14:20:01 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:20:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) BIOUSDT |
| 14:20:01 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:20:01 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0680 rsi=57.8 |
| 14:20:01 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:20:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORCAUSDT |
| 14:20:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:20:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2325.2900 rsi=51.6 |
| 14:20:01 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:20:01 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ETHUSDT |
| 14:21:01 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:21:01 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=55.2 above_sma=True regime=MEAN_REVERTING) |
| 14:21:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:21:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=35.3 above_sma=True regime=MEAN_REVERTING) |
| 14:21:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:21:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2323.5800 rsi=39.8 |
| 14:21:02 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:21:05 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:21:05 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0660 rsi=53.3 |
| 14:21:05 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:21:05 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORCAUSDT |
| 14:22:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:22:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=31.3 above_sma=True regime=MEAN_REVERTING) |
| 14:22:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:22:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=36.5 above_sma=False regime=TRENDING) |
| 14:22:11 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:22:11 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=49.3 above_sma=False regime=MEAN_REVERTING) |
| 14:22:15 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:22:15 | FILTER | ⚡ PAPER_SPEED bypass ORCAUSDT: SLEEP_MODE(vol=159=5%_of_avg=3090,min=10%[base=45%×0.20]) |
| 14:22:15 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0660 rsi=57.1 |
| 14:22:15 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:22:15 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORCAUSDT |
| 14:22:15 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.287 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=81.851799 |
| 14:22:15 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 14:22:15 | TRADE | ✅ Opened LONG ORCAUSDT qty=81.851799 risk=4.23U [TrendFollowing \| TRENDING] |
| 14:23:02 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:23:02 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=33.3 above_sma=True regime=MEAN_REVERTING) |
| 14:23:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:23:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2322.8700 rsi=43.1 |
| 14:23:02 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:23:02 | SIGNAL | 💰 Orchestrator ETHUSDT: score=0.280 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.072800 |
| 14:23:02 | TRADE | ⚡ PAPER_SPEED market-fill override ETHUSDT: USE_LIMIT_ORDERS bypassed |
| 14:23:02 | TRADE | ✅ Opened SHORT ETHUSDT qty=0.072800 risk=4.23U [TrendFollowing \| TRENDING] |
| 14:23:02 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:23:02 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=50.6 above_sma=True regime=MEAN_REVERTING) |
| 14:24:03 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:24:03 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=37.5 above_sma=True regime=MEAN_REVERTING) |
| 14:24:13 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:24:13 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=55.3 above_sma=True regime=MEAN_REVERTING) |
| 14:25:01 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:25:01 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=52.3 above_sma=True regime=MEAN_REVERTING) |
| 14:25:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:25:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0568 rsi=68.7 |
| 14:25:01 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:25:01 | SIGNAL | 💰 Orchestrator BIOUSDT: score=0.250 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=2977.215071 |
| 14:25:01 | TRADE | ⚡ PAPER_SPEED market-fill override BIOUSDT: USE_LIMIT_ORDERS bypassed |
| 14:25:01 | TRADE | ✅ Opened SHORT BIOUSDT qty=2977.215071 risk=4.23U [MeanReversion \| MEAN_REVERTING] |
| 14:26:06 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:26:06 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=56.8 above_sma=True regime=MEAN_REVERTING) |
| 14:27:01 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:27:01 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=55.7 above_sma=True regime=MEAN_REVERTING) |
| 14:28:11 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:28:11 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=50.7 above_sma=True regime=MEAN_REVERTING) |
| 14:29:02 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:29:02 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=50.7 above_sma=True regime=MEAN_REVERTING) |
| 14:30:07 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 14:30:07 | SIGNAL | ⚡ PAPER_SPEED fallback ORDIUSDT: LONG entry=5.0550 rsi=46.4 |
| 14:30:07 | SIGNAL | 🔔 Signal LONG ORDIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:07 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ORDIUSDT |
| 14:30:07 | SIGNAL | 💰 Orchestrator ORDIUSDT: score=0.146 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=33.453178 |
| 14:30:07 | TRADE | ⚡ PAPER_SPEED market-fill override ORDIUSDT: USE_LIMIT_ORDERS bypassed |
| 14:30:07 | TRADE | ✅ Opened LONG ORDIUSDT qty=33.453178 risk=4.23U [TrendFollowing \| TRENDING] |
| 14:34:39 | TRADE | Position closed [SL] ORCAUSDT @ 2.063 |
| 14:40:11 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:40:11 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0630 rsi=40.0 |
| 14:40:11 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:40:11 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.624 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=81.924086 |
| 14:40:11 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 14:40:11 | TRADE | ✅ Opened SHORT ORCAUSDT qty=81.924086 risk=4.23U [TrendFollowing \| TRENDING] |
| 14:43:40 | TRADE | Position closed [SL] ORCAUSDT @ 2.07 |
| 14:49:02 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:49:02 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0720 rsi=75.0 |
| 14:49:02 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:49:02 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.156 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=81.490006 |
| 14:49:02 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 14:49:02 | TRADE | ✅ Opened SHORT ORCAUSDT qty=81.490006 risk=4.22U [MeanReversion \| MEAN_REVERTING] |
| 14:49:44 | TRADE | Position closed [SL] BIOUSDT @ 0.0577 |
| 14:51:55 | TRADE | Position closed [SL] ORDIUSDT @ 5.059 |
| 14:55:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 14:55:01 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.540 |
| 14:55:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=TRENDING) |

---
*EOW Quant Engine V4.0 — 2026-05-03 14:55 UTC*