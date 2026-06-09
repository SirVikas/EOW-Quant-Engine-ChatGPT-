"""
Recovery recommender — recommends a recovery procedure for an anomaly,
bridging to the Self-Healing Playbook Framework when a playbook exists.
"""
import threading
import time
from typing import List


class RecoveryRecommender:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._recommendations: List[dict] = []
        self._counter = 0

    def recommend(self, response_id: str, anomaly_type: str) -> dict:
        playbook_id = None
        steps: list = []
        try:
            from core.self_healing_playbooks.playbook_registry import playbook_registry
            playbook = playbook_registry.find_for(anomaly_type)
            if playbook:
                playbook_id = playbook.playbook_id
                steps = list(playbook.steps)
        except Exception:
            pass
        with self._lock:
            self._counter += 1
            recommendation = {
                "recommendation_id": f"ARV-{self._counter:03d}",
                "response_id": response_id,
                "anomaly_type": str(anomaly_type).upper(),
                "playbook_id": playbook_id,
                "steps": steps or ["No playbook registered — manual investigation required"],
                "recommended_at": time.time(),
            }
            self._recommendations.append(recommendation)
            return recommendation

    def recommendation_summary(self) -> dict:
        with self._lock:
            recommendations = list(self._recommendations)
            with_playbook = sum(1 for r in recommendations if r["playbook_id"])
            return {
                "total": len(recommendations),
                "with_playbook": with_playbook,
                "manual": len(recommendations) - with_playbook,
                "recent": recommendations[-10:],
            }


recovery_recommender = RecoveryRecommender()
