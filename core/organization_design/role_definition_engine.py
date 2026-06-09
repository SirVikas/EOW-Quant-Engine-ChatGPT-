"""Role Definition Engine — defines and tracks roles."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RoleDefinition:
    role_id: str
    title: str
    level: int
    department: str
    responsibilities: list
    required_certifications: list
    created_at: datetime


class RoleDefinitionEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._roles: dict[str, RoleDefinition] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ROL-{self._counter:03d}"

    def define_role(self, title: str, level: int, department: str,
                    responsibilities: list,
                    required_certifications: Optional[list] = None) -> RoleDefinition:
        with self._lock:
            role = RoleDefinition(
                role_id=self._next_id(),
                title=title,
                level=max(1, min(10, level)),
                department=department,
                responsibilities=responsibilities,
                required_certifications=required_certifications or [],
                created_at=datetime.utcnow(),
            )
            self._roles[role.role_id] = role
            return role

    def roles_in(self, department: str) -> list[dict]:
        with self._lock:
            return [
                {"role_id": r.role_id, "title": r.title, "level": r.level,
                 "responsibilities": r.responsibilities}
                for r in self._roles.values() if r.department == department
            ]

    def role_catalog(self) -> list[dict]:
        with self._lock:
            return [
                {"role_id": r.role_id, "title": r.title, "level": r.level,
                 "department": r.department}
                for r in sorted(self._roles.values(), key=lambda x: x.level)
            ]


role_definition_engine = RoleDefinitionEngine()
