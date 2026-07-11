from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFontDatabase


EXPECTED_FONTS = {
    "Inter": [
        "Inter-Regular.ttf",
        "Inter-Medium.ttf",
        "Inter-SemiBold.ttf",
        "Inter-Bold.ttf",
    ],
    "Cairo": [
        "Cairo-Regular.ttf",
        "Cairo-Medium.ttf",
        "Cairo-SemiBold.ttf",
        "Cairo-Bold.ttf",
    ],
}


def load_bundled_fonts() -> dict[str, bool]:
    fonts_dir = Path(__file__).resolve().parents[2] / "resources" / "fonts"
    loaded = {"Inter": False, "Cairo": False}
    for family, files in EXPECTED_FONTS.items():
        family_ok = False
        for name in files:
            path = fonts_dir / name
            if path.exists() and QFontDatabase.addApplicationFont(path.as_posix()) >= 0:
                family_ok = True
        loaded[family] = family_ok
    return loaded
