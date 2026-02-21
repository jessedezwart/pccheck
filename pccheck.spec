# -*- mode: python ; coding: utf-8 -*-
# Build:  uv sync --group dev ; uv run pyinstaller pccheck.spec
# Output: dist/pccheck.exe  (single file, requires admin via UAC manifest)

from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "checks.base",
        "checks.categories",
        "report",
    ] + collect_submodules("checks.categories"),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="pccheck",
    debug=False,
    strip=False,
    upx=True,
    console=True,
    uac_admin=True,   # embeds requireAdministrator in the EXE manifest
)
