# EOW Quant Engine — Performance Report

**Generated:** 2026-05-03 16:26 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **441 trades** with a net **LOSS** of **-168.47 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $831.53 USDT |
| Net PnL | -168.4658 USDT |
| Win Rate | 35.6% |
| Profit Factor | 0.482 |
| Sharpe Ratio | -2.237 |
| Sortino Ratio | -2.040 |
| Calmar Ratio | -0.502 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Total Fees | 71.0665 USDT |
| Total Slippage | 14.8493 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -82.5500 USDT (before all costs)
- **Fees deducted:** -71.0665 USDT
- **Slippage deducted:** -14.8493 USDT
- **Net PnL (bankable):** -168.4658 USDT

### 2.2 Trade Statistics

- Avg win: +0.9988 USDT
- Avg loss: -1.1453 USDT
- Profit factor: 0.482

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-16.9%** | **-2.24** | **-2.04** | **19.2%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 15:58:01 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=0=4%_of_avg=4,min=10%[base=45%×0.20]) |
| 15:58:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=32.4 above_sma=False regime=TRENDING) |
| 15:58:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2328.7200 rsi=53.9 |
| 15:58:02 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 15:59:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2328.5400 rsi=56.4 |
| 15:59:00 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 15:59:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=35.1 above_sma=False regime=TRENDING) |
| 15:59:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=36.5 above_sma=False regime=MEAN_REVERTING) |
| 16:00:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=35.1 above_sma=False regime=TRENDING) |
| 16:00:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2328.4400 rsi=55.7 |
| 16:00:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:00:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=35.1 above_sma=False regime=MEAN_REVERTING) |
| 16:01:01 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=31.1 |
| 16:01:01 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:01:01 | SIGNAL | 🔔 Signal LONG ETHUSDT \| EMA cross UP \| trend↑ \| RSI=62.6↑ \| ATR=1.1914 |
| 16:01:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78677.4200 rsi=40.6 |
| 16:01:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:01:46 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #5: meta_score=55.0 verdict=BLOCKED |
| 16:02:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:02:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=68.8 above_sma=True regime=TRENDING) |
| 16:02:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:02:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78677.6900 rsi=39.8 |
| 16:02:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:02:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:02:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=26.5 above_sma=False regime=TRENDING) |
| 16:02:02 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:02:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=52.1 above_sma=True regime=MEAN_REVERTING) |
| 16:03:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:03:00 | SIGNAL | ⚡ ALPHA PullbackEntry BIOUSDT score=0.587 rr=4.00 |
| 16:03:00 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PBE: EMA_DIST=0.12% RSI=33.3 RR=4.00 SCORE=0.587 |
| 16:03:00 | SIGNAL | 💰 Orchestrator BIOUSDT: score=0.517 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=2400.305123 |
| 16:03:00 | TRADE | ⚡ PAPER_SPEED market-fill override BIOUSDT: USE_LIMIT_ORDERS bypassed |
| 16:03:00 | TRADE | ✅ Opened LONG BIOUSDT qty=2400.305123 risk=4.16U [TrendFollowing \| TRENDING] |
| 16:03:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:03:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=37.3 above_sma=False regime=TRENDING) |
| 16:03:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:03:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=51.0 above_sma=True regime=MEAN_REVERTING) |
| 16:03:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:03:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=63.9 above_sma=True regime=TRENDING) |
| 16:04:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:04:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=83.4 above_sma=True regime=TRENDING) |
| 16:04:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:04:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78687.2500 rsi=56.5 |
| 16:04:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:04:04 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:04:04 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=57.5 above_sma=False regime=MEAN_REVERTING) |
| 16:05:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:05:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78692.1200 rsi=83.1 |
| 16:05:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:05:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:05:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=48.2 above_sma=False regime=MEAN_REVERTING) |
| 16:05:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:05:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=81.3 above_sma=True regime=TRENDING) |
| 16:06:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:06:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78674.1100 rsi=69.8 |
| 16:06:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:06:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:06:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=42.3 above_sma=False regime=MEAN_REVERTING) |
| 16:06:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:06:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=76.3 above_sma=True regime=TRENDING) |
| 16:07:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:07:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78658.4300 rsi=47.3 |
| 16:07:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:07:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:07:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=43.3 above_sma=False regime=MEAN_REVERTING) |
| 16:07:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:07:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2328.1800 rsi=58.6 |
| 16:07:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:08:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:08:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=32.5 above_sma=False regime=TRENDING) |
| 16:08:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:08:01 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| BB lower touch \| RSI=34.3 \| Mean=0.0001 \| TP=0.0001 |
| 16:08:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:08:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2327.0300 rsi=47.0 |
| 16:08:02 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:09:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:09:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=27.9 above_sma=False regime=TRENDING) |
| 16:09:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:09:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=37.9 above_sma=False regime=MEAN_REVERTING) |
| 16:09:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:09:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2325.5900 rsi=40.4 |
| 16:09:02 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:10:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:10:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=36.1 above_sma=False regime=TRENDING) |
| 16:10:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:10:01 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=33.2 |
| 16:10:01 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:10:04 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:10:04 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2325.8200 rsi=39.7 |
| 16:10:04 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:11:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:11:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=33.7 above_sma=False regime=TRENDING) |
| 16:11:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:11:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=35.0 above_sma=False regime=TRENDING) |
| 16:11:03 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:11:03 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=27.8 above_sma=False regime=TRENDING) |
| 16:11:46 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #6: meta_score=55.0 verdict=BLOCKED |
| 16:12:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:12:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=33.7 above_sma=False regime=TRENDING) |
| 16:12:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:12:01 | FILTER | ⚡ PAPER_SPEED bypass ETHUSDT: SLEEP_MODE(vol=6=6%_of_avg=102,min=10%[base=45%×0.20]) |
| 16:12:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=28.4 above_sma=False regime=TRENDING) |
| 16:12:09 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:12:09 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=38.9 |
| 16:12:09 | SIGNAL | 🔔 Signal SHORT LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:13:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:13:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=33.7 above_sma=False regime=TRENDING) |
| 16:13:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:13:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=41.1 above_sma=False regime=MEAN_REVERTING) |
| 16:13:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:13:02 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=27.5 above_sma=False regime=TRENDING) |
| 16:14:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:14:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=30.6 above_sma=False regime=TRENDING) |
| 16:14:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:14:02 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=33.7 above_sma=False regime=TRENDING) |
| 16:14:08 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:14:08 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=29.2 above_sma=False regime=TRENDING) |
| 16:15:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:15:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=28.9 above_sma=False regime=TRENDING) |
| 16:15:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:15:01 | FILTER | ⚡ PAPER_SPEED bypass ETHUSDT: SLEEP_MODE(vol=9=10%_of_avg=91,min=10%[base=45%×0.20]) |
| 16:15:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=19.4 above_sma=False regime=TRENDING) |
| 16:15:03 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:15:03 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=30.3 above_sma=False regime=TRENDING) |
| 16:16:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:16:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=21.8 above_sma=False regime=TRENDING) |
| 16:16:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:16:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=9.9 above_sma=False regime=TRENDING) |
| 16:16:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:16:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=27.7 above_sma=False regime=TRENDING) |
| 16:16:46 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #7: meta_score=55.0 verdict=BLOCKED |
| 16:17:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:17:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=27.9 above_sma=False regime=TRENDING) |
| 16:17:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:17:02 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=19.4 above_sma=False regime=TRENDING) |
| 16:17:03 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:17:04 | FILTER | ⚡ PAPER_SPEED bypass LUNCUSDT: SLEEP_MODE(vol=8644134=5%_of_avg=180466438,min=10%[base=45%×0.20]) |
| 16:17:04 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=9.8 above_sma=False regime=TRENDING) |
| 16:18:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:18:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=36.5 above_sma=False regime=TRENDING) |
| 16:18:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:18:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=23.6 above_sma=False regime=TRENDING) |
| 16:18:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:18:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=23.5 above_sma=False regime=TRENDING) |
| 16:19:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:19:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=34.3 above_sma=False regime=TRENDING) |
| 16:19:03 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:19:03 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=19.3 above_sma=False regime=TRENDING) |
| 16:19:05 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:19:05 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=27.6 above_sma=False regime=TRENDING) |
| 16:20:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:20:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=16.2 above_sma=False regime=TRENDING) |
| 16:20:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:20:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=32.4 above_sma=False regime=TRENDING) |
| 16:20:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:20:01 | FILTER | ⚡ PAPER_SPEED bypass LUNCUSDT: SLEEP_MODE(vol=12690404=7%_of_avg=181630830,min=10%[base=45%×0.20]) |
| 16:20:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=33.6 above_sma=False regime=TRENDING) |
| 16:21:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:21:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=31.4 above_sma=False regime=TRENDING) |
| 16:21:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:21:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=16.5 above_sma=False regime=TRENDING) |
| 16:21:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 16:21:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=36.6 above_sma=False regime=TRENDING) |
| 16:22:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:22:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=37.2 above_sma=False regime=TRENDING) |
| 16:22:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:22:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=48.5 above_sma=False regime=MEAN_REVERTING) |
| 16:22:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:22:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2323.1500 rsi=24.2 |
| 16:22:02 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:23:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:23:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78622.3200 rsi=51.2 |
| 16:23:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:23:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:23:02 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=35.5 above_sma=False regime=MEAN_REVERTING) |
| 16:23:06 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:23:06 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=49.5 above_sma=False regime=MEAN_REVERTING) |
| 16:24:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:24:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=53.7 above_sma=False regime=MEAN_REVERTING) |
| 16:24:02 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:24:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=55.6 above_sma=False regime=MEAN_REVERTING) |
| 16:24:03 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:24:03 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2325.3200 rsi=46.9 |
| 16:24:03 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:25:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:25:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78653.5000 rsi=60.0 |
| 16:25:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 16:25:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:25:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=53.5 above_sma=False regime=MEAN_REVERTING) |
| 16:25:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:25:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=65.2 above_sma=False regime=MEAN_REVERTING) |
| 16:26:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:26:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=62.2 above_sma=True regime=TRENDING) |
| 16:26:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:26:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=60.9 above_sma=True regime=MEAN_REVERTING) |
| 16:26:04 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 16:26:04 | SIGNAL | 🔔 Signal SHORT LUNCUSDT \| BB upper touch \| RSI=73.2 \| Mean=0.0001 \| TP=0.0001 |
| 16:26:04 | SIGNAL | 💰 Orchestrator LUNCUSDT: score=0.288 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=1970693.861373 |
| 16:26:04 | TRADE | ⚡ PAPER_SPEED market-fill override LUNCUSDT: USE_LIMIT_ORDERS bypassed |
| 16:26:04 | TRADE | ✅ Opened SHORT LUNCUSDT qty=1970693.861373 risk=4.16U [MeanReversion \| MEAN_REVERTING] |

---
*EOW Quant Engine V4.0 — 2026-05-03 16:26 UTC*