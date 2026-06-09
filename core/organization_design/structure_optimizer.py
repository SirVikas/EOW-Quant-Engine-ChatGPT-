"""Structure Optimizer — recommends structural improvements."""
import threading


class StructureOptimizer:
    def __init__(self):
        self._lock = threading.RLock()

    def analyze(self) -> list[dict]:
        from core.organization_design.organization_registry import organization_registry
        from core.workforce_management.agent_hr_engine import agent_hr_engine

        findings = []
        org_tree = organization_registry.org_tree()
        active_agents = agent_hr_engine.active_agents()

        # Units without a head
        headless = [u for u in org_tree if not u["head_agent_id"]]
        if headless:
            findings.append({
                "area": "Leadership",
                "finding": f"{len(headless)} org unit(s) without a designated head",
                "recommendation": "Assign head agents to all org units",
            })

        # Check agent-to-unit ratio
        if org_tree and active_agents:
            ratio = len(active_agents) / len(org_tree)
            if ratio < 1.0:
                findings.append({
                    "area": "Staffing",
                    "finding": f"Low agent-to-unit ratio: {ratio:.1f}",
                    "recommendation": "Hire additional agents or consolidate org units",
                })

        if not findings:
            findings.append({
                "area": "Overall",
                "finding": "No structural issues detected",
                "recommendation": "Continue monitoring",
            })

        return findings

    def optimization_report(self) -> dict:
        findings = self.analyze()
        return {"findings_count": len(findings), "findings": findings}


structure_optimizer = StructureOptimizer()
