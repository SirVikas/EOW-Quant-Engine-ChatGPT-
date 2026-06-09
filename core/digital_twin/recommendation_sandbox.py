"""
PHOENIX Digital Twin — Recommendation Sandbox
Safe simulation environment for testing recommendations before deployment.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


@dataclass
class SandboxRun:
    run_id: str
    rec_id: str
    rec_description: str
    simulated_parameters: Dict
    sim_outcome: Dict
    safe_to_deploy: Optional[bool]
    risk_flags: List[str]
    sandbox_verdict: str  # SAFE/CAUTION/UNSAFE/BLOCKED
    created_at: str


class RecommendationSandbox:
    def __init__(self):
        self._lock = threading.RLock()
        self._runs: Dict[str, SandboxRun] = {}

    def test_recommendation(
        self, rec_id: str, rec_description: str, parameters: dict = None
    ) -> dict:
        from core.digital_twin.scenario_simulator import scenario_simulator

        params = parameters or {}
        sim_result = scenario_simulator.simulate(
            name=f"sandbox_{rec_id}", parameters=params
        )

        risk_flags = []
        if sim_result["drawdown_projection"] > 0.10:
            risk_flags.append("HIGH_DRAWDOWN_RISK")
        if sim_result["capital_impact_pct"] < -5:
            risk_flags.append("CAPITAL_RISK")
        if sim_result["stability_score"] < 0.6:
            risk_flags.append("STABILITY_RISK")

        n = len(risk_flags)
        if sim_result["risk_score"] > 0.8 or n >= 3:
            verdict = "BLOCKED"
        elif n == 2:
            verdict = "UNSAFE"
        elif n == 1:
            verdict = "CAUTION"
        else:
            verdict = "SAFE"

        safe_to_deploy = verdict in ("SAFE", "CAUTION")
        run_id = f"SBX-{uuid.uuid4().hex[:8].upper()}"
        run = SandboxRun(
            run_id=run_id,
            rec_id=rec_id,
            rec_description=rec_description,
            simulated_parameters=params,
            sim_outcome=sim_result,
            safe_to_deploy=safe_to_deploy,
            risk_flags=risk_flags,
            sandbox_verdict=verdict,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._runs[run_id] = run
        return asdict(run)

    def pending_tests(self) -> list:
        with self._lock:
            return [asdict(r) for r in self._runs.values() if r.safe_to_deploy is None]

    def all_runs(self, verdict_filter: str = None) -> list:
        with self._lock:
            runs = list(self._runs.values())
        if verdict_filter:
            runs = [r for r in runs if r.sandbox_verdict == verdict_filter]
        return [asdict(r) for r in runs]

    def sandbox_stats(self) -> dict:
        with self._lock:
            runs = list(self._runs.values())
        total = len(runs)
        safe = sum(1 for r in runs if r.sandbox_verdict == "SAFE")
        caution = sum(1 for r in runs if r.sandbox_verdict == "CAUTION")
        unsafe = sum(1 for r in runs if r.sandbox_verdict == "UNSAFE")
        blocked = sum(1 for r in runs if r.sandbox_verdict == "BLOCKED")
        rate = (safe + caution) / total if total else 0.0
        return {
            "total_tested": total,
            "safe": safe,
            "caution": caution,
            "unsafe": unsafe,
            "blocked": blocked,
            "safe_deployment_rate": round(rate, 4),
        }


recommendation_sandbox = RecommendationSandbox()
