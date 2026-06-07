"""
FTD-EGI-001 Component 1 — Historical Decision Backfill Engine

Scans all available institutional sources and extracts decisions that exist
outside IMRAF (CLAUDE.md, git history, code comments, FTD archives) and
imports them into institutional memory so EMA can answer "Why was X changed?"

Sources scanned:
    1. CLAUDE.md  — governance rules, known risks, operating principles
    2. Git commit history — commit messages as change decisions
    3. Key source files  — inline comments with WHY explanations
    4. FTD archives      — any text files describing FTDs
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


# ── Known decisions hardcoded from institutional memory (pre-IMRAF) ──────────
# These are facts that existed only in CLAUDE.md, code comments, and
# conversation history. Now permanently imported into IMRAF.
_KNOWN_DECISIONS: List[Dict[str, Any]] = [
    {
        "decision": "TRAIL_ATR_MULT set to 0.60 (was ATR_MULT * 0.7 = ~1.75)",
        "rationale": (
            "TSL was always landing below fee-adjusted breakeven price. "
            "Mathematical proof: for SHORT with old mult=1.75, TSL=0.135090 < BE=0.135910, "
            "so TSL fires first on every trade. With mult=0.60, TSL=0.135854 > BE — "
            "trailing stop fires correctly, capturing gains beyond breakeven."
        ),
        "component": "trade_manager",
        "version": "1.53.0",
        "category": "ARCHITECTURE",
        "tags": ["tsl", "breakeven", "atr_mult", "architecture"],
        "outcome": "BE exits no longer fire on all profitable trades. TSL fires correctly.",
        "status": "ACTIVE",
    },
    {
        "decision": "strategy_id replaces strategy_type as context memory lookup key",
        "rationale": (
            "Live lookup used strategy_type ('TrendFollowing') but storage used "
            "strategy_id ('ALPHA_PBE_v1'). Result: 318 lookups, only 1 boost despite "
            "34 profitable contexts. Key mismatch silently destroyed context amplification."
        ),
        "component": "alpha_context_memory",
        "version": "1.53.4",
        "category": "BUG",
        "tags": ["context_memory", "strategy_id", "key_mismatch", "bug"],
        "outcome": "Context amplification now works. Profitable contexts receive 1.25x boost.",
        "status": "FIXED",
    },
    {
        "decision": "Phase-H startup uses data_lake.get_trades(limit=500) not pnl_calc.trades",
        "rationale": (
            "Original Phase-H: [asdict(t) for t in pnl_calc.trades] with 4818 trades "
            "ran synchronously inside async lifespan, blocking the event loop for >145s. "
            "The bat file timeout killed the process. Fix: fetch only 500 recent trades "
            "from DataLake directly — fast, non-blocking, sufficient for context restore."
        ),
        "component": "main",
        "version": "1.53.2",
        "category": "INCIDENT",
        "tags": ["startup", "event_loop", "phase_h", "timeout"],
        "outcome": "Engine boots in <30s. No event loop block.",
        "status": "FIXED",
    },
    {
        "decision": "ALPHA_TCB_v1 disabled permanently (Breakout strategy)",
        "rationale": (
            "ALPHA_TCB_v1 showed excessive drawdown in ranging regimes. "
            "OOS validation failed repeatedly. Risk-adjusted returns negative. "
            "Kept in codebase but in _DISABLED_STRATEGY_IDS frozenset."
        ),
        "component": "strategy_engine",
        "version": "1.53.3",
        "category": "GOVERNANCE",
        "tags": ["strategy", "breakout", "disabled", "governance"],
        "outcome": "Breakout losses eliminated. Trade frequency reduced ~15%.",
        "status": "ACTIVE",
    },
    {
        "decision": "Backfill double-counting prevention on restart",
        "rationale": (
            "Each restart: load JSON context → run DataLake backfill → n inflated. "
            "Fix: check total_contexts > 0 before backfill. If JSON already loaded, "
            "skip DataLake loop entirely."
        ),
        "component": "alpha_context_memory",
        "version": "1.53.4",
        "category": "BUG",
        "tags": ["backfill", "context_memory", "restart", "double_counting"],
        "outcome": "Context counts accurate across restarts.",
        "status": "FIXED",
    },
    {
        "decision": "diagnose.py API timeout raised from 3s to 10s",
        "rationale": (
            "RL/Economic Truth/AI endpoints compute heavy aggregations. "
            "3s timeout caused false UNAVAILABLE reports on valid endpoints. "
            "10s allows heavy endpoints to complete normally."
        ),
        "component": "diagnose",
        "version": "1.53.4",
        "category": "DECISION",
        "tags": ["diagnose", "timeout", "api"],
        "outcome": "All API endpoints report correctly. No false UNAVAILABLE.",
        "status": "ACTIVE",
    },
    {
        "decision": "APP_VERSION single source of truth in config.py only",
        "rationale": (
            "Multiple version strings in dashboard.html, run.py banners, and metadata.json "
            "caused drift. CLAUDE.md mandates: only config.APP_VERSION updated. "
            "All downstream components read from /api/version."
        ),
        "component": "config",
        "version": "1.53.0",
        "category": "ARCHITECTURE",
        "tags": ["versioning", "ssot", "config", "architecture"],
        "outcome": "Version is always consistent across all reports and UI.",
        "status": "ACTIVE",
    },
    {
        "decision": "BREAKEVEN_TRIGGER_R lowered from 1.0 to 0.40",
        "rationale": (
            "Average winning trade = 0.09R. BE at 1.0R never armed (99.8% of wins "
            "below 1.0R). 0.40R arms BE on trades that develop past the noise floor, "
            "protecting gains via trailing stop without triggering prematurely."
        ),
        "component": "trade_manager",
        "version": "1.53.0",
        "category": "ARCHITECTURE",
        "tags": ["breakeven", "trigger", "r_multiple", "architecture"],
        "outcome": "BE protects developing trades. TSL handles exit above BE.",
        "status": "ACTIVE",
    },
    {
        "decision": "ALPHA_PBE_v1 (PullbackEntryInTrend) re-enabled",
        "rationale": (
            "Context memory showed ALPHA_PBE_v1 as profitable across multiple regimes. "
            "Was disabled alongside other strategies during cleanup. Re-enabled after "
            "context memory key mismatch fix confirmed it had been recording correctly."
        ),
        "component": "strategy_engine",
        "version": "1.53.3",
        "category": "GOVERNANCE",
        "tags": ["strategy", "alpha_pbe_v1", "enabled", "governance"],
        "outcome": "PBE signals active again. Context amplification applied correctly.",
        "status": "ACTIVE",
    },
    {
        "decision": "RSI governor floor raised to 46.0 (was 44.0)",
        "rationale": (
            "Survival ceiling at 0.25 caused TRENDING bands to get stuck at floor "
            "during low-survival periods. Raised floor to 46.0 and ceiling to 0.35 "
            "to allow bands to move above noise floor."
        ),
        "component": "adaptive_rsi_governor",
        "version": "1.53.1",
        "category": "ARCHITECTURE",
        "tags": ["rsi_governor", "trending", "floor", "survival_ceiling"],
        "outcome": "Trending bands no longer stuck at floor. RSI gate operates correctly.",
        "status": "ACTIVE",
    },
    {
        "decision": "SQLite WAL mode for IMRAF and DataLake",
        "rationale": (
            "WAL (Write-Ahead Logging) allows concurrent reads during writes. "
            "Without WAL, async read queries during trade close would block on "
            "exclusive write locks, causing latency spikes."
        ),
        "component": "imraf_engine",
        "version": "1.54.0",
        "category": "ARCHITECTURE",
        "tags": ["sqlite", "wal", "concurrency", "architecture"],
        "outcome": "No lock contention. Concurrent reads and writes work correctly.",
        "status": "ACTIVE",
    },
]


class HistoricalDecisionBackfill:
    """
    Scans institutional sources and imports historical decisions into IMRAF.
    Ensures decisions made before IMRAF existed are not lost.
    """

    def __init__(self, project_root: Path = Path(".")):
        self._root = project_root
        self._imraf = None
        self._load_imraf()

    def _load_imraf(self) -> None:
        try:
            from core.institutional_memory.imraf_engine import imraf
            self._imraf = imraf
        except Exception as exc:
            logger.warning(f"[Backfill] IMRAF unavailable: {exc}")

    # ── Source 1: Hardcoded known decisions ───────────────────────────────────

    def extract_known_decisions(self) -> List[Dict[str, Any]]:
        """Return the list of known pre-IMRAF decisions."""
        return list(_KNOWN_DECISIONS)

    # ── Source 2: CLAUDE.md ───────────────────────────────────────────────────

    def extract_from_claude_md(self) -> List[Dict[str, Any]]:
        """Parse CLAUDE.md for governance rules and known risks."""
        candidates = []
        claude_md = self._root / "CLAUDE.md"
        if not claude_md.exists():
            return candidates

        text = claude_md.read_text(encoding="utf-8")

        # Extract known risks section
        risk_pattern = re.compile(r"\*\*(.+?)\*\*\s*\n(.*?)(?=\n\*\*|\Z)", re.DOTALL)
        for m in risk_pattern.finditer(text):
            title = m.group(1).strip()
            body  = m.group(2).strip()[:300]
            if title and len(body) > 20:
                candidates.append({
                    "decision": title,
                    "rationale": body,
                    "component": "governance",
                    "version":   "unknown",
                    "category":  "GOVERNANCE",
                    "tags":      ["claude_md", "governance"],
                    "outcome":   "",
                    "status":    "ACTIVE",
                    "source":    "CLAUDE.md",
                })
        return candidates

    # ── Source 3: Git commit history ─────────────────────────────────────────

    def extract_from_git_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Extract architectural decisions from git commit messages."""
        candidates = []
        try:
            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--pretty=format:%H|%s|%ai"],
                capture_output=True, text=True, cwd=str(self._root), timeout=10,
            )
            for line in result.stdout.strip().splitlines():
                parts = line.split("|", 2)
                if len(parts) < 3:
                    continue
                commit_hash, subject, date = parts

                # Only record commits with architectural signal words
                keywords = ["fix:", "feat:", "refactor:", "arch:", "governance:",
                           "TRAIL", "TSL", "strategy_id", "IMRAF", "DIAL", "AEOS", "EMA"]
                if not any(kw.lower() in subject.lower() for kw in keywords):
                    continue

                candidates.append({
                    "decision": subject[:120],
                    "rationale": f"Git commit {commit_hash[:8]} on {date[:10]}",
                    "component": "main",
                    "version":   "git",
                    "category":  "DEVELOPER",
                    "tags":      ["git_commit", commit_hash[:8]],
                    "outcome":   "",
                    "status":    "DELIVERED",
                    "source":    f"git:{commit_hash[:8]}",
                })
        except Exception as exc:
            logger.debug(f"[Backfill] Git history extraction: {exc}")
        return candidates

    # ── Source 4: Key file comments ───────────────────────────────────────────

    def extract_from_file_comments(self) -> List[Dict[str, Any]]:
        """
        Extract WHY comments from critical source files.
        Only lines with 'why', 'because', 'fixed', 'prevents' etc.
        """
        candidates = []
        target_files = [
            "config.py",
            "core/trade_manager.py",
            "core/signal_ecology/alpha_context_memory.py",
            "core/signal_ecology/adaptive_rsi_governor.py",
        ]
        why_pattern = re.compile(
            r"#\s*(.{20,200}(?:fix|prevent|because|reason|was|changed|avoid|ensure).{0,100})",
            re.IGNORECASE,
        )
        for rel_path in target_files:
            fpath = self._root / rel_path
            if not fpath.exists():
                continue
            try:
                for i, line in enumerate(fpath.read_text(encoding="utf-8").splitlines(), 1):
                    m = why_pattern.search(line)
                    if m:
                        candidates.append({
                            "decision": m.group(1).strip()[:120],
                            "rationale": f"Source: {rel_path}:{i}",
                            "component": rel_path.replace("core/", "").replace(".py", "").replace("/", "_"),
                            "version":   "source",
                            "category":  "KNOWLEDGE",
                            "tags":      ["source_comment", rel_path],
                            "outcome":   "",
                            "status":    "ACTIVE",
                            "source":    f"{rel_path}:{i}",
                        })
            except Exception:
                pass
        return candidates


