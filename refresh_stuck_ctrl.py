"""Refresh a stuck Ctrl key state on Windows.

Usage:
- Double-click this file (or a shortcut) to run once.
- It force-releases both Ctrl keys and verifies release status.
- A popup confirms success, or shows the reason for failure.
"""

from __future__ import annotations

import ctypes
import time
from typing import Tuple

# Windows virtual-key codes
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
KEYEVENTF_KEYUP = 0x0002
MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_ICONERROR = 0x00000010


USER32 = ctypes.windll.user32


def _key_event(vk_code: int, key_up: bool = False) -> None:
    flags = KEYEVENTF_KEYUP if key_up else 0
    USER32.keybd_event(vk_code, 0, flags, 0)


def _is_key_down(vk_code: int) -> bool:
    # High-order bit indicates current key state.
    return bool(USER32.GetAsyncKeyState(vk_code) & 0x8000)


def _show_popup(title: str, message: str, is_error: bool = False) -> None:
    style = MB_OK | (MB_ICONERROR if is_error else MB_ICONINFORMATION)
    USER32.MessageBoxW(None, message, title, style)


def _release_once() -> None:
    _key_event(VK_LCONTROL, key_up=True)
    _key_event(VK_RCONTROL, key_up=True)


def refresh_ctrl_state(max_attempts: int = 20, delay_sec: float = 0.03) -> Tuple[bool, str]:
    """Force-reset Ctrl state and verify release.

    Returns:
        (success, reason)
    """
    if max_attempts < 1:
        return False, "Invalid configuration: max_attempts must be at least 1."

    for attempt in range(1, max_attempts + 1):
        _release_once()
        time.sleep(delay_sec)

        left_down = _is_key_down(VK_LCONTROL)
        right_down = _is_key_down(VK_RCONTROL)

        if not left_down and not right_down:
            return True, f"Ctrl keys released successfully (attempt {attempt}/{max_attempts})."

    left_down = _is_key_down(VK_LCONTROL)
    right_down = _is_key_down(VK_RCONTROL)

    stuck_parts = []
    if left_down:
        stuck_parts.append("Left Ctrl still appears pressed")
    if right_down:
        stuck_parts.append("Right Ctrl still appears pressed")

    reason = "; ".join(stuck_parts) if stuck_parts else "Unknown state verification failure"
    return (
        False,
        f"Failed to release Ctrl keys after {max_attempts} attempts. Reason: {reason}. "
        "Possible causes: physical key is held down, keyboard driver issue, or app-level input hook.",
    )


if __name__ == "__main__":
    success, message = refresh_ctrl_state()
    if success:
        _show_popup("Ctrl Key Refresh", f"Keys released. {message}", is_error=False)
    else:
        _show_popup("Ctrl Key Refresh - Failed", message, is_error=True)
