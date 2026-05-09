# EOW Quant Engine — Performance Report

**Generated:** 2026-05-09 15:46 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **846 trades** with a net **LOSS** of **-251.38 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $748.62 USDT |
| Net PnL | -251.3808 USDT |
| Win Rate | 26.6% |
| Profit Factor | 0.482 |
| Sharpe Ratio | -2.285 |
| Sortino Ratio | -2.292 |
| Calmar Ratio | -0.281 |
| Max Drawdown | 26.69% |
| Risk of Ruin | 100.00% |
| Total Fees | 117.6628 USDT |
| Total Slippage | 49.7966 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -83.9214 USDT (before all costs)
- **Fees deducted:** -117.6628 USDT
- **Slippage deducted:** -49.7966 USDT
- **Net PnL (bankable):** -251.3808 USDT

### 2.2 Trade Statistics

- Avg win: +1.0395 USDT
- Avg loss: -0.7814 USDT
- Profit factor: 0.482

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-25.1%** | **-2.29** | **-2.29** | **26.7%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 15:38:59 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:38:59 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=46.4 above_sma=False regime=TRENDING) |
| 15:38:59 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:38:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=32.2 above_sma=False regime=TRENDING) |
| 15:38:59 | SIGNAL | 📈 STREAK FILUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:38:59 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI_CRASH_GUARD blocked SHORT (rsi=70.6 prev=61.1≤65, need prev>65 — first-touch spike, not established reversal) |
| 15:38:59 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:38:59 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=TRENDING) |
| 15:39:00 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:39:00 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=70.0 above_sma=True regime=TRENDING) |
| 15:39:00 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:39:00 | FILTER | ⚡ PAPER_SPEED bypass ARBUSDT: SLEEP_MODE(vol=5966=8%_of_avg=78762,min=10%[base=45%×0.20]) |
| 15:39:00 | SIGNAL | ⚡ ALPHA PullbackEntry ARBUSDT score=0.542 rr=5.00 |
| 15:39:00 | SIGNAL | ⚡ PAPER_SPEED fallback ARBUSDT: SHORT entry=0.1397 rsi=57.9 |
| 15:39:19 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:39:19 | SIGNAL | ⚡ ALPHA PullbackEntry STRKUSDT score=0.585 rr=5.00 |
| 15:39:19 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: SHORT entry=0.0529 rsi=57.1 |
| 15:39:25 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:39:25 | FILTER | ⚡ PAPER_SPEED bypass ASTERUSDT: SLEEP_MODE(vol=606=4%_of_avg=16777,min=10%[base=45%×0.20]) |
| 15:39:25 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 15:39:45 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #11: meta_score=50.5 verdict=— |
| 15:40:03 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:03 | SIGNAL | ⚡ ALPHA TrendBreakout GALAUSDT score=0.898 rr=5.00 |
| 15:40:03 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=TRENDING) |
| 15:40:03 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:03 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=44.9 above_sma=False regime=TRENDING) |
| 15:40:03 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:03 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=80.6 above_sma=True regime=TRENDING) |
| 15:40:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=60.6 above_sma=True regime=MEAN_REVERTING) |
| 15:40:03 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:03 | SIGNAL | ⚡ ALPHA PullbackEntry NOTUSDT score=0.626 rr=5.00 |
| 15:40:03 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=TRENDING) |
| 15:40:03 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:03 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=62.1 above_sma=True regime=TRENDING) |
| 15:40:03 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:03 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=54.5 above_sma=True regime=TRENDING) |
| 15:40:03 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:03 | SIGNAL | ⚡ ALPHA TrendBreakout ICPUSDT score=0.654 rr=5.00 |
| 15:40:03 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=27.5 above_sma=False regime=TRENDING) |
| 15:40:04 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:04 | FILTER | ⚡ PAPER_SPEED bypass STRKUSDT: SLEEP_MODE(vol=4774=1%_of_avg=580106,min=10%[base=45%×0.20]) |
| 15:40:04 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: SHORT entry=0.0530 rsi=71.4 |
| 15:40:06 | SIGNAL | 📈 STREAK FILUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:06 | SIGNAL | ⚡ PAPER_SPEED fallback FILUSDT: SHORT entry=1.2070 rsi=75.0 |
| 15:40:06 | SIGNAL | 🔔 Signal SHORT FILUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 15:40:06 | SIGNAL | ⚡ LCC_OVERRIDE FILUSDT: state=PAUSED cl=5 [bypass=active, size not reduced] |
| 15:40:06 | SIGNAL | ⚠️ ALLOC_ZERO FILUSDT: score=0.121 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 15:40:06 | SIGNAL | 🎯 CONSISTENCY FILUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 15:40:06 | SIGNAL | 💰 Orchestrator FILUSDT: score=0.121 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=124.122132 |
| 15:40:06 | TRADE | ⚡ PAPER_SPEED market-fill override FILUSDT: USE_LIMIT_ORDERS bypassed |
| 15:40:06 | TRADE | ✅ Opened SHORT FILUSDT qty=124.122132 risk=3.75U [MeanReversion \| MEAN_REVERTING] |
| 15:40:06 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:06 | SIGNAL | ⚡ PAPER_SPEED fallback ARBUSDT: SHORT entry=0.1398 rsi=52.9 |
| 15:40:31 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:31 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=TRENDING) |
| 15:40:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=75.2 above_sma=True regime=TRENDING) |
| 15:40:59 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 15:40:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=77.9 above_sma=True regime=TRENDING) |
| 15:40:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=58.8 above_sma=True regime=MEAN_REVERTING) |
| 15:40:59 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:59 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 15:40:59 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:59 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=62.1 above_sma=True regime=TRENDING) |
| 15:40:59 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:40:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=63.6 above_sma=True regime=TRENDING) |
| 15:41:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:41:00 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=57.7800 rsi=45.5 |
| 15:41:00 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:41:01 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=32.4 above_sma=False regime=TRENDING) |
| 15:41:02 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:41:02 | SIGNAL | ⚡ ALPHA PullbackEntry STRKUSDT score=0.629 rr=5.00 |
| 15:41:02 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: SHORT entry=0.0530 rsi=66.7 |
| 15:41:07 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 15:41:07 | SIGNAL | ⚡ PAPER_SPEED fallback ASTERUSDT: LONG entry=0.7020 rsi=42.9 |
| 15:41:08 | TRADE | [TM] FILUSDT TIME_EXIT @ 1.2090 (Fast-fail: 1.0min r=-0.690<-0.45) |
| 15:41:20 | TRADE | Position closed [SL] FILUSDT @ 1.209 |
| 15:41:24 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:41:24 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=46.7 above_sma=False regime=TRENDING) |
| 15:41:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:41:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=77.0 above_sma=True regime=TRENDING) |
| 15:41:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:41:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=79.4 above_sma=True regime=TRENDING) |
| 15:42:00 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=TRENDING) |
| 15:42:00 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:00 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=44.0 above_sma=False regime=TRENDING) |
| 15:42:00 | SIGNAL | 📈 STREAK TONUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=58.8 above_sma=True regime=MEAN_REVERTING) |
| 15:42:01 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:01 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=54.5 above_sma=True regime=TRENDING) |
| 15:42:01 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:01 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=48.2 above_sma=False regime=MEAN_REVERTING) |
| 15:42:01 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:01 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=57.8000 rsi=47.8 |
| 15:42:01 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:01 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=32.4 above_sma=False regime=TRENDING) |
| 15:42:03 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:03 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=62.1 above_sma=True regime=TRENDING) |
| 15:42:04 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:04 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: SHORT entry=0.0530 rsi=66.7 |
| 15:42:11 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:11 | FILTER | ⚡ PAPER_SPEED bypass ASTERUSDT: SLEEP_MODE(vol=1612=9%_of_avg=17795,min=10%[base=45%×0.20]) |
| 15:42:11 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=TRENDING) |
| 15:42:30 | SIGNAL | 📈 STREAK OPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:30 | FILTER | ⚡ PAPER_SPEED bypass OPUSDT: SLEEP_MODE(vol=2484=5%_of_avg=52400,min=10%[base=45%×0.20]) |
| 15:42:30 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=57.1 above_sma=False regime=MEAN_REVERTING) |
| 15:42:30 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:30 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 15:42:59 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:59 | SIGNAL | ⚡ ALPHA PullbackEntry SAHARAUSDT score=0.586 rr=4.00 |
| 15:42:59 | SIGNAL | ⚡ PAPER_SPEED fallback SAHARAUSDT: SHORT entry=0.0386 rsi=57.6 |
| 15:42:59 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=TRENDING) |
| 15:42:59 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=TRENDING) |
| 15:42:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=76.4 above_sma=True regime=TRENDING) |
| 15:42:59 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 15:42:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:42:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=76.0 above_sma=True regime=TRENDING) |
| 15:43:00 | SIGNAL | 📈 STREAK OPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:43:00 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=55.6 above_sma=True regime=MEAN_REVERTING) |
| 15:43:00 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:43:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=TRENDING) |
| 15:43:01 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:43:01 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 15:43:01 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:43:01 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=57.7800 rsi=47.8 |
| 15:43:02 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:43:02 | FILTER | ⚡ PAPER_SPEED bypass ASTERUSDT: SLEEP_MODE(vol=397=2%_of_avg=16509,min=10%[base=45%×0.20]) |
| 15:43:02 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=TRENDING) |
| 15:43:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:43:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=61.5 above_sma=True regime=MEAN_REVERTING) |
| 15:43:04 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:43:04 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=42.5 above_sma=False regime=TRENDING) |
| 15:43:09 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:43:09 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: SHORT entry=0.0530 rsi=66.7 |
| 15:44:06 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:06 | SIGNAL | ⚡ ALPHA PullbackEntry SAHARAUSDT score=0.565 rr=4.00 |
| 15:44:06 | SIGNAL | ⚡ PAPER_SPEED fallback SAHARAUSDT: SHORT entry=0.0385 rsi=55.5 |
| 15:44:06 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:06 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=TRENDING) |
| 15:44:06 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:06 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=TRENDING) |
| 15:44:06 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:06 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=66.0 above_sma=True regime=TRENDING) |
| 15:44:06 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:06 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=70.2 above_sma=True regime=TRENDING) |
| 15:44:06 | SIGNAL | 📈 STREAK TONUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:06 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=42.6 above_sma=True regime=MEAN_REVERTING) |
| 15:44:06 | SIGNAL | 📈 STREAK OPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:06 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=51.7 above_sma=False regime=MEAN_REVERTING) |
| 15:44:07 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:07 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=TRENDING) |
| 15:44:07 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:07 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=56.7 above_sma=True regime=TRENDING) |
| 15:44:09 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:09 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=55.1 above_sma=False regime=MEAN_REVERTING) |
| 15:44:09 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:09 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=40.0 above_sma=False regime=TRENDING) |
| 15:44:12 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:12 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=38.8 above_sma=False regime=TRENDING) |
| 15:44:12 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:12 | FILTER | ⚡ PAPER_SPEED bypass STRKUSDT: SLEEP_MODE(vol=40376=7%_of_avg=583832,min=10%[base=45%×0.20]) |
| 15:44:12 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=60.0 above_sma=False regime=MEAN_REVERTING) |
| 15:44:18 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:44:18 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 15:44:45 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #12: meta_score=50.4 verdict=— |
| 15:45:25 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:25 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=61.1 above_sma=True regime=TRENDING) |
| 15:45:25 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:25 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 15:45:25 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:25 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=51.4 above_sma=True regime=TRENDING) |
| 15:45:25 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:25 | SIGNAL | ⚡ PAPER_SPEED fallback SAHARAUSDT: SHORT entry=0.0386 rsi=58.6 |
| 15:45:25 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:25 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=45.2 above_sma=False regime=MEAN_REVERTING) |
| 15:45:26 | SIGNAL | 📈 STREAK OPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:26 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=43.8 above_sma=False regime=MEAN_REVERTING) |
| 15:45:35 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:35 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=54.5 above_sma=True regime=TRENDING) |
| 15:45:36 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:36 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=36.7 above_sma=False regime=TRENDING) |
| 15:45:36 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:36 | FILTER | ⚡ PAPER_SPEED bypass STRKUSDT: SLEEP_MODE(vol=3441=1%_of_avg=565998,min=10%[base=45%×0.20]) |
| 15:45:36 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: SHORT entry=0.0530 rsi=75.0 |
| 15:45:38 | SIGNAL | 📈 STREAK TONUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:38 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=MEAN_REVERTING) |
| 15:45:40 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:40 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=26.1 above_sma=False regime=TRENDING) |
| 15:45:41 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 15:45:41 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=TRENDING) |
| 15:45:53 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |

---
*EOW Quant Engine V4.0 — 2026-05-09 15:46 UTC*