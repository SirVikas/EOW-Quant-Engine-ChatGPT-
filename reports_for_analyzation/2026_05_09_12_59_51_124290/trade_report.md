# EOW Quant Engine — Performance Report

**Generated:** 2026-05-09 07:25 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **777 trades** with a net **LOSS** of **-235.99 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $764.01 USDT |
| Net PnL | -235.9887 USDT |
| Win Rate | 27.7% |
| Profit Factor | 0.491 |
| Sharpe Ratio | -2.244 |
| Sortino Ratio | -2.234 |
| Calmar Ratio | -0.304 |
| Max Drawdown | 25.19% |
| Risk of Ruin | 100.00% |
| Total Fees | 109.3052 USDT |
| Total Slippage | 43.5284 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -83.1551 USDT (before all costs)
- **Fees deducted:** -109.3052 USDT
- **Slippage deducted:** -43.5284 USDT
- **Net PnL (bankable):** -235.9887 USDT

### 2.2 Trade Statistics

- Avg win: +1.0578 USDT
- Avg loss: -0.8246 USDT
- Profit factor: 0.491

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-23.6%** | **-2.24** | **-2.23** | **25.2%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 07:20:59 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:20:59 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=23.4 above_sma=False regime=TRENDING) |
| 07:20:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:20:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:20:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=65.0 above_sma=True regime=MEAN_REVERTING) |
| 07:21:00 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:00 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:00 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=69.0 above_sma=True regime=TRENDING) |
| 07:21:00 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:00 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:00 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.622 rr=5.00 |
| 07:21:00 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.5730 rsi=60.4 |
| 07:21:00 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:00 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:00 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=31.8 above_sma=False regime=TRENDING) |
| 07:21:01 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:01 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:01 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=41.5 above_sma=False regime=MEAN_REVERTING) |
| 07:21:01 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:01 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:01 | FILTER | ⚡ PAPER_SPEED bypass LTCUSDT: SLEEP_MODE(vol=18=7%_of_avg=251,min=10%[base=45%×0.20]) |
| 07:21:01 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=61.5 above_sma=True regime=MEAN_REVERTING) |
| 07:21:01 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:01 | SIGNAL | 📈 STREAK OPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:01 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=47.3 above_sma=True regime=MEAN_REVERTING) |
| 07:21:05 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:05 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:05 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=36.4 above_sma=False regime=TRENDING) |
| 07:21:06 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:06 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:06 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=35.6 above_sma=False regime=TRENDING) |
| 07:21:39 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #30: meta_score=51.6 verdict=— |
| 07:21:59 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:59 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:59 | SIGNAL | ⚡ PAPER_SPEED fallback GALAUSDT: SHORT entry=0.0043 rsi=61.5 |
| 07:21:59 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:59 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 07:21:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_CRASH_GUARD blocked SHORT (rsi=76.6 prev=65.0≤65, need prev>65 — first-touch spike, not established reversal) |
| 07:21:59 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:59 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=69.4 above_sma=True regime=TRENDING) |
| 07:21:59 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:59 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:59 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 07:21:59 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:59 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:21:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=48.9 above_sma=True regime=MEAN_REVERTING) |
| 07:21:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:21:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:00 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.514 rr=5.00 |
| 07:22:00 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.5730 rsi=57.8 |
| 07:22:00 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:00 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:00 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=25.0 above_sma=False regime=TRENDING) |
| 07:22:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=83.7 above_sma=True regime=TRENDING) |
| 07:22:00 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:00 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:00 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=39.1 above_sma=False regime=TRENDING) |
| 07:22:02 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:02 | SIGNAL | 📈 STREAK OPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:02 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=48.1 above_sma=False regime=MEAN_REVERTING) |
| 07:22:02 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:02 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:02 | FILTER | ⚡ PAPER_SPEED bypass LTCUSDT: SLEEP_MODE(vol=13=6%_of_avg=226,min=10%[base=45%×0.20]) |
| 07:22:02 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=69.2 above_sma=True regime=MEAN_REVERTING) |
| 07:22:14 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:14 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:14 | FILTER | ⚡ PAPER_SPEED bypass UNIUSDT: SLEEP_MODE(vol=83=1%_of_avg=6385,min=10%[base=45%×0.20]) |
| 07:22:14 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=44.7 above_sma=False regime=TRENDING) |
| 07:22:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=93.8 above_sma=True regime=TRENDING) |
| 07:22:59 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:59 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=66.7 above_sma=False regime=MEAN_REVERTING) |
| 07:22:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=91.5 above_sma=True regime=TRENDING) |
| 07:22:59 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:59 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:59 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=24.5 above_sma=False regime=TRENDING) |
| 07:22:59 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:22:59 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:22:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=57.1 above_sma=False regime=MEAN_REVERTING) |
| 07:23:00 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:00 | SIGNAL | 📈 STREAK OPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:00 | FILTER | ⚡ PAPER_SPEED bypass OPUSDT: SLEEP_MODE(vol=8547=10%_of_avg=86147,min=10%[base=45%×0.20]) |
| 07:23:00 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=53.7 above_sma=True regime=MEAN_REVERTING) |
| 07:23:01 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:01 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:01 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=67.1 above_sma=True regime=MEAN_REVERTING) |
| 07:23:01 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:01 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:01 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.5900 rsi=78.3 |
| 07:23:01 | SIGNAL | 🔔 Signal SHORT LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:23:01 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:01 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:01 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=42.4 above_sma=False regime=MEAN_REVERTING) |
| 07:23:02 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:02 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:02 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: SHORT entry=3.6830 rsi=55.9 |
| 07:23:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:03 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.5710 rsi=53.3 |
| 07:23:04 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:04 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:04 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=43.5 above_sma=False regime=TRENDING) |
| 07:23:09 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:09 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:09 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=45.5 above_sma=False regime=TRENDING) |
| 07:23:59 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:59 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:59 | FILTER | ⚡ PAPER_SPEED bypass ICPUSDT: SLEEP_MODE(vol=358=10%_of_avg=3740,min=10%[base=45%×0.20]) |
| 07:23:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=68.1 above_sma=True regime=MEAN_REVERTING) |
| 07:23:59 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:59 | SIGNAL | 📈 STREAK OPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:59 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=52.8 above_sma=True regime=MEAN_REVERTING) |
| 07:23:59 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:59 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:59 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=17.0 above_sma=False regime=TRENDING) |
| 07:23:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:59 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=0=8%_of_avg=5,min=10%[base=45%×0.20]) |
| 07:23:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=96.5 above_sma=True regime=TRENDING) |
| 07:23:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=91.4 above_sma=True regime=TRENDING) |
| 07:23:59 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:23:59 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:23:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=57.1 above_sma=False regime=MEAN_REVERTING) |
| 07:24:00 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:00 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:00 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=61.5 above_sma=False regime=MEAN_REVERTING) |
| 07:24:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=52.2 above_sma=False regime=MEAN_REVERTING) |
| 07:24:00 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:00 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:00 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: SHORT entry=3.6830 rsi=79.2 |
| 07:24:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:00 | FILTER | ⚡ PAPER_SPEED bypass LTCUSDT: SLEEP_MODE(vol=11=7%_of_avg=152,min=10%[base=45%×0.20]) |
| 07:24:00 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.5800 rsi=72.7 |
| 07:24:00 | SIGNAL | 🔔 Signal SHORT LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:24:00 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:00 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:00 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.5680 rsi=53.3 |
| 07:24:01 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:01 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:01 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=47.8 above_sma=False regime=MEAN_REVERTING) |
| 07:24:06 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:06 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:06 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=43.5 above_sma=False regime=TRENDING) |
| 07:24:59 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:59 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:59 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=53.8 above_sma=True regime=MEAN_REVERTING) |
| 07:24:59 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:59 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:59 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=64.3 above_sma=False regime=MEAN_REVERTING) |
| 07:24:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:24:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:24:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=96.7 above_sma=True regime=TRENDING) |
| 07:25:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=91.4 above_sma=True regime=TRENDING) |
| 07:25:00 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:00 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:00 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=58.6100 rsi=79.2 |
| 07:25:00 | SIGNAL | 🔔 Signal SHORT LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:25:01 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:01 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:01 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 07:25:01 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:01 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:01 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=15.2 above_sma=False regime=TRENDING) |
| 07:25:01 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:01 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:01 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: SHORT entry=3.7510 rsi=70.5 |
| 07:25:01 | SIGNAL | 🔔 Signal SHORT ICPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:25:01 | SIGNAL | ⚡ DTP OPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:01 | SIGNAL | 📈 STREAK OPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:01 | FILTER | ⚡ PAPER_SPEED OPUSDT: RSI filter blocked (rsi=53.8 above_sma=True regime=TRENDING) |
| 07:25:02 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:02 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:02 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=52.9 above_sma=True regime=MEAN_REVERTING) |
| 07:25:03 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:03 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:03 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=81.5 above_sma=False regime=MEAN_REVERTING) |
| 07:25:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=TRENDING) |
| 07:25:07 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 07:25:07 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 07:25:07 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 07:25:51 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |

---
*EOW Quant Engine V4.0 — 2026-05-09 07:25 UTC*