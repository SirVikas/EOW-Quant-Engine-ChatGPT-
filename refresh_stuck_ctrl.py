"""Refresh a stuck Ctrl key state on Windows.

Usage:
- Double-click this file (or a shortcut) to run once.
- It force-releases both Ctrl keys and verifies release status.
- A popup confirms success, or shows the reason for failure.
"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from typing import Tuple

# Windows virtual-key codes
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_ICONERROR = 0x00000010

if sys.platform == "win32":
    USER32 = ctypes.WinDLL("user32", use_last_error=True)
else:
    USER32 = None


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR),
    ]


class INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUTUNION)]


def _show_popup(title: str, message: str, is_error: bool = False) -> None:
    if USER32 is None:
        print(f"{title}: {message}")
        return
    style = MB_OK | (MB_ICONERROR if is_error else MB_ICONINFORMATION)
    USER32.MessageBoxW(None, message, title, style)


def _key_event_fallback(vk_code: int, key_up: bool = False) -> None:
    flags = KEYEVENTF_KEYUP if key_up else 0
    USER32.keybd_event(vk_code, 0, flags, 0)


def _send_input_key(vk_code: int, key_up: bool) -> bool:
    flags = KEYEVENTF_KEYUP if key_up else 0
    inp = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(vk_code, 0, flags, 0, 0))
    sent = USER32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    return sent == 1


def _is_key_down(vk_code: int) -> bool:
    return bool(USER32.GetAsyncKeyState(vk_code) & 0x8000)


def _tap_ctrl() -> None:
    """Optional tap to resync apps that track Ctrl transitions."""
    _send_input_key(VK_LCONTROL, key_up=False)
    time.sleep(0.01)
    _send_input_key(VK_LCONTROL, key_up=True)


def _release_once() -> Tuple[bool, str]:
    methods = []

    # Preferred method: SendInput.
    l_ok = _send_input_key(VK_LCONTROL, key_up=True)
    r_ok = _send_input_key(VK_RCONTROL, key_up=True)
    methods.append(f"SendInput(L={l_ok}, R={r_ok})")

    # Fallback method for stubborn app hooks.
    _key_event_fallback(VK_LCONTROL, key_up=True)
    _key_event_fallback(VK_RCONTROL, key_up=True)
    methods.append("keybd_event fallback")

    # Optional tap to satisfy apps that need transition edges to clear stuck-state flags.
    _tap_ctrl()
    methods.append("Ctrl tap resync")

    return l_ok and r_ok, ", ".join(methods)


def refresh_ctrl_state(max_attempts: int = 30, delay_sec: float = 0.04) -> Tuple[bool, str]:
    """Force-reset Ctrl state and verify release.

    Returns:
        (success, reason)
    """
    if USER32 is None:
        return False, "This script only works on Windows."

    if max_attempts < 1:
        return False, "Invalid configuration: max_attempts must be at least 1."

    last_method = ""
    for attempt in range(1, max_attempts + 1):
        _, last_method = _release_once()
        time.sleep(delay_sec)

        if not _is_key_down(VK_LCONTROL) and not _is_key_down(VK_RCONTROL):
            return True, (
                f"Ctrl keys released successfully (attempt {attempt}/{max_attempts}). "
                f"Method: {last_method}."
            )

    left_down = _is_key_down(VK_LCONTROL)
    right_down = _is_key_down(VK_RCONTROL)

    stuck_parts = []
    if left_down:
        stuck_parts.append("Left Ctrl still appears pressed")
    if right_down:
        stuck_parts.append("Right Ctrl still appears pressed")

    reason = "; ".join(stuck_parts) if stuck_parts else "Unknown state verification failure"
    last_error = ctypes.get_last_error()
    error_info = f"WinError={last_error}" if last_error else "WinError=0"

    return (
        False,
        f"Failed to release Ctrl keys after {max_attempts} attempts. Reason: {reason}. "
        f"Last method: {last_method}. {error_info}. "
        "Possible causes: physical key is held down, keyboard driver issue, app-level input hook, "
        "or insufficient OS permissions.",
    )


if __name__ == "__main__":
    success, message = refresh_ctrl_state()
    if success:
        _show_popup("Ctrl Key Refresh", f"Keys released. {message}", is_error=False)
    else:
        _show_popup("Ctrl Key Refresh - Failed", message, is_error=True)
