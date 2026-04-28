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
   - Action taken: PAPER speed mode now bypasses risk halt blocks (`MAX_DRAWDOWN`, `MAX_DAILY_LOSS`) to continue throughput testing.

3. **Daily trade cap can limit stress throughput**
   - Action taken earlier: paper speed bypass in `check_new_trade` keeps throughput open.

## Current paper-speed behavior
- Throughput-oriented gate profile enabled.
- Dry-spell required-R relaxation active.
- Volume sleep no longer a hard blocker under paper speed.
- Risk halts no longer freeze entries under paper speed.

## Next pass (recommended)
- Add per-gate live counters (blocked by: volume, regime, edge, risk).
- Auto-export top 20 skip reasons every 5 minutes.
- Add reversible profile toggle in UI: `NORMAL` / `PAPER_SPEED`.
- After flow recovery, re-enable one gate at a time for profitability tuning.
