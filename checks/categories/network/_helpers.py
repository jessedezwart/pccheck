"""
Network checks:
  - NIC interrupt moderation (adds latency to batch interrupts)
  - Receive Side Scaling (RSS) — multi-core packet processing
  - Nagle's algorithm / TCPNoDelay (causes 40-200 ms added latency in games)
  - NIC power saving mode
  - DNS response time

To remove a check, delete or comment out its entry in get_checks().
"""

from __future__ import annotations

import winreg

from checks.base import (
    NIC_CLASS_GUID,
    CheckResult,
    Status,
    find_adapter_subkeys,
    ps_json,
    reg_hklm,
    run_cmd,
    run_powershell,
)

_TCPIP_INTERFACES = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"

_VIRTUAL_KEYWORDS = frozenset(
    [
        "virtual",
        "vpn",
        "bluetooth",
        "tunnel",
        "loopback",
        "wan miniport",
        "microsoft wi-fi direct",
        "tap-",
        "multiplexor",
        "isatap",
        "teredo",
        "npcap",
        "kernel debug network adapter",
        "ras async adapter",
        "remote ndis based internet sharing device",
    ]
)

_NIC_LABEL_BY_GUID: dict[str, str] | None = None


def _is_virtual(name: str) -> bool:
    low = name.lower()
    return any(kw in low for kw in _VIRTUAL_KEYWORDS)


def _physical_nics() -> list[tuple[str, str]]:
    """Return (desc, registry_path) for physical NIC adapters only."""
    return [
        (desc, path) for desc, path in find_adapter_subkeys(NIC_CLASS_GUID) if not _is_virtual(desc)
    ]


def _normalize_guid(value: str) -> str:
    return value.strip().strip("{}").lower()


def _nic_labels_by_guid() -> dict[str, str]:
    global _NIC_LABEL_BY_GUID
    if _NIC_LABEL_BY_GUID is not None:
        return _NIC_LABEL_BY_GUID

    mapping: dict[str, str] = {}
    rows = ps_json(
        "Get-NetAdapter -IncludeHidden -ErrorAction SilentlyContinue "
        "| Select-Object InterfaceGuid,Name,InterfaceDescription"
    )

    if isinstance(rows, dict):
        rows = [rows]
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            guid = row.get("InterfaceGuid")
            name = str(row.get("Name") or "").strip()
            desc = str(row.get("InterfaceDescription") or "").strip()
            if not isinstance(guid, str) or not guid.strip():
                continue
            key = _normalize_guid(guid)
            if desc and name and desc.lower() != name.lower():
                mapping[key] = f"{name} ({desc})"
            else:
                mapping[key] = name or desc

    _NIC_LABEL_BY_GUID = mapping
    return mapping


def _nic_name_by_guid(interface_guid: str) -> str | None:
    """Return NIC display name for a TCP/IP interface GUID, if known."""
    target = _normalize_guid(interface_guid)

    # Prefer live adapter mapping for reliable interface names.
    label = _nic_labels_by_guid().get(target)
    if label:
        return label

    # Registry fallback.
    for desc, path in find_adapter_subkeys(NIC_CLASS_GUID):
        cfg_id = reg_hklm(path, "NetCfgInstanceId")
        if not isinstance(cfg_id, str):
            continue
        if _normalize_guid(cfg_id) == target:
            return desc
    return None


def _get_tcpip_interface_guids() -> list[str]:
    """Return interface GUIDs under TCPIP Interfaces key."""
    guids: list[str] = []
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            _TCPIP_INTERFACES,
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        )
        i = 0
        while True:
            try:
                guids.append(winreg.EnumKey(key, i))
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except OSError:
        pass
    return guids


__all__ = [
    "annotations",
    "winreg",
    "CheckResult",
    "Status",
    "reg_hklm",
    "ps_json",
    "run_cmd",
    "run_powershell",
    "find_adapter_subkeys",
    "NIC_CLASS_GUID",
    "_TCPIP_INTERFACES",
    "_VIRTUAL_KEYWORDS",
    "_is_virtual",
    "_physical_nics",
    "_nic_name_by_guid",
    "_get_tcpip_interface_guids",
]
