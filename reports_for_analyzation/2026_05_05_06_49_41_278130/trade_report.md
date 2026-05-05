# EOW Quant Engine — Performance Report

**Generated:** 2026-05-05 01:17 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **473 trades** with a net **LOSS** of **-175.95 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $824.05 USDT |
| Net PnL | -175.9519 USDT |
| Win Rate | 34.5% |
| Profit Factor | 0.489 |
| Sharpe Ratio | -2.229 |
| Sortino Ratio | -2.066 |
| Calmar Ratio | -0.485 |
| Max Drawdown | 19.31% |
| Risk of Ruin | 100.00% |
| Total Fees | 74.7825 USDT |
| Total Slippage | 17.6363 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -83.5331 USDT (before all costs)
- **Fees deducted:** -74.7825 USDT
- **Slippage deducted:** -17.6363 USDT
- **Net PnL (bankable):** -175.9519 USDT

### 2.2 Trade Statistics

- Avg win: +1.0341 USDT
- Avg loss: -1.1113 USDT
- Profit factor: 0.489

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-17.6%** | **-2.23** | **-2.07** | **19.3%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 01:07:00 | SIGNAL | ⚡ PAPER_SPEED fallback DASHUSDT: LONG entry=47.0300 rsi=39.3 |
| 01:07:00 | SIGNAL | 🔔 Signal LONG DASHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:07:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:07:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:07:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=53.0 above_sma=True regime=MEAN_REVERTING) |
| 01:07:20 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:07:20 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:07:20 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0538 rsi=42.9 |
| 01:07:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:07:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:07:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=48.6 above_sma=True regime=MEAN_REVERTING) |
| 01:07:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:07:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:07:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=45.0 above_sma=True regime=MEAN_REVERTING) |
| 01:07:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:07:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:07:59 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0259 rsi=50.4 |
| 01:07:59 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:07:59 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:07:59 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=43.4 above_sma=False regime=MEAN_REVERTING) |
| 01:08:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:08:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:08:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=64.6 |
| 01:08:00 | SIGNAL | 🔔 Signal SHORT LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:08:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:08:01 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:08:01 | FILTER | ⚡ PAPER_SPEED bypass BIOUSDT: SLEEP_MODE(vol=20763=7%_of_avg=309669,min=10%[base=45%×0.20]) |
| 01:08:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=36.8 above_sma=False regime=TRENDING) |
| 01:08:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:08:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:08:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=55.0 above_sma=True regime=MEAN_REVERTING) |
| 01:08:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:08:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:08:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=52.8 above_sma=False regime=MEAN_REVERTING) |
| 01:08:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:08:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:08:59 | SIGNAL | ⚡ ALPHA PullbackEntry TSTUSDT score=0.538 rr=4.00 |
| 01:08:59 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0259 rsi=56.8 |
| 01:09:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:09:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:09:00 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=47.1 above_sma=False regime=MEAN_REVERTING) |
| 01:09:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:09:00 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:09:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=36.8 above_sma=False regime=TRENDING) |
| 01:09:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:09:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:09:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=52.5 above_sma=True regime=MEAN_REVERTING) |
| 01:09:59 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:09:59 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:09:59 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0538 rsi=50.0 |
| 01:09:59 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:09:59 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:09:59 | FILTER | ⚡ PAPER_SPEED bypass DASHUSDT: SLEEP_MODE(vol=38=6%_of_avg=615,min=10%[base=45%×0.20]) |
| 01:09:59 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=52.1 above_sma=False regime=MEAN_REVERTING) |
| 01:09:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:09:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:09:59 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=56.3 above_sma=True regime=MEAN_REVERTING) |
| 01:09:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:09:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:09:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=56.7 above_sma=True regime=MEAN_REVERTING) |
| 01:10:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:10:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:10:00 | SIGNAL | ⚡ ALPHA PullbackEntry TSTUSDT score=0.514 rr=4.00 |
| 01:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0259 rsi=59.7 |
| 01:10:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:10:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=80209.6300 rsi=61.2 |
| 01:10:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:10:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:10:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=69.6 above_sma=True regime=TRENDING) |
| 01:10:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:10:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:10:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2360.5500 rsi=64.6 |
| 01:10:59 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:11:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:11:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:11:00 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0257 rsi=54.1 |
| 01:11:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:11:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:11:00 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=55.6 above_sma=True regime=MEAN_REVERTING) |
| 01:11:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:11:00 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:11:00 | FILTER | ⚡ PAPER_SPEED bypass BIOUSDT: SLEEP_MODE(vol=7140=3%_of_avg=285117,min=10%[base=45%×0.20]) |
| 01:11:00 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0536 rsi=45.0 |
| 01:11:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:11:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:11:01 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=61.1 |
| 01:11:01 | SIGNAL | 🔔 Signal SHORT LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:11:59 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:11:59 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:11:59 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=47.0 above_sma=False regime=MEAN_REVERTING) |
| 01:11:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:11:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:11:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=80239.8600 rsi=61.8 |
| 01:11:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:11:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:11:59 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0258 rsi=59.9 |
| 01:11:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:11:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:11:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=57.8 above_sma=True regime=MEAN_REVERTING) |
| 01:12:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:12:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:12:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=55.9 |
| 01:12:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:12:01 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:12:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0537 rsi=42.1 |
| 01:12:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:12:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:12:59 | SIGNAL | ⚡ PAPER_SPEED fallback TSTUSDT: SHORT entry=0.0258 rsi=60.1 |
| 01:12:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:12:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:12:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=64.4 above_sma=True regime=TRENDING) |
| 01:12:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:12:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:12:59 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=48.7 |
| 01:12:59 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:12:59 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:12:59 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=40.9 above_sma=False regime=MEAN_REVERTING) |
| 01:13:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:13:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:13:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=62.3 above_sma=True regime=TRENDING) |
| 01:13:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:13:00 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:13:00 | SIGNAL | ⚡ ALPHA TrendBreakout BIOUSDT score=0.761 rr=4.00 |
| 01:13:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=31.6 above_sma=False regime=TRENDING) |
| 01:13:59 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:13:59 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:13:59 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=39.4 |
| 01:13:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:13:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:13:59 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=80227.0700 rsi=59.3 |
| 01:13:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:13:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:13:59 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2360.2200 rsi=57.2 |
| 01:13:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:13:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:13:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=60.7 above_sma=False regime=MEAN_REVERTING) |
| 01:13:59 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:13:59 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:14:00 | SIGNAL | ⚡ ALPHA TrendBreakout BIOUSDT score=0.718 rr=4.00 |
| 01:14:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=30.0 above_sma=False regime=TRENDING) |
| 01:14:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:14:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:14:00 | SIGNAL | ⚡ PAPER_SPEED fallback DASHUSDT: LONG entry=46.9600 rsi=34.5 |
| 01:14:00 | SIGNAL | 🔔 Signal LONG DASHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:14:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:14:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:14:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 01:14:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:14:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:14:59 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=63.2 above_sma=True regime=TRENDING) |
| 01:15:00 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:15:00 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:15:00 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=60.9 above_sma=False regime=MEAN_REVERTING) |
| 01:15:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:15:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:15:00 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=36.2 above_sma=False regime=TRENDING) |
| 01:15:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:15:00 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:15:00 | SIGNAL | ⚡ PAPER_SPEED fallback DASHUSDT: LONG entry=46.9500 rsi=36.1 |
| 01:15:00 | SIGNAL | 🔔 Signal LONG DASHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:15:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:15:00 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:15:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=30.0 above_sma=False regime=TRENDING) |
| 01:15:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:15:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:15:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=72.6 above_sma=True regime=TRENDING) |
| 01:15:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:15:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:15:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=60.8 above_sma=False regime=MEAN_REVERTING) |
| 01:16:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:16:00 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:16:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=38.2 |
| 01:16:00 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:16:01 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:16:01 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=43.5 above_sma=False regime=MEAN_REVERTING) |
| 01:16:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:16:01 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:16:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=26.3 above_sma=False regime=TRENDING) |
| 01:16:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:16:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:16:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=72.0 above_sma=True regime=TRENDING) |
| 01:16:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:16:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:16:59 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=72.7 above_sma=True regime=TRENDING) |
| 01:16:59 | SIGNAL | ⚡ DTP DASHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:16:59 | SIGNAL | 📈 STREAK DASHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:16:59 | FILTER | ⚡ PAPER_SPEED DASHUSDT: RSI filter blocked (rsi=56.2 above_sma=False regime=MEAN_REVERTING) |
| 01:16:59 | SIGNAL | ⚡ DTP TSTUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:16:59 | SIGNAL | 📈 STREAK TSTUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:16:59 | FILTER | ⚡ PAPER_SPEED TSTUSDT: RSI filter blocked (rsi=53.5 above_sma=False regime=MEAN_REVERTING) |
| 01:16:59 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:16:59 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:16:59 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=30.0 above_sma=False regime=TRENDING) |
| 01:17:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:17:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:17:00 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=72.8 above_sma=True regime=TRENDING) |
| 01:17:02 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 01:17:02 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.560 |
| 01:17:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=37.0 above_sma=False regime=TRENDING) |

---
*EOW Quant Engine V4.0 — 2026-05-05 01:17 UTC*