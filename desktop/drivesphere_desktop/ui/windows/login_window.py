from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
	QCheckBox,
	QComboBox,
	QFrame,
	QGraphicsDropShadowEffect,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMainWindow,
	QPushButton,
	QVBoxLayout,
	QWidget,
)

from drivesphere_desktop.core.api_client import ApiClient
from drivesphere_desktop.core.auth import AuthService
from drivesphere_desktop.core.settings import DEFAULT_BASE_URL, static_image_path
from drivesphere_desktop.core.state import AppState
from drivesphere_desktop.ui.dialogs import show_warning
from drivesphere_desktop.ui.windows.main_window import MainWindow


def _apply_shadow(widget: QWidget, blur: int = 30, y: int = 12) -> None:
	effect = QGraphicsDropShadowEffect(widget)
	effect.setBlurRadius(blur)
	effect.setOffset(0, y)
	effect.setColor(QColor(17, 24, 39, 36))
	widget.setGraphicsEffect(effect)


def _enable_styled_background(widget: QWidget) -> None:
	widget.setAttribute(Qt.WA_StyledBackground, True)


class LoginWindow(QMainWindow):
	def __init__(
		self,
		state: AppState | None = None,
		on_authenticated: Callable[[AppState, ApiClient], None] | None = None,
	) -> None:
		super().__init__()
		self.state = state or AppState()
		self._on_authenticated = on_authenticated
		self._main_window: MainWindow | None = None
		if not self.state.base_url:
			self.state.base_url = DEFAULT_BASE_URL
		self.api_client = ApiClient(self.state.base_url)
		self.auth = AuthService(self.api_client)
		self.setWindowTitle("DriveSphere - Login")
		self.resize(1180, 720)
		self.setMinimumSize(1100, 680)

		root = QWidget(objectName="AuthRoot")
		_enable_styled_background(root)
		self.setCentralWidget(root)

		root_layout = QVBoxLayout(root)
		root_layout.setContentsMargins(12, 12, 12, 12)
		root_layout.addStretch(1)

		panel = QFrame(objectName="AuthPanel")
		_enable_styled_background(panel)
		_apply_shadow(panel, blur=34, y=16)
		panel.setMaximumWidth(980)
		root_layout.addWidget(panel, alignment=Qt.AlignCenter)
		root_layout.addStretch(1)

		panel_layout = QVBoxLayout(panel)
		panel_layout.setContentsMargins(22, 22, 22, 22)

		glass = QFrame(objectName="AuthGlass")
		_enable_styled_background(glass)
		panel_layout.addWidget(glass)

		glass_layout = QHBoxLayout(glass)
		glass_layout.setContentsMargins(24, 24, 24, 24)
		glass_layout.setSpacing(20)

		left = QFrame(objectName="LoginHero")
		_enable_styled_background(left)
		left_layout = QVBoxLayout(left)
		left_layout.setContentsMargins(36, 42, 36, 42)
		left_layout.setSpacing(10)
		left_layout.addStretch(1)

		logo = QLabel()
		logo_path = static_image_path("logo", "logo.png")
		pixmap = QPixmap(logo_path)
		if not pixmap.isNull():
			logo.setPixmap(pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
		logo.setAlignment(Qt.AlignCenter)

		brand = QLabel("DriveSphere", objectName="AuthBrand")
		brand.setAlignment(Qt.AlignCenter)
		tagline = QLabel("Seamless Journeys, Global Reach", objectName="AuthTagline")
		tagline.setAlignment(Qt.AlignCenter)
		self.brand_label = brand
		self.tagline_label = tagline

		left_layout.addWidget(logo)
		left_layout.addWidget(brand)
		left_layout.addWidget(tagline)
		left_layout.addStretch(2)

		right = QFrame(objectName="LoginRight")
		right_layout = QVBoxLayout(right)
		right_layout.setContentsMargins(0, 0, 0, 0)
		right_layout.setSpacing(10)

		lang_row = QHBoxLayout()
		lang_row.addStretch(1)
		lang_toggle = QFrame(objectName="LangToggle")
		_enable_styled_background(lang_toggle)
		toggle_layout = QHBoxLayout(lang_toggle)
		toggle_layout.setContentsMargins(6, 4, 6, 4)
		toggle_layout.setSpacing(4)

		self.lang_en = QPushButton("EN", objectName="LangToggleButton")
		self.lang_ar = QPushButton("AR", objectName="LangToggleButton")
		self.lang_en.setProperty("active", True)
		self.lang_ar.setProperty("active", False)
		self.lang_en.clicked.connect(lambda: self._set_language("en"))
		self.lang_ar.clicked.connect(lambda: self._set_language("ar"))

		toggle_layout.addWidget(self.lang_en)
		toggle_layout.addWidget(self.lang_ar)
		lang_row.addWidget(lang_toggle)
		right_layout.addLayout(lang_row)

		card = QFrame(objectName="LoginCard")
		_enable_styled_background(card)
		_apply_shadow(card, blur=16, y=6)
		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(18, 18, 18, 18)
		card_layout.setSpacing(10)

		title = QLabel("Welcome Back!", objectName="AuthCardTitle")
		self.title_label = title
		card_layout.addWidget(title)

		form = QFrame(objectName="LoginForm")
		_enable_styled_background(form)
		form_layout = QVBoxLayout(form)
		form_layout.setContentsMargins(12, 12, 12, 12)
		form_layout.setSpacing(10)

		self.identifier_label, self.identifier = self._build_input(form_layout, "Email or Username", "U")
		self.password_label, self.password = self._build_input(form_layout, "Password", "P", is_password=True)
		self.branch_label, self.branch = self._build_select(form_layout, "Branch", "B")

		row = QHBoxLayout()
		self.remember = QCheckBox("Remember Me")
		self.forgot_btn = QPushButton("Forgot Password?")
		self.forgot_btn.setObjectName("ForgotLinkButton")
		self.forgot_btn.clicked.connect(self._open_forgot_password)
		row.addWidget(self.remember)
		row.addStretch(1)
		row.addWidget(self.forgot_btn)
		form_layout.addLayout(row)

		self.sign_in = QPushButton("Sign In", objectName="LoginSignInButton")
		self.sign_in.clicked.connect(self._handle_login)
		form_layout.addWidget(self.sign_in)

		card_layout.addWidget(form)
		right_layout.addWidget(card)
		right_layout.addStretch(1)

		glass_layout.addWidget(left, 11)
		glass_layout.addWidget(right, 9)

		self._set_language(self.state.ui_lang)
		self._load_branches()

	def _build_input(
		self,
		parent_layout: QVBoxLayout,
		label_text: str,
		icon_text: str,
		is_password: bool = False,
	) -> tuple[QLabel, QLineEdit]:
		label = QLabel(label_text, objectName="AuthLabel")
		parent_layout.addWidget(label)

		wrap = QFrame(objectName="InputWrap")
		_enable_styled_background(wrap)
		layout = QHBoxLayout(wrap)
		layout.setContentsMargins(12, 6, 12, 6)
		layout.setSpacing(8)

		icon = QLabel(icon_text)
		icon.setFixedWidth(22)
		icon.setAlignment(Qt.AlignCenter)
		layout.addWidget(icon)

		edit = QLineEdit(objectName="AuthInput")
		edit.setPlaceholderText(label_text)
		if is_password:
			edit.setEchoMode(QLineEdit.Password)
		layout.addWidget(edit, 1)

		if is_password:
			toggle = QPushButton("o", objectName="EyeButton")
			toggle.clicked.connect(lambda: self._toggle_password(edit))
			layout.addWidget(toggle)

		parent_layout.addWidget(wrap)
		return label, edit

	def _build_select(self, parent_layout: QVBoxLayout, label_text: str, icon_text: str) -> tuple[QLabel, QComboBox]:
		label = QLabel(label_text, objectName="AuthLabel")
		parent_layout.addWidget(label)

		wrap = QFrame(objectName="InputWrap")
		_enable_styled_background(wrap)
		layout = QHBoxLayout(wrap)
		layout.setContentsMargins(12, 6, 12, 6)
		layout.setSpacing(8)

		icon = QLabel(icon_text)
		icon.setFixedWidth(22)
		icon.setAlignment(Qt.AlignCenter)
		layout.addWidget(icon)

		combo = QComboBox(objectName="AuthSelect")
		layout.addWidget(combo, 1)

		parent_layout.addWidget(wrap)
		return label, combo

	def _toggle_password(self, edit: QLineEdit) -> None:
		if edit.echoMode() == QLineEdit.Password:
			edit.setEchoMode(QLineEdit.Normal)
		else:
			edit.setEchoMode(QLineEdit.Password)

	def _open_forgot_password(self) -> None:
		QDesktopServices.openUrl(QUrl(self.api_client.absolute_url("/forgot-password/")))

	def _set_language(self, lang: str) -> None:
		self.state.set_language(lang)
		self.lang_en.setProperty("active", lang == "en")
		self.lang_ar.setProperty("active", lang == "ar")
		self.lang_en.style().unpolish(self.lang_en)
		self.lang_en.style().polish(self.lang_en)
		self.lang_ar.style().unpolish(self.lang_ar)
		self.lang_ar.style().polish(self.lang_ar)
		direction = Qt.RightToLeft if self.state.is_rtl else Qt.LeftToRight
		self.setLayoutDirection(direction)
		self._apply_translations()

		try:
			if self.auth.is_authenticated:
				self.api_client.set_language(lang)
		except Exception:
			pass

	def _apply_translations(self) -> None:
		ar = self.state.is_rtl
		self.brand_label.setText("DriveSphere")
		self.tagline_label.setText("رحلات سلسة، حضور عالمي" if ar else "Seamless Journeys, Global Reach")
		self.title_label.setText("مرحبًا بعودتك!" if ar else "Welcome Back!")
		self.identifier_label.setText("البريد الإلكتروني أو اسم المستخدم" if ar else "Email or Username")
		self.password_label.setText("كلمة المرور" if ar else "Password")
		self.branch_label.setText("الفرع" if ar else "Branch")
		self.identifier.setPlaceholderText("البريد الإلكتروني أو اسم المستخدم" if ar else "Email or Username")
		self.password.setPlaceholderText("كلمة المرور" if ar else "Password")
		self.sign_in.setText("تسجيل الدخول" if ar else "Sign In")
		self.remember.setText("تذكرني" if ar else "Remember Me")
		self.forgot_btn.setText("نسيت كلمة المرور؟" if ar else "Forgot Password?")

	def _load_branches(self) -> None:
		try:
			form_data = self.api_client.fetch_login_form()
			self.branch.clear()
			self.branch.addItem("اختر الفرع" if self.state.is_rtl else "Select Branch", "")
			for value, label in form_data.branches:
				if not value:
					continue
				self.branch.addItem(label, value)
		except Exception:
			self.branch.clear()
			self.branch.addItem("اختر الفرع" if self.state.is_rtl else "Select Branch", "")

	def _handle_login(self) -> None:
		identifier = self.identifier.text().strip()
		password = self.password.text()
		branch = str(self.branch.currentData() or "")
		if not identifier or not password:
			show_warning(
				self,
				is_rtl=self.state.is_rtl,
				title_en="Login Failed",
				message_en="Enter username/email and password.",
				title_ar="فشل تسجيل الدخول",
				message_ar="أدخل اسم المستخدم/البريد الإلكتروني وكلمة المرور.",
			)
			return

		ok = self.auth.login(identifier, password, branch, self.remember.isChecked())
		if not ok:
			show_warning(
				self,
				is_rtl=self.state.is_rtl,
				title_en="Login Failed",
				message_en=self.auth.last_error or "Unable to sign in.",
				title_ar="فشل تسجيل الدخول",
				message_ar=self.auth.last_error or "تعذر تسجيل الدخول.",
			)
			return
		self.state.user_display_name = identifier
		self.state.active_branch_name = self.branch.currentText().strip()
		if self._on_authenticated is not None:
			self._on_authenticated(self.state, self.api_client)
			self.close()
			return
		self._main_window = MainWindow(self.state, self.api_client)
		self._main_window.show()
		self.close()
