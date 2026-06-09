"""Risk Response Director — directs risk responses."""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RiskResponse:
    response_id: str
    esc_id: str
    response_action: str
    responder: str
    executed_at: datetime
    outcome: str


class RiskResponseDirector:
    def __init__(self):
        self._lock = threading.RLock()
        self._responses: dict[str, RiskResponse] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RSP-{self._counter:03d}"

    def direct_response(self, esc_id: str, response_action: str,
                        responder: str) -> RiskResponse:
        with self._lock:
            r = RiskResponse(
                response_id=self._next_id(),
                esc_id=esc_id,
                response_action=response_action,
                responder=responder,
                executed_at=datetime.utcnow(),
                outcome="MITIGATED",  # default optimistic; caller can override via complete_response
            )
            self._responses[r.response_id] = r
            return r

    def complete_response(self, response_id: str, outcome: str) -> Optional[RiskResponse]:
        with self._lock:
            r = self._responses.get(response_id)
            if r:
                r.outcome = outcome
            return r

    def response_effectiveness(self) -> dict:
        with self._lock:
            if not self._responses:
                return {"total_responses": 0, "effectiveness_pct": 100.0}
            mitigated = sum(1 for r in self._responses.values() if r.outcome == "MITIGATED")
            pct = round(mitigated / len(self._responses) * 100, 1)
            return {"total_responses": len(self._responses), "effectiveness_pct": pct}


risk_response_director = RiskResponseDirector()
