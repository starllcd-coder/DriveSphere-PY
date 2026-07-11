from pathlib import Path
import os
import sys


BASE_DIR = Path(__file__).resolve().parents[3]
WEB_STATIC_DIR = BASE_DIR / "web" / "static"
WEB_IMG_DIR = WEB_STATIC_DIR / "img"
DESKTOP_ASSETS_IMG_DIR = BASE_DIR / "desktop" / "drivesphere_desktop" / "assets" / "images"
DEFAULT_BASE_URL = os.getenv("DRIVESPHERE_BASE_URL", "http://127.0.0.1:8000")


def static_image_path(*parts: str) -> str:
	path = WEB_IMG_DIR.joinpath(*parts)
	return path.as_posix()


def desktop_image_path(*parts: str) -> str:
	if getattr(sys, "frozen", False):
		exe_dir = Path(sys.executable).resolve().parent
		candidates = [
			exe_dir / "_internal" / "drivesphere_desktop" / "assets" / "images",
			exe_dir / "assets" / "images",
		]
		for base in candidates:
			path = base.joinpath(*parts)
			if path.exists():
				return path.as_posix()
	path = DESKTOP_ASSETS_IMG_DIR.joinpath(*parts)
	return path.as_posix()