class DecisionImporter:
    """Imports extracted decision candidates into IMRAF."""

    def __init__(self):
        self._imraf = None
        self._load_imraf()

    def _load_imraf(self) -> None:
        try:
            from core.institutional_memory.imraf_engine import imraf
            self._imraf = imraf
        except Exception as exc:
            logger.warning(f"[Importer] IMRAF unavailable: {exc}")

    def import_decisions(
        self, decisions: List[Dict[str, Any]], dry_run: bool = False
    ) -> Dict[str, Any]:
        """Import a list of decision candidates into IMRAF."""
        if not self._imraf:
            return {"status": "DEGRADED", "imported": 0, "skipped": 0}

        imported = 0
        skipped  = 0
        errors   = 0
        record_ids = []

        for d in decisions:
            try:
                existing = self._imraf.search(d["decision"][:40], limit=3)
                already_stored = any(
                    d["decision"][:30].lower() in r["title"].lower()
                    for r in existing
                )
                if already_stored:
                    skipped += 1
                    continue

                if not dry_run:
                    rid = self._imraf.record(
                        category    = d.get("category", "DECISION"),
                        title       = d["decision"][:120],
                        data        = {
                            "decision":   d["decision"],
                            "rationale":  d.get("rationale", ""),
                            "component":  d.get("component", ""),
                            "version":    d.get("version", ""),
                            "outcome":    d.get("outcome", ""),
                            "status":     d.get("status", ""),
                            "source":     d.get("source", "backfill"),
                            "backfill_ts": int(time.time() * 1000),
                        },
                        subcategory = d.get("component", ""),
                        tags        = d.get("tags", []) + ["backfill"],
                    )
                    record_ids.append(rid)
                imported += 1
            except Exception as exc:
                logger.error(f"[Importer] Failed to import: {d.get('decision','?')[:40]}: {exc}")
                errors += 1

        return {
            "status":     "DRY_RUN" if dry_run else "OK",
            "imported":   imported,
            "skipped":    skipped,
            "errors":     errors,
            "record_ids": record_ids,
            "total_candidates": len(decisions),
        }


