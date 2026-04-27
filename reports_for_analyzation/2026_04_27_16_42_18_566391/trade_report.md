# EOW Quant Engine — Performance Report

**Generated:** 2026-04-27 11:09 UTC  
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
| 11:03:39 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 11:03:39 | SYSTEM | Mode: PAPER \| Capital: 1000.0 USDT |
| 11:03:39 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 11:03:40 | SYSTEM | 📂 DataLake replay: 243 trades → equity=848.92 USDT |
| 11:03:40 | SYSTEM | 📂 State restored: snapshot(848.92) validated vs replay(848.92) |
| 11:03:40 | SYSTEM | ⚡ Phase 4 Profit Engine online \| rr_min=2.0 score_min=0.48 max_per_trade=5% daily_cap=6% |
| 11:03:40 | SYSTEM | 🧠 Phase 5 EV Engine online \| ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 11:03:40 | SYSTEM | 🔓 Phase 5.1 Activation Layer online \| activator_tiers=T1@5min T2@12min T3@25min \| explore_rate=3% smart_fee_rr≥3.0:15% |
| 11:03:40 | SYSTEM | Phase 6.6 Gate online \| can_trade=True reason=BOOT_GRACE safe_mode=False |
| 11:03:40 | SYSTEM | All subsystems online. Scanning markets… |
| 11:03:40 | SYSTEM | ⚡ [FTD-031] Performance layer online \| target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 11:03:49 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\data\exports\optimized_dna.json |
| 11:03:56 | SYSTEM | ⚡ Mode switched to PAPER |
| 11:04:01 | SIGNAL | ⚡ ALPHA VolatilitySqueeze AAVEUSDT score=0.781 rr=6.00 |
| 11:04:01 | SIGNAL | 🔔 Signal SHORT AAVEUSDT \| VSE: BB_WIDTH=0.56% SQUEEZE→EXPAND RR=6.00 SCORE=0.781 |
| 11:04:13 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| EMA cross DOWN \| trend↓ \| RSI=48.7 \| ATR=0.0040 |
| 11:05:05 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| BB lower touch \| RSI=12.2 \| Mean=0.0096 \| TP=0.0097 |
| 11:05:05 | SIGNAL | ⚡ ALPHA VolatilitySqueeze AAVEUSDT score=0.666 rr=6.00 |
| 11:05:05 | SIGNAL | 🔔 Signal SHORT AAVEUSDT \| VSE: BB_WIDTH=0.85% SQUEEZE→EXPAND RR=6.00 SCORE=0.666 |
| 11:05:05 | SIGNAL | 🔔 Signal LONG SOLUSDT \| BB lower touch \| RSI=20.0 \| Mean=85.2005 \| TP=85.2840 |
| 11:05:06 | SIGNAL | ⚡ ALPHA VolatilitySqueeze XRPUSDT score=0.677 rr=6.00 |
| 11:05:06 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| VSE: BB_WIDTH=0.19% SQUEEZE→EXPAND RR=6.00 SCORE=0.677 |
| 11:05:06 | SIGNAL | ⚡ ALPHA TrendBreakout ETHUSDT score=0.617 rr=5.00 |
| 11:05:06 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| TCB: ADX=25.6 VOL=1.8x RR=5.00 SCORE=0.617 |
| 11:05:06 | SIGNAL | ⚡ ALPHA VolatilitySqueeze TRUMPUSDT score=0.647 rr=6.00 |
| 11:05:06 | SIGNAL | 🔔 Signal SHORT TRUMPUSDT \| VSE: BB_WIDTH=0.73% SQUEEZE→EXPAND RR=6.00 SCORE=0.647 |
| 11:05:07 | SIGNAL | ⚡ ALPHA VolatilitySqueeze BNBUSDT score=0.639 rr=6.00 |
| 11:05:07 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| VSE: BB_WIDTH=0.17% SQUEEZE→EXPAND RR=6.00 SCORE=0.639 |
| 11:05:07 | SIGNAL | ⚡ ALPHA VolatilitySqueeze ADAUSDT score=0.753 rr=6.00 |
| 11:05:07 | SIGNAL | 🔔 Signal SHORT ADAUSDT \| VSE: BB_WIDTH=0.35% SQUEEZE→EXPAND RR=6.00 SCORE=0.753 |
| 11:05:08 | SIGNAL | ⚡ ALPHA VolatilitySqueeze SUIUSDT score=0.722 rr=6.00 |
| 11:05:08 | SIGNAL | 🔔 Signal SHORT SUIUSDT \| VSE: BB_WIDTH=0.55% SQUEEZE→EXPAND RR=6.00 SCORE=0.722 |
| 11:05:59 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| BB lower touch \| RSI=11.2 \| Mean=0.0096 \| TP=0.0097 |
| 11:07:59 | SIGNAL | ⚡ ALPHA TrendBreakout BNBUSDT score=0.559 rr=5.00 |
| 11:07:59 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| TCB: ADX=28.2 VOL=2.0x RR=5.00 SCORE=0.559 |
| 11:08:00 | SIGNAL | 🔔 Signal LONG BTCUSDT \| BB lower touch \| RSI=26.8 \| Mean=77849.6153 \| TP=77882.6953 |
| 11:08:40 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #1: meta_score=85.0 verdict=BLOCKED |
| 11:08:58 | SYSTEM | 📦 Master Report Bundle downloaded → eow_bundle_1777288136.zip (243 trades, 244 KB) |
| 11:09:03 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:03 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:03 | SIGNAL | ⚡ DTP ZBTUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:03 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:03 | SIGNAL | ⚡ ALPHA TrendBreakout BNBUSDT score=0.527 rr=5.00 |
| 11:09:03 | SIGNAL | 🔔 Signal SHORT BNBUSDT \| TCB: ADX=31.4 VOL=1.4x RR=5.00 SCORE=0.527 |
| 11:09:03 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:03 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:04 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:04 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:05 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:05 | SIGNAL | ⚡ DTP AAVEUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:07 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:07 | SIGNAL | ⚡ DTP ADAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:07 | SIGNAL | ⚡ DTP SUIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:08 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:10 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:12 | SIGNAL | ⚡ DTP TRUMPUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 11:09:13 | SIGNAL | ⚡ DTP LDOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |

---
*EOW Quant Engine V4.0 — 2026-04-27 11:09 UTC*