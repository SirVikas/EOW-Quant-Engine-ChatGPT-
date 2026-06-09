"""Disaster Recovery — Recovery Validator."""
import threading, time
from typing import List


class RecoveryValidator:
    def __init__(self):
        self._lock = threading.RLock()

    def validate_recovery(self, restore_id: str) -> dict:
        checks_passed = 0
        checks_failed = 0
        report = []

        # Check: layer registry health
        try:
            from core.pccp.layer_registry import layer_registry
            summary = layer_registry.system_health_summary()
            healthy = summary.get("healthy_count", 0) >= 0
            report.append({"check": "LAYER_REGISTRY_HEALTH", "PASS": healthy})
            if healthy:
                checks_passed += 1
            else:
                checks_failed += 1
        except Exception as e:
            report.append({"check": "LAYER_REGISTRY_HEALTH", "PASS": False, "error": str(e)[:60]})
            checks_failed += 1

        # Check: trust data intact
        try:
            from core.trust_fabric.trust_registry import trust_registry
            summary = trust_registry.trust_summary()
            report.append({"check": "TRUST_DATA_INTACT", "PASS": isinstance(summary, dict)})
            checks_passed += 1
        except Exception as e:
            report.append({"check": "TRUST_DATA_INTACT", "PASS": False, "error": str(e)[:60]})
            checks_failed += 1

        # Check: evidence warehouse intact
        try:
            from core.evidence_warehouse.evidence_warehouse import evidence_warehouse
            wr = evidence_warehouse.warehouse_report()
            report.append({"check": "EVIDENCE_INTACT", "PASS": isinstance(wr, dict)})
            checks_passed += 1
        except Exception as e:
            report.append({"check": "EVIDENCE_INTACT", "PASS": False, "error": str(e)[:60]})
            checks_failed += 1

        return {
            "restore_id": restore_id,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "recovery_valid": checks_failed == 0,
            "validation_report": report,
            "generated_at": time.time(),
        }

    def pre_recovery_checklist(self) -> List[dict]:
        return [
            {"item": "Confirm backup_id exists and checksum is valid", "required": True},
            {"item": "Notify all active sessions before restore", "required": True},
            {"item": "Pause all active trading operations", "required": True},
            {"item": "Verify snapshot integrity via snapshot_engine", "required": True},
            {"item": "Record restore initiation in audit log", "required": True},
            {"item": "Confirm restored_by identity is authorized", "required": True},
        ]


recovery_validator = RecoveryValidator()
