from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_interrupt_moderation() -> CheckResult:
    """NIC interrupt moderation batches network interrupts to reduce CPU load,
    but it adds 0.1–2 ms of latency per packet. For gaming, disable it."""
    nics = _physical_nics()
    if not nics:
        return CheckResult(
            "NIC Interrupt Moderation",
            Status.UNKNOWN,
            "No physical NICs found in registry",
            "Disable in Device Manager > NIC > Properties > Advanced > Interrupt Moderation = Disabled.",
        )

    enabled_nics: list[str] = []
    disabled_nics: list[str] = []

    for desc, path in nics[:4]:
        val = reg_hklm(path, "*InterruptModeration")
        if val == "0":
            disabled_nics.append(desc)
        elif val == "1":
            enabled_nics.append(desc)
        else:
            # Not set = adapter uses its own default (usually enabled)
            enabled_nics.append(f"{desc} (default)")

    if enabled_nics:
        return CheckResult(
            "NIC Interrupt Moderation",
            Status.WARNING,
            f"Enabled on: {', '.join(enabled_nics[:2])}",
            "Disable in Device Manager > NIC > Properties > Advanced tab > "
            "Interrupt Moderation = Disabled.",
        )
    return CheckResult(
        "NIC Interrupt Moderation",
        Status.GOOD,
        "Disabled on all physical NICs",
    )


IMPACT_EXPLANATION = "Likely low-to-moderate impact: interrupt moderation mainly affects online latency/jitter rather than average FPS. Source: https://learn.microsoft.com/en-us/windows-hardware/drivers/network/interrupt-moderation"


def run_check() -> CheckResult:
    return check_interrupt_moderation()
