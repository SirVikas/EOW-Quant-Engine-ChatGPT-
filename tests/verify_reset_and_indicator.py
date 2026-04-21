"""
tests/verify_reset_and_indicator.py — qFTD-007-v2 integration smoke-test.

Verifies:
  1. BOOT_MODE config field exists and defaults to "FRESH"
  2. STARTUP_GRACE_SECONDS config field exists and defaults to 60.0
  3. indicator_validator.validate_symbol_buffers() actually updates is_ready()
  4. indicator_validator.is_ready() returns False before any call
  5. indicator_validator.is_ready() returns True after a fully-warm buffer call
  6. Passing NaN indicator_values correctly fails validation

Run with:
    python -m pytest tests/verify_reset_and_indicator.py -v
or standalone:
    python tests/verify_reset_and_indicator.py
"""
from __future__ import annotations

import math
import sys
import os

# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_boot_mode_default():
    from config import cfg
    assert cfg.BOOT_MODE == "FRESH", (
        f"Expected BOOT_MODE='FRESH', got {cfg.BOOT_MODE!r}. "
        "Default must be FRESH so engine always starts clean unless explicitly told to RESUME."
    )


def test_startup_grace_seconds_exists():
    from config import cfg
    assert hasattr(cfg, "STARTUP_GRACE_SECONDS"), (
        "STARTUP_GRACE_SECONDS not found in config — qFTD-007-v2 boot grace period missing."
    )
    assert cfg.STARTUP_GRACE_SECONDS == 60.0, (
        f"Expected STARTUP_GRACE_SECONDS=60.0, got {cfg.STARTUP_GRACE_SECONDS}"
    )


def test_indicator_validator_initially_not_ready():
    from core.indicator_validator import IndicatorValidator
    iv = IndicatorValidator()
    assert not iv.is_ready(), (
        "Fresh IndicatorValidator should return is_ready()=False before any call."
    )


def test_indicator_validator_ready_after_warm_buffers():
    from config import cfg
    from core.indicator_validator import IndicatorValidator
    iv = IndicatorValidator()

    n = max(cfg.IV_MIN_CANDLES, cfg.IV_ADX_MIN_CANDLES, cfg.IV_VOLUME_MIN_CANDLES) + 5
    closes = [100.0 + i * 0.1 for i in range(n)]
    volumes = [1_000_000.0] * n

    result = iv.validate_symbol_buffers(
        candle_close_buf=closes,
        candle_volume_buf=volumes,
        indicator_values={"adx": 22.5, "atr": 0.005},
    )
    assert result.ok, (
        f"Expected ok=True with {n} candles, got failed={result.failed}. "
        "indicator_validator must pass when buffers are sufficiently warm."
    )
    assert iv.is_ready(), (
        "is_ready() must return True after a successful validate_symbol_buffers() call."
    )


def test_indicator_validator_nan_fails():
    from core.indicator_validator import IndicatorValidator
    iv = IndicatorValidator()

    closes = [100.0] * 30
    volumes = [1_000_000.0] * 30

    result = iv.validate_symbol_buffers(
        candle_close_buf=closes,
        candle_volume_buf=volumes,
        indicator_values={"adx": float("nan"), "atr": 0.005},
    )
    assert not result.ok, (
        "NaN in indicator_values must cause ok=False — NaN propagation would silently corrupt signals."
    )
    assert any("adx=NaN" in f for f in result.failed), (
        f"Expected 'adx=NaN' in failed list, got {result.failed}"
    )


def test_binance_testnet_default_false():
    from config import cfg
    assert cfg.BINANCE_TESTNET is False, (
        f"BINANCE_TESTNET must default to False. Got {cfg.BINANCE_TESTNET!r}. "
        "PAPER mode uses real Binance endpoints — testnet routing was qFTD-007 bug."
    )


if __name__ == "__main__":
    tests = [
        test_boot_mode_default,
        test_startup_grace_seconds_exists,
        test_indicator_validator_initially_not_ready,
        test_indicator_validator_ready_after_warm_buffers,
        test_indicator_validator_nan_fails,
        test_binance_testnet_default_false,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print()
    if failed:
        print(f"{failed}/{len(tests)} tests FAILED")
        sys.exit(1)
    else:
        print(f"All {len(tests)} tests passed.")
