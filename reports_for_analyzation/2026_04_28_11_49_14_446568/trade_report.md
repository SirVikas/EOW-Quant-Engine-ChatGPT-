# EOW Quant Engine — Performance Report

**Generated:** 2026-04-28 06:17 UTC  
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
| 06:11:23 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 06:11:23 | SYSTEM | Mode: PAPER \| Capital: 1000.0 USDT |
| 06:11:23 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 06:11:24 | SYSTEM | 📂 DataLake replay: 243 trades → equity=848.92 USDT |
| 06:11:24 | SYSTEM | 📂 State restored: snapshot(848.92) validated vs replay(848.92) |
| 06:11:24 | SYSTEM | ⚡ Phase 4 Profit Engine online \| rr_min=2.0 score_min=0.48 max_per_trade=5% daily_cap=6% |
| 06:11:24 | SYSTEM | 🧠 Phase 5 EV Engine online \| ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 06:11:24 | SYSTEM | 🔓 Phase 5.1 Activation Layer online \| activator_tiers=T1@5min T2@12min T3@25min \| explore_rate=3% smart_fee_rr≥3.0:15% |
| 06:11:24 | SYSTEM | Phase 6.6 Gate online \| can_trade=True reason=BOOT_GRACE safe_mode=False |
| 06:11:24 | SYSTEM | All subsystems online. Scanning markets… |
| 06:11:24 | SYSTEM | ⚡ [FTD-031] Performance layer online \| target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 06:11:28 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\data\exports\optimized_dna.json |
| 06:11:29 | FILTER | ⚡ PAPER_SPEED bypass ZBTUSDT: SLEEP_MODE(vol=13672=5%_of_avg=252196,min=10%[base=45%×0.20]) |
| 06:11:29 | FILTER | ⚡ PAPER_SPEED bypass TONUSDT: SLEEP_MODE(vol=3923=8%_of_avg=51913,min=10%[base=45%×0.20]) |
| 06:11:40 | SYSTEM | ⚡ Mode switched to PAPER |
| 06:12:06 | FILTER | ⚡ PAPER_SPEED bypass ADAUSDT: SLEEP_MODE(vol=20=0%_of_avg=51380,min=10%[base=45%×0.20]) |
| 06:13:00 | FILTER | ⚡ PAPER_SPEED bypass SOLUSDT: SLEEP_MODE(vol=139=8%_of_avg=1742,min=10%[base=45%×0.20]) |
| 06:13:00 | SIGNAL | ⚡ ALPHA TrendBreakout ORCAUSDT score=0.638 rr=4.00 |
| 06:13:00 | SIGNAL | 🔔 Signal LONG ORCAUSDT \| TCB: ADX=26.9 VOL=1.8x RR=4.00 SCORE=0.638 |
| 06:13:01 | FILTER | ⚡ PAPER_SPEED bypass ADAUSDT: SLEEP_MODE(vol=3995=8%_of_avg=49753,min=10%[base=45%×0.20]) |
| 06:14:00 | SIGNAL | ⚡ ALPHA PullbackEntry ETHUSDT score=0.493 rr=5.00 |
| 06:14:00 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PBE: EMA_DIST=0.00% RSI=60.0 RR=5.00 SCORE=0.493 |
| 06:14:01 | SIGNAL | ⚡ ALPHA PullbackEntry LUNCUSDT score=0.604 rr=4.00 |
| 06:14:01 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PBE: EMA_DIST=0.22% RSI=42.0 RR=4.00 SCORE=0.604 |
| 06:14:10 | FILTER | ⚡ PAPER_SPEED bypass ADAUSDT: SLEEP_MODE(vol=3799=8%_of_avg=48469,min=10%[base=45%×0.20]) |
| 06:15:00 | SIGNAL | ⚡ ALPHA TrendBreakout TRXUSDT score=0.703 rr=5.00 |
| 06:15:00 | SIGNAL | 🔔 Signal SHORT TRXUSDT \| TCB: ADX=27.4 VOL=4.2x RR=5.00 SCORE=0.703 |
| 06:16:00 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| EMA cross DOWN \| trend↓ \| RSI=51.6 \| ATR=0.7571 |
| 06:16:03 | FILTER | ⚡ PAPER_SPEED bypass ADAUSDT: SLEEP_MODE(vol=3762=8%_of_avg=46769,min=10%[base=45%×0.20]) |
| 06:16:25 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #1: meta_score=85.0 verdict=BLOCKED |
| 06:16:59 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:16:59 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:16:59 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:16:59 | SIGNAL | ⚡ DTP ZBTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:16:59 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:00 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:00 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| BB lower touch \| RSI=29.7 \| Mean=0.0001 \| TP=0.0001 |
| 06:17:01 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:02 | SIGNAL | ⚡ DTP SUIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:02 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:03 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 06:17:03 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |

---
*EOW Quant Engine V4.0 — 2026-04-28 06:17 UTC*