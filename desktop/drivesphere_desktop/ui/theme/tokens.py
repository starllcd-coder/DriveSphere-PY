from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from drivesphere_desktop.core.settings import static_image_path


@dataclass(frozen=True)
class ThemeTokens:
	font_body: str = "Inter"
	font_display: str = "Inter"
	font_ar: str = "Cairo"
	ink: str = "#1b2b3a"
	muted: str = "#6b7b8e"
	panel: str = "rgba(255,255,255,140)"
	panel_strong: str = "rgba(255,255,255,184)"
	glass: str = "rgba(255,255,255,115)"
	stroke: str = "rgba(20,35,60,25)"
	blue_1: str = "#0d3b72"
	blue_2: str = "#2a6dd3"
	gold_1: str = "#b88b3b"
	gold_2: str = "#e7c57a"
	bg: str = "#f3f5f9"


TOKENS = ThemeTokens()


def load_stylesheet() -> str:
	candidates: list[Path] = [Path(__file__).with_name("stylesheet.qss")]

	# In frozen builds, PyInstaller extracts files under _MEIPASS.
	meipass = getattr(sys, "_MEIPASS", None)
	if meipass:
		base = Path(meipass)
		candidates.extend(
			[
				base / "drivesphere_desktop" / "ui" / "theme" / "stylesheet.qss",
				base / "_internal" / "drivesphere_desktop" / "ui" / "theme" / "stylesheet.qss",
			]
		)

	qss_path = next((p for p in candidates if p.exists()), None)
	if qss_path is None:
		raise FileNotFoundError(
			"stylesheet.qss was not found. Checked: "
			+ ", ".join(str(p) for p in candidates)
		)

	qss = qss_path.read_text(encoding="utf-8")
	replacements = {
		"FONT_BODY": TOKENS.font_body,
		"FONT_DISPLAY": TOKENS.font_display,
		"FONT_AR": TOKENS.font_ar,
		"INK": TOKENS.ink,
		"MUTED": TOKENS.muted,
		"PANEL": TOKENS.panel,
		"PANEL_STRONG": TOKENS.panel_strong,
		"GLASS": TOKENS.glass,
		"STROKE": TOKENS.stroke,
		"BLUE_1": TOKENS.blue_1,
		"BLUE_2": TOKENS.blue_2,
		"GOLD_1": TOKENS.gold_1,
		"GOLD_2": TOKENS.gold_2,
		"BG": TOKENS.bg,
		"WAVES_LIGHT": static_image_path("backgrounds", "waves_light.png"),
	}
	for key, value in replacements.items():
		qss = qss.replace(f"@{key}@", value)
	return qss
