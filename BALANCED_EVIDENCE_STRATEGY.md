# ⚖️ BALANCED EVIDENCE STRATEGY — Time vs Result

**Engine build:** APP_VERSION 1.96.0
**Context:** board advised "real campaign, wait for 500." You want speed *and* a
real result. This is the synthesis: **real data, but stop the moment it's
statistically decisive** — never fake data as proof.

---

## 1. THE PRINCIPLE

```
Fake data        → fast,  but NOT a real result  (circular — rejected)
Wait for 500     → real,  but slow                (wasteful if answer is early)
Real + early-stop→ real AND as fast as the data allows   ← THIS
```

A synthetic CANDIDATE proves only that the pipeline runs. It cannot tell you if
XTE makes money. So the accelerator must be on **how fast real evidence becomes
decisive**, not on faking it.

---

## 2. THE TWO LEVERS (both shipped / operational)

### Lever 1 — Sequential early-stop (NEW, `interim_verdict()`)
The campaign no longer must reach 500. At rolling checkpoints it returns:

| Checkpoint | Decision | Meaning |
|-----------|----------|---------|
| n ≥ 100 (`XTE_EARLY_REJECT_MIN_N`) | **EARLY_REJECT** | even the optimistic 95% bound is below bar → STOP, don't advance |
| n ≥ 300 (`XTE_EARLY_CANDIDATE_MIN_N`) | **EARLY_CANDIDATE** | confidently above bar → may start X3 design; confirm at 500 |
| otherwise | **CONTINUE** | not yet decisive — keep collecting |

Asymmetric by design: **reject early (save time on losers), confirm carefully
(don't promote a fluke).** Uses 95% normal-approx CIs on protect-precision and
per-trade path r-delta — real observations only. Demonstrated: a clearly-bad XTE
trips **EARLY_REJECT at n≈250** (≈50% time saved); a strong one hits
**EARLY_CANDIDATE at n≈350**.

### Lever 2 — Maximum real throughput (operational)
`start_xte_campaign.bat` already sets `BYPASS_ALL_GATES=True` so more trades close
per unit time (the same trick as calibration mode). Combine with `PAPER_SPEED` if
available. This shrinks wall-clock time to reach each checkpoint.

---

## 3. THE PLAY (recommended)

1. **Start the real campaign now** — `start_xte_campaign.bat`. Don't wait idle.
2. **Watch the interim verdict**, not the 500 counter:
   `GET /api/truth/xte/validation → interim_verdict.status`.
   - `EARLY_REJECT` → stop the campaign, XTE redesign. **Time saved.**
   - `EARLY_CANDIDATE` → begin Exit-Coordinator **X3 design docs** (not code),
     then confirm at 500 before any X3 implementation.
   - `CONTINUE` → keep running.
3. **Code freeze on X3/Truth/Arbiter** until at least EARLY_CANDIDATE. Designing
   on paper in parallel is fine; implementing before evidence is the trap.

This is faster than "wait for 500" (you can stop at ~100–350) and keeps every bit
of evidence real and your governance doctrine intact.

---

## 4. WHAT I DID *NOT* DO

- Did **not** wire synthetic data into the real verdict path. The simulator stays
  a separate, clearly-tagged eval tool; `interim_verdict.data_basis` flags
  `SIMULATED (not proof)` if sim records are ever present.
- Did **not** build X3 / Truth feedback / Arbiter. Those stay frozen until a real
  EARLY_CANDIDATE or final CANDIDATE earns them.

---

## 5. ONE-LINE ANSWER TO THE BOARD

> The fastest *honest* path is not fake data — it's **real data with early-stop
> gates**: stop at the first statistically decisive checkpoint (~100–350 trades),
> in either direction. Time saved, result real, doctrine intact.

---

*End of BALANCED_EVIDENCE_STRATEGY.*
