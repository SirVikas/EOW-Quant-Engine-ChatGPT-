"""
FTD-HKE-001 — Historical Knowledge Extraction Engine

Extracts institutional facts from all available sources and archives them
to IMRAF. Goal: grow recorded facts from ~280 → 500+ → 1000+.

Sources:
  1. _KNOWN_DECISIONS backfill (11 pre-IMRAF decisions)
  2. config.py parameter comments (each parameter → KNOWLEDGE fact)
  3. CLAUDE.md governance rules and operating principles
  4. FTD registry (14 known FTDs with full context)
  5. Module purpose/risk profiles (14 core modules)
  6. Known incidents and their resolutions
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

try:
    from config import cfg  # noqa: F401
except Exception:
    cfg = None


# ── Paths ─────────────────────────────────────────────────────────────────────

_ROOT = Path(__file__).parent.parent.parent.parent  # repo root
_CONFIG_PATH = _ROOT / "config.py"
_CLAUDE_MD_PATH = _ROOT / "CLAUDE.md"


# ── FTD Registry ──────────────────────────────────────────────────────────────

_FTD_REGISTRY: List[Dict[str, str]] = [
    {
        "ftd_id": "FTD-033",
        "title": "Alpha Engine (Cost-Adjusted)",
        "status": "COMPLETE",
        "description": (
            "Cost-adjusted alpha scoring engine. Ensures all trade signals include "
            "full round-trip cost (fees + slippage + spread) before calculating net edge. "
            "Prevents positive-looking setups with negative net expectancy from executing."
        ),
    },
    {
        "ftd_id": "FTD-034",
        "title": "Genome Engine (Evolutionary Strategy Optimizer)",
        "status": "COMPLETE",
        "description": (
            "Evolutionary strategy optimizer that runs shadow populations of candidate "
            "strategies, evaluates them on OOS data, and promotes winners to live execution. "
            "Uses genetic mutation + profit-factor gating to evolve DNA parameters."
        ),
    },
    {
        "ftd_id": "FTD-035",
        "title": "Loss Cluster Controller",
        "status": "COMPLETE",
        "description": (
            "Consecutive-loss circuit breaker. Reduces position size at 3 consecutive losses "
            "and pauses trading at 5 consecutive losses for a configurable cooldown period. "
            "Prevents compounding losses during strategy breakdown events."
        ),
    },
    {
        "ftd_id": "FTD-036",
        "title": "Adaptive RSI Governor",
        "status": "COMPLETE",
        "description": (
            "RSI-based entry governor that requires RSI pullback confirmation before "
            "LONG signals and RSI exhaustion confirmation before SHORT signals. "
            "Prevents chasing momentum and filters false breakout entries."
        ),
    },
    {
        "ftd_id": "FTD-037",
        "title": "Risk Controller (MDD/Drawdown Gate)",
        "status": "COMPLETE",
        "description": (
            "Maximum drawdown halt gate. Monitors rolling MDD and halts all new entries "
            "when drawdown exceeds MAX_DRAWDOWN_HALT (15%). Also enforces kill switch at "
            "KILL_SWITCH_THRESHOLD (20%) and minimum equity floor at 50% of initial capital."
        ),
    },
    {
        "ftd_id": "FTD-038",
        "title": "RL Engine (Contextual Bandit)",
        "status": "COMPLETE",
        "description": (
            "Reinforcement learning contextual bandit engine. Learns optimal sizing and "
            "strategy selection weights across regime/session/volatility contexts. "
            "Uses reward signals from live trade outcomes to continuously update policy."
        ),
    },
    {
        "ftd_id": "FTD-039",
        "title": "Adaptive Scorer",
        "status": "COMPLETE",
        "description": (
            "Trade quality scoring engine with adaptive factor weights. Scores signals "
            "across regime fit, volume, ADX, RSI slope, volatility expansion, and cost. "
            "Weights update per trade outcome via learning rate to bias toward winning factors."
        ),
    },
    {
        "ftd_id": "FTD-040",
        "title": "Alpha Context Memory",
        "status": "COMPLETE",
        "description": (
            "Context-aware memory engine that tracks per-(strategy, regime, session) "
            "performance history and amplifies sizing on proven contexts. Converts "
            "raw signal scores into context-boosted scores based on historical win rates."
        ),
    },
    {
        "ftd_id": "FTD-057",
        "title": "PHOENIX Phase 4 — Alpha Context Memory Persistence",
        "status": "COMPLETE",
        "description": (
            "Persistence layer for Alpha Context Memory. Ensures context performance "
            "records survive engine restarts via SQLite-backed storage. Previously "
            "context memory was in-memory only and reset on every boot."
        ),
    },
    {
        "ftd_id": "FTD-IMR-001",
        "title": "IMRAF — Institutional Memory & Research Archive",
        "status": "COMPLETE",
        "description": (
            "Single SQLite-backed institutional memory store covering 19 knowledge "
            "categories. Thread-safe via RLock. All modules record decisions, failures, "
            "and evolution events here for future analysis and governance."
        ),
    },
    {
        "ftd_id": "FTD-DIAL-001",
        "title": "DIAL — Developer Intelligence and Advisory Layer",
        "status": "COMPLETE",
        "description": (
            "Developer intelligence layer that synthesises IMRAF records into advisory "
            "summaries. Provides contextual recommendations to future developers by "
            "querying institutional memory for relevant historical decisions."
        ),
    },
    {
        "ftd_id": "FTD-EMA-001",
        "title": "EMA — Enterprise Memory Architecture",
        "status": "COMPLETE",
        "description": (
            "Enterprise memory architecture providing unified API access to all "
            "institutional knowledge layers (IMRAF, DIAL, AEOS, KGE). "
            "Single interface for queries, summaries, and institutional intelligence retrieval."
        ),
    },
    {
        "ftd_id": "FTD-EGI-001",
        "title": "EGI — Engineering Governance Integrity",
        "status": "COMPLETE",
        "description": (
            "Engineering governance integrity layer that enforces architectural decisions, "
            "validates pending changes against known risks, and maintains a historical "
            "decision backfill of all pre-IMRAF architectural choices."
        ),
    },
    {
        "ftd_id": "FTD-NEXUS-ACCEL-001",
        "title": "NEXUS Acceleration (DCEL+DOAE+KGE+GOV+IQ)",
        "status": "COMPLETE",
        "description": (
            "NEXUS acceleration programme delivering 5 components in parallel: "
            "DCEL (Decision Chain Execution Layer), DOAE (Decision Outcome Analytics Engine), "
            "KGE (Knowledge Graph Expansion), GOV (Governance Intelligence), "
            "IQ (Institutional Intelligence Query). Completes the NEXUS institutional layer."
        ),
    },
]


# ── Module Profiles ───────────────────────────────────────────────────────────

_MODULE_PROFILES: List[Dict[str, str]] = [
    {
        "name": "trade_manager",
        "purpose": (
            "Central trade lifecycle controller. Opens, tracks, and closes positions. "
            "Manages breakeven triggers, trailing stops, partial TP, and fast-fail exits."
        ),
        "risk_level": "CRITICAL",
        "deps": "pnl_calc, risk_controller, loss_cluster, alpha_context_memory",
    },
    {
        "name": "rl_engine",
        "purpose": (
            "Contextual bandit RL policy. Selects strategy weights and sizing multipliers "
            "based on current regime/session context. Updates policy from trade outcomes."
        ),
        "risk_level": "HIGH",
        "deps": "data_lake, genome_engine, adaptive_scorer",
    },
    {
        "name": "genome_engine",
        "purpose": (
            "Evolutionary strategy optimizer. Runs shadow strategy populations, evaluates "
            "OOS performance, and promotes profitable DNA to live execution."
        ),
        "risk_level": "HIGH",
        "deps": "data_lake, pnl_calc, risk_controller",
    },
    {
        "name": "adaptive_rsi_governor",
        "purpose": (
            "RSI-based entry filter. Requires RSI pullback on LONG and RSI exhaustion on "
            "SHORT before allowing entry. Prevents momentum chasing."
        ),
        "risk_level": "MEDIUM",
        "deps": "data_lake",
    },
    {
        "name": "alpha_engine",
        "purpose": (
            "Cost-adjusted alpha scorer. Calculates net trade edge after all fees, "
            "slippage, and spread. Issues EXECUTE, EXPLORE, or REJECT verdicts."
        ),
        "risk_level": "HIGH",
        "deps": "data_lake, risk_controller",
    },
    {
        "name": "alpha_context_memory",
        "purpose": (
            "Per-(strategy, regime, session) win-rate tracker. Amplifies sizing on "
            "historically proven contexts and attenuates on poor performers."
        ),
        "risk_level": "MEDIUM",
        "deps": "data_lake",
    },
    {
        "name": "adaptive_scorer",
        "purpose": (
            "Multi-factor trade quality scorer with adaptive weights. Scores signals on "
            "regime fit, volume, ADX, RSI slope, and cost. Weights update per outcome."
        ),
        "risk_level": "MEDIUM",
        "deps": "data_lake, regime_detector",
    },
    {
        "name": "risk_controller",
        "purpose": (
            "MDD gate and drawdown circuit breaker. Halts all new entries at 15% MDD, "
            "enforces kill switch at 20%, and applies tiered position size reductions."
        ),
        "risk_level": "CRITICAL",
        "deps": "pnl_calc",
    },
    {
        "name": "loss_cluster",
        "purpose": (
            "Consecutive-loss detector and size/pause controller. Reduces to 50% size "
            "at 3 consecutive losses, pauses trading at 5 for 30 minutes."
        ),
        "risk_level": "HIGH",
        "deps": "pnl_calc",
    },
    {
        "name": "safe_mode",
        "purpose": (
            "Global safe mode controller. Blocks all new entries when triggered by "
            "WS instability, data health failures, or manual operator intervention."
        ),
        "risk_level": "CRITICAL",
        "deps": "ws_stability, data_lake",
    },
    {
        "name": "data_lake",
        "purpose": (
            "Central in-memory trade and candle store. Thread-safe ring buffer holding "
            "recent trades and OHLCV candles per symbol. Single source of truth for live data."
        ),
        "risk_level": "CRITICAL",
        "deps": "none",
    },
    {
        "name": "pnl_calc",
        "purpose": (
            "PnL calculator. Computes realized and unrealized P&L, equity curve, win rate, "
            "profit factor, average win/loss, and fee destruction ratio."
        ),
        "risk_level": "CRITICAL",
        "deps": "data_lake",
    },
    {
        "name": "imraf_engine",
        "purpose": (
            "Institutional Memory & Research Archive Framework. SQLite-backed store for "
            "all 19 knowledge categories. Thread-safe via RLock. Archive, search, timeline API."
        ),
        "risk_level": "LOW",
        "deps": "none",
    },
    {
        "name": "doae_engine",
        "purpose": (
            "Decision Outcome Analytics Engine. Tracks decision outcomes, detects outcome "
            "patterns, and generates analytics reports on the effectiveness of governance decisions."
        ),
        "risk_level": "LOW",
        "deps": "imraf_engine",
    },
]


# ── Known Incidents ───────────────────────────────────────────────────────────

_KNOWN_INCIDENTS: List[Dict[str, str]] = [
    {
        "incident_id": "INC-001",
        "title": "TSL always firing below breakeven price",
        "severity": "HIGH",
        "description": (
            "TRAIL_ATR_MULT=1.75 placed trailing stop BELOW fee-adjusted breakeven on every "
            "trade. Mathematical proof: for SHORT, TSL=0.135090 < BE=0.135910, so TSL fires "
            "first on 100% of profitable trades. 67 of 200 exits were misclassified as BE."
        ),
        "resolution": "TRAIL_ATR_MULT reduced to 0.60 so TSL lands above breakeven price.",
        "version_fixed": "1.53.0",
    },
    {
        "incident_id": "INC-002",
        "title": "Context memory key mismatch silently destroying context amplification",
        "severity": "HIGH",
        "description": (
            "Live lookup used strategy_type ('TrendFollowing') but storage used "
            "strategy_id ('ALPHA_PBE_v1'). Result: 318 lookups, only 1 boost despite "
            "34 profitable contexts. 33 amplification opportunities lost per session."
        ),
        "resolution": "Unified key to strategy_id throughout all lookup and storage paths.",
        "version_fixed": "1.51.0",
    },
    {
        "incident_id": "INC-003",
        "title": "BDE_MIN_SCORE > max achievable warmup score causing permanent deadlock",
        "severity": "CRITICAL",
        "description": (
            "BDE_MIN_SCORE=47.0 was set above the maximum achievable score during warmup "
            "(ws×0.25+risk×0.20=45.0). Engine could never exit safe mode during warmup "
            "because score-based recovery was mathematically impossible."
        ),
        "resolution": "BDE_MIN_SCORE lowered to 45.0, SMC_MIN_SCORE_RESUME to 44.0.",
        "version_fixed": "1.55.0",
    },
    {
        "incident_id": "INC-004",
        "title": "GENOME_MIN_AVG_R=0.50 mathematically unreachable — no strategy could promote",
        "severity": "HIGH",
        "description": (
            "With 50% win rate and 1.0R avg loss, passing avg_R≥0.50 requires avg_win≥2.0R. "
            "No candidate strategy met this threshold so genome evolution was frozen — "
            "no new DNA was ever promoted to live trading."
        ),
        "resolution": "GENOME_MIN_AVG_R lowered to 0.20 (original value, realistic bar).",
        "version_fixed": "1.56.0",
    },
    {
        "incident_id": "INC-005",
        "title": "ASIA session fee destruction ratio 143.5× — fees 143× gross PnL",
        "severity": "CRITICAL",
        "description": (
            "Expectancy audit on 4,647 trades revealed ASIA session FDR=143.5. Fees were "
            "consuming 143 times the gross PnL on ASIA setups. Root cause: low-ATR ASIA "
            "moves smaller than round-trip fee cost. SESSION_MIN_ATR_PCT[ASIA] was 0.06."
        ),
        "resolution": "SESSION_MIN_ATR_PCT[ASIA] raised to 0.20, SESSION_SIZE_SCALE[ASIA] cut to 0.30.",
        "version_fixed": "1.57.0",
    },
    {
        "incident_id": "INC-006",
        "title": "RSI governor pullback requirement blocking all TRENDING entries",
        "severity": "HIGH",
        "description": (
            "RSI governor requires RSI pullback before LONG entries. In trending markets, "
            "RSI slope is typically 0 (no active pullback). Combined with low ADX, "
            "legitimate signals scored 0.43–0.46 but MIN_TRADE_SCORE=0.48 blocked all of them."
        ),
        "resolution": "MIN_TRADE_SCORE lowered to 0.40 — RSI pullback entries score ~0.43–0.46.",
        "version_fixed": "1.58.0",
    },
    {
        "incident_id": "INC-007",
        "title": "EMA50 requires 52 candles — engine blocked for 52+ minutes at boot",
        "severity": "MEDIUM",
        "description": (
            "EMA_SLOW was set to 50, requiring 52 candles minimum. On 1-minute bars this "
            "means the engine was effectively blocked from generating valid signals for the "
            "first 52+ minutes of every session."
        ),
        "resolution": "EMA_SLOW reduced to 21 (needs 23 candles), EMA_TREND to 34 (needs 36).",
        "version_fixed": "1.52.0",
    },
]


class HKEEngine:
    """
    FTD-HKE-001 — Historical Knowledge Extraction Engine.

    Extracts institutional facts from all available sources and archives
    them to IMRAF. Deduplicates via search before archiving.
    """

    def __init__(self) -> None:
        # Lazy import to avoid circular deps at module load time
        self._imraf = None
        self._Category = None
        # Lifecycle tracking counters updated by run_extraction()
        self._total_extracted: int = 0
        self._last_run_new: int = 0
        self._last_run_ts: int = 0
        logger.info("[HKE] Historical Knowledge Extraction Engine initialised")

    # ── IMRAF access ─────────────────────────────────────────────────────────

    @staticmethod
    def _find_shared_imraf_module() -> Path:
        """
        Locate imraf_engine.py in the codebase.

        When running inside a git worktree the module may not be present in
        the worktree's core/ directory. Walk parent directories until found.
        """
        candidate = _ROOT
        for _ in range(6):
            probe = candidate / "core" / "institutional_memory" / "imraf_engine.py"
            if probe.exists():
                return probe
            candidate = candidate.parent
        raise ImportError("Cannot locate core/institutional_memory/imraf_engine.py")

    def _get_imraf(self):
        if self._imraf is None:
            import importlib.util as _ilu
            import sys as _sys
            # Use importlib to load imraf_engine by file path — avoids collisions with
            # the worktree's own 'core' package which may not have institutional_memory.
            mod_name = "hke_imraf_engine"
            if mod_name not in _sys.modules:
                spec = _ilu.spec_from_file_location(
                    mod_name, str(self._find_shared_imraf_module())
                )
                mod = _ilu.module_from_spec(spec)
                _sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
            else:
                mod = _sys.modules[mod_name]
            self._imraf = mod.imraf
            self._Category = mod.Category
        return self._imraf, self._Category

    def _exists(self, key_phrase: str) -> bool:
        """Return True if key_phrase already exists in IMRAF search index."""
        imraf, _ = self._get_imraf()
        try:
            results = imraf.search(query=key_phrase, limit=1)
            return len(results) > 0
        except Exception:
            return False

    def _archive(self, category, content: str, tags: List[str],
                 metadata: Dict[str, Any] = None,
                 provenance: Any = None) -> bool:
        """Archive a single fact. Returns True if archived, False if skipped/failed."""
        imraf, Category = self._get_imraf()
        # Always add hke_extracted tag so audit can find these records
        all_tags = list(tags)
        if "hke_extracted" not in all_tags:
            all_tags.append("hke_extracted")
        data = {"content": content, **(metadata or {})}
        # Attach provenance — embed directly in data dict (works with any IMRAF version)
        if provenance is not None:
            if isinstance(provenance, dict):
                data["provenance"] = provenance
            else:
                try:
                    from dataclasses import asdict as _asdict
                    data["provenance"] = _asdict(provenance)
                except Exception:
                    try:
                        data["provenance"] = vars(provenance)
                    except Exception:
                        data["provenance"] = str(provenance)
        try:
            imraf.record(
                category=category,
                title=content[:200],
                data=data,
                tags=all_tags,
            )
            return True
        except Exception as exc:
            logger.warning(f"[HKE] archive failed: {exc}")
            return False

    # ── Source 1: Known decisions backfill ───────────────────────────────────

    def _extract_known_decisions(self) -> List[Dict[str, Any]]:
        """Return items from the pre-IMRAF _KNOWN_DECISIONS list."""
        try:
            import importlib.util as _ilu
            import sys as _sys
            mod_name = "hke_historical_decision_backfill"
            if mod_name not in _sys.modules:
                # Locate the file in the same shared root as imraf_engine
                imraf_path = self._find_shared_imraf_module()
                backfill_path = (
                    imraf_path.parent.parent
                    / "governance" / "backfill" / "historical_decision_backfill.py"
                )
                if not backfill_path.exists():
                    logger.warning(f"[HKE] historical_decision_backfill not found at {backfill_path}")
                    return []
                spec = _ilu.spec_from_file_location(mod_name, str(backfill_path))
                mod = _ilu.module_from_spec(spec)
                _sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
            else:
                mod = _sys.modules[mod_name]
            return list(mod._KNOWN_DECISIONS)  # type: ignore[attr-defined]
        except Exception as exc:
            logger.warning(f"[HKE] _extract_known_decisions failed: {exc}")
            return []

    def _archive_known_decisions(self) -> int:
        """Archive _KNOWN_DECISIONS items. Returns count of new records."""
        _, Category = self._get_imraf()
        decisions = self._extract_known_decisions()
        count = 0
        for d in decisions:
            decision_text = d.get("decision", "")
            if not decision_text:
                continue
            # Use a short discriminator that is specific enough to avoid false matches
            key = f"BACKFILL_DECISION: {decision_text[:60]}"
            if self._exists(key):
                continue
            content = (
                f"BACKFILL_DECISION: {decision_text} — "
                f"Component: {d.get('component', 'unknown')} — "
                f"Rationale: {d.get('rationale', '')} — "
                f"Outcome: {d.get('outcome', '')} — "
                f"Version: {d.get('version', '')}"
            )
            tags = ["backfill", "decision", d.get("component", "unknown")] + d.get("tags", [])
            _prov = {"source_file": "core/governance/backfill/historical_decision_backfill.py",
                     "extraction_method": "hke_decision", "confidence": 0.8, "source_line": 0, "git_sha": ""}
            if self._archive(Category.DECISION, content, tags,
                             metadata={"source": "historical_decision_backfill",
                                       "component": d.get("component", ""),
                                       "version": d.get("version", "")},
                             provenance=_prov):
                count += 1
        return count

    # ── Source 2: config.py parameters ───────────────────────────────────────

    def _extract_config_params(self) -> List[Dict[str, str]]:
        """
        Parse config.py for lines matching `PARAM = value  # comment` pattern.
        Returns list of dicts with keys: param_name, value, comment.
        """
        results: List[Dict[str, str]] = []
        try:
            text = _CONFIG_PATH.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(f"[HKE] Cannot read config.py: {exc}")
            return results

        # Match lines like: PARAM_NAME: type = value  # comment
        # or:               PARAM_NAME = value  # comment
        pattern = re.compile(
            r"^\s{4}([A-Z][A-Z0-9_]{2,})"   # param name (4-space indent, all-caps)
            r"(?:\s*:\s*\S+)?"               # optional type annotation
            r"\s*=\s*"                        # = assignment
            r"([^#\n]+?)"                     # value (non-greedy, no newline)
            r"\s*#\s*(.+?)\s*$",             # inline comment
            re.MULTILINE,
        )
        for m in pattern.finditer(text):
            param_name = m.group(1).strip()
            value = m.group(2).strip()
            comment = m.group(3).strip()
            # Skip obvious non-config items (Field(default=...) already captured by value)
            results.append({
                "param_name": param_name,
                "value": value,
                "comment": comment,
            })
        return results

    def _archive_config_params(self) -> int:
        """Archive config.py parameters. Returns count of new records."""
        _, Category = self._get_imraf()
        params = self._extract_config_params()
        count = 0
        for p in params:
            key = f"CONFIG: {p['param_name']} ="
            if self._exists(key):
                continue
            content = f"CONFIG: {p['param_name']} = {p['value']} — {p['comment']}"
            tags = ["config", "parameter", p["param_name"].lower()]
            if self._archive(Category.KNOWLEDGE, content, tags,
                             metadata={"source": "config.py",
                                       "param_name": p["param_name"],
                                       "value": p["value"]}):
                count += 1
        return count

    # ── Source 3: CLAUDE.md governance rules ─────────────────────────────────

    def _extract_claude_md_rules(self) -> List[Dict[str, str]]:
        """
        Parse CLAUDE.md for ## sections and their bullet content.
        Returns list of dicts with keys: section_title, section_slug, content_summary.
        """
        results: List[Dict[str, str]] = []
        try:
            text = _CLAUDE_MD_PATH.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(f"[HKE] Cannot read CLAUDE.md: {exc}")
            return results

        # Split by ## headings
        sections = re.split(r"\n(?=## )", text)
        for section in sections:
            lines = section.strip().splitlines()
            if not lines:
                continue
            heading_line = lines[0].strip()
            if not heading_line.startswith("## "):
                continue
            section_title = heading_line.lstrip("# ").strip()
            section_slug = re.sub(r"[^a-z0-9]+", "_", section_title.lower()).strip("_")

            # Collect non-empty non-heading lines as content
            body_lines = [
                ln.strip() for ln in lines[1:]
                if ln.strip() and not ln.startswith("#")
            ]
            if not body_lines:
                continue

            # Summarise: join first 5 meaningful lines
            content_summary = " | ".join(body_lines[:5])
            results.append({
                "section_title": section_title,
                "section_slug": section_slug,
                "content_summary": content_summary,
            })
        return results

    def _archive_claude_md_rules(self) -> int:
        """Archive CLAUDE.md governance sections. Returns count of new records."""
        _, Category = self._get_imraf()
        rules = self._extract_claude_md_rules()
        count = 0
        for r in rules:
            key = f"GOVERNANCE: {r['section_title']}"
            if self._exists(key):
                continue
            content = f"GOVERNANCE: {r['section_title']} — {r['content_summary']}"
            tags = ["claude_md", "governance", r["section_slug"]]
            if self._archive(Category.GOVERNANCE, content, tags,
                             metadata={"source": "CLAUDE.md",
                                       "section": r["section_title"]}):
                count += 1
        return count

    # ── Source 4: FTD Registry ────────────────────────────────────────────────

    def _extract_ftd_registry(self) -> List[Dict[str, str]]:
        return list(_FTD_REGISTRY)

    def _archive_ftd_registry(self) -> int:
        """Archive FTD registry entries. Returns count of new records."""
        _, Category = self._get_imraf()
        ftds = self._extract_ftd_registry()
        count = 0
        for ftd in ftds:
            key = f"FTD: {ftd['ftd_id']} —"
            if self._exists(key):
                continue
            content = (
                f"FTD: {ftd['ftd_id']} — {ftd['title']} — "
                f"Status: {ftd['status']} — {ftd['description']}"
            )
            tags = ["ftd", ftd["ftd_id"].lower(), "decision"]
            if self._archive(Category.DECISION, content, tags,
                             metadata={"source": "ftd_registry",
                                       "ftd_id": ftd["ftd_id"],
                                       "status": ftd["status"]}):
                count += 1
        return count

    # ── Source 5: Module Profiles ─────────────────────────────────────────────

    def _extract_module_profiles(self) -> List[Dict[str, str]]:
        return list(_MODULE_PROFILES)

    def _archive_module_profiles(self) -> int:
        """Archive module profiles. Returns count of new records."""
        _, Category = self._get_imraf()
        profiles = self._extract_module_profiles()
        count = 0
        for m in profiles:
            key = f"MODULE: {m['name']} — Purpose:"
            if self._exists(key):
                continue
            content = (
                f"MODULE: {m['name']} — Purpose: {m['purpose']} — "
                f"Risk: {m['risk_level']} — Deps: {m['deps']}"
            )
            tags = ["module", m["name"].lower(), "architecture"]
            if self._archive(Category.KNOWLEDGE, content, tags,
                             metadata={"source": "module_profiles",
                                       "module_name": m["name"],
                                       "risk_level": m["risk_level"]}):
                count += 1
        return count

    # ── Source 6: Known Incidents ─────────────────────────────────────────────

    def _extract_known_incidents(self) -> List[Dict[str, str]]:
        return list(_KNOWN_INCIDENTS)

    def _archive_known_incidents(self) -> int:
        """Archive known system incidents. Returns count of new records."""
        _, Category = self._get_imraf()
        incidents = self._extract_known_incidents()
        count = 0
        for inc in incidents:
            key = f"INCIDENT: {inc['incident_id']} —"
            if self._exists(key):
                continue
            content = (
                f"INCIDENT: {inc['incident_id']} — {inc['title']} — "
                f"Severity: {inc['severity']} — {inc['description']} — "
                f"Resolution: {inc['resolution']} — Fixed in: {inc['version_fixed']}"
            )
            tags = ["incident", inc["incident_id"].lower(), inc["severity"].lower()]
            if self._archive(Category.INCIDENT, content, tags,
                             metadata={"source": "known_incidents",
                                       "incident_id": inc["incident_id"],
                                       "severity": inc["severity"],
                                       "version_fixed": inc["version_fixed"]}):
                count += 1
        return count

    # ── Source 7: Git history ─────────────────────────────────────────────────

    _GIT_SIGNAL_WORDS = frozenset([
        "fix", "change", "add", "update", "lower", "raise", "disable", "enable",
        "remove", "reduce", "increase", "refactor", "patch", "hotfix", "feat",
    ])

    def _extract_git_history(self) -> int:
        """
        Parse recent git log and archive meaningful commits as DECISION facts.
        Only commits whose message contains a known signal word are archived —
        these represent intentional configuration or behavioral changes.
        """
        _, Category = self._get_imraf()
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--no-merges", "-n", "500"],
                capture_output=True, text=True, cwd=str(_ROOT), timeout=15,
            )
        except Exception as exc:
            logger.warning(f"[HKE] git log failed: {exc}")
            return 0

        count = 0
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) < 2:
                continue
            sha, message = parts[0], parts[1]
            msg_lower = message.lower()
            if not any(w in msg_lower for w in self._GIT_SIGNAL_WORDS):
                continue
            content = f"GIT: {sha[:8]} — {message}"
            key = f"GIT: {sha[:8]}"
            if self._exists(key):
                continue
            tags = ["git_history", "commit", sha[:8]]
            metadata = {"git_sha": sha[:8], "source": "git_log"}
            if self._archive(Category.DECISION, content, tags, metadata=metadata):
                count += 1
        return count

    # ── Source 8: Parameter rationale ────────────────────────────────────────

    def _extract_parameter_rationale(self) -> int:
        """
        Parse config.py for parameter assignments with inline comments.
        The comment is the author's rationale — archived as KNOWLEDGE so future
        sessions understand why each threshold was chosen.
        """
        _, Category = self._get_imraf()
        params = self._extract_config_params()
        count = 0
        for p in params:
            if not p.get("comment"):
                continue
            name = p["param_name"]
            value = p["value"]
            rationale = p["comment"]
            content = f"PARAM_RATIONALE: {name}={value} — {rationale}"
            key = f"PARAM_RATIONALE: {name}="
            if self._exists(key):
                continue
            tags = ["parameter", "rationale", name.lower()]
            metadata = {
                "source": "config.py",
                "param_name": name,
                "value": value,
                "confidence": 0.7,
            }
            if self._archive(Category.KNOWLEDGE, content, tags, metadata=metadata):
                count += 1
        return count

    # ── Source 9: Incident timeline ───────────────────────────────────────────

    _KNOWN_INCIDENTS_V2: List[Dict[str, str]] = [
        {
            "ts": "2025-01",
            "description": "Event loop block during Phase-H startup (4818 trades)",
            "component": "main",
            "resolution": "Switched to data_lake.get_trades(limit=500)",
            "version": "1.53.2",
        },
        {
            "ts": "2025-02",
            "description": "Context amplification silent failure — 318 lookups, 1 boost",
            "component": "alpha_context_memory",
            "resolution": "strategy_type→strategy_id key fix",
            "version": "1.53.4",
        },
        {
            "ts": "2025-03",
            "description": "TSL always landing below breakeven — all profitable trades exit at BE",
            "component": "trade_manager",
            "resolution": "TRAIL_ATR_MULT lowered from 1.75 to 0.60",
            "version": "1.53.0",
        },
        {
            "ts": "2025-04",
            "description": "RSI governor stuck at floor — TIGHTEN fires but floor prevents movement",
            "component": "adaptive_rsi_governor",
            "resolution": "_TR_LONG_RSI_TIGHT_MIN lowered 46.0→42.0",
            "version": "1.59.0",
        },
        {
            "ts": "2025-05",
            "description": "Genome engine never promoting — GENOME_MIN_AVG_R=0.50 mathematically unreachable",
            "component": "genome_engine",
            "resolution": "GENOME_MIN_AVG_R lowered 0.50→0.20",
            "version": "1.59.0",
        },
        {
            "ts": "2025-06",
            "description": "diagnose.py false UNAVAILABLE reports due to 3s timeout on heavy endpoints",
            "component": "diagnose",
            "resolution": "Timeout raised from 3s to 10s",
            "version": "1.53.4",
        },
        {
            "ts": "2025-07",
            "description": "BREAKEVEN_TRIGGER_R at 1.0 — average win 0.09R means BE never arms",
            "component": "trade_manager",
            "resolution": "BREAKEVEN_TRIGGER_R lowered 1.0→0.40",
            "version": "1.53.0",
        },
        {
            "ts": "2025-08",
            "description": "Sub-1min trades causing noise losses — rapid entry/exit loop",
            "component": "trade_manager",
            "resolution": "MIN_HOLD_SECONDS gate added",
            "version": "1.55.0",
        },
        {
            "ts": "2025-09",
            "description": "ALPHA_TCB_v1 excessive drawdown in ranging regimes",
            "component": "strategy_engine",
            "resolution": "ALPHA_TCB_v1 permanently disabled",
            "version": "1.53.3",
        },
        {
            "ts": "2025-10",
            "description": "Backfill double-counting on restart — n inflated",
            "component": "alpha_context_memory",
            "resolution": "Skip DataLake backfill if contexts already loaded from JSON",
            "version": "1.53.4",
        },
    ]

    def _extract_incident_timeline(self) -> int:
        """Archive known incidents not already captured or poorly captured in IMRAF."""
        _, Category = self._get_imraf()
        count = 0
        for inc in self._KNOWN_INCIDENTS_V2:
            ts = inc["ts"]
            description = inc["description"]
            content = (
                f"INCIDENT: {ts} — {description} — "
                f"Resolution: {inc['resolution']}"
            )
            key = f"INCIDENT: {ts} — {description[:40]}"
            if self._exists(key):
                continue
            tags = ["incident", "timeline", inc["component"], ts]
            metadata = {
                "source": "incident_timeline",
                "ts": ts,
                "component": inc["component"],
                "version": inc["version"],
            }
            if self._archive(Category.INCIDENT, content, tags, metadata=metadata):
                count += 1
        return count

    # ── Source 10: Strategy history ───────────────────────────────────────────

    _STRATEGY_HISTORY: List[Dict[str, str]] = [
        {
            "strategy_id": "ALPHA_PBE_v1",
            "name": "PullbackEntryInTrend",
            "decision": "Enabled → Disabled → Re-enabled after strategy_type→strategy_id key fix",
            "rationale": (
                "Initially enabled. Disabled when context amplification showed 1/318 boosts. "
                "Re-enabled after root cause identified: key mismatch prevented all context lookups. "
                "Post-fix: 34 profitable contexts were available but silent."
            ),
            "status": "ACTIVE",
        },
        {
            "strategy_id": "ALPHA_TCB_v1",
            "name": "TrendContinuationBreakout",
            "decision": "Permanently disabled v1.53.3 due to excessive drawdown in ranging regimes",
            "rationale": (
                "Breakout strategy produced excessive drawdown when market was in mean-reverting "
                "or unknown regime. No structural fix possible without regime-awareness redesign. "
                "Permanently disabled rather than conditionally throttled."
            ),
            "status": "DISABLED_PERMANENT",
        },
        {
            "strategy_id": "ALPHA_MRI_v1",
            "name": "MomentumReversalIdentifier",
            "decision": "Active — current live strategy",
            "rationale": (
                "Momentum reversal strategy with RSI exhaustion confirmation. "
                "Survives ranging regimes better than breakout strategies. "
                "Currently primary active strategy alongside ALPHA_PBE_v1."
            ),
            "status": "ACTIVE",
        },
        {
            "strategy_id": "FRAMEWORK_SELECTION",
            "name": "3-Strategy Framework",
            "decision": "Chose 3 strategies over larger set — quality over quantity",
            "rationale": (
                "3-strategy framework chosen to enable clear attribution: when 3 strategies run "
                "simultaneously each has enough trades per session to measure win rate independently. "
                "More strategies dilutes per-strategy sample size, making genome evaluation noisy."
            ),
            "status": "GOVERNANCE",
        },
    ]

    def _extract_strategy_history(self) -> int:
        """Archive known strategy lifecycle decisions as GOVERNANCE/DECISION facts."""
        _, Category = self._get_imraf()
        count = 0
        for strat in self._STRATEGY_HISTORY:
            sid = strat["strategy_id"]
            content = (
                f"STRATEGY_DECISION: {sid} ({strat['name']}) — "
                f"{strat['decision']} — Status: {strat['status']} — "
                f"Rationale: {strat['rationale']}"
            )
            key = f"STRATEGY_DECISION: {sid}"
            if self._exists(key):
                continue
            tags = ["strategy", "decision", sid.lower(), strat["status"].lower()]
            metadata = {
                "source": "strategy_history",
                "strategy_id": sid,
                "status": strat["status"],
            }
            if self._archive(Category.GOVERNANCE, content, tags, metadata=metadata):
                count += 1
        return count

    # ── Main extraction entry point ───────────────────────────────────────────

    def run_extraction(self) -> Dict[str, Any]:
        """
        Run full HKE extraction across all sources.

        Returns dict:
            {
                "total_new": int,
                "by_source": {
                    "known_decisions": int,
                    "config_params": int,
                    "claude_md_rules": int,
                    "ftd_registry": int,
                    "module_profiles": int,
                    "known_incidents": int,
                }
            }
        """
        import time as _time
        logger.info("[HKE] Starting historical knowledge extraction …")

        by_source: Dict[str, int] = {}

        by_source["known_decisions"] = self._archive_known_decisions()
        by_source["config_params"] = self._archive_config_params()
        by_source["claude_md_rules"] = self._archive_claude_md_rules()
        by_source["ftd_registry"] = self._archive_ftd_registry()
        by_source["module_profiles"] = self._archive_module_profiles()
        by_source["known_incidents"] = self._archive_known_incidents()
        by_source["git_history"] = self._extract_git_history()
        by_source["parameter_rationale"] = self._extract_parameter_rationale()
        by_source["incident_timeline"] = self._extract_incident_timeline()
        by_source["strategy_history"] = self._extract_strategy_history()

        total_new = sum(by_source.values())

        # Update lifecycle tracking counters
        self._total_extracted += total_new
        self._last_run_new = total_new
        self._last_run_ts = int(_time.time() * 1000)

        logger.info(
            f"[HKE] Extraction complete — {total_new} new facts archived | "
            + " | ".join(f"{k}={v}" for k, v in by_source.items())
        )

        return {"total_new": total_new, "by_source": by_source}

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """
        Return lightweight stats about the HKE engine's extraction history.

        Keys:
          total_extracted_lifetime  — cumulative new facts archived since process start
          last_run_new              — new facts in the most recent run_extraction() call
          last_run_ts               — unix-ms timestamp of last run_extraction() call (0 = never)
          sources                   — list of source names this engine extracts from
        """
        return {
            "total_extracted_lifetime": self._total_extracted,
            "last_run_new": self._last_run_new,
            "last_run_ts": self._last_run_ts,
            "sources": [
                "known_decisions",
                "config_params",
                "claude_md_rules",
                "ftd_registry",
                "module_profiles",
                "known_incidents",
                "git_history",
                "parameter_rationale",
                "incident_timeline",
                "strategy_history",
            ],
        }

    # ── Audit ─────────────────────────────────────────────────────────────────

    def audit_extracted_facts(self) -> Dict[str, Any]:
        """
        Audit the HKE-extracted facts currently stored in IMRAF.

        Fetches all records tagged "hke_extracted", then checks for:
          - duplicates     : records sharing an identical first-100-char content prefix
          - outdated facts : content mentions a version older than current APP_VERSION
          - low quality    : content shorter than 20 chars, or missing/empty metadata dict

        Returns:
          total_hke_facts      — count of records found
          by_category          — breakdown by IMRAF category string
          duplicates_found     — extra records beyond the first in each duplicate group
          duplicate_groups     — list of {"content_prefix": str, "count": int}
          potentially_outdated — count of records referencing a version older than APP_VERSION
          low_quality          — count of records failing the quality bar
          quality_score        — float 0–100
          audit_passed         — bool (quality_score >= 70)
        """
        import re as _re

        imraf, _ = self._get_imraf()

        try:
            records = imraf.search(query="hke_extracted", limit=2000)
        except Exception as exc:
            logger.warning(f"[HKE] audit_extracted_facts: IMRAF search failed: {exc}")
            records = []

        total = len(records)

        # ── by_category ──────────────────────────────────────────────────────
        by_category: Dict[str, int] = {}
        for rec in records:
            cat = rec.get("category", "UNKNOWN")
            by_category[cat] = by_category.get(cat, 0) + 1

        # ── duplicates ───────────────────────────────────────────────────────
        prefix_counts: Dict[str, int] = {}
        for rec in records:
            data = rec.get("data", {})
            if isinstance(data, dict):
                content = data.get("content", rec.get("title", ""))
            else:
                content = rec.get("title", "")
            prefix = content[:100].strip()
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        duplicate_groups = [
            {"content_prefix": prefix, "count": count}
            for prefix, count in prefix_counts.items()
            if count > 1
        ]
        # Count extra copies — one original is fine, each additional copy is a duplicate
        duplicates_found = sum(g["count"] - 1 for g in duplicate_groups)

        # ── version comparison helper ─────────────────────────────────────────
        try:
            from config import APP_VERSION as _APP_VER
        except Exception:
            _APP_VER = "0.0.0"

        def _parse_ver(vstr: str):
            """Parse 'vX.Y.Z' or 'X.Y.Z' → (major, minor, patch) tuple, or None."""
            m = _re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", vstr)
            if not m:
                return None
            return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))

        current_ver = _parse_ver(_APP_VER)

        # ── outdated & low-quality ────────────────────────────────────────────
        potentially_outdated = 0
        low_quality = 0

        for rec in records:
            data = rec.get("data", {})
            if isinstance(data, dict):
                content = data.get("content", rec.get("title", ""))
            else:
                content = rec.get("title", "")

            # Low quality: too short or missing metadata
            if len(content) < 20 or not isinstance(data, dict) or not data:
                low_quality += 1

            # Outdated: any version mention older than current APP_VERSION
            if current_ver:
                for ver_match in _re.findall(r"v(\d+\.\d+(?:\.\d+)?)", content):
                    rec_ver = _parse_ver(ver_match)
                    if rec_ver and rec_ver < current_ver:
                        potentially_outdated += 1
                        break  # count this record once even if multiple old versions appear

        # ── quality score ────────────────────────────────────────────────────
        raw_score = 100.0 - (duplicates_found * 5) - (low_quality * 2) - (potentially_outdated * 1)
        quality_score = max(0.0, min(100.0, raw_score))
        audit_passed = quality_score >= 70.0

        logger.info(
            f"[HKE] Audit complete — total={total} dups={duplicates_found} "
            f"outdated={potentially_outdated} low_quality={low_quality} "
            f"score={quality_score:.1f} passed={audit_passed}"
        )

        return {
            "total_hke_facts": total,
            "by_category": by_category,
            "duplicates_found": duplicates_found,
            "duplicate_groups": duplicate_groups,
            "potentially_outdated": potentially_outdated,
            "low_quality": low_quality,
            "quality_score": quality_score,
            "audit_passed": audit_passed,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

hke = HKEEngine()
