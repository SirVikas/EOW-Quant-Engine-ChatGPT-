# 📋 XTE CAMPAIGN OPERATIONS RUNBOOK — GAP-R15

**Status:** Operational process (no code) — the institutional runbook the audit
flagged as the biggest *practical* gap.
**Engine build:** APP_VERSION 1.95.2
**Audience:** operator + approver. **Purpose:** execute the evidence campaign and
the advisor lifecycle *consistently*, end to end.

> Context: after rounds 1–3, the architecture is complete and the remaining gaps
> are **evidence**, not code. This runbook is how the evidence gets generated and
> acted on. Per the institutional verdict: **stop building, run the campaign.**

---

## 0. PRE-FLIGHT

- [ ] Confirm engine is in **paper mode** (`TRADE_MODE`), not live capital.
- [ ] Confirm current build ≥ 1.95.2 (`GET /api/version`).
- [ ] Confirm baseline tests green (`python tests/test_live_process_access.py`).
- [ ] Note the start equity / trade count for a clean campaign window.

---

## 1. STEP 1 — ENABLE THE CAMPAIGN

Set environment variables (do **not** edit code defaults), then restart the engine:

```bash
export XTE_OBSERVE_ENABLED=True          # score open positions each tick (observe-only)
export XTE_OBSERVE_PATH_ENABLED=True     # capture per-tick path → path-accurate proof
export EXIT_COORDINATOR_SHADOW_ENABLED=True   # collect exit-authority parity data in parallel
# (optional) tune the success bar:
# export XTE_SUCCESS_MIN_UPLIFT_PCT=3.0
# export XTE_SUCCESS_MIN_PROTECT_PRECISION=50.0
```

These are observation-only and revert instantly (Step 6). They do **not** change
any trade decision.

---

## 2. STEP 2 — CONFIRM IT IS RUNNING

```
GET /api/truth/xte/observation   → status.observe_enabled == true
GET /api/exit/coordinator        → transitions_observed increasing
GET /api/governance/lifecycle    → advisors.XTE.stage == "OBSERVE"
```

If `observe_enabled` is false, the env did not load — re-check Step 1 + restart.

---

## 3. STEP 3 — MONITOR PROGRESS (toward 500)

Poll periodically:

```
GET /api/truth/xte/observation → status.calibration_progress_pct
GET /api/governance/lifecycle  → advisors.XTE.campaign.{samples,progress_pct,complete}
```

- The lifecycle **auto-fires a completion trigger** at 500 (logged:
  `[LIFECYCLE] XTE CAMPAIGN COMPLETE … review triggered`) and stamps
  `completion_ts`.
- Let the campaign run until `complete == true`. More samples = stronger verdict.

---

## 4. STEP 4 — REVIEW THE VERDICT

```
GET /api/truth/xte/validation
```

Read:
- `verdict.status` → `CANDIDATE` | `REJECT` | `INSUFFICIENT_DATA`
- `verdict.economic_uplift_pct` vs `success_criteria.min_uplift_pct` (default 3%)
- `verdict.protect_precision_pct` vs `min_protect_precision_pct` (default 50%)
- `verdict.economic_basis` → `path-accurate` (preferred) or `bounded-upper-estimate`
- `calibration` (score buckets), `counterfactual`, `path_counterfactual` for detail

---

## 5. STEP 5 — DECISION TREE (promote / reject)

```
verdict.status == INSUFFICIENT_DATA  → keep running (back to Step 3)

verdict.status == REJECT             → DO NOT promote.
   • XTE does not clear the economic bar. Redesign exit features (not reweight).
   • Record the negative result in IMRAF. Campaign closed.

verdict.status == CANDIDATE          → eligible to advance, but NOT to act yet:
   1. Approver records the promotion (governance, audited):
         learning_lifecycle.approve("XTE", "ADVISE", approver="<name>", note="<verdict ref>")
      → moves XTE OBSERVE→…→ADVISE (acting stages require this explicit approval).
   2. ADVISE means "logged advisory compared to live", still NOT modifying exits.
   3. To let XTE actually affect exits, open a dedicated ADR-gated Exit
      Coordinator X3 FTD first (single exit author) — see
      UNIFIED_EXIT_AUTHORITY_BLUEPRINT.md (X3). XTE acting before X3 is prohibited.
```

**Hard rule:** lifecycle never auto-enters an acting stage. A human approval +
(for live exit influence) X3 + ADR are mandatory. This is the safety boundary.

---

## 6. STEP 6 — ROLLBACK (any time)

```bash
export XTE_OBSERVE_ENABLED=False
export XTE_OBSERVE_PATH_ENABLED=False
export EXIT_COORDINATOR_SHADOW_ENABLED=False
# restart
```

No live state depends on these — disabling is an instant no-op. The archived
evidence (`reports/xte_observations/*.jsonl`) is retained.

---

## 7. GOVERNANCE & TRACEABILITY

- **Who approves promotion:** the designated approver, via
  `learning_lifecycle.approve(...)` — every approval is persisted with approver +
  timestamp in `reports/governance/learning_lifecycle.json`.
- **What to record in IMRAF:** campaign window, sample count, verdict, decision
  (promote/reject), approver. So a future session can answer *"did XTE earn its
  acting stage, and on what evidence?"*
- **Artifacts:** observation archive, path archive, exit-coordinator parity stats,
  lifecycle state — all forensic, all `reports/`.

---

## 8. ONE-PAGE CHECKLIST

```
[ ] 1. export XTE_OBSERVE_ENABLED / XTE_OBSERVE_PATH_ENABLED / EXIT_COORDINATOR_SHADOW_ENABLED = True ; restart
[ ] 2. confirm observe_enabled == true
[ ] 3. monitor calibration_progress_pct until complete (500)
[ ] 4. read /api/truth/xte/validation verdict
[ ] 5. CANDIDATE → approve→ADVISE (+ X3 FTD before acting) | REJECT → redesign | else keep running
[ ] 6. rollback = flags False (if needed)
[ ] 7. record campaign + verdict + decision in IMRAF
```

---

*End of XTE_CAMPAIGN_OPERATIONS_RUNBOOK. This closes GAP-R15. The remaining gaps
(R1–R14) are resolved by executing this runbook — they are evidence/authority
gaps, not code gaps.*
