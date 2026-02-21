from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_mouse_polling_rate() -> CheckResult:
    """Higher mouse polling rate (500–8000 Hz) means more position updates per
    second, reducing the average input lag from movement to cursor update.
    Windows reports the polling rate indirectly via HID report interval."""
    # The mouse report interval is stored in:
    # HKLM\SYSTEM\CurrentControlSet\Services\mouclass\Parameters\MouseDataQueueSize  (unrelated)
    # The real polling rate is in the HID device's firmware; we can try to
    # read it from the USB descriptor or from known mouse software registries.

    # Method 1: Check via registry for known mouse software (Logitech, Razer, etc.)
    logitech_rate = reg_hklm(
        r"SOFTWARE\Logitech\LCGS\Ghub",
        "PollingRate",
    )
    reg_hklm(
        r"SOFTWARE\Razer\Synapse3\Apps\Razer Synapse 3\Config",
        "PollingRate",
    )

    if logitech_rate:
        rate = int(logitech_rate) if str(logitech_rate).isdigit() else logitech_rate
        status = Status.GOOD if str(rate) in ("1000", "2000", "4000", "8000") else Status.INFO
        return CheckResult(
            "Mouse Polling Rate",
            status,
            f"{rate} Hz (Logitech G HUB)",
            "" if status == Status.GOOD else "Increase to 1000+ Hz in Logitech G HUB settings.",
        )

    # Method 2: WMI / HID device enumeration
    mice = _get_hid_mice()
    mouse_names = [m.get("Name", "") for m in mice if m.get("Name")]

    if not mouse_names:
        mouse_names_raw = run_cmd(
            "wmic path Win32_PointingDevice get Name,Manufacturer /format:list"
        )
        names = re.findall(r"Name=(.+)", mouse_names_raw)
        mouse_names = [n.strip() for n in names if n.strip()]

    # Method 3: Check MouseHIDConfig via registry (unreliable, but worth trying)
    # Some Corsair mice write polling rate here:
    corsair_rate = reg_hklm(
        r"SOFTWARE\Corsair\CorsairHid\DeviceProperties",
        "PollingRate",
    )
    if corsair_rate:
        return CheckResult(
            "Mouse Polling Rate",
            Status.GOOD,
            f"{corsair_rate} Hz (Corsair iCUE)",
        )

    # Method 4: PowerShell - read USB device bandwidth consumption as a proxy
    # Higher polling rate mice use proportionally more USB bandwidth
    # This is approximate and not reliable enough to report a Hz value

    if mouse_names:
        return CheckResult(
            "Mouse Polling Rate",
            Status.INFO,
            f"Mouse detected: {mouse_names[0][:40]}",
            "Polling rate cannot be read from OS directly. "
            "Set 1000 Hz (or higher if supported) in your mouse's companion software. "
            "Use MouseTester or HWINFO to verify actual polling rate.",
        )

    return CheckResult(
        "Mouse Polling Rate",
        Status.INFO,
        "No mouse detected via WMI",
        "Set polling rate to 1000 Hz or higher in your mouse's software (Synapse, G HUB, Armory Crate, etc.).",
    )


def run_check() -> CheckResult:
    return check_mouse_polling_rate()
