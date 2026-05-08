# EOW Quant Engine — Performance Report

**Generated:** 2026-05-06 06:56 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **531 trades** with a net **LOSS** of **-180.42 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $819.58 USDT |
| Net PnL | -180.4189 USDT |
| Win Rate | 32.8% |
| Profit Factor | 0.512 |
| Sharpe Ratio | -2.113 |
| Sortino Ratio | -2.018 |
| Calmar Ratio | -0.434 |
| Max Drawdown | 19.74% |
| Risk of Ruin | 100.00% |
| Total Fees | 81.9021 USDT |
| Total Slippage | 22.9760 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -75.5408 USDT (before all costs)
- **Fees deducted:** -81.9021 USDT
- **Slippage deducted:** -22.9760 USDT
- **Net PnL (bankable):** -180.4189 USDT

### 2.2 Trade Statistics

- Avg win: +1.0889 USDT
- Avg loss: -1.0361 USDT
- Profit factor: 0.512

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-18.0%** | **-2.11** | **-2.02** | **19.7%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 06:42:02 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:42:02 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:42:02 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3920 rsi=61.5 |
| 06:42:05 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:42:05 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:42:05 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=66.7 above_sma=False regime=MEAN_REVERTING) |
| 06:42:05 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:42:05 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:42:05 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0192 rsi=44.1 |
| 06:43:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:43:58 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:43:58 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=62.8 above_sma=True regime=TRENDING) |
| 06:43:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:43:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:43:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=73.9 above_sma=True regime=TRENDING) |
| 06:43:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:43:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:43:59 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=52.8 |
| 06:43:59 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:43:59 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:43:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=48.1 above_sma=True regime=MEAN_REVERTING) |
| 06:44:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:44:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:44:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=36.7 above_sma=False regime=TRENDING) |
| 06:44:01 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:44:01 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:44:01 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=70.9 above_sma=True regime=TRENDING) |
| 06:44:01 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:44:01 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:44:01 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=80.6 above_sma=True regime=TRENDING) |
| 06:44:01 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:44:01 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:44:01 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 06:44:02 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:44:02 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:44:02 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: SHORT entry=2.3930 rsi=61.5 |
| 06:44:02 | SIGNAL | 🔔 Signal SHORT TRUMPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:45:16 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:45:16 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:45:16 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=68.4 above_sma=True regime=TRENDING) |
| 06:45:16 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:45:16 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:45:16 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=67.8 above_sma=True regime=TRENDING) |
| 06:45:16 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:45:16 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:45:16 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=79.8 above_sma=True regime=TRENDING) |
| 06:45:17 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:45:17 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:45:17 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=43.1 above_sma=False regime=MEAN_REVERTING) |
| 06:45:18 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:45:18 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:45:18 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=75.7 above_sma=True regime=TRENDING) |
| 06:45:18 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:45:18 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:45:18 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=53.1 |
| 06:45:18 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:45:18 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:45:18 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=72.7 above_sma=True regime=TRENDING) |
| 06:45:19 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:45:19 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:45:19 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=48.0 above_sma=False regime=MEAN_REVERTING) |
| 06:45:21 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:45:21 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:45:21 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=47.1 above_sma=True regime=MEAN_REVERTING) |
| 06:47:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:47:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:47:00 | FILTER | ⚡ PAPER_SPEED bypass LUNCUSDT: SLEEP_MODE(vol=36516685=9%_of_avg=399533046,min=10%[base=45%×0.20]) |
| 06:47:00 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=52.5 above_sma=False regime=MEAN_REVERTING) |
| 06:47:05 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:47:05 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:47:05 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=65.4 above_sma=True regime=TRENDING) |
| 06:47:14 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:47:14 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:47:15 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=48.0 above_sma=False regime=MEAN_REVERTING) |
| 06:47:16 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:47:16 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:47:17 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=40.8 above_sma=True regime=MEAN_REVERTING) |
| 06:47:17 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:47:17 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:47:17 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=68.5 above_sma=True regime=TRENDING) |
| 06:47:17 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:47:17 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:47:17 | SIGNAL | ⚡ ALPHA TrendBreakout TRUMPUSDT score=0.673 rr=5.00 |
| 06:47:17 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=76.9 above_sma=True regime=TRENDING) |
| 06:47:17 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:47:17 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:47:17 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=71.4 above_sma=True regime=TRENDING) |
| 06:47:18 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:47:18 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:47:18 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=42.0 above_sma=False regime=MEAN_REVERTING) |
| 06:47:19 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:47:19 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:47:19 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=73.5 above_sma=True regime=TRENDING) |
| 06:47:19 | SYSTEM | ⚡ Mode switched to PAPER |
| 06:49:04 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:49:04 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:49:04 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=73.8 above_sma=True regime=TRENDING) |
| 06:49:04 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:49:04 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:49:04 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=45.6 |
| 06:49:04 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:49:04 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:49:04 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=69.6 above_sma=True regime=TRENDING) |
| 06:49:04 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:49:04 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:49:04 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=69.0 above_sma=True regime=TRENDING) |
| 06:49:10 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:49:10 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:49:10 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: LONG entry=2.7140 rsi=34.5 |
| 06:49:10 | SIGNAL | 🔔 Signal LONG ICPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:49:11 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:49:11 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:49:11 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=63.3 above_sma=True regime=TRENDING) |
| 06:49:11 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:49:11 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:49:11 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=75.0 above_sma=True regime=TRENDING) |
| 06:49:20 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:49:20 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:49:20 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: LONG entry=0.0192 rsi=29.3 |
| 06:49:20 | SIGNAL | 🔔 Signal LONG TSTUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:51:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:51:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:51:01 | SIGNAL | ⚡ ALPHA TrendBreakout LUNCUSDT score=0.793 rr=4.00 |
| 06:51:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=27.3 above_sma=False regime=TRENDING) |
| 06:51:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:51:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:51:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=68.2 above_sma=True regime=TRENDING) |
| 06:51:01 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:51:01 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:51:01 | FILTER | ⚡ PAPER_SPEED bypass TSTUSDT: SLEEP_MODE(vol=652=0%_of_avg=158584,min=10%[base=45%×0.20]) |
| 06:51:01 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: LONG entry=0.0192 rsi=23.7 |
| 06:51:01 | SIGNAL | 🔔 Signal LONG TSTUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:51:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:51:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:51:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=67.4 above_sma=True regime=TRENDING) |
| 06:51:06 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:51:06 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:51:06 | SIGNAL | ⚡ PAPER_SPEED fallback ICPUSDT: LONG entry=2.7160 rsi=37.9 |
| 06:51:06 | SIGNAL | 🔔 Signal LONG ICPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:51:06 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:51:06 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:51:06 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=70.4 above_sma=True regime=TRENDING) |
| 06:51:06 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:51:06 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:51:06 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=75.0 above_sma=True regime=TRENDING) |
| 06:51:11 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:51:11 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:51:11 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.9300 rsi=56.0 |
| 06:52:11 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:52:11 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:52:11 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=2.1340 rsi=44.6 |
| 06:52:11 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:52:11 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:52:11 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=68.7 above_sma=True regime=TRENDING) |
| 06:52:11 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:52:11 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:52:11 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=29.8 above_sma=False regime=TRENDING) |
| 06:52:13 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:52:13 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:52:13 | SIGNAL | ⚡ ALPHA TrendBreakout TSTUSDT score=0.692 rr=5.00 |
| 06:52:13 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=19.6 above_sma=False regime=TRENDING) |
| 06:52:18 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:52:18 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:52:18 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=63.2 above_sma=True regime=TRENDING) |
| 06:52:23 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:52:24 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:52:24 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=40.0 above_sma=False regime=MEAN_REVERTING) |
| 06:53:36 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:53:36 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:53:36 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=56.9000 rsi=58.3 |
| 06:53:42 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:53:43 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:53:43 | FILTER | ⚡ PAPER_SPEED TRUMPUSDT: RSI filter blocked (rsi=72.7 above_sma=True regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=25.4 above_sma=False regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.1290 rsi=45.4 |
| 06:55:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | SIGNAL | ⚡ ALPHA TrendBreakout TSTUSDT score=0.662 rr=5.00 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=14.8 above_sma=False regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=69.2 above_sma=True regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=64.5 above_sma=True regime=TRENDING) |
| 06:55:59 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:55:59 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:55:59 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=48.3 above_sma=False regime=MEAN_REVERTING) |
| 06:56:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:56:02 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:56:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2368.3400 rsi=60.3 |
| 06:56:11 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 06:56:11 | SIGNAL | 📈 STREAK TRUMPUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 06:56:11 | FILTER | ⚡ PAPER_SPEED bypass TRUMPUSDT: SLEEP_MODE(vol=59=9%_of_avg=669,min=10%[base=45%×0.20]) |
| 06:56:11 | SIGNAL | ⚡ PAPER_SPEED fallback TRUMPUSDT: LONG entry=2.3920 rsi=57.1 |
| 06:56:35 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |

---
*EOW Quant Engine V4.0 — 2026-05-06 06:56 UTC*