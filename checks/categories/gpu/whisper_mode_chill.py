from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_whisper_mode_chill() -> CheckResult:
    """NVIDIA Whisper Mode / AMD Chill cap frame rates to save power.
    If enabled unexpectedly they silently limit in-game performance."""

    # Check NVIDIA Whisper Mode global flag
    whisper = reg_hkcu(
        r"Software\NVIDIA Corporation\Global\NVTweak",
        "NvCplAdapterManagementPowerSaveEnabled",
    )
    if whisper == 1:
        return CheckResult(
            "Whisper Mode / AMD Chill",
            Status.WARNING,
            "NVIDIA Whisper Mode appears ON",
            "Disable in NVIDIA Control Panel > Manage 3D Settings > Power management mode "
            "= Prefer maximum performance.",
        )

    # Check AMD Chill
    chill = reg_hklm(
        f"SYSTEM\\CurrentControlSet\\Control\\Class\\{VIDEO_CLASS_GUID}\\0000",
        "ChillEnabled",
    )
    if chill == 1:
        return CheckResult(
            "Whisper Mode / AMD Chill",
            Status.WARNING,
            "AMD Chill is globally enabled",
            "Disable AMD Chill in Radeon Software > Gaming > Global Graphics > Chill = Off.",
        )

    # Check AMD Chill via HKCU path used by Radeon Software
    chill2 = reg_hkcu(
        r"Software\ATI Technologies\CBT",
        "ChillEnabled",
    )
    if chill2 == 1:
        return CheckResult(
            "Whisper Mode / AMD Chill",
            Status.WARNING,
            "AMD Chill is enabled",
            "Disable AMD Chill in Radeon Software > Gaming > Global Graphics > Chill = Off.",
        )

    return CheckResult(
        "Whisper Mode / AMD Chill",
        Status.GOOD,
        "Not detected as enabled",
    )


def run_check() -> CheckResult:
    return check_whisper_mode_chill()
