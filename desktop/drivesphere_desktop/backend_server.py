from __future__ import annotations

import os
import sys
from pathlib import Path


def _resolve_web_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        candidate = meipass / "web"
        if candidate.exists():
            return candidate
        adjacent = Path(sys.executable).resolve().parent / "web"
        if adjacent.exists():
            return adjacent
        return meipass

    return Path(__file__).resolve().parents[2] / "web"


def main() -> None:
    web_dir = _resolve_web_dir()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.desktop")
    os.environ.setdefault("DRIVESPHERE_BASE_DIR", str(web_dir))

    sys.path.insert(0, str(web_dir))
    os.chdir(str(web_dir))

    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", *sys.argv[1:]])


if __name__ == "__main__":
    main()
