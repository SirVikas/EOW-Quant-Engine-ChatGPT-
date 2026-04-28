"""Refresh a stuck Ctrl key state on Windows.

Double-click this script to force-release Ctrl and show a popup result.
"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from typing import Tuple

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


def _popup(title: str, message: str, is_error: bool = False) -> None:
    if USER32 is None:
        print(f"{title}: {message}")
        return
    style = MB_OK | (MB_ICONERROR if is_error else MB_ICONINFORMATION)
    USER32.MessageBoxW(None, message, title, style)


def _send_input_key(vk_code: int, key_up: bool) -> bool:
    flags = KEYEVENTF_KEYUP if key_up else 0
    inp = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(vk_code, 0, flags, 0, 0))
    return USER32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) == 1


def _fallback_keyup(vk_code: int) -> None:
    USER32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def _is_down(vk_code: int) -> bool:
    return bool(USER32.GetAsyncKeyState(vk_code) & 0x8000)


def refresh_ctrl_state(max_attempts: int = 30, delay_sec: float = 0.04) -> Tuple[bool, str]:
    if USER32 is None:
        return False, "This utility only works on Windows."

    for attempt in range(1, max_attempts + 1):
        _send_input_key(VK_LCONTROL, key_up=True)
        _send_input_key(VK_RCONTROL, key_up=True)
        _fallback_keyup(VK_LCONTROL)
        _fallback_keyup(VK_RCONTROL)

        # Resync edge for apps that track transitions.
        _send_input_key(VK_LCONTROL, key_up=False)
        time.sleep(0.01)
        _send_input_key(VK_LCONTROL, key_up=True)
        time.sleep(delay_sec)

        if not _is_down(VK_LCONTROL) and not _is_down(VK_RCONTROL):
            return True, f"Keys released successfully (attempt {attempt}/{max_attempts})."

    stuck = []
    if _is_down(VK_LCONTROL):
        stuck.append("Left Ctrl still pressed")
    if _is_down(VK_RCONTROL):
        stuck.append("Right Ctrl still pressed")
    reason = "; ".join(stuck) if stuck else "Unknown verification failure"
    return False, (
        f"Failed to release Ctrl after {max_attempts} attempts. Reason: {reason}. "
        f"WinError={ctypes.get_last_error() or 0}."
    )


if __name__ == "__main__":
    ok, msg = refresh_ctrl_state()
    if ok:
        _popup("Ctrl Key Refresh", msg, is_error=False)
    else:
        _popup("Ctrl Key Refresh - Failed", msg, is_error=True)