class DecisionValidator:
    """Validates imported decisions for completeness and integrity."""

    def __init__(self):
        self._imraf = None
        self._load_imraf()

    def _load_imraf(self) -> None:
        try:
            from core.institutional_memory.imraf_engine import imraf
            self._imraf = imraf
        except Exception:
            pass

    def validate(self) -> Dict[str, Any]:
        """Check that backfill decisions are in IMRAF and meet quality standards."""
        if not self._imraf:
            return {"status": "DEGRADED"}

        backfill_records = self._imraf.search("backfill", limit=200)
        total_backfill   = len(backfill_records)

        # Check each known decision is present
        missing = []
        for kd in _KNOWN_DECISIONS:
            key = kd["decision"][:30].lower()
            found = any(key in r["title"].lower() for r in backfill_records)
            if not found:
                missing.append(kd["decision"][:60])

        # Quality check: each record should have rationale
        incomplete = [
            r["title"] for r in backfill_records
            if not r.get("data", {}).get("rationale", "")
        ]

        coverage_pct = round(
            (len(_KNOWN_DECISIONS) - len(missing)) / len(_KNOWN_DECISIONS) * 100, 1
        ) if _KNOWN_DECISIONS else 100.0

        return {
            "status":           "OK" if not missing else "INCOMPLETE",
            "total_imported":   total_backfill,
            "known_decisions":  len(_KNOWN_DECISIONS),
            "coverage_pct":     coverage_pct,
            "missing_decisions": missing,
            "incomplete_records": incomplete[:5],
            "validation_ts":    int(time.time() * 1000),
        }


def run_full_backfill(
    project_root: Path = Path("."), dry_run: bool = False
) -> Dict[str, Any]:
    """
    Run the complete backfill pipeline:
    1. Extract from all sources
    2. Import into IMRAF
    3. Validate results
    """
    scanner  = HistoricalDecisionBackfill(project_root)
    importer = DecisionImporter()

    # Gather from all sources
    known    = scanner.extract_known_decisions()
    from_md  = scanner.extract_from_claude_md()
    from_git = scanner.extract_from_git_history(limit=30)
    from_src = scanner.extract_from_file_comments()

    all_decisions = known + from_md + from_git + from_src
    logger.info(
        f"[Backfill] Extracted {len(known)} known + {len(from_md)} CLAUDE.md + "
        f"{len(from_git)} git + {len(from_src)} source = {len(all_decisions)} total"
    )

    result = importer.import_decisions(all_decisions, dry_run=dry_run)
    result["sources"] = {
        "known_decisions": len(known),
        "from_claude_md":  len(from_md),
        "from_git":        len(from_git),
        "from_source":     len(from_src),
    }

    if not dry_run:
        validator = DecisionValidator()
        result["validation"] = validator.validate()

    return result
