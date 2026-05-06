# EOW Quant Engine — Performance Report

**Generated:** 2026-05-06 03:24 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **525 trades** with a net **LOSS** of **-177.16 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $822.84 USDT |
| Net PnL | -177.1559 USDT |
| Win Rate | 33.0% |
| Profit Factor | 0.517 |
| Sharpe Ratio | -2.087 |
| Sortino Ratio | -1.991 |
| Calmar Ratio | -0.431 |
| Max Drawdown | 19.73% |
| Risk of Ruin | 100.00% |
| Total Fees | 81.1122 USDT |
| Total Slippage | 22.3836 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -73.6601 USDT (before all costs)
- **Fees deducted:** -81.1122 USDT
- **Slippage deducted:** -22.3836 USDT
- **Net PnL (bankable):** -177.1559 USDT

### 2.2 Trade Statistics

- Avg win: +1.0948 USDT
- Avg loss: -1.0413 USDT
- Profit factor: 0.517

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-17.7%** | **-2.09** | **-1.99** | **19.7%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 03:08:02 | TRADE | ✅ Opened LONG ICPUSDT qty=61.076438 risk=12.35U [MeanReversion \| MEAN_REVERTING] |
| 03:08:12 | TRADE | [TM] ICPUSDT TIME_EXIT @ 2.6910 (Fast-fail: 0.2min r=-0.535<-0.45) |
| 03:08:12 | TRADE | Position closed [SL] ICPUSDT @ 2.691 |
| 03:08:17 | TRADE | [TM] LUNCUSDT TIME_EXIT @ 0.0001 (Fast-fail: 1.2min r=-0.454<-0.45) |
| 03:08:17 | TRADE | Position closed [SL] LUNCUSDT @ 0.0001111 |
| 03:09:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=63.3 above_sma=True regime=TRENDING) |
| 03:09:00 | SIGNAL | ⚡ ALPHA TrendBreakout DOGSUSDT score=0.706 rr=4.00 |
| 03:09:00 | SIGNAL | ⚡ PAPER_SPEED fallback DOGSUSDT: SHORT entry=0.0001 rsi=40.4 |
| 03:09:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=47.4 above_sma=False regime=MEAN_REVERTING) |
| 03:09:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=63.3 above_sma=True regime=TRENDING) |
| 03:09:02 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0200 rsi=44.9 |
| 03:09:07 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.6400 rsi=53.8 |
| 03:09:11 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3860 rsi=40.0 |
| 03:09:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=58.0 above_sma=True regime=MEAN_REVERTING) |
| 03:09:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2369.2000 rsi=54.9 |
| 03:09:59 | SIGNAL | ⚡ PAPER_SPEED fallback DOGSUSDT: SHORT entry=0.0001 rsi=40.4 |
| 03:09:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81370.6600 rsi=57.4 |
| 03:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.6400 rsi=53.8 |
| 03:10:01 | SYSTEM | 🔬 Live Process Snapshot downloaded → eow_live_process_20260506_031001.zip (156 KB \| logs=2000 rl_contexts=3 trades=523) |
| 03:10:09 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0200 rsi=43.3 |
| 03:10:13 | FILTER | ⚡ PAPER_SPEED bypass TRUMPUSDT: SLEEP_MODE(vol=152=8%_of_avg=1819,min=10%[base=45%×0.20]) |
| 03:10:13 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3860 rsi=36.8 |
| 03:10:41 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #1: meta_score=56.1 verdict=BLOCKED |
| 03:10:58 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81392.6700 rsi=51.5 |
| 03:10:59 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.6500 rsi=55.6 |
| 03:10:59 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=34.9 above_sma=False regime=TRENDING) |
| 03:10:59 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.0250 rsi=63.2 |
| 03:10:59 | SIGNAL | 🔔 Signal SHORT TONUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:10:59 | SIGNAL | 💰 Orchestrator TONUSDT: score=0.324 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=81.182707 |
| 03:10:59 | TRADE | ⚡ PAPER_SPEED market-fill override TONUSDT: USE_LIMIT_ORDERS bypassed |
| 03:10:59 | TRADE | ✅ Opened SHORT TONUSDT qty=81.182707 risk=4.11U [MeanReversion \| MEAN_REVERTING] |
| 03:10:59 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0201 rsi=47.9 |
| 03:11:00 | SIGNAL | ⚡ ALPHA PullbackEntry ETHUSDT score=0.482 rr=5.00 |
| 03:11:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2369.1000 rsi=44.9 |
| 03:11:42 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3900 rsi=47.8 |
| 03:11:58 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2369.1200 rsi=45.5 |
| 03:11:58 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81400.0000 rsi=55.1 |
| 03:12:02 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.6400 rsi=60.0 |
| 03:12:09 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=35.7 above_sma=False regime=TRENDING) |
| 03:12:17 | FILTER | ⚡ PAPER_SPEED bypass TRUMPUSDT: SLEEP_MODE(vol=113=6%_of_avg=1980,min=10%[base=45%×0.20]) |
| 03:12:17 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3900 rsi=50.0 |
| 03:12:17 | FILTER | ⚡ PAPER_SPEED bypass TSTUSDT: SLEEP_MODE(vol=23104=7%_of_avg=340139,min=10%[base=45%×0.20]) |
| 03:12:17 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0201 rsi=42.6 |
| 03:13:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81417.8200 rsi=60.1 |
| 03:13:01 | SIGNAL | ⚡ PAPER_SPEED fallback DOGSUSDT: SHORT entry=0.0001 rsi=39.5 |
| 03:13:03 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2369.7200 rsi=49.8 |
| 03:13:04 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0200 rsi=41.4 |
| 03:13:06 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 03:13:07 | FILTER | ⚡ PAPER_SPEED bypass TRUMPUSDT: SLEEP_MODE(vol=20=1%_of_avg=1891,min=10%[base=45%×0.20]) |
| 03:13:07 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3900 rsi=52.4 |
| 03:13:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:13:58 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81415.9700 rsi=55.2 |
| 03:13:59 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:13:59 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=32.4 above_sma=False regime=TRENDING) |
| 03:13:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:13:59 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=34.3 |
| 03:13:59 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:13:59 | SIGNAL | 💰 Orchestrator LUNCUSDT: score=0.255 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=1477176.586848 |
| 03:13:59 | TRADE | ⚡ PAPER_SPEED market-fill override LUNCUSDT: USE_LIMIT_ORDERS bypassed |
| 03:13:59 | TRADE | ✅ Opened LONG LUNCUSDT qty=1477176.586848 risk=4.11U [MeanReversion \| MEAN_REVERTING] |
| 03:14:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:14:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2369.6600 rsi=45.5 |
| 03:14:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:14:00 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.6200 rsi=52.4 |
| 03:14:02 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:14:02 | FILTER | ⚡ PAPER_SPEED bypass TSTUSDT: SLEEP_MODE(vol=8082=2%_of_avg=336666,min=10%[base=45%×0.20]) |
| 03:14:02 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0200 rsi=46.3 |
| 03:14:03 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:14:03 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=2.6960 rsi=40.3 |
| 03:14:09 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:14:09 | FILTER | ⚡ PAPER_SPEED bypass TRUMPUSDT: SLEEP_MODE(vol=87=5%_of_avg=1895,min=10%[base=45%×0.20]) |
| 03:14:09 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3890 rsi=47.6 |
| 03:14:35 | TRADE | [TM] LUNCUSDT TIME_EXIT @ 0.0001 (Fast-fail: 0.6min r=-0.458<-0.45) |
| 03:14:36 | TRADE | Position closed [SL] LUNCUSDT @ 0.00011109 |
| 03:15:04 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:15:04 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2368.3800 rsi=42.7 |
| 03:15:04 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:15:04 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81410.0100 rsi=56.3 |
| 03:15:05 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:15:05 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3890 rsi=50.0 |
| 03:15:05 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:15:05 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=25.8 above_sma=False regime=TRENDING) |
| 03:15:05 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:15:05 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.5900 rsi=40.9 |
| 03:15:07 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:15:07 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=34.8 above_sma=False regime=TRENDING) |
| 03:15:15 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:15:15 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=2.6930 rsi=39.7 |
| 03:15:41 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #2: meta_score=55.0 verdict=BLOCKED |
| 03:15:59 | TRADE | [TM] TONUSDT BE: SL→2.0222 (R=1.04≥1.0 mode=TREND_FOLLOW → SL→BE) |
| 03:16:04 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:16:04 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=27.0 above_sma=False regime=TRENDING) |
| 03:16:04 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:16:04 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=2.6980 rsi=49.2 |
| 03:16:05 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:16:05 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2369.6200 rsi=46.9 |
| 03:16:06 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:16:06 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=30.8 above_sma=False regime=TRENDING) |
| 03:16:07 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:16:07 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81419.8700 rsi=55.3 |
| 03:16:08 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:16:08 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.5700 rsi=37.5 |
| 03:16:32 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 03:16:32 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3870 rsi=45.5 |
| 03:16:59 | TRADE | Position closed [TSL+] TONUSDT @ 2.005 |
| 03:17:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81389.8900 rsi=44.1 |
| 03:17:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2368.9300 rsi=36.1 |
| 03:17:01 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=21.4 above_sma=False regime=TRENDING) |
| 03:17:02 | FILTER | ⚡ PAPER_SPEED bypass LTCUSDT: SLEEP_MODE(vol=28=9%_of_avg=333,min=10%[base=45%×0.20]) |
| 03:17:02 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.5700 rsi=28.6 |
| 03:17:02 | SIGNAL | ⚡ ALPHA PullbackEntry ICPUSDT score=0.632 rr=5.00 |
| 03:17:02 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=2.7020 rsi=57.1 |
| 03:17:02 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=30.4 above_sma=False regime=TRENDING) |
| 03:17:03 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3860 rsi=43.5 |
| 03:17:58 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=59.1 above_sma=True regime=MEAN_REVERTING) |
| 03:17:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81369.3400 rsi=37.2 |
| 03:17:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=34.7 above_sma=False regime=TRENDING) |
| 03:18:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2368.4700 rsi=34.5 |
| 03:18:01 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=32.1 above_sma=False regime=TRENDING) |
| 03:18:02 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.5500 rsi=15.0 |
| 03:18:06 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=38.1 above_sma=True regime=MEAN_REVERTING) |
| 03:18:59 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=2.7190 rsi=60.9 |
| 03:18:59 | SIGNAL | 🔔 Signal SHORT ICPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:18:59 | SIGNAL | 💰 Orchestrator ICPUSDT: score=0.504 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=60.525500 |
| 03:18:59 | TRADE | ⚡ PAPER_SPEED market-fill override ICPUSDT: USE_LIMIT_ORDERS bypassed |
| 03:18:59 | TRADE | ✅ Opened SHORT ICPUSDT qty=60.525500 risk=12.34U [MeanReversion \| MEAN_REVERTING] |
| 03:18:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2369.4300 rsi=34.7 |
| 03:18:59 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=29.6 above_sma=False regime=TRENDING) |
| 03:18:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81389.9900 rsi=37.4 |
| 03:19:00 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=35.0 above_sma=True regime=MEAN_REVERTING) |
| 03:19:01 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0200 rsi=41.8 |
| 03:19:01 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.5600 rsi=15.0 |
| 03:19:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2370.3900 rsi=39.1 |
| 03:19:59 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=25.0 above_sma=False regime=TRENDING) |
| 03:19:59 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=50.0 |
| 03:19:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81409.9900 rsi=38.8 |
| 03:20:00 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0200 rsi=44.6 |
| 03:20:04 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=22.7 above_sma=True regime=MEAN_REVERTING) |
| 03:20:31 | SIGNAL | ⚡ ALPHA PullbackEntry TRUMPUSDT score=0.565 rr=5.00 |
| 03:20:31 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=40.9 above_sma=True regime=MEAN_REVERTING) |
| 03:20:41 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #3: meta_score=56.3 verdict=BLOCKED |
| 03:20:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=45.0 above_sma=True regime=MEAN_REVERTING) |
| 03:20:59 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=27.8 above_sma=True regime=MEAN_REVERTING) |
| 03:20:59 | SIGNAL | ⚡ PAPER_SPEED fallback DOGSUSDT: SHORT entry=0.0001 rsi=40.0 |
| 03:20:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81430.0700 rsi=48.5 |
| 03:20:59 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=56.3 above_sma=True regime=MEAN_REVERTING) |
| 03:21:01 | TRADE | [TM] ICPUSDT BE: SL→2.7152 (R=1.00≥1.0 mode=TREND_FOLLOW → SL→BE) |
| 03:21:02 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0200 rsi=40.4 |
| 03:21:02 | SIGNAL | ⚡ ALPHA PullbackEntry LUNCUSDT score=0.620 rr=5.00 |
| 03:21:02 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=62.1 |
| 03:21:58 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81453.8300 rsi=53.4 |
| 03:21:59 | FILTER | ⚡ PAPER_SPEED bypass TSTUSDT: SLEEP_MODE(vol=18242=6%_of_avg=305022,min=10%[base=45%×0.20]) |
| 03:21:59 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0199 rsi=46.0 |
| 03:21:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:21:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=55.2 above_sma=False regime=MEAN_REVERTING) |
| 03:21:59 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:21:59 | SIGNAL | ⚡ PAPER_SPEED fallback DOGSUSDT: SHORT entry=0.0001 rsi=40.0 |
| 03:22:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:22:02 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=42.8 above_sma=True regime=MEAN_REVERTING) |
| 03:22:02 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:22:02 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=31.2 above_sma=True regime=MEAN_REVERTING) |
| 03:22:02 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:22:03 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=MEAN_REVERTING) |
| 03:23:00 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=50.5 above_sma=True regime=MEAN_REVERTING) |
| 03:23:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2370.7700 rsi=55.6 |
| 03:23:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 03:23:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=68.1 above_sma=True regime=TRENDING) |
| 03:23:01 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
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
| 03:23:19 | SIGNAL | 🔔 Signal SHORT TRUMPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:23:19 | SIGNAL | 💰 Orchestrator TRUMPUSDT: score=0.396 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=68.857253 |
| 03:23:19 | TRADE | ⚡ PAPER_SPEED market-fill override TRUMPUSDT: USE_LIMIT_ORDERS bypassed |
| 03:23:19 | TRADE | ✅ Opened SHORT TRUMPUSDT qty=68.857253 risk=12.34U [MeanReversion \| MEAN_REVERTING] |
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

---
*EOW Quant Engine V4.0 — 2026-05-06 03:24 UTC*