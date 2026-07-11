# DriveSphere Desktop (PySide6)

## Quick Start

1. Install dependencies:
	- pip install -r requirements.txt
2. Run desktop app:
	- python -m drivesphere_desktop.main

## Runtime Mode

Desktop now runs in embedded **web parity mode only** using Qt WebEngine.

It opens:

- `/login/`

This guarantees the same UI, routes, and behavior as the web app because it renders the exact web frontend inside a desktop window.

## Installer Packaging

Windows build now packages:

- `DriveSphereDesktop` (UI shell)
- `DriveSphereBackend` (dedicated local Django backend executable)

This means desktop can start its own backend without requiring the user to manually install Python on the target machine.

## Backend URL

- Default: http://127.0.0.1:8000
- Override with environment variable:
  - DRIVESPHERE_BASE_URL=http://your-host:8000

Useful env overrides:
- `DRIVESPHERE_AUTOSTART_BACKEND=0` to disable auto-start
- `DRIVESPHERE_BACKEND_PYTHON=<full-path-to-python.exe>` to force backend interpreter
- `DRIVESPHERE_DESKTOP_DATA_DIR=<path>` to override dedicated desktop backend data directory

## Desktop Backend Isolation

Parity desktop uses a dedicated backend profile:

- Django settings module: `config.settings.desktop`
- Dedicated local database/media (default):
  - `%LOCALAPPDATA%\DriveSphereDesktop\data\desktop.sqlite3`
  - `%LOCALAPPDATA%\DriveSphereDesktop\data\media\`

This keeps desktop parity backend data separate from standard web runtime data.

## Build & Packaging

Windows build script:
- `desktop/build/windows/build_release.ps1`

Example:
- `powershell -ExecutionPolicy Bypass -File .\desktop\build\windows\build_release.ps1 -Version 1.0.0`

Optional installer (Inno Setup):
- `powershell -ExecutionPolicy Bypass -File .\desktop\build\windows\build_release.ps1 -Version 1.0.0 -BuildInstaller`

Full checklist:
- `desktop/RELEASE.md`

## Font Bundles

For close pixel parity with web typography, place Inter and Cairo font files in:

- drivesphere_desktop/resources/fonts/

See drivesphere_desktop/resources/fonts/README.md for expected file names.
