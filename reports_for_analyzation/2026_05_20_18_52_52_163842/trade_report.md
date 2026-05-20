# EOW Quant Engine — Performance Report

**Generated:** 2026-05-20 13:20 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **259 trades** with a net **LOSS** of **-75.77 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $924.23 USDT |
| Net PnL | -75.7687 USDT |
| Win Rate | 18.1% |
| Profit Factor | 0.344 |
| Sharpe Ratio | -6.130 |
| Sortino Ratio | -7.239 |
| Calmar Ratio | -0.961 |
| Max Drawdown | 7.67% |
| Risk of Ruin | 100.00% |
| Total Fees | 38.4126 USDT |
| Total Slippage | 28.8094 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -8.5467 USDT (before all costs)
- **Fees deducted:** -38.4126 USDT
- **Slippage deducted:** -28.8094 USDT
- **Net PnL (bankable):** -75.7687 USDT

### 2.2 Trade Statistics

- Avg win: +0.8447 USDT
- Avg loss: -0.5447 USDT
- Profit factor: 0.344

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-7.6%** | **-6.13** | **-7.24** | **7.7%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 13:06:58 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=77533.3500 rsi=48.5 |
| 13:06:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:06:58 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: SHORT entry=0.3868 rsi=51.2 |
| 13:06:59 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:06:59 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=81.8 above_sma=True bands=[56.5,43.5] (rsi=81.8 above_sma=True regime=TRENDING) |
| 13:06:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:06:59 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9560 rsi=45.8 |
| 13:07:57 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:07:57 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=40.0 above_sma=False bands=[56.5,43.5] (rsi=40.0 above_sma=False regime=TRENDING) |
| 13:07:57 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:07:57 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=36.6 above_sma=False bands=[56.5,43.5] (rsi=36.6 above_sma=False regime=TRENDING) |
| 13:07:57 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:07:57 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=42.9 above_sma=False bands=[56.5,43.5] (rsi=42.9 above_sma=False regime=TRENDING) |
| 13:07:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:07:58 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=41.0 above_sma=False bands=[56.5,43.5] (rsi=41.0 above_sma=False regime=TRENDING) |
| 13:07:58 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:07:58 | SIGNAL | ⚡ PAPER_SPEED fallback SPKUSDT: LONG entry=0.0286 rsi=48.0 |
| 13:08:05 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:08:05 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9620 rsi=53.6 |
| 13:08:07 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:08:07 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=81.1 above_sma=True bands=[56.5,43.5] (rsi=81.1 above_sma=True regime=TRENDING) |
| 13:08:57 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:08:57 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=45.8 above_sma=True bands=[27.0,73.0] (rsi=45.8 above_sma=True regime=MEAN_REVERTING) |
| 13:08:57 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:08:57 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=41.0 above_sma=False bands=[56.5,43.5] (rsi=41.0 above_sma=False regime=TRENDING) |
| 13:08:57 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:08:57 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9620 rsi=50.0 |
| 13:08:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:08:58 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=40.9 above_sma=False bands=[56.5,43.5] (rsi=40.9 above_sma=False regime=TRENDING) |
| 13:08:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:08:58 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2133.1600 rsi=42.3 |
| 13:08:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:08:58 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: SHORT entry=0.3875 rsi=46.6 |
| 13:09:06 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:09:06 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=81.1 above_sma=True bands=[56.5,43.5] (rsi=81.1 above_sma=True regime=TRENDING) |
| 13:09:57 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:09:57 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=40.0 above_sma=False bands=[56.5,43.5] (rsi=40.0 above_sma=False regime=TRENDING) |
| 13:09:57 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:09:57 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=77.8 above_sma=True bands=[56.5,43.5] (rsi=77.8 above_sma=True regime=TRENDING) |
| 13:09:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:09:58 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=43.4 above_sma=False bands=[56.5,43.5] (rsi=43.4 above_sma=False regime=TRENDING) |
| 13:09:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:09:58 | SIGNAL | ⚡ PAPER_SPEED fallback EDENUSDT: SHORT entry=0.0810 rsi=46.9 |
| 13:09:58 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:09:58 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=47.2 above_sma=True bands=[27.0,73.0] (rsi=47.2 above_sma=True regime=MEAN_REVERTING) |
| 13:09:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:09:58 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=38.3 above_sma=False bands=[56.5,43.5] (rsi=38.3 above_sma=False regime=TRENDING) |
| 13:10:00 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:10:00 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.531 rr=5.00 |
| 13:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9590 rsi=40.7 |
| 13:10:31 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #43: meta_score=48.2 verdict=— |
| 13:10:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:10:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=17.0 above_sma=False bands=[56.0,44.0] (rsi=17.0 above_sma=False regime=TRENDING) |
| 13:10:58 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:10:58 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=39.2 above_sma=True bands=[27.0,73.0] (rsi=39.2 above_sma=True regime=MEAN_REVERTING) |
| 13:10:58 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:10:58 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.499 rr=5.00 |
| 13:10:58 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9580 rsi=32.0 |
| 13:10:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:10:58 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=43.4 above_sma=False bands=[56.0,44.0] (rsi=43.4 above_sma=False regime=TRENDING) |
| 13:10:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:10:58 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=24.7 above_sma=False bands=[56.0,44.0] (rsi=24.7 above_sma=False regime=TRENDING) |
| 13:10:59 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:10:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=25.0 above_sma=False bands=[56.0,44.0] (rsi=25.0 above_sma=False regime=TRENDING) |
| 13:10:59 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:10:59 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=73.7 above_sma=True bands=[56.0,44.0] (rsi=73.7 above_sma=True regime=TRENDING) |
| 13:11:57 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:11:57 | SIGNAL | ⚡ ALPHA TrendBreakout ONDOUSDT score=0.608 rr=5.00 |
| 13:11:57 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=23.7 above_sma=False bands=[55.5,44.5] (rsi=23.7 above_sma=False regime=TRENDING) |
| 13:11:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:11:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=19.3 above_sma=False bands=[55.5,44.5] (rsi=19.3 above_sma=False regime=TRENDING) |
| 13:11:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:11:58 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=36.5 above_sma=False bands=[55.5,44.5] (rsi=36.5 above_sma=False regime=TRENDING) |
| 13:11:59 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:11:59 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=49.8 above_sma=True bands=[27.0,73.0] (rsi=49.8 above_sma=True regime=MEAN_REVERTING) |
| 13:11:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:11:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=27.0 above_sma=False bands=[55.5,44.5] (rsi=27.0 above_sma=False regime=TRENDING) |
| 13:12:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:12:03 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9560 rsi=29.6 |
| 13:12:05 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:12:05 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=75.7 above_sma=True bands=[55.5,44.5] (rsi=75.7 above_sma=True regime=TRENDING) |
| 13:12:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:12:58 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=32.8 above_sma=False bands=[55.0,45.0] (rsi=32.8 above_sma=False regime=TRENDING) |
| 13:12:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:12:58 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=1=7%_of_avg=10,min=10%[base=45%×0.20]) |
| 13:12:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=22.1 above_sma=False bands=[55.0,45.0] (rsi=22.1 above_sma=False regime=TRENDING) |
| 13:12:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:12:58 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=37.1 above_sma=False bands=[55.0,45.0] (rsi=37.1 above_sma=False regime=TRENDING) |
| 13:12:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:12:58 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=34.0 above_sma=False bands=[55.0,45.0] (rsi=34.0 above_sma=False regime=TRENDING) |
| 13:13:00 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:13:00 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=38.1 above_sma=False bands=[27.0,73.0] (rsi=38.1 above_sma=False regime=MEAN_REVERTING) |
| 13:13:01 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:13:01 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=68.3 above_sma=True bands=[55.0,45.0] (rsi=68.3 above_sma=True regime=TRENDING) |
| 13:13:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:13:03 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9550 rsi=30.8 |
| 13:13:57 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:13:57 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=37.8 above_sma=False bands=[54.5,45.5] (rsi=37.8 above_sma=False regime=TRENDING) |
| 13:13:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:13:58 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=1=10%_of_avg=10,min=10%[base=45%×0.20]) |
| 13:13:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=22.7 above_sma=False bands=[54.5,45.5] (rsi=22.7 above_sma=False regime=TRENDING) |
| 13:13:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:13:58 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=42.5 above_sma=False bands=[54.5,45.5] (rsi=42.5 above_sma=False regime=TRENDING) |
| 13:13:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:13:58 | SIGNAL | ⚡ PAPER_SPEED fallback EDENUSDT: SHORT entry=0.0810 rsi=50.0 |
| 13:13:59 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:13:59 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=30.5 above_sma=False bands=[27.0,73.0] (rsi=30.5 above_sma=False regime=MEAN_REVERTING) |
| 13:14:02 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:14:02 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=67.5 above_sma=True bands=[54.5,45.5] (rsi=67.5 above_sma=True regime=TRENDING) |
| 13:14:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:14:03 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.516 rr=5.00 |
| 13:14:03 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9560 rsi=36.0 |
| 13:14:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:14:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: CONTEXT_TOXIC: toxic_context avg=-0.3349 n=20 (rsi=17.2 above_sma=False regime=MEAN_REVERTING) |
| 13:14:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:14:58 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=43.7 above_sma=False bands=[54.0,46.0] (rsi=43.7 above_sma=False regime=TRENDING) |
| 13:14:58 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:14:58 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9550 rsi=40.9 |
| 13:14:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:14:58 | SIGNAL | ⚡ PAPER_SPEED fallback EDENUSDT: SHORT entry=0.0808 rsi=48.9 |
| 13:14:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:14:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=29.7 above_sma=False bands=[54.0,46.0] (rsi=29.7 above_sma=False regime=TRENDING) |
| 13:15:01 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:15:01 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=29.9 above_sma=False bands=[27.0,73.0] (rsi=29.9 above_sma=False regime=MEAN_REVERTING) |
| 13:15:02 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:15:02 | FILTER | ⚡ PAPER_SPEED bypass NEARUSDT: SLEEP_MODE(vol=2177=5%_of_avg=41254,min=10%[base=45%×0.20]) |
| 13:15:02 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=59.4 above_sma=True bands=[54.0,46.0] (rsi=59.4 above_sma=True regime=TRENDING) |
| 13:15:31 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #44: meta_score=48.2 verdict=— |
| 13:15:58 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:15:58 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9540 rsi=40.9 |
| 13:15:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:15:58 | SIGNAL | ⚡ PAPER_SPEED fallback EDENUSDT: SHORT entry=0.0805 rsi=55.0 |
| 13:15:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:15:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: CONTEXT_TOXIC: toxic_context avg=-0.3349 n=20 (rsi=21.4 above_sma=False regime=MEAN_REVERTING) |
| 13:15:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:15:58 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: SHORT entry=0.3862 rsi=50.7 |
| 13:15:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:15:58 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=30.9 above_sma=False bands=[53.5,46.5] (rsi=30.9 above_sma=False regime=TRENDING) |
| 13:15:58 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:15:58 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=27.2 above_sma=False bands=[27.0,73.0] (rsi=27.2 above_sma=False regime=MEAN_REVERTING) |
| 13:15:58 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:15:58 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=53.6 above_sma=True bands=[53.5,46.5] (rsi=53.6 above_sma=True regime=TRENDING) |
| 13:16:57 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:16:57 | FILTER | ⚡ PAPER_SPEED BTCUSDT: CONTEXT_TOXIC: toxic_context avg=-0.3349 n=20 (rsi=11.6 above_sma=False regime=MEAN_REVERTING) |
| 13:16:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:16:58 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=19.7 above_sma=False bands=[53.0,47.0] (rsi=19.7 above_sma=False regime=TRENDING) |
| 13:16:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:16:58 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=44.4 above_sma=False bands=[53.0,47.0] (rsi=44.4 above_sma=False regime=TRENDING) |
| 13:16:58 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:16:58 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=27.9 above_sma=False bands=[27.0,73.0] (rsi=27.9 above_sma=False regime=MEAN_REVERTING) |
| 13:16:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:16:58 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=61.4 above_sma=True bands=[27.0,73.0] (rsi=61.4 above_sma=True regime=MEAN_REVERTING) |
| 13:16:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:16:59 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.9550 rsi=40.9 |
| 13:17:07 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:17:07 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=55.2 above_sma=True bands=[53.0,47.0] (rsi=55.2 above_sma=True regime=TRENDING) |
| 13:17:57 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:17:57 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=43.8 above_sma=False bands=[52.5,47.5] (rsi=43.8 above_sma=False regime=TRENDING) |
| 13:17:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:17:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: CONTEXT_TOXIC: toxic_context avg=-0.3349 n=20 (rsi=12.5 above_sma=False regime=MEAN_REVERTING) |
| 13:17:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:17:58 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=64.3 above_sma=True bands=[27.0,73.0] (rsi=64.3 above_sma=True regime=MEAN_REVERTING) |
| 13:17:58 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:17:58 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI_LEVEL: rsi=47.6 above_sma=True bands=[27.0,73.0] (rsi=47.6 above_sma=True regime=MEAN_REVERTING) |
| 13:17:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:17:58 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=19.8 above_sma=False bands=[52.5,47.5] (rsi=19.8 above_sma=False regime=TRENDING) |
| 13:17:59 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:17:59 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=30.1 above_sma=False bands=[52.5,47.5] (rsi=30.1 above_sma=False regime=TRENDING) |
| 13:17:59 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:17:59 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: LONG entry=1.6600 rsi=51.6 |
| 13:18:57 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: CONTEXT_TOXIC: toxic_context avg=-0.3349 n=20 (rsi=23.0 above_sma=False regime=MEAN_REVERTING) |
| 13:18:58 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=32.8 above_sma=False bands=[52.0,48.0] (rsi=32.8 above_sma=False regime=TRENDING) |
| 13:18:58 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI_LEVEL: rsi=55.0 above_sma=True bands=[27.0,73.0] (rsi=55.0 above_sma=True regime=MEAN_REVERTING) |
| 13:18:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=27.6 above_sma=False bands=[27.0,73.0] (rsi=27.6 above_sma=False regime=MEAN_REVERTING) |
| 13:18:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=35.4 above_sma=False bands=[52.0,48.0] (rsi=35.4 above_sma=False regime=TRENDING) |
| 13:18:58 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:58 | SIGNAL | ⚡ ALPHA PullbackEntry NEARUSDT score=0.524 rr=5.00 |
| 13:18:58 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: LONG entry=1.6590 rsi=38.5 |
| 13:18:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:18:59 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=69.8 above_sma=True bands=[27.0,73.0] (rsi=69.8 above_sma=True regime=MEAN_REVERTING) |
| 13:19:57 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:57 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: LONG entry=1.6600 rsi=50.0 |
| 13:19:57 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:57 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=28.1 above_sma=False bands=[27.0,73.0] (rsi=28.1 above_sma=False regime=MEAN_REVERTING) |
| 13:19:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: CONTEXT_TOXIC: toxic_context avg=-0.3349 n=20 (rsi=22.2 above_sma=False regime=MEAN_REVERTING) |
| 13:19:58 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:58 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=40.8 above_sma=False bands=[51.5,48.5] (rsi=40.8 above_sma=False regime=TRENDING) |
| 13:19:58 | SIGNAL | ⚡ DTP EDENUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:19:58 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=63.4 above_sma=True bands=[27.0,73.0] (rsi=63.4 above_sma=True regime=MEAN_REVERTING) |
| 13:19:58 | SYSTEM | 🔬 Live Process Snapshot downloaded → eow_live_process_20260520_131958.zip (103 KB \| logs=2000 rl_contexts=21 trades=259) |
| 13:20:00 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:20:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI_LEVEL: rsi=47.6 above_sma=True bands=[27.0,73.0] (rsi=47.6 above_sma=True regime=MEAN_REVERTING) |
| 13:20:00 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 13:20:00 | FILTER | ⚡ PAPER_SPEED SPKUSDT: RSI_LEVEL: rsi=30.7 above_sma=False bands=[51.5,48.5] (rsi=30.7 above_sma=False regime=TRENDING) |

---
*EOW Quant Engine V4.0 — 2026-05-20 13:20 UTC*