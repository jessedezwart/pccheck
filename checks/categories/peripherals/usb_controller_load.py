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

    # Count devices per controller via Win32_USBControllerDevice associations.
    # Parsing in Python is more reliable than wildcard matching escaped DeviceID strings.
    def _norm_device_id(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        return value.replace("\\\\", "\\").strip().upper()

    def _extract_assoc_device_id(path_value: object) -> str | None:
        if not isinstance(path_value, str):
            return None
        m = re.search(r'DeviceID="([^"]+)"', path_value, re.IGNORECASE)
        if not m:
            return None
        return _norm_device_id(m.group(1))

    controller_names: dict[str, str] = {}
    devices_by_controller: dict[str, set[str]] = {}
    for row in rows:
        ctrl_id = _norm_device_id(row.get("DeviceID"))
        ctrl_name = str(row.get("Name") or "?").strip()
        if not ctrl_id:
            continue
        controller_names[ctrl_id] = ctrl_name
        devices_by_controller.setdefault(ctrl_id, set())

    assoc_rows = wmi_query(
        "Win32_USBControllerDevice",
        props=["Antecedent", "Dependent"],
    )
    for assoc in assoc_rows:
        ctrl_id = _extract_assoc_device_id(assoc.get("Antecedent"))
        dep_id = _extract_assoc_device_id(assoc.get("Dependent"))
        if not ctrl_id or not dep_id:
            continue
        if ctrl_id in devices_by_controller:
            devices_by_controller[ctrl_id].add(dep_id)

    controller_info = [
        (controller_names[cid], len(devices_by_controller.get(cid, set())))
        for cid in controller_names
    ]

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

    return CheckResult(
        "USB Controller Load",
        Status.GOOD,
        f"{total_devices} device(s) across {len(controller_info)} controller(s)",
    )


IMPACT_EXPLANATION = "Likely low-to-moderate impact: heavy shared USB bus activity can increase input-device service latency in edge cases. Source: https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/usb-bandwidth-allocation"


def run_check() -> CheckResult:
    return check_usb_controller_load()
