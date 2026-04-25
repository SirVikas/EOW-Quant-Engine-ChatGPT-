"""
FTD-030B Part 1 — Memory Store

Append-only JSONL store for correction cycle outcomes.
Partial records are rejected. Records are written after resolve_cycle().
"""
from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, List, Optional

STORE_PATH = "reports/learning_memory/memory_store.jsonl"

_REQUIRED_FIELDS = {"cycle_id", "timestamp", "context", "change", "outcome", "validation", "decision"}
_REQUIRED_CONTEXT = {"regime", "volatility", "timeframe", "instrument"}
_REQUIRED_CHANGE = {"parameter", "direction"}
_REQUIRED_OUTCOME = {"score_delta", "rollback"}
_REQUIRED_VALIDATION = {"meta_score", "contradiction"}
_REQUIRED_DECISION = {"ai_mode", "rationale"}


class MemoryStore:
    """
    Append-only JSONL store for learning memory records.
    Thread-safe at write level (file append, no partial flush).
    """

    MODULE = "MEMORY_STORE"
    PHASE  = "030B"

    def __init__(self, path: str = STORE_PATH):
        self._path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def append(self, record: Dict[str, Any]) -> bool:
        """Validate and append a record. Returns False if record is partial/invalid."""
        if not self._validate(record):
            return False
        record["_stored_ts"] = int(time.time() * 1000)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        return True

    def load_all(self) -> List[Dict[str, Any]]:
        """Load all records from JSONL. Skips malformed lines."""
        if not os.path.exists(self._path):
            return []
        records: List[Dict[str, Any]] = []
        with open(self._path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    def recent(self, n: int = 100) -> List[Dict[str, Any]]:
        return self.load_all()[-n:]

    def count(self) -> int:
        return len(self.load_all())

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate(self, r: Dict[str, Any]) -> bool:
        if not _REQUIRED_FIELDS.issubset(r.keys()):
            return False
        if not _REQUIRED_CONTEXT.issubset(r.get("context", {}).keys()):
            return False
        if not _REQUIRED_CHANGE.issubset(r.get("change", {}).keys()):
            return False
        if not _REQUIRED_OUTCOME.issubset(r.get("outcome", {}).keys()):
            return False
        if not _REQUIRED_VALIDATION.issubset(r.get("validation", {}).keys()):
            return False
        if not _REQUIRED_DECISION.issubset(r.get("decision", {}).keys()):
            return False
        direction = r["change"].get("direction", "")
        if direction not in ("UP", "DOWN"):
            return False
        return True

    @staticmethod
    def build_record(
        cycle_id: str,
        regime: str,
        volatility: str,
        timeframe: str,
        instrument: str,
        parameter: str,
        direction: str,
        score_delta: float,
        rollback: bool,
        meta_score: float,
        contradiction: bool,
        ai_mode: str,
        rationale: str,
    ) -> Dict[str, Any]:
        return {
            "cycle_id": cycle_id,
            "timestamp": time.time(),
            "context": {
                "regime": regime,
                "volatility": volatility,
                "timeframe": timeframe,
                "instrument": instrument,
            },
            "change": {
                "parameter": parameter,
                "direction": direction,
            },
            "outcome": {
                "score_delta": round(score_delta, 4),
                "rollback": rollback,
            },
            "validation": {
                "meta_score": round(meta_score, 2),
                "contradiction": contradiction,
            },
            "decision": {
                "ai_mode": ai_mode,
                "rationale": rationale,
            },
        }
