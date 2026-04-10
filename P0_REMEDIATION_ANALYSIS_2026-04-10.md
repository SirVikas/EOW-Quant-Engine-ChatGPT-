# P0 Remediation Analysis (Independent) — April 10, 2026

## Scope
This memo provides an independent technical analysis of the two P0 items from the forensic audit:

1. API security hardening (AuthN/AuthZ + CORS lockdown).
2. Trading expectancy hardening (deterministic backtest + realistic fills to reduce backtest/live divergence).

The analysis is based on direct repository review and comparative design choices.

---

## Current-State Validation (Repository Findings)

### P0-A: Control-plane security exposure is real
Observed in `main.py`:

- Global permissive CORS is enabled (`allow_origins=["*"]`, methods/headers wildcard).
- High-risk mutating endpoints have no authentication/authorization:
  - `POST /api/mode/{mode}`
  - `POST /api/import-dna`
  - `POST /api/emergency-close`
  - `POST /api/resume`

Operational impact:

- Any network path to this service can invoke control actions.
- In a browser context, wildcard CORS makes accidental/malicious cross-origin invocations easier.
- There is no role separation for emergency operations vs routine operations.

### P0-B: Backtest/live realism gap remains material
Observed in engine path (`main.py`, `core/data_lake.py` and trading flow):

- Live strategy decisions include practical constraints (fees, slippage estimate, throttle, limit-order logic).
- Backtest methodology is not isolated as a deterministic execution engine with explicit fill policy and event ordering.
- Persistence focuses on ingestion and closed-trade storage; no canonical replayable event ledger exists for deterministic simulation.

Operational impact:

- Calibration and promotion logic can be overly optimistic if fill assumptions are not exchange-realistic.
- Profit factor can degrade live despite good headline win-rate when cost/slippage tails are underestimated.

---

## Comparative Design Study

## A) AuthN/AuthZ + CORS (P0)

### Option A1 — Shared static API key header only
- Pros: fastest implementation.
- Cons: no principal identity, weak revocation, poor auditability, no fine-grained RBAC.
- Verdict: insufficient for production control plane.

### Option A2 — JWT Bearer with role claims + short-lived tokens
- Pros: explicit identity, role-based decisions at endpoint level, good observability/audit trails, industry-standard gateway compatibility.
- Cons: key management and token issuing flow required.
- Verdict: best tradeoff for this codebase now.

### Option A3 — mTLS-only service-to-service trust
- Pros: strong transport identity.
- Cons: burdensome for human operator workflows; still needs app-level authorization model.
- Verdict: valuable later for private control channels, not a standalone immediate fix.

**Selected approach:** A2 now, optionally layered with A3 later.

#### P0-A Implementation blueprint
1. Add security settings in `config.py`:
   - `ALLOWED_ORIGINS` (explicit list)
   - `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_SECRET`, `JWT_ALGO`, `JWT_EXP_MIN`
   - `AUTH_ENABLED` + emergency break-glass flag.
2. Create `core/security.py`:
   - token validation
   - role extraction
   - dependency guards (`require_role("operator")`, `require_role("admin")`).
3. Protect endpoints:
   - `/api/mode`, `/api/import-dna`, `/api/resume` => `operator` or `admin`
   - `/api/emergency-close` => `admin` only.
4. Replace wildcard CORS with strict configured origin list.
5. Add immutable audit log entries for all privileged invocations (who/what/when/result).
6. Add deny-by-default behavior when auth config is missing in LIVE mode.

Security acceptance criteria:
- Anonymous calls to privileged endpoints return 401.
- Valid token with insufficient role returns 403.
- Only configured origins receive CORS allow response.
- All privileged actions leave a signed/auditable trail.

---

## B) Deterministic Backtest + Realistic Fill Model (P0)

### Option B1 — Continue heuristic PnL simulation
- Pros: minimal engineering effort.
- Cons: cannot quantify execution bias; weak reproducibility.
- Verdict: not acceptable for expectancy recovery.

### Option B2 — Event-driven deterministic simulator with configurable fill model
- Pros: reproducible runs, explicit latency/depth/slippage assumptions, apples-to-apples strategy comparison.
- Cons: moderate build complexity.
- Verdict: best immediate ROI and scientific validity.

### Option B3 — Hybrid paper-trading-only calibration
- Pros: realistic exchange behavior.
- Cons: slow learning cycle, expensive time-to-signal, hard scenario coverage.
- Verdict: useful validation phase after B2 foundation.

**Selected approach:** B2 as primary engine, then validate top cohorts via B3.

#### P0-B Implementation blueprint
1. Add `core/backtest_engine.py` (deterministic event loop):
   - candle/tick replay with stable ordering
   - deterministic random seed hooks (where stochastic components exist)
   - explicit order lifecycle states.
2. Add `core/fill_model.py`:
   - latency model (fixed + percentile profile)
   - slippage model as function of volatility + spread proxy + order aggressiveness
   - partial fill/depth constraints (parameterized by notional bucket).
3. Add execution parity constraints:
   - same fee schedule and risk filters as live code path
   - same throttles, cooldowns, and mode transitions where relevant.
4. Add calibration suite:
   - compare historical paper/live fills vs simulated fills
   - optimize slippage and latency coefficients by symbol/regime bucket.
5. Add reliability tooling:
   - deterministic regression snapshots for PF, expectancy, MAE/MFE, turnover, fee drag.

Expectancy acceptance criteria:
- Re-running same dataset/config yields byte-identical trade sequence.
- Out-of-sample PF improves above 1.0 in selected promoted strategies.
- Simulated-vs-paper execution error stays within predefined tolerance bands.

---

## Estimated Implementation Timeline

Assumes one primary engineer + one reviewer, normal CI cadence.

### Week 1 (Days 1–5): Security hardening to production-safe baseline
- Day 1: Config + security module scaffolding, JWT validation, role primitives.
- Day 2: Endpoint protection + strict CORS implementation.
- Day 3: Audit logging + LIVE-mode fail-closed checks.
- Day 4: Unit/integration tests for 401/403/role matrix.
- Day 5: Staging verification, operational runbook, rollback plan.

**Deliverable:** Unauthorized control-plane risk reduced to near-zero for exposed endpoints.

### Week 2 (Days 6–10): Deterministic backtest core
- Day 6–7: Event replay engine and deterministic order lifecycle.
- Day 8: Fill model v1 (latency, slippage, partial fills).
- Day 9: Parity checks against live risk/fee controls.
- Day 10: Baseline calibration report and regression fixtures.

**Deliverable:** Reproducible expectancy measurements with explicit cost realism.

### Week 3 (Days 11–15): Calibration and rollout gating
- Day 11–12: Parameter fitting by symbol/regime buckets.
- Day 13: Out-of-sample validation, PF/expectancy gate definitions.
- Day 14: Promotion policy update for genome strategy selection.
- Day 15: Go/no-go review with performance and safety scorecard.

**Deliverable:** Strategy promotion based on realistic execution-adjusted profitability.

---

## Recommended Execution Order

1. Ship P0-A first (security): immediate catastrophic-risk reduction.
2. Ship P0-B foundation next (deterministic simulator).
3. Enforce promotion gates only after calibrated fill realism is validated.

This order minimizes downside risk while restoring trustworthy expectancy metrics.
