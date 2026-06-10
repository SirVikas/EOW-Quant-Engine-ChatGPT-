"""Verifier: POST-v1.83.0 Remaining Developer Gaps (v1.84.0, GAP-01..GAP-05)"""
import sys, importlib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

MODULES = [
    "core.evidence_orchestration.evidence_orchestrator",
    "core.evidence_orchestration.evidence_scheduler",
    "core.evidence_orchestration.evidence_campaign_manager",
    "core.evidence_orchestration.evidence_retention_controller",
    "core.certification_pipeline.certification_engine",
    "core.certification_pipeline.readiness_gate_manager",
    "core.certification_pipeline.certification_scheduler",
    "core.certification_pipeline.certification_archive",
    "core.anomaly_response.response_engine",
    "core.anomaly_response.escalation_manager",
    "core.anomaly_response.containment_manager",
    "core.anomaly_response.recovery_recommender",
    "core.proof_maturity.proof_maturity_engine",
    "core.proof_maturity.evidence_scoring_engine",
    "core.proof_maturity.confidence_weighting",
    "core.proof_maturity.maturity_dashboard",
    "core.self_healing_playbooks.playbook_registry",
    "core.self_healing_playbooks.playbook_executor",
    "core.self_healing_playbooks.recovery_playbook_manager",
    "core.self_healing_playbooks.verification_engine",
]

passed = 0
for mod in MODULES:
    try:
        importlib.import_module(mod)
        print(f"  OK  {mod}")
        passed += 1
    except Exception as e:
        print(f"  FAIL {mod}: {e}")

failures = len(MODULES) - passed

# ── functional smoke checks ──────────────────────────────────────────────────

def check(label, fn):
    global passed, failures
    try:
        result = fn()
        assert result, f"empty result: {result!r}"
        print(f"  OK  {label}")
        passed += 1
    except Exception as e:
        print(f"  FAIL {label}: {e}")
        failures += 1


def _eo():
    from core.evidence_orchestration.evidence_orchestrator import evidence_orchestrator
    run = evidence_orchestrator.run_due(force=True)
    assert len(run["runs"]) == 4, f"expected 4 forced runs, got {len(run['runs'])}"
    report = evidence_orchestrator.orchestration_report()
    assert report["total_runs"] >= 4
    return evidence_orchestrator.one_liner()


def _cp():
    from core.certification_pipeline.certification_engine import certification_engine
    record = certification_engine.run_certification("DAILY")
    assert record["verdict"] in ("CERTIFIED", "PROVISIONAL", "NOT_CERTIFIED")
    assert "composite_score" in certification_engine.daily_readiness_score()
    return certification_engine.one_liner()


def _ar():
    from core.anomaly_response.response_engine import response_engine
    response = response_engine.handle_anomaly("WS_STALE", "HIGH", "verifier", "smoke test")
    assert response["escalation"]["level"] == "ESCALATE"
    assert response["recommendation"]["playbook_id"], "WS_STALE should map to a playbook"
    resolved = response_engine.resolve(response["response_id"], "smoke resolved")
    assert resolved["status"] == "RESOLVED"
    return response_engine.one_liner()


def _pmx():
    from core.proof_maturity.proof_maturity_engine import proof_maturity_engine
    from core.proof_maturity.maturity_dashboard import maturity_dashboard
    report = proof_maturity_engine.proof_maturity_report()
    assert 0.0 <= report["proof_maturity_index"] <= 100.0
    assert report["proof_level"]
    assert maturity_dashboard.dashboard()["snapshots"] >= 1
    return proof_maturity_engine.one_liner()


def _shp():
    from core.self_healing_playbooks.recovery_playbook_manager import recovery_playbook_manager
    recovery = recovery_playbook_manager.handle_failure("DATA_GAP", "smoke test")
    assert recovery["execution"]["status"] == "EXECUTED"
    assert recovery["verification"]["verdict"] == "VERIFIED"
    return recovery_playbook_manager.one_liner()


check("GAP-01 evidence orchestration run_due(force)", _eo)
check("GAP-02 certification run + readiness score", _cp)
check("GAP-03 anomaly handle → escalate → resolve", _ar)
check("GAP-04 proof maturity index + dashboard", _pmx)
check("GAP-05 failure → playbook → verification", _shp)

total = len(MODULES) + 5
print(f"\n{passed}/{total} checks verified")
sys.exit(0 if failures == 0 else 1)
