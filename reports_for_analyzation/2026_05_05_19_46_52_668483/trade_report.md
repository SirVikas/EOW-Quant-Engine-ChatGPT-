# EOW Quant Engine — Performance Report

**Generated:** 2026-05-05 14:15 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **509 trades** with a net **LOSS** of **-171.25 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $828.75 USDT |
| Net PnL | -171.2473 USDT |
| Win Rate | 33.6% |
| Profit Factor | 0.521 |
| Sharpe Ratio | -2.051 |
| Sortino Ratio | -1.948 |
| Calmar Ratio | -0.430 |
| Max Drawdown | 19.73% |
| Risk of Ruin | 100.00% |
| Total Fees | 79.0662 USDT |
| Total Slippage | 20.8491 USDT |
| Deployability | 45/100 (NOT READY) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -71.3320 USDT (before all costs)
- **Fees deducted:** -79.0662 USDT
- **Slippage deducted:** -20.8491 USDT
- **Net PnL (bankable):** -171.2473 USDT

### 2.2 Trade Statistics

- Avg win: +1.0890 USDT
- Avg loss: -1.0576 USDT
- Profit factor: 0.521

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-17.1%** | **-2.05** | **-1.95** | **19.7%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 14:08:07 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:08:07 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=34.8 above_sma=False regime=TRENDING) |
| 14:08:07 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:08:07 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:08:07 | SIGNAL | ⚡ PAPER_SPEED fallback DOGSUSDT: SHORT entry=0.0001 rsi=47.2 |
| 14:08:08 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:08:08 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:08:08 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=46.5 above_sma=False regime=MEAN_REVERTING) |
| 14:08:08 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:08:08 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:08:08 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2386.6600 rsi=37.5 |
| 14:08:08 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:08:09 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:08:09 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:08:09 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=49.5 above_sma=True regime=MEAN_REVERTING) |
| 14:08:10 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:08:10 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:08:10 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=68.1 above_sma=True regime=TRENDING) |
| 14:08:11 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:08:11 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:08:11 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0534 rsi=69.2 |
| 14:08:11 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:08:12 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:08:12 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:08:12 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=29.4 above_sma=False regime=TRENDING) |
| 14:09:05 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:05 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:05 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81294.7400 rsi=44.7 |
| 14:09:05 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:05 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:05 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=51.0 above_sma=False regime=MEAN_REVERTING) |
| 14:09:06 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:06 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:06 | SIGNAL | ⚡ PAPER_SPEED fallback DOGSUSDT: SHORT entry=0.0001 rsi=42.6 |
| 14:09:06 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:06 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:06 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=32.9 above_sma=False regime=TRENDING) |
| 14:09:06 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:06 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:06 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=1.8090 rsi=29.7 |
| 14:09:06 | SIGNAL | 🔔 Signal LONG TONUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:09:06 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:06 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:06 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=62.9 |
| 14:09:06 | SIGNAL | 🔔 Signal SHORT LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:09:06 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:06 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:06 | SIGNAL | ⚡ ALPHA TrendBreakout ONDOUSDT score=0.686 rr=5.00 |
| 14:09:06 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=77.9 above_sma=True regime=TRENDING) |
| 14:09:07 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:07 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:07 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=55.7500 rsi=38.5 |
| 14:09:07 | SIGNAL | 🔔 Signal LONG LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:09:10 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:10 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:10 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=57.1 above_sma=False regime=MEAN_REVERTING) |
| 14:09:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=29.6 above_sma=False regime=TRENDING) |
| 14:09:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=56.8 above_sma=False regime=MEAN_REVERTING) |
| 14:09:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81268.0000 rsi=48.5 |
| 14:09:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:59 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=23.5 above_sma=False regime=TRENDING) |
| 14:09:59 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:59 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:59 | SIGNAL | ⚡ PAPER_SPEED fallback DOGSUSDT: SHORT entry=0.0001 rsi=49.1 |
| 14:09:59 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:09:59 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:09:59 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=89.4 above_sma=True regime=TRENDING) |
| 14:10:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:10:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:10:00 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=58.6 above_sma=True regime=MEAN_REVERTING) |
| 14:10:05 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:10:05 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:10:05 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=MEAN_REVERTING) |
| 14:10:05 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:10:05 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:10:05 | FILTER | ⚡ PAPER_SPEED LTCUSDT: RSI filter blocked (rsi=47.6 above_sma=False regime=MEAN_REVERTING) |
| 14:11:02 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:11:02 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:11:02 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81256.4600 rsi=50.5 |
| 14:11:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:11:02 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:11:02 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=55.5 above_sma=False regime=MEAN_REVERTING) |
| 14:11:02 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:11:02 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:11:02 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=25.7 above_sma=False regime=TRENDING) |
| 14:11:02 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:11:02 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:11:02 | SIGNAL | ⚡ PAPER_SPEED fallback DOGSUSDT: SHORT entry=0.0001 rsi=44.8 |
| 14:11:03 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:11:03 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:11:03 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=47.1 above_sma=False regime=MEAN_REVERTING) |
| 14:11:03 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:11:03 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:11:03 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=55.7000 rsi=40.0 |
| 14:11:03 | SIGNAL | 🔔 Signal LONG LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:11:03 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:11:03 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:11:03 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=28.4 above_sma=False regime=TRENDING) |
| 14:11:05 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:11:05 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:11:05 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: SHORT entry=0.3230 rsi=88.7 |
| 14:11:05 | SIGNAL | 🔔 Signal SHORT ONDOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:11:10 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:11:10 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:11:10 | FILTER | ⚡ PAPER_SPEED bypass BIOUSDT: SLEEP_MODE(vol=11965=6%_of_avg=197198,min=10%[base=45%×0.20]) |
| 14:11:10 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0533 rsi=64.3 |
| 14:11:10 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:12:10 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:12:10 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:12:10 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81249.4500 rsi=42.2 |
| 14:12:10 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:12:10 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:12:10 | SIGNAL | ⚡ ALPHA TrendBreakout TONUSDT score=0.696 rr=4.00 |
| 14:12:10 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=22.0 above_sma=False regime=TRENDING) |
| 14:12:10 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:12:10 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:12:10 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=37.2 |
| 14:12:10 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:12:10 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:12:10 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:12:10 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=47.1 above_sma=False regime=MEAN_REVERTING) |
| 14:12:10 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:12:10 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:12:10 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=55.6900 rsi=23.8 |
| 14:12:10 | SIGNAL | 🔔 Signal LONG LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:12:11 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:12:11 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:12:11 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: SHORT entry=0.3219 rsi=75.0 |
| 14:12:11 | SIGNAL | 🔔 Signal SHORT ONDOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:12:11 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:12:11 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:12:11 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: LONG entry=0.0214 rsi=36.0 |
| 14:12:11 | SIGNAL | 🔔 Signal LONG TSTUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:12:11 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:12:11 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:12:11 | SIGNAL | ⚡ ALPHA TrendBreakout DOGSUSDT score=0.810 rr=4.00 |
| 14:12:11 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=24.6 above_sma=False regime=TRENDING) |
| 14:12:27 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:12:27 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:12:27 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0533 rsi=61.5 |
| 14:12:27 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:13:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:13:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:13:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=28.1 above_sma=False regime=TRENDING) |
| 14:13:03 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:13:03 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:13:03 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=55.7300 rsi=30.4 |
| 14:13:03 | SIGNAL | 🔔 Signal LONG LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:13:03 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:13:03 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:13:03 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=39.4 |
| 14:13:03 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:13:03 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:13:03 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:13:03 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81327.0500 rsi=46.5 |
| 14:13:03 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:13:03 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:13:03 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=24.6 above_sma=False regime=TRENDING) |
| 14:13:04 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:13:04 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:13:04 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=49.5 above_sma=False regime=MEAN_REVERTING) |
| 14:13:05 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:13:05 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:13:05 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=74.6 above_sma=True regime=TRENDING) |
| 14:13:06 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:13:06 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:13:06 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=53.8 above_sma=False regime=MEAN_REVERTING) |
| 14:13:07 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:13:07 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:13:07 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: LONG entry=0.0214 rsi=37.8 |
| 14:13:07 | SIGNAL | 🔔 Signal LONG TSTUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:14:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:14:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:14:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=43.4 above_sma=False regime=MEAN_REVERTING) |
| 14:15:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:15:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:15:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=43.4 above_sma=False regime=MEAN_REVERTING) |
| 14:15:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:15:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:15:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81233.0900 rsi=42.9 |
| 14:15:04 | SIGNAL | ⚡ DTP DOGSUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:15:04 | SIGNAL | 📈 STREAK DOGSUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:15:04 | FILTER | ⚡ PAPER_SPEED DOGSUSDT: RSI filter blocked (rsi=23.4 above_sma=False regime=TRENDING) |
| 14:15:07 | SIGNAL | ⚡ DTP LTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:15:07 | SIGNAL | 📈 STREAK LTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:15:07 | SIGNAL | ⚡ PAPER_SPEED fallback LTCUSDT: LONG entry=55.6700 rsi=26.9 |
| 14:15:07 | SIGNAL | 🔔 Signal LONG LTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:15:07 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:15:07 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:15:07 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=25.0 above_sma=False regime=TRENDING) |
| 14:15:08 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 14:15:08 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 14:15:08 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: LONG entry=0.3207 rsi=57.8 |

---
*EOW Quant Engine V4.0 — 2026-05-05 14:15 UTC*