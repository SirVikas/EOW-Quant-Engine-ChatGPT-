"""Capability Registry — tracks all PHOENIX capabilities and their lifecycle stages."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List

STAGE_ORDER = ["EXPERIMENTAL", "EMERGING", "OPERATIONAL", "MATURE", "LEGACY", "RETIRED"]

CORE_CAPABILITIES = [
    ("NEXUS", "PHOENIX Institutional Intelligence Layer", "INTELLIGENCE"),
    ("PCCP", "Portfolio and Capital Control Platform", "TRADING"),
    ("CTAO", "Continuous Truth and Adaptive Optimization", "GOVERNANCE"),
    ("Constitution", "Constitutional governance and constraint enforcement", "GOVERNANCE"),
    ("Trust_Fabric", "Multi-dimensional trust scoring and decay", "TRUST"),
    ("Observability", "Full-spectrum system observability platform", "REPORTING"),
    ("Command_Center", "Operational command and control center", "GOVERNANCE"),
    ("Evidence_Warehouse", "Institutional evidence collection and storage", "RESEARCH"),
    ("Knowledge_Graph", "Entity relationship knowledge graph", "INTELLIGENCE"),
    ("Autonomous_Improvement", "Self-directed improvement engine", "RECOVERY"),
]


@dataclass
class Capability:
    cap_id: str
    name: str
    description: str
    category: str
    maturity_stage: str
    version: str
    introduced_at: str
    last_assessed: str


class CapabilityRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._capabilities: dict[str, Capability] = {}
        self._counter = 0
        # Seed core capabilities at MATURE stage
        for name, desc, category in CORE_CAPABILITIES:
            cap_id = self._register_internal(name, desc, category, "MATURE", "1.0.0")

    def _next_id(self) -> str:
        self._counter += 1
        return f"CAP-{self._counter:03d}"

    def _register_internal(self, name: str, description: str, category: str,
                           maturity_stage: str, version: str) -> str:
        cap_id = self._next_id()
        now = datetime.now(timezone.utc).isoformat()
        cap = Capability(
            cap_id=cap_id,
            name=name,
            description=description,
            category=category,
            maturity_stage=maturity_stage,
            version=version,
            introduced_at=now,
            last_assessed=now,
        )
        self._capabilities[cap_id] = cap
        return cap_id

    def register(self, name: str, description: str, category: str,
                 maturity_stage: str = "EXPERIMENTAL", version: str = "1.0.0") -> str:
        with self._lock:
            return self._register_internal(name, description, category, maturity_stage, version)

    def advance_stage(self, cap_id: str) -> bool:
        with self._lock:
            cap = self._capabilities.get(cap_id)
            if cap is None:
                return False
            idx = STAGE_ORDER.index(cap.maturity_stage) if cap.maturity_stage in STAGE_ORDER else -1
            if idx < 0 or idx >= len(STAGE_ORDER) - 1:
                return False
            cap.maturity_stage = STAGE_ORDER[idx + 1]
            cap.last_assessed = datetime.now(timezone.utc).isoformat()
            return True

    def retire(self, cap_id: str) -> bool:
        with self._lock:
            cap = self._capabilities.get(cap_id)
            if cap is None:
                return False
            cap.maturity_stage = "RETIRED"
            cap.last_assessed = datetime.now(timezone.utc).isoformat()
            return True

    def by_stage(self, stage: str) -> List[dict]:
        with self._lock:
            return [asdict(c) for c in self._capabilities.values() if c.maturity_stage == stage]

    def all_capabilities(self) -> List[dict]:
        with self._lock:
            return [asdict(c) for c in self._capabilities.values()]

    def capability_stats(self) -> dict:
        with self._lock:
            by_stage: dict[str, int] = {}
            by_category: dict[str, int] = {}
            mature_count = 0
            for cap in self._capabilities.values():
                by_stage[cap.maturity_stage] = by_stage.get(cap.maturity_stage, 0) + 1
                by_category[cap.category] = by_category.get(cap.category, 0) + 1
                if cap.maturity_stage == "MATURE":
                    mature_count += 1
            return {
                "total": len(self._capabilities),
                "by_stage": by_stage,
                "by_category": by_category,
                "mature_count": mature_count,
            }


capability_registry = CapabilityRegistry()
