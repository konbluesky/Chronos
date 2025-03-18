# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtSvg', 'PyQt6.QtSvgWidgets', 'crontab']
hiddenimports += collect_submodules('PyQt6')
hiddenimports += collect_submodules('crontab')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.icns', '.'), ('icon.png', '.'), ('icon.svg', '.'), ('Info.plist', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Chronos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity='',
    entitlements_file='',
    version='v5.6.20250208.ed5bff5',
    icon=['icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Chronos',
)
app = BUNDLE(
    coll,
    name='Chronos.app',
    icon='icon.icns',
    bundle_identifier='com.konbluesky.chronos',
)
