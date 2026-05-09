# EOW Quant Engine — Performance Report

**Generated:** 2026-05-09 11:08 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **798 trades** with a net **LOSS** of **-241.18 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $758.82 USDT |
| Net PnL | -241.1789 USDT |
| Win Rate | 27.2% |
| Profit Factor | 0.487 |
| Sharpe Ratio | -2.261 |
| Sortino Ratio | -2.259 |
| Calmar Ratio | -0.296 |
| Max Drawdown | 25.69% |
| Risk of Ruin | 100.00% |
| Total Fees | 111.8658 USDT |
| Total Slippage | 45.4488 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -83.8643 USDT (before all costs)
- **Fees deducted:** -111.8658 USDT
- **Slippage deducted:** -45.4488 USDT
- **Net PnL (bankable):** -241.1789 USDT

### 2.2 Trade Statistics

- Avg win: +1.0558 USDT
- Avg loss: -0.8094 USDT
- Profit factor: 0.487

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-24.1%** | **-2.26** | **-2.26** | **25.7%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 11:03:14 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=TRENDING) |
| 11:03:59 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:03:59 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:03:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=10.0 above_sma=False regime=TRENDING) |
| 11:03:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:03:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:03:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=65.7 above_sma=True regime=MEAN_REVERTING) |
| 11:03:59 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:03:59 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:03:59 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 11:03:59 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:03:59 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:03:59 | SIGNAL | ⚡ ALPHA TrendBreakout NEARUSDT score=0.708 rr=5.00 |
| 11:03:59 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=78.6 above_sma=True regime=TRENDING) |
| 11:03:59 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:03:59 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:03:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=62.3 above_sma=True regime=TRENDING) |
| 11:03:59 | SIGNAL | ⚡ DTP ARBUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:03:59 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:03:59 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=59.1 above_sma=True regime=MEAN_REVERTING) |
| 11:04:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 11:04:00 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:00 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:00 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=MEAN_REVERTING) |
| 11:04:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=64.2 above_sma=True regime=MEAN_REVERTING) |
| 11:04:00 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:00 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=64.7 above_sma=True regime=TRENDING) |
| 11:04:00 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:00 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=63.6 above_sma=True regime=TRENDING) |
| 11:04:01 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:01 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:01 | FILTER | ⚡ PAPER_SPEED bypass TONUSDT: SLEEP_MODE(vol=1316=7%_of_avg=17599,min=10%[base=45%×0.20]) |
| 11:04:01 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=40.8 above_sma=False regime=TRENDING) |
| 11:04:08 | SIGNAL | ⚡ DTP ASTERUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:08 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:08 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=TRENDING) |
| 11:04:10 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:10 | SIGNAL | 📈 STREAK OPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:10 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=40.6 above_sma=False regime=TRENDING) |
| 11:04:14 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:14 | SIGNAL | 📈 STREAK FILUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:14 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=61.1 above_sma=True regime=MEAN_REVERTING) |
| 11:04:35 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #34: meta_score=50.7 verdict=— |
| 11:04:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=66.9 above_sma=True regime=MEAN_REVERTING) |
| 11:04:59 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:59 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=27.3 above_sma=False regime=TRENDING) |
| 11:04:59 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:59 | SIGNAL | 📈 STREAK OPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:59 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=40.6 above_sma=False regime=TRENDING) |
| 11:04:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=40.0 above_sma=False regime=TRENDING) |
| 11:04:59 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:04:59 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:04:59 | SIGNAL | ⚡ ALPHA TrendBreakout NEARUSDT score=0.753 rr=5.00 |
| 11:04:59 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=86.7 above_sma=True regime=TRENDING) |
| 11:05:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=53.8 above_sma=True regime=MEAN_REVERTING) |
| 11:05:00 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:00 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=63.6 above_sma=True regime=TRENDING) |
| 11:05:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=68.7 above_sma=True regime=TRENDING) |
| 11:05:00 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:00 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=64.7 above_sma=True regime=TRENDING) |
| 11:05:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_CRASH_GUARD blocked SHORT (rsi=70.1 prev=64.2≤65, need prev>65 — first-touch spike, not established reversal) |
| 11:05:01 | SIGNAL | ⚡ DTP ARBUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:01 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:01 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=59.1 above_sma=True regime=MEAN_REVERTING) |
| 11:05:01 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:01 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:01 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=62.7 above_sma=True regime=MEAN_REVERTING) |
| 11:05:01 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:01 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:01 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=44.4 above_sma=False regime=TRENDING) |
| 11:05:14 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:14 | SIGNAL | 📈 STREAK FILUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:14 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=64.7 above_sma=True regime=TRENDING) |
| 11:05:45 | SIGNAL | ⚡ DTP ASTERUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:45 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:45 | FILTER | ⚡ PAPER_SPEED bypass ASTERUSDT: SLEEP_MODE(vol=598=2%_of_avg=30878,min=10%[base=45%×0.20]) |
| 11:05:45 | SIGNAL | ⚡ PAPER_SPEED fallback ASTERUSDT: LONG entry=0.6980 rsi=44.4 |
| 11:05:59 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:59 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=33.3 above_sma=False regime=TRENDING) |
| 11:05:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=65.7 above_sma=True regime=MEAN_REVERTING) |
| 11:05:59 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:59 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=63.6 above_sma=True regime=TRENDING) |
| 11:05:59 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:05:59 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:05:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=55.2 above_sma=True regime=MEAN_REVERTING) |
| 11:06:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=53.8 above_sma=True regime=MEAN_REVERTING) |
| 11:06:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=53.9 above_sma=True regime=TRENDING) |
| 11:06:00 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:00 | SIGNAL | 📈 STREAK OPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:00 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=40.6 above_sma=False regime=TRENDING) |
| 11:06:00 | SIGNAL | ⚡ DTP ARBUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:00 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:00 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=63.6 above_sma=True regime=MEAN_REVERTING) |
| 11:06:01 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:01 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:01 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=41.7 above_sma=False regime=TRENDING) |
| 11:06:01 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:01 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:01 | SIGNAL | ⚡ ALPHA TrendBreakout ONDOUSDT score=0.521 rr=5.00 |
| 11:06:01 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=70.0 above_sma=True regime=TRENDING) |
| 11:06:01 | SIGNAL | ⚡ DTP ASTERUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:01 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:01 | FILTER | ⚡ PAPER_SPEED bypass ASTERUSDT: SLEEP_MODE(vol=24=0%_of_avg=30873,min=10%[base=45%×0.20]) |
| 11:06:01 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=MEAN_REVERTING) |
| 11:06:02 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:02 | SIGNAL | 📈 STREAK FILUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:02 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=53.3 above_sma=True regime=TRENDING) |
| 11:06:13 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:13 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:13 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=86.7 above_sma=True regime=TRENDING) |
| 11:06:15 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:15 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:15 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 11:06:28 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:28 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:28 | SIGNAL | ⚡ ALPHA PullbackEntry STRKUSDT score=0.550 rr=5.00 |
| 11:06:28 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: SHORT entry=0.0562 rsi=55.6 |
| 11:06:59 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:59 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:59 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=58.3 above_sma=True regime=MEAN_REVERTING) |
| 11:06:59 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:59 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=28.6 above_sma=False regime=TRENDING) |
| 11:06:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:06:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:06:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=48.7 above_sma=True regime=MEAN_REVERTING) |
| 11:07:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=57.1 above_sma=True regime=MEAN_REVERTING) |
| 11:07:00 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:00 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:00 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=69.2 above_sma=True regime=TRENDING) |
| 11:07:00 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:00 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:00 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.4970 rsi=53.7 |
| 11:07:00 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:00 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:00 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=76.5 above_sma=True regime=TRENDING) |
| 11:07:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=71.0 above_sma=True regime=TRENDING) |
| 11:07:02 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:02 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:02 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=40.0 above_sma=False regime=TRENDING) |
| 11:07:03 | SIGNAL | ⚡ DTP ASTERUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:03 | SIGNAL | 📈 STREAK ASTERUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:03 | FILTER | ⚡ PAPER_SPEED bypass ASTERUSDT: SLEEP_MODE(vol=83=0%_of_avg=30838,min=10%[base=45%×0.20]) |
| 11:07:03 | FILTER | ⚡ PAPER_SPEED ASTERUSDT: RSI filter blocked (rsi=42.9 above_sma=True regime=MEAN_REVERTING) |
| 11:07:06 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:06 | SIGNAL | 📈 STREAK FILUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:06 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=56.3 above_sma=True regime=MEAN_REVERTING) |
| 11:07:08 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:08 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:08 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=56.5 above_sma=True regime=MEAN_REVERTING) |
| 11:07:08 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:08 | SIGNAL | 📈 STREAK OPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:08 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=44.8 above_sma=False regime=TRENDING) |
| 11:07:12 | SIGNAL | ⚡ DTP ARBUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:07:12 | SIGNAL | 📈 STREAK ARBUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:07:12 | FILTER | ⚡ PAPER_SPEED ARBUSDT: RSI filter blocked (rsi=63.6 above_sma=True regime=MEAN_REVERTING) |
| 11:08:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:08:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:08:00 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=MEAN_REVERTING) |
| 11:08:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:08:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:08:01 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=71.0 above_sma=True regime=TRENDING) |
| 11:08:01 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:08:01 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:08:01 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=30.8 above_sma=False regime=TRENDING) |
| 11:08:02 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 11:08:02 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 11:08:02 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=48.7 above_sma=True regime=MEAN_REVERTING) |
| 11:08:02 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |

---
*EOW Quant Engine V4.0 — 2026-05-09 11:08 UTC*