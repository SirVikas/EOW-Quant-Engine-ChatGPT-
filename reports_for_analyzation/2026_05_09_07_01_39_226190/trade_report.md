# EOW Quant Engine — Performance Report

**Generated:** 2026-05-09 01:27 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **754 trades** with a net **LOSS** of **-226.62 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $773.38 USDT |
| Net PnL | -226.6186 USDT |
| Win Rate | 28.4% |
| Profit Factor | 0.501 |
| Sharpe Ratio | -2.188 |
| Sortino Ratio | -2.170 |
| Calmar Ratio | -0.312 |
| Max Drawdown | 24.27% |
| Risk of Ruin | 100.00% |
| Total Fees | 107.0292 USDT |
| Total Slippage | 41.8213 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -77.7681 USDT (before all costs)
- **Fees deducted:** -107.0292 USDT
- **Slippage deducted:** -41.8213 USDT
- **Net PnL (bankable):** -226.6186 USDT

### 2.2 Trade Statistics

- Avg win: +1.0619 USDT
- Avg loss: -0.8405 USDT
- Profit factor: 0.501

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-22.7%** | **-2.19** | **-2.17** | **24.3%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 01:21:03 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:03 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:03 | SIGNAL | ⚡ PAPER_SPEED fallback GALAUSDT: SHORT entry=0.0042 rsi=62.5 |
| 01:21:03 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:03 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:03 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=26.7 above_sma=False regime=TRENDING) |
| 01:21:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:03 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=2.5580 rsi=41.7 |
| 01:21:03 | SIGNAL | ⚡ DTP JTOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:03 | SIGNAL | 📈 STREAK JTOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:03 | SIGNAL | ⚡ PAPER_SPEED fallback JTOUSDT: LONG entry=0.5653 rsi=54.9 |
| 01:21:05 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:05 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:05 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2311.0600 rsi=60.6 |
| 01:21:05 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:21:06 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:06 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:06 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=71.1 above_sma=True regime=TRENDING) |
| 01:21:06 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:06 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:06 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=30.0 |
| 01:21:06 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:21:07 | SIGNAL | ⚡ DTP NILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:07 | SIGNAL | 📈 STREAK NILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:07 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=22.5 above_sma=False regime=TRENDING) |
| 01:21:09 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:09 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:09 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=37.0 above_sma=False regime=TRENDING) |
| 01:21:12 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:21:12 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:21:12 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: LONG entry=0.0557 rsi=60.0 |
| 01:22:13 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:13 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:13 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=80268.6800 rsi=60.7 |
| 01:22:13 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:13 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:13 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=54.0 above_sma=True regime=MEAN_REVERTING) |
| 01:22:13 | SIGNAL | ⚡ DTP JTOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:13 | SIGNAL | 📈 STREAK JTOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:13 | SIGNAL | ⚡ PAPER_SPEED fallback JTOUSDT: LONG entry=0.5655 rsi=57.6 |
| 01:22:14 | SIGNAL | ⚡ DTP NILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:14 | SIGNAL | 📈 STREAK NILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:14 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=32.5 above_sma=False regime=TRENDING) |
| 01:22:14 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:14 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:14 | SIGNAL | ⚡ PAPER_SPEED fallback GALAUSDT: SHORT entry=0.0042 rsi=62.5 |
| 01:22:14 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:14 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:14 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=21.4 above_sma=False regime=TRENDING) |
| 01:22:14 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:14 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:14 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=89.9 above_sma=True regime=TRENDING) |
| 01:22:15 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:15 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:15 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.565 rr=5.00 |
| 01:22:15 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: LONG entry=2.5620 rsi=44.7 |
| 01:22:16 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:16 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:16 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=22.1 above_sma=False regime=TRENDING) |
| 01:22:17 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:17 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:17 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: SHORT entry=1.5890 rsi=41.4 |
| 01:22:18 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:18 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:18 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: LONG entry=0.0557 rsi=60.0 |
| 01:22:18 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:18 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:18 | SIGNAL | ⚡ ALPHA TrendBreakout FILUSDT score=0.536 rr=5.00 |
| 01:22:18 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=71.8 above_sma=True regime=TRENDING) |
| 01:22:37 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:22:37 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:22:37 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=34.0 |
| 01:22:37 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 01:24:14 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:14 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:14 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=78.4 above_sma=True regime=TRENDING) |
| 01:24:14 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:14 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:14 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=80252.4200 rsi=53.1 |
| 01:24:14 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:14 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:14 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=51.4 above_sma=False regime=MEAN_REVERTING) |
| 01:24:14 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:14 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:14 | SIGNAL | ⚡ ALPHA PullbackEntry LUNCUSDT score=0.484 rr=5.00 |
| 01:24:14 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=44.1 above_sma=True regime=MEAN_REVERTING) |
| 01:24:14 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:14 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:14 | SIGNAL | ⚡ ALPHA TrendBreakout NOTUSDT score=0.652 rr=5.00 |
| 01:24:14 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=17.6 above_sma=False regime=TRENDING) |
| 01:24:14 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:14 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:14 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 01:24:14 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:14 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:14 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=73.7 above_sma=True regime=TRENDING) |
| 01:24:15 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:15 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:15 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=43.0 above_sma=False regime=MEAN_REVERTING) |
| 01:24:15 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:15 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:15 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI filter blocked (rsi=31.2 above_sma=False regime=TRENDING) |
| 01:24:15 | SIGNAL | ⚡ DTP JTOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:15 | SIGNAL | 📈 STREAK JTOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:15 | SIGNAL | ⚡ ALPHA PullbackEntry JTOUSDT score=0.489 rr=4.00 |
| 01:24:15 | SIGNAL | ⚡ PAPER_SPEED fallback JTOUSDT: SHORT entry=0.5649 rsi=57.8 |
| 01:24:20 | SIGNAL | ⚡ DTP NILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:20 | SIGNAL | 📈 STREAK NILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:20 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=29.4 above_sma=False regime=TRENDING) |
| 01:24:22 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:22 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:22 | FILTER | ⚡ PAPER_SPEED STRKUSDT: RSI filter blocked (rsi=63.2 above_sma=True regime=TRENDING) |
| 01:24:24 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:24:24 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:24:24 | SIGNAL | ⚡ PAPER_SPEED fallback NEARUSDT: SHORT entry=1.5940 rsi=53.1 |
| 01:25:09 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:09 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:09 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: SHORT entry=0.4671 rsi=39.8 |
| 01:25:15 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:15 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:15 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=79.7 above_sma=True regime=TRENDING) |
| 01:25:15 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:15 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:15 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=42.5 above_sma=False regime=MEAN_REVERTING) |
| 01:25:15 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:15 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:15 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=56.8 above_sma=False regime=MEAN_REVERTING) |
| 01:25:15 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:15 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:15 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=20.0 above_sma=False regime=TRENDING) |
| 01:25:15 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:15 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:15 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=75.7 above_sma=True regime=TRENDING) |
| 01:25:16 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:16 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:16 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=45.5 above_sma=False regime=MEAN_REVERTING) |
| 01:25:16 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:16 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:16 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=0=10%_of_avg=4,min=10%[base=45%×0.20]) |
| 01:25:16 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=80252.4200 rsi=54.1 |
| 01:25:19 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:19 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:19 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=45.9 above_sma=True regime=MEAN_REVERTING) |
| 01:25:20 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:20 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:20 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: LONG entry=0.0557 rsi=61.1 |
| 01:25:23 | SIGNAL | ⚡ DTP JTOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:23 | SIGNAL | 📈 STREAK JTOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:23 | FILTER | ⚡ PAPER_SPEED JTOUSDT: RSI filter blocked (rsi=62.2 above_sma=True regime=TRENDING) |
| 01:25:24 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:24 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:24 | SIGNAL | ⚡ ALPHA TrendBreakout NEARUSDT score=0.739 rr=5.00 |
| 01:25:24 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=64.5 above_sma=True regime=TRENDING) |
| 01:25:31 | SIGNAL | ⚡ DTP NILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:25:31 | SIGNAL | 📈 STREAK NILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:25:31 | FILTER | ⚡ PAPER_SPEED NILUSDT: RSI filter blocked (rsi=27.4 above_sma=False regime=TRENDING) |
| 01:25:37 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #58: meta_score=52.0 verdict=— |
| 01:26:09 | SIGNAL | ⚡ DTP GALAUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:09 | SIGNAL | 📈 STREAK GALAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:09 | FILTER | ⚡ PAPER_SPEED GALAUSDT: RSI filter blocked (rsi=45.5 above_sma=False regime=MEAN_REVERTING) |
| 01:26:09 | SIGNAL | ⚡ DTP NOTUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:09 | SIGNAL | 📈 STREAK NOTUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:09 | FILTER | ⚡ PAPER_SPEED NOTUSDT: RSI filter blocked (rsi=18.8 above_sma=False regime=TRENDING) |
| 01:26:10 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:10 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:10 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=49.9 above_sma=False regime=MEAN_REVERTING) |
| 01:26:10 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:10 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:10 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: SHORT entry=0.4671 rsi=40.5 |
| 01:26:10 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:10 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:10 | SIGNAL | ⚡ PAPER_SPEED fallback TONUSDT: SHORT entry=2.5510 rsi=46.3 |
| 01:26:10 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:10 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:10 | FILTER | ⚡ PAPER_SPEED ICPUSDT: RSI filter blocked (rsi=79.1 above_sma=True regime=TRENDING) |
| 01:26:10 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:10 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:10 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=80259.5500 rsi=52.1 |
| 01:26:11 | SIGNAL | ⚡ DTP STRKUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:11 | SIGNAL | 📈 STREAK STRKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:11 | SIGNAL | ⚡ ALPHA PullbackEntry STRKUSDT score=0.496 rr=5.00 |
| 01:26:11 | SIGNAL | ⚡ PAPER_SPEED fallback STRKUSDT: LONG entry=0.0556 rsi=61.1 |
| 01:26:12 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:12 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:12 | FILTER | ⚡ PAPER_SPEED bypass NEARUSDT: SLEEP_MODE(vol=280=2%_of_avg=11331,min=10%[base=45%×0.20]) |
| 01:26:12 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI filter blocked (rsi=66.7 above_sma=True regime=TRENDING) |
| 01:26:12 | SIGNAL | ⚡ DTP NILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:12 | SIGNAL | 📈 STREAK NILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:12 | SIGNAL | ⚡ PAPER_SPEED fallback NILUSDT: SHORT entry=0.0709 rsi=43.4 |
| 01:26:13 | SIGNAL | ⚡ DTP JTOUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:13 | SIGNAL | 📈 STREAK JTOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:13 | FILTER | ⚡ PAPER_SPEED JTOUSDT: RSI filter blocked (rsi=63.2 above_sma=True regime=TRENDING) |
| 01:26:15 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:15 | SIGNAL | 📈 STREAK FILUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:15 | FILTER | ⚡ PAPER_SPEED FILUSDT: RSI filter blocked (rsi=72.7 above_sma=True regime=TRENDING) |
| 01:26:27 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_3 af=RELAX score_min=0.400 vol_mult=0.20× fee_tol=0.10 |
| 01:26:27 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.400 |
| 01:26:27 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=49.5 above_sma=True regime=MEAN_REVERTING) |
| 01:26:54 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |

---
*EOW Quant Engine V4.0 — 2026-05-09 01:27 UTC*