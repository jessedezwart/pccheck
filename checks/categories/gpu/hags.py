from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_hags() -> CheckResult:
    """Hardware-Accelerated GPU Scheduling (HAGS) offloads GPU scheduling
    to the GPU itself, reducing CPU overhead and latency. Enable it if supported."""
    val = reg_hklm(
        r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        "HwSchMode",
    )
    # 1 = disabled, 2 = enabled
    if val == 2:
        return CheckResult(
            "HAGS (HW-Accelerated GPU Scheduling)",
            Status.GOOD,
            "Enabled",
        )
    if val == 1 or val is None:
        return CheckResult(
            "HAGS (HW-Accelerated GPU Scheduling)",
            Status.INFO,
            "Disabled",
            "Enable in Settings > Display > Graphics > Default graphics settings > "
            "Hardware-Accelerated GPU Scheduling. Reduces GPU latency on DX12/Vulkan. "
            "Note: on some systems, it may not be possible to disable HAGS while the "
            "virtualization stack is enabled (e.g., Hyper-V/VBS/Memory Integrity/WSL2).",
        )
    return CheckResult(
        "HAGS (HW-Accelerated GPU Scheduling)",
        Status.UNKNOWN,
        f"Unknown value ({val})",
    )


def run_check() -> CheckResult:
    return check_hags()
