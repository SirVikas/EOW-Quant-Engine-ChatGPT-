# EOW Quant Engine — Performance Report

**Generated:** 2026-05-01 14:33 UTC  
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
| 14:27:18 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 14:27:18 | SYSTEM | Mode: PAPER \| Capital: 1000.0 USDT |
| 14:27:18 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 14:27:19 | SYSTEM | 📂 DataLake replay: 243 trades → equity=848.92 USDT |
| 14:27:19 | SYSTEM | 📂 State restored: snapshot(848.92) validated vs replay(848.92) |
| 14:27:19 | SYSTEM | ⚡ Phase 4 Profit Engine online \| rr_min=2.0 score_min=0.48 max_per_trade=5% daily_cap=6% |
| 14:27:19 | SYSTEM | 🧠 Phase 5 EV Engine online \| ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 14:27:19 | SYSTEM | 🔓 Phase 5.1 Activation Layer online \| activator_tiers=T1@5min T2@12min T3@25min \| explore_rate=3% smart_fee_rr≥3.0:15% |
| 14:27:19 | SYSTEM | Phase 6.6 Gate online \| can_trade=True reason=BOOT_GRACE safe_mode=False |
| 14:27:19 | SYSTEM | All subsystems online. Scanning markets… |
| 14:27:19 | SYSTEM | ⚡ [FTD-031] Performance layer online \| target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 14:27:24 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2310.4800 |
| 14:27:24 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:24 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=78258.5200 |
| 14:27:24 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:24 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\data\exports\optimized_dna.json |
| 14:27:24 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: LONG entry=1.3911 |
| 14:27:24 | SIGNAL | 🔔 Signal LONG XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:24 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0628 |
| 14:27:24 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:24 | FILTER | ⚡ PAPER_SPEED bypass BIOUSDT: SLEEP_MODE(vol=14953=8%_of_avg=180438,min=10%[base=45%×0.20]) |
| 14:27:24 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0402 |
| 14:27:24 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:24 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: SHORT entry=0.0100 |
| 14:27:24 | SIGNAL | 🔔 Signal SHORT PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:24 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=620.7400 |
| 14:27:24 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:26 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=84.2100 |
| 14:27:26 | SIGNAL | 🔔 Signal LONG SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:27 | FILTER | ⚡ PAPER_SPEED bypass TRXUSDT: SLEEP_MODE(vol=3581=8%_of_avg=46891,min=10%[base=45%×0.20]) |
| 14:27:27 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3266 |
| 14:27:27 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:28 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=3787=8%_of_avg=46421,min=10%[base=45%×0.20]) |
| 14:27:28 | SIGNAL | ⚡ PAPER_SPEED fallback UUSDT: SHORT entry=1.0000 |
| 14:27:28 | SIGNAL | 🔔 Signal SHORT UUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:29 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1551 |
| 14:27:29 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:27:31 | SYSTEM | ⚡ Mode switched to PAPER |
| 14:27:36 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0300 |
| 14:27:36 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=620.8400 |
| 14:29:00 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: LONG entry=1.3919 |
| 14:29:00 | SIGNAL | 🔔 Signal LONG XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0300 |
| 14:29:00 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1556 |
| 14:29:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: SHORT entry=84.2200 |
| 14:29:00 | SIGNAL | 🔔 Signal SHORT SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0628 |
| 14:29:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=78274.5800 |
| 14:29:00 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2310.3500 |
| 14:29:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0100 |
| 14:29:01 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:03 | FILTER | ⚡ PAPER_SPEED bypass TRXUSDT: SLEEP_MODE(vol=3113=7%_of_avg=45509,min=10%[base=45%×0.20]) |
| 14:29:03 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3266 |
| 14:29:03 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:29:40 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0401 |
| 14:29:40 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=78275.8600 |
| 14:30:00 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2309.2800 |
| 14:30:00 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: SHORT entry=84.1700 |
| 14:30:00 | SIGNAL | 🔔 Signal SHORT SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1555 |
| 14:30:00 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0628 |
| 14:30:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3918 |
| 14:30:00 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=620.7000 |
| 14:30:00 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: SHORT entry=0.0100 |
| 14:30:01 | SIGNAL | 🔔 Signal SHORT PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:02 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3266 |
| 14:30:02 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:03 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0230 |
| 14:30:03 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:30:18 | FILTER | ⚡ PAPER_SPEED bypass BIOUSDT: SLEEP_MODE(vol=2485=2%_of_avg=152535,min=10%[base=45%×0.20]) |
| 14:30:18 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0400 |
| 14:30:18 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78168.0000 |
| 14:31:00 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:00 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: SHORT entry=0.0100 |
| 14:31:00 | SIGNAL | 🔔 Signal SHORT PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3904 |
| 14:31:00 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=620.2900 |
| 14:31:00 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2306.2500 |
| 14:31:00 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:01 | SIGNAL | ⚡ ALPHA TrendBreakout SOLUSDT score=0.524 rr=5.00 |
| 14:31:01 | SIGNAL | 🔔 Signal SHORT SOLUSDT \| TCB: ADX=29.8 VOL=1.3x RR=5.00 SCORE=0.524 |
| 14:31:01 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0628 |
| 14:31:01 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0400 |
| 14:31:01 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:02 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1559 |
| 14:31:02 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:02 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: SHORT entry=0.3265 |
| 14:31:02 | SIGNAL | 🔔 Signal SHORT TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:31:02 | FILTER | ⚡ PAPER_SPEED bypass UUSDT: SLEEP_MODE(vol=3436=8%_of_avg=43748,min=10%[base=45%×0.20]) |
| 14:31:03 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0210 |
| 14:31:03 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=84.1300 |
| 14:32:00 | SIGNAL | 🔔 Signal LONG SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0100 |
| 14:32:00 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2308.6400 |
| 14:32:00 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:00 | SIGNAL | ⚡ ALPHA PullbackEntry CHIPUSDT score=0.557 rr=5.00 |
| 14:32:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PBE: EMA_DIST=0.22% RSI=62.4 RR=5.00 SCORE=0.557 |
| 14:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: LONG entry=1.3925 |
| 14:32:00 | SIGNAL | 🔔 Signal LONG XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=620.7600 |
| 14:32:00 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1561 |
| 14:32:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=78248.8700 |
| 14:32:00 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:03 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: LONG entry=2.0270 |
| 14:32:03 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:05 | SIGNAL | 🔔 Signal SHORT TRXUSDT \| EMA cross DOWN \| trend↓ \| RSI=36.4 \| ATR=0.0001 |
| 14:32:07 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0402 |
| 14:32:07 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:32:19 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #1: meta_score=85.0 verdict=BLOCKED |
| 14:33:00 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:00 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3921 |
| 14:33:00 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=78285.7800 |
| 14:33:00 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: SHORT entry=0.0625 |
| 14:33:00 | SIGNAL | 🔔 Signal SHORT CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: SHORT entry=620.6600 |
| 14:33:00 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:00 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=84.1600 |
| 14:33:01 | SIGNAL | 🔔 Signal LONG SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3265 |
| 14:33:01 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2309.0200 |
| 14:33:01 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:01 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1560 |
| 14:33:01 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:03 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:03 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0180 |
| 14:33:03 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:03 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:03 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0100 |
| 14:33:03 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 14:33:19 | SIGNAL | ⚡ DTP UUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:26 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 14:33:26 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0401 |
| 14:33:26 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |

---
*EOW Quant Engine V4.0 — 2026-05-01 14:33 UTC*