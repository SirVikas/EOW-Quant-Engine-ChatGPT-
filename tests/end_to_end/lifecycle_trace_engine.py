"""Traces the full PHOENIX institutional lifecycle: Finding → ... → Future Decision."""
import time, importlib

LIFECYCLE_STAGES = [
    "FINDING_REGISTRY",
    "ROOT_CAUSE_ENGINE",
    "CTAO_RECOMMENDATION",
    "DIGITAL_TWIN_VALIDATION",
    "HUMAN_APPROVAL",
    "PRODUCTION_RECORD",
    "MARKET_VALIDATION",
    "EVIDENCE_WAREHOUSE",
    "TRUST_UPDATE",
    "STRATEGIC_MEMORY",
    "FUTURE_DECISION_SUPPORT",
]

def trace_lifecycle(subject_id="TEST-LIFECYCLE-001"):
    trace = []
    ts = time.time()

    # Stage 1: Finding
    try:
        from core.ctao.finding_registry import finding_registry
        fid = finding_registry.record_finding("LIFECYCLE_TEST", "MEDIUM", 0.8, "LIFECYCLE_TRACER", f"Lifecycle trace for {subject_id}")
        trace.append({"stage": "FINDING_REGISTRY", "status": "OK", "id": fid})
    except Exception as e:
        trace.append({"stage": "FINDING_REGISTRY", "status": "FAIL", "error": str(e)[:80]})

    # Stage 2: Root Cause
    fid_val = trace[0].get("id", subject_id) if trace[0]["status"] == "OK" else subject_id
    try:
        from core.ctao.root_cause_engine import root_cause_engine
        rc = root_cause_engine.analyze(fid_val, "lifecycle test signal instability")
        trace.append({"stage": "ROOT_CAUSE_ENGINE", "status": "OK", "cause": rc.get("root_cause", "")[:50]})
    except Exception as e:
        trace.append({"stage": "ROOT_CAUSE_ENGINE", "status": "FAIL", "error": str(e)[:80]})

    # Stage 3: Recommendation
    try:
        from core.ctao.recommendation_engine import ctao_recommendation_engine
        rec_id = ctao_recommendation_engine.generate(fid_val, "lifecycle test recommendation", severity="MEDIUM")
        rec_id = rec_id if isinstance(rec_id, str) else rec_id.get("rec_id", "REC-TEST")
        trace.append({"stage": "CTAO_RECOMMENDATION", "status": "OK", "rec_id": rec_id})
    except Exception as e:
        trace.append({"stage": "CTAO_RECOMMENDATION", "status": "FAIL", "error": str(e)[:80]})

    # Stage 4: Digital Twin
    rec_id_val = "REC-LIFECYCLE"
    try:
        from core.digital_twin.digital_twin_engine import digital_twin_engine
        result = digital_twin_engine.pre_deployment_check(rec_id_val, "lifecycle test check")
        trace.append({"stage": "DIGITAL_TWIN_VALIDATION", "status": "OK", "verdict": str(result.get("verdict", ""))[:30]})
    except Exception as e:
        trace.append({"stage": "DIGITAL_TWIN_VALIDATION", "status": "FAIL", "error": str(e)[:80]})

    # Stage 5: Human Approval
    try:
        from core.human_governance.approval_registry import approval_registry
        ap_id = approval_registry.request_approval(rec_id_val, "RECOMMENDATION", "deploy lifecycle test rec", "LIFECYCLE_TRACER")
        trace.append({"stage": "HUMAN_APPROVAL", "status": "OK", "approval_id": ap_id})
    except Exception as e:
        trace.append({"stage": "HUMAN_APPROVAL", "status": "FAIL", "error": str(e)[:80]})

    # Stage 6: Market Validation
    try:
        from core.real_market_validation.validation_engine import real_market_validation_engine
        val = real_market_validation_engine.validate(rec_id_val, "RECOMMENDATION", {"profit_pct": 2.0}, {"profit_pct": 1.8})
        trace.append({"stage": "MARKET_VALIDATION", "status": "OK", "verdict": str(val.get("verdict", ""))[:30]})
    except Exception as e:
        trace.append({"stage": "MARKET_VALIDATION", "status": "FAIL", "error": str(e)[:80]})

    # Stage 7: Evidence Warehouse
    try:
        from core.evidence_warehouse.evidence_warehouse import evidence_warehouse
        eid = evidence_warehouse.deposit("RECOMMENDATION", rec_id_val, "LIFECYCLE_TRACER", {"lifecycle": "test"}, quality=0.8)
        trace.append({"stage": "EVIDENCE_WAREHOUSE", "status": "OK", "evidence_id": eid})
    except Exception as e:
        trace.append({"stage": "EVIDENCE_WAREHOUSE", "status": "FAIL", "error": str(e)[:80]})

    # Stage 8: Trust Update
    try:
        from core.trust_fabric.trust_fabric_engine import trust_fabric_engine
        trust_fabric_engine.update_trust(rec_id_val, "RECOMMENDATION", 0.75, 3)
        trace.append({"stage": "TRUST_UPDATE", "status": "OK"})
    except Exception as e:
        trace.append({"stage": "TRUST_UPDATE", "status": "FAIL", "error": str(e)[:80]})

    # Stage 9: Strategic Memory
    try:
        from core.strategic_memory.lesson_registry import lesson_registry
        lesson_registry.record_lesson("Lifecycle Test Lesson", "System completed full lifecycle trace", evidence_count=1, confidence=0.6, source_type="PATTERN")
        trace.append({"stage": "STRATEGIC_MEMORY", "status": "OK"})
    except Exception as e:
        trace.append({"stage": "STRATEGIC_MEMORY", "status": "FAIL", "error": str(e)[:80]})

    # Stage 10: Future Decision Support
    try:
        from core.pcao.pcao_engine import pcao_engine
        briefing = pcao_engine.executive_briefing()
        trace.append({"stage": "FUTURE_DECISION_SUPPORT", "status": "OK", "verdict": str(briefing.get("verdict", ""))[:30]})
    except Exception as e:
        trace.append({"stage": "FUTURE_DECISION_SUPPORT", "status": "FAIL", "error": str(e)[:80]})

    passed = sum(1 for t in trace if t["status"] == "OK")
    return {
        "subject_id": subject_id,
        "stages_total": len(trace),
        "stages_passed": passed,
        "stages_failed": len(trace) - passed,
        "lifecycle_completeness_pct": round(passed / len(trace) * 100, 1),
        "trace": trace,
        "duration_seconds": round(time.time() - ts, 2),
        "generated_at": ts,
    }
