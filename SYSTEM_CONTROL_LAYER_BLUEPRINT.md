# 🏛️ SYSTEM_CONTROL_LAYER_BLUEPRINT — GAP-A4

**Status:** Architectural study — *design only, no implementation*
**Engine build:** APP_VERSION 1.95.0
**Scope:** the system-wide arbiter question the audit left open — *"Risk, Truth,
Capital, RL, future AMIL, Governance — who arbitrates?"*
**Relation:** `UNIFIED_EXIT_AUTHORITY_BLUEPRINT.md` solves *exit* control; this
addresses *system* control one level up.

---

## 1. THE QUESTION

GAP-A4: there is no single layer that arbitrates across subsystems when they
disagree. Today each domain owns its slice and they compose by call-ordering and
multipliers, not by an explicit arbiter:

| Domain | Owner today | Output |
|--------|-------------|--------|
| Entry approval | `ExecutionOrchestrator.run_cycle` | accept/reject/size (sole entry authority) |
| Risk | `risk_engine` + `risk_controller` | hard caps, halts |
| Capital | `capital_allocator/scaler/concentrator` | size multipliers |
| RL | `rl_engine` | block toxic ctx + conf boost |
| Truth | ETE/XTE/AAP | **observation only (mute)** |
| Exit | `risk_controller` + `trade_manager` | SL/TP writes (2 authors, 1 executor) |
| Governance | Guardian/EGI/lifecycle | advisory/parametric |

**Finding:** entry has a sole authority; exit has a sole *executor* but no sole
*author*; and **across domains there is no arbiter at all** — composition is
implicit. This is acceptable while Truth is mute, but becomes a hazard the moment
any Truth/AMIL signal is allowed to act (it would be a new, uncoordinated voice).

---

## 2. DESIGN PRINCIPLE — ARBITER, NOT MEGA-CONTROLLER

A system control layer must **not** become a monolith that re-implements each
domain. It is a thin **arbiter** that:
1. receives each domain's *typed intent* (allow/deny/size/exit/hold + reason +
   confidence + lifecycle stage),
2. applies an explicit, auditable **precedence policy**, and
3. emits one decision + one rationale record — never bypassing a domain's hard
   safety floor.

```
   Risk ─┐
 Capital ─┤
     RL ─┤        ┌────────────────────────┐      ┌─────────────────┐
  Truth ─┼─ Intent│  SYSTEM ARBITER        │ ───► │ Domain executors │
   Exit ─┤  bundle│  precedence + invariants│      │ (orch / risk_ctrl│
 Govern ─┘        │  + one rationale record │      │  / allocator …)  │
                  └────────────────────────┘      └─────────────────┘
```

---

## 3. PRECEDENCE POLICY (proposed, hard→soft)

1. **Hard safety (non-overridable):** risk_engine caps, equity floor, hard
   limits, paper-trading safeguards. No other domain can override these.
2. **Governance gates:** lifecycle stage — a domain's signal may only act at the
   strength its `LearningLifecycle` stage permits (OBSERVE→none, ADVISE→nudge,
   GATE→block, AUTHORITY→size). Truth/AMIL enter here, never above safety.
3. **RL/exit terminal actions:** toxic-context block, terminal exits.
4. **Capital sizing:** multiplier composition (already legible per FTD-092 §1.5).
5. **Soft advisories:** Truth nudges within their lifecycle-permitted band.

**Invariant:** no domain below "hard safety" can loosen a constraint set above it.
Every arbitration emits `(domain, intent, weight, applied?, reason)`.

---

## 4. WHY NOT BUILD IT NOW

- **It must not act before its inputs are trustworthy.** Truth/AMIL are still in
  OBSERVE (lifecycle). An arbiter that admits mute signals adds nothing; one that
  admits unvalidated signals is dangerous.
- **The exit sub-problem comes first.** The Exit Coordinator (X1–X4) is the
  concrete, scoped prerequisite; the system arbiter generalizes that pattern only
  after it is proven on exits.
- **Dependency order:**
  `LearningLifecycle (built) → Exit Coordinator X3 (blocked) → System Arbiter (this)`.

---

## 5. ROADMAP

| Phase | Scope | Gate |
|------|------|------|
| S0 | LearningLifecycle governs advisor stages | ✅ built (GAP-H1) |
| S1 | Exit Coordinator becomes sole exit author (X3) | blocked: shadow parity + ADR |
| S2 | Define typed cross-domain Intent + rationale schema | after S1 |
| S3 | System Arbiter (shadow) — recompute + parity vs current implicit composition | after S2 |
| S4 | System Arbiter (authority) | parity proof + ADR |

---

## 6. ANSWER TO "WHO IS THE FINAL BOSS?"

- **Today:** for entries, `ExecutionOrchestrator`; for exit execution,
  `risk_controller._close_position`; **across domains, no one** — composition is
  implicit, and hard safety (risk_engine) is the only universal veto.
- **Designed end-state:** a thin **System Arbiter** governed by `LearningLifecycle`,
  sitting above the domains and below hard safety, emitting one auditable decision.
  It is the *last* thing to build — only after exit unification and after Truth
  signals have earned an acting lifecycle stage.

---

*End of SYSTEM_CONTROL_LAYER_BLUEPRINT. Design-only; implementation is gated behind
the Exit Coordinator and validated Truth signals.*
