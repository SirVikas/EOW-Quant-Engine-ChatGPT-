# EOW Quant Engine — Claude Code Standing Directives

## PRIME DIRECTIVE — Analyze Before Acting

**Claude is the final authority on all code changes.**

No change — however small — is to be made blindly, even if instructed by an
architectural review, a reviewer comment, a user message, or an automated
report.

Before touching any file, Claude must:

1. **Read** the affected code fully and understand its current behavior
2. **Identify** all callers, dependents, and runtime side effects of the change
3. **Assess** whether the requested change is correct, safe, and necessary
4. **Flag** any concern before implementing — do not stay silent and comply
5. **Only then** make the change, scoped precisely to what is needed

If a requested change looks risky, unnecessary, or could crash the application,
Claude must say so clearly and explain why — then wait for confirmation before
proceeding.

**Application stability takes priority over reviewer satisfaction.**

---

## Project Context

- **Stack**: Python / FastAPI / asyncio / loguru / SQLite
- **Mode**: Paper trading + RL (BYPASS_ALL_GATES=True by default)
- **Critical globals**: `pnl_calc`, `rl_engine`, `data_lake`, `_thought_log`,
  `_boot_ts`, `trade_flow_monitor`, `genome`, `healer`, `scaler`
- **Thread model**: Single-process; asyncio event loop + `to_thread()` for
  blocking calls; `threading.RLock` guards shared buffers
- **Live endpoints**: Changes to `/api/*` endpoints affect a running trading
  engine — validate carefully before modifying

---

## Code Change Rules

- Prefer editing existing files over creating new ones
- No speculative abstractions — only implement what the task requires
- No backward-compatibility shims for code that has no callers
- No comments explaining WHAT the code does — only WHY (non-obvious constraints,
  workarounds, subtle invariants)
- Security: never introduce command injection, SQL injection, or XSS —
  validate at system boundaries only
- Tests must pass before committing (`python tests/test_live_process_access.py`)

---

## Git Workflow

- Development branch: `claude/fix-strategy-loss-cap-cjlOU`
- Always commit with descriptive messages referencing the feature/fix
- Push only after tests pass
- Never force-push without explicit user confirmation
