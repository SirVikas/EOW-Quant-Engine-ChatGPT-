# EOW Quant Engine — Performance Report

**Generated:** 2026-05-02 09:33 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **366 trades** with a net **LOSS** of **-169.41 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $830.59 USDT |
| Net PnL | -169.4084 USDT |
| Win Rate | 36.6% |
| Profit Factor | 0.362 |
| Sharpe Ratio | -2.650 |
| Sortino Ratio | -2.291 |
| Calmar Ratio | -0.625 |
| Max Drawdown | 18.67% |
| Risk of Ruin | 100.00% |
| Total Fees | 61.9199 USDT |
| Total Slippage | 8.1139 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -99.3746 USDT (before all costs)
- **Fees deducted:** -61.9199 USDT
- **Slippage deducted:** -8.1139 USDT
- **Net PnL (bankable):** -169.4084 USDT

### 2.2 Trade Statistics

- Avg win: +0.7187 USDT
- Avg loss: -1.1453 USDT
- Profit factor: 0.362

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-16.9%** | **-2.65** | **-2.29** | **18.7%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 08:56:00 | TRADE | 📋 Limit SHORT MEGAUSDT @ 0.1483 qty=1124.190637 risk=12.50U [TrendFollowing \| TRENDING] |
| 08:56:03 | TRADE | [TM] MEGAUSDT BE: SL→0.0983 (R=1.85≥1.8 → SL→BE±0.05) |
| 08:56:03 | TRADE | Position closed [TSL+] MEGAUSDT @ 0.14723 |
| 08:57:01 | SIGNAL | ⚡ ALPHA TrendBreakout WLFIUSDT score=0.737 rr=5.00 |
| 08:57:01 | SIGNAL | 🔔 Signal LONG WLFIUSDT \| TCB: ADX=27.5 VOL=11.5x RR=5.00 SCORE=0.737 |
| 08:57:01 | SIGNAL | 💰 Orchestrator WLFIUSDT: score=0.710 upstream_mult=0.67× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=2997.150260 |
| 08:57:01 | TRADE | 📋 Limit LONG WLFIUSDT @ 0.0557 qty=2997.150260 risk=12.52U [TrendFollowing \| TRENDING] |
| 08:58:29 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #6: meta_score=85.0 verdict=BLOCKED |
| 09:00:08 | TRADE | Position closed [SL] WLFIUSDT @ 0.0555 |
| 09:03:29 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #7: meta_score=85.0 verdict=BLOCKED |
| 09:06:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:06:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:06:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:06:00 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:06:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:06:03 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:06:12 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:07:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:07:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:07:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:07:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:07:01 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:07:05 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:07:11 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:08:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:08:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:08:01 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:08:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:08:02 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:08:04 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:08:29 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #8: meta_score=85.0 verdict=BLOCKED |
| 09:08:32 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:09:00 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:09:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:09:01 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:09:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:09:02 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:09:04 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:09:04 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:10:00 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:10:00 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:10:01 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:10:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:10:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:10:02 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:10:03 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:11:00 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:11:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:11:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:11:01 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:11:01 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:11:01 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:11:10 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:12:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:12:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:12:00 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:12:01 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:12:01 | SIGNAL | ⚡ ALPHA PullbackEntry MEGAUSDT score=0.634 rr=5.00 |
| 09:12:01 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PBE: EMA_DIST=0.13% RSI=66.4 RR=5.00 SCORE=0.634 |
| 09:12:01 | SIGNAL | 💰 Orchestrator MEGAUSDT: score=0.665 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=1125.476121 |
| 09:12:01 | TRADE | 📋 Limit SHORT MEGAUSDT @ 0.1483 qty=1125.476121 risk=4.17U [TrendFollowing \| TRENDING] |
| 09:12:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:12:02 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:12:05 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:12:21 | TRADE | Position closed [SL] MEGAUSDT @ 0.14896 |
| 09:13:29 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #9: meta_score=55.0 verdict=BLOCKED |
| 09:17:52 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:18:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:18:00 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:18:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:18:02 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:18:02 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:18:02 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:18:04 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:18:04 | SIGNAL | ⚡ ALPHA PullbackEntry PENDLEUSDT score=0.574 rr=5.00 |
| 09:18:04 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PBE: EMA_DIST=0.03% RSI=33.3 RR=5.00 SCORE=0.574 |
| 09:18:04 | SIGNAL | 💰 Orchestrator PENDLEUSDT: score=0.543 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=109.492857 |
| 09:18:04 | TRADE | 📋 Limit LONG PENDLEUSDT @ 1.5215 qty=109.492857 risk=4.17U [TrendFollowing \| TRENDING] |
| 09:18:29 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #10: meta_score=55.0 verdict=BLOCKED |
| 09:19:00 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:19:00 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:19:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:19:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:19:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:19:01 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:19:01 | SIGNAL | ⚡ ALPHA PullbackEntry MEGAUSDT score=0.651 rr=5.00 |
| 09:19:01 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PBE: EMA_DIST=0.09% RSI=60.0 RR=5.00 SCORE=0.651 |
| 09:19:01 | SIGNAL | 💰 Orchestrator MEGAUSDT: score=0.630 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=1121.454431 |
| 09:19:01 | TRADE | 📋 Limit SHORT MEGAUSDT @ 0.1486 qty=1121.454431 risk=4.17U [TrendFollowing \| TRENDING] |
| 09:20:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:20:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:20:00 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:20:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:20:05 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:21:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:21:00 | SIGNAL | ⚡ DTP WLFIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:21:00 | SIGNAL | ⚡ ALPHA TrendBreakout WLFIUSDT score=0.723 rr=4.00 |
| 09:21:00 | SIGNAL | 🔔 Signal LONG WLFIUSDT \| TCB: ADX=54.1 VOL=2.2x RR=4.00 SCORE=0.723 |
| 09:21:00 | SIGNAL | 💰 Orchestrator WLFIUSDT: score=0.699 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=2933.945924 |
| 09:21:00 | TRADE | 📋 Limit LONG WLFIUSDT @ 0.0568 qty=2933.945924 risk=4.17U [TrendFollowing \| TRENDING] |
| 09:21:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:21:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:21:01 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:22:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:22:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:22:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:22:02 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:23:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:23:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:23:03 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:23:06 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 09:23:11 | TRADE | Position closed [SL] PENDLEUSDT @ 1.52 |
| 09:24:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:24:00 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:24:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:24:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:24:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:24:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:24:03 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:24:03 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:25:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:25:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:25:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:25:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:25:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:25:01 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:25:05 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:25:05 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:26:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:26:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:26:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:26:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:26:01 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:26:01 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:26:02 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:26:02 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:27:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:27:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:27:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:27:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:27:02 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:27:02 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:27:04 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:27:04 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:28:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:28:00 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:28:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:28:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:28:02 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:28:02 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:28:05 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.510 vol_mult=1.00× fee_tol=0.10 |
| 09:28:05 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.560 |
| 09:28:18 | TRADE | Position closed [SL] WLFIUSDT @ 0.056 |
| 09:28:29 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #11: meta_score=55.0 verdict=BLOCKED |
| 09:29:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:29:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:29:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:29:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:29:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:29:00 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:29:01 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:29:01 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:29:01 | SIGNAL | ⚡ ALPHA PullbackEntry PENDLEUSDT score=0.763 rr=5.00 |
| 09:29:01 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PBE: EMA_DIST=0.06% RSI=40.0 RR=5.00 SCORE=0.763 |
| 09:29:01 | SIGNAL | 💰 Orchestrator PENDLEUSDT: score=0.733 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=54.536553 |
| 09:29:01 | TRADE | 📋 Limit LONG PENDLEUSDT @ 1.5225 qty=54.536553 risk=4.15U [TrendFollowing \| TRENDING] |
| 09:29:03 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:29:03 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:30:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:30:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:30:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:30:00 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:30:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:30:01 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:30:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:30:02 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:31:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:31:00 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:31:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:31:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:31:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:31:02 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:31:04 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:31:04 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:32:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:32:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:32:04 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:32:04 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:32:05 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:32:05 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:32:05 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:32:05 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:33:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:33:00 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:33:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:33:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:33:04 | SIGNAL | ⚡ DTP TRXUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:33:04 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |
| 09:33:07 | SIGNAL | ⚡ DTP ETHUSDT: tier=NORMAL af=TIGHTEN score_min=0.540 vol_mult=1.00× fee_tol=0.10 |
| 09:33:07 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=4 score_adj=+0.05 → eff_min=0.590 |

---
*EOW Quant Engine V4.0 — 2026-05-02 09:33 UTC*