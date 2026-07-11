# Desktop Release Guide (Windows)

## 1) Prerequisites

- Python 3.10+ available in PATH (or set `DRIVESPHERE_DESKTOP_PYTHON`)
- Desktop deps installed from:
  - `desktop/requirements.txt`
  - `desktop/requirements-build.txt`
- Optional installer build:
  - Inno Setup 6 installed (`ISCC.exe`)

## 2) Build Portable Release

From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\desktop\build\windows\build_release.ps1 -Version 1.0.0
```

Output:
- folder: `desktop/releases/1.0.0/DriveSphereDesktop/`
- zip: `desktop/releases/1.0.0/DriveSphereDesktop-1.0.0-win64.zip`

## 3) Build Installer (.exe)

```powershell
powershell -ExecutionPolicy Bypass -File .\desktop\build\windows\build_release.ps1 -Version 1.0.0 -BuildInstaller
```

Additional output:
- installer: `desktop/releases/1.0.0/DriveSphereDesktop-1.0.0-setup.exe`

## 4) Runtime Modes

- Native mode (default): login + native pages + backend autostart + offline cache/queue
- Wrapper mode (optional): run desktop with `--web`

## 5) Recommended Pre-Release Checks

1. Launch app on clean machine and login.
2. Confirm backend autostart and `/healthz/` reachability.
3. Disable backend and verify cached/offline behavior + queued actions.
4. Re-enable backend and verify queue sync.
5. Validate key workflows: bookings, payments, customers, vehicles.
