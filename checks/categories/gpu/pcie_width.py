from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def _read_pcie_width_from_pnp() -> tuple[str, int, int] | None:
    """
    Cross-vendor fallback via PnP PCI device properties.
    Returns (gpu_name, current_width, max_width).
    """
    ps = (
        "$dev = Get-PnpDevice -Class Display -ErrorAction SilentlyContinue | "
        "Where-Object { $_.InstanceId -like 'PCI*' } | "
        "Sort-Object @{Expression={ if (($_.FriendlyName -as [string]) -match "
        "'parsec|virtual|remote|microsoft basic') {1} else {0} }}, FriendlyName | "
        "Select-Object -First 1; "
        "if ($dev) { "
        "$cur = (Get-PnpDeviceProperty -InstanceId $dev.InstanceId "
        "-KeyName 'DEVPKEY_PciDevice_CurrentLinkWidth' -ErrorAction SilentlyContinue).Data; "
        "$max = (Get-PnpDeviceProperty -InstanceId $dev.InstanceId "
        "-KeyName 'DEVPKEY_PciDevice_MaxLinkWidth' -ErrorAction SilentlyContinue).Data; "
        'if ($null -ne $cur -and $null -ne $max) { "$($dev.FriendlyName)|$cur|$max" } }'
    )
    out = run_powershell(ps)
    parts = [p.strip() for p in out.split("|")]
    if len(parts) != 3:
        return None
    try:
        return parts[0], int(parts[1]), int(parts[2])
    except ValueError:
        return None


def check_pcie_width() -> CheckResult:
    """GPU should run at PCIe x16 for full bandwidth. x8 is usually fine; x4 can bottleneck."""
    if _is_nvidia():
        width_str = _nvidia_smi("--query-gpu=pcie.link.width.current --format=csv,noheader,nounits")
        max_str = _nvidia_smi("--query-gpu=pcie.link.width.max --format=csv,noheader,nounits")
        if width_str.strip().isdigit():
            width = int(width_str.strip())
            max_w = int(max_str.strip()) if max_str.strip().isdigit() else 16
            value = f"x{width} (max x{max_w})"
            if width >= 16:
                return CheckResult("PCIe Link Width", Status.GOOD, value)
            if width >= 8:
                return CheckResult(
                    "PCIe Link Width",
                    Status.INFO,
                    value,
                    "x8 usually has small gaming impact. Check motherboard lane-sharing if unexpected.",
                )
            return CheckResult(
                "PCIe Link Width",
                Status.BAD,
                value,
                f"x{width} is significantly reduced. Check motherboard lane sharing / slot wiring / BIOS.",
            )

    pnp_value = _read_pcie_width_from_pnp()
    if pnp_value is None:
        return CheckResult(
            "PCIe Link Width",
            Status.INFO,
            "Not exposed by current telemetry path",
            "Check PCIe link width in GPU-Z > Advanced tab. x16 ideal, x8 generally acceptable.",
        )

    gpu_name, width, max_w = pnp_value
    value = f"{gpu_name}: x{width} (max x{max_w})"
    if width >= max_w >= 16:
        return CheckResult("PCIe Link Width", Status.GOOD, value)
    if width >= 8:
        return CheckResult(
            "PCIe Link Width",
            Status.INFO,
            value,
            "x8 usually has little real-world impact. Validate slot/lanes if max width should be higher.",
        )
    return CheckResult(
        "PCIe Link Width",
        Status.WARNING,
        value,
        "Very low active PCIe width can bottleneck high-end GPUs. Verify slot and BIOS lane configuration.",
    )


def run_check() -> CheckResult:
    return check_pcie_width()
