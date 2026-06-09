"""Group Reasoning Engine — structured multi-agent reasoning sessions."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class ReasoningSession:
    session_id: str
    topic: str
    participants: List[str]
    premises: List[str]
    conclusions: List[str]
    reasoning_method: str  # DEDUCTIVE/INDUCTIVE/ABDUCTIVE/ANALOGICAL
    confidence: float  # 0-1
    created_at: str


class GroupReasoningEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: dict[str, ReasoningSession] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"GRS-{self._counter:03d}"

    def start_session(self, topic: str, participants: List[str],
                      reasoning_method: str = "INDUCTIVE") -> str:
        with self._lock:
            session_id = self._next_id()
            s = ReasoningSession(
                session_id=session_id,
                topic=topic,
                participants=list(participants),
                premises=[],
                conclusions=[],
                reasoning_method=reasoning_method,
                confidence=0.0,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._sessions[session_id] = s
            return session_id

    def add_premise(self, session_id: str, premise: str) -> bool:
        with self._lock:
            s = self._sessions.get(session_id)
            if s is None:
                return False
            s.premises.append(premise)
            return True

    def conclude(self, session_id: str, conclusions: List[str], confidence: float) -> bool:
        with self._lock:
            s = self._sessions.get(session_id)
            if s is None:
                return False
            s.conclusions = list(conclusions)
            s.confidence = confidence
            return True

    def all_sessions(self, limit: int = 20) -> List[dict]:
        with self._lock:
            sessions = sorted(self._sessions.values(),
                              key=lambda x: x.created_at, reverse=True)
            return [asdict(s) for s in sessions[:limit]]

    def reasoning_stats(self) -> dict:
        with self._lock:
            by_method: dict[str, int] = {}
            concluded = 0
            total_conf = 0.0
            for s in self._sessions.values():
                by_method[s.reasoning_method] = by_method.get(s.reasoning_method, 0) + 1
                if s.conclusions:
                    concluded += 1
                    total_conf += s.confidence
            total = len(self._sessions)
            avg_conf = total_conf / concluded if concluded else 0
            return {
                "total": total,
                "by_method": by_method,
                "avg_confidence": avg_conf,
                "concluded_count": concluded,
            }


group_reasoning_engine = GroupReasoningEngine()
