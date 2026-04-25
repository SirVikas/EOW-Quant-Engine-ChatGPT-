"""
FTD-030B — memory_store.py
Append-only JSONL store for learning memory records.

Schema (one record per correction cycle, stored after resolve_cycle()):
  cycle_id, timestamp, context, change, outcome, validation, decision

Rules:
  - Partial records are REJECTED (all 7 top-level keys must be present)
  - Append-only — existing records are never modified
  - Loaded into memory by PatternIndexer at startup
"""
from __future__ import annotations

import json
import pathlib
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

STORE_PATH    = pathlib.Path("reports/learning_memory/memory_store.jsonl")
REQUIRED_KEYS = {"cycle_id", "timestamp", "context", "change", "outcome", "validation", "decision"}

VOLATILITY_BUCKETS = ("LOW", "MED", "HIGH")   # ATR% < 0.1 / 0.1–0.3 / >0.3


@dataclass
class MemoryRecord:
    cycle_id:   str
    timestamp:  float
    context:    Dict[str, str]   # regime, volatility, timeframe, instrument
    change:     Dict[str, str]   # parameter, direction (UP|DOWN)
    outcome:    Dict[str, Any]   # score_delta: float, rollback: bool
    validation: Dict[str, Any]   # meta_score: float, contradiction: bool
    decision:   Dict[str, str]   # ai_mode, rationale

    @classmethod
    def build(
        cls,
        cycle_id:       str,
        regime:         str,
        volatility_pct: float,
        parameter:      str,
        direction:       str,
        score_delta:    float,
        rollback:       bool,
        meta_score:     float,
        contradiction:  bool,
        ai_mode:        str = "AUTO",
        rationale:      str = "",
        timeframe:      str = "SCALP",
        instrument:     str = "CRYPTO",
    ) -> "MemoryRecord":
        vol_bucket = (
            "LOW"  if volatility_pct < 0.1 else
            "HIGH" if volatility_pct > 0.3 else "MED"
        )
        return cls(
            cycle_id=cycle_id,
            timestamp=time.time(),
            context={"regime": regime, "volatility": vol_bucket,
                     "timeframe": timeframe, "instrument": instrument},
            change={"parameter": parameter, "direction": direction.upper()},
            outcome={"score_delta": round(score_delta, 4), "rollback": rollback},
            validation={"meta_score": round(meta_score, 2), "contradiction": contradiction},
            decision={"ai_mode": ai_mode, "rationale": rationale},
        )

    def is_complete(self) -> bool:
        d = asdict(self)
        return REQUIRED_KEYS.issubset(d.keys()) and all(v is not None for v in d.values())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MemoryStore:
    """
    Append-only JSONL persisted memory store.
    Keeps an in-memory list for fast access; writes each record to disk atomically.
    """

    def __init__(self, path: pathlib.Path = STORE_PATH):
        self._path    = path
        self._records: List[MemoryRecord] = []
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, record: MemoryRecord) -> bool:
        """Append record. Returns False (and rejects) if record is incomplete."""
        if not record.is_complete():
            return False
        self._records.append(record)
        self._append_to_disk(record)
        return True

    def all_records(self) -> List[MemoryRecord]:
        return list(self._records)

    def recent(self, n: int = 50) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._records[-n:]]

    def count(self) -> int:
        return len(self._records)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not self._path.exists():
            return
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if not REQUIRED_KEYS.issubset(d.keys()):
                    continue
                self._records.append(MemoryRecord(**d))
            except Exception:
                pass

    def _append_to_disk(self, record: MemoryRecord) -> None:
        try:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), default=str) + "\n")
        except Exception:
            pass

    def summary(self) -> Dict[str, Any]:
        return {
            "total_records": self.count(),
            "path": str(self._path),
            "module": "MEMORY_STORE",
            "phase": "030B",
        }
