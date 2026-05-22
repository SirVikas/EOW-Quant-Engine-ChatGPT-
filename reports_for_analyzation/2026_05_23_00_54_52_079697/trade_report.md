# EOW Quant Engine — Performance Report

**Generated:** 2026-05-22 19:21 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **451 trades** with a net **LOSS** of **-129.74 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $870.26 USDT |
| Net PnL | -129.7385 USDT |
| Win Rate | 19.5% |
| Profit Factor | 0.395 |
| Sharpe Ratio | -5.141 |
| Sortino Ratio | -6.309 |
| Calmar Ratio | -0.547 |
| Max Drawdown | 13.26% |
| Risk of Ruin | 100.00% |
| Total Fees | 66.0134 USDT |
| Total Slippage | 49.5100 USDT |
| Deployability | 47/100 (NOT READY) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -14.2151 USDT (before all costs)
- **Fees deducted:** -66.0134 USDT
- **Slippage deducted:** -49.5100 USDT
- **Net PnL (bankable):** -129.7385 USDT

### 2.2 Trade Statistics

- Avg win: +0.9640 USDT
- Avg loss: -0.5911 USDT
- Profit factor: 0.395

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-13.0%** | **-5.14** | **-6.31** | **13.3%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 19:18:31 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 19:18:31 | SYSTEM | Mode: PAPER \| Capital: 1000.0 USDT |
| 19:18:32 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 19:18:33 | SYSTEM | 📂 DataLake replay: 451 trades → equity=870.26 USDT |
| 19:18:33 | SYSTEM | 📂 State restored: snapshot(870.26) validated vs replay(870.26) |
| 19:18:33 | SYSTEM | ⚡ Phase 4 Profit Engine online \| rr_min=2.0 score_min=0.48 max_per_trade=5% daily_cap=6% |
| 19:18:33 | SYSTEM | 🧠 Phase 5 EV Engine online \| ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 19:18:33 | SYSTEM | 🔓 Phase 5.1 Activation Layer online \| activator_tiers=T1@5min T2@12min T3@25min \| explore_rate=3% smart_fee_rr≥3.0:15% |
| 19:18:33 | SYSTEM | Phase 6.6 Gate online \| can_trade=True reason=BYPASS_ALL_GATES safe_mode=False |
| 19:18:33 | SYSTEM | All subsystems online. Scanning markets… |
| 19:18:33 | SYSTEM | 🕐 [SESSION_ROUTER] Timezone Authority=UTC \| ASIA 00:00–05:59 UTC \| LONDON 06:00–12:59 UTC \| NY 13:00–18:59 UTC \| LATE 19:00–23:59 UTC |
| 19:18:33 | SYSTEM | ⚡ [FTD-031] Performance layer online \| target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 19:18:40 | SIGNAL | ⚡ PAPER_SPEED fallback GENIUSUSDT: LONG entry=0.6445 rsi=42.8 |
| 19:18:40 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=38.8 above_sma=False bands=[30.0,70.0] (rsi=38.8 above_sma=False regime=MEAN_REVERTING) |
| 19:18:40 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=29.1 above_sma=False bands=[48.0,52.0] (rsi=29.1 above_sma=False regime=TRENDING) |
| 19:18:40 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V18.0\eow_quant_engine_FINAL_v2.2\eow_quant_engine\data\exports\optimized_dna.json |
| 19:18:40 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI_LEVEL: rsi=49.4 above_sma=False bands=[30.0,70.0] (rsi=49.4 above_sma=False regime=MEAN_REVERTING) |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=47.8 above_sma=False bands=[48.0,52.0] (rsi=47.8 above_sma=False regime=TRENDING) |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED ALLOUSDT: RSI_LEVEL: rsi=35.1 above_sma=False bands=[48.0,52.0] (rsi=35.1 above_sma=False regime=TRENDING) |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI_LEVEL: rsi=41.7 above_sma=False bands=[30.0,70.0] (rsi=41.7 above_sma=False regime=MEAN_REVERTING) |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED FETUSDT: RSI_LEVEL: rsi=32.5 above_sma=False bands=[48.0,52.0] (rsi=32.5 above_sma=False regime=TRENDING) |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=27.8 above_sma=False bands=[48.0,52.0] (rsi=27.8 above_sma=False regime=TRENDING) |
| 19:18:41 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=42.9 above_sma=False bands=[30.0,70.0] (rsi=42.9 above_sma=False regime=MEAN_REVERTING) |
| 19:18:45 | FILTER | ⚡ PAPER_SPEED WLDUSDT: RSI_LEVEL: rsi=28.8 above_sma=False bands=[48.0,52.0] (rsi=28.8 above_sma=False regime=TRENDING) |
| 19:18:45 | FILTER | ⚡ PAPER_SPEED FIDAUSDT: RSI_LEVEL: rsi=37.4 above_sma=False bands=[48.0,52.0] (rsi=37.4 above_sma=False regime=TRENDING) |
| 19:18:46 | FILTER | ⚡ PAPER_SPEED INJUSDT: RSI_LEVEL: rsi=48.5 above_sma=False bands=[30.0,70.0] (rsi=48.5 above_sma=False regime=MEAN_REVERTING) |
| 19:18:47 | SYSTEM | ⚡ Mode switched to PAPER |
| 19:18:47 | FILTER | ⚡ PAPER_SPEED ALTUSDT: RSI_LEVEL: rsi=34.8 above_sma=False bands=[48.0,52.0] (rsi=34.8 above_sma=False regime=TRENDING) |
| 19:18:47 | SIGNAL | ⚡ PAPER_SPEED fallback UUSDT: SHORT entry=1.0007 rsi=100.0 |
| 19:20:00 | FILTER | ⚡ PAPER_SPEED NEARUSDT: RSI_LEVEL: rsi=31.9 above_sma=False bands=[48.0,52.0] (rsi=31.9 above_sma=False regime=TRENDING) |
| 19:20:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI_LEVEL: rsi=45.6 above_sma=False bands=[48.0,52.0] (rsi=45.6 above_sma=False regime=TRENDING) |
| 19:20:01 | FILTER | ⚡ PAPER_SPEED EDENUSDT: RSI_LEVEL: rsi=25.8 above_sma=False bands=[48.0,52.0] (rsi=25.8 above_sma=False regime=TRENDING) |
| 19:20:01 | FILTER | ⚡ PAPER_SPEED WLDUSDT: RSI_LEVEL: rsi=35.4 above_sma=False bands=[48.0,52.0] (rsi=35.4 above_sma=False regime=TRENDING) |
| 19:20:01 | SIGNAL | ⚡ PAPER_SPEED fallback ONDOUSDT: SHORT entry=0.3954 rsi=54.5 |
| 19:20:01 | FILTER | ⚡ PAPER_SPEED INJUSDT: RSI_LEVEL: rsi=42.9 above_sma=False bands=[30.0,70.0] (rsi=42.9 above_sma=False regime=MEAN_REVERTING) |
| 19:20:02 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI_LEVEL: rsi=55.8 above_sma=False bands=[30.0,70.0] (rsi=55.8 above_sma=False regime=MEAN_REVERTING) |
| 19:20:02 | FILTER | ⚡ PAPER_SPEED FETUSDT: RSI_LEVEL: rsi=47.1 above_sma=False bands=[48.0,52.0] (rsi=47.1 above_sma=False regime=TRENDING) |
| 19:20:02 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI_LEVEL: rsi=49.3 above_sma=False bands=[30.0,70.0] (rsi=49.3 above_sma=False regime=MEAN_REVERTING) |
| 19:20:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI_LEVEL: rsi=54.5 above_sma=False bands=[30.0,70.0] (rsi=54.5 above_sma=False regime=MEAN_REVERTING) |
| 19:20:07 | FILTER | ⚡ PAPER_SPEED ALTUSDT: RSI_LEVEL: rsi=39.1 above_sma=False bands=[48.0,52.0] (rsi=39.1 above_sma=False regime=TRENDING) |
| 19:20:07 | FILTER | ⚡ PAPER_SPEED FIDAUSDT: RSI_LEVEL: rsi=38.8 above_sma=False bands=[48.0,52.0] (rsi=38.8 above_sma=False regime=TRENDING) |
| 19:20:10 | FILTER | ⚡ PAPER_SPEED GENIUSUSDT: RSI_LEVEL: rsi=43.3 above_sma=False bands=[48.0,52.0] (rsi=43.3 above_sma=False regime=TRENDING) |
| 19:20:11 | FILTER | ⚡ PAPER_SPEED ALLOUSDT: RSI_LEVEL: rsi=37.8 above_sma=False bands=[48.0,52.0] (rsi=37.8 above_sma=False regime=TRENDING) |
| 19:20:19 | SIGNAL | ⚡ PAPER_SPEED fallback UUSDT: SHORT entry=1.0007 rsi=100.0 |

---
*EOW Quant Engine V4.0 — 2026-05-22 19:21 UTC*