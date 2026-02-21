from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_rebar() -> CheckResult:
    """Resizable BAR / Smart Access Memory can improve performance in supported titles."""
    adapters = _gpu_adapters()
    has_nvidia = any(
        any(token in desc.upper() for token in ("NVIDIA", "GEFORCE", "QUADRO", "RTX", "GTX"))
        for desc, _ in adapters
    )
    has_amd = any(any(token in desc.upper() for token in ("AMD", "RADEON", "RX")) for desc, _ in adapters)

    if has_nvidia:
        for desc, path in adapters:
            if "NVIDIA" not in desc.upper() and "GEFORCE" not in desc.upper():
                continue
            val = reg_hklm(path, "NvCplReBarEnabled")
            if val is None:
                continue
            if int(val) == 1:
                return CheckResult("ReBAR / Smart Access Memory", Status.GOOD, "Enabled (NVIDIA)")
            return CheckResult(
                "ReBAR / Smart Access Memory",
                Status.WARNING,
                "Disabled (NVIDIA)",
                "Enable Resizable BAR in BIOS (PCIe settings) and confirm in NVIDIA Control Panel/GPU-Z.",
            )

    if has_amd:
        for desc, path in adapters:
            if not any(token in desc.upper() for token in ("AMD", "RADEON", "RX")):
                continue

            # Seen on many modern AMD drivers: 0=off, 1=on (or driver-managed on).
            rebar_mode = reg_hklm(path, "KMD_RebarControlMode")
            if rebar_mode is not None:
                if int(rebar_mode) >= 1:
                    return CheckResult(
                        "ReBAR / Smart Access Memory", Status.GOOD, "Enabled (AMD, driver flag)"
                    )
                return CheckResult(
                    "ReBAR / Smart Access Memory",
                    Status.WARNING,
                    "Disabled (AMD, driver flag)",
                    "Enable Smart Access Memory / Resizable BAR in BIOS and Radeon Software.",
                )

            sam_val = reg_hklm(path, "DalSAMEnabled")
            if sam_val is not None:
                if int(sam_val) == 1:
                    return CheckResult("ReBAR / Smart Access Memory", Status.GOOD, "Enabled (AMD SAM)")
                return CheckResult(
                    "ReBAR / Smart Access Memory",
                    Status.WARNING,
                    "Disabled (AMD)",
                    "Enable Smart Access Memory / Resizable BAR in BIOS for a free performance boost.",
                )

    return CheckResult(
        "ReBAR / Smart Access Memory",
        Status.INFO,
        "Not exposed by current driver telemetry",
        "Confirm in GPU-Z > Advanced > Resizable BAR. Enable in BIOS if supported.",
    )


def run_check() -> CheckResult:
    return check_rebar()
