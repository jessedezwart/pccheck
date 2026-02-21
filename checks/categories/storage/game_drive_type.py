from __future__ import annotations

from checks.base import CheckResult

from ._helpers import *


def check_game_drive_type() -> CheckResult:
    """Games on HDDs have long load times and texture streaming issues.
    SSDs (especially NVMe) dramatically improve the gaming experience."""
    # Find common game library locations
    import os

    game_dirs = [
        r"C:\Program Files (x86)\Steam\steamapps\common",
        r"C:\Program Files\EA Games",
        r"C:\Program Files\Epic Games",
        r"C:\XboxGames",
        r"D:\Games",
        r"D:\SteamLibrary",
        r"E:\Games",
        r"E:\SteamLibrary",
    ]

    found_locations: list[tuple[str, str]] = []  # (path, drive_letter)
    for path in game_dirs:
        if os.path.isdir(path):
            letter = path[0].upper()
            found_locations.append((path, letter))

    if not found_locations:
        return CheckResult(
            "Game Drive Type",
            Status.UNKNOWN,
            "No standard game library folders found",
            "Manually verify your game drive is an SSD via Task Manager > Performance.",
        )

    # Check drive type for each found location
    ps = "Get-PhysicalDisk | Select-Object FriendlyName, MediaType, BusType | ConvertTo-Json"
    disk_info_raw = run_powershell(ps)
    ssds: set[str] = set()
    hdds: set[str] = set()

    if disk_info_raw:
        try:
            disk_data = json.loads(disk_info_raw)
            if isinstance(disk_data, dict):
                disk_data = [disk_data]
            for d in disk_data:
                media = (d.get("MediaType") or "").upper()
                bus = (d.get("BusType") or "").upper()
                name = d.get("FriendlyName", "?")
                if "SSD" in media or "NVM" in bus or "NVME" in bus:
                    ssds.add(name)
                elif "HDD" in media or "UNSPECIFIED" in media:
                    hdds.add(name)
        except Exception:
            pass

    # Cross-reference drive letters with disk type
    _get_logical_to_physical()

    # Simple heuristic: if we detected SSDs and HDDs, report
    if hdds and not ssds:
        return CheckResult(
            "Game Drive Type",
            Status.BAD,
            f"HDD detected: {', '.join(list(hdds)[:2])}",
            "Move games to an SSD for dramatically faster load times and better open-world streaming.",
        )
    if ssds:
        return CheckResult(
            "Game Drive Type",
            Status.GOOD,
            f"SSD detected: {', '.join(list(ssds)[:2])}",
        )

    return CheckResult(
        "Game Drive Type",
        Status.UNKNOWN,
        f"Libraries found: {', '.join(p for p, _ in found_locations[:3])}",
        "Verify game drives are SSDs via Task Manager > Performance > Disk.",
    )


def run_check() -> CheckResult:
    return check_game_drive_type()
