"""Strategic Goal Engine — evaluates actions against the PHOENIX goal hierarchy."""
import threading


_RISK_KEYWORDS = {"increase risk", "bypass", "ignore capital", "skip gate", "override limit"}


class StrategicGoalEngine:
    GOAL_TIERS = {
        "CAPITAL_PRESERVATION": {"tier": 1, "priority": 100, "description": "Protect capital above all else"},
        "PROFITABILITY":        {"tier": 2, "priority": 80,  "description": "Generate returns within risk limits"},
        "SYSTEM_STABILITY":     {"tier": 3, "priority": 60,  "description": "Maintain operational reliability"},
        "ADAPTATION":           {"tier": 4, "priority": 40,  "description": "Learn and improve continuously"},
        "OBSERVABILITY":        {"tier": 5, "priority": 20,  "description": "Maintain visibility into all operations"},
    }

    def __init__(self):
        self._lock = threading.RLock()

    def evaluate_against_goals(self, action_description: str, affected_goals: list) -> dict:
        with self._lock:
            goal_scores = {}
            highest_priority_goal = None
            highest_priority = -1
            violates_tier12 = False

            for goal in affected_goals:
                tier_info = self.GOAL_TIERS.get(goal)
                if tier_info:
                    priority = tier_info["priority"]
                    goal_scores[goal] = priority
                    if priority > highest_priority:
                        highest_priority = priority
                        highest_priority_goal = goal
                    if tier_info["tier"] in (1, 2):
                        violates_tier12 = True

            approved = not violates_tier12
            recommendation = (
                "APPROVED: Action aligns with goal hierarchy."
                if approved else
                "REJECTED: Action affects Tier 1 or 2 goals — capital preservation or profitability at risk."
            )

            return {
                "action": action_description,
                "goal_scores": goal_scores,
                "highest_priority_goal": highest_priority_goal,
                "recommendation": recommendation,
                "approved": approved,
            }

    def resolve_conflict_by_goals(self, option_a: str, goals_a: list,
                                   option_b: str, goals_b: list) -> dict:
        with self._lock:
            score_a = sum(self.GOAL_TIERS.get(g, {}).get("priority", 0) for g in goals_a)
            score_b = sum(self.GOAL_TIERS.get(g, {}).get("priority", 0) for g in goals_b)
            winner = option_a if score_a >= score_b else option_b
            return {
                "winner": winner,
                "option_a": option_a, "score_a": score_a,
                "option_b": option_b, "score_b": score_b,
            }

    def goal_hierarchy_report(self) -> dict:
        return {"goals": self.GOAL_TIERS}

    def constitutional_check(self, action_description: str) -> dict:
        with self._lock:
            lower = action_description.lower()
            warnings = [kw for kw in _RISK_KEYWORDS if kw in lower]
            return {
                "passed": len(warnings) == 0,
                "warnings": warnings,
            }


strategic_goal_engine = StrategicGoalEngine()
