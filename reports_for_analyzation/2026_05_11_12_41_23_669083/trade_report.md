# EOW Quant Engine — Performance Report

**Generated:** 2026-05-11 07:07 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **1156 trades** with a net **LOSS** of **-316.58 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $683.42 USDT |
| Net PnL | -316.5775 USDT |
| Win Rate | 23.8% |
| Profit Factor | 0.455 |
| Sharpe Ratio | -2.434 |
| Sortino Ratio | -2.492 |
| Calmar Ratio | -0.209 |
| Max Drawdown | 33.08% |
| Risk of Ruin | 100.00% |
| Total Fees | 153.0279 USDT |
| Total Slippage | 76.3204 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -87.2292 USDT (before all costs)
- **Fees deducted:** -153.0279 USDT
- **Slippage deducted:** -76.3204 USDT
- **Net PnL (bankable):** -316.5775 USDT

### 2.2 Trade Statistics

- Avg win: +0.9609 USDT
- Avg loss: -0.6593 USDT
- Profit factor: 0.455

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-31.7%** | **-2.43** | **-2.49** | **33.1%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 07:01:00 | SIGNAL | ⚠️ ALLOC_ZERO ONDOUSDT: score=0.297 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 07:01:00 | SIGNAL | 🎯 CONSISTENCY ONDOUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 07:01:00 | SIGNAL | 💰 Orchestrator ONDOUSDT: score=0.297 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=314.175041 |
| 07:01:00 | TRADE | ⚡ PAPER_SPEED market-fill override ONDOUSDT: USE_LIMIT_ORDERS bypassed |
| 07:01:00 | TRADE | ✅ Opened LONG ONDOUSDT qty=314.175041 risk=3.42U [MeanReversion \| MEAN_REVERTING] |
| 07:01:00 | SIGNAL | 📈 STREAK APTUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:00 | FILTER | ⚡ PAPER_SPEED APTUSDT: RSI filter blocked (rsi=33.3 above_sma=False regime=TRENDING) |
| 07:01:00 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:00 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=26.3 above_sma=False regime=TRENDING) |
| 07:01:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=44.3 above_sma=False regime=TRENDING) |
| 07:01:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=54.6 above_sma=False regime=MEAN_REVERTING) |
| 07:01:01 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:01 | FILTER | ⚡ PAPER_SPEED SEIUSDT: RSI filter blocked (rsi=42.2 above_sma=False regime=TRENDING) |
| 07:01:01 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:01 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=36.6 above_sma=False regime=TRENDING) |
| 07:01:02 | SIGNAL | 📈 STREAK XLMUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:02 | FILTER | ⚡ PAPER_SPEED XLMUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 07:01:03 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:03 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=45.3 above_sma=False regime=TRENDING) |
| 07:01:04 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:04 | SIGNAL | ⚡ ALPHA PullbackEntry WLDUSDT score=0.610 rr=5.00 |
| 07:01:04 | SIGNAL | ⚡ PAPER_SPEED fallback WLDUSDT: SHORT entry=0.2813 rsi=56.2 |
| 07:01:05 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:05 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=51.7 above_sma=False regime=TRENDING) |
| 07:01:06 | SIGNAL | 📈 STREAK TONUSDT: COLD len=19 score_adj=+0.05 → eff_min=0.480 |
| 07:01:06 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.573 rr=5.00 |
| 07:01:06 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.2980 rsi=59.3 |
| 07:01:14 | TRADE | [TM] ONDOUSDT TIME_EXIT @ 0.4343 (Fast-fail: 0.2min r=-0.458<-0.45) |
| 07:01:14 | TRADE | Position closed [SL] ONDOUSDT @ 0.4343 |
| 07:01:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:01:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=51.8 above_sma=False regime=TRENDING) |
| 07:01:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:01:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=50.4 above_sma=False regime=TRENDING) |
| 07:02:00 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:02:00 | SIGNAL | ⚡ ALPHA TrendBreakout SEIUSDT score=0.684 rr=5.00 |
| 07:02:00 | FILTER | ⚡ PAPER_SPEED SEIUSDT: RSI filter blocked (rsi=38.0 above_sma=False regime=TRENDING) |
| 07:02:00 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:02:00 | SIGNAL | ⚡ ALPHA TrendBreakout LAYERUSDT score=0.755 rr=5.00 |
| 07:02:00 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=23.8 above_sma=False regime=TRENDING) |
| 07:02:00 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:02:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=37.0 above_sma=False regime=TRENDING) |
| 07:02:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:02:00 | SIGNAL | ⚡ ALPHA PullbackEntry WLDUSDT score=0.727 rr=5.00 |
| 07:02:00 | SIGNAL | ⚡ PAPER_SPEED fallback WLDUSDT: SHORT entry=0.2816 rsi=66.7 |
| 07:02:01 | SIGNAL | 📈 STREAK TONUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:02:01 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.521 rr=5.00 |
| 07:02:01 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.2950 rsi=57.1 |
| 07:02:01 | SIGNAL | 📈 STREAK APTUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:02:01 | SIGNAL | ⚡ ALPHA TrendBreakout APTUSDT score=0.791 rr=5.00 |
| 07:02:01 | FILTER | ⚡ PAPER_SPEED APTUSDT: RSI filter blocked (rsi=28.6 above_sma=False regime=TRENDING) |
| 07:02:02 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:02:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=48.4 above_sma=False regime=MEAN_REVERTING) |
| 07:02:04 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:02:04 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=48.4 above_sma=False regime=TRENDING) |
| 07:02:09 | SIGNAL | 📈 STREAK XLMUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:02:09 | FILTER | ⚡ PAPER_SPEED XLMUSDT: RSI filter blocked (rsi=43.7 above_sma=False regime=TRENDING) |
| 07:03:00 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=43.5 above_sma=False regime=TRENDING) |
| 07:03:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=48.5 above_sma=False regime=TRENDING) |
| 07:03:00 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:00 | FILTER | ⚡ PAPER_SPEED SEIUSDT: RSI filter blocked (rsi=42.4 above_sma=False regime=TRENDING) |
| 07:03:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=48.7 above_sma=False regime=TRENDING) |
| 07:03:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=53.7 above_sma=False regime=MEAN_REVERTING) |
| 07:03:02 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:02 | SIGNAL | ⚡ PAPER_SPEED fallback WLDUSDT: SHORT entry=0.2812 rsi=54.5 |
| 07:03:02 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:02 | SIGNAL | ⚡ ALPHA PullbackEntry LTCUSDT score=0.578 rr=5.00 |
| 07:03:02 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.8100 rsi=57.9 |
| 07:03:02 | SIGNAL | 📈 STREAK APTUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:02 | FILTER | ⚡ PAPER_SPEED APTUSDT: RSI filter blocked (rsi=28.6 above_sma=False regime=TRENDING) |
| 07:03:04 | SIGNAL | 📈 STREAK TONUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:04 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.486 rr=5.00 |
| 07:03:04 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.2930 rsi=57.1 |
| 07:03:04 | SIGNAL | 📈 STREAK XLMUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:04 | SIGNAL | ⚡ PAPER_SPEED fallback XLMUSDT: SHORT entry=0.1664 rsi=53.3 |
| 07:03:04 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:03:04 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=25.6 above_sma=False regime=TRENDING) |
| 07:03:11 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #20: meta_score=47.6 verdict=— |
| 07:04:00 | SIGNAL | 📈 STREAK TONUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:00 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.551 rr=5.00 |
| 07:04:00 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.2940 rsi=55.6 |
| 07:04:00 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:00 | FILTER | ⚡ PAPER_SPEED SEIUSDT: RSI filter blocked (rsi=44.8 above_sma=False regime=TRENDING) |
| 07:04:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2331.0000 rsi=53.6 |
| 07:04:00 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:00 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=24.4 above_sma=False regime=TRENDING) |
| 07:04:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=47.8 above_sma=False regime=TRENDING) |
| 07:04:01 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:01 | FILTER | ⚡ PAPER_SPEED WLDUSDT: RSI filter blocked (rsi=46.2 above_sma=False regime=TRENDING) |
| 07:04:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=TRENDING) |
| 07:04:01 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:01 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=46.2 above_sma=False regime=TRENDING) |
| 07:04:01 | SIGNAL | 📈 STREAK XLMUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:01 | FILTER | ⚡ PAPER_SPEED XLMUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 07:04:07 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:07 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.7300 rsi=53.7 |
| 07:04:12 | SIGNAL | 📈 STREAK APTUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:12 | FILTER | ⚡ PAPER_SPEED APTUSDT: RSI filter blocked (rsi=25.0 above_sma=False regime=TRENDING) |
| 07:04:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=48.3 above_sma=False regime=TRENDING) |
| 07:04:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:04:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=40.2 above_sma=False regime=TRENDING) |
| 07:05:00 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:00 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=24.4 above_sma=False regime=TRENDING) |
| 07:05:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:00 | FILTER | ⚡ PAPER_SPEED WLDUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 07:05:02 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:02 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=48.8 above_sma=False regime=TRENDING) |
| 07:05:02 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:02 | FILTER | ⚡ PAPER_SPEED SEIUSDT: RSI filter blocked (rsi=36.3 above_sma=False regime=TRENDING) |
| 07:05:03 | SIGNAL | 📈 STREAK XLMUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:03 | FILTER | ⚡ PAPER_SPEED bypass XLMUSDT: SLEEP_MODE(vol=722=2%_of_avg=31876,min=10%[base=45%×0.20]) |
| 07:05:03 | SIGNAL | ⚡ PAPER_SPEED fallback XLMUSDT: SHORT entry=0.1663 rsi=53.3 |
| 07:05:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:03 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.559 rr=5.00 |
| 07:05:03 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.2950 rsi=64.0 |
| 07:05:03 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:03 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.7400 rsi=52.5 |
| 07:05:05 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:05 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=65.9 above_sma=True regime=MEAN_REVERTING) |
| 07:05:14 | SIGNAL | 📈 STREAK APTUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:14 | FILTER | ⚡ PAPER_SPEED APTUSDT: RSI filter blocked (rsi=25.0 above_sma=False regime=TRENDING) |
| 07:05:33 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:05:33 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=30.0 above_sma=False regime=TRENDING) |
| 07:06:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=36.7 above_sma=False regime=TRENDING) |
| 07:06:01 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:01 | SIGNAL | ⚡ ALPHA TrendBreakout LAYERUSDT score=0.702 rr=4.00 |
| 07:06:01 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=23.4 above_sma=False regime=TRENDING) |
| 07:06:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=25.7 above_sma=False regime=TRENDING) |
| 07:06:01 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:01 | FILTER | ⚡ PAPER_SPEED SEIUSDT: RSI filter blocked (rsi=34.7 above_sma=False regime=TRENDING) |
| 07:06:01 | SIGNAL | 📈 STREAK TONUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:01 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.512 rr=5.00 |
| 07:06:01 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=56.5 above_sma=False regime=MEAN_REVERTING) |
| 07:06:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=65.9 above_sma=True regime=MEAN_REVERTING) |
| 07:06:01 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:01 | SIGNAL | ⚡ ALPHA TrendBreakout WLDUSDT score=0.897 rr=5.00 |
| 07:06:01 | FILTER | ⚡ PAPER_SPEED WLDUSDT: RSI filter blocked (rsi=27.8 above_sma=False regime=TRENDING) |
| 07:06:02 | SIGNAL | 📈 STREAK XLMUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:02 | FILTER | ⚡ PAPER_SPEED XLMUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 07:06:02 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:02 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=45.2 above_sma=False regime=TRENDING) |
| 07:06:04 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:04 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=44.3 above_sma=False regime=TRENDING) |
| 07:06:06 | SIGNAL | 📈 STREAK APTUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.480 |
| 07:06:06 | FILTER | ⚡ PAPER_SPEED APTUSDT: RSI filter blocked (rsi=18.2 above_sma=False regime=TRENDING) |
| 07:06:20 | SIGNAL | ⚡ DTP ASTERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:06:20 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:06:20 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=41.7 above_sma=False regime=TRENDING) |
| 07:07:00 | SIGNAL | ⚡ DTP WLDUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:00 | FILTER | ⚡ PAPER_SPEED WLDUSDT: RSI filter blocked (rsi=28.6 above_sma=False regime=TRENDING) |
| 07:07:00 | SIGNAL | ⚡ DTP SEIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:00 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:00 | FILTER | ⚡ PAPER_SPEED SEIUSDT: RSI filter blocked (rsi=30.1 above_sma=False regime=TRENDING) |
| 07:07:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=34.8 above_sma=False regime=TRENDING) |
| 07:07:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:00 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 07:07:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=16.9 above_sma=False regime=TRENDING) |
| 07:07:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=45.2 above_sma=False regime=MEAN_REVERTING) |
| 07:07:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=24.7 above_sma=False regime=TRENDING) |
| 07:07:01 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:01 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:01 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=46.1 above_sma=False regime=TRENDING) |
| 07:07:01 | SIGNAL | ⚡ DTP LAYERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:01 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:01 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=35.9 above_sma=False regime=TRENDING) |
| 07:07:02 | SIGNAL | ⚡ DTP APTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:02 | SIGNAL | 📈 STREAK APTUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:02 | FILTER | ⚡ PAPER_SPEED APTUSDT: RSI filter blocked (rsi=18.2 above_sma=False regime=TRENDING) |
| 07:07:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=52.2 above_sma=False regime=MEAN_REVERTING) |
| 07:07:05 | SIGNAL | ⚡ DTP XLMUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:05 | SIGNAL | 📈 STREAK XLMUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:05 | FILTER | ⚡ PAPER_SPEED XLMUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 07:07:07 | SIGNAL | ⚡ DTP ASTERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 07:07:07 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=20 score_adj=+0.05 → eff_min=0.430 |
| 07:07:07 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=41.7 above_sma=False regime=TRENDING) |
| 07:07:40 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |

---
*EOW Quant Engine V4.0 — 2026-05-11 07:07 UTC*