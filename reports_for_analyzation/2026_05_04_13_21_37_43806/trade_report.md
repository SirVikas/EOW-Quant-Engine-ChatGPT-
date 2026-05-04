# EOW Quant Engine — Performance Report

**Generated:** 2026-05-04 07:49 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **458 trades** with a net **LOSS** of **-167.03 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $832.97 USDT |
| Net PnL | -167.0325 USDT |
| Win Rate | 35.1% |
| Profit Factor | 0.500 |
| Sharpe Ratio | -2.154 |
| Sortino Ratio | -1.988 |
| Calmar Ratio | -0.480 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Total Fees | 73.1255 USDT |
| Total Slippage | 16.3936 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -77.5134 USDT (before all costs)
- **Fees deducted:** -73.1255 USDT
- **Slippage deducted:** -16.3936 USDT
- **Net PnL (bankable):** -167.0325 USDT

### 2.2 Trade Statistics

- Avg win: +1.0356 USDT
- Avg loss: -1.1238 USDT
- Profit factor: 0.500

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-16.7%** | **-2.15** | **-1.99** | **19.2%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 07:41:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=22.2 above_sma=False regime=TRENDING) |
| 07:41:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=27.5 above_sma=False regime=TRENDING) |
| 07:41:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=52.2 above_sma=True regime=MEAN_REVERTING) |
| 07:41:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=65.0 above_sma=True regime=TRENDING) |
| 07:41:01 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:01 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:01 | SIGNAL | ⚡ PAPER_SPEED fallback DASHUSDT: SHORT entry=47.9100 rsi=40.5 |
| 07:41:02 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:02 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:03 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=MEAN_REVERTING) |
| 07:41:09 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:09 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:09 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0601 rsi=70.0 |
| 07:41:09 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:41:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=25.6 above_sma=False regime=TRENDING) |
| 07:41:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=17.3 above_sma=False regime=TRENDING) |
| 07:41:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:41:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:41:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=67.1 above_sma=True regime=TRENDING) |
| 07:42:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:42:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:42:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=55.7 above_sma=True regime=MEAN_REVERTING) |
| 07:42:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:42:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:42:00 | SIGNAL | ⚡ ALPHA PullbackEntry DASHUSDT score=0.548 rr=5.00 |
| 07:42:00 | SIGNAL | ⚡ PAPER_SPEED fallback DASHUSDT: SHORT entry=48.0600 rsi=59.5 |
| 07:42:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:42:00 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:42:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=70.0 above_sma=True regime=TRENDING) |
| 07:42:11 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:42:11 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:42:11 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=37.5 above_sma=False regime=MEAN_REVERTING) |
| 07:42:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:42:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:42:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=29.7 above_sma=False regime=TRENDING) |
| 07:42:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:42:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:42:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=21.5 above_sma=False regime=TRENDING) |
| 07:42:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:42:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:43:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=54.8 above_sma=True regime=MEAN_REVERTING) |
| 07:43:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:43:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:43:00 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=62.6 above_sma=True regime=TRENDING) |
| 07:43:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:43:00 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:43:00 | SIGNAL | ⚡ ALPHA TrendBreakout BIOUSDT score=0.762 rr=5.00 |
| 07:43:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=78.6 above_sma=True regime=TRENDING) |
| 07:43:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:43:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:43:00 | SIGNAL | ⚡ ALPHA PullbackEntry DASHUSDT score=0.490 rr=5.00 |
| 07:43:00 | SIGNAL | ⚡ PAPER_SPEED fallback DASHUSDT: SHORT entry=48.1600 rsi=58.3 |
| 07:43:10 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:43:10 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:43:10 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 07:43:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:43:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:43:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=31.1 above_sma=False regime=TRENDING) |
| 07:44:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=61.8 above_sma=True regime=MEAN_REVERTING) |
| 07:44:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=20.0 above_sma=False regime=TRENDING) |
| 07:44:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:01 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=56.8 |
| 07:44:02 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:02 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:02 | SIGNAL | ⚡ PAPER_SPEED fallback DASHUSDT: SHORT entry=48.1600 rsi=63.0 |
| 07:44:03 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:03 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:03 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=72.7 above_sma=True regime=TRENDING) |
| 07:44:03 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:03 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:03 | FILTER | ⚡ PAPER_SPEED bypass PARTIUSDT: SLEEP_MODE(vol=2006=3%_of_avg=76118,min=10%[base=45%×0.20]) |
| 07:44:03 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=53.3 above_sma=False regime=MEAN_REVERTING) |
| 07:44:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=79856.9600 rsi=51.1 |
| 07:44:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:59 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=53.8 |
| 07:44:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2368.0400 rsi=49.4 |
| 07:44:59 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:44:59 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:44:59 | SIGNAL | ⚡ ALPHA PullbackEntry DASHUSDT score=0.544 rr=5.00 |
| 07:44:59 | SIGNAL | ⚡ PAPER_SPEED fallback DASHUSDT: SHORT entry=48.1800 rsi=56.5 |
| 07:45:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:45:00 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:45:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=76.9 above_sma=True regime=TRENDING) |
| 07:45:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:45:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:45:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=48.1 above_sma=False regime=MEAN_REVERTING) |
| 07:45:07 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:45:07 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:45:07 | FILTER | ⚡ PAPER_SPEED bypass PARTIUSDT: SLEEP_MODE(vol=6401=9%_of_avg=72717,min=10%[base=45%×0.20]) |
| 07:45:07 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=56.2 above_sma=False regime=MEAN_REVERTING) |
| 07:45:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:45:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:45:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=79824.0100 rsi=44.2 |
| 07:45:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:45:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:45:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2366.8600 rsi=45.0 |
| 07:46:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:46:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:46:00 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=57.8 above_sma=False regime=MEAN_REVERTING) |
| 07:46:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:46:00 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:46:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=78.6 above_sma=True regime=TRENDING) |
| 07:46:01 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:46:01 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:46:01 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 07:46:01 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:46:01 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:46:01 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=54.4 above_sma=True regime=MEAN_REVERTING) |
| 07:46:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:46:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:46:01 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=47.6 |
| 07:46:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:46:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:46:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=79871.4800 rsi=54.2 |
| 07:46:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:46:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:46:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2369.0100 rsi=56.0 |
| 07:46:59 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:46:59 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:46:59 | SIGNAL | ⚡ ALPHA TrendBreakout DASHUSDT score=0.683 rr=5.00 |
| 07:46:59 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=68.5 above_sma=True regime=TRENDING) |
| 07:47:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:47:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:47:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=59.7 above_sma=True regime=MEAN_REVERTING) |
| 07:47:02 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:47:02 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:47:02 | SIGNAL | ⚡ ALPHA PullbackEntry LUNCUSDT score=0.541 rr=5.00 |
| 07:47:02 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=36.2 |
| 07:47:03 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:47:03 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:47:03 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=73.3 above_sma=True regime=TRENDING) |
| 07:47:45 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:47:45 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:47:45 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=60.0 above_sma=True regime=MEAN_REVERTING) |
| 07:47:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:47:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:47:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=79899.7100 rsi=59.8 |
| 07:47:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:47:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:47:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2369.5400 rsi=55.9 |
| 07:48:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:48:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:48:00 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=74.2 above_sma=True regime=TRENDING) |
| 07:48:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:48:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:48:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=35.5 |
| 07:48:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:48:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:48:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=62.2 above_sma=True regime=MEAN_REVERTING) |
| 07:48:02 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:48:02 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:48:02 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=76.5 above_sma=True regime=TRENDING) |
| 07:48:05 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:48:05 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:48:05 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |
| 07:49:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=79876.4600 rsi=61.2 |
| 07:49:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | SIGNAL | ⚡ ALPHA TrendBreakout DASHUSDT score=0.658 rr=5.00 |
| 07:49:00 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=75.2 above_sma=True regime=TRENDING) |
| 07:49:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2368.4500 rsi=55.4 |
| 07:49:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | SIGNAL | ⚡ ALPHA TrendBreakout LUNCUSDT score=0.632 rr=5.00 |
| 07:49:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=32.6 |
| 07:49:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=59.6 above_sma=True regime=MEAN_REVERTING) |
| 07:49:06 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:06 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:06 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0604 rsi=57.9 |
| 07:49:42 | SIGNAL | ⚡ DTP PARTIUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 07:49:42 | SIGNAL | 📈 STREAK PARTIUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.560 |
| 07:49:42 | FILTER | ⚡ PAPER_SPEED PARTIUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=MEAN_REVERTING) |

---
*EOW Quant Engine V4.0 — 2026-05-04 07:49 UTC*