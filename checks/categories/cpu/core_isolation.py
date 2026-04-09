from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *

_HVCI_PATH = (
    r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity"
)


def check_core_isolation_memory_integrity() -> CheckResult:
    """Core Isolation / Memory Integrity (HVCI) often has measurable gaming overhead."""
    hvci_enabled = reg_hklm(_HVCI_PATH, "Enabled")
    if hvci_enabled == 1:
        return CheckResult(
            "Core Isolation (Memory Integrity / HVCI)",
            Status.WARNING,
            "Enabled",
            "For gaming performance, disable: Settings > Windows Security > Device Security > "
            "Core isolation > Memory integrity OFF, then reboot.",
        )
    if hvci_enabled == 0:
        return CheckResult(
            "Core Isolation (Memory Integrity / HVCI)",
            Status.GOOD,
            "Disabled",
        )

    # Fallback: detect if HVCI is actively running via Device Guard services.
    ps_out = run_powershell(
        "$dg = Get-CimInstance -ClassName Win32_DeviceGuard "
        "-Namespace root\\Microsoft\\Windows\\DeviceGuard -ErrorAction SilentlyContinue; "
        "if ($dg -and $dg.SecurityServicesRunning) { $dg.SecurityServicesRunning -join ',' }"
    )
    running = {token.strip() for token in ps_out.split(",") if token.strip()}
    if "2" in running:
        return CheckResult(
            "Core Isolation (Memory Integrity / HVCI)",
            Status.WARNING,
            "Running",
            "For gaming performance, disable Memory integrity in Windows Security, then reboot.",
        )
    if ps_out:
        return CheckResult(
            "Core Isolation (Memory Integrity / HVCI)",
            Status.GOOD,
            "Not running",
        )

    return CheckResult(
        "Core Isolation (Memory Integrity / HVCI)",
        Status.UNKNOWN,
        "Could not determine state",
        "Check Windows Security > Device Security > Core isolation > Memory integrity.",
    )


IMPACT_EXPLANATION = "Likely moderate impact in CPU-limited scenarios: HVCI/VBS security features can reduce throughput and frame-time consistency on some systems. Source: https://learn.microsoft.com/en-us/windows/security/hardware-security/enable-virtualization-based-protection-of-code-integrity"


def run_check() -> CheckResult:
    return check_core_isolation_memory_integrity()
