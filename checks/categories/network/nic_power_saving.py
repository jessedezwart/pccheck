from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def _allow_turn_off_enabled(pnp_cap: int | None) -> bool:
    """Interpret NIC PnPCapabilities for
    'Allow the computer to turn off this device to save power'.

    Common values seen in the field:
      - 24 or 280: option is unchecked (disabled)
      - 0 or 272: option is checked (enabled)
      - 256: often reported by Realtek when the UI checkbox is already unchecked
      - None: treat as enabled/default
    """
    if pnp_cap in (24, 256, 280):
        return False
    return True


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
    disabled_driver_managed: list[str] = []

    for desc, path in nics[:4]:
        # PnPCapabilities drives Device Manager power-tab behavior for many NICs.
        pnp_cap = reg_hklm(path, "PnPCapabilities")
        if not isinstance(pnp_cap, int):
            pnp_cap = None
        if pnp_cap == 256:
            disabled_driver_managed.append(f"{desc} (PnPCapabilities=256)")
        elif _allow_turn_off_enabled(pnp_cap):
            suffix = f" (PnPCapabilities={pnp_cap})" if pnp_cap is not None else ""
            power_managed.append(f"{desc}{suffix}")

    if power_managed:
        return CheckResult(
            "NIC Power Management",
            Status.WARNING,
            f"Power saving on: {', '.join(power_managed[:2])}",
            "Device Manager > NIC > Properties > Power Management > "
            "Uncheck 'Allow the computer to turn off this device to save power'.",
        )
    if disabled_driver_managed:
        return CheckResult(
            "NIC Power Management",
            Status.GOOD,
            f"Disabled (driver-managed): {', '.join(disabled_driver_managed[:2])}",
        )
    return CheckResult(
        "NIC Power Management",
        Status.GOOD,
        "Power saving disabled on physical NICs",
    )


def run_check() -> CheckResult:
    return check_nic_power_saving()
