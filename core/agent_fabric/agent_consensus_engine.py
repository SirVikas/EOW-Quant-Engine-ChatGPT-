"""Agent consensus engine for multi-agent coordination."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import Counter


@dataclass
class ConsensusRound:
    round_id: str
    topic: str
    participating_agents: list
    votes: dict
    result: str
    confidence: float
    completed_at: str


class AgentConsensusEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._rounds: list = []
        self._counter = 0

    def run_consensus(self, topic: str, participating_agents: list, vote_options: list) -> dict:
        with self._lock:
            self._counter += 1
            votes = {}
            for idx, agent_id in enumerate(participating_agents):
                votes[agent_id] = vote_options[idx % len(vote_options)]
            vote_counts = Counter(votes.values())
            result, _ = vote_counts.most_common(1)[0]
            confidence = vote_counts[result] / max(1, len(participating_agents))
            r = ConsensusRound(
                round_id=f"CON-{self._counter:03d}",
                topic=topic,
                participating_agents=participating_agents,
                votes=votes,
                result=result,
                confidence=confidence,
                completed_at=datetime.utcnow().isoformat(),
            )
            self._rounds.append(r)
            return asdict(r)

    def recent_rounds(self, limit: int = 10) -> list:
        with self._lock:
            return [asdict(r) for r in self._rounds[-limit:]]

    def consensus_stats(self) -> dict:
        with self._lock:
            total = len(self._rounds)
            avg_conf = sum(r.confidence for r in self._rounds) / max(1, total)
            result_counts = Counter(r.result for r in self._rounds)
            most_common = result_counts.most_common(1)[0][0] if result_counts else ""
            return {"total_rounds": total, "avg_confidence": avg_conf, "most_common_result": most_common}


agent_consensus_engine = AgentConsensusEngine()
