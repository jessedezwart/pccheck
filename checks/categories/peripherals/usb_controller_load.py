from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_usb_controller_load() -> CheckResult:
    """USB controllers have limited shared bandwidth. Many high-speed devices
    on the same controller (especially USB 2.0) can cause input jitter.
    Connect gaming peripherals to USB 3.0 ports on separate controllers."""
    rows = wmi_query(
        "Win32_USBController",
        props=["Name", "DeviceID", "Status"],
    )
    if not rows:
        return CheckResult(
            "USB Controller Load",
            Status.UNKNOWN,
            "Could not enumerate USB controllers",
            "Check USB controllers in Device Manager > Universal Serial Bus controllers.",
        )

    # Count devices per controller via Win32_USBControllerDevice
    ps_script = """
$controllers = Get-WmiObject Win32_USBController
$assoc = Get-WmiObject Win32_USBControllerDevice
$result = @()
foreach ($ctrl in $controllers) {
    $devCount = ($assoc | Where-Object { $_.Antecedent -like "*$($ctrl.DeviceID)*" }).Count
    $result += "$($ctrl.Name)|$devCount"
}
$result -join ";"
"""
    ps_out = run_powershell(ps_script)
    controller_info: list[tuple[str, int]] = []

    if ps_out:
        for part in ps_out.split(";"):
            part = part.strip()
            if "|" in part:
                name, _, count_str = part.rpartition("|")
                try:
                    controller_info.append((name.strip(), int(count_str.strip())))
                except ValueError:
                    pass

    if not controller_info:
        # Fallback: just list controller names
        names = [r.get("Name", "?") for r in rows]
        return CheckResult(
            "USB Controller Load",
            Status.INFO,
            f"{len(names)} controller(s): {', '.join(names[:3])}",
            "Connect gaming peripherals (mouse, keyboard) to USB 3.0 ports and "
            "avoid sharing with high-bandwidth USB 2.0 devices.",
        )

    overloaded = [(n, c) for n, c in controller_info if c > 8]
    total_devices = sum(c for _, c in controller_info)

    if overloaded:
        overload_str = ", ".join(f"{n[:30]} ({c} devices)" for n, c in overloaded[:2])
        return CheckResult(
            "USB Controller Load",
            Status.WARNING,
            f"{overload_str}",
            "Too many devices on one USB controller. Move gaming peripherals to ports "
            "on a different controller (check device manager for separate USB root hubs).",
        )

    ", ".join(f"{n[:25]} ({c} dev)" for n, c in controller_info[:3])
    return CheckResult(
        "USB Controller Load",
        Status.GOOD,
        f"{total_devices} device(s) across {len(controller_info)} controller(s)",
    )


def run_check() -> CheckResult:
    return check_usb_controller_load()
