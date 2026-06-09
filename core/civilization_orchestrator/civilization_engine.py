"""Civilization Engine — top-level civilization orchestration layer."""
import threading
from datetime import datetime, timezone


class CivilizationEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def civilization_status(self) -> dict:
        with self._lock:
            from core.civilization_orchestrator.master_orchestrator import master_orchestrator
            from core.civilization_orchestrator.institutional_alignment_engine import institutional_alignment_engine
            from core.civilization_orchestrator.long_horizon_director import long_horizon_director

            orch_status = master_orchestrator.orchestration_status()
            alignment = institutional_alignment_engine.alignment_summary()
            horizon = long_horizon_director.horizon_outlook()

            return {
                "orchestration": orch_status,
                "institutional_alignment": alignment,
                "long_horizon": horizon,
                "civilization_health": "HEALTHY" if orch_status["status"] == "READY" else "DEGRADED",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def one_liner(self) -> str:
        with self._lock:
            from core.civilization_orchestrator.institutional_alignment_engine import institutional_alignment_engine
            from core.civilization_orchestrator.long_horizon_director import long_horizon_director

            alignment = institutional_alignment_engine.alignment_summary()
            horizon = long_horizon_director.horizon_outlook()
            aligned_count = alignment.get("aligned", 0)
            active_directives = horizon.get("active_directives", 0)
            return (
                f"PHOENIX Civilization Layer: {aligned_count} layers aligned, "
                f"{active_directives} horizon directives active"
            )

    def summary(self) -> dict:
        with self._lock:
            status = self.civilization_status()
            return {
                "one_liner": self.one_liner(),
                "health": status["civilization_health"],
                "aligned_layers": status["institutional_alignment"].get("aligned", 0),
                "total_layers": status["institutional_alignment"].get("total_layers", 0),
                "active_directives": status["long_horizon"].get("active_directives", 0),
                "system_ready": status["orchestration"]["status"] == "READY",
            }


civilization_engine = CivilizationEngine()
