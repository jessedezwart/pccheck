"""
Display checks:
  - Monitor refresh rate set to maximum Hz
  - HDR enabled unexpectedly (adds processing overhead)
  - Variable Refresh Rate / G-Sync / FreeSync status
  - Multiple monitors active while gaming

To remove a check, delete or comment out its entry in get_checks().
"""

from __future__ import annotations

import ctypes
import json
import re

from checks.base import (
    CheckResult,
    Status,
    reg_hkcu,
    reg_hklm,
    run_cmd,
    run_powershell,
    wmi_query,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_display_adapters() -> list[dict]:
    rows = wmi_query(
        "Win32_VideoController",
        props=[
            "Name",
            "CurrentRefreshRate",
            "MaxRefreshRate",
            "CurrentHorizontalResolution",
            "CurrentVerticalResolution",
            "Status",
        ],
    )
    return [r for r in rows if r.get("CurrentRefreshRate")]


ENUM_CURRENT_SETTINGS = -1


class _DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", ctypes.c_ushort),
        ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort),
        ("dmDriverExtra", ctypes.c_ushort),
        ("dmFields", ctypes.c_ulong),
        ("dmOrientation", ctypes.c_short),
        ("dmPaperSize", ctypes.c_short),
        ("dmPaperLength", ctypes.c_short),
        ("dmPaperWidth", ctypes.c_short),
        ("dmScale", ctypes.c_short),
        ("dmCopies", ctypes.c_short),
        ("dmDefaultSource", ctypes.c_short),
        ("dmPrintQuality", ctypes.c_short),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", ctypes.c_ushort),
        ("dmBitsPerPel", ctypes.c_ulong),
        ("dmPelsWidth", ctypes.c_ulong),
        ("dmPelsHeight", ctypes.c_ulong),
        ("dmDisplayFlags", ctypes.c_ulong),
        ("dmDisplayFrequency", ctypes.c_ulong),
        ("dmICMMethod", ctypes.c_ulong),
        ("dmICMIntent", ctypes.c_ulong),
        ("dmMediaType", ctypes.c_ulong),
        ("dmDitherType", ctypes.c_ulong),
        ("dmReserved1", ctypes.c_ulong),
        ("dmReserved2", ctypes.c_ulong),
        ("dmPanningWidth", ctypes.c_ulong),
        ("dmPanningHeight", ctypes.c_ulong),
    ]


def _get_primary_display_refresh() -> tuple[int, int] | None:
    user32 = ctypes.windll.user32
    current_mode = _DEVMODEW()
    current_mode.dmSize = ctypes.sizeof(_DEVMODEW)

    if not user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(current_mode)):
        return None

    current_hz = int(current_mode.dmDisplayFrequency or 0)
    width = int(current_mode.dmPelsWidth or 0)
    height = int(current_mode.dmPelsHeight or 0)

    if current_hz <= 0 or width <= 0 or height <= 0:
        return None

    max_hz = current_hz
    mode_index = 0
    while True:
        mode = _DEVMODEW()
        mode.dmSize = ctypes.sizeof(_DEVMODEW)
        if not user32.EnumDisplaySettingsW(None, mode_index, ctypes.byref(mode)):
            break
        if int(mode.dmPelsWidth) == width and int(mode.dmPelsHeight) == height:
            hz = int(mode.dmDisplayFrequency or 0)
            if hz > max_hz:
                max_hz = hz
        mode_index += 1

    return current_hz, max_hz


__all__ = [
    "annotations",
    "ctypes",
    "json",
    "re",
    "CheckResult",
    "Status",
    "reg_hklm",
    "reg_hkcu",
    "run_cmd",
    "run_powershell",
    "wmi_query",
    "ENUM_CURRENT_SETTINGS",
    "_DEVMODEW",
    "_get_display_adapters",
    "_get_primary_display_refresh",
]
