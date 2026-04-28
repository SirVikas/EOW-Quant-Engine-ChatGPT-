"""Refresh a stuck Ctrl key state on Windows.

Usage:
- Double-click this file (or a shortcut) to run once.
- It forces both Ctrl keys to KEYUP and then performs a quick Ctrl tap.
"""

from __future__ import annotations

import ctypes
import time

# Windows virtual-key codes
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
KEYEVENTF_KEYUP = 0x0002


def _key_event(vk_code: int, key_up: bool = False) -> None:
    flags = KEYEVENTF_KEYUP if key_up else 0
    ctypes.windll.user32.keybd_event(vk_code, 0, flags, 0)


def refresh_ctrl_state() -> None:
    """Force-reset Ctrl state so apps stop thinking Ctrl is held."""
    # 1) Release both Ctrl keys in case either is stuck logically.
    _key_event(VK_LCONTROL, key_up=True)
    _key_event(VK_RCONTROL, key_up=True)
    time.sleep(0.03)

    # 2) Quick tap helps some apps re-sync internal keyboard state.
    _key_event(VK_LCONTROL, key_up=False)
    time.sleep(0.02)
    _key_event(VK_LCONTROL, key_up=True)


if __name__ == "__main__":
    refresh_ctrl_state()
    print("Ctrl key state refreshed.")
