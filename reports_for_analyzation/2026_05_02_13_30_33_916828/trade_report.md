# EOW Quant Engine — Performance Report

**Generated:** 2026-05-02 07:58 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **357 trades** with a net **LOSS** of **-165.57 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $834.43 USDT |
| Net PnL | -165.5718 USDT |
| Win Rate | 37.0% |
| Profit Factor | 0.364 |
| Sharpe Ratio | -2.626 |
| Sortino Ratio | -2.265 |
| Calmar Ratio | -0.639 |
| Max Drawdown | 18.29% |
| Risk of Ruin | 100.00% |
| Total Fees | 61.2534 USDT |
| Total Slippage | 8.0134 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -96.3050 USDT (before all costs)
- **Fees deducted:** -61.2534 USDT
- **Slippage deducted:** -8.0134 USDT
- **Net PnL (bankable):** -165.5718 USDT

### 2.2 Trade Statistics

- Avg win: +0.7167 USDT
- Avg loss: -1.1563 USDT
- Profit factor: 0.364

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-16.6%** | **-2.63** | **-2.27** | **18.3%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 07:49:10 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:50:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:50:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:50:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=52.0 above_sma=False regime=MEAN_REVERTING) |
| 07:50:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:50:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:50:00 | FILTER | ⚡ PAPER_SPEED XRPUSDT: RSI filter blocked (rsi=16.7 above_sma=False regime=TRENDING) |
| 07:50:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:50:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:50:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1512 rsi=57.3 |
| 07:50:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:50:03 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:50:03 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:50:03 | SIGNAL | ⚡ PAPER_SPEED fallback WLFIUSDT: SHORT entry=0.0541 rsi=68.8 |
| 07:50:03 | SIGNAL | 🔔 Signal SHORT WLFIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:50:05 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:50:05 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:50:05 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0102 rsi=41.0 |
| 07:50:05 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:50:26 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:50:26 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:50:26 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5290 rsi=57.1 |
| 07:50:26 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:51:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:51:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:51:00 | FILTER | ⚡ PAPER_SPEED XRPUSDT: RSI filter blocked (rsi=20.0 above_sma=False regime=TRENDING) |
| 07:51:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:51:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:51:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=54.2 above_sma=False regime=MEAN_REVERTING) |
| 07:51:00 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:51:00 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:51:00 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0102 rsi=49.3 |
| 07:51:00 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:51:00 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:51:00 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:51:00 | SIGNAL | ⚡ PAPER_SPEED fallback WLFIUSDT: SHORT entry=0.0538 rsi=50.0 |
| 07:51:00 | SIGNAL | 🔔 Signal SHORT WLFIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:51:01 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:51:01 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:51:01 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1509 rsi=51.2 |
| 07:51:01 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:51:06 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:51:06 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:51:06 | FILTER | ⚡ PAPER_SPEED bypass PENDLEUSDT: SLEEP_MODE(vol=39=2%_of_avg=1931,min=10%[base=45%×0.20]) |
| 07:51:06 | SIGNAL | 🔔 Signal SHORT PENDLEUSDT \| EMA cross DOWN \| trend↓ \| RSI=47.4 \| ATR=0.0021 |
| 07:51:16 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #6: meta_score=55.0 verdict=BLOCKED |
| 07:52:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:52:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:52:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=64.6 above_sma=True regime=MEAN_REVERTING) |
| 07:52:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:52:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:52:00 | FILTER | ⚡ PAPER_SPEED XRPUSDT: RSI filter blocked (rsi=21.1 above_sma=False regime=TRENDING) |
| 07:52:00 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:52:00 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:52:00 | FILTER | ⚡ PAPER_SPEED bypass PENGUUSDT: SLEEP_MODE(vol=281111=8%_of_avg=3366718,min=10%[base=45%×0.20]) |
| 07:52:00 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0102 rsi=56.7 |
| 07:52:00 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:52:09 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:52:09 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:52:09 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1509 rsi=50.0 |
| 07:52:09 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:52:10 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:52:10 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:52:10 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5300 rsi=57.9 |
| 07:52:10 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:52:13 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:52:13 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:52:13 | SIGNAL | ⚡ PAPER_SPEED fallback WLFIUSDT: SHORT entry=0.0537 rsi=47.1 |
| 07:52:13 | SIGNAL | 🔔 Signal SHORT WLFIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:53:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:53:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:53:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=63.4 above_sma=True regime=MEAN_REVERTING) |
| 07:53:01 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:53:01 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:53:01 | SIGNAL | ⚡ PAPER_SPEED fallback WLFIUSDT: SHORT entry=0.0538 rsi=50.0 |
| 07:53:01 | SIGNAL | 🔔 Signal SHORT WLFIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:53:02 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:53:02 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:53:02 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1510 rsi=52.3 |
| 07:53:02 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:53:02 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:53:02 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:53:02 | FILTER | ⚡ PAPER_SPEED XRPUSDT: RSI filter blocked (rsi=15.8 above_sma=False regime=TRENDING) |
| 07:53:03 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:53:03 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:53:03 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0102 rsi=57.0 |
| 07:53:03 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:53:14 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:53:14 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:53:14 | FILTER | ⚡ PAPER_SPEED PENDLEUSDT: RSI filter blocked (rsi=68.4 above_sma=True regime=TRENDING) |
| 07:54:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:54:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:54:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=54.6 above_sma=True regime=MEAN_REVERTING) |
| 07:54:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:54:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:54:00 | FILTER | ⚡ PAPER_SPEED XRPUSDT: RSI filter blocked (rsi=5.9 above_sma=False regime=TRENDING) |
| 07:54:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:54:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:54:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1509 rsi=50.0 |
| 07:54:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:54:00 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:54:00 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:54:00 | SIGNAL | ⚡ PAPER_SPEED fallback WLFIUSDT: SHORT entry=0.0539 rsi=47.1 |
| 07:54:00 | SIGNAL | 🔔 Signal SHORT WLFIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:54:04 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:54:04 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:54:04 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0102 rsi=48.9 |
| 07:54:04 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:54:43 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:54:43 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:54:43 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5290 rsi=47.1 |
| 07:54:43 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:55:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:55:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:55:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=51.9 above_sma=True regime=MEAN_REVERTING) |
| 07:55:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:55:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:55:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1510 rsi=54.6 |
| 07:55:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:55:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:55:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:55:00 | FILTER | ⚡ PAPER_SPEED XRPUSDT: RSI filter blocked (rsi=11.1 above_sma=False regime=TRENDING) |
| 07:55:03 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:55:03 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:55:03 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5300 rsi=47.1 |
| 07:55:03 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:55:05 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:55:05 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:55:05 | SIGNAL | ⚡ PAPER_SPEED fallback WLFIUSDT: SHORT entry=0.0539 rsi=50.0 |
| 07:55:05 | SIGNAL | 🔔 Signal SHORT WLFIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:55:05 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:55:05 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:55:05 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0102 rsi=58.6 |
| 07:55:05 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:56:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:56:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:56:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1505 rsi=33.8 |
| 07:56:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:56:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:56:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:56:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=54.5 above_sma=True regime=MEAN_REVERTING) |
| 07:56:00 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:56:00 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:56:00 | SIGNAL | ⚡ PAPER_SPEED fallback WLFIUSDT: SHORT entry=0.0540 rsi=64.3 |
| 07:56:00 | SIGNAL | 🔔 Signal SHORT WLFIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:56:01 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:56:01 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:56:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5310 rsi=56.2 |
| 07:56:01 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:56:01 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:56:01 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:56:01 | FILTER | ⚡ PAPER_SPEED XRPUSDT: RSI filter blocked (rsi=10.5 above_sma=False regime=TRENDING) |
| 07:56:01 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:56:01 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:56:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0102 rsi=55.1 |
| 07:56:01 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:56:16 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #7: meta_score=55.0 verdict=BLOCKED |
| 07:57:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:57:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:57:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: LONG entry=1.3854 rsi=15.8 |
| 07:57:00 | SIGNAL | 🔔 Signal LONG XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:57:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:57:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:57:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=62.6 above_sma=True regime=MEAN_REVERTING) |
| 07:57:02 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:57:02 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:57:02 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1511 rsi=50.2 |
| 07:57:02 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:57:02 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:57:02 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:57:02 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0102 rsi=48.4 |
| 07:57:02 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:57:09 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:57:09 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:57:09 | SIGNAL | ⚡ ALPHA PullbackEntry WLFIUSDT score=0.666 rr=5.00 |
| 07:57:09 | SIGNAL | 🔔 Signal SHORT WLFIUSDT \| PBE: EMA_DIST=0.05% RSI=57.1 RR=5.00 SCORE=0.666 |
| 07:58:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:00 | FILTER | ⚡ PAPER_SPEED CHIPUSDT: RSI filter blocked (rsi=45.9 above_sma=True regime=MEAN_REVERTING) |
| 07:58:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:00 | SIGNAL | ⚡ ALPHA PullbackEntry MEGAUSDT score=0.509 rr=5.00 |
| 07:58:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PBE: EMA_DIST=0.02% RSI=42.9 RR=5.00 SCORE=0.509 |
| 07:58:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:00 | FILTER | ⚡ PAPER_SPEED XRPUSDT: RSI filter blocked (rsi=16.7 above_sma=False regime=TRENDING) |
| 07:58:03 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:03 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:03 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: SHORT entry=0.0102 rsi=42.9 |
| 07:58:03 | SIGNAL | 🔔 Signal SHORT PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:58:07 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:07 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:07 | FILTER | ⚡ PAPER_SPEED bypass PENDLEUSDT: SLEEP_MODE(vol=0=0%_of_avg=2401,min=10%[base=45%×0.20]) |
| 07:58:07 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5300 rsi=52.9 |
| 07:58:07 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:58:12 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_2 af=TIGHTEN score_min=0.560 vol_mult=0.30× fee_tol=0.10 |
| 07:58:12 | SIGNAL | 📈 STREAK WLFIUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.610 |
| 07:58:12 | FILTER | ⚡ PAPER_SPEED bypass WLFIUSDT: SLEEP_MODE(vol=14366=7%_of_avg=193081,min=10%[base=45%×0.20]) |
| 07:58:12 | SIGNAL | ⚡ PAPER_SPEED fallback WLFIUSDT: SHORT entry=0.0538 rsi=57.1 |
| 07:58:12 | SIGNAL | 🔔 Signal SHORT WLFIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |

---
*EOW Quant Engine V4.0 — 2026-05-02 07:58 UTC*