# EOW Quant Engine — Performance Report

**Generated:** 2026-05-01 06:11 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **243 trades** with a net **LOSS** of **-151.08 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $848.92 USDT |
| Net PnL | -151.0820 USDT |
| Win Rate | 45.7% |
| Profit Factor | 0.379 |
| Sharpe Ratio | -2.915 |
| Sortino Ratio | -2.329 |
| Calmar Ratio | -0.929 |
| Max Drawdown | 16.87% |
| Risk of Ruin | 100.00% |
| Total Fees | 50.5689 USDT |
| Total Slippage | 0.0000 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -100.5131 USDT (before all costs)
- **Fees deducted:** -50.5689 USDT
- **Slippage deducted:** -0.0000 USDT
- **Net PnL (bankable):** -151.0820 USDT

### 2.2 Trade Statistics

- Avg win: +0.8310 USDT
- Avg loss: -1.8434 USDT
- Profit factor: 0.379

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-15.1%** | **-2.92** | **-2.33** | **16.9%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 06:06:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0618 |
| 06:06:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:06:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:00 | SIGNAL | ⚡ ALPHA TrendBreakout LUNCUSDT score=0.733 rr=5.00 |
| 06:06:00 | SIGNAL | 🔔 Signal SHORT LUNCUSDT \| TCB: ADX=36.6 VOL=5.6x RR=5.00 SCORE=0.733 |
| 06:06:00 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:00 | SIGNAL | ⚡ ALPHA TrendBreakout ORCAUSDT score=0.656 rr=4.00 |
| 06:06:00 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| TCB: ADX=29.1 VOL=1.4x RR=4.00 SCORE=0.656 |
| 06:06:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:00 | SIGNAL | ⚡ ALPHA TrendBreakout MEGAUSDT score=0.630 rr=5.00 |
| 06:06:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| TCB: ADX=25.4 VOL=2.0x RR=5.00 SCORE=0.630 |
| 06:06:01 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:01 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=84.0600 |
| 06:06:01 | SIGNAL | 🔔 Signal LONG SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:06:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0413 |
| 06:06:01 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:06:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2285.1600 |
| 06:06:01 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:06:01 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:01 | FILTER | ⚡ PAPER_SPEED bypass PENGUUSDT: SLEEP_MODE(vol=51061=7%_of_avg=761330,min=10%[base=45%×0.20]) |
| 06:06:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0099 |
| 06:06:01 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:06:01 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:01 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=618.2100 |
| 06:06:01 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:06:02 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:02 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3772 |
| 06:06:02 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:06:03 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:03 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3264 |
| 06:06:03 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:06:04 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:04 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=567=5%_of_avg=10990,min=10%[base=45%×0.20]) |
| 06:06:17 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #4: meta_score=85.0 verdict=BLOCKED |
| 06:06:56 | SIGNAL | ⚡ DTP PLUMEUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:06:56 | SIGNAL | ⚡ PAPER_SPEED fallback PLUMEUSDT: LONG entry=0.0115 |
| 06:06:56 | SIGNAL | 🔔 Signal LONG PLUMEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:00 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:00 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=1.9700 |
| 06:07:00 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=77176.6600 |
| 06:07:00 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 |
| 06:07:00 | SIGNAL | 🔔 Signal SHORT LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:00 | SIGNAL | ⚡ ALPHA TrendBreakout BIOUSDT score=0.755 rr=5.00 |
| 06:07:00 | SIGNAL | 🔔 Signal LONG BIOUSDT \| TCB: ADX=28.8 VOL=2.3x RR=5.00 SCORE=0.755 |
| 06:07:00 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:00 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3264 |
| 06:07:00 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1535 |
| 06:07:00 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0618 |
| 06:07:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:02 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:02 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=618.2200 |
| 06:07:02 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:03 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:03 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=84.1100 |
| 06:07:03 | SIGNAL | 🔔 Signal LONG SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:04 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:04 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: LONG entry=1.3779 |
| 06:07:04 | SIGNAL | 🔔 Signal LONG XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:07:06 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:06 | SIGNAL | ⚡ ALPHA VolatilitySqueeze ETHUSDT score=0.589 rr=6.00 |
| 06:07:06 | SIGNAL | 🔔 Signal LONG ETHUSDT \| VSE: BB_WIDTH=0.15% SQUEEZE→EXPAND RR=6.00 SCORE=0.589 |
| 06:07:08 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:07:08 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0099 |
| 06:07:08 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:00 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:00 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=1.9720 |
| 06:08:00 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0618 |
| 06:08:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=618.0400 |
| 06:08:00 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1540 |
| 06:08:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 |
| 06:08:00 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:00 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:00 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: SHORT entry=0.0099 |
| 06:08:00 | SIGNAL | 🔔 Signal SHORT PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:01 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:01 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: SHORT entry=84.0900 |
| 06:08:01 | SIGNAL | 🔔 Signal SHORT SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:01 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:01 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3774 |
| 06:08:01 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2284.4000 |
| 06:08:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0416 |
| 06:08:01 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:02 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:02 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=77160.1800 |
| 06:08:02 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:02 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:02 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=0=0%_of_avg=11009,min=10%[base=45%×0.20]) |
| 06:08:03 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:03 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3264 |
| 06:08:03 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:08:05 | SIGNAL | ⚡ DTP PLUMEUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:08:05 | FILTER | ⚡ PAPER_SPEED bypass PLUMEUSDT: SLEEP_MODE(vol=0=0%_of_avg=127892,min=10%[base=45%×0.20]) |
| 06:08:06 | SIGNAL | ⚡ PAPER_SPEED fallback PLUMEUSDT: LONG entry=0.0115 |
| 06:08:06 | SIGNAL | 🔔 Signal LONG PLUMEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1535 |
| 06:09:00 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:00 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:00 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: SHORT entry=0.3262 |
| 06:09:00 | SIGNAL | 🔔 Signal SHORT TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 |
| 06:09:00 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0618 |
| 06:09:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2284.3600 |
| 06:09:00 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:00 | SIGNAL | ⚡ ALPHA PullbackEntry BTCUSDT score=0.502 rr=5.00 |
| 06:09:00 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PBE: EMA_DIST=0.00% RSI=44.8 RR=5.00 SCORE=0.502 |
| 06:09:00 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:00 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=1.9720 |
| 06:09:00 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=617.9300 |
| 06:09:00 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:00 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:00 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0099 |
| 06:09:00 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:02 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:02 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=31=0%_of_avg=10909,min=10%[base=45%×0.20]) |
| 06:09:03 | SIGNAL | ⚡ DTP PLUMEUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:03 | SIGNAL | ⚡ PAPER_SPEED fallback PLUMEUSDT: LONG entry=0.0115 |
| 06:09:03 | SIGNAL | 🔔 Signal LONG PLUMEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:05 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:05 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: SHORT entry=84.0700 |
| 06:09:05 | SIGNAL | 🔔 Signal SHORT SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:06 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:06 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: LONG entry=1.3774 |
| 06:09:06 | SIGNAL | 🔔 Signal LONG XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:09:07 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:09:07 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0416 |
| 06:09:07 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1537 |
| 06:10:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:00 | SIGNAL | ⚡ ALPHA TrendBreakout BTCUSDT score=0.538 rr=5.00 |
| 06:10:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| TCB: ADX=51.9 VOL=1.5x RR=5.00 SCORE=0.538 |
| 06:10:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=617.9300 |
| 06:10:00 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0618 |
| 06:10:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:00 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=1.9800 |
| 06:10:00 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:00 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 |
| 06:10:00 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:01 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:01 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=300=3%_of_avg=10921,min=10%[base=45%×0.20]) |
| 06:10:01 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:01 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3771 |
| 06:10:01 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:02 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:02 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0414 |
| 06:10:02 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2284.3200 |
| 06:10:02 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:03 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:03 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: SHORT entry=0.0099 |
| 06:10:03 | SIGNAL | 🔔 Signal SHORT PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:03 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:03 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=84.0700 |
| 06:10:03 | SIGNAL | 🔔 Signal LONG SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:03 | SIGNAL | ⚡ DTP PLUMEUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:03 | SIGNAL | ⚡ PAPER_SPEED fallback PLUMEUSDT: LONG entry=0.0115 |
| 06:10:03 | SIGNAL | 🔔 Signal LONG PLUMEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 06:10:08 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_2 af=RELAX score_min=0.400 vol_mult=0.30× fee_tol=0.10 |
| 06:10:08 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3262 |
| 06:10:08 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |

---
*EOW Quant Engine V4.0 — 2026-05-01 06:11 UTC*