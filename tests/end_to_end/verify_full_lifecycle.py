"""End-to-end lifecycle verification runner."""
import sys
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")
from tests.end_to_end.lifecycle_trace_engine import trace_lifecycle

def main():
    print("=" * 70)
    print("PHOENIX END-TO-END LIFECYCLE VERIFICATION")
    print("=" * 70)
    result = trace_lifecycle()
    for stage in result["trace"]:
        icon = "✓" if stage["status"] == "OK" else "✗"
        print(f"  {icon} {stage['stage']}")
        if stage["status"] == "FAIL":
            print(f"      {stage.get('error', '')}")
    print(f"\n  Completeness: {result['lifecycle_completeness_pct']}%")
    print(f"  Duration: {result['duration_seconds']}s")
    passed = result["stages_failed"] == 0
    print(f"\nLIFECYCLE VERIFICATION: {'PASS' if passed else 'PARTIAL'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
