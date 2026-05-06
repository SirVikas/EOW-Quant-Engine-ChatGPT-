# EOW Quant Engine — Performance Report

**Generated:** 2026-05-06 01:05 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **514 trades** with a net **LOSS** of **-174.60 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $825.40 USDT |
| Net PnL | -174.5977 USDT |
| Win Rate | 33.3% |
| Profit Factor | 0.516 |
| Sharpe Ratio | -2.081 |
| Sortino Ratio | -1.980 |
| Calmar Ratio | -0.434 |
| Max Drawdown | 19.73% |
| Risk of Ruin | 100.00% |
| Total Fees | 79.6628 USDT |
| Total Slippage | 21.2966 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -73.6383 USDT (before all costs)
- **Fees deducted:** -79.6628 USDT
- **Slippage deducted:** -21.2966 USDT
- **Net PnL (bankable):** -174.5977 USDT

### 2.2 Trade Statistics

- Avg win: +1.0890 USDT
- Avg loss: -1.0520 USDT
- Profit factor: 0.516

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-17.5%** | **-2.08** | **-1.98** | **19.7%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 00:57:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:57:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:57:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=26.5 above_sma=False regime=TRENDING) |
| 00:57:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:57:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:57:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=68.5 above_sma=True regime=TRENDING) |
| 00:57:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:57:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:57:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2364.7500 rsi=56.6 |
| 00:58:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:58:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:58:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=79.7 above_sma=True regime=TRENDING) |
| 00:58:00 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:58:00 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:58:00 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=68.6 above_sma=True regime=TRENDING) |
| 00:58:07 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:58:07 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:58:07 | FILTER | ⚡ PAPER_SPEED bypass LTCUSDT: SLEEP_MODE(vol=27=9%_of_avg=318,min=10%[base=45%×0.20]) |
| 00:58:07 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=56.2600 rsi=47.7 |
| 00:58:58 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:58:58 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:58:58 | SIGNAL | ⚡ ALPHA TrendBreakout TONUSDT score=0.809 rr=5.00 |
| 00:58:58 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=81.1 above_sma=True regime=TRENDING) |
| 00:58:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:58:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:58:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2364.8100 rsi=61.5 |
| 00:58:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:58:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:58:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=64.0 above_sma=True regime=TRENDING) |
| 00:58:59 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:58:59 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:58:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=78.2 above_sma=True regime=TRENDING) |
| 00:58:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:58:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:58:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=75.9 above_sma=True regime=TRENDING) |
| 00:58:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:58:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:58:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=30.5 above_sma=False regime=TRENDING) |
| 00:59:02 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:02 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:02 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=68.6 above_sma=True regime=TRENDING) |
| 00:59:03 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:03 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:03 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=56.2500 rsi=48.8 |
| 00:59:58 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:58 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:58 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2364.6300 rsi=60.6 |
| 00:59:58 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:58 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:58 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=81030.0100 rsi=61.1 |
| 00:59:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:59 | SIGNAL | ⚡ ALPHA TrendBreakout TONUSDT score=0.751 rr=5.00 |
| 00:59:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=81.1 above_sma=True regime=TRENDING) |
| 00:59:59 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:59 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:59 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=75.0 above_sma=True regime=TRENDING) |
| 00:59:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=36.0 above_sma=False regime=TRENDING) |
| 00:59:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=76.3 above_sma=True regime=TRENDING) |
| 00:59:59 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:59 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:59 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=56.2500 rsi=50.0 |
| 00:59:59 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 00:59:59 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 00:59:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=76.5 above_sma=True regime=TRENDING) |
| 01:00:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:00:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:00:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81012.7500 rsi=61.7 |
| 01:00:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:00:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:00:59 | SIGNAL | ⚡ ALPHA TrendBreakout LUNCUSDT score=0.834 rr=4.00 |
| 01:00:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=27.9 above_sma=False regime=TRENDING) |
| 01:00:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:00:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:00:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=84.8 above_sma=True regime=TRENDING) |
| 01:01:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:01:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:01:00 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=63.9 above_sma=True regime=TRENDING) |
| 01:01:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:01:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:01:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2363.6500 rsi=60.8 |
| 01:01:01 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:01:01 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:01:01 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=79.4 above_sma=True regime=TRENDING) |
| 01:01:01 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:01:01 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:01:01 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=60.4 above_sma=False regime=MEAN_REVERTING) |
| 01:01:07 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:01:07 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:01:07 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=56.2300 rsi=50.0 |
| 01:02:00 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:00 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:00 | SIGNAL | ⚡ ALPHA TrendBreakout TONUSDT score=0.886 rr=4.00 |
| 01:02:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=92.9 above_sma=True regime=TRENDING) |
| 01:02:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:00 | SIGNAL | ⚡ ALPHA TrendBreakout LUNCUSDT score=0.787 rr=4.00 |
| 01:02:00 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=22.9 above_sma=False regime=TRENDING) |
| 01:02:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=71.2 above_sma=True regime=TRENDING) |
| 01:02:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81060.1800 rsi=70.9 |
| 01:02:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:02:01 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:01 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:01 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0210 rsi=64.2 |
| 01:02:01 | SIGNAL | 🔔 Signal SHORT TSTUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:02:02 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:02 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:02 | SIGNAL | ⚡ ALPHA TrendBreakout DOGSUSDT score=0.673 rr=4.00 |
| 01:02:02 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=87.2 above_sma=True regime=TRENDING) |
| 01:02:02 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:02 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:02 | FILTER | ⚡ PAPER_SPEED bypass LTCUSDT: SLEEP_MODE(vol=23=8%_of_avg=303,min=10%[base=45%×0.20]) |
| 01:02:02 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=56.2800 rsi=61.9 |
| 01:02:03 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:03 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:03 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=63.9 above_sma=True regime=TRENDING) |
| 01:02:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=73.7 above_sma=True regime=TRENDING) |
| 01:02:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=36.4 above_sma=False regime=TRENDING) |
| 01:02:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=52.2 above_sma=False regime=MEAN_REVERTING) |
| 01:02:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:02:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:02:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81073.5900 rsi=72.7 |
| 01:02:59 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:03:01 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:03:01 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:03:01 | SIGNAL | ⚡ ALPHA TrendBreakout DOGSUSDT score=0.622 rr=4.00 |
| 01:03:01 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=88.6 above_sma=True regime=TRENDING) |
| 01:03:03 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:03:03 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:03:03 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=56.3100 rsi=67.4 |
| 01:03:10 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:03:10 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:03:10 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=65.6 above_sma=True regime=TRENDING) |
| 01:03:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:03:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:03:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81120.0000 rsi=81.3 |
| 01:03:59 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:03:59 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:03:59 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:03:59 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=56.3200 rsi=73.2 |
| 01:03:59 | SIGNAL | 🔔 Signal SHORT LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:03:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:03:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:03:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=92.7 above_sma=True regime=TRENDING) |
| 01:03:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:03:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:03:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=76.7 above_sma=True regime=TRENDING) |
| 01:03:59 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:03:59 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:03:59 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: LONG entry=0.3202 rsi=60.9 |
| 01:03:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:03:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:03:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=34.5 above_sma=False regime=TRENDING) |
| 01:04:00 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:00 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:00 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=88.4 above_sma=True regime=TRENDING) |
| 01:04:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=51.3 above_sma=False regime=MEAN_REVERTING) |
| 01:04:58 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:58 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:58 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=93.1 above_sma=True regime=TRENDING) |
| 01:04:58 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:58 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:58 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=45.7 above_sma=False regime=MEAN_REVERTING) |
| 01:04:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=33.0 above_sma=False regime=TRENDING) |
| 01:04:59 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:04:59 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:04:59 | SIGNAL | ⚡ ALPHA TrendBreakout DOGSUSDT score=0.731 rr=4.00 |
| 01:04:59 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=89.8 above_sma=True regime=TRENDING) |
| 01:05:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:05:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:05:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81148.3000 rsi=77.2 |
| 01:05:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:05:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:05:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:05:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=68.4 above_sma=True regime=TRENDING) |
| 01:05:02 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:05:02 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:05:02 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: LONG entry=0.3201 rsi=58.2 |
| 01:05:02 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:05:02 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.400 |
| 01:05:02 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: SHORT entry=56.3300 rsi=68.6 |
| 01:05:02 | SIGNAL | 🔔 Signal SHORT LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |

---
*EOW Quant Engine V4.0 — 2026-05-06 01:05 UTC*