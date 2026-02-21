"""
Peripheral checks:
  - Mouse polling rate (higher = more responsive input)
  - USB controller shared bandwidth / device count

To remove a check, delete or comment out its entry in get_checks().
"""

from __future__ import annotations

import re

from checks.base import (
    CheckResult,
    Status,
    reg_hklm,
    run_cmd,
    run_powershell,
    wmi_query,
)

# HID class GUID for mice
_HID_MOUSE_GUID = "{4d36e96f-e325-11ce-bfc1-08002be10318}"
# USB controller class GUID
_USB_CONTROLLER_GUID = "{36fc9e60-c465-11cf-8056-444553540000}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_hid_mice() -> list[dict]:
    """Return WMI Win32_PointingDevice rows."""
    return wmi_query(
        "Win32_PointingDevice",
        props=["Name", "DeviceID", "HardwareType", "Manufacturer", "PNPDeviceID"],
    )


__all__ = [
    "annotations",
    "re",
    "CheckResult",
    "Status",
    "reg_hklm",
    "run_powershell",
    "run_cmd",
    "wmi_query",
    "_HID_MOUSE_GUID",
    "_USB_CONTROLLER_GUID",
    "_get_hid_mice",
]
