"""
Market data auditor — master data assurance engine aggregating all sub-monitors.
"""
import threading


class MarketDataAuditor:
    def __init__(self) -> None:
        self._lock = threading.RLock()

    def audit_report(self) -> dict:
        from core.data_assurance.data_gap_detector import data_gap_detector
        from core.data_assurance.data_integrity_validator import data_integrity_validator
        from core.data_assurance.feed_health_monitor import feed_health_monitor

        gap_summary = data_gap_detector.gap_summary()
        health_report = feed_health_monitor.feed_health_report()
        feeds_healthy_pct = health_report["health_pct"]

        # Aggregate integrity across all feeds
        all_checks = data_integrity_validator._checks
        total = len(all_checks)
        passed = sum(1 for c in all_checks if c.result == "PASS")
        integrity_pct = round(passed / total * 100, 2) if total else 100.0

        # Determine trust level
        if gap_summary["active_gaps"] == 0 and feeds_healthy_pct >= 95 and integrity_pct >= 95:
            trust_level = "HIGH"
        elif gap_summary["active_gaps"] <= 2 and feeds_healthy_pct >= 80 and integrity_pct >= 80:
            trust_level = "MEDIUM"
        elif feeds_healthy_pct >= 50:
            trust_level = "LOW"
        else:
            trust_level = "UNTRUSTED"

        return {
            "total_gaps_detected": gap_summary["total_gaps"],
            "active_gaps": gap_summary["active_gaps"],
            "feeds_healthy_pct": feeds_healthy_pct,
            "integrity_score_pct": integrity_pct,
            "data_trust_level": trust_level,
            "gap_severity_breakdown": gap_summary["by_severity"],
        }

    def one_liner(self) -> str:
        r = self.audit_report()
        return (
            f"Data Assurance | Trust={r['data_trust_level']} | "
            f"ActiveGaps={r['active_gaps']} | FeedsHealthy={r['feeds_healthy_pct']}% | "
            f"Integrity={r['integrity_score_pct']}%"
        )


market_data_auditor = MarketDataAuditor()
