"""
EOW Quant Engine — Institutional Memory & Research Archive Framework (IMRAF)
FTD-IMR-001

Single SQLite-backed store for all 19 knowledge categories.
Sync sqlite3, thread-safe via threading.RLock, following DataLake pattern.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from config import APP_VERSION, cfg


@dataclass
class Provenance:
    source_file: str = ""        # e.g. "config.py", "core/rl_engine.py"
    source_line: int = 0         # line number, 0 if unknown
    git_sha: str = ""            # first 8 chars of commit SHA, "" if unknown
    extraction_method: str = ""  # "hke_config", "hke_decision", "dcel_hook", "manual", etc.
    confidence: float = 0.5      # 0.0-1.0: 1.0 = verified, 0.5 = inferred, 0.1 = synthetic


class Category(str, Enum):
    RESEARCH       = "RESEARCH"
    FAILURE        = "FAILURE"
    EVOLUTION      = "EVOLUTION"
    REGIME         = "REGIME"
    DECISION       = "DECISION"
    ATTRIBUTION    = "ATTRIBUTION"
    KNOWLEDGE      = "KNOWLEDGE"
    AI_TRAINING    = "AI_TRAINING"
    POSTMORTEM     = "POSTMORTEM"
    META_LEARNING  = "META_LEARNING"
    BUG            = "BUG"
    ARCHITECTURE   = "ARCHITECTURE"
    INCIDENT       = "INCIDENT"
    DEPLOYMENT     = "DEPLOYMENT"
    DEVELOPER      = "DEVELOPER"
    REGRESSION     = "REGRESSION"
    EVOLUTION_TL   = "EVOLUTION_TL"
    OPERATIONAL    = "OPERATIONAL"
    SELF_IMPROVE   = "SELF_IMPROVE"
    FTD        = "FTD"
    DELIVERY   = "DELIVERY"
    VERIFIER   = "VERIFIER"
    GOVERNANCE = "GOVERNANCE"


_SCHEMA = """
CREATE TABLE IF NOT EXISTS imraf_records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL,
    subcategory TEXT DEFAULT '',
    title       TEXT NOT NULL,
    data        TEXT NOT NULL,
    tags        TEXT DEFAULT '',
    engine_ver  TEXT DEFAULT '',
    ts          INTEGER NOT NULL,
    search_text TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_cat ON imraf_records(category);
