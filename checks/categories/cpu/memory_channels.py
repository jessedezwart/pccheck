from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_memory_channels() -> CheckResult:
    """Dual-channel RAM gives ~20-50% more memory bandwidth over single-channel,
    important for integrated GPUs and CPU-intensive games."""
    rows = wmi_query("Win32_PhysicalMemory", props=["BankLabel", "Capacity", "Speed"])
    if not rows:
        # Fallback via wmic
        out = run_cmd("wmic memorychip get BankLabel,Capacity /format:list")
        count = out.count("BankLabel=")
    else:
        count = len(rows)

    if count == 0:
        return CheckResult("Memory Channels", Status.UNKNOWN, "No DIMMs detected")
    if count == 1:
        return CheckResult(
            "Memory Channels",
            Status.BAD,
            "Single-channel (1 DIMM)",
            "Install a matching second stick in the paired slot for dual-channel mode.",
        )
    if count % 2 == 0:
        return CheckResult(
            "Memory Channels",
            Status.GOOD,
            f"Likely dual-channel ({count} DIMMs)",
            "Confirm sticks are in the correct A2/B2 (or 2/4) slots per your motherboard manual.",
        )
    return CheckResult(
        "Memory Channels",
        Status.WARNING,
        f"{count} DIMMs (odd count)",
        "Odd DIMM count — one channel may run single. Check motherboard manual for optimal slot population.",
    )


IMPACT_EXPLANATION = "Likely moderate-to-high impact in memory-sensitive games: single-channel memory can limit bandwidth and hurt frame-time consistency. Source: https://en.wikipedia.org/wiki/Multi-channel_memory_architecture"


def run_check() -> CheckResult:
    return check_memory_channels()
