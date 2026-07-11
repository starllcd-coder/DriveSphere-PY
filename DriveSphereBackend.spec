# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\LENOVO\\Desktop\\DriveSphere\\web', 'web')]
binaries = []
hiddenimports = ['dotenv', 'corsheaders', 'rest_framework', 'rest_framework_simplejwt', 'rest_framework_simplejwt.token_blacklist', 'django_redis', 'celery', 'redis', 'psycopg', 'psycopg_binary', 'twilio', 'sentry_sdk']
hiddenimports += collect_submodules('apps')
hiddenimports += collect_submodules('api')
hiddenimports += collect_submodules('config')
tmp_ret = collect_all('rest_framework')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('rest_framework_simplejwt')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('corsheaders')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('dotenv')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('twilio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\LENOVO\\Desktop\\DriveSphere\\desktop\\drivesphere_desktop\\backend_server.py'],
    pathex=['C:\\Users\\LENOVO\\Desktop\\DriveSphere\\web'],
    binaries=binaries,
    datas=datas,
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
    name='DriveSphereBackend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DriveSphereBackend',
)
