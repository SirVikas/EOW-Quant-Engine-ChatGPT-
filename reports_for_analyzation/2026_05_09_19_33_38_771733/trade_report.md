# EOW Quant Engine — Performance Report

**Generated:** 2026-05-09 13:58 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **823 trades** with a net **LOSS** of **-246.25 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $753.75 USDT |
| Net PnL | -246.2477 USDT |
| Win Rate | 26.9% |
| Profit Factor | 0.486 |
| Sharpe Ratio | -2.270 |
| Sortino Ratio | -2.273 |
| Calmar Ratio | -0.288 |
| Max Drawdown | 26.19% |
| Risk of Ruin | 100.00% |
| Total Fees | 114.8958 USDT |
| Total Slippage | 47.7213 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -83.6306 USDT (before all costs)
- **Fees deducted:** -114.8958 USDT
- **Slippage deducted:** -47.7213 USDT
- **Net PnL (bankable):** -246.2477 USDT

### 2.2 Trade Statistics

- Avg win: +1.0523 USDT
- Avg loss: -0.7954 USDT
- Profit factor: 0.486

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-24.6%** | **-2.27** | **-2.27** | **26.2%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 13:49:08 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=MEAN_REVERTING) |
| 13:49:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=48.4 above_sma=False regime=TRENDING) |
| 13:49:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=58.2 above_sma=True regime=MEAN_REVERTING) |
| 13:49:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=57.9 above_sma=True regime=TRENDING) |
| 13:49:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=27.8 above_sma=False regime=TRENDING) |
| 13:49:59 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=64.3 above_sma=True regime=MEAN_REVERTING) |
| 13:49:59 | SIGNAL | ⚡ PAPER_SPEED fallback SAHARAUSDT: LONG entry=0.0366 rsi=28.5 |
| 13:49:59 | SIGNAL | 🔔 Signal LONG SAHARAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 13:49:59 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) SAHARAUSDT |
| 13:49:59 | SIGNAL | ⚠️ ALLOC_ZERO SAHARAUSDT: score=0.308 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 13:49:59 | SIGNAL | 💰 Orchestrator SAHARAUSDT: score=0.308 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=4130.265542 |
| 13:49:59 | TRADE | ⚡ PAPER_SPEED market-fill override SAHARAUSDT: USE_LIMIT_ORDERS bypassed |
| 13:49:59 | TRADE | ✅ Opened LONG SAHARAUSDT qty=4130.265542 risk=3.78U [MeanReversion \| MEAN_REVERTING] |
| 13:49:59 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=36.1 above_sma=False regime=TRENDING) |
| 13:50:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 13:50:04 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 13:50:04 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=45.8 above_sma=False regime=TRENDING) |
| 13:50:05 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=43.3 above_sma=False regime=TRENDING) |
| 13:50:06 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 13:50:07 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=40.0 above_sma=False regime=TRENDING) |
| 13:50:10 | FILTER | ⚡ PAPER_SPEED bypass UNIUSDT: SLEEP_MODE(vol=26=2%_of_avg=1473,min=10%[base=45%×0.20]) |
| 13:50:10 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=47.4 above_sma=False regime=TRENDING) |
| 13:50:19 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=26.7 above_sma=True regime=MEAN_REVERTING) |
| 13:50:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=MEAN_REVERTING) |
| 13:50:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=40.7 above_sma=False regime=TRENDING) |
| 13:50:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=58.2 above_sma=True regime=MEAN_REVERTING) |
| 13:50:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=44.4 above_sma=False regime=TRENDING) |
| 13:50:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=36.3 above_sma=False regime=TRENDING) |
| 13:50:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=42.6 above_sma=False regime=TRENDING) |
| 13:51:01 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=44.4 above_sma=False regime=TRENDING) |
| 13:51:01 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=43.7 above_sma=False regime=TRENDING) |
| 13:51:01 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=25.5 above_sma=False regime=TRENDING) |
| 13:51:02 | FILTER | ⚡ PAPER_SPEED bypass ASTERUSDT: SLEEP_MODE(vol=517=1%_of_avg=71973,min=10%[base=45%×0.20]) |
| 13:51:02 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=33.3 above_sma=True regime=MEAN_REVERTING) |
| 13:51:04 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=39.4 above_sma=False regime=TRENDING) |
| 13:51:04 | FILTER | ⚡ PAPER_SPEED bypass NEARUSDT: SLEEP_MODE(vol=643=2%_of_avg=26600,min=10%[base=45%×0.20]) |
| 13:51:04 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=61.5 above_sma=True regime=TRENDING) |
| 13:51:06 | FILTER | ⚡ PAPER_SPEED bypass ARBUSDT: SLEEP_MODE(vol=10994=4%_of_avg=255539,min=10%[base=45%×0.20]) |
| 13:51:06 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=39.4 above_sma=False regime=TRENDING) |
| 13:51:23 | TRADE | [TM] SAHARAUSDT TIME_EXIT @ 0.0364 (Fast-fail: 1.4min r=-0.450<-0.45) |
| 13:51:23 | TRADE | Position closed [SL] SAHARAUSDT @ 0.03638 |
| 13:51:42 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=30.8 above_sma=False regime=TRENDING) |
| 13:51:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=52.9 above_sma=True regime=MEAN_REVERTING) |
| 13:51:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=32.2 above_sma=False regime=TRENDING) |
| 13:51:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=34.7 above_sma=False regime=TRENDING) |
| 13:52:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=42.1 above_sma=False regime=TRENDING) |
| 13:52:00 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=48.4 above_sma=False regime=TRENDING) |
| 13:52:00 | SIGNAL | ⚡ PAPER_SPEED fallback GALAUSDT: SHORT entry=0.0041 rsi=57.1 |
| 13:52:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=31.2 above_sma=False regime=TRENDING) |
| 13:52:01 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 13:52:01 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=46.7 above_sma=False regime=TRENDING) |
| 13:52:01 | FILTER | ⚡ PAPER_SPEED bypass FILUSDT: SLEEP_MODE(vol=328=4%_of_avg=7701,min=10%[base=45%×0.20]) |
| 13:52:01 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=33.3 above_sma=False regime=TRENDING) |
| 13:52:04 | SIGNAL | ⚡ PAPER_SPEED fallback OPUSDT: SHORT entry=0.1643 rsi=53.8 |
| 13:52:08 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=58.9 above_sma=True regime=MEAN_REVERTING) |
| 13:52:08 | FILTER | ⚡ PAPER_SPEED bypass ARBUSDT: SLEEP_MODE(vol=2635=1%_of_avg=253806,min=10%[base=45%×0.20]) |
| 13:52:08 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=46.4 above_sma=False regime=TRENDING) |
| 13:52:24 | SIGNAL | ⚡ PAPER_SPEED fallback ASTERUSDT: LONG entry=0.7090 rsi=25.0 |
| 13:52:24 | SIGNAL | 🔔 Signal LONG ASTERUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 13:52:24 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ASTERUSDT |
| 13:52:24 | SIGNAL | ⚠️ ALLOC_ZERO ASTERUSDT: score=0.197 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 13:52:24 | SIGNAL | 💰 Orchestrator ASTERUSDT: score=0.197 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=212.803547 |
| 13:52:24 | TRADE | ⚡ PAPER_SPEED market-fill override ASTERUSDT: USE_LIMIT_ORDERS bypassed |
| 13:52:24 | TRADE | ✅ Opened LONG ASTERUSDT qty=212.803547 risk=3.77U [MeanReversion \| MEAN_REVERTING] |
| 13:52:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=53.2 above_sma=True regime=MEAN_REVERTING) |
| 13:52:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=36.6 above_sma=False regime=MEAN_REVERTING) |
| 13:52:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=52.9 above_sma=True regime=MEAN_REVERTING) |
| 13:52:59 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=1=9%_of_avg=8,min=10%[base=45%×0.20]) |
| 13:52:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=34.3 above_sma=False regime=MEAN_REVERTING) |
| 13:52:59 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=42.1 above_sma=False regime=MEAN_REVERTING) |
| 13:53:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 13:53:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=43.8 above_sma=False regime=TRENDING) |
| 13:53:01 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=38.5 above_sma=False regime=TRENDING) |
| 13:53:03 | FILTER | ⚡ PAPER_SPEED bypass ARBUSDT: SLEEP_MODE(vol=3806=1%_of_avg=253819,min=10%[base=45%×0.20]) |
| 13:53:03 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 13:53:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=33.3 above_sma=False regime=TRENDING) |
| 13:53:08 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 13:53:09 | SIGNAL | ⚡ PAPER_SPEED fallback OPUSDT: SHORT entry=0.1643 rsi=58.3 |
| 13:53:11 | FILTER | ⚡ PAPER_SPEED bypass STRKUSDT: SLEEP_MODE(vol=7167=7%_of_avg=106553,min=10%[base=45%×0.20]) |
| 13:53:11 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 13:53:28 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #26: meta_score=50.4 verdict=— |
| 13:53:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=MEAN_REVERTING) |
| 13:53:59 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=0=6%_of_avg=6,min=10%[base=45%×0.20]) |
| 13:53:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=36.6 above_sma=False regime=MEAN_REVERTING) |
| 13:53:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=43.2 above_sma=False regime=TRENDING) |
| 13:53:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=55.4 above_sma=True regime=MEAN_REVERTING) |
| 13:54:00 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=51.7 above_sma=False regime=TRENDING) |
| 13:54:00 | FILTER | ⚡ PAPER_SPEED bypass ICPUSDT: SLEEP_MODE(vol=378=9%_of_avg=4343,min=10%[base=45%×0.20]) |
| 13:54:00 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=52.5 above_sma=False regime=MEAN_REVERTING) |
| 13:54:01 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 13:54:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=39.4 above_sma=False regime=MEAN_REVERTING) |
| 13:54:01 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 13:54:02 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=MEAN_REVERTING) |
| 13:54:02 | SIGNAL | ⚡ PAPER_SPEED fallback OPUSDT: SHORT entry=0.1644 rsi=56.5 |
| 13:54:04 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.0600 rsi=66.7 |
| 13:54:04 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=52.9 above_sma=False regime=MEAN_REVERTING) |
| 13:54:14 | FILTER | ⚡ PAPER_SPEED bypass NEARUSDT: SLEEP_MODE(vol=0=0%_of_avg=25379,min=10%[base=45%×0.20]) |
| 13:54:14 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: SHORT entry=1.5700 rsi=88.9 |
| 13:54:14 | SIGNAL | 🔔 Signal SHORT NEARUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 13:54:14 | SIGNAL | ⚠️ ALLOC_ZERO NEARUSDT: score=0.109 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 13:54:14 | SIGNAL | 💰 Orchestrator NEARUSDT: score=0.109 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=96.100455 |
| 13:54:14 | TRADE | ⚡ PAPER_SPEED market-fill override NEARUSDT: USE_LIMIT_ORDERS bypassed |
| 13:54:14 | TRADE | ✅ Opened SHORT NEARUSDT qty=96.100455 risk=3.77U [MeanReversion \| MEAN_REVERTING] |
| 13:54:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=74.2 above_sma=False regime=MEAN_REVERTING) |
| 13:54:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI_CRASH_GUARD blocked SHORT (rsi=78.6 prev=60.0≤65, need prev>65 — first-touch spike, not established reversal) |
| 13:54:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=43.2 above_sma=False regime=TRENDING) |
| 13:54:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=60.5 above_sma=True regime=TRENDING) |
| 13:55:00 | SIGNAL | ⚡ PAPER_SPEED fallback FILUSDT: SHORT entry=1.2270 rsi=77.8 |
| 13:55:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=62.5 above_sma=False regime=MEAN_REVERTING) |
| 13:55:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=92.9 above_sma=True regime=TRENDING) |
| 13:55:00 | SIGNAL | ⚡ PAPER_SPEED fallback OPUSDT: SHORT entry=0.1651 rsi=80.0 |
| 13:55:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=59.3 above_sma=False regime=MEAN_REVERTING) |
| 13:55:01 | FILTER | ⚡ PAPER_SPEED bypass ARBUSDT: SLEEP_MODE(vol=19487=8%_of_avg=255273,min=10%[base=45%×0.20]) |
| 13:55:01 | SIGNAL | ⚡ PAPER_SPEED fallback ARBUSDT: SHORT entry=0.1414 rsi=88.9 |
| 13:55:06 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=62.3 above_sma=True regime=MEAN_REVERTING) |
| 13:55:08 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=75.0 above_sma=False regime=MEAN_REVERTING) |
| 13:55:45 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 13:55:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=48.5 above_sma=False regime=TRENDING) |
| 13:55:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=74.2 above_sma=False regime=MEAN_REVERTING) |
| 13:55:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=61.9 above_sma=False regime=MEAN_REVERTING) |
| 13:55:59 | SIGNAL | ⚡ PAPER_SPEED fallback NOTUSDT: SHORT entry=0.0006 rsi=76.9 |
| 13:55:59 | SIGNAL | 🔔 Signal SHORT NOTUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 13:55:59 | SIGNAL | ⚠️ ALLOC_ZERO NOTUSDT: score=0.235 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 13:55:59 | SIGNAL | 💰 Orchestrator NOTUSDT: score=0.235 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=239869.180805 |
| 13:55:59 | TRADE | ⚡ PAPER_SPEED market-fill override NOTUSDT: USE_LIMIT_ORDERS bypassed |
| 13:55:59 | TRADE | ✅ Opened SHORT NOTUSDT qty=239869.180805 risk=3.77U [MeanReversion \| MEAN_REVERTING] |
| 13:55:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=55.1 above_sma=True regime=TRENDING) |
| 13:56:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 13:56:00 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=70.0 above_sma=False regime=MEAN_REVERTING) |
| 13:56:03 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.0400 rsi=66.7 |
| 13:56:04 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=53.6 above_sma=True regime=MEAN_REVERTING) |
| 13:56:04 | SIGNAL | ⚡ PAPER_SPEED fallback ARBUSDT: SHORT entry=0.1414 rsi=86.7 |
| 13:56:05 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=70.6 above_sma=False regime=MEAN_REVERTING) |
| 13:56:09 | SIGNAL | ⚡ PAPER_SPEED fallback OPUSDT: SHORT entry=0.1649 rsi=74.1 |
| 13:56:55 | TRADE | [TM] ASTERUSDT TIME_EXIT @ 0.7070 (Fast-fail: 4.5min r=-0.805<-0.45) |
| 13:57:01 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 13:57:01 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=56.3 above_sma=True regime=TRENDING) |
| 13:57:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 13:57:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=80377.9000 rsi=71.7 |
| 13:57:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 13:57:01 | SIGNAL | ⚠️ ALLOC_ZERO BTCUSDT: score=0.243 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 13:57:01 | SIGNAL | 💰 Orchestrator BTCUSDT: score=0.243 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.001877 |
| 13:57:01 | TRADE | ⚡ PAPER_SPEED market-fill override BTCUSDT: USE_LIMIT_ORDERS bypassed |
| 13:57:01 | TRADE | ✅ Opened SHORT BTCUSDT qty=0.001877 risk=3.77U [MeanReversion \| MEAN_REVERTING] |
| 13:57:03 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 13:57:03 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.0500 rsi=64.7 |
| 13:57:03 | SIGNAL | ⚡ DTP SAHARAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 13:57:03 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=23.3 above_sma=False regime=TRENDING) |
| 13:57:03 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 13:57:03 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=58.3 above_sma=False regime=MEAN_REVERTING) |
| 13:57:03 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 13:57:04 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=MEAN_REVERTING) |
| 13:57:04 | TRADE | Position closed [SL] ASTERUSDT @ 0.707 |
| 13:57:04 | SIGNAL | 📈 STREAK TONUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:57:04 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=48.5 above_sma=False regime=TRENDING) |
| 13:57:04 | SIGNAL | 📈 STREAK FILUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:57:04 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=62.5 above_sma=False regime=MEAN_REVERTING) |
| 13:57:05 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:57:05 | FILTER | ⚡ PAPER_SPEED bypass ARBUSDT: SLEEP_MODE(vol=8795=3%_of_avg=256987,min=10%[base=45%×0.20]) |
| 13:57:05 | SIGNAL | ⚡ PAPER_SPEED fallback ARBUSDT: SHORT entry=0.1414 rsi=84.6 |
| 13:57:06 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:57:06 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=62.5 above_sma=False regime=MEAN_REVERTING) |
| 13:57:06 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:57:06 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=50.7 above_sma=True regime=MEAN_REVERTING) |
| 13:57:09 | SIGNAL | 📈 STREAK OPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:57:09 | FILTER | ⚡ PAPER_SPEED bypass OPUSDT: SLEEP_MODE(vol=4494=6%_of_avg=69427,min=10%[base=45%×0.20]) |
| 13:57:09 | SIGNAL | ⚡ PAPER_SPEED fallback OPUSDT: SHORT entry=0.1648 rsi=66.7 |
| 13:57:21 | TRADE | [TM] NOTUSDT BE: SL→0.0006 (R=1.35≥1.0 mode=TREND_FOLLOW → SL→BE) |
| 13:57:25 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:57:25 | FILTER | ⚡ PAPER_SPEED bypass STRKUSDT: SLEEP_MODE(vol=0=0%_of_avg=103438,min=10%[base=45%×0.20]) |
| 13:57:25 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 13:58:00 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=53.8 above_sma=False regime=MEAN_REVERTING) |
| 13:58:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.0600 rsi=60.0 |
| 13:58:00 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=23.9 above_sma=False regime=TRENDING) |
| 13:58:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=51.9 above_sma=True regime=TRENDING) |
| 13:58:00 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | SIGNAL | ⚡ ALPHA PullbackEntry STRKUSDT score=0.538 rr=5.00 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=MEAN_REVERTING) |
| 13:58:00 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 13:58:00 | SIGNAL | 📈 STREAK FILUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:01 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 13:58:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=62.8 above_sma=False regime=MEAN_REVERTING) |
| 13:58:01 | SIGNAL | 📈 STREAK TONUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:01 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=41.9 above_sma=False regime=TRENDING) |
| 13:58:02 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:02 | FILTER | ⚡ PAPER_SPEED bypass ARBUSDT: SLEEP_MODE(vol=11646=5%_of_avg=255387,min=10%[base=45%×0.20]) |
| 13:58:02 | SIGNAL | ⚡ PAPER_SPEED fallback ARBUSDT: SHORT entry=0.1414 rsi=84.6 |
| 13:58:02 | SIGNAL | 📈 STREAK OPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:02 | SIGNAL | ⚡ ALPHA PullbackEntry OPUSDT score=0.536 rr=5.00 |
| 13:58:02 | SIGNAL | ⚡ PAPER_SPEED fallback OPUSDT: SHORT entry=0.1647 rsi=59.1 |
| 13:58:19 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 13:58:19 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI_CRASH_GUARD blocked SHORT (rsi=72.9 prev=50.7≤65, need prev>65 — first-touch spike, not established reversal) |
| 13:58:28 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #27: meta_score=50.2 verdict=— |
| 13:58:35 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |

---
*EOW Quant Engine V4.0 — 2026-05-09 13:58 UTC*