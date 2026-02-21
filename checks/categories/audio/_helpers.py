"""
Audio checks:
  - Exclusive vs shared audio mode (exclusive = lower latency)
  - Sample rate mismatch between Windows and game output
  - Spatial audio processing (Windows Sonic / Dolby Atmos) adding latency

To remove a check, delete or comment out its entry in get_checks().
"""

from __future__ import annotations

import re
import winreg

from checks.base import (
    CheckResult,
    Status,
    reg_hkcu,
    reg_hklm,
    run_cmd,
    run_powershell,
)

# Audio endpoint property store paths
_MMDEVICES_RENDER = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"
_MMDEVICES_CAPTURE = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture"

# Property keys (PKEY format stored under \Properties)
# PKEY_AudioEndpoint_Disable_SysFx  = {1da5d803-d492-4edd-8c23-e0c0ffee7f0e},5  → value 1 = exclusive allowed
# PKEY_AudioEngine_DeviceFormat = {f19f064d-082c-4e27-bc73-6882a1bb8e4c},0 → WAVEFORMATEX blob

_SPATIAL_AUDIO_GUID = "{...}"  # varies; we check Sonic / Atmos registry paths


def _enum_audio_render_devices() -> list[str]:
    """Return list of GUIDs for render (output) audio devices."""
    guids: list[str] = []
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            _MMDEVICES_RENDER,
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        )
        i = 0
        while True:
            try:
                guids.append(winreg.EnumKey(key, i))
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except OSError:
        pass
    return guids


def _read_device_property(device_guid: str, prop_key: str, hive=winreg.HKEY_LOCAL_MACHINE):
    path = f"{_MMDEVICES_RENDER}\\{device_guid}\\Properties"
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        try:
            val, _ = winreg.QueryValueEx(key, prop_key)
            return val
        finally:
            winreg.CloseKey(key)
    except OSError:
        return None


def _get_default_device_guid() -> str | None:
    """Try to identify the default render device GUID."""
    # PowerShell COM approach is complex; use simpler method
    run_powershell(
        "[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "Get-WmiObject -Query 'SELECT * FROM Win32_SoundDevice' | "
        "Select-Object Name, Status | ConvertTo-Json"
    )
    return None  # Best effort — we'll iterate all devices


__all__ = [
    "annotations",
    "re",
    "winreg",
    "CheckResult",
    "Status",
    "reg_hklm",
    "reg_hkcu",
    "run_powershell",
    "run_cmd",
    "_MMDEVICES_RENDER",
    "_MMDEVICES_CAPTURE",
    "_SPATIAL_AUDIO_GUID",
    "_enum_audio_render_devices",
    "_read_device_property",
    "_get_default_device_guid",
]
