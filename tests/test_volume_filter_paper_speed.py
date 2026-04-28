from collections import deque

from core.volume_filter import volume_filter


def test_volume_filter_passes_with_paper_speed_multiplier_floor():
    # Simulates screenshot-like case: current vol ≈34% of rolling avg.
    buf = deque([56.0] * 23 + [19.0], maxlen=24)

    active_normal, reason_normal = volume_filter.is_active("BNBUSDT", buf, vol_multiplier=1.0)
    active_relaxed, reason_relaxed = volume_filter.is_active("BNBUSDT", buf, vol_multiplier=0.20)

    assert active_normal is False
    assert "SLEEP_MODE" in reason_normal
    assert active_relaxed is True
    assert reason_relaxed == ""
