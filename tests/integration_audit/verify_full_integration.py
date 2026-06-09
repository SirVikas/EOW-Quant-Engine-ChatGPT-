"""Master integration verification — runs dependency mapper + gap detector."""
import sys, time
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")
from tests.integration_audit.integration_dependency_mapper import map_dependencies
from tests.integration_audit.integration_gap_detector import detect_gaps

def main():
    print("=" * 70)
    print("PHOENIX INSTITUTIONAL INTEGRATION AUDIT")
    print("=" * 70)

    print("\n[1] Dependency Map")
    dep = map_dependencies()
    for p in dep["pairs"]:
        status = "✓" if p["integration_viable"] else "✗"
        print(f"  {status} {p['layer_a']} ↔ {p['layer_b']}")
    print(f"\n  Viable: {dep['viable']}/{dep['total_pairs']}")

    print("\n[2] Integration Gap Detection")
    gaps = detect_gaps()
    for r in gaps["results"]:
        icon = "✓" if r["status"] == "PASS" else ("⚠" if r["status"] == "WARN" else "✗")
        print(f"  {icon} {r['check']}")
        if r["status"] == "FAIL":
            print(f"      Error: {r.get('error', '')}")
    print(f"\n  Integration Health: {gaps['integration_health_pct']}%")

    print("\n" + "=" * 70)
    overall = dep["viable"] == dep["total_pairs"] and gaps["failed"] == 0
    print(f"INTEGRATION AUDIT: {'PASS' if overall else 'PARTIAL — review warnings above'}")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
