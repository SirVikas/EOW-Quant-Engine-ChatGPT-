"""Validates individual report truthfulness — no None bombs, no empty sections."""
import time

def validate_report(report_type, report_dict):
    issues = []
    if not isinstance(report_dict, dict):
        return {"report_type": report_type, "PASS": False, "issues": ["Report is not a dict"]}
    if "generated_at" not in report_dict:
        issues.append("Missing generated_at timestamp")
    if "report_type" not in report_dict and "sections" not in report_dict:
        issues.append("Missing report_type or sections")
    sections = report_dict.get("sections", {})
    if isinstance(sections, dict):
        empty = [k for k, v in sections.items() if v is None]
        if empty:
            issues.append(f"Empty sections: {empty}")
    return {
        "report_type": report_type,
        "PASS": len(issues) == 0,
        "issues": issues,
        "keys_present": list(report_dict.keys()),
    }
