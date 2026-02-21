from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_nagle_algorithm() -> CheckResult:
    """Nagle's algorithm bundles small TCP packets together, adding 40-200 ms
    of latency in online games. Disable it (TCPNoDelay=1) for gaming."""
    guids = _get_tcpip_interface_guids()
    nagle_enabled: list[str] = []
    nagle_disabled: int = 0

    for guid in guids:
        path = f"{_TCPIP_INTERFACES}\\{guid}"
        nic_name = _nic_name_by_guid(guid)
        if nic_name and _is_virtual(nic_name):
            continue
        label = nic_name or (guid.strip("{}")[:8] + "...")

        no_delay = reg_hklm(path, "TCPNoDelay")
        ack_freq = reg_hklm(path, "TcpAckFrequency")

        # Both must be 1 to fully disable Nagle
        if no_delay == 1 and ack_freq == 1:
            nagle_disabled += 1
        elif no_delay is None and ack_freq is None:
            # Default Windows behaviour = Nagle is ON
            dhcp = reg_hklm(path, "DhcpIPAddress") or reg_hklm(path, "IPAddress")
            if dhcp:  # only flag interfaces with an actual IP
                nagle_enabled.append(label)
        else:
            nagle_enabled.append(f"{label} (partial)")

    if nagle_enabled:
        return CheckResult(
            "Nagle's Algorithm (TCPNoDelay)",
            Status.WARNING,
            f"Enabled on: {', '.join(nagle_enabled[:2])}",
            "Set TCPNoDelay=1 and TcpAckFrequency=1 in HKLM\\SYSTEM\\...\\Tcpip\\Parameters\\Interfaces\\{guid}, "
            "or use the Leatrix Latency Fix tool to automate this.",
        )
    if nagle_disabled:
        return CheckResult(
            "Nagle's Algorithm (TCPNoDelay)",
            Status.GOOD,
            f"Disabled on {nagle_disabled} interface(s)",
        )
    return CheckResult(
        "Nagle's Algorithm (TCPNoDelay)",
        Status.UNKNOWN,
        "No active TCP interfaces found",
        "Apply Leatrix Latency Fix or manually set TCPNoDelay=1 per interface.",
    )


def run_check() -> CheckResult:
    return check_nagle_algorithm()
