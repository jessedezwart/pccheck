from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_sample_rate() -> CheckResult:
    """A sample rate mismatch between Windows and the game requires real-time
    resampling, adding CPU overhead and potential audio artefacts.
    Match Windows output format to the game's native rate (usually 48000 Hz)."""
    # The default device format is stored as a WAVEFORMATEX blob
    # PKEY_AudioEngine_DeviceFormat = {f19f064d-082c-4e27-bc73-6882a1bb8e4c},0
    # Bytes 24-27 of the blob = nSamplesPerSec (little-endian DWORD)

    guids = _enum_audio_render_devices()
    sample_rates: list[int] = []
    mismatched: list[str] = []

    for guid in guids:
        state_path = f"{_MMDEVICES_RENDER}\\{guid}"
        state = reg_hklm(state_path, "DeviceState")
        if state != 1:
            continue

        fmt_key = "{f19f064d-082c-4e27-bc73-6882a1bb8e4c},0"
        blob = _read_device_property(guid, fmt_key)
        if isinstance(blob, (bytes, bytearray)) and len(blob) >= 28:
            import struct

            sample_rate = struct.unpack_from("<I", blob, 24)[0]
            sample_rates.append(sample_rate)
            if sample_rate not in (44100, 48000, 96000, 192000):
                mismatched.append(f"{guid[:8]}: {sample_rate} Hz (unusual)")

    if mismatched:
        return CheckResult(
            "Audio Sample Rate",
            Status.WARNING,
            ", ".join(mismatched),
            "Set sample rate to 48000 Hz (16-bit or 24-bit) in Sound Properties > "
            "Playback device > Properties > Advanced > Default Format.",
        )
    if sample_rates:
        rates_str = ", ".join(f"{r} Hz" for r in set(sample_rates))
        dominant = max(set(sample_rates), key=sample_rates.count)
        if dominant not in (48000, 96000, 192000):
            return CheckResult(
                "Audio Sample Rate",
                Status.INFO,
                rates_str,
                "Consider switching to 48000 Hz, which matches most game and console audio.",
            )
        return CheckResult("Audio Sample Rate", Status.GOOD, rates_str)

    # Fallback: PowerShell
    ps_out = run_powershell(
        "Get-AudioDevice -Playback 2>$null | Select-Object -ExpandProperty DefaultFormat"
    )
    if ps_out:
        return CheckResult("Audio Sample Rate", Status.INFO, ps_out)

    return CheckResult(
        "Audio Sample Rate",
        Status.UNKNOWN,
        "Cannot read format (run as Admin or check manually)",
        "Sound Control Panel > Playback > device > Properties > Advanced > Default Format.",
    )


def run_check() -> CheckResult:
    return check_sample_rate()
