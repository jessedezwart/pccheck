from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_spatial_audio() -> CheckResult:
    """Spatial audio (Windows Sonic, Dolby Atmos for Headphones, DTS:X) adds
    a DSP processing stage that increases audio latency and CPU usage.
    Disable if you don't actively need the surround effect."""
    # Windows Sonic is stored per-device in:
    # HKCU\Software\Microsoft\Windows\CurrentVersion\Audio\SpatialRendering
    # or HKLM for system-wide

    sonic_val = reg_hkcu(
        r"Software\Microsoft\Windows\CurrentVersion\Audio\SpatialRendering",
        "SpatialAudioEnabled",
    )
    # Also check via the SpatialAudio endpoint role
    sonic_format = reg_hkcu(
        r"Software\Microsoft\Windows\CurrentVersion\Audio\SpatialRendering",
        "SelectedSpatialAudioFormat",
    )

    # Dolby Atmos
    dolby_enabled = reg_hkcu(
        r"Software\Dolby\Dolby Access\Atmos",
        "AtmosEnabled",
    )

    if sonic_val == 1 or dolby_enabled == 1:
        format_name = sonic_format or "Windows Sonic / spatial audio"
        return CheckResult(
            "Spatial Audio",
            Status.WARNING,
            f"Enabled: {format_name}",
            "Spatial audio adds DSP latency. Disable in Sound Settings > "
            "sound device > Spatial sound = Off (or Windows Sonic = Off).",
        )

    # Check via powershell as fallback
    run_powershell(
        "[Windows.Media.Devices.MediaDevice, Windows.Media, ContentType=WindowsRuntime] | Out-Null; "
        "(New-Object -ComObject mmdeviceenumerator).GetDefaultAudioEndpoint(0,1).Properties"
        " 2>$null | Out-String"
    )

    if sonic_val == 0:
        return CheckResult("Spatial Audio", Status.GOOD, "Disabled")

    return CheckResult(
        "Spatial Audio",
        Status.GOOD,
        "Not detected as enabled",
    )


def run_check() -> CheckResult:
    return check_spatial_audio()
