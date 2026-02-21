from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_vbs_hvci() -> CheckResult:
    """Virtualization Based Security (VBS) and HVCI add a hypervisor layer
    that can reduce GPU performance by 5-15%. Disable if not needed for security."""
    # Prefer querying the live running state via CIM
    ps_out = run_powershell(
        "(Get-CimInstance -ClassName Win32_DeviceGuard "
        "-Namespace root\\Microsoft\\Windows\\DeviceGuard "
        "-ErrorAction SilentlyContinue).VirtualizationBasedSecurityStatus"
    )
    # 0=off 1=configured 2=running
    if ps_out == "2":
        return CheckResult(
            "VBS / HVCI",
            Status.WARNING,
            "Running (active)",
            "VBS is active. Disable: Settings > Windows Security > Device Security > "
            "Core Isolation > Memory Integrity OFF, then reboot.",
        )
    if ps_out in ("0", "1"):
        return CheckResult("VBS / HVCI", Status.GOOD, "Not running")

    # Fallback: check registry config flag
    enabled = reg_hklm(
        r"SYSTEM\CurrentControlSet\Control\DeviceGuard",
        "EnableVirtualizationBasedSecurity",
    )
    hvci = reg_hklm(
        r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity",
        "Enabled",
    )
    if enabled == 1 or hvci == 1:
        return CheckResult(
            "VBS / HVCI",
            Status.WARNING,
            "Configured (reboot to check state)",
            "VBS appears to be enabled. Disable Memory Integrity in Windows Security settings.",
        )
    return CheckResult("VBS / HVCI", Status.GOOD, "Disabled")


def run_check() -> CheckResult:
    return check_vbs_hvci()
