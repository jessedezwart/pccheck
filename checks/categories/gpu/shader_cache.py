from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_shader_cache() -> CheckResult:
    """NVIDIA shader cache should not be disabled; otherwise shader stutter can increase."""
    has_nvidia_adapter = any("NVIDIA" in desc.upper() for desc, _ in _gpu_adapters())
    if not has_nvidia_adapter and not _is_nvidia():
        return CheckResult(
            "Shader Cache (NVIDIA)",
            Status.GOOD,
            "Not applicable (no NVIDIA GPU detected)",
        )

    val = reg_hkcu(r"Software\NVIDIA Corporation\NvCplInfoSaver", "ShaderCacheEnable")
    if val == 0:
        return CheckResult(
            "Shader Cache (NVIDIA)",
            Status.BAD,
            "Disabled",
            "Enable in NVIDIA Control Panel > Manage 3D Settings > Shader Cache Size (Driver Default or larger).",
        )
    if val is None:
        return CheckResult(
            "Shader Cache (NVIDIA)",
            Status.INFO,
            "Driver-managed / key not present",
            "Open NVIDIA Control Panel and verify Shader Cache is not disabled.",
        )
    return CheckResult("Shader Cache (NVIDIA)", Status.GOOD, "Enabled")


def run_check() -> CheckResult:
    return check_shader_cache()
