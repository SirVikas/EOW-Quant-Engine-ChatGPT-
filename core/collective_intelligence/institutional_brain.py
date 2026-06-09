"""Institutional Brain — simulated collective reasoning across all institutional layers."""
import threading
from datetime import datetime, timezone


class InstitutionalBrain:
    def __init__(self):
        self._lock = threading.RLock()

    def think(self, question: str) -> dict:
        with self._lock:
            from core.collective_intelligence.group_reasoning_engine import group_reasoning_engine
            from core.institutional_memory.institutional_wisdom_registry import institutional_wisdom_registry
            from core.meta_knowledge.knowledge_value_ranker import knowledge_value_ranker

            agents_consulted = []
            try:
                from core.agent_fabric.agent_registry import agent_registry
                agents_consulted = [a.get("name", "agent") for a in agent_registry.active_agents()[:5]]
            except Exception:
                agents_consulted = ["PHOENIX_CORE"]

            session_id = group_reasoning_engine.start_session(
                topic=question,
                participants=agents_consulted,
                reasoning_method="INDUCTIVE",
            )

            # Add wisdom as premises
            premises_used = []
            for w in institutional_wisdom_registry.canonical_wisdom()[:5]:
                group_reasoning_engine.add_premise(session_id, w["principle"])
                premises_used.append(w["principle"])

            # Add top knowledge insights
            for item in knowledge_value_ranker.most_valuable(3):
                premise = f"High-value knowledge: {item['subject_id']}"
                group_reasoning_engine.add_premise(session_id, premise)
                premises_used.append(premise)

            # Synthesize conclusion
            conclusion = f"Based on {len(premises_used)} institutional premises, the system is operating within governed parameters."
            confidence = min(0.9, 0.5 + len(premises_used) * 0.05)
            group_reasoning_engine.conclude(session_id, [conclusion], confidence)

            return {
                "question": question,
                "agents_consulted": agents_consulted,
                "premises_used": premises_used,
                "conclusion": conclusion,
                "confidence": confidence,
                "reasoning_session_id": session_id,
            }

    def brain_status(self) -> dict:
        with self._lock:
            from core.collective_intelligence.group_reasoning_engine import group_reasoning_engine
            from core.institutional_memory.institutional_wisdom_registry import institutional_wisdom_registry

            active_agents = 0
            try:
                from core.agent_fabric.agent_registry import agent_registry
                active_agents = len(agent_registry.active_agents())
            except Exception:
                pass

            wisdom_count = institutional_wisdom_registry.wisdom_stats()["total"]
            sessions = group_reasoning_engine.reasoning_stats()["total"]

            brain_health = "OPTIMAL" if sessions > 5 else "OPERATIONAL"

            return {
                "active_agents": active_agents,
                "wisdom_count": wisdom_count,
                "reasoning_sessions": sessions,
                "brain_health": brain_health,
            }


institutional_brain = InstitutionalBrain()
