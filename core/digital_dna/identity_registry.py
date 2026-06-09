"""Identity Registry — PHOENIX core identity dimensions."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional

SEED_IDENTITY = [
    ("SYSTEM_NAME", "PHOENIX", "Core system name identifier", True),
    ("MISSION", "Institutional Autonomous Trading Intelligence Platform", "System mission statement", True),
    ("PRIMARY_OBJECTIVE", "Capital Preservation with Intelligent Growth", "Primary operational objective", True),
    ("GOVERNANCE_MODEL", "Constitutional Democratic with Human Override", "Governance structure", True),
    ("LEARNING_PARADIGM", "Evidence-First Institutional Learning", "How the system learns", True),
    ("TRUST_MODEL", "Earned Trust with Evidence Decay", "Trust establishment and maintenance model", True),
    ("EVOLUTION_PHILOSOPHY", "Governed Controlled Evolution", "Philosophy for system evolution", True),
]


@dataclass
class Identity:
    identity_id: str
    dimension: str
    value: str
    description: str
    established_at: str
    immutable: bool


class IdentityRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._identities: dict[str, Identity] = {}
        now = datetime.now(timezone.utc).isoformat()
        for i, (dimension, value, desc, immutable) in enumerate(SEED_IDENTITY, 1):
            identity = Identity(
                identity_id=f"IDN-{i:03d}",
                dimension=dimension,
                value=value,
                description=desc,
                established_at=now,
                immutable=immutable,
            )
            self._identities[dimension] = identity

    def get(self, dimension: str) -> Optional[dict]:
        with self._lock:
            i = self._identities.get(dimension)
            return asdict(i) if i else None

    def all_identity(self) -> List[dict]:
        with self._lock:
            return [asdict(i) for i in self._identities.values()]

    def identity_card(self) -> dict:
        with self._lock:
            return {dim: identity.value for dim, identity in self._identities.items()}


identity_registry = IdentityRegistry()
