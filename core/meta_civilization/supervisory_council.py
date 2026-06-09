"""Supervisory Council — governing council over multiple PHOENIX civilizations."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CouncilMember:
    council_member_id: str
    civilization_id: str
    member_role: str
    joined_at: datetime


class SupervisoryCouncil:
    def __init__(self):
        self._lock = threading.RLock()
        self._members: dict[str, CouncilMember] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"SCM-{self._counter:03d}"

    def add_member(self, civilization_id: str, member_role: str) -> CouncilMember:
        with self._lock:
            m = CouncilMember(
                council_member_id=self._next_id(),
                civilization_id=civilization_id,
                member_role=member_role,
                joined_at=datetime.utcnow(),
            )
            self._members[m.council_member_id] = m
            return m

    def council_members(self) -> list[dict]:
        with self._lock:
            return [
                {"council_member_id": m.council_member_id,
                 "civilization_id": m.civilization_id,
                 "member_role": m.member_role,
                 "joined_at": m.joined_at.isoformat()}
                for m in self._members.values()
            ]

    def council_quorum(self) -> bool:
        with self._lock:
            return len(self._members) >= 3


supervisory_council = SupervisoryCouncil()
