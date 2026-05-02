# EOW Quant Engine — Performance Report

**Generated:** 2026-05-02 02:35 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **271 trades** with a net **LOSS** of **-153.20 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $846.80 USDT |
| Net PnL | -153.1955 USDT |
| Win Rate | 42.1% |
| Profit Factor | 0.378 |
| Sharpe Ratio | -2.795 |
| Sortino Ratio | -2.309 |
| Calmar Ratio | -0.834 |
| Max Drawdown | 17.08% |
| Risk of Ruin | 100.00% |
| Total Fees | 52.9106 USDT |
| Total Slippage | 1.7563 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -98.5286 USDT (before all costs)
- **Fees deducted:** -52.9106 USDT
- **Slippage deducted:** -1.7563 USDT
- **Net PnL (bankable):** -153.1955 USDT

### 2.2 Trade Statistics

- Avg win: +0.8176 USDT
- Avg loss: -1.5695 USDT
- Profit factor: 0.378

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-15.3%** | **-2.79** | **-2.31** | **17.1%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 02:31:01 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:31:01 | SIGNAL | 🔄 AIE INVERSE → SHORT BTCUSDT |
| 02:31:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:31:01 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:31:01 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3269 |
| 02:31:01 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:31:01 | SIGNAL | 🔄 AIE INVERSE → SHORT TRXUSDT |
| 02:31:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:31:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:31:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2295.4300 |
| 02:31:01 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:31:01 | SIGNAL | 🔄 AIE INVERSE → LONG ETHUSDT |
| 02:31:01 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:31:01 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:31:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: SHORT entry=0.0099 |
| 02:31:01 | SIGNAL | 🔔 Signal SHORT PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:31:02 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:31:02 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:31:02 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: SHORT entry=83.9000 |
| 02:31:02 | SIGNAL | 🔔 Signal SHORT SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:31:02 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:31:02 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:31:02 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3845 |
| 02:31:02 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:31:03 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:31:03 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:31:03 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5430 |
| 02:31:03 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:31:03 | SIGNAL | 🔄 AIE INVERSE → SHORT PENDLEUSDT |
| 02:31:14 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:31:14 | SIGNAL | 📈 STREAK ORCAUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:31:14 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=1.9810 |
| 02:31:14 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:00 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:00 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1552 |
| 02:32:00 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:00 | SIGNAL | 🔄 AIE INVERSE → SHORT MEGAUSDT |
| 02:32:00 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:00 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0433 |
| 02:32:00 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:00 | SIGNAL | 🔄 AIE INVERSE → SHORT BIOUSDT |
| 02:32:00 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:00 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0654 |
| 02:32:00 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:00 | SIGNAL | 🔄 AIE INVERSE → SHORT CHIPUSDT |
| 02:32:00 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:00 | SIGNAL | 📈 STREAK BNBUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:00 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=615.6800 |
| 02:32:00 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:01 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:01 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:01 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3269 |
| 02:32:01 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:01 | SIGNAL | 🔄 AIE INVERSE → SHORT TRXUSDT |
| 02:32:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=78268.0300 |
| 02:32:01 | SIGNAL | 🔔 Signal SHORT BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:01 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:01 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:01 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2295.4800 |
| 02:32:01 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:01 | SIGNAL | 🔄 AIE INVERSE → SHORT ETHUSDT |
| 02:32:01 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:01 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:01 | FILTER | ⚡ PAPER_SPEED bypass PENGUUSDT: SLEEP_MODE(vol=46705=6%_of_avg=723636,min=10%[base=45%×0.20]) |
| 02:32:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0099 |
| 02:32:01 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:02 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:02 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:02 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: SHORT entry=1.5410 |
| 02:32:02 | SIGNAL | 🔔 Signal SHORT PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:02 | SIGNAL | 🔄 AIE INVERSE → LONG PENDLEUSDT |
| 02:32:04 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:04 | SIGNAL | 📈 STREAK ORCAUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:04 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=1.9780 |
| 02:32:04 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:04 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:04 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:04 | FILTER | ⚡ PAPER_SPEED bypass XRPUSDT: SLEEP_MODE(vol=2587=6%_of_avg=43229,min=10%[base=45%×0.20]) |
| 02:32:04 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: SHORT entry=1.3844 |
| 02:32:04 | SIGNAL | 🔔 Signal SHORT XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:32:08 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:32:08 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:32:08 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=83.9100 |
| 02:32:08 | SIGNAL | 🔔 Signal LONG SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:01 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:01 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: SHORT entry=0.1547 |
| 02:33:01 | SIGNAL | 🔔 Signal SHORT MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:01 | SIGNAL | 🔄 AIE INVERSE → LONG MEGAUSDT |
| 02:33:01 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:01 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: LONG entry=0.0100 |
| 02:33:01 | SIGNAL | 🔔 Signal LONG PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:01 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:01 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0654 |
| 02:33:01 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:01 | SIGNAL | 🔄 AIE INVERSE → SHORT CHIPUSDT |
| 02:33:01 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=78289.8500 |
| 02:33:01 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:01 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:01 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0431 |
| 02:33:01 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:01 | SIGNAL | 🔄 AIE INVERSE → LONG BIOUSDT |
| 02:33:01 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:01 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:01 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=83.9300 |
| 02:33:01 | SIGNAL | 🔔 Signal LONG SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:02 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:02 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:02 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: LONG entry=1.3854 |
| 02:33:02 | SIGNAL | 🔔 Signal LONG XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:02 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:02 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:02 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2296.2900 |
| 02:33:02 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:02 | SIGNAL | 🔄 AIE INVERSE → SHORT ETHUSDT |
| 02:33:02 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:02 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:02 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: SHORT entry=1.5390 |
| 02:33:02 | SIGNAL | 🔔 Signal SHORT PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:02 | SIGNAL | 🔄 AIE INVERSE → LONG PENDLEUSDT |
| 02:33:04 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:04 | SIGNAL | 📈 STREAK ORCAUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:04 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=1.9750 |
| 02:33:04 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:04 | SIGNAL | 🔄 AIE INVERSE → LONG ORCAUSDT |
| 02:33:04 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:04 | SIGNAL | 📈 STREAK BNBUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:04 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=615.8800 |
| 02:33:04 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:04 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:33:04 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:33:04 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3270 |
| 02:33:04 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:33:04 | SIGNAL | 🔄 AIE INVERSE → SHORT TRXUSDT |
| 02:34:05 | SIGNAL | ⚡ DTP CHIPUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:05 | SIGNAL | 📈 STREAK CHIPUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:05 | SIGNAL | ⚡ PAPER_SPEED fallback CHIPUSDT: LONG entry=0.0655 |
| 02:34:05 | SIGNAL | 🔔 Signal LONG CHIPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:05 | SIGNAL | 🔄 AIE INVERSE → SHORT CHIPUSDT |
| 02:34:05 | SIGNAL | ⚡ DTP BNBUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:05 | SIGNAL | 📈 STREAK BNBUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:05 | SIGNAL | ⚡ PAPER_SPEED fallback BNBUSDT: LONG entry=615.8800 |
| 02:34:05 | SIGNAL | 🔔 Signal LONG BNBUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:05 | SIGNAL | ⚡ DTP MEGAUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:05 | SIGNAL | 📈 STREAK MEGAUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:05 | SIGNAL | ⚡ PAPER_SPEED fallback MEGAUSDT: LONG entry=0.1554 |
| 02:34:05 | SIGNAL | 🔔 Signal LONG MEGAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:05 | SIGNAL | 🔄 AIE INVERSE → SHORT MEGAUSDT |
| 02:34:05 | SIGNAL | ⚡ DTP ETHUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:05 | SIGNAL | 📈 STREAK ETHUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:05 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2296.6100 |
| 02:34:05 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:05 | SIGNAL | 🔄 AIE INVERSE → SHORT ETHUSDT |
| 02:34:05 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:05 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:05 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=78296.2800 |
| 02:34:05 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:05 | SIGNAL | ⚡ DTP PENGUUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:05 | SIGNAL | 📈 STREAK PENGUUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:05 | SIGNAL | ⚡ PAPER_SPEED fallback PENGUUSDT: SHORT entry=0.0100 |
| 02:34:05 | SIGNAL | 🔔 Signal SHORT PENGUUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:05 | SIGNAL | ⚡ DTP XRPUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:05 | SIGNAL | 📈 STREAK XRPUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:05 | SIGNAL | ⚡ PAPER_SPEED fallback XRPUSDT: LONG entry=1.3854 |
| 02:34:05 | SIGNAL | 🔔 Signal LONG XRPUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:06 | SIGNAL | ⚡ DTP SOLUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:06 | SIGNAL | 📈 STREAK SOLUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:06 | SIGNAL | ⚡ PAPER_SPEED fallback SOLUSDT: LONG entry=83.9500 |
| 02:34:06 | SIGNAL | 🔔 Signal LONG SOLUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:06 | SIGNAL | ⚡ DTP TRXUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:06 | SIGNAL | 📈 STREAK TRXUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:06 | FILTER | ⚡ PAPER_SPEED bypass TRXUSDT: SLEEP_MODE(vol=1689=7%_of_avg=22955,min=10%[base=45%×0.20]) |
| 02:34:06 | SIGNAL | ⚡ PAPER_SPEED fallback TRXUSDT: LONG entry=0.3270 |
| 02:34:06 | SIGNAL | 🔔 Signal LONG TRXUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:06 | SIGNAL | 🔄 AIE INVERSE → SHORT TRXUSDT |
| 02:34:07 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:07 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:07 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0430 |
| 02:34:07 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:07 | SIGNAL | 🔄 AIE INVERSE → LONG BIOUSDT |
| 02:34:07 | SIGNAL | ⚡ DTP ORCAUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:07 | SIGNAL | 📈 STREAK ORCAUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:07 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=1.9740 |
| 02:34:07 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:07 | SIGNAL | 🔄 AIE INVERSE → LONG ORCAUSDT |
| 02:34:15 | SIGNAL | ⚡ DTP PENDLEUSDT: tier=TIER_3 af=TIGHTEN score_min=0.560 vol_mult=0.20× fee_tol=0.10 |
| 02:34:15 | SIGNAL | 📈 STREAK PENDLEUSDT: COLD len=14 score_adj=+0.05 → eff_min=0.610 |
| 02:34:15 | SIGNAL | ⚡ PAPER_SPEED fallback PENDLEUSDT: LONG entry=1.5420 |
| 02:34:15 | SIGNAL | 🔔 Signal LONG PENDLEUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 02:34:15 | SIGNAL | 🔄 AIE INVERSE → SHORT PENDLEUSDT |

---
*EOW Quant Engine V4.0 — 2026-05-02 02:35 UTC*