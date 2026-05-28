# EOW Quant Engine — Performance Report

**Generated:** 2026-05-28 15:23 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **1831 trades** with a net **LOSS** of **-254.55 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $745.45 USDT |
| Net PnL | -254.5513 USDT |
| Win Rate | 22.6% |
| Profit Factor | 0.476 |
| Sharpe Ratio | -3.567 |
| Sortino Ratio | -4.692 |
| Calmar Ratio | -0.137 |
| Max Drawdown | 25.50% |
| Risk of Ruin | 100.00% |
| Total Fees | 132.6213 USDT |
| Total Slippage | 71.8621 USDT |
| Deployability | 45/100 (NOT READY) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -50.0679 USDT (before all costs)
- **Fees deducted:** -132.6213 USDT
- **Slippage deducted:** -71.8621 USDT
- **Net PnL (bankable):** -254.5513 USDT

### 2.2 Trade Statistics

- Avg win: +0.5595 USDT
- Avg loss: -0.3425 USDT
- Profit factor: 0.476

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-25.5%** | **-3.57** | **-4.69** | **25.5%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 14:59:32 | SIGNAL | 📈 STREAK UUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:03 | SIGNAL | 📈 STREAK BTCUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:03 | SIGNAL | 📈 STREAK ETHUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:04 | SIGNAL | 📈 STREAK SEIUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:05 | SIGNAL | 📈 STREAK TONUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:05 | SIGNAL | 📈 STREAK ONDOUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:05 | SIGNAL | 📈 STREAK RENDERUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:05 | SIGNAL | 📈 STREAK FETUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:06 | SIGNAL | 📈 STREAK OPGUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:11 | SIGNAL | 📈 STREAK ALTUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:15 | SIGNAL | 📈 STREAK FILUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:16 | SIGNAL | 📈 STREAK UUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:18 | SIGNAL | 📈 STREAK ICPUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.480 |
| 15:00:41 | TRADE | [TM] WLDUSDT TIME_EXIT @ 0.2876 (Fast-fail: 1.4min r=-0.500<-0.45) |
| 15:01:40 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:40 | SIGNAL | 📈 STREAK UUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:40 | SIGNAL | ⚡ DTP SEIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:40 | SIGNAL | 📈 STREAK SEIUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:40 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:40 | SIGNAL | 📈 STREAK ETHUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:40 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:40 | SIGNAL | 📈 STREAK ICPUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:41 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:41 | SIGNAL | 📈 STREAK ONDOUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:41 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:41 | SIGNAL | 📈 STREAK BTCUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:41 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:41 | SIGNAL | 📈 STREAK FILUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:42 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:42 | SIGNAL | 📈 STREAK NEARUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:42 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:42 | SIGNAL | 📈 STREAK OPGUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:43 | SIGNAL | ⚡ DTP FETUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:43 | SIGNAL | 📈 STREAK FETUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:43 | SIGNAL | ⚡ DTP ALTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:43 | SIGNAL | 📈 STREAK ALTUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:44 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:44 | SIGNAL | 📈 STREAK TONUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:01:45 | SIGNAL | ⚡ DTP RENDERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:01:45 | SIGNAL | 📈 STREAK RENDERUSDT: HOT len=4 score_adj=-0.03 → eff_min=0.430 |
| 15:02:54 | TRADE | Position closed [SL] WLDUSDT @ 0.2881 |
| 15:04:16 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #368: meta_score=42.3 verdict=— |
| 15:05:04 | FILTER | ⚡ PAPER_SPEED bypass ONDOUSDT: SLEEP_MODE(vol=4260=6%_of_avg=74382,min=10%[base=45%×0.20]) |
| 15:05:04 | FILTER | ⚡ PAPER_SPEED bypass RENDERUSDT: SLEEP_MODE(vol=283=3%_of_avg=9333,min=10%[base=45%×0.20]) |
| 15:05:05 | SIGNAL | ⚡ ALPHA PullbackEntry NEARUSDT score=0.612 rr=5.00 |
| 15:05:05 | SIGNAL | ⚡ DISABLED_OVERRIDE NEARUSDT: ALPHA_PBE_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 15:05:05 | SIGNAL | 🔔 Signal SHORT NEARUSDT \| PBE: EMA_DIST=0.14% RSI=67.6 RR=5.00 SCORE=0.612 |
| 15:05:05 | SIGNAL | 🧮 EV NEARUSDT: ev=-0.1399 p_win=10.0% n=10 |
| 15:05:24 | FILTER | ⚡ PAPER_SPEED bypass ALTUSDT: SLEEP_MODE(vol=0=0%_of_avg=399877,min=10%[base=45%×0.20]) |
| 15:08:09 | SIGNAL | ⚡ DTP WLDUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:09 | SIGNAL | ⚡ ALPHA PullbackEntry WLDUSDT score=0.671 rr=5.00 |
| 15:08:09 | SIGNAL | ⚡ DISABLED_OVERRIDE WLDUSDT: ALPHA_PBE_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 15:08:09 | SIGNAL | 🔔 Signal SHORT WLDUSDT \| PBE: EMA_DIST=0.09% RSI=58.8 RR=5.00 SCORE=0.671 |
| 15:08:09 | SIGNAL | 🧮 EV WLDUSDT: ev=0.3866 p_win=31.8% n=22 |
| 15:08:09 | SIGNAL | ⚠️ ALLOC_ZERO WLDUSDT: score=0.555 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 15:08:09 | SIGNAL | 💰 Orchestrator WLDUSDT: score=0.555 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=311.922404 |
| 15:08:09 | TRADE | 📋 Limit SHORT WLDUSDT @ 0.2870 qty=311.922404 risk=3.73U [TrendFollowing \| TRENDING] |
| 15:08:10 | SIGNAL | ⚡ DTP SEIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:10 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:10 | SIGNAL | ⚡ DTP RENDERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:10 | SIGNAL | ⚡ DISABLED_OVERRIDE RENDERUSDT: MR_BB_RSI_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 15:08:10 | SIGNAL | 🔔 Signal SHORT RENDERUSDT \| BB upper touch \| RSI=82.6 \| Mean=1.9491 \| TP=1.9446 |
| 15:08:10 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) RENDERUSDT |
| 15:08:10 | FILTER | 🤖 RL_GATE RENDERUSDT: ECO_TOXIC(q=-0.184 wr=19% n=524) |
| 15:08:10 | SIGNAL | ⚡ RL_OVERRIDE RENDERUSDT: TOXIC context MEAN_REVERTING\|MeanReversion [bypass=active, learning continues] |
| 15:08:10 | FILTER | 🚫 LEAN_GATE RENDERUSDT: SL_TOO_TIGHT(0.1200%<0.15%) (rr=0.00 sl=0.120%) |
| 15:08:10 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:10 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:10 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:10 | SIGNAL | ⚡ DTP FETUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:11 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:12 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:13 | SIGNAL | ⚡ DTP ALTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:13 | SIGNAL | ⚡ ALPHA PullbackEntry ALTUSDT score=0.482 rr=5.00 |
| 15:08:13 | SIGNAL | ⚡ DISABLED_OVERRIDE ALTUSDT: ALPHA_PBE_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 15:08:13 | SIGNAL | 🔔 Signal SHORT ALTUSDT \| PBE: EMA_DIST=0.15% RSI=57.1 RR=5.00 SCORE=0.482 |
| 15:08:13 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) ALTUSDT |
| 15:08:13 | FILTER | 🤖 RL_GATE ALTUSDT: ECO_TOXIC(q=-0.184 wr=19% n=524) |
| 15:08:13 | SIGNAL | ⚡ RL_OVERRIDE ALTUSDT: TOXIC context MEAN_REVERTING\|MeanReversion [bypass=active, learning continues] |
| 15:08:13 | SIGNAL | 🧮 EV ALTUSDT: ev=0.4399 p_win=31.0% n=29 |
| 15:08:13 | SIGNAL | ⚠️ ALLOC_ZERO ALTUSDT: score=0.410 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 15:08:13 | SIGNAL | 💰 Orchestrator ALTUSDT: score=0.410 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=21584.789609 |
| 15:08:13 | TRADE | 📋 Limit SHORT ALTUSDT @ 0.0069 qty=21584.789609 risk=3.73U [MeanReversion \| MEAN_REVERTING] |
| 15:08:13 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:20 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:08:44 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:09:16 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #369: meta_score=42.3 verdict=— |
| 15:09:24 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:09:24 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:09:24 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:09:24 | SIGNAL | ⚡ ALPHA PullbackEntry TONUSDT score=0.537 rr=5.00 |
| 15:09:24 | SIGNAL | ⚡ DISABLED_OVERRIDE TONUSDT: ALPHA_PBE_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 15:09:24 | SIGNAL | 🔔 Signal SHORT TONUSDT \| PBE: EMA_DIST=0.00% RSI=65.4 RR=5.00 SCORE=0.537 |
| 15:09:24 | SIGNAL | 🔄 AIE INVERSE suppressed (bypass) TONUSDT |
| 15:09:24 | FILTER | 🤖 RL_GATE TONUSDT: ECO_TOXIC(q=-0.184 wr=19% n=524) |
| 15:09:24 | SIGNAL | ⚡ RL_OVERRIDE TONUSDT: TOXIC context MEAN_REVERTING\|MeanReversion [bypass=active, learning continues] |
| 15:09:24 | SIGNAL | 🧮 EV TONUSDT: ev=0.4569 p_win=28.6% n=21 |
| 15:09:24 | SIGNAL | ⚠️ ALLOC_ZERO TONUSDT: score=0.560 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 15:09:24 | SIGNAL | 💰 Orchestrator TONUSDT: score=0.560 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=85.522303 |
| 15:09:24 | TRADE | 📋 Limit SHORT TONUSDT @ 1.7445 qty=85.522303 risk=3.73U [MeanReversion \| MEAN_REVERTING] |
| 15:09:25 | SIGNAL | ⚡ DTP SEIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:09:25 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:09:25 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:09:26 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:09:27 | SIGNAL | ⚡ DTP FETUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:09:29 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:10:27 | SIGNAL | ⚡ DTP RENDERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:10:28 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:10:35 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:03 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:03 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:04 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:04 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:04 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:04 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:05 | SIGNAL | ⚡ DTP SEIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:07 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:07 | SIGNAL | ⚡ ALPHA TrendBreakout FILUSDT score=0.820 rr=5.00 |
| 15:12:07 | SIGNAL | ⚡ DISABLED_OVERRIDE FILUSDT: ALPHA_TCB_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 15:12:07 | SIGNAL | 🔔 Signal SHORT FILUSDT \| TCB: ADX=31.9 VOL=3.6x RR=5.00 SCORE=0.820 |
| 15:12:07 | SIGNAL | 🧮 EV FILUSDT: ev=-0.0113 p_win=14.3% n=14 |
| 15:12:07 | SIGNAL | ⚡ DTP FETUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:10 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:10 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=464=8%_of_avg=5762,min=10%[base=45%×0.20]) |
| 15:12:16 | SIGNAL | ⚡ DTP RENDERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:12:16 | FILTER | ⚡ PAPER_SPEED bypass RENDERUSDT: SLEEP_MODE(vol=218=3%_of_avg=8042,min=10%[base=45%×0.20]) |
| 15:13:03 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:03 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:03 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:03 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:05 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:05 | SIGNAL | ⚡ DTP FETUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:06 | SIGNAL | ⚡ DTP SEIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:07 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:08 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:09 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:14 | SIGNAL | ⚡ DTP RENDERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 15:13:14 | FILTER | ⚡ PAPER_SPEED bypass RENDERUSDT: SLEEP_MODE(vol=628=8%_of_avg=7763,min=10%[base=45%×0.20]) |
| 15:14:16 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #370: meta_score=42.3 verdict=— |
| 15:14:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:00 | SIGNAL | ⚡ DTP SEIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:00 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:00 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:00 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:01 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:01 | SIGNAL | ⚡ DTP FETUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:06 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:08 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:15:14 | SIGNAL | ⚡ DTP RENDERUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:00 | SIGNAL | ⚡ DTP SEIUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:00 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:00 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:02 | SIGNAL | ⚡ DTP FETUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:04 | SIGNAL | ⚡ DTP ICPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:07 | SIGNAL | ⚡ DTP RENDERUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:08 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:17 | SIGNAL | ⚡ DTP FILUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 15:16:40 | TRADE | [TM] WLDUSDT TIME_EXIT @ 0.2869 (Stale: 8.5min r=0.073<0.15) |
| 15:16:40 | TRADE | Position closed [SL] WLDUSDT @ 0.2869 |
| 15:17:45 | TRADE | [TM] TONUSDT TIME_EXIT @ 1.7440 (Stale: 8.3min r=0.086<0.15) |
| 15:17:45 | TRADE | Position closed [SL] TONUSDT @ 1.744 |
| 15:19:16 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #371: meta_score=42.3 verdict=— |
| 15:19:18 | SIGNAL | 📈 STREAK FILUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:18 | SIGNAL | ⚡ ALPHA TrendBreakout FILUSDT score=0.832 rr=5.00 |
| 15:19:18 | SIGNAL | ⚡ DISABLED_OVERRIDE FILUSDT: ALPHA_TCB_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 15:19:18 | SIGNAL | 🔔 Signal SHORT FILUSDT \| TCB: ADX=33.1 VOL=3.1x RR=5.00 SCORE=0.832 |
| 15:19:18 | SIGNAL | ⚡ LCC_OVERRIDE FILUSDT: state=REDUCING cl=3 [bypass=active, size not reduced] |
| 15:19:18 | SIGNAL | 🧮 EV FILUSDT: ev=-0.0097 p_win=14.3% n=14 |
| 15:19:19 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK FETUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK RENDERUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:19 | SIGNAL | ⚡ ALPHA PullbackEntry NEARUSDT score=0.573 rr=5.00 |
| 15:19:19 | SIGNAL | ⚡ DISABLED_OVERRIDE NEARUSDT: ALPHA_PBE_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 15:19:19 | SIGNAL | 🔔 Signal SHORT NEARUSDT \| PBE: EMA_DIST=0.08% RSI=57.4 RR=5.00 SCORE=0.573 |
| 15:19:19 | SIGNAL | ⚡ LCC_OVERRIDE NEARUSDT: state=REDUCING cl=3 [bypass=active, size not reduced] |
| 15:19:19 | SIGNAL | 🧮 EV NEARUSDT: ev=-0.1384 p_win=10.0% n=10 |
| 15:19:21 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:22 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:19:24 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:10 | TRADE | [TM] ALTUSDT BE: SL→0.0069 (R=1.63≥1.5 mode=TREND_FOLLOW → SL→BE) |
| 15:20:21 | SIGNAL | 📈 STREAK ICPUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:21 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:21 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:21 | SIGNAL | 📈 STREAK SEIUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:21 | SIGNAL | 📈 STREAK FILUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:22 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:23 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:24 | SIGNAL | 📈 STREAK RENDERUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:24 | SIGNAL | 📈 STREAK FETUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:25 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:26 | SIGNAL | 📈 STREAK UUSDT: COLD len=3 score_adj=+0.05 → eff_min=0.480 |
| 15:20:26 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=475=5%_of_avg=9120,min=10%[base=45%×0.20]) |

---
*EOW Quant Engine V4.0 — 2026-05-28 15:23 UTC*