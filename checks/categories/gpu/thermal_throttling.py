from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_gpu_thermal_throttling() -> CheckResult:
    """Detect active GPU thermal throttling when vendor telemetry is available."""
    if _is_nvidia():
        out = _nvidia_smi(
            "--query-gpu=temperature.gpu,"
            "clocks_throttle_reasons.hw_thermal_slowdown,"
            "clocks_throttle_reasons.hw_slowdown,"
            "clocks_throttle_reasons.sw_thermal_slowdown "
            "--format=csv,noheader"
        )
        parts = [p.strip() for p in out.split(",")]
        if len(parts) >= 4:
            try:
                temp = int(parts[0])
                hw_thermal = parts[1].lower() == "active"
                hw_slow = parts[2].lower() == "active"
                sw_thermal = parts[3].lower() == "active"
                throttling = hw_thermal or hw_slow or sw_thermal

                if throttling:
                    return CheckResult(
                        "GPU Thermal Throttling",
                        Status.BAD,
                        f"{temp}C - THROTTLING ACTIVE",
                        "GPU is throttling now. Improve cooling, airflow, and fan curve.",
                    )
                if temp >= 90:
                    return CheckResult(
                        "GPU Thermal Throttling",
                        Status.WARNING,
                        f"{temp}C (very hot)",
                        "GPU is near throttle territory. Improve cooling before sustained heavy loads.",
                    )
                if temp >= 80:
                    return CheckResult(
                        "GPU Thermal Throttling",
                        Status.INFO,
                        f"{temp}C (warm but acceptable)",
                        "Consider improving airflow or fan curve for better sustained boost behavior.",
                    )
                return CheckResult("GPU Thermal Throttling", Status.GOOD, f"{temp}C - not throttling")
            except (ValueError, IndexError):
                pass

    adapters = _gpu_adapters()
    has_amd = any(any(token in desc.upper() for token in ("AMD", "RADEON", "RX")) for desc, _ in adapters)
    if has_amd:
        return CheckResult(
            "GPU Thermal Throttling",
            Status.INFO,
            "Live throttle telemetry not exposed for AMD via this tool",
            "Monitor GPU hotspot/temperature in AMD Adrenalin, HWiNFO64, or GPU-Z under gaming load.",
        )

    has_nvidia = any("NVIDIA" in desc.upper() for desc, _ in adapters)
    if has_nvidia:
        return CheckResult(
            "GPU Thermal Throttling",
            Status.INFO,
            "NVIDIA GPU detected but nvidia-smi unavailable",
            "Install/update NVIDIA driver components and verify temperatures with HWiNFO64 or GPU-Z.",
        )

    return CheckResult(
        "GPU Thermal Throttling",
        Status.INFO,
        "No vendor telemetry path available",
        "Monitor GPU temperature in HWiNFO64 or GPU-Z under gaming load.",
    )


def run_check() -> CheckResult:
    return check_gpu_thermal_throttling()
