"""
FTD-EGI-001 Component 4 — Institutional Truth Engine

Answers "Why was X changed?" with structured decision provenance:
Decision, Date, Author, FTD, Verifier, Outcome, Current Status.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger


@dataclass
class TruthRecord:
    """Structured answer to 'Why was X changed?'"""
    query: str
    decision: str
    date: str
    author: str
    ftd_reference: str
    verifier: str
    outcome: str
    current_status: str
    confidence: str          # HIGH / MEDIUM / LOW
    source: str              # imraf / backfill / inferred
    supporting_records: List[Dict[str, Any]] = field(default_factory=list)
    related_queries: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "decision": self.decision,
            "date": self.date,
            "author": self.author,
            "ftd_reference": self.ftd_reference,
            "verifier": self.verifier,
            "outcome": self.outcome,
            "current_status": self.current_status,
            "confidence": self.confidence,
            "source": self.source,
            "supporting_records": self.supporting_records,
            "related_queries": self.related_queries,
        }


_UNKNOWN = "Unknown — not recorded in institutional memory"

_NOT_FOUND = TruthRecord(
    query="",
    decision=_UNKNOWN,
    date=_UNKNOWN,
    author=_UNKNOWN,
    ftd_reference=_UNKNOWN,
    verifier=_UNKNOWN,
    outcome=_UNKNOWN,
    current_status="No record found in IMRAF or backfill history",
    confidence="LOW",
    source="none",
)

# Static truth index for pre-IMRAF decisions (mirrors _KNOWN_DECISIONS in backfill)
_STATIC_TRUTH: List[Dict[str, Any]] = [
    {
        "keywords": ["trail", "atr", "mult", "0.60", "trailing"],
        "decision": "TRAIL_ATR_MULT set to 0.60 to reduce premature stop-outs on volatile assets",
        "date": "2024-Q3",
        "author": "engineering",
        "ftd_reference": "FTD-STRATEGY-001",
        "verifier": "pytest:strategies",
        "outcome": "Reduced stop-out rate; P&L improved on trending days",
        "current_status": "ACTIVE — current default value in config.py",
        "confidence": "HIGH",
        "source": "backfill",
    },
    {
        "keywords": ["strategy_id", "strategy_type", "context memory", "lookup key"],
        "decision": "strategy_id replaces strategy_type as context memory lookup key for cross-session consistency",
        "date": "2024-Q3",
        "author": "engineering",
        "ftd_reference": "FTD-EMA-001",
        "verifier": "pytest:enterprise_memory",
        "outcome": "Eliminated lookup mismatches across strategy restarts",
        "current_status": "ACTIVE — strategy_id is canonical key",
        "confidence": "HIGH",
        "source": "backfill",
    },
    {
        "keywords": ["phase-h", "startup", "data_lake", "get_trades", "pnl_calc"],
        "decision": "Phase-H startup uses data_lake.get_trades(limit=500) instead of pnl_calc.trades to fix empty-trades crash on cold start",
        "date": "2024-Q3",
        "author": "engineering",
        "ftd_reference": "FTD-IMR-001",
        "verifier": "pytest:test_live_process_access",
        "outcome": "Eliminated cold-start crash; engine boots cleanly",
        "current_status": "ACTIVE — Phase-H boot path uses data_lake",
        "confidence": "HIGH",
        "source": "backfill",
    },
    {
        "keywords": ["alpha_tcb", "alpha tcb", "tcb", "disabled", "false positive"],
        "decision": "ALPHA_TCB_v1 disabled after producing false-positive signals during low-volatility regime",
        "date": "2024-Q4",
        "author": "engineering",
        "ftd_reference": "FTD-STRATEGY-002",
        "verifier": "pytest:strategies",
        "outcome": "False positive rate reduced to zero for that strategy class",
        "current_status": "DISABLED — excluded from active strategy roster",
        "confidence": "HIGH",
        "source": "backfill",
    },
    {
        "keywords": ["backfill", "double", "count", "duplicate"],
        "decision": "Backfill dedup guard added to prevent double-counting historical trades on engine restart",
        "date": "2024-Q4",
        "author": "engineering",
        "ftd_reference": "FTD-IMR-001",
        "verifier": "pytest:institutional_memory",
        "outcome": "Backfill idempotent; P&L calculations consistent across restarts",
        "current_status": "ACTIVE — dedup guard in place",
        "confidence": "HIGH",
        "source": "backfill",
    },
    {
        "keywords": ["diagnose", "timeout", "30", "60", "health"],
        "decision": "diagnose() timeout extended from 30s to 60s to prevent false-positive health failures under load",
        "date": "2025-Q1",
        "author": "engineering",
        "ftd_reference": "FTD-IMR-001",
        "verifier": "pytest:test_live_process_access",
        "outcome": "Health check false-positive rate eliminated",
        "current_status": "ACTIVE — 60s timeout in effect",
        "confidence": "MEDIUM",
        "source": "backfill",
    },
    {
        "keywords": ["app_version", "version", "single source", "ssot", "config.py"],
        "decision": "APP_VERSION declared as single source of truth in config.py; all other version strings removed",
        "date": "2025-Q1",
        "author": "engineering",
        "ftd_reference": "FTD-EGI-001",
        "verifier": "pytest:governance",
        "outcome": "Version drift eliminated; dashboard always shows correct build",
        "current_status": "ACTIVE — enforced by CLAUDE.md directive",
        "confidence": "HIGH",
        "source": "backfill",
    },
    {
        "keywords": ["breakeven", "trigger", "1r", "2r", "be_trigger"],
        "decision": "BREAKEVEN_TRIGGER_R set to 1.0R (was 2.0R) to protect profits earlier on momentum trades",
        "date": "2025-Q1",
        "author": "engineering",
        "ftd_reference": "FTD-STRATEGY-001",
        "verifier": "pytest:strategies",
        "outcome": "Drawdown reduced; win-rate preserved",
        "current_status": "ACTIVE — 1.0R breakeven trigger",
        "confidence": "HIGH",
        "source": "backfill",
    },
    {
        "keywords": ["alpha_pbe", "alpha pbe", "pbe", "re-enabled", "re-enable"],
        "decision": "ALPHA_PBE_v1 re-enabled after parameter recalibration resolved excessive whipsaw",
        "date": "2025-Q2",
        "author": "engineering",
        "ftd_reference": "FTD-STRATEGY-002",
        "verifier": "pytest:strategies",
        "outcome": "Additional alpha capture without whipsaw degradation",
        "current_status": "ACTIVE — recalibrated parameters",
        "confidence": "MEDIUM",
        "source": "backfill",
    },
    {
        "keywords": ["rsi", "governor", "floor", "minimum", "25", "threshold"],
        "decision": "RSI governor minimum floor raised to 25 to prevent over-selling in deeply oversold conditions",
        "date": "2025-Q2",
        "author": "engineering",
        "ftd_reference": "FTD-STRATEGY-001",
        "verifier": "pytest:strategies",
        "outcome": "Prevented false sell signals in extreme RSI ranges",
        "current_status": "ACTIVE — floor enforced",
        "confidence": "MEDIUM",
        "source": "backfill",
    },
    {
        "keywords": ["sqlite", "wal", "write-ahead", "journal", "concurrency"],
        "decision": "SQLite WAL mode enabled for IMRAF to allow concurrent reads during write operations",
        "date": "2025-Q2",
        "author": "engineering",
        "ftd_reference": "FTD-IMR-001",
        "verifier": "pytest:institutional_memory",
        "outcome": "Eliminated read-lock contention; IMRAF reads non-blocking",
        "current_status": "ACTIVE — WAL mode enforced on IMRAF init",
        "confidence": "HIGH",
        "source": "backfill",
    },
]


class InstitutionalTruthEngine:
    """
    Answers 'Why was X changed?' by querying IMRAF and static backfill records.

    Resolution order:
    1. IMRAF DECISION records (most recent, highest trust)
    2. IMRAF GOVERNANCE records
    3. Static backfill truth index (_STATIC_TRUTH)
    4. Inferred from IMRAF INCIDENT records
    5. Not found → LOW confidence answer
    """

    def __init__(self):
        self._imraf = None
        self._load_imraf()

    def _load_imraf(self) -> None:
        try:
            from core.institutional_memory.imraf_engine import imraf
            self._imraf = imraf
        except Exception:
            pass

    # ── Public API ───────────────────────────────────────────────────────────

    def why(self, query: str) -> TruthRecord:
        """
        Answer 'Why was X changed?'
        Returns TruthRecord with structured decision provenance.
        """
        query_lower = query.lower()
        tokens = re.findall(r"\w+", query_lower)

        # 1. Search IMRAF DECISION records
        record = self._search_imraf("DECISION", tokens, query)
        if record:
            return record

        # 2. Search IMRAF GOVERNANCE records
        record = self._search_imraf("GOVERNANCE", tokens, query)
        if record:
            return record

        # 3. Static backfill
        record = self._search_static(tokens, query)
        if record:
            return record

        # 4. Incident inference
        record = self._search_imraf("INCIDENT", tokens, query)
        if record:
            record.confidence = "LOW"
            record.source = "inferred"
            return record

        result = TruthRecord(**vars(_NOT_FOUND))
        result.query = query
        return result

    def search(self, query: str, limit: int = 10) -> List[TruthRecord]:
        """Return up to `limit` matching truth records for a query."""
        tokens = re.findall(r"\w+", query.lower())
        results: List[TruthRecord] = []

        if self._imraf:
            for category in ("DECISION", "GOVERNANCE", "INCIDENT"):
                try:
                    raw = self._imraf.query(category=category, limit=200)
                    for r in raw:
                        if self._matches(r, tokens):
                            parsed = self._parse_imraf_record(r, query, category)
                            if parsed:
                                results.append(parsed)
                                if len(results) >= limit:
                                    return results
                except Exception:
                    pass

        for entry in _STATIC_TRUTH:
            if any(kw in query.lower() for kw in entry["keywords"]):
                results.append(self._parse_static(entry, query))
                if len(results) >= limit:
                    break

        return results

    def list_decisions(self, component: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """List all known decisions, optionally filtered by component."""
        results: List[Dict[str, Any]] = []

        if self._imraf:
            try:
                raw = self._imraf.query(category="DECISION", limit=500)
                for r in raw:
                    data = r.get("data", {}) if isinstance(r, dict) else {}
                    comp = data.get("component", "")
                    if component and component.lower() not in comp.lower():
                        continue
                    results.append({
                        "id": r.get("id"),
                        "title": r.get("title", ""),
                        "date": r.get("created_at", ""),
                        "component": comp,
                        "source": "imraf",
                    })
                    if len(results) >= limit:
                        return results
            except Exception:
                pass

        for entry in _STATIC_TRUTH:
            if component and component.lower() not in entry["decision"].lower():
                continue
            results.append({
                "title": entry["decision"][:80],
                "date": entry["date"],
                "component": "",
                "source": "backfill",
            })
            if len(results) >= limit:
                break

        return results

    def get_decision_coverage(self) -> Dict[str, Any]:
        """Return coverage metrics for governance reporting."""
        imraf_count = 0
        static_count = len(_STATIC_TRUTH)

        if self._imraf:
            try:
                records = self._imraf.query(category="DECISION", limit=1000)
                imraf_count = len(records)
            except Exception:
                pass

        total = imraf_count + static_count
        return {
            "imraf_decisions": imraf_count,
            "static_backfill_decisions": static_count,
            "total_decisions": total,
            "coverage_pct": round(min(total / max(total, 1) * 100, 100.0), 1),
        }

    # ── Private helpers ──────────────────────────────────────────────────────

    def _search_imraf(
        self, category: str, tokens: List[str], query: str
    ) -> Optional[TruthRecord]:
        if not self._imraf:
            return None
        try:
            raw = self._imraf.query(category=category, limit=200)
            best = None
            best_score = 0
            for r in raw:
                score = self._score(r, tokens)
                if score > best_score:
                    best_score = score
                    best = r
            if best and best_score >= 1:
                return self._parse_imraf_record(best, query, category)
        except Exception as exc:
            logger.debug(f"[TruthEngine] IMRAF search error: {exc}")
        return None

    def _search_static(self, tokens: List[str], query: str) -> Optional[TruthRecord]:
        best = None
        best_score = 0
        for entry in _STATIC_TRUTH:
            score = sum(1 for kw in entry["keywords"] if kw in tokens or kw in query.lower())
            if score > best_score:
                best_score = score
                best = entry
        if best and best_score >= 1:
            return self._parse_static(best, query)
        return None

    @staticmethod
    def _score(record: Dict[str, Any], tokens: List[str]) -> int:
        text = (
            record.get("title", "") + " " +
            str(record.get("data", ""))
        ).lower()
        return sum(1 for t in tokens if len(t) > 3 and t in text)

    @staticmethod
    def _matches(record: Dict[str, Any], tokens: List[str]) -> bool:
        text = (record.get("title", "") + " " + str(record.get("data", ""))).lower()
        return any(len(t) > 3 and t in text for t in tokens)

    @staticmethod
    def _parse_imraf_record(
        r: Dict[str, Any], query: str, category: str
    ) -> Optional[TruthRecord]:
        if not isinstance(r, dict):
            return None
        data = r.get("data", {}) if isinstance(r.get("data"), dict) else {}
        return TruthRecord(
            query=query,
            decision=r.get("title", data.get("change", _UNKNOWN)),
            date=r.get("created_at", _UNKNOWN),
            author=data.get("author", "engineering"),
            ftd_reference=data.get("ftd_reference", data.get("related_ftd", _UNKNOWN)),
            verifier=data.get("verifier", data.get("verifier_name", _UNKNOWN)),
            outcome=data.get("outcome", data.get("observed_impact", _UNKNOWN)),
            current_status=data.get("current_status", "ACTIVE"),
            confidence="HIGH" if category == "DECISION" else "MEDIUM",
            source="imraf",
            supporting_records=[r],
        )

    @staticmethod
    def _parse_static(entry: Dict[str, Any], query: str) -> TruthRecord:
        return TruthRecord(
            query=query,
            decision=entry["decision"],
            date=entry["date"],
            author=entry["author"],
            ftd_reference=entry["ftd_reference"],
            verifier=entry["verifier"],
            outcome=entry["outcome"],
            current_status=entry["current_status"],
            confidence=entry["confidence"],
            source=entry["source"],
        )


# ── Module-level singleton ───────────────────────────────────────────────────

truth_engine = InstitutionalTruthEngine()


def why(query: str) -> TruthRecord:
    """Convenience function. Answer 'Why was X changed?'"""
    return truth_engine.why(query)
