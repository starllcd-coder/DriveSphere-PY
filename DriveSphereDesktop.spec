# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('C:\\Users\\LENOVO\\Desktop\\DriveSphere\\desktop\\drivesphere_desktop\\ui\\theme\\stylesheet.qss', 'drivesphere_desktop\\ui\\theme'), ('C:\\Users\\LENOVO\\Desktop\\DriveSphere\\web\\static\\img', 'web\\static\\img')]
datas += collect_data_files('drivesphere_desktop')


a = Analysis(
    ['C:\\Users\\LENOVO\\Desktop\\DriveSphere\\desktop\\drivesphere_desktop\\main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    name='DriveSphereDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\LENOVO\\Desktop\\DriveSphere\\desktop\\drivesphere_desktop\\assets\\images\\logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DriveSphereDesktop',
)
