from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def _parse_sample_rate_from_device_format(blob: bytes | bytearray) -> int | None:
    """Parse nSamplesPerSec from PKEY_AudioEngine_DeviceFormat.

    Seen layouts:
      - Raw WAVEFORMAT(EX/EXTENSIBLE): sample rate at offset 4
      - Property-blob wrapper + WAVEFORMAT: sample rate at offset 12
    """
    import struct

    if not isinstance(blob, (bytes, bytearray)) or len(blob) < 8:
        return None

    def _try_base(base: int) -> int | None:
        if len(blob) < base + 8:
            return None
        fmt_tag = struct.unpack_from("<H", blob, base)[0]
        if fmt_tag not in (1, 3, 0xFFFE):
            return None
        rate = struct.unpack_from("<I", blob, base + 4)[0]
        if 8_000 <= rate <= 768_000:
            return rate
        return None

    # Prefer wrapped layout first (common in MMDevices property store), then raw layout.
    return _try_base(8) or _try_base(0)


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
    labels: list[str] = []

    for guid in guids:
        state_path = f"{_MMDEVICES_RENDER}\\{guid}"
        state = reg_hklm(state_path, "DeviceState")
        if state != 1:
            continue

        device_name = (
            reg_hklm(state_path, "FriendlyName")
            or _read_device_property(guid, "{b3f8fa53-0004-438e-9003-51a46e139bfc},6")
            or _read_device_property(guid, "{a45c254e-df1c-4efd-8020-67d146a850e0},14")
            or guid[:8]
        )

        fmt_key = "{f19f064d-082c-4e27-bc73-6882a1bb8e4c},0"
        blob = _read_device_property(guid, fmt_key)
        sample_rate = _parse_sample_rate_from_device_format(blob) if blob is not None else None
        if sample_rate is not None:
            sample_rates.append(sample_rate)
            labels.append(f"{device_name}: {sample_rate} Hz")
            if sample_rate not in (44100, 48000, 96000, 192000):
                mismatched.append(f"{device_name}: {sample_rate} Hz (unusual)")

    if mismatched:
        return CheckResult(
            "Audio Sample Rate",
            Status.WARNING,
            ", ".join(mismatched),
            "Set sample rate to 48000 Hz (16-bit or 24-bit) in Sound Properties > "
            "Playback device > Properties > Advanced > Default Format.",
        )
    if sample_rates:
        rates_str = ", ".join(labels) if labels else ", ".join(f"{r} Hz" for r in set(sample_rates))
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
