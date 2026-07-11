from __future__ import annotations

import os
import re

import requests
from PySide6.QtCore import QSettings, Qt, QUrl, QStandardPaths
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from drivesphere_desktop.core.settings import (
    BASE_DIR,
    DEFAULT_BASE_URL,
    desktop_image_path,
    static_image_path,
)


class _DesktopWebPage(QWebEnginePage):
    """Route popup/new-tab and JS dialogs through desktop-native handlers."""

    def __init__(self, owner: "WebAppWindow", parent=None):
        super().__init__(parent)
        self._owner = owner

    def createWindow(self, _window_type):  # noqa: N802 (Qt override name)
        popup_page = QWebEnginePage(self.profile(), self)
        popup_page.urlChanged.connect(self._owner._open_popup_url)
        return popup_page

    def javaScriptAlert(self, _security_origin, msg):  # noqa: N802
        self._owner._show_js_alert(msg)

    def javaScriptConfirm(self, _security_origin, msg):  # noqa: N802
        return self._owner._show_js_confirm(msg)

    def javaScriptPrompt(self, _security_origin, msg, default_value):  # noqa: N802
        return self._owner._show_js_prompt(msg, default_value)


class WebAppWindow(QMainWindow):
    def __init__(self, base_url: str | None = None, start_path: str = "/login/") -> None:
        super().__init__()
        self._settings = QSettings("DriveSphere", "DriveSphereDesktop")
        explicit_base = (base_url or "").strip().rstrip("/")
        if explicit_base:
            self.base_url = explicit_base
            self._settings.setValue("base_url", self.base_url)
        else:
            self.base_url = (
                self._settings.value("base_url", DEFAULT_BASE_URL, str) or DEFAULT_BASE_URL
            ).rstrip("/")
        self.start_path = start_path if start_path.startswith("/") else f"/{start_path}"
        self._allow_close = False
        self._tray_notice_shown = False
        self.setWindowTitle("DriveSphere Desktop")
        window_icon = QIcon(desktop_image_path("logo.ico"))
        if not window_icon.isNull():
            self.setWindowIcon(window_icon)
        self.resize(1440, 900)

        root = QWidget()
        root.setObjectName("MainRoot")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.top_chrome = QWidget()
        self.top_chrome.setLayout(top)
        self.back_btn = QPushButton("Back")
        self.forward_btn = QPushButton("Forward")
        self.reload_btn = QPushButton("Reload")
        self.home_btn = QPushButton("Home")
        self.go_btn = QPushButton("Go")
        self.url_edit = QLineEdit()
        self.base_url_edit = QLineEdit(self.base_url)
        self.base_url_edit.setPlaceholderText("http://127.0.0.1:8000")
        top.addWidget(self.back_btn)
        top.addWidget(self.forward_btn)
        top.addWidget(self.reload_btn)
        top.addWidget(self.home_btn)
        top.addWidget(QLabel("Server:"))
        top.addWidget(self.base_url_edit)
        top.addWidget(self.go_btn)
        top.addWidget(QLabel("URL:"))
        top.addWidget(self.url_edit, 1)
        layout.addWidget(self.top_chrome)
        self.top_chrome.setVisible(False)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
        except Exception as exc:
            self._show_modal_dialog(
                "Qt WebEngine Missing",
                f"Qt WebEngine is required for exact web parity mode.\n{exc}\n\nمكتبة Qt WebEngine مطلوبة لتشغيل وضع المطابقة الكاملة.",
                confirm_label="OK",
                confirm_object_name="DsBtnDanger",
                width=620,
            )
            raise

        self.web = QWebEngineView()
        self.web.setPage(_DesktopWebPage(self, self.web))
        self.stack.addWidget(self.web)

        self.offline_page = self._build_offline_page()
        self.stack.addWidget(self.offline_page)

        self._setup_tray()

        self.back_btn.clicked.connect(self.web.back)
        self.forward_btn.clicked.connect(self.web.forward)
        self.reload_btn.clicked.connect(self.web.reload)
        self.home_btn.clicked.connect(lambda: self.navigate("/dashboard/"))
        self.go_btn.clicked.connect(self._apply_server_url)
        self.base_url_edit.returnPressed.connect(self._apply_server_url)
        self.url_edit.returnPressed.connect(self._navigate_url_bar)
        self.web.urlChanged.connect(self._on_url_changed)
        self.web.loadFinished.connect(self._on_load_finished)
        self.web.titleChanged.connect(self.setWindowTitle)
        self.web.page().printRequested.connect(self._on_print_requested)
        self.web.page().profile().downloadRequested.connect(self._on_download_requested)

        self.navigate(self.start_path)

    def _open_popup_url(self, url: QUrl) -> None:
        if not url.isValid():
            return
        self.web.setUrl(url)

    def _is_arabic_text(self, text: str) -> bool:
        if not text:
            return False
        return re.search(r"[\u0600-\u06FF]", text) is not None

    def _show_modal_dialog(
        self,
        title: str,
        message: str,
        *,
        confirm_label: str = "OK",
        cancel_label: str | None = None,
        confirm_object_name: str = "DsBtnPrimary",
        width: int = 520,
    ) -> bool:
        is_ar = self._is_arabic_text(f"{title} {message}")
        dialog = QDialog(self)
        dialog.setObjectName("DsDialog")
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.resize(width, 180 if cancel_label else 160)
        dialog.setLayoutDirection(Qt.RightToLeft if is_ar else Qt.LeftToRight)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("DsDialogTitle")
        title_lbl.setAlignment(Qt.AlignRight if is_ar else Qt.AlignLeft)

        body = QLabel(message or "")
        body.setObjectName("DsDialogBody")
        body.setWordWrap(True)
        body.setAlignment((Qt.AlignTop | Qt.AlignRight) if is_ar else (Qt.AlignTop | Qt.AlignLeft))

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addStretch(1)

        cancel_btn = None
        if cancel_label:
            cancel_btn = QPushButton(cancel_label)
            cancel_btn.setObjectName("DsBtnGhost")
            cancel_btn.clicked.connect(dialog.reject)
            actions.addWidget(cancel_btn)

        confirm_btn = QPushButton(confirm_label)
        confirm_btn.setObjectName(confirm_object_name)
        confirm_btn.clicked.connect(dialog.accept)
        actions.addWidget(confirm_btn)

        root.addWidget(title_lbl)
        root.addWidget(body)
        root.addStretch(1)
        root.addLayout(actions)

        confirm_btn.setDefault(True)
        if cancel_btn:
            cancel_btn.setAutoDefault(False)
        return dialog.exec() == QDialog.Accepted

    def _resolve_page_lang(self, callback) -> None:
        script = """
        (function () {
          var html = document.documentElement || {};
          var body = document.body || {};
          var lang = String((html.getAttribute && html.getAttribute('lang')) || '').toLowerCase();
          var dir = String((html.getAttribute && html.getAttribute('dir')) || body.dir || '').toLowerCase();
          var arBtn = document.getElementById('ds-lang-ar');
          var arActive = !!(arBtn && arBtn.classList && arBtn.classList.contains('is-active'));
          return (lang.indexOf('ar') === 0 || dir === 'rtl' || arActive) ? 'ar' : 'en';
        })();
        """
        try:
            self.web.page().runJavaScript(
                script,
                lambda value: callback("ar" if str(value or "").startswith("ar") else "en"),
            )
        except Exception:
            callback("en")

    def _show_js_alert(self, message: str) -> None:
        is_ar = self._is_arabic_text(message or "")
        self._show_modal_dialog(
            "تنبيه" if is_ar else "Notification",
            message or ("تمت العملية بنجاح." if is_ar else "Action completed."),
            confirm_label="حسناً" if is_ar else "OK",
            confirm_object_name="DsBtnPrimary",
            width=470,
        )

    def _show_js_confirm(self, message: str) -> bool:
        is_ar = self._is_arabic_text(message or "")
        return self._show_modal_dialog(
            "تأكيد الإجراء" if is_ar else "Confirm Action",
            message or ("هل أنت متأكد أنك تريد المتابعة؟" if is_ar else "Are you sure you want to continue?"),
            confirm_label="تأكيد" if is_ar else "Confirm",
            cancel_label="إلغاء" if is_ar else "Cancel",
            confirm_object_name="DsBtnDanger",
            width=560,
        )

    def _show_js_prompt(self, message: str, default_value: str):
        is_ar = self._is_arabic_text(message or "")
        dialog = QDialog(self)
        dialog.setObjectName("DsDialog")
        dialog.setWindowTitle("إدخال مطلوب" if is_ar else "Input Required")
        dialog.setModal(True)
        dialog.resize(620, 210)
        dialog.setLayoutDirection(Qt.RightToLeft if is_ar else Qt.LeftToRight)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        title_lbl = QLabel("الرجاء التأكيد" if is_ar else "Please Confirm")
        title_lbl.setObjectName("DsDialogTitle")
        title_lbl.setAlignment(Qt.AlignRight if is_ar else Qt.AlignLeft)

        body = QLabel(message or "")
        body.setObjectName("DsDialogBody")
        body.setWordWrap(True)
        body.setAlignment((Qt.AlignTop | Qt.AlignRight) if is_ar else (Qt.AlignTop | Qt.AlignLeft))

        input_box = QLineEdit(default_value or "")
        input_box.setObjectName("DsInput")
        input_box.setLayoutDirection(Qt.RightToLeft if is_ar else Qt.LeftToRight)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addStretch(1)

        cancel = QPushButton("إلغاء" if is_ar else "Cancel")
        cancel.setObjectName("DsBtnGhost")
        cancel.clicked.connect(dialog.reject)
        actions.addWidget(cancel)

        confirm = QPushButton("تأكيد" if is_ar else "Confirm")
        confirm.setObjectName("DsBtnPrimary")
        confirm.clicked.connect(dialog.accept)
        actions.addWidget(confirm)

        root.addWidget(title_lbl)
        root.addWidget(body)
        root.addWidget(input_box)
        root.addLayout(actions)

        confirm.setDefault(True)
        cancel.setAutoDefault(False)
        ok = dialog.exec() == QDialog.Accepted
        return (ok, input_box.text() if ok else "")

    def _build_offline_page(self) -> QWidget:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(48, 48, 48, 48)

        card = QFrame()
        card.setObjectName("AuthCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)

        title = QLabel("Cannot Reach DriveSphere Server")
        title.setStyleSheet("font-size: 26px; font-weight: 800;")
        subtitle = QLabel("Start the web backend and click Retry, or change server URL.")

        form = QHBoxLayout()
        self.offline_url_edit = QLineEdit(self.base_url)
        retry_btn = QPushButton("Retry")
        retry_btn.setObjectName("PrimaryButton")
        form.addWidget(self.offline_url_edit, 1)
        form.addWidget(retry_btn)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addLayout(form)

        box.addStretch(1)
        box.addWidget(card)
        box.addStretch(1)

        retry_btn.clicked.connect(self._retry_from_offline)
        self.offline_url_edit.returnPressed.connect(self._retry_from_offline)
        return page

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = None
            return

        icon = QIcon(desktop_image_path("logo.ico"))
        if icon.isNull():
            icon = QIcon(static_image_path("logo", "logo.png"))
        if icon.isNull():
            ico_path = BASE_DIR / "web" / "static" / "img" / "logo" / "logo.ico"
            icon = QIcon(str(ico_path))

        self.tray = QSystemTrayIcon(icon, self)
        from PySide6.QtWidgets import QMenu

        tray_menu = QMenu()
        show_action = QAction("Show", self)
        reload_action = QAction("Reload", self)
        quit_action = QAction("Quit", self)
        show_action.triggered.connect(self._restore_from_tray)
        reload_action.triggered.connect(self.web.reload)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(show_action)
        tray_menu.addAction(reload_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        self.showNormal()
        self.activateWindow()

    def _quit_app(self) -> None:
        self._allow_close = True
        if self.tray is not None:
            self.tray.hide()
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close or self.tray is None:
            event.accept()
            app = QApplication.instance()
            if app is not None:
                app.quit()
            return

        self.hide()
        event.ignore()
        if not self._tray_notice_shown:
            self.tray.showMessage(
                "DriveSphere",
                "App is still running in the system tray.",
                QSystemTrayIcon.Information,
                2500,
            )
            self._tray_notice_shown = True

    def _server_ok(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/login/", timeout=6)
            return response.status_code < 500
        except Exception:
            return False

    def _set_server_url(self, url: str) -> None:
        cleaned = (url or "").strip().rstrip("/")
        if not cleaned:
            return
        self.base_url = cleaned
        self._settings.setValue("base_url", self.base_url)
        self.base_url_edit.setText(self.base_url)
        self.offline_url_edit.setText(self.base_url)

    def _apply_server_url(self) -> None:
        self._set_server_url(self.base_url_edit.text())
        self.navigate("/login/")

    def _retry_from_offline(self) -> None:
        self._set_server_url(self.offline_url_edit.text())
        self.navigate("/login/")

    def navigate(self, path: str) -> None:
        if not self._server_ok():
            self.stack.setCurrentWidget(self.offline_page)
            return
        self.stack.setCurrentWidget(self.web)
        full = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        self.web.setUrl(QUrl(full))

    def _navigate_url_bar(self) -> None:
        target = self.url_edit.text().strip()
        if not target:
            return
        if target.startswith("http://") or target.startswith("https://"):
            self.web.setUrl(QUrl(target))
        else:
            self.navigate(target)

    def _on_url_changed(self, url: QUrl) -> None:
        self.url_edit.setText(url.toString())

    def _on_print_requested(self) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return

        def _after_print(ok: bool) -> None:
            if not ok:
                self._show_modal_dialog(
                    "Print",
                    "Failed to print this document.\n\nتعذرت طباعة هذا المستند.",
                    confirm_label="OK",
                    confirm_object_name="DsBtnDanger",
                    width=520,
                )

        self.web.page().print(printer, _after_print)

    def _on_download_requested(self, request) -> None:
        try:
            download_dir = (
                QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
                or os.getcwd()
            )
            filename = request.downloadFileName() or "document.pdf"

            if hasattr(request, "setDownloadDirectory"):
                request.setDownloadDirectory(download_dir)
            if hasattr(request, "setDownloadFileName"):
                request.setDownloadFileName(filename)
            if hasattr(request, "stateChanged"):
                request.stateChanged.connect(lambda _state: None)

            request.accept()
            full_path = os.path.normpath(os.path.join(download_dir, filename))

            def _show_for_lang(lang: str) -> None:
                is_ar = lang == "ar"
                self._show_modal_dialog(
                    "بدء التنزيل" if is_ar else "Download Started",
                    f"جارٍ حفظ الملف في:\n{full_path}" if is_ar else f"Saving file to:\n{full_path}",
                    confirm_label="حسناً" if is_ar else "OK",
                    confirm_object_name="DsBtnPrimary",
                    width=560,
                )

            self._resolve_page_lang(_show_for_lang)
        except Exception as exc:
            def _show_err_for_lang(lang: str) -> None:
                is_ar = lang == "ar"
                self._show_modal_dialog(
                    "تنزيل" if is_ar else "Download",
                    f"تعذر بدء التنزيل.\n{exc}" if is_ar else f"Failed to start download.\n{exc}",
                    confirm_label="حسناً" if is_ar else "OK",
                    confirm_object_name="DsBtnDanger",
                    width=560,
                )

            self._resolve_page_lang(_show_err_for_lang)

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            self.stack.setCurrentWidget(self.offline_page)
            return
        self._inject_desktop_css()

    def _inject_desktop_css(self) -> None:
        css = """
        :root {
            --ds-scrollbar-track: rgba(15, 23, 42, 0.06);
            --ds-scrollbar-thumb: rgba(15, 23, 42, 0.35);
            --ds-scrollbar-thumb-hover: rgba(15, 23, 42, 0.55);
        }

        .ds-kpi__trend {
            top: 12px;
            bottom: auto;
        }
        [dir="rtl"] .ds-kpi__trend, .is-rtl .ds-kpi__trend {
            left: 14px;
            right: auto;
        }

        * {
            scrollbar-width: thin;
            scrollbar-color: var(--ds-scrollbar-thumb) var(--ds-scrollbar-track);
        }

        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: var(--ds-scrollbar-track);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--ds-scrollbar-thumb);
            border-radius: 10px;
            border: 2px solid transparent;
            background-clip: padding-box;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--ds-scrollbar-thumb-hover);
        }
        """
        script = (
            "(function(){"
            "var style=document.getElementById('ds-scrollbar-style');"
            "if(!style){style=document.createElement('style');style.id='ds-scrollbar-style';document.head.appendChild(style);}"
            "style.textContent=" + repr(css) + ";"
            "})();"
        )
        self.web.page().runJavaScript(script)
