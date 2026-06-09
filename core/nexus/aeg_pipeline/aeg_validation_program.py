"""
PHOENIX AEG — Validation Program  [AEG-01 … AEG-05]

Proves AEG recommendations deserve promotion and full autonomy.

AEG-01: Shadow Mode Evidence     — 30/60/90/180d shadow validation reports
AEG-02: Promotion Accuracy       — rate at which promoted rec_types remain accurate
AEG-03: Rollback Accuracy        — rate at which rollbacks were justified
AEG-04: Sandbox Drift Detection  — divergence between sandbox and live accuracy
AEG-05: Autonomy Readiness Score — single index (0–100) measuring AEG maturity
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


READINESS_WEIGHTS = {
    "sandbox_accuracy":       0.25,
    "shadow_graduation_rate": 0.20,
    "promotion_success_rate": 0.20,
    "rollback_justification": 0.15,
    "damage_score":           0.10,   # inverted: lower damage → higher score
    "live_rec_count":         0.10,
}


class AEGValidationProgram:
    """
    Aggregates AEG performance metrics into validation reports and a readiness index.
    """

    # ── AEG-01: Shadow Mode Evidence ─────────────────────────────────────────

    def shadow_validation_report(self) -> dict:
        try:
            from core.nexus.aeg_pipeline.aeg_shadow_mode import aeg_shadow_mode as _asm
            summary = _asm.summary()
        except Exception:
            summary = {}

        sessions = summary.get("sessions", [])
        windows = {30: [], 60: [], 90: [], 180: []}
        now = time.time()
        for s in sessions:
            age_days = (now - s.get("started_at", now)) / 86400
            for w in [30, 60, 90, 180]:
                if age_days <= w:
                    windows[w].append(s)

        window_reports = {}
        for days, sess_list in windows.items():
            if not sess_list:
                window_reports[f"{days}d"] = {"sessions": 0, "note": "No data yet"}
                continue
            graduated = sum(1 for s in sess_list if s.get("status") == "GRADUATED")
            failed    = sum(1 for s in sess_list if s.get("status") == "FAILED")
            avg_acc   = sum(s.get("accuracy", 0) for s in sess_list) / len(sess_list)
            window_reports[f"{days}d"] = {
                "sessions":       len(sess_list),
                "graduated":      graduated,
                "failed":         failed,
                "graduation_rate": round(graduated / max(1, len(sess_list)), 3),
                "avg_accuracy":   round(avg_acc, 3),
            }

        return {
            "total_sessions":    summary.get("total_sessions", 0),
            "graduated":         summary.get("graduated_sessions", 0),
            "window_reports":    window_reports,
            "generated_at":      time.time(),
        }

    # ── AEG-02: Promotion Accuracy ────────────────────────────────────────────

    def promotion_accuracy_report(self) -> dict:
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine as _ape
            summary = _ape.summary()
            live_recs = summary.get("live_recommendations", 0)
            promotions = summary.get("total_promoted", live_recs)
        except Exception:
            promotions = 0
            live_recs = 0

        try:
            from core.nexus.aeg_pipeline.aeg_rollback_framework import aeg_rollback_framework as _arf
            rollback_count = len(_arf.suspended_rec_types())
        except Exception:
            rollback_count = 0

        # Promotion success = promoted and still live (not rolled back)
        success = max(0, promotions - rollback_count)
        success_rate = success / max(1, promotions)

        return {
            "total_promotions":   promotions,
            "still_live":         live_recs,
            "rolled_back":        rollback_count,
            "success_rate":       round(success_rate, 3),
            "verdict":            "STRONG" if success_rate >= 0.85 else ("ACCEPTABLE" if success_rate >= 0.70 else "WEAK"),
            "generated_at":       time.time(),
        }

    # ── AEG-03: Rollback Accuracy ─────────────────────────────────────────────

    def rollback_accuracy_report(self) -> dict:
        try:
            from core.nexus.aeg_pipeline.aeg_rollback_framework import aeg_rollback_framework as _arf
            suspended = _arf.suspended_rec_types()
        except Exception:
            suspended = []

        try:
            from core.nexus.aeg_pipeline.aeg_damage_accounting import aeg_damage_accounting as _ada
            portfolio = _ada.portfolio_summary()
        except Exception:
            portfolio = {}

        # A rollback is "justified" if the rec_type had negative economic verdict
        justified = 0
        for s in suspended:
            rt = s.get("rec_type", "")
            try:
                from core.nexus.aeg_pipeline.aeg_damage_accounting import aeg_damage_accounting as _ada
                account = _ada.account_for(rt, days=90)
                if account.get("economic_verdict") in ("NEGATIVE", "NEUTRAL"):
                    justified += 1
            except Exception:
                pass

        total = len(suspended)
        justification_rate = justified / max(1, total) if total > 0 else None

        return {
            "total_rollbacks":     total,
            "justified":           justified,
            "justification_rate":  round(justification_rate, 3) if justification_rate is not None else None,
            "verdict":             (
                "WELL_CALIBRATED" if (justification_rate or 0) >= 0.80
                else "NEEDS_REVIEW" if total > 0
                else "NO_ROLLBACKS_YET"
            ),
            "suspended_rec_types": [s.get("rec_type") for s in suspended],
            "generated_at":        time.time(),
        }

    # ── AEG-04: Sandbox Drift Detection ──────────────────────────────────────

    def sandbox_drift_report(self) -> dict:
        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            all_stats = _ass.all_stats()
        except Exception:
            all_stats = []

        drift_items = []
        for s in all_stats:
            rt = s.get("rec_type", "")
            sandbox_acc = s.get("accuracy") or 0
            try:
                from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
                live_stats = _ass.live_stats_for(rt) if hasattr(_ass, "live_stats_for") else {}
            except Exception:
                live_stats = {}
            live_acc = live_stats.get("accuracy") if live_stats else None

            if live_acc is not None:
                drift = sandbox_acc - live_acc
                drift_items.append({
                    "rec_type":     rt,
                    "sandbox_acc":  round(sandbox_acc, 3),
                    "live_acc":     round(live_acc, 3),
                    "drift":        round(drift, 3),
                    "drift_label":  "HIGH_DRIFT" if abs(drift) > 0.15 else ("MODERATE" if abs(drift) > 0.05 else "STABLE"),
                })

        high_drift = sum(1 for d in drift_items if d["drift_label"] == "HIGH_DRIFT")
        return {
            "total_tracked":  len(drift_items),
            "high_drift":     high_drift,
            "stable":         sum(1 for d in drift_items if d["drift_label"] == "STABLE"),
            "items":          sorted(drift_items, key=lambda x: abs(x["drift"]), reverse=True),
            "alert":          high_drift > 0,
            "generated_at":   time.time(),
        }

    # ── AEG-05: Autonomy Readiness Score ─────────────────────────────────────

    def autonomy_readiness_index(self) -> dict:
        components: Dict[str, float] = {}

        # Sandbox accuracy (average across live rec types)
        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            all_stats = _ass.all_stats()
            accs = [(s.get("accuracy") or 0) for s in all_stats if s.get("samples_with_outcome", 0) >= 10]
            components["sandbox_accuracy"] = sum(accs) / max(1, len(accs))
        except Exception:
            components["sandbox_accuracy"] = 0.0

        # Shadow graduation rate
        try:
            from core.nexus.aeg_pipeline.aeg_shadow_mode import aeg_shadow_mode as _asm
            summ = _asm.summary()
            total_s = summ.get("total_sessions", 0)
            grad_s  = summ.get("graduated_sessions", 0)
            components["shadow_graduation_rate"] = grad_s / max(1, total_s) if total_s > 0 else 0.0
        except Exception:
            components["shadow_graduation_rate"] = 0.0

        # Promotion success rate
        promo_report = self.promotion_accuracy_report()
        components["promotion_success_rate"] = promo_report.get("success_rate", 0.0)

        # Rollback justification rate (higher = better: rollbacks were warranted)
        rb_report = self.rollback_accuracy_report()
        components["rollback_justification"] = rb_report.get("justification_rate") or 0.5

        # Damage score (inverted: negative damage → score 1.0, heavy damage → 0.0)
        try:
            from core.nexus.aeg_pipeline.aeg_damage_accounting import aeg_damage_accounting as _ada
            port = _ada.portfolio_summary()
            net_pnl = port.get("total_net_pnl", 0)
            components["damage_score"] = min(1.0, max(0.0, (net_pnl + 10000) / 20000))
        except Exception:
            components["damage_score"] = 0.5

        # Live recommendation count normalized (0 = 0, 10+ = 1.0)
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine as _ape
            live = _ape.summary().get("live_recommendations", 0)
            components["live_rec_count"] = min(1.0, live / 10.0)
        except Exception:
            components["live_rec_count"] = 0.0

        # Weighted score
        score = sum(
            components.get(k, 0) * w
            for k, w in READINESS_WEIGHTS.items()
        ) * 100

        score = round(score, 1)
        if score >= 80:
            readiness_label = "AUTONOMY_READY"
        elif score >= 60:
            readiness_label = "ADVANCED"
        elif score >= 40:
            readiness_label = "DEVELOPING"
        else:
            readiness_label = "EARLY_STAGE"

        return {
            "readiness_score":  score,
            "readiness_label":  readiness_label,
            "components":       {k: round(v, 4) for k, v in components.items()},
            "weights":          READINESS_WEIGHTS,
            "interpretation":   f"AEG readiness at {score:.1f}/100 — {readiness_label}",
            "generated_at":     time.time(),
        }

    def full_validation_report(self) -> dict:
        return {
            "shadow_validation":  self.shadow_validation_report(),
            "promotion_accuracy": self.promotion_accuracy_report(),
            "rollback_accuracy":  self.rollback_accuracy_report(),
            "sandbox_drift":      self.sandbox_drift_report(),
            "autonomy_readiness": self.autonomy_readiness_index(),
            "generated_at":       time.time(),
        }


# Singleton
aeg_validation_program = AEGValidationProgram()
