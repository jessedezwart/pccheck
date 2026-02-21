from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def _windows_vrr_enabled() -> bool | None:
    """
    Best-effort Windows global VRR toggle detection.
    Value is stored inside DirectXUserGlobalSettings when present.
    """
    blob = reg_hkcu(r"Software\Microsoft\DirectX\UserGpuPreferences", "DirectXUserGlobalSettings")
    if not blob or not isinstance(blob, str):
        return None

    for item in blob.split(";"):
        part = item.strip().lower()
        if part.startswith("vrroptimizeenable="):
            return part.endswith("=1")
    return None


def check_vrr() -> CheckResult:
    """Variable Refresh Rate (G-Sync / FreeSync / VRR) syncs display refresh to GPU output."""
    # NVIDIA G-Sync (global key used on some driver builds)
    gsync_val = reg_hklm(
        r"SYSTEM\CurrentControlSet\Services\nvlddmkm\Global\NVTweak",
        "NvCplGSyncEnabled",
    )

    # AMD FreeSync (key presence/value varies by driver generation)
    freesync_val = reg_hkcu(r"Software\AMD\CN\OverDrive\Freesync", "Enabled")

    # Windows VRR setting
    windows_vrr = _windows_vrr_enabled()

    if gsync_val == 1 or freesync_val == 1 or windows_vrr is True:
        return CheckResult(
            "VRR / G-Sync / FreeSync",
            Status.GOOD,
            "Enabled",
            "VRR eliminates tearing with lower latency than classic V-Sync. Enable it in-game too.",
        )

    if gsync_val == 0 or freesync_val == 0 or windows_vrr is False:
        return CheckResult(
            "VRR / G-Sync / FreeSync",
            Status.INFO,
            "Disabled",
            "Enable G-Sync in NVIDIA Control Panel or FreeSync in AMD Radeon Software for smoother frametimes.",
        )

    return CheckResult(
        "VRR / G-Sync / FreeSync",
        Status.INFO,
        "Not exposed by current driver/Windows registry keys",
        "Check monitor OSD plus GPU control panel directly (NVIDIA Set up G-SYNC / AMD Display > FreeSync).",
    )


def run_check() -> CheckResult:
    return check_vrr()
