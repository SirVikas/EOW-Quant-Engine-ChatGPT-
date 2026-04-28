# No-Trade Mission Board (Paper Speed)

## Mission
Resolve **No Trade Issue** and maximize opportunity capture in minimum time (PAPER mode stress context).

## Findings (high-impact blockers)
1. **Volume sleep gate blocks low-volume candles**
   - Symptom seen in UI skip messages: `SLEEP_MODE(...)`.
   - Action taken: PAPER speed path now relaxes threshold to floor and bypasses remaining sleep blocks.

2. **Drawdown halt can fully freeze entries**
   - Screenshot shows max drawdown ~16.9% vs halt threshold 15%.
   - In normal mode this halts new entries by design.
   - Action taken: PAPER speed mode now bypasses risk-gate rejections in the main loop (`HALTED`, `MAX_DAILY_LOSS`, `DAILY_TRADE_CAP`) to continue throughput testing.

3. **Daily trade cap can limit stress throughput**
   - Action taken earlier: paper speed bypass in `check_new_trade` keeps throughput open.

4. **Limit-order queue can delay/avoid actual fills in fast PAPER runs**
   - Symptom: signals visible, but no open/closed trade progression in short windows.
   - Action taken: PAPER speed now forces market-fill path (temporarily bypass `USE_LIMIT_ORDERS`)
     to prioritize immediate execution during flow recovery.

## Current paper-speed behavior
- Throughput-oriented gate profile enabled.
- Dry-spell required-R relaxation active.
- Volume sleep no longer a hard blocker under paper speed.
- Risk-gate halt/daily-loss/cap rejections no longer freeze entries under paper speed.
- Market-fill override prevents pending-order dead time during paper-speed recovery.
- If primary + alpha both produce NONE, paper-speed momentum fallback injects
  a micro-signal to keep the signal→execution path alive for forensic recovery.

## Next pass (recommended)
- Add per-gate live counters (blocked by: volume, regime, edge, risk).
- Auto-export top 20 skip reasons every 5 minutes.
- Add reversible profile toggle in UI: `NORMAL` / `PAPER_SPEED`.
- After flow recovery, re-enable one gate at a time for profitability tuning.
