from __future__ import annotations

from datetime import datetime
from typing import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QDialog,
	QDialogButtonBox,
	QLineEdit,
	QListWidget,
	QListWidgetItem,
	QLabel,
	QMainWindow,
	QPushButton,
	QScrollArea,
	QStackedWidget,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)

from drivesphere_desktop.core.api_client import ApiClient
from drivesphere_desktop.core.state import AppState
from drivesphere_desktop.ui.pages.bookings_page import BookingsPage
from drivesphere_desktop.ui.pages.customers_page import CustomersPage
from drivesphere_desktop.ui.pages.dashboard_page import DashboardPage
from drivesphere_desktop.ui.pages.maintenance_page import MaintenancePage
from drivesphere_desktop.ui.pages.payments_page import PaymentsPage
from drivesphere_desktop.ui.pages.reports_page import ReportsPage
from drivesphere_desktop.ui.pages.settings_page import SettingsPage
from drivesphere_desktop.ui.pages.vehicles_page import VehiclesPage
from drivesphere_desktop.ui.dialogs import show_warning


class MainWindow(QMainWindow):
	def __init__(
		self,
		state: AppState | None = None,
		api_client: ApiClient | None = None,
		on_logout: Callable[[], None] | None = None,
	) -> None:
		super().__init__()
		self.state = state or AppState()
		self.api_client = api_client or ApiClient(self.state.base_url)
		self._on_logout = on_logout
		self.setWindowTitle("DriveSphere")
		self.resize(1280, 800)

		root = QWidget(objectName="MainRoot")
		root.setAttribute(Qt.WA_StyledBackground, True)
		self.setCentralWidget(root)
		shell = QHBoxLayout(root)
		shell.setContentsMargins(16, 16, 16, 16)
		shell.setSpacing(16)

		sidebar = QFrame(objectName="AuthPanel")
		sidebar.setFixedWidth(280)
		side_layout = QVBoxLayout(sidebar)
		side_layout.setContentsMargins(14, 16, 14, 16)
		side_layout.setSpacing(10)

		brand = QLabel("DriveSphere")
		brand.setObjectName("AuthBrand")
		brand.setStyleSheet("font-size: 28px;")
		side_layout.addWidget(brand)

		nav_container = QWidget()
		nav_layout = QVBoxLayout(nav_container)
		nav_layout.setContentsMargins(0, 0, 0, 0)
		nav_layout.setSpacing(8)

		self.nav_buttons: dict[str, QPushButton] = {}
		for key, label in [
			("dashboard", "Dashboard"),
			("bookings", "Bookings"),
			("customers", "Customers"),
			("fleet", "Fleet"),
			("payments", "Payments"),
			("maintenance", "Maintenance"),
			("reports", "Reports"),
			("settings", "Settings"),
		]:
			btn = QPushButton(label)
			btn.setObjectName("LangToggleButton")
			btn.setCheckable(True)
			btn.clicked.connect(lambda checked=False, k=key: self._go_to(k))
			nav_layout.addWidget(btn)
			self.nav_buttons[key] = btn
		nav_layout.addStretch(1)

		scroller = QScrollArea()
		scroller.setWidgetResizable(True)
		scroller.setWidget(nav_container)
		scroller.setFrameShape(QScrollArea.NoFrame)
		side_layout.addWidget(scroller, 1)

		self.logout_btn = QPushButton("Logout")
		self.logout_btn.setObjectName("PrimaryButton")
		self.logout_btn.clicked.connect(self._logout)
		side_layout.addWidget(self.logout_btn)

		main = QFrame(objectName="AuthPanel")
		main_layout = QVBoxLayout(main)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)

		topbar = QFrame(objectName="AuthGlass")
		top_layout = QHBoxLayout(topbar)
		top_layout.setContentsMargins(18, 12, 18, 12)
		self.page_title = QLabel("Dashboard")
		self.page_title.setStyleSheet("font-size: 28px; font-weight: 800;")
		top_layout.addWidget(self.page_title)
		top_layout.addStretch(1)

		self.user_info = QLabel("-")
		self.user_info.setObjectName("AuthLabel")
		self.connection_info = QLabel("Online")
		self.connection_info.setObjectName("AuthLabel")
		self.clock = QLabel("--")
		self.clock.setObjectName("AuthLabel")
		self.lang_en = QPushButton("EN")
		self.lang_ar = QPushButton("AR")
		for btn in (self.lang_en, self.lang_ar):
			btn.setObjectName("LangToggleButton")
		self.lang_en.clicked.connect(lambda: self._set_language("en"))
		self.lang_ar.clicked.connect(lambda: self._set_language("ar"))

		top_layout.addWidget(self.user_info)
		top_layout.addWidget(self.connection_info)
		top_layout.addWidget(self.clock)
		top_layout.addWidget(self.lang_en)
		top_layout.addWidget(self.lang_ar)

		content_wrap = QWidget()
		content_layout = QVBoxLayout(content_wrap)
		content_layout.setContentsMargins(18, 18, 18, 18)

		self.pages = QStackedWidget()
		self.dashboard_page = DashboardPage()
		self.bookings_page = BookingsPage(self.api_client)
		self.customers_page = CustomersPage(self.api_client)
		self.vehicles_page = VehiclesPage(self.api_client)
		self.payments_page = PaymentsPage(self.api_client)
		self.maintenance_page = MaintenancePage(self.api_client)
		self.reports_page = ReportsPage(self.api_client)
		self.settings_page = SettingsPage(self.api_client)

		self.page_map = {
			"dashboard": self.dashboard_page,
			"bookings": self.bookings_page,
			"customers": self.customers_page,
			"fleet": self.vehicles_page,
			"payments": self.payments_page,
			"maintenance": self.maintenance_page,
			"reports": self.reports_page,
			"settings": self.settings_page,
		}
		for page in self.page_map.values():
			self.pages.addWidget(page)

		self.search_btn = QPushButton("Search")
		self.search_btn.setObjectName("LangToggleButton")
		self.notify_btn = QPushButton("Notifications")
		self.notify_btn.setObjectName("LangToggleButton")
		self.search_btn.clicked.connect(self._open_search_dialog)
		self.notify_btn.clicked.connect(self._open_notifications_dialog)
		top_layout.insertWidget(2, self.search_btn)
		top_layout.insertWidget(3, self.notify_btn)

		content_layout.addWidget(self.pages)

		main_layout.addWidget(topbar)
		main_layout.addWidget(content_wrap, 1)

		shell.addWidget(sidebar)
		shell.addWidget(main, 1)

		self.dashboard_page.bind_period_handlers(
			lambda: self._load_dashboard("today"),
			lambda: self._load_dashboard("weekly"),
			lambda: self._load_dashboard("monthly"),
		)

		self._set_language(self.state.ui_lang)
		self._apply_user_info()
		self._go_to("dashboard")
		self._start_clock()
		self._load_dashboard("today")
		self._refresh_connection_status()

	def _start_clock(self) -> None:
		self._tick_clock()
		timer = QTimer(self)
		timer.timeout.connect(self._tick_clock)
		timer.start(30000)
		self._clock_timer = timer
		sync_timer = QTimer(self)
		sync_timer.timeout.connect(self._on_sync_tick)
		sync_timer.start(12000)
		self._sync_timer = sync_timer

	def _tick_clock(self) -> None:
		self.clock.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))

	def _on_sync_tick(self) -> None:
		try:
			self.api_client.sync_queue()
		except Exception:
			pass
		self._refresh_connection_status()

	def _refresh_connection_status(self) -> None:
		try:
			self.connection_info.setText(self.api_client.connection_label())
		except Exception:
			self.connection_info.setText("Offline")

	def _go_to(self, key: str) -> None:
		page = self.page_map[key]
		self.pages.setCurrentWidget(page)
		self.page_title.setText(self.nav_buttons[key].text())
		for name, btn in self.nav_buttons.items():
			btn.setChecked(name == key)
			btn.setProperty("active", name == key)
			btn.style().unpolish(btn)
			btn.style().polish(btn)
		if hasattr(page, "load_data"):
			page.load_data()
		self._refresh_connection_status()

	def _set_language(self, lang: str) -> None:
		self.state.set_language(lang)
		self._apply_translations()
		self.lang_en.setProperty("active", lang == "en")
		self.lang_ar.setProperty("active", lang == "ar")
		self.lang_en.style().unpolish(self.lang_en)
		self.lang_en.style().polish(self.lang_en)
		self.lang_ar.style().unpolish(self.lang_ar)
		self.lang_ar.style().polish(self.lang_ar)
		direction = Qt.RightToLeft if self.state.is_rtl else Qt.LeftToRight
		self.setLayoutDirection(direction)
		try:
			self.api_client.set_language(lang)
		except Exception:
			pass

	def _apply_user_info(self) -> None:
		user = self.state.user_display_name or "User"
		branch = self.state.active_branch_name or ("لا يوجد فرع" if self.state.is_rtl else "No Branch")
		self.user_info.setText(f"{user} | {branch}")

	def _apply_translations(self) -> None:
		if self.state.is_rtl:
			labels = {
				"dashboard": "لوحة التحكم",
				"bookings": "الحجوزات",
				"customers": "العملاء",
				"fleet": "الاسطول",
				"payments": "المدفوعات",
				"maintenance": "الصيانة",
				"reports": "التقارير",
				"settings": "الاعدادات",
			}
			self.logout_btn.setText("تسجيل الخروج")
		else:
			labels = {
				"dashboard": "Dashboard",
				"bookings": "Bookings",
				"customers": "Customers",
				"fleet": "Fleet",
				"payments": "Payments",
				"maintenance": "Maintenance",
				"reports": "Reports",
				"settings": "Settings",
			}
			self.logout_btn.setText("Logout")

		for key, text in labels.items():
			self.nav_buttons[key].setText(text)

		for page in self.page_map.values():
			if hasattr(page, "set_language"):
				page.set_language("ar" if self.state.is_rtl else "en")

		self._apply_user_info()

		if self.state.is_rtl:
			self.search_btn.setText("بحث")
			self.notify_btn.setText("الإشعارات")
		else:
			self.search_btn.setText("Search")
			self.notify_btn.setText("Notifications")

	def _load_dashboard(self, period: str) -> None:
		try:
			payload = self.api_client.fetch_dashboard_bundle(period=period)
			self.dashboard_page.update_dashboard(payload)
		except Exception:
			self.dashboard_page.update_dashboard({})
		self._refresh_connection_status()

	def _logout(self) -> None:
		try:
			self.api_client.logout()
		except Exception:
			pass
		self.close()
		if self._on_logout is not None:
			self._on_logout()

	def _open_search_dialog(self) -> None:
		dialog = QDialog(self)
		dialog.setWindowTitle("Search Bookings" if not self.state.is_rtl else "البحث في الحجوزات")
		dialog.resize(900, 480)
		layout = QVBoxLayout(dialog)

		input_row = QHBoxLayout()
		query_edit = QLineEdit()
		query_edit.setPlaceholderText(
			"Search bookings by customer, phone, plate"
			if not self.state.is_rtl
			else "ابحث عن الحجز بالعميل أو الهاتف أو اللوحة"
		)
		search_btn = QPushButton("Search" if not self.state.is_rtl else "بحث")
		input_row.addWidget(query_edit, 1)
		input_row.addWidget(search_btn)
		layout.addLayout(input_row)

		table = QTableWidget(0, 5)
		table.setHorizontalHeaderLabels(["ID", "Customer", "Vehicle", "Pickup", "Status"])
		table.horizontalHeader().setStretchLastSection(True)
		table.verticalHeader().setVisible(False)
		table.setSelectionBehavior(QTableWidget.SelectRows)
		table.setEditTriggers(QTableWidget.NoEditTriggers)
		layout.addWidget(table, 1)

		buttons = QDialogButtonBox(QDialogButtonBox.Close)
		buttons.rejected.connect(dialog.reject)
		layout.addWidget(buttons)

		def run_search() -> None:
			try:
				q = query_edit.text().strip()
				data = self.api_client.get_json(f"/api/bookings/?q={q}&status=")
				rows = data.get("results", [])
				table.setRowCount(len(rows))
				for r, item in enumerate(rows):
					values = [
						str(item.get("id", "-")),
						str(item.get("customer", {}).get("name", "-")),
						str(item.get("vehicle", {}).get("plate", "-")),
						str(item.get("pickup_date", "-")),
						str(item.get("status", "-")),
					]
					for c, value in enumerate(values):
						table.setItem(r, c, QTableWidgetItem(value))
			except Exception as exc:
				show_warning(
					self,
					is_rtl=self.state.is_rtl,
					title_en="Search",
					message_en=str(exc),
					title_ar="بحث",
					message_ar=str(exc),
				)

		search_btn.clicked.connect(run_search)
		query_edit.returnPressed.connect(run_search)
		dialog.exec()

	def _open_notifications_dialog(self) -> None:
		dialog = QDialog(self)
		dialog.setWindowTitle("Notifications" if not self.state.is_rtl else "الإشعارات")
		dialog.resize(520, 500)
		layout = QVBoxLayout(dialog)

		list_widget = QListWidget()
		layout.addWidget(list_widget, 1)

		controls = QHBoxLayout()
		clear_btn = QPushButton("Mark All Read" if not self.state.is_rtl else "وضع الكل كمقروء")
		refresh_btn = QPushButton("Refresh" if not self.state.is_rtl else "تحديث")
		controls.addWidget(clear_btn)
		controls.addWidget(refresh_btn)
		controls.addStretch(1)
		layout.addLayout(controls)

		close_box = QDialogButtonBox(QDialogButtonBox.Close)
		close_box.rejected.connect(dialog.reject)
		layout.addWidget(close_box)

		def load_notifications() -> None:
			try:
				payload = self.api_client.fetch_notifications()
				results = payload.get("results", [])
				count = int(payload.get("count", 0))
				self.notify_btn.setText(
					("Notifications" if not self.state.is_rtl else "الإشعارات") + f" ({count})"
				)
				list_widget.clear()
				if not results:
					list_widget.addItem(QListWidgetItem("No notifications" if not self.state.is_rtl else "لا توجد إشعارات"))
					return
				for item in results:
					title = item.get("title", "")
					detail = item.get("detail", "")
					list_widget.addItem(QListWidgetItem(f"{title}\n{detail}".strip()))
			except Exception as exc:
				show_warning(
					self,
					is_rtl=self.state.is_rtl,
					title_en="Notifications",
					message_en=str(exc),
					title_ar="الإشعارات",
					message_ar=str(exc),
				)

		def clear_notifications() -> None:
			try:
				self.api_client.clear_notifications()
				load_notifications()
			except Exception as exc:
				show_warning(
					self,
					is_rtl=self.state.is_rtl,
					title_en="Notifications",
					message_en=str(exc),
					title_ar="الإشعارات",
					message_ar=str(exc),
				)

		clear_btn.clicked.connect(clear_notifications)
		refresh_btn.clicked.connect(load_notifications)
		load_notifications()
		dialog.exec()
