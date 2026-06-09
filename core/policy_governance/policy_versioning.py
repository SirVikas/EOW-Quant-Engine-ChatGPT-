"""Policy versioning — tracks policy version history."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class PolicyVersion:
    version_id: str
    policy_id: str
    version_number: int
    content: dict
    changed_by: str
    change_reason: str
    created_at: str


class PolicyVersioning:
    def __init__(self):
        self._lock = threading.RLock()
        self._versions: list = []
        self._counter = 0
        self._version_map: dict = {}  # policy_id -> current version number

    def create_version(self, policy_id: str, content: dict, changed_by: str,
                       change_reason: str) -> str:
        with self._lock:
            self._counter += 1
            version_number = self._version_map.get(policy_id, 0) + 1
            self._version_map[policy_id] = version_number
            v = PolicyVersion(
                version_id=f"PV-{self._counter:03d}",
                policy_id=policy_id,
                version_number=version_number,
                content=content,
                changed_by=changed_by,
                change_reason=change_reason,
                created_at=datetime.utcnow().isoformat(),
            )
            self._versions.append(v)
            return v.version_id

    def get_version(self, policy_id: str, version_number: Optional[int] = None) -> dict:
        with self._lock:
            policy_versions = [v for v in self._versions if v.policy_id == policy_id]
            if not policy_versions:
                return {}
            if version_number is None:
                return asdict(max(policy_versions, key=lambda x: x.version_number))
            for v in policy_versions:
                if v.version_number == version_number:
                    return asdict(v)
            return {}

    def version_history(self, policy_id: str) -> list:
        with self._lock:
            return sorted([asdict(v) for v in self._versions if v.policy_id == policy_id],
                          key=lambda x: x["version_number"])


policy_versioning = PolicyVersioning()
