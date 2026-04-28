# NO TRADE Deep Dive — Gate Map and Throughput Unblock

## Scope
Focused forensic pass over the live signal→execution path in `main.py` (gate chain), plus risk/volume behavior previously observed in runtime reports.

## High-probability trade blockers in chain
The following gates can independently return before order open:
- volume sleep
- sector guard
- risk engine gate
- market structure gate
- edge engine / adaptive edge engine
- regime stability gate
- profit guard hard stop
- calibration mode lock
- fee gate / learned cost gate
- signal filter / strategy gate / score gate / decay gate
- RR gate / smart-fee gate / EV gate / EV-confidence gate
- drawdown controller / allocation / consistency / execution orchestrator
- final edge decision

## Confirmed root cause (forensics)
- `scripts/pipeline_break_forensics.py` showed scan + gate path as healthy, but
  cycle result was repeatedly blocked at concentrator stage:
  `CONCENTRATE_REJECT(rank=0.493 below all bands)`.
- This means trades were reaching orchestrator and rank/competition passed,
  but were dropped before pre-trade gate/execution due to rank band floor.

## Unblock strategy applied
For PAPER speed runs, engine now uses a **single bypass variable** in the on-tick pipeline:
- `_paper_speed = (TRADE_MODE == PAPER and PAPER_SPEED_MODE)`
- `_bypass_all_gates = cfg.BYPASS_ALL_GATES or _paper_speed`

All gate checks in the main chain now reference `_bypass_all_gates`.
This ensures the flow is not blocked by one missed conditional during paper stress mode.

Additional concentrator fix applied:
- In `core/profit/capital_concentrator.py`, PAPER_SPEED now converts
  concentrator reject (`ok=False`) into `SAFE_FALLBACK` (base allocation)
  instead of hard reject.

## Expected impact
- Signals that previously died in intermediate gates can now proceed to execution path.
- Combined with market-fill override for PAPER speed, trade-start probability is maximized.

## Next calibration plan (after flow starts)
1. Keep PAPER speed for 10-15 min and capture skip/open metrics.
2. Re-enable one gate cluster at a time:
   - Risk + DD
   - Cost/Fee gates
   - Score/RR/EV gates
3. Stop at first cluster that re-introduces no-trade; tune there.
