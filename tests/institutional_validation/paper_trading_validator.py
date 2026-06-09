"""
Paper trading validation — evidence accumulator for live trading readiness.
Returns PENDING until sufficient live trade data is collected.
"""
from datetime import datetime


def validate(window_days: int = 30) -> dict:
    return {
        "window_days": window_days,
        "trades_required": window_days * 2,
        "validation_status": "PENDING",
        "evidence_level": "NONE",
        "notes": (
            "No live trading data available yet. "
            f"Requires {window_days * 2} trades over {window_days} days to assess."
        ),
        "validated_at": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    print(validate(30))
