# EOW Quant Engine — Performance Report

**Generated:** 2026-05-09 02:27 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **757 trades** with a net **LOSS** of **-228.64 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $771.36 USDT |
| Net PnL | -228.6418 USDT |
| Win Rate | 28.3% |
| Profit Factor | 0.498 |
| Sharpe Ratio | -2.203 |
| Sortino Ratio | -2.186 |
| Calmar Ratio | -0.311 |
| Max Drawdown | 24.47% |
| Risk of Ruin | 100.00% |
| Total Fees | 107.3995 USDT |
| Total Slippage | 42.0991 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -79.1432 USDT (before all costs)
- **Fees deducted:** -107.3995 USDT
- **Slippage deducted:** -42.0991 USDT
- **Net PnL (bankable):** -228.6418 USDT

### 2.2 Trade Statistics

- Avg win: +1.0619 USDT
- Avg loss: -0.8396 USDT
- Profit factor: 0.498

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-22.9%** | **-2.20** | **-2.19** | **24.5%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 02:17:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:17:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=57.1 above_sma=False regime=MEAN_REVERTING) |
| 02:17:00 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:17:00 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=40.0 above_sma=False regime=MEAN_REVERTING) |
| 02:17:01 | SIGNAL | ⚡ DTP NILUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:17:01 | SIGNAL | ⚡ PAPER_SPEED fallback NILUSDT: LONG entry=0.0711 rsi=33.3 |
| 02:17:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:17:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=53.9 above_sma=True regime=MEAN_REVERTING) |
| 02:17:02 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #1: meta_score=52.7 verdict=— |
| 02:17:04 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:17:04 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=43.7 above_sma=False regime=TRENDING) |
| 02:17:05 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:17:05 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.9600 rsi=54.5 |
| 02:17:05 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:17:05 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=38.5 above_sma=False regime=MEAN_REVERTING) |
| 02:17:05 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:17:05 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=59.5 above_sma=True regime=MEAN_REVERTING) |
| 02:17:32 | TRADE | [TM] NOTUSDT TIME_EXIT @ 0.0007 (Fast-fail: 0.5min r=-0.708<-0.45) |
| 02:17:32 | TRADE | Position closed [SL] NOTUSDT @ 0.000654 |
| 02:18:03 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=56.8 above_sma=True regime=MEAN_REVERTING) |
| 02:18:03 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=52.9 above_sma=True regime=MEAN_REVERTING) |
| 02:18:03 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=44.4 above_sma=True regime=MEAN_REVERTING) |
| 02:18:03 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=55.7 above_sma=True regime=TRENDING) |
| 02:18:03 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=37.2 above_sma=False regime=MEAN_REVERTING) |
| 02:18:03 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=55.4 above_sma=False regime=MEAN_REVERTING) |
| 02:18:03 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=53.3 above_sma=False regime=MEAN_REVERTING) |
| 02:18:04 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 02:18:04 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=40.6 above_sma=False regime=TRENDING) |
| 02:18:04 | SIGNAL | ⚡ PAPER_SPEED fallback NILUSDT: LONG entry=0.0712 rsi=33.3 |
| 02:18:06 | FILTER | ⚡ PAPER_SPEED bypass LTCUSDT: SLEEP_MODE(vol=29=9%_of_avg=306,min=10%[base=45%×0.20]) |
| 02:18:06 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 02:18:07 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=69.2 above_sma=True regime=MEAN_REVERTING) |
| 02:18:08 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=32.3 above_sma=False regime=MEAN_REVERTING) |
| 02:18:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=53.5 above_sma=True regime=TRENDING) |
| 02:18:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=50.8 above_sma=True regime=MEAN_REVERTING) |
| 02:18:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=55.6 above_sma=True regime=MEAN_REVERTING) |
| 02:18:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=31.6 above_sma=False regime=TRENDING) |
| 02:18:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=54.7 above_sma=False regime=MEAN_REVERTING) |
| 02:19:00 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=51.2 above_sma=True regime=MEAN_REVERTING) |
| 02:19:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=70.0 above_sma=True regime=TRENDING) |
| 02:19:01 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=35.5 above_sma=False regime=TRENDING) |
| 02:19:03 | SIGNAL | ⚡ PAPER_SPEED fallback NILUSDT: LONG entry=0.0711 rsi=31.2 |
| 02:19:05 | FILTER | ⚡ PAPER_SPEED bypass NEARUSDT: SLEEP_MODE(vol=1272=7%_of_avg=19223,min=10%[base=45%×0.20]) |
| 02:19:05 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=68.0 above_sma=True regime=MEAN_REVERTING) |
| 02:19:07 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.9600 rsi=55.6 |
| 02:19:11 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=35.5 above_sma=False regime=TRENDING) |
| 02:19:13 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=55.6 above_sma=True regime=MEAN_REVERTING) |
| 02:19:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=33.0 above_sma=False regime=MEAN_REVERTING) |
| 02:19:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=55.6 above_sma=True regime=MEAN_REVERTING) |
| 02:19:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=52.0 above_sma=False regime=MEAN_REVERTING) |
| 02:19:59 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=63.0 above_sma=True regime=MEAN_REVERTING) |
| 02:19:59 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=57.9 above_sma=True regime=MEAN_REVERTING) |
| 02:19:59 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=37.8 above_sma=True regime=MEAN_REVERTING) |
| 02:19:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=55.4 above_sma=True regime=TRENDING) |
| 02:20:00 | SIGNAL | ⚡ ALPHA TrendBreakout TONUSDT score=0.616 rr=5.00 |
| 02:20:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=71.4 above_sma=True regime=TRENDING) |
| 02:20:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 02:20:00 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=40.7 above_sma=False regime=TRENDING) |
| 02:20:02 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=51.3 above_sma=False regime=MEAN_REVERTING) |
| 02:20:05 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=44.4 above_sma=False regime=TRENDING) |
| 02:20:15 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 02:21:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=40.4 above_sma=False regime=MEAN_REVERTING) |
| 02:21:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 02:21:00 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=51.5 above_sma=True regime=MEAN_REVERTING) |
| 02:21:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=49.0 above_sma=False regime=MEAN_REVERTING) |
| 02:21:00 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.9200 rsi=54.5 |
| 02:21:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=51.9 above_sma=False regime=TRENDING) |
| 02:21:00 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=51.3 above_sma=False regime=TRENDING) |
| 02:21:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=51.1 above_sma=True regime=TRENDING) |
| 02:21:00 | SIGNAL | ⚡ ALPHA PullbackEntry FILUSDT score=0.550 rr=5.00 |
| 02:21:00 | SIGNAL | ⚡ PAPER_SPEED fallback FILUSDT: SHORT entry=1.2750 rsi=55.6 |
| 02:21:00 | SIGNAL | ⚡ ALPHA TrendBreakout TONUSDT score=0.763 rr=5.00 |
| 02:21:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=79.6 above_sma=True regime=TRENDING) |
| 02:21:01 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=60.7 above_sma=False regime=MEAN_REVERTING) |
| 02:21:02 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 02:21:08 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=35.3 above_sma=True regime=MEAN_REVERTING) |
| 02:21:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=49.7 above_sma=True regime=TRENDING) |
| 02:21:59 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=3.9450 rsi=55.9 |
| 02:21:59 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 02:21:59 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 02:22:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=78.2 above_sma=True regime=TRENDING) |
| 02:22:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=44.9 above_sma=True regime=MEAN_REVERTING) |
| 02:22:00 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 02:22:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=48.7 above_sma=False regime=MEAN_REVERTING) |
| 02:22:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=MEAN_REVERTING) |
| 02:22:01 | SIGNAL | ⚡ ALPHA PullbackEntry NILUSDT score=0.535 rr=5.00 |
| 02:22:01 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=43.3 above_sma=True regime=MEAN_REVERTING) |
| 02:22:02 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=51.5 above_sma=True regime=MEAN_REVERTING) |
| 02:22:02 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #2: meta_score=52.5 verdict=— |
| 02:22:03 | FILTER | ⚡ PAPER_SPEED bypass UNIUSDT: SLEEP_MODE(vol=256=8%_of_avg=3200,min=10%[base=45%×0.20]) |
| 02:22:03 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=36.4 above_sma=False regime=TRENDING) |
| 02:22:07 | SIGNAL | ⚡ PAPER_SPEED fallback FILUSDT: SHORT entry=1.2780 rsi=58.6 |
| 02:22:59 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:22:59 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=3.9400 rsi=62.3 |
| 02:22:59 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:22:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=TRENDING) |
| 02:22:59 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:22:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=49.0 above_sma=False regime=MEAN_REVERTING) |
| 02:22:59 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:22:59 | SIGNAL | ⚡ PAPER_SPEED fallback NOTUSDT: LONG entry=0.0007 rsi=28.6 |
| 02:22:59 | SIGNAL | 🔔 Signal LONG NOTUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:22:59 | SIGNAL | 💰 Orchestrator NOTUSDT: score=0.467 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=237022.548888 |
| 02:22:59 | TRADE | ⚡ PAPER_SPEED market-fill override NOTUSDT: USE_LIMIT_ORDERS bypassed |
| 02:22:59 | TRADE | ✅ Opened LONG NOTUSDT qty=237022.548888 risk=11.59U [MeanReversion \| MEAN_REVERTING] |
| 02:22:59 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:22:59 | FILTER | ⚡ PAPER_SPEED bypass NEARUSDT: SLEEP_MODE(vol=346=3%_of_avg=13147,min=10%[base=45%×0.20]) |
| 02:22:59 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=46.2 above_sma=False regime=MEAN_REVERTING) |
| 02:23:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:23:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=80421.2700 rsi=46.2 |
| 02:23:00 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:23:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=67.2 above_sma=True regime=TRENDING) |
| 02:23:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:23:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=35.3 above_sma=False regime=MEAN_REVERTING) |
| 02:23:01 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:23:01 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=61.3 above_sma=True regime=TRENDING) |
| 02:23:01 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:23:01 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=56.8 above_sma=True regime=MEAN_REVERTING) |
| 02:23:05 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 02:23:05 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 02:23:05 | TRADE | [TM] NOTUSDT TIME_EXIT @ 0.0006 (Fast-fail: 0.1min r=-0.625<-0.45) |
| 02:23:05 | TRADE | Position closed [SL] NOTUSDT @ 0.000649 |
| 02:23:08 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=52.4 above_sma=True regime=MEAN_REVERTING) |
| 02:23:10 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=61.5 above_sma=True regime=TRENDING) |
| 02:23:13 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=42.1 above_sma=False regime=TRENDING) |
| 02:23:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=62.9 above_sma=True regime=TRENDING) |
| 02:23:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=37.3 above_sma=True regime=MEAN_REVERTING) |
| 02:23:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=TRENDING) |
| 02:23:59 | SIGNAL | ⚡ ALPHA PullbackEntry ICPUSDT score=0.483 rr=4.00 |
| 02:23:59 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=3.9420 rsi=59.8 |
| 02:24:00 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=53.6 above_sma=True regime=TRENDING) |
| 02:24:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=28.4 above_sma=False regime=TRENDING) |
| 02:24:00 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=35.7 above_sma=False regime=MEAN_REVERTING) |
| 02:24:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=49.7 above_sma=False regime=MEAN_REVERTING) |
| 02:24:00 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=58.3 above_sma=True regime=TRENDING) |
| 02:24:00 | SIGNAL | ⚡ ALPHA TrendBreakout LTCUSDT score=0.790 rr=5.00 |
| 02:24:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=27.3 above_sma=False regime=TRENDING) |
| 02:24:01 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=26.3 above_sma=False regime=TRENDING) |
| 02:24:02 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=43.2 above_sma=True regime=MEAN_REVERTING) |
| 02:24:04 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=52.5 above_sma=True regime=MEAN_REVERTING) |
| 02:25:10 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=TRENDING) |
| 02:25:10 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=53.5 above_sma=True regime=MEAN_REVERTING) |
| 02:25:10 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=33.1 above_sma=False regime=MEAN_REVERTING) |
| 02:25:10 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=53.8 above_sma=True regime=MEAN_REVERTING) |
| 02:25:10 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=26.1 above_sma=False regime=TRENDING) |
| 02:25:10 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=57.4 above_sma=True regime=TRENDING) |
| 02:25:11 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=3.9370 rsi=53.3 |
| 02:25:12 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=39.8 above_sma=True regime=MEAN_REVERTING) |
| 02:25:12 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=33.3 above_sma=False regime=TRENDING) |
| 02:25:13 | SIGNAL | ⚡ PAPER_SPEED fallback FILUSDT: SHORT entry=1.2790 rsi=53.6 |
| 02:25:15 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=37.0 above_sma=False regime=MEAN_REVERTING) |
| 02:25:18 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=58.3 above_sma=True regime=TRENDING) |
| 02:25:19 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 02:26:05 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=32.7 above_sma=False regime=TRENDING) |
| 02:26:05 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=TRENDING) |
| 02:26:05 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=45.3 above_sma=False regime=MEAN_REVERTING) |
| 02:26:06 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=57.4 above_sma=True regime=TRENDING) |
| 02:26:06 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=47.6 above_sma=False regime=TRENDING) |
| 02:26:06 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=45.2 above_sma=False regime=TRENDING) |
| 02:26:06 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=38.8 above_sma=False regime=MEAN_REVERTING) |
| 02:26:06 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=53.8 above_sma=True regime=MEAN_REVERTING) |
| 02:26:06 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=20.5 above_sma=False regime=TRENDING) |
| 02:26:07 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: SHORT entry=0.0553 rsi=53.8 |
| 02:26:07 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: LONG entry=1.6030 rsi=29.2 |
| 02:26:07 | SIGNAL | 🔔 Signal LONG NEARUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:26:07 | SIGNAL | 💰 Orchestrator NEARUSDT: score=0.339 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=96.290279 |
| 02:26:07 | TRADE | ⚡ PAPER_SPEED market-fill override NEARUSDT: USE_LIMIT_ORDERS bypassed |
| 02:26:07 | TRADE | ✅ Opened LONG NEARUSDT qty=96.290279 risk=3.86U [MeanReversion \| MEAN_REVERTING] |
| 02:26:09 | SIGNAL | ⚡ ALPHA TrendBreakout UNIUSDT score=0.819 rr=5.00 |
| 02:26:09 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=33.3 above_sma=False regime=TRENDING) |
| 02:26:10 | SIGNAL | ⚡ PAPER_SPEED fallback NILUSDT: LONG entry=0.0709 rsi=29.2 |
| 02:26:10 | SIGNAL | 🔔 Signal LONG NILUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:26:10 | SIGNAL | 💰 Orchestrator NILUSDT: score=0.246 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=2178.285592 |
| 02:26:10 | TRADE | ⚡ PAPER_SPEED market-fill override NILUSDT: USE_LIMIT_ORDERS bypassed |
| 02:26:10 | TRADE | ✅ Opened LONG NILUSDT qty=2178.285592 risk=3.86U [MeanReversion \| MEAN_REVERTING] |
| 02:26:22 | TRADE | [TM] NEARUSDT TIME_EXIT @ 1.6010 (Fast-fail: 0.2min r=-0.520<-0.45) |
| 02:26:25 | TRADE | Position closed [SL] NEARUSDT @ 1.601 |
| 02:27:02 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #3: meta_score=52.2 verdict=— |
| 02:27:20 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:20 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=TRENDING) |
| 02:27:20 | SIGNAL | 📈 STREAK TONUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:20 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=62.3 above_sma=True regime=TRENDING) |
| 02:27:20 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:20 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=46.4 above_sma=False regime=MEAN_REVERTING) |
| 02:27:20 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:20 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=45.6 above_sma=False regime=TRENDING) |
| 02:27:20 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:20 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=40.5 above_sma=False regime=MEAN_REVERTING) |
| 02:27:20 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:20 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=33.0 above_sma=False regime=TRENDING) |
| 02:27:21 | SIGNAL | 📈 STREAK OPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:21 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=57.9 above_sma=True regime=MEAN_REVERTING) |
| 02:27:22 | SIGNAL | 📈 STREAK FILUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:22 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 02:27:22 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:22 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=30.0 above_sma=False regime=TRENDING) |
| 02:27:23 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:23 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=53.8 above_sma=False regime=MEAN_REVERTING) |
| 02:27:24 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 02:27:24 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=35.0 above_sma=False regime=TRENDING) |
| 02:27:43 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |

---
*EOW Quant Engine V4.0 — 2026-05-09 02:27 UTC*