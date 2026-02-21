from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_nic_power_saving() -> CheckResult:
    """Windows can cut NIC power in sleep states, causing wake-up latency
    spikes mid-game. Disable power management on the NIC."""
    nics = _physical_nics()
    if not nics:
        return CheckResult(
            "NIC Power Management",
            Status.UNKNOWN,
            "No physical NICs found",
            "Check Device Manager > NIC > Properties > Power Management tab.",
        )

    power_managed: list[str] = []

    for desc, path in nics[:4]:
        # PnPCapabilities: 24 (0x18) = disable power management
        pnp_cap = reg_hklm(path, "PnPCapabilities")
        if pnp_cap is None or pnp_cap != 24:
            # Also check "SelectiveSuspend" key
            sel_suspend = reg_hklm(path, "*SelectiveSuspend")
            if sel_suspend != "0":
                power_managed.append(desc)

    if power_managed:
        return CheckResult(
            "NIC Power Management",
            Status.WARNING,
            f"Power saving on: {', '.join(power_managed[:2])}",
            "Device Manager > NIC > Properties > Power Management > "
            "Uncheck 'Allow the computer to turn off this device to save power'.",
        )
    return CheckResult(
        "NIC Power Management",
        Status.GOOD,
        "Power saving disabled on physical NICs",
    )


def run_check() -> CheckResult:
    return check_nic_power_saving()
