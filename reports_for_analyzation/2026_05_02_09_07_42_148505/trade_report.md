# EOW Quant Engine — Performance Report

**Generated:** 2026-05-02 03:28 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **288 trades** with a net **LOSS** of **-156.21 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $843.79 USDT |
| Net PnL | -156.2127 USDT |
| Win Rate | 40.3% |
| Profit Factor | 0.374 |
| Sharpe Ratio | -2.764 |
| Sortino Ratio | -2.318 |
| Calmar Ratio | -0.787 |
| Max Drawdown | 17.37% |
| Risk of Ruin | 100.00% |
| Total Fees | 54.5353 USDT |
| Total Slippage | 2.9748 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -98.7026 USDT (before all costs)
- **Fees deducted:** -54.5353 USDT
- **Slippage deducted:** -2.9748 USDT
- **Net PnL (bankable):** -156.2127 USDT

### 2.2 Trade Statistics

- Avg win: +0.8060 USDT
- Avg loss: -1.4518 USDT
- Profit factor: 0.374

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-15.6%** | **-2.76** | **-2.32** | **17.4%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 03:10:00 | TRADE | ✅ Opened SHORT BNBUSDT qty=0.102955 risk=1.69U [MeanReversion \| MEAN_REVERTING] |
| 03:10:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 03:10:00 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 03:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: SHORT entry=83.8100 |
| 03:10:00 | SIGNAL | 🔔 Signal SHORT SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:10:00 | SIGNAL | 💰 Orchestrator SOLUSDT: score=0.170 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.756283 |
| 03:10:00 | TRADE | ⚡ PAPER_SPEED market-fill override SOLUSDT: USE_LIMIT_ORDERS bypassed |
| 03:10:00 | TRADE | ✅ Opened SHORT SOLUSDT qty=0.756283 risk=1.69U [TrendFollowing \| TRENDING] |
| 03:10:13 | TRADE | Position closed [SL] XRPUSDT @ 1.3845 |
| 03:10:16 | TRADE | Position closed [SL] BNBUSDT @ 615.44 |
| 03:10:20 | TRADE | Position closed [BE] CHIPUSDT @ 0.06594 |
| 03:11:07 | TRADE | Position closed [SL] MEGAUSDT @ 0.15272 |
| 03:12:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:12:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:12:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78273.4000 |
| 03:12:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:12:01 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:12:01 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:12:01 | FILTER | ⚡ PAPER_SPEED bypass PENDLEUSDT: SLEEP_MODE(vol=0=0%_of_avg=2068,min=10%[base=45%×0.20]) |
| 03:12:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: SHORT entry=1.5370 |
| 03:12:01 | SIGNAL | 🔔 Signal SHORT PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:12:38 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #2: meta_score=55.0 verdict=BLOCKED |
| 03:13:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:13:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:13:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0660 |
| 03:13:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:13:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:13:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:13:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78279.1800 |
| 03:13:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:13:05 | SIGNAL | ⚡ DTP XRPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:13:05 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:13:05 | FILTER | ⚡ PAPER_SPEED bypass XRPUSDT: SLEEP_MODE(vol=311=1%_of_avg=31291,min=10%[base=45%×0.20]) |
| 03:13:05 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3844 |
| 03:13:05 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:13:06 | SIGNAL | ⚡ DTP BNBUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:13:06 | SIGNAL | 📈 STREAK BNBUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:13:06 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=615.5500 |
| 03:13:06 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:13:16 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:13:16 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:13:16 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5380 |
| 03:13:16 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:14:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:14:00 | SIGNAL | 📈 STREAK BNBUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:14:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=615.5600 |
| 03:14:00 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:14:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:14:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:14:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3845 |
| 03:14:00 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:14:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:14:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:14:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0660 |
| 03:14:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:14:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:14:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:14:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1532 |
| 03:14:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:14:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:14:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:14:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78274.4700 |
| 03:14:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:14:05 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:14:05 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.610 |
| 03:14:05 | FILTER | ⚡ PAPER_SPEED bypass PENDLEUSDT: SLEEP_MODE(vol=119=6%_of_avg=1984,min=10%[base=45%×0.20]) |
| 03:14:05 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5380 |
| 03:14:05 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:14:40 | TRADE | Position closed [BE] SOLUSDT @ 83.73 |
| 03:15:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:15:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:15:00 | SIGNAL | ⚡ ALPHA PullbackEntry MEGAUSDT score=0.491 rr=5.00 |
| 03:15:00 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PBE: EMA_DIST=0.10% RSI=63.1 RR=5.00 SCORE=0.491 |
| 03:15:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:15:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:15:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3845 |
| 03:15:00 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:15:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:15:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:15:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78277.3100 |
| 03:15:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:15:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:15:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:15:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0660 |
| 03:15:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:15:01 | SIGNAL | ⚡ DTP BNBUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:15:01 | SIGNAL | 📈 STREAK BNBUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:15:01 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=615.6600 |
| 03:15:01 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:15:14 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:15:14 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:15:14 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5380 |
| 03:15:14 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:16:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:16:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:16:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1535 |
| 03:16:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:16:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:16:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:16:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78248.9200 |
| 03:16:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:16:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:16:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:16:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0660 |
| 03:16:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:16:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:16:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:16:01 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3843 |
| 03:16:01 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:16:02 | SIGNAL | ⚡ DTP BNBUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:16:02 | SIGNAL | 📈 STREAK BNBUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:16:02 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=615.6500 |
| 03:16:02 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:16:13 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:16:13 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:16:13 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: SHORT entry=1.5350 |
| 03:16:13 | SIGNAL | 🔔 Signal SHORT PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:17:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:17:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:17:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0660 |
| 03:17:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:17:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:17:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:17:00 | SIGNAL | ⚡ ALPHA PullbackEntry MEGAUSDT score=0.622 rr=5.00 |
| 03:17:00 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PBE: EMA_DIST=0.18% RSI=58.1 RR=5.00 SCORE=0.622 |
| 03:17:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:17:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:17:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78248.9300 |
| 03:17:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:17:01 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:17:01 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:17:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: SHORT entry=1.5350 |
| 03:17:01 | SIGNAL | 🔔 Signal SHORT PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:17:01 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:17:01 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:17:01 | FILTER | ⚡ PAPER_SPEED bypass SOLUSDT: SLEEP_MODE(vol=24=3%_of_avg=754,min=10%[base=45%×0.20]) |
| 03:17:01 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: SHORT entry=83.7500 |
| 03:17:01 | SIGNAL | 🔔 Signal SHORT SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:17:01 | SIGNAL | ⚡ DTP BNBUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:17:01 | SIGNAL | 📈 STREAK BNBUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:17:01 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=615.6500 |
| 03:17:01 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:17:05 | SIGNAL | ⚡ DTP XRPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:17:05 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:17:05 | FILTER | ⚡ PAPER_SPEED bypass XRPUSDT: SLEEP_MODE(vol=2416=8%_of_avg=30231,min=10%[base=45%×0.20]) |
| 03:17:05 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3843 |
| 03:17:05 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:17:38 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #3: meta_score=55.0 verdict=BLOCKED |
| 03:18:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:18:00 | SIGNAL | 📈 STREAK BNBUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:18:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=615.8300 |
| 03:18:00 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:18:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:18:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:18:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| EMA cross UP \| trend↑ \| RSI=54.7 \| ATR=0.0002 |
| 03:18:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:18:00 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:18:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3849 |
| 03:18:00 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:18:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:18:00 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:18:00 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: SHORT entry=83.7900 |
| 03:18:00 | SIGNAL | 🔔 Signal SHORT SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:18:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:18:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:18:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78276.4300 |
| 03:18:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:18:01 | SIGNAL | ⚡ DTP MEGAUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:18:01 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:18:01 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1533 |
| 03:18:01 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:18:01 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=NORMAL af=TIGHTEN score_min=0.560 vol_mult=1.00× fee_tol=0.10 |
| 03:18:01 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.610 |
| 03:18:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: SHORT entry=1.5320 |
| 03:18:01 | SIGNAL | 🔔 Signal SHORT PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:18:31 | TRADE | Position closed [TSL+] ORCAUSDT @ 1.967 |
| 03:19:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78289.0500 |
| 03:19:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:19:00 | SIGNAL | 💰 Orchestrator BTCUSDT: score=0.213 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.001618 |
| 03:19:00 | TRADE | ⚡ PAPER_SPEED market-fill override BTCUSDT: USE_LIMIT_ORDERS bypassed |
| 03:19:00 | TRADE | ✅ Opened SHORT BTCUSDT qty=0.001618 risk=1.69U [TrendFollowing \| TRENDING] |
| 03:19:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0664 |
| 03:19:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:19:00 | SIGNAL | 💰 Orchestrator CHIPUSDT: score=0.348 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=1908.256753 |
| 03:19:00 | TRADE | ⚡ PAPER_SPEED market-fill override CHIPUSDT: USE_LIMIT_ORDERS bypassed |
| 03:19:00 | TRADE | ✅ Opened LONG CHIPUSDT qty=1908.256753 risk=1.69U [TrendFollowing \| TRENDING] |
| 03:19:01 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1534 |
| 03:19:01 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:19:01 | SIGNAL | 💰 Orchestrator MEGAUSDT: score=0.248 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=825.733477 |
| 03:19:01 | TRADE | ⚡ PAPER_SPEED market-fill override MEGAUSDT: USE_LIMIT_ORDERS bypassed |
| 03:19:01 | TRADE | ✅ Opened LONG MEGAUSDT qty=825.733477 risk=1.69U [TrendFollowing \| TRENDING] |
| 03:19:02 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=615.8200 |
| 03:19:02 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 03:19:02 | SIGNAL | 💰 Orchestrator BNBUSDT: score=0.229 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.205662 |
| 03:19:02 | TRADE | ⚡ PAPER_SPEED market-fill override BNBUSDT: USE_LIMIT_ORDERS bypassed |
| 03:19:02 | TRADE | ✅ Opened SHORT BNBUSDT qty=0.205662 risk=1.69U [MeanReversion \| MEAN_REVERTING] |
| 03:19:47 | TRADE | Position closed [BE] CHIPUSDT @ 0.06646 |
| 03:21:51 | TRADE | Position closed [SL] MEGAUSDT @ 0.15312 |
| 03:22:22 | TRADE | Position closed [SL] ETHUSDT @ 2304.17 |
| 03:22:38 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #4: meta_score=55.0 verdict=BLOCKED |

---
*EOW Quant Engine V4.0 — 2026-05-02 03:28 UTC*