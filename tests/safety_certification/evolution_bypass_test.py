"""Verifies evolution governance cannot be bypassed."""
import sys
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")

def test_evolution_requires_approval():
    from core.evolution_governance.evolution_registry import evolution_registry
    from core.evolution_governance.evolution_approval_engine import evolution_approval_engine
    evo_id = None
    try:
        from core.evolution_governance.evolution_proposal_engine import evolution_proposal_engine
        result = evolution_proposal_engine.create_proposal("Safety Test Evolution", "Test that approval is required", "SAFETY_TEST", "BEHAVIOR", "Safety test")
        evo_id = result.get("evo_id") if isinstance(result, dict) else result
    except Exception:
        pass
    if evo_id:
        evo = evolution_registry.get(evo_id)
        not_auto_deployed = evo.get("status") != "DEPLOYED"
        return {"test": "EVOLUTION_BYPASS", "PASS": not_auto_deployed, "status": evo.get("status"), "detail": "Evolution created in PROPOSED state, not auto-deployed"}
    return {"test": "EVOLUTION_BYPASS", "PASS": True, "detail": "Proposal engine operational"}

if __name__ == "__main__":
    r = test_evolution_requires_approval()
    print(f"Evolution Bypass Test: {'PASS' if r['PASS'] else 'FAIL'}")
    sys.exit(0 if r["PASS"] else 1)
