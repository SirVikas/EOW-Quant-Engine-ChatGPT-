"""Verifies trust fabric cannot self-promote without evidence."""
import sys
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")

def test_trust_requires_evidence():
    from core.trust_fabric.trust_registry import trust_registry
    trust_registry.set_trust("BYPASS_TEST_SUBJ", "RECOMMENDATION", 1.0, 0)  # max trust, 0 evidence
    entry = trust_registry.get_trust("BYPASS_TEST_SUBJ")
    status = entry.get("status") if entry else "NOT_FOUND"
    # Should be UNVERIFIED or PROVISIONAL, not TRUSTED (requires evidence>=10)
    not_auto_trusted = status not in ("TRUSTED",)
    return {
        "test": "TRUST_BYPASS",
        "PASS": not_auto_trusted,
        "trust_score": entry.get("trust_score") if entry else None,
        "status": status,
        "detail": "Trust with 0 evidence is not TRUSTED status",
    }

if __name__ == "__main__":
    r = test_trust_requires_evidence()
    print(f"Trust Bypass Test: {'PASS' if r['PASS'] else 'FAIL'} (status={r['status']})")
    sys.exit(0 if r["PASS"] else 1)