CREATE INDEX IF NOT EXISTS idx_ts  ON imraf_records(ts);
"""

_DB_PATH = Path("data/institutional_memory.db")


class IMRAFEngine:
    """
    Institutional Memory & Research Archive Framework engine.
    All methods are sync and thread-safe via RLock.
    """

    def __init__(self, db_path: Path = _DB_PATH):
        self._db_path = db_path
        self._lock = threading.RLock()
        self._boot_ts = time.time()
        os.makedirs(self._db_path.parent, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        # Seed with boot deployment record
        self.record(
            category    = Category.DEPLOYMENT,
            title       = f"Engine boot v{APP_VERSION}",
            data        = {"version": APP_VERSION, "event": "BOOT", "db": str(self._db_path)},
            subcategory = "BOOT",
            tags        = ["boot", "deployment"],
        )
        logger.info(f"[IMRAF] Institutional memory ready → {self._db_path}")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    @staticmethod
    def _build_search_text(category: str, subcategory: str, title: str,
                           tags: str, data: dict) -> str:
        parts = [category, subcategory, title, tags]
        for v in data.values():
            if isinstance(v, str):
                parts.append(v)
        return " ".join(parts).lower()

    # ── Public API ────────────────────────────────────────────────────────────

    def record(
        self,
        category:    "Category | str",
        title:       str,
        data:        dict,
        subcategory: str = "",
        tags:        "List[str] | None" = None,
        provenance:  "Optional[Provenance]" = None,
    ) -> int:
        cat_str  = category.value if isinstance(category, Category) else str(category)
        tags_str = ",".join(tags or [])
        # Merge provenance into data under a dedicated key — no schema change needed.
        stored_data = dict(data)
        if provenance is not None:
            try:
                stored_data["provenance"] = asdict(provenance)
            except Exception:
                pass  # provenance failure must never crash archive()
        data_str = json.dumps(stored_data, default=str)
        ts       = int(time.time() * 1000)
        search   = self._build_search_text(cat_str, subcategory, title, tags_str, stored_data)
        with self._lock:
            cur = self._conn.execute(
                """INSERT INTO imraf_records
                   (category, subcategory, title, data, tags, engine_ver, ts, search_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (cat_str, subcategory, title, data_str, tags_str, APP_VERSION, ts, search),
            )
            self._conn.commit()
            return cur.lastrowid  # type: ignore[return-value]

    # archive() is an alias for record() — same signature, kept for callers that use
    # the archive name after reading the FTD spec.
    def archive(
        self,
        category:    "Category | str",
        title:       str,
        data:        dict,
        subcategory: str = "",
        tags:        "List[str] | None" = None,
        provenance:  "Optional[Provenance]" = None,
    ) -> int:
        return self.record(
            category=category,
            title=title,
            data=data,
            subcategory=subcategory,
            tags=tags,
            provenance=provenance,
        )

    def search(
        self,
        query:    str,
        category: "Optional[Category]" = None,
        limit:    int = 50,
        since_ts: "Optional[int]" = None,
    ) -> "List[Dict[str, Any]]":
        q_like = f"%{query.lower()}%"
        sql    = "SELECT * FROM imraf_records WHERE search_text LIKE ?"
        params: list = [q_like]
        if category is not None:
            sql += " AND category = ?"
            params.append(category.value if isinstance(category, Category) else str(category))
        if since_ts is not None:
            sql += " AND ts >= ?"
            params.append(since_ts)
        sql += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def timeline(
        self,
        category: "Optional[Category]" = None,
        limit:    int = 100,
    ) -> "List[Dict[str, Any]]":
        with self._lock:
            if category is not None:
                cat_str = category.value if isinstance(category, Category) else str(category)
                rows = self._conn.execute(
                    "SELECT * FROM imraf_records WHERE category=? ORDER BY ts DESC LIMIT ?",
                    (cat_str, limit),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM imraf_records ORDER BY ts DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_record(self, record_id: int) -> "Optional[Dict[str, Any]]":
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM imraf_records WHERE id=?", (record_id,)
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def get_stats(self) -> "Dict[str, Any]":
        with self._lock:
            total = self._conn.execute(
                "SELECT COUNT(*) FROM imraf_records"
            ).fetchone()[0]
            rows  = self._conn.execute(
                "SELECT category, COUNT(*) as cnt FROM imraf_records GROUP BY category"
            ).fetchall()
        by_cat = {r["category"]: r["cnt"] for r in rows}
        return {
            "total_records": total,
            "by_category":   by_cat,
            "db_path":       str(self._db_path),
            "boot_ts":       self._boot_ts,
        }

    def get_provenance_stats(self) -> "Dict[str, Any]":
        """
        Scan all records and return provenance coverage statistics.

        Returns:
            total           — total record count
            with_provenance — records that have a "provenance" key in their data JSON
            coverage_pct    — percentage of records with provenance
            by_method       — breakdown by extraction_method string
            avg_confidence  — mean confidence across records that have provenance
        """
        with self._lock:
            rows = self._conn.execute(
                "SELECT data FROM imraf_records"
            ).fetchall()

        total = len(rows)
        with_provenance = 0
        by_method: Dict[str, int] = {}
        confidence_sum = 0.0

        for row in rows:
            try:
                data = json.loads(row[0])
                prov = data.get("provenance") if isinstance(data, dict) else None
                if prov and isinstance(prov, dict):
                    with_provenance += 1
                    method = prov.get("extraction_method", "unknown") or "unknown"
                    by_method[method] = by_method.get(method, 0) + 1
                    confidence_sum += float(prov.get("confidence", 0.5))
            except Exception:
                pass

        coverage_pct = round(with_provenance / total * 100, 2) if total > 0 else 0.0
        avg_confidence = round(confidence_sum / with_provenance, 4) if with_provenance > 0 else 0.0

        return {
            "total": total,
            "with_provenance": with_provenance,
            "coverage_pct": coverage_pct,
            "by_method": by_method,
            "avg_confidence": avg_confidence,
        }

    def get_provenance_report(self, limit: int = 100) -> "List[Dict[str, Any]]":
        """
        Return records that have provenance, sorted by confidence ascending
        (lowest confidence first — these need the most review).
        """
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM imraf_records ORDER BY ts DESC"
            ).fetchall()

        records_with_prov = []
        for row in rows:
            d = self._row_to_dict(row)
            data = d.get("data", {})
            if not isinstance(data, dict):
                continue
            prov = data.get("provenance")
            if prov and isinstance(prov, dict):
                d["_confidence"] = float(prov.get("confidence", 0.5))
                records_with_prov.append(d)

        # Sort by confidence ascending so lowest-confidence records appear first
        records_with_prov.sort(key=lambda r: r["_confidence"])
        for r in records_with_prov:
            del r["_confidence"]

        return records_with_prov[:limit]

    def boot_summary(self) -> str:
        stats = self.get_stats()
        lines = [
            f"[IMRAF] Institutional Memory & Research Archive Framework",
            f"  DB path       : {stats['db_path']}",
            f"  Total records : {stats['total_records']}",
            f"  Categories    : {len(stats['by_category'])}",
            f"  Engine ver    : {APP_VERSION}",
            f"  Boot ts       : {stats['boot_ts']:.0f}",
        ]
        for cat, cnt in sorted(stats["by_category"].items()):
            lines.append(f"    {cat:<20}: {cnt}")
        return "\n".join(lines)

    def close(self) -> None:
        with self._lock:
            self._conn.close()
        logger.info("[IMRAF] Connection closed.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> "Dict[str, Any]":
        d = dict(row)
        try:
            d["data"] = json.loads(d["data"])
        except (json.JSONDecodeError, KeyError):
            pass
        if "tags" in d and d["tags"]:
            d["tags"] = d["tags"].split(",")
        else:
            d["tags"] = []
        return d


# ── Singleton ─────────────────────────────────────────────────────────────────

imraf = IMRAFEngine()


# ── Module-level convenience functions ───────────────────────────────────────

def record_failure(component: str, root_cause: str, impact: str,
                   resolution: str = "", prevention: str = "") -> int:
    return imraf.record(
        category    = Category.FAILURE,
        title       = f"Failure: {component}",
        data        = {"component": component, "root_cause": root_cause,
                       "impact": impact, "resolution": resolution,
                       "prevention": prevention},
        subcategory = component,
        tags        = ["failure", component],
    )


def record_incident(title: str, timeline: Any, root_cause: str,
                    corrective_actions: Any, severity: str = "MEDIUM") -> int:
    return imraf.record(
        category    = Category.INCIDENT,
        title       = title,
        data        = {"timeline": timeline, "root_cause": root_cause,
                       "corrective_actions": corrective_actions,
                       "severity": severity},
        subcategory = severity,
        tags        = ["incident", severity.lower()],
    )


def record_decision(symbol: str, signal: str, regime: str, strategy: str,
                    confidence: float, decision: str, reason: str,
                    filters_applied: "Optional[List]" = None) -> int:
    return imraf.record(
        category    = Category.DECISION,
        title       = f"Decision: {symbol} {decision}",
        data        = {"symbol": symbol, "signal": signal, "regime": regime,
                       "strategy": strategy, "confidence": confidence,
                       "decision": decision, "reason": reason,
                       "filters_applied": filters_applied or []},
        subcategory = decision,
        tags        = ["decision", symbol, regime],
    )


def record_evolution(strategy: str, version_from: str, version_to: str,
                     metric_before: Any, metric_after: Any,
                     change_summary: str) -> int:
    return imraf.record(
        category    = Category.EVOLUTION,
        title       = f"Evolution: {strategy} {version_from}→{version_to}",
        data        = {"strategy": strategy, "version_from": version_from,
                       "version_to": version_to, "metric_before": metric_before,
                       "metric_after": metric_after,
                       "change_summary": change_summary},
        subcategory = strategy,
        tags        = ["evolution", strategy],
    )


def record_regime(regime: str, symbol: str, characteristics: Any) -> int:
    return imraf.record(
        category    = Category.REGIME,
        title       = f"Regime: {regime} on {symbol}",
        data        = {"regime": regime, "symbol": symbol,
                       "characteristics": characteristics},
        subcategory = regime,
        tags        = ["regime", regime, symbol],
    )


def record_knowledge(title: str, finding: str, source: str = "",
                     tags: "Optional[List[str]]" = None) -> int:
    return imraf.record(
        category    = Category.KNOWLEDGE,
        title       = title,
        data        = {"finding": finding, "source": source},
        tags        = (tags or []) + ["knowledge"],
    )


def record_postmortem(incident_title: str, data_state: Any, signal_state: Any,
                      risk_state: Any, root_cause: str,
                      corrective_actions: Any) -> int:
    return imraf.record(
        category    = Category.POSTMORTEM,
        title       = f"Postmortem: {incident_title}",
        data        = {"incident_title": incident_title, "data_state": data_state,
                       "signal_state": signal_state, "risk_state": risk_state,
                       "root_cause": root_cause,
                       "corrective_actions": corrective_actions},
        subcategory = "postmortem",
        tags        = ["postmortem"],
    )


def record_bug(bug_id: str, component: str, root_cause: str, fix: str,
               prevention: str, status: str = "FIXED") -> int:
    return imraf.record(
        category    = Category.BUG,
        title       = f"Bug {bug_id}: {component}",
        data        = {"bug_id": bug_id, "component": component,
                       "root_cause": root_cause, "fix": fix,
                       "prevention": prevention, "status": status},
        subcategory = component,
        tags        = ["bug", status.lower(), component],
    )


def record_architecture(decision_title: str, decision: str, alternatives: Any,
                        reasoning: str, trade_offs: Any) -> int:
    return imraf.record(
        category    = Category.ARCHITECTURE,
        title       = decision_title,
        data        = {"decision": decision, "alternatives": alternatives,
                       "reasoning": reasoning, "trade_offs": trade_offs},
        subcategory = "architecture",
        tags        = ["architecture"],
    )


def record_self_improvement(change: str, observed_impact: str,
                             performance_delta: Any, stability_delta: Any,
                             outcome: str) -> int:
    return imraf.record(
        category    = Category.SELF_IMPROVE,
        title       = f"Self-improvement: {change}",
        data        = {"change": change, "observed_impact": observed_impact,
                       "performance_delta": performance_delta,
                       "stability_delta": stability_delta, "outcome": outcome},
        subcategory = outcome,
        tags        = ["self_improve", outcome.lower()],
    )


def record_research(strategy: str, version: str, regime: str, parameters: Any,
                    results: Any, data_source: str = "Binance Futures") -> int:
    return imraf.record(
        category    = Category.RESEARCH,
        title       = f"Research: {strategy} v{version} in {regime}",
        data        = {"strategy": strategy, "version": version, "regime": regime,
                       "parameters": parameters, "results": results,
                       "data_source": data_source},
        subcategory = strategy,
        tags        = ["research", strategy, regime],
    )


def record_regression(component: str, trigger: str, previous_behavior: str,
                      current_behavior: str, affected_versions: Any) -> int:
    return imraf.record(
        category    = Category.REGRESSION,
        title       = f"Regression: {component}",
        data        = {"component": component, "trigger": trigger,
                       "previous_behavior": previous_behavior,
                       "current_behavior": current_behavior,
                       "affected_versions": affected_versions},
        subcategory = component,
        tags        = ["regression", component],
    )


def record_operational(metric: str, value: Any, context: Any,
                       threshold: Any = None) -> int:
    return imraf.record(
        category    = Category.OPERATIONAL,
        title       = f"Operational: {metric}",
        data        = {"metric": metric, "value": value, "context": context,
                       "threshold": threshold},
        subcategory = metric,
        tags        = ["operational", metric],
    )


def record_ai_training(features: Any, prediction: Any, outcome: Any,
                       confidence: float, regime: str, context: Any) -> int:
    return imraf.record(
        category    = Category.AI_TRAINING,
        title       = f"AI Training: {regime}",
        data        = {"features": features, "prediction": prediction,
                       "outcome": outcome, "confidence": confidence,
                       "regime": regime, "context": context},
        subcategory = regime,
        tags        = ["ai_training", regime],
    )


def record_meta_learning(experiment_type: str, hypothesis: str, result: Any,
                         validation_method: str, success: bool) -> int:
    return imraf.record(
        category    = Category.META_LEARNING,
        title       = f"Meta-learning: {experiment_type}",
        data        = {"experiment_type": experiment_type, "hypothesis": hypothesis,
                       "result": result, "validation_method": validation_method,
                       "success": success},
        subcategory = experiment_type,
        tags        = ["meta_learning", "success" if success else "failure"],
    )


def record_developer(title: str, rationale: str, trade_offs: Any,
                     implementation_notes: str) -> int:
    return imraf.record(
        category    = Category.DEVELOPER,
        title       = title,
        data        = {"rationale": rationale, "trade_offs": trade_offs,
                       "implementation_notes": implementation_notes},
        subcategory = "developer",
        tags        = ["developer"],
    )


def record_deployment_event(version: str, event_type: str, description: str,
                             rollback_available: bool = True) -> int:
    return imraf.record(
        category    = Category.DEPLOYMENT,
        title       = f"Deployment {event_type}: v{version}",
        data        = {"version": version, "event_type": event_type,
                       "description": description,
                       "rollback_available": rollback_available},
        subcategory = event_type,
        tags        = ["deployment", event_type.lower(), f"v{version}"],
    )


def record_attribution(symbol: str, pnl: float, alpha_contribution: float,
                       regime_contribution: float, timing_contribution: float,
                       strategy: str) -> int:
    return imraf.record(
        category    = Category.ATTRIBUTION,
        title       = f"Attribution: {symbol} {strategy}",
        data        = {"symbol": symbol, "pnl": pnl,
                       "alpha_contribution": alpha_contribution,
                       "regime_contribution": regime_contribution,
                       "timing_contribution": timing_contribution,
                       "strategy": strategy},
        subcategory = strategy,
        tags        = ["attribution", symbol, strategy],
    )


def record_evolution_timeline(milestone: str, description: str,
                               impact: Any) -> int:
    return imraf.record(
        category    = Category.EVOLUTION_TL,
        title       = f"Evolution timeline: {milestone}",
        data        = {"milestone": milestone, "description": description,
                       "impact": impact},
        subcategory = "timeline",
        tags        = ["evolution_timeline", milestone],
    )


def record_ftd(
    ftd_id: str,
    title: str,
    status: str,           # PLANNED | IN_PROGRESS | DELIVERED | REJECTED | ROLLBACK
    delivered_by: str = "claude",
    completion_date: str = "",
    dependencies: list = None,
    verification_result: str = "",
    rollback_history: list = None,
    description: str = "",
) -> int:
    return imraf.record(
        category    = Category.FTD,
        title       = f"FTD {ftd_id}: {title}",
        data        = {
            "ftd_id": ftd_id, "title": title, "status": status,
            "delivered_by": delivered_by, "completion_date": completion_date,
            "dependencies": dependencies or [], "verification_result": verification_result,
            "rollback_history": rollback_history or [], "description": description,
        },
        subcategory = ftd_id,
        tags        = ["ftd", status.lower(), ftd_id],
    )


def record_delivery(
    title: str,
    developer: str,
    delivery_type: str,    # DEVELOPER_REPORT | DELIVERY_REPORT | IMPLEMENTATION_REPORT
    summary: str,
    files_changed: list = None,
    tests_status: str = "",
    version: str = "",
) -> int:
    return imraf.record(
        category    = Category.DELIVERY,
        title       = f"Delivery: {title}",
        data        = {
            "title": title, "developer": developer, "delivery_type": delivery_type,
            "summary": summary, "files_changed": files_changed or [],
            "tests_status": tests_status, "version": version,
        },
        subcategory = delivery_type,
        tags        = ["delivery", delivery_type.lower(), developer],
    )


def record_verifier(
    verifier_name: str,
    passed_tests: int,
    failed_tests: int,
    coverage: float,
    confidence: str,       # HIGH | MEDIUM | LOW
    historical_failures: list = None,
    component: str = "",
    notes: str = "",
) -> int:
    return imraf.record(
        category    = Category.VERIFIER,
        title       = f"Verifier: {verifier_name}",
        data        = {
            "verifier_name": verifier_name, "passed_tests": passed_tests,
            "failed_tests": failed_tests, "coverage": coverage,
            "confidence": confidence, "historical_failures": historical_failures or [],
            "component": component, "notes": notes,
            "pass_rate": round(passed_tests / max(passed_tests + failed_tests, 1) * 100, 1),
        },
        subcategory = component,
        tags        = ["verifier", confidence.lower(), component],
    )


def record_governance(
    decision: str,
    rationale: str,
    impact: str,
    stakeholder: str = "PHOENIX",
    category_type: str = "ROADMAP",  # ROADMAP | STRATEGIC | FEATURE | DISABLE | DELAY
    affected_components: list = None,
    review_date: str = "",
) -> int:
    return imraf.record(
        category    = Category.GOVERNANCE,
        title       = f"Governance: {decision[:80]}",
        data        = {
            "decision": decision, "rationale": rationale, "impact": impact,
            "stakeholder": stakeholder, "category_type": category_type,
            "affected_components": affected_components or [],
            "review_date": review_date,
        },
        subcategory = category_type,
        tags        = ["governance", category_type.lower(), stakeholder.lower()],
    )
