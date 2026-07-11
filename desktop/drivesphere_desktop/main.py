import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QLockFile, QStandardPaths
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from drivesphere_desktop.core.backend_runtime import BackendRuntime
from drivesphere_desktop.core.settings import DEFAULT_BASE_URL, desktop_image_path
from drivesphere_desktop.ui.theme.font_loader import load_bundled_fonts
from drivesphere_desktop.ui.theme.tokens import load_stylesheet
from drivesphere_desktop.ui.dialogs import ask_confirm, show_info
from drivesphere_desktop.ui.windows.web_app_window import WebAppWindow


def _create_lock() -> QLockFile:
	lock_dir = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
	if not lock_dir:
		lock_dir = os.getcwd()
	lock_path = str(Path(lock_dir) / "drivesphere_desktop.lock")
	lock = QLockFile(lock_path)
	lock.setStaleLockTime(0)
	return lock


def _startup_path(argv: list[str]) -> str:
	if len(argv) < 2:
		return "/login/"
	arg = argv[1].strip()
	if not arg:
		return "/login/"
	if arg.startswith("http://") or arg.startswith("https://"):
		parsed = urlparse(arg)
		return parsed.path or "/login/"
	return arg if arg.startswith("/") else f"/{arg}"


def main() -> None:
	app = QApplication(sys.argv)
	app.setApplicationName("DriveSphere")
	app.setQuitOnLastWindowClosed(False)
	app_icon = QIcon(desktop_image_path("logo.ico"))
	if not app_icon.isNull():
		app.setWindowIcon(app_icon)

	lock = _create_lock()
	loaded_fonts = load_bundled_fonts()
	app.setFont(QFont("Inter" if loaded_fonts.get("Inter") else "Segoe UI", 10))
	app.setStyleSheet(load_stylesheet())

	if not lock.tryLock(100):
		show_info(
			None,
			is_rtl=False,
			title_en="DriveSphere",
			message_en="DriveSphere desktop is already running.\n\nتطبيق DriveSphere لسطح المكتب يعمل بالفعل.",
			title_ar="درايف سفير",
			message_ar="تطبيق DriveSphere لسطح المكتب يعمل بالفعل.\n\nDriveSphere desktop is already running.",
		)
		return

	backend = BackendRuntime(DEFAULT_BASE_URL)
	ok, message = backend.start()
	if not ok:
		result = ask_confirm(
			None,
			is_rtl=False,
			title_en="DriveSphere Backend",
			message_en=f"{message}\n\nContinue in offline-only mode?\n\nهل تريد المتابعة في وضع عدم الاتصال فقط؟",
			title_ar="خلفية DriveSphere",
			message_ar=f"{message}\n\nهل تريد المتابعة في وضع عدم الاتصال فقط؟\n\nContinue in offline-only mode?",
			danger=False,
		)
		if not result:
			lock.unlock()
			return

	try:
		window = WebAppWindow(backend.base_url or DEFAULT_BASE_URL, _startup_path(sys.argv))
		window.show()
		app.exec()
	finally:
		backend.stop()
		lock.unlock()


if __name__ == "__main__":
	main()
