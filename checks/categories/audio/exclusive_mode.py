from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_exclusive_mode() -> CheckResult:
    """Exclusive mode lets applications take full control of the audio device,
    bypassing Windows mixing for the lowest possible audio latency.
    Shared mode adds a software mixer step (~10-20 ms extra latency)."""
    # Registry: HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render\{guid}\Properties
    # PKEY {00000000-0000-0000-0000-000000000000},0 = device friendly name
    # Exclusive mode allowed flag:
    #   {1da5d803-d492-4edd-8c23-e0c0ffee7f0e},5  = DWORD 0 → exclusive allowed
    #   The "Allow applications to take exclusive control" checkbox in Sound properties

    # For each render device, check the exclusive-mode flag
    guids = _enum_audio_render_devices()
    exclusive_blocked: list[str] = []
    exclusive_ok: list[str] = []

    # Windows stores "DeviceState" as DWORD at device level; 1 = active
    for guid in guids:
        # Check state: 1=Active, 2=Disabled, 4=Not present, 8=Unplugged
        state_path = f"{_MMDEVICES_RENDER}\\{guid}"
        state = reg_hklm(state_path, "DeviceState")
        if state != 1:
            continue  # Only care about active devices

        # Check exclusive mode flag (stored as DWORD under Properties)
        # Key name is the PKEY string literal
        excl_key = "{1da5d803-d492-4edd-8c23-e0c0ffee7f0e},5"
        val = _read_device_property(guid, excl_key)
        if val == 1:
            exclusive_blocked.append(guid[:8])
        else:
            exclusive_ok.append(guid[:8])

    if not exclusive_blocked and not exclusive_ok:
        # PowerShell fallback: check sound device properties
        return CheckResult(
            "Audio Exclusive Mode",
            Status.UNKNOWN,
            "Could not read audio device properties (run as Admin)",
            "Right-click sound icon > Sounds > Playback > device Properties > Advanced > "
            "enable 'Allow applications to take exclusive control of this device'.",
        )

    if exclusive_blocked:
        return CheckResult(
            "Audio Exclusive Mode",
            Status.WARNING,
            f"{len(exclusive_blocked)} device(s) block exclusive mode",
            "Enable exclusive mode: Sound Control Panel > Playback device > Properties > "
            "Advanced > check 'Allow applications to take exclusive control'.",
        )
    return CheckResult(
        "Audio Exclusive Mode",
        Status.GOOD,
        f"Allowed on {len(exclusive_ok)} active device(s)",
    )


def run_check() -> CheckResult:
    return check_exclusive_mode()
