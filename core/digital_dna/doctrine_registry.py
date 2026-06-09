"""Doctrine Registry — immutable and mutable institutional doctrines."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional

SEED_DOCTRINES = [
    ("Capital First", "Never risk unrecoverable capital loss", "RISK", True),
    ("Truth Always", "System truth takes precedence over comfort", "TRADING", True),
    ("Evidence Required", "No action without evidence basis", "GOVERNANCE", True),
    ("Govern Before Automate", "Governance precedes any autonomous action", "GOVERNANCE", True),
    ("Learn From Everything", "All outcomes become institutional lessons", "EVOLUTION", True),
    ("Trust Must Be Earned", "Trust is never assumed, only proven", "TRUST", True),
    ("Audit Everything", "No decision escapes the audit trail", "GOVERNANCE", True),
    ("Humans Override", "Human authority supersedes all autonomous systems", "GOVERNANCE", True),
    ("Adapt or Decline", "Non-adapting capabilities become liabilities", "EVOLUTION", False),
    ("Complexity Kills", "Prefer simple robust systems over complex fragile ones", "TRADING", False),
]


@dataclass
class Doctrine:
    doctrine_id: str
    title: str
    statement: str
    category: str
    immutable: bool
    version: int
    created_at: str


class DoctrineRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._doctrines: dict[str, Doctrine] = {}
        self._counter = 0
        for title, statement, category, immutable in SEED_DOCTRINES:
            self._seed(title, statement, category, immutable)

    def _next_id(self) -> str:
        self._counter += 1
        return f"DOC-{self._counter:03d}"

    def _seed(self, title: str, statement: str, category: str, immutable: bool) -> str:
        doc_id = self._next_id()
        now = datetime.now(timezone.utc).isoformat()
        d = Doctrine(
            doctrine_id=doc_id,
            title=title,
            statement=statement,
            category=category,
            immutable=immutable,
            version=1,
            created_at=now,
        )
        self._doctrines[doc_id] = d
        return doc_id

    def get(self, doctrine_id: str) -> Optional[dict]:
        with self._lock:
            d = self._doctrines.get(doctrine_id)
            return asdict(d) if d else None

    def all_doctrines(self, category: Optional[str] = None) -> List[dict]:
        with self._lock:
            doctrines = list(self._doctrines.values())
            if category:
                doctrines = [d for d in doctrines if d.category == category]
            return [asdict(d) for d in doctrines]

    def doctrine_stats(self) -> dict:
        with self._lock:
            by_category: dict[str, int] = {}
            immutable_count = mutable_count = 0
            for d in self._doctrines.values():
                by_category[d.category] = by_category.get(d.category, 0) + 1
                if d.immutable:
                    immutable_count += 1
                else:
                    mutable_count += 1
            return {
                "total": len(self._doctrines),
                "immutable": immutable_count,
                "mutable": mutable_count,
                "by_category": by_category,
            }


doctrine_registry = DoctrineRegistry()
