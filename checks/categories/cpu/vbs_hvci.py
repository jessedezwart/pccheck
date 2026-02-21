from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_vbs() -> CheckResult:
    """Report VBS state separately from Core Isolation (HVCI/Memory Integrity)."""
    # Prefer querying the live running state via CIM
    ps_out = run_powershell(
        "(Get-CimInstance -ClassName Win32_DeviceGuard "
        "-Namespace root\\Microsoft\\Windows\\DeviceGuard "
        "-ErrorAction SilentlyContinue).VirtualizationBasedSecurityStatus"
    )
    # 0=off 1=configured 2=running
    if ps_out == "2":
        return CheckResult(
            "Virtualization-Based Security (VBS)",
            Status.INFO,
            "Running (active)",
            "Can be expected when using Hyper-V/WSL2/VMs. For max gaming performance, "
            "you can disable VBS if you do not need virtualization security features.",
        )
    if ps_out == "1":
        return CheckResult(
            "Virtualization-Based Security (VBS)",
            Status.INFO,
            "Configured (not currently running)",
            "If you do not need virtualization security features, disable VBS for maximum gaming performance.",
        )
    if ps_out == "0":
        return CheckResult("Virtualization-Based Security (VBS)", Status.GOOD, "Not running")

    # Fallback: check registry config flag
    enabled = reg_hklm(
        r"SYSTEM\CurrentControlSet\Control\DeviceGuard",
        "EnableVirtualizationBasedSecurity",
    )
    if enabled == 1:
        return CheckResult(
            "Virtualization-Based Security (VBS)",
            Status.INFO,
            "Configured (reboot to check state)",
            "VBS appears enabled by policy/configuration.",
        )
    return CheckResult("Virtualization-Based Security (VBS)", Status.GOOD, "Disabled")


def run_check() -> CheckResult:
    return check_vbs()
