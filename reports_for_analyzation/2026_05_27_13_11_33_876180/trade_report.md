# EOW Quant Engine — Performance Report

**Generated:** 2026-05-27 02:17 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **1284 trades** with a net **LOSS** of **-232.63 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $767.37 USDT |
| Net PnL | -232.6342 USDT |
| Win Rate | 20.4% |
| Profit Factor | 0.412 |
| Sharpe Ratio | -4.425 |
| Sortino Ratio | -5.537 |
| Calmar Ratio | -0.196 |
| Max Drawdown | 23.26% |
| Risk of Ruin | 100.00% |
| Total Fees | 113.4184 USDT |
| Total Slippage | 71.8621 USDT |
| Deployability | 25/100 (NOT READY) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -47.3537 USDT (before all costs)
- **Fees deducted:** -113.4184 USDT
- **Slippage deducted:** -71.8621 USDT
- **Net PnL (bankable):** -232.6342 USDT

### 2.2 Trade Statistics

- Avg win: +0.6227 USDT
- Avg loss: -0.3873 USDT
- Profit factor: 0.412

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-23.3%** | **-4.42** | **-5.54** | **23.3%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 00:48:03 | SIGNAL | 📈 STREAK UUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 00:48:03 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=8=0%_of_avg=5835,min=10%[base=45%×0.20]) |
| 00:48:03 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.480 |
| 00:48:04 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #8: meta_score=46.2 verdict=— |
| 00:48:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:48:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:48:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:48:59 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:48:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:48:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:49:00 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:49:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:49:00 | SIGNAL | ⚡ DISABLED_OVERRIDE ONDOUSDT: MR_BB_RSI_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 00:49:00 | SIGNAL | 🔔 Signal SHORT ONDOUSDT \| BB upper touch \| RSI=75.0 \| Mean=0.4060 \| TP=0.4060 |
| 00:49:00 | FILTER | 🤖 RL_GATE ONDOUSDT: ECO_TOXIC(q=-0.100 wr=18% n=310) |
| 00:49:00 | SIGNAL | ⚡ RL_OVERRIDE ONDOUSDT: TOXIC context MEAN_REVERTING\|MeanReversion [bypass=active, learning continues] |
| 00:49:00 | SIGNAL | ⚡ LCC_OVERRIDE ONDOUSDT: state=PAUSED cl=5 [bypass=active, size not reduced] |
| 00:49:00 | SIGNAL | ⚠️ ALLOC_ZERO ONDOUSDT: score=0.234 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 00:49:00 | SIGNAL | 🎯 CONSISTENCY ONDOUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 00:49:00 | SIGNAL | 💰 Orchestrator ONDOUSDT: score=0.234 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=188.184008 |
| 00:49:00 | TRADE | 📋 Limit SHORT ONDOUSDT @ 0.4084 qty=188.184008 risk=3.84U [MeanReversion \| MEAN_REVERTING] |
| 00:49:00 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:49:00 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:49:00 | SIGNAL | ⚡ DTP WLDUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:49:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:49:01 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:49:01 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:49:14 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:49:14 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:49:14 | FILTER | ⚡ PAPER_SPEED bypass SPKUSDT: SLEEP_MODE(vol=2926=8%_of_avg=35664,min=10%[base=45%×0.20]) |
| 00:49:15 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:49:15 | SIGNAL | 📈 STREAK UUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:49:54 | TRADE | [TM] ONDOUSDT PARTIAL_TP 94.092004 @ 0.4073 (R=3.02≥3.0 → 50% exit) |
| 00:49:59 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:49:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:49:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:49:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:49:59 | SIGNAL | ⚡ DTP WLDUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:49:59 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:50:00 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:50:00 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:50:00 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:50:00 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:50:01 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:50:01 | SIGNAL | 📈 STREAK UUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:50:03 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:50:03 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:50:10 | TRADE | [TM] RENDERUSDT TIME_EXIT @ 2.3250 (Fast-fail: 2.1min r=-0.571<-0.45) |
| 00:50:12 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 00:50:12 | SIGNAL | 📈 STREAK TONUSDT: COLD len=5 score_adj=+0.05 → eff_min=0.430 |
| 00:50:13 | TRADE | Position closed [SL] RENDERUSDT @ 2.324 |
| 00:50:59 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 00:51:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 00:51:00 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 00:51:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 00:51:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 00:51:03 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 00:51:06 | SIGNAL | 📈 STREAK TONUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 00:51:10 | SIGNAL | 📈 STREAK UUSDT: COLD len=6 score_adj=+0.05 → eff_min=0.480 |
| 00:51:57 | TRADE | Position closed [SL] ONDOUSDT @ 0.4088 |
| 00:51:59 | SIGNAL | 📈 STREAK UUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:51:59 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:51:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:51:59 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:52:00 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:52:00 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:52:00 | SIGNAL | ⚡ ALPHA TrendBreakout TONUSDT score=0.701 rr=5.00 |
| 00:52:00 | SIGNAL | ⚡ DISABLED_OVERRIDE TONUSDT: ALPHA_TCB_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 00:52:00 | SIGNAL | 🔔 Signal LONG TONUSDT \| TCB: ADX=35.4 VOL=1.4x RR=5.00 SCORE=0.701 |
| 00:52:00 | SIGNAL | ⚡ LCC_OVERRIDE TONUSDT: state=PAUSED cl=7 [bypass=active, size not reduced] |
| 00:52:00 | SIGNAL | ⚠️ ALLOC_ZERO TONUSDT: score=0.495 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 00:52:00 | SIGNAL | 🎯 CONSISTENCY TONUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 00:52:00 | SIGNAL | 💰 Orchestrator TONUSDT: score=0.495 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=23.411624 |
| 00:52:00 | TRADE | 📋 Limit LONG TONUSDT @ 1.9674 qty=23.411624 risk=3.84U [TrendFollowing \| TRENDING] |
| 00:52:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:52:04 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:52:59 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:52:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:52:59 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:52:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:53:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:53:04 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #9: meta_score=46.1 verdict=— |
| 00:53:04 | SIGNAL | 📈 STREAK UUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:53:20 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:53:44 | TRADE | [TM] TONUSDT TIME_EXIT @ 1.9650 (Fast-fail: 1.7min r=-0.492<-0.45) |
| 00:53:59 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:54:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:54:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:54:00 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:54:00 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:54:01 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:54:06 | SIGNAL | 📈 STREAK UUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 00:54:41 | TRADE | Position closed [SL] TONUSDT @ 1.965 |
| 00:55:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:55:01 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:55:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:55:01 | SIGNAL | 📈 STREAK OPGUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:55:01 | SIGNAL | ⚡ ALPHA PullbackEntry OPGUSDT score=0.527 rr=5.00 |
| 00:55:01 | SIGNAL | ⚡ DISABLED_OVERRIDE OPGUSDT: ALPHA_PBE_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 00:55:01 | SIGNAL | 🔔 Signal SHORT OPGUSDT \| PBE: EMA_DIST=0.09% RSI=61.3 RR=5.00 SCORE=0.527 |
| 00:55:01 | FILTER | 🤖 RL_GATE OPGUSDT: ECO_TOXIC(q=-0.110 wr=18% n=311) |
| 00:55:01 | SIGNAL | ⚡ RL_OVERRIDE OPGUSDT: TOXIC context MEAN_REVERTING\|MeanReversion [bypass=active, learning continues] |
| 00:55:01 | SIGNAL | ⚡ LCC_OVERRIDE OPGUSDT: state=PAUSED cl=8 [bypass=active, size not reduced] |
| 00:55:01 | SIGNAL | ⚠️ ALLOC_ZERO OPGUSDT: score=0.362 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 00:55:01 | SIGNAL | 🎯 CONSISTENCY OPGUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 00:55:01 | SIGNAL | 💰 Orchestrator OPGUSDT: score=0.362 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=365.110059 |
| 00:55:01 | TRADE | 📋 Limit SHORT OPGUSDT @ 0.2104 qty=365.110059 risk=3.84U [MeanReversion \| MEAN_REVERTING] |
| 00:55:01 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:55:04 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:55:07 | SIGNAL | 📈 STREAK UUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:55:59 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:56:00 | SIGNAL | 📈 STREAK RENDERUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:56:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:56:00 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:56:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:56:01 | SIGNAL | 📈 STREAK UUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 00:56:02 | TRADE | [TM] OPGUSDT TIME_EXIT @ 0.2107 (Fast-fail: 1.0min r=-0.634<-0.45) |
| 00:56:03 | TRADE | Position closed [SL] OPGUSDT @ 0.2107 |
| 00:56:12 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:56:59 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:56:59 | FILTER | ⚡ PAPER_SPEED bypass SPKUSDT: SLEEP_MODE(vol=2124=7%_of_avg=30687,min=10%[base=45%×0.20]) |
| 00:57:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:57:00 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:57:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:57:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:57:01 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:57:01 | FILTER | ⚡ PAPER_SPEED bypass ONDOUSDT: SLEEP_MODE(vol=625=3%_of_avg=23639,min=10%[base=45%×0.20]) |
| 00:57:03 | SIGNAL | 📈 STREAK UUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:57:04 | SIGNAL | 📈 STREAK RENDERUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:57:59 | SIGNAL | 📈 STREAK RENDERUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:57:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:58:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:58:00 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:58:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:58:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:58:01 | SIGNAL | 📈 STREAK SPKUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:58:01 | SIGNAL | ⚡ DISABLED_OVERRIDE SPKUSDT: MR_BB_RSI_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 00:58:01 | SIGNAL | 🔔 Signal SHORT SPKUSDT \| BB upper touch \| RSI=76.0 \| Mean=0.0260 \| TP=0.0260 |
| 00:58:01 | FILTER | 🤖 RL_GATE SPKUSDT: ECO_TOXIC(q=-0.113 wr=18% n=312) |
| 00:58:01 | SIGNAL | ⚡ RL_OVERRIDE SPKUSDT: TOXIC context MEAN_REVERTING\|MeanReversion [bypass=active, learning continues] |
| 00:58:01 | FILTER | 🚫 LEAN_GATE SPKUSDT: SL_TOO_TIGHT(0.0717%<0.15%) (rr=0.00 sl=0.072%) |
| 00:58:02 | SIGNAL | 📈 STREAK UUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:58:04 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #10: meta_score=46.0 verdict=— |
| 00:58:59 | SIGNAL | 📈 STREAK NEARUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:58:59 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:59:00 | SIGNAL | 📈 STREAK WLDUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:59:00 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:59:00 | SIGNAL | 📈 STREAK RENDERUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:59:00 | SIGNAL | 📈 STREAK ONDOUSDT: COLD len=9 score_adj=+0.05 → eff_min=0.480 |
| 00:59:00 | SIGNAL | ⚡ ALPHA TrendBreakout ONDOUSDT score=0.805 rr=5.00 |
| 00:59:00 | SIGNAL | ⚡ DISABLED_OVERRIDE ONDOUSDT: ALPHA_TCB_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 00:59:00 | SIGNAL | 🔔 Signal LONG ONDOUSDT \| TCB: ADX=60.0 VOL=3.2x RR=5.00 SCORE=0.805 |
| 00:59:00 | SIGNAL | ⚡ LCC_OVERRIDE ONDOUSDT: state=PAUSED cl=9 [bypass=active, size not reduced] |
| 00:59:00 | SIGNAL | ⚠️ ALLOC_ZERO ONDOUSDT: score=0.783 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 00:59:00 | SIGNAL | 🎯 CONSISTENCY ONDOUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 00:59:00 | SIGNAL | 💰 Orchestrator ONDOUSDT: score=0.783 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=112.424608 |
| 00:59:00 | TRADE | 📋 Limit LONG ONDOUSDT @ 0.4096 qty=112.424608 risk=3.84U [TrendFollowing \| TRENDING] |
| 01:01:15 | TRADE | [TM] ONDOUSDT TIME_EXIT @ 0.4090 (Fast-fail: 2.2min r=-0.499<-0.45) |
| 01:01:16 | TRADE | Position closed [SL] ONDOUSDT @ 0.409 |
| 01:03:04 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #11: meta_score=46.0 verdict=— |
| 01:06:33 | TRADE | Position closed [BE] FETUSDT @ 0.2572 |
| 01:08:04 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #12: meta_score=46.0 verdict=— |
| 01:08:59 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=1=8%_of_avg=14,min=10%[base=45%×0.20]) |
| 01:11:59 | SIGNAL | ⚡ DTP FETUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:11:59 | SIGNAL | ⚡ ALPHA TrendBreakout FETUSDT score=0.700 rr=5.00 |
| 01:11:59 | SIGNAL | ⚡ DISABLED_OVERRIDE FETUSDT: ALPHA_TCB_v1 allowed [bypass=active — RL needs outcomes; Q-decay will deprioritise if losing] |
| 01:11:59 | SIGNAL | 🔔 Signal SHORT FETUSDT \| TCB: ADX=34.7 VOL=1.5x RR=5.00 SCORE=0.700 |
| 01:11:59 | SIGNAL | ⚡ LCC_OVERRIDE FETUSDT: state=PAUSED cl=0 [bypass=active, size not reduced] |
| 01:11:59 | SIGNAL | ⚠️ ALLOC_ZERO FETUSDT: score=0.499 below min allocator band [bypass=active, orchestrator BYPASS override] |
| 01:11:59 | SIGNAL | 🎯 CONSISTENCY FETUSDT: mode=PAUSED ce_mult=0.00× reason=MODE_PAUSED |
| 01:11:59 | SIGNAL | 💰 Orchestrator FETUSDT: score=0.499 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=182.746399 |
| 01:11:59 | TRADE | 📋 Limit SHORT FETUSDT @ 0.2521 qty=182.746399 risk=3.84U [TrendFollowing \| TRENDING] |
| 01:11:59 | SIGNAL | ⚡ DTP OPGUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP NEARUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP WLDUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP RENDERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:01 | SIGNAL | ⚡ DTP SPKUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:02 | SIGNAL | ⚡ DTP ONDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:15 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:12:47 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 01:13:00 | TRADE | [TM] FETUSDT TIME_EXIT @ 0.2529 (Fast-fail: 1.0min r=-0.510<-0.45) |
| 01:13:00 | TRADE | Position closed [SL] FETUSDT @ 0.2529 |
| 01:13:04 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #13: meta_score=46.0 verdict=— |
| 01:14:06 | FILTER | ⚡ PAPER_SPEED bypass SPKUSDT: SLEEP_MODE(vol=4418=8%_of_avg=57843,min=10%[base=45%×0.20]) |
| 01:14:24 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=462=6%_of_avg=8077,min=10%[base=45%×0.20]) |
| 01:15:16 | FILTER | ⚡ PAPER_SPEED bypass SPKUSDT: SLEEP_MODE(vol=3662=6%_of_avg=57701,min=10%[base=45%×0.20]) |
| 01:18:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #14: meta_score=46.0 verdict=— |
| 01:23:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #15: meta_score=46.0 verdict=— |
| 01:28:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #16: meta_score=46.0 verdict=— |
| 01:33:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #17: meta_score=46.0 verdict=— |
| 01:38:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #18: meta_score=46.0 verdict=— |
| 01:43:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #19: meta_score=46.0 verdict=— |
| 01:48:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #20: meta_score=46.0 verdict=— |
| 01:53:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #21: meta_score=46.0 verdict=— |
| 01:58:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #22: meta_score=46.0 verdict=— |
| 02:03:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #23: meta_score=46.0 verdict=— |
| 02:08:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #24: meta_score=46.0 verdict=— |
| 02:13:05 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #25: meta_score=46.0 verdict=— |

---
*EOW Quant Engine V4.0 — 2026-05-27 02:17 UTC*