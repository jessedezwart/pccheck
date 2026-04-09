from __future__ import annotations

import ctypes
from ctypes import wintypes

from checks.base import CheckResult

from ._helpers import *

_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_OPEN_EXISTING = 3
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_IOCTL_STORAGE_QUERY_PROPERTY = 0x002D1400
_STORAGE_DEVICE_WRITE_CACHE_PROPERTY = 4
_PROPERTY_STANDARD_QUERY = 0


class _STORAGE_PROPERTY_QUERY(ctypes.Structure):
    _fields_ = [
        ("PropertyId", wintypes.DWORD),
        ("QueryType", wintypes.DWORD),
        ("AdditionalParameters", ctypes.c_byte * 1),
    ]


def _query_write_cache_state(physical_drive_index: int) -> int | None:
    """
    Returns WRITE_CACHE_ENABLE enum value:
    0=unknown, 1=disabled, 2=enabled.
    """
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE

    device_io_control = kernel32.DeviceIoControl
    device_io_control.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    device_io_control.restype = wintypes.BOOL

    close_handle = kernel32.CloseHandle

    path = f"\\\\.\\PhysicalDrive{physical_drive_index}"
    handle = create_file(
        path, 0, _FILE_SHARE_READ | _FILE_SHARE_WRITE, None, _OPEN_EXISTING, 0, None
    )
    if handle in (0, _INVALID_HANDLE_VALUE):
        return None

    try:
        query = _STORAGE_PROPERTY_QUERY(
            _STORAGE_DEVICE_WRITE_CACHE_PROPERTY, _PROPERTY_STANDARD_QUERY
        )
        out_buffer = (ctypes.c_ubyte * 64)()
        returned = wintypes.DWORD(0)

        ok = device_io_control(
            handle,
            _IOCTL_STORAGE_QUERY_PROPERTY,
            ctypes.byref(query),
            ctypes.sizeof(query),
            ctypes.byref(out_buffer),
            ctypes.sizeof(out_buffer),
            ctypes.byref(returned),
            None,
        )
        if not ok or returned.value < 16:
            return None

        raw = bytes(out_buffer[: returned.value])
        return int.from_bytes(raw[12:16], byteorder="little", signed=False)
    finally:
        close_handle(handle)


def check_write_caching() -> CheckResult:
    """Write caching buffers writes in RAM for better throughput and burst performance."""
    disks = _get_disk_info()
    if not disks:
        return CheckResult(
            "Write Caching",
            Status.INFO,
            "No disk inventory available",
            "Check Device Manager > Disk drives > Properties > Policies.",
        )

    enabled: list[str] = []
    disabled: list[str] = []
    unknown: list[str] = []

    for disk in disks:
        model = str(disk.get("Model") or "Unknown disk").strip()
        index = disk.get("Index")
        if index is None:
            unknown.append(model)
            continue

        state = _query_write_cache_state(int(index))
        if state == 2:
            enabled.append(model)
        elif state == 1:
            disabled.append(model)
        else:
            unknown.append(model)

    if disabled:
        return CheckResult(
            "Write Caching",
            Status.WARNING,
            f"Disabled on: {', '.join(disabled[:3])}",
            "Enable write caching in Device Manager > Disk > Policies for affected drives.",
        )

    if enabled and not unknown:
        return CheckResult("Write Caching", Status.GOOD, "Enabled on all detected drives")

    if enabled and unknown:
        return CheckResult(
            "Write Caching",
            Status.INFO,
            f"Enabled on {len(enabled)} drive(s), unknown on {len(unknown)}",
            "Some drives do not expose write-cache state through this API. Verify in Device Manager if needed.",
        )

    return CheckResult(
        "Write Caching",
        Status.INFO,
        "Write-cache state not exposed",
        "Check each disk in Device Manager > Properties > Policies.",
    )


IMPACT_EXPLANATION = "Likely low impact on average FPS, but write-cache policy can affect I/O burst behavior and content streaming smoothness. Source: https://learn.microsoft.com/en-us/windows/win32/fileio/file-caching"


def run_check() -> CheckResult:
    return check_write_caching()
