# EOW Quant Engine — Performance Report

**Generated:** 2026-05-02 05:42 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **324 trades** with a net **LOSS** of **-160.93 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $839.07 USDT |
| Net PnL | -160.9276 USDT |
| Win Rate | 38.6% |
| Profit Factor | 0.369 |
| Sharpe Ratio | -2.681 |
| Sortino Ratio | -2.282 |
| Calmar Ratio | -0.702 |
| Max Drawdown | 17.84% |
| Risk of Ruin | 100.00% |
| Total Fees | 57.3651 USDT |
| Total Slippage | 5.0972 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -98.4653 USDT (before all costs)
- **Fees deducted:** -57.3651 USDT
- **Slippage deducted:** -5.0972 USDT
- **Net PnL (bankable):** -160.9276 USDT

### 2.2 Trade Statistics

- Avg win: +0.7535 USDT
- Avg loss: -1.2820 USDT
- Profit factor: 0.369

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-16.1%** | **-2.68** | **-2.28** | **17.8%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 05:23:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:23:01 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=614.3700 |
| 05:23:01 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:23:04 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3832 |
| 05:23:04 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:23:07 | SIGNAL | ⚡ ALPHA VolatilitySqueeze ORCAUSDT score=0.554 rr=6.00 |
| 05:23:07 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| VSE: BB_WIDTH=0.89% SQUEEZE→EXPAND RR=6.00 SCORE=0.554 |
| 05:24:00 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=1=4%_of_avg=13,min=10%[base=45%×0.20]) |
| 05:24:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78070.8400 |
| 05:24:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:24:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=614.6200 |
| 05:24:00 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:24:00 | FILTER | ⚡ PAPER_SPEED bypass TRXUSDT: SLEEP_MODE(vol=12080=7%_of_avg=178522,min=10%[base=45%×0.20]) |
| 05:24:00 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3284 |
| 05:24:00 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:24:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3838 |
| 05:24:00 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:24:01 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1520 |
| 05:24:01 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:24:01 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0652 |
| 05:24:01 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:24:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2298.3500 |
| 05:24:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:24:06 | SIGNAL | ⚡ ALPHA VolatilitySqueeze ORCAUSDT score=0.570 rr=6.00 |
| 05:24:06 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| VSE: BB_WIDTH=1.01% SQUEEZE→EXPAND RR=6.00 SCORE=0.570 |
| 05:25:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:25:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0652 |
| 05:25:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:25:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:25:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78070.7200 |
| 05:25:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:25:00 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:25:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2298.3600 |
| 05:25:00 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:25:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:25:01 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3285 |
| 05:25:01 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:25:01 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:25:01 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=614.6400 |
| 05:25:01 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:25:01 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:25:01 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3839 |
| 05:25:01 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:25:02 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:25:02 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1523 |
| 05:25:02 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:25:03 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:25:03 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=1.9270 |
| 05:25:03 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:26:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:26:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78064.3800 |
| 05:26:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:26:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:26:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0653 |
| 05:26:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:26:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:26:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=614.8900 |
| 05:26:00 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:26:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:26:01 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1519 |
| 05:26:01 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:26:03 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:26:03 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2298.5700 |
| 05:26:03 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:26:04 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:26:04 | FILTER | ⚡ PAPER_SPEED bypass XRPUSDT: SLEEP_MODE(vol=1008=7%_of_avg=15488,min=10%[base=45%×0.20]) |
| 05:26:04 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3840 |
| 05:26:04 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:26:08 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:26:08 | FILTER | ⚡ PAPER_SPEED bypass TRXUSDT: SLEEP_MODE(vol=9727=6%_of_avg=173771,min=10%[base=45%×0.20]) |
| 05:26:08 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3285 |
| 05:26:08 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:26:17 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:26:17 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=1.9310 |
| 05:26:17 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:27:00 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:27:00 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=1.9320 |
| 05:27:00 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:27:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:27:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0652 |
| 05:27:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:27:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:27:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1517 |
| 05:27:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:27:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:27:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=614.8200 |
| 05:27:00 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:27:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:27:01 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=0=4%_of_avg=13,min=10%[base=45%×0.20]) |
| 05:27:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78067.0100 |
| 05:27:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:27:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:27:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2298.9500 |
| 05:27:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:27:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:27:01 | FILTER | ⚡ PAPER_SPEED bypass TRXUSDT: SLEEP_MODE(vol=10514=7%_of_avg=143076,min=10%[base=45%×0.20]) |
| 05:27:02 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3284 |
| 05:27:02 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:27:03 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:27:03 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3831 |
| 05:27:03 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:28:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:28:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0651 |
| 05:28:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:28:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:28:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78067.0100 |
| 05:28:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:28:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:28:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2298.9200 |
| 05:28:02 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:28:02 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:28:02 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1518 |
| 05:28:02 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:28:02 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:28:02 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=614.7700 |
| 05:28:02 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:28:02 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:28:02 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3829 |
| 05:28:02 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:28:04 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:28:04 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3285 |
| 05:28:04 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:28:34 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:28:34 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=1.9360 |
| 05:28:34 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:29:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78060.1600 |
| 05:29:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:29:00 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=1.9430 |
| 05:29:00 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:29:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0651 |
| 05:29:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:29:00 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3285 |
| 05:29:00 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:29:03 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:29:03 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3832 |
| 05:29:03 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:29:03 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:29:03 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1518 |
| 05:29:03 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:29:04 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:29:04 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=615.1400 |
| 05:29:04 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:29:08 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:29:08 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2298.8000 |
| 05:29:08 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=615.2100 |
| 05:30:00 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0651 |
| 05:30:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:00 | SIGNAL | 💰 Orchestrator CHIPUSDT: score=0.200 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=1935.079547 |
| 05:30:00 | TRADE | ⚡ PAPER_SPEED market-fill override CHIPUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:00 | TRADE | ✅ Opened SHORT CHIPUSDT qty=1935.079547 risk=1.68U [MeanReversion \| MEAN_REVERTING] |
| 05:30:00 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:00 | FILTER | ⚡ PAPER_SPEED bypass TRXUSDT: SLEEP_MODE(vol=9134=10%_of_avg=93356,min=10%[base=45%×0.20]) |
| 05:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3285 |
| 05:30:00 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:01 | SIGNAL | 💰 Orchestrator TRXUSDT: score=0.254 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=383.481517 |
| 05:30:01 | TRADE | ⚡ PAPER_SPEED market-fill override TRXUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:01 | TRADE | ✅ Opened LONG TRXUSDT qty=383.481517 risk=1.68U [TrendFollowing \| TRENDING] |
| 05:30:01 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:01 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3834 |
| 05:30:01 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:01 | SIGNAL | 💰 Orchestrator XRPUSDT: score=0.360 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=91.060921 |
| 05:30:01 | TRADE | ⚡ PAPER_SPEED market-fill override XRPUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:01 | TRADE | ✅ Opened SHORT XRPUSDT qty=91.060921 risk=1.68U [TrendFollowing \| TRENDING] |
| 05:30:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78110.6400 |
| 05:30:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:01 | SIGNAL | 💰 Orchestrator BTCUSDT: score=0.506 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.001613 |
| 05:30:01 | TRADE | ⚡ PAPER_SPEED market-fill override BTCUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:01 | TRADE | ✅ Opened SHORT BTCUSDT qty=0.001613 risk=1.68U [TrendFollowing \| TRENDING] |
| 05:30:02 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:02 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1519 |
| 05:30:02 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:02 | SIGNAL | 💰 Orchestrator MEGAUSDT: score=0.231 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=829.319806 |
| 05:30:02 | TRADE | ⚡ PAPER_SPEED market-fill override MEGAUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:02 | TRADE | ✅ Opened SHORT MEGAUSDT qty=829.319806 risk=1.68U [TrendFollowing \| TRENDING] |
| 05:30:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2299.8900 |
| 05:30:02 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 05:30:02 | SIGNAL | 💰 Orchestrator ETHUSDT: score=0.264 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.054774 |
| 05:30:02 | TRADE | ⚡ PAPER_SPEED market-fill override ETHUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:02 | TRADE | ✅ Opened LONG ETHUSDT qty=0.054774 risk=1.68U [TrendFollowing \| TRENDING] |
| 05:30:17 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 05:30:17 | FILTER | ⚡ PAPER_SPEED bypass ORCAUSDT: SLEEP_MODE(vol=256=5%_of_avg=5158,min=10%[base=45%×0.20]) |
| 05:30:17 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| EMA cross UP \| trend↑ \| RSI=57.1 \| ATR=0.0076 |
| 05:30:17 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.332 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=64.901431 |
| 05:30:17 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 05:30:17 | TRADE | ✅ Opened LONG ORCAUSDT qty=64.901431 risk=1.68U [TrendFollowing \| TRENDING] |
| 05:31:05 | TRADE | Position closed [TSL+] PENDLEUSDT @ 1.533 |
| 05:31:29 | TRADE | Position closed [SL] ETHUSDT @ 2300.28 |
| 05:31:41 | TRADE | Position closed [TSL+] ORCAUSDT @ 1.946 |
| 05:32:27 | TRADE | Position closed [SL] MEGAUSDT @ 0.152 |
| 05:33:37 | TRADE | Position closed [SL] CHIPUSDT @ 0.06532 |

---
*EOW Quant Engine V4.0 — 2026-05-02 05:42 UTC*