from __future__ import annotations

import json

from PySide6.QtWidgets import (
	QComboBox,
	QFormLayout,
	QHBoxLayout,
	QHeaderView,
	QLabel,
	QLineEdit,
	QPushButton,
	QTableWidget,
	QTableWidgetItem,
	QTabWidget,
	QTextEdit,
	QVBoxLayout,
	QWidget,
)

from drivesphere_desktop.core.api_client import ApiClient


class SettingsPage(QWidget):
	def __init__(self, api_client: ApiClient) -> None:
		super().__init__()
		self.api_client = api_client
		self.is_rtl = False

		root = QVBoxLayout(self)
		root.setContentsMargins(0, 0, 0, 0)
		root.setSpacing(12)

		self.tabs = QTabWidget()
		root.addWidget(self.tabs, 1)

		self.general_tab = QWidget()
		self.employees_tab = QWidget()
		self.integrations_tab = QWidget()
		self.db_tab = QWidget()
		self.tabs.addTab(self.general_tab, "General")
		self.tabs.addTab(self.employees_tab, "Employees")
		self.tabs.addTab(self.integrations_tab, "Integrations")
		self.tabs.addTab(self.db_tab, "Database")

		self._build_general_tab()
		self._build_employees_tab()
		self._build_integrations_tab()
		self._build_db_tab()

	def _style_input(self, widget) -> None:
		widget.setObjectName("DsInput")

	def _style_button(self, widget, primary: bool = False) -> None:
		widget.setObjectName("DsBtnPrimary" if primary else "LangToggleButton")

	def set_language(self, lang: str) -> None:
		self.is_rtl = lang == "ar"

	def _notify(self, text: str) -> None:
		self.status_label.setText(text)

	def _build_general_tab(self) -> None:
		layout = QVBoxLayout(self.general_tab)
		form = QFormLayout()
		self.business_name = QLineEdit()
		self.business_phone = QLineEdit()
		self.business_email = QLineEdit()
		self.business_address = QLineEdit()
		self.business_currency = QLineEdit()
		for w in [self.business_name, self.business_phone, self.business_email, self.business_address, self.business_currency]:
			self._style_input(w)
		form.addRow("Business Name", self.business_name)
		form.addRow("Phone", self.business_phone)
		form.addRow("Email", self.business_email)
		form.addRow("Address", self.business_address)
		form.addRow("Currency Code", self.business_currency)
		layout.addLayout(form)

		row = QHBoxLayout()
		load_btn = QPushButton("Load")
		save_btn = QPushButton("Save")
		self._style_button(load_btn)
		self._style_button(save_btn, primary=True)
		row.addWidget(load_btn)
		row.addWidget(save_btn)
		row.addStretch(1)
		layout.addLayout(row)
		self.status_label = QLabel("")
		layout.addWidget(self.status_label)
		layout.addStretch(1)

		def load() -> None:
			try:
				data = self.api_client.get_json("/settings/api/business/")
				payload = data.get("data", {})
				self.business_name.setText(str(payload.get("business_name", "")))
				self.business_phone.setText(str(payload.get("phone_number", "")))
				self.business_email.setText(str(payload.get("email", "")))
				self.business_address.setText(str(payload.get("address", "")))
				self.business_currency.setText(str(payload.get("currency_code", "")))
				self._notify("Business profile loaded.")
			except Exception as exc:
				self._notify(f"Load failed: {exc}")

		def save() -> None:
			try:
				payload = {
					"business_name": self.business_name.text().strip(),
					"phone_number": self.business_phone.text().strip(),
					"email": self.business_email.text().strip(),
					"address": self.business_address.text().strip(),
					"currency_code": self.business_currency.text().strip(),
				}
				self.api_client.post_json("/settings/api/business/save/", payload)
				self._notify("Business profile saved.")
			except Exception as exc:
				self._notify(f"Save failed: {exc}")

		load_btn.clicked.connect(load)
		save_btn.clicked.connect(save)

	def _build_employees_tab(self) -> None:
		layout = QVBoxLayout(self.employees_tab)
		self.emp_table = QTableWidget(0, 4)
		self.emp_table.setHorizontalHeaderLabels(["Email", "Username", "Role", "Status"])
		self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		self.emp_table.verticalHeader().setVisible(False)
		layout.addWidget(self.emp_table)

		form = QFormLayout()
		self.emp_username = QLineEdit()
		self.emp_email = QLineEdit()
		self.emp_password = QLineEdit()
		self.emp_role = QComboBox()
		for w in [self.emp_username, self.emp_email, self.emp_password]:
			self._style_input(w)
		self._style_input(self.emp_role)
		for role in ["ADMIN", "MANAGER", "AGENT", "MECHANIC", "ACCOUNTANT", "VIEWER"]:
			self.emp_role.addItem(role, role)
		form.addRow("Username", self.emp_username)
		form.addRow("Email", self.emp_email)
		form.addRow("Password", self.emp_password)
		form.addRow("Role", self.emp_role)
		layout.addLayout(form)

		row = QHBoxLayout()
		refresh_btn = QPushButton("Refresh")
		create_btn = QPushButton("Create Employee")
		self._style_button(refresh_btn)
		self._style_button(create_btn, primary=True)
		row.addWidget(refresh_btn)
		row.addWidget(create_btn)
		row.addStretch(1)
		layout.addLayout(row)
		self.emp_status = QLabel("")
		layout.addWidget(self.emp_status)

		def refresh() -> None:
			try:
				payload = self.api_client.get_json("/settings/api/employees/")
				rows = payload.get("results", [])
				self.emp_table.setRowCount(len(rows))
				for r, item in enumerate(rows):
					values = [
						str(item.get("email", "")),
						str(item.get("username", "")),
						str(item.get("role", "")),
						"Active" if item.get("is_active") else "Inactive",
					]
					for c, value in enumerate(values):
						self.emp_table.setItem(r, c, QTableWidgetItem(value))
				self.emp_status.setText(f"{len(rows)} employees loaded.")
			except Exception as exc:
				self.emp_status.setText(f"Load failed: {exc}")

		def create() -> None:
			try:
				self.api_client.post_json(
					"/settings/api/employees/create/",
					{
						"username": self.emp_username.text().strip(),
						"email": self.emp_email.text().strip(),
						"password": self.emp_password.text().strip(),
						"role": self.emp_role.currentData(),
					},
				)
				self.emp_status.setText("Employee created.")
				refresh()
			except Exception as exc:
				self.emp_status.setText(f"Create failed: {exc}")

		refresh_btn.clicked.connect(refresh)
		create_btn.clicked.connect(create)

	def _build_integrations_tab(self) -> None:
		layout = QVBoxLayout(self.integrations_tab)

		form = QFormLayout()
		self.int_type = QComboBox()
		for item in [
			("ACCOUNTING_QUICKBOOKS", "QuickBooks"),
			("ACCOUNTING_ZOHO", "Zoho Books"),
			("TELEMATICS_PROVIDER_A", "Telematics Provider A"),
			("TELEMATICS_PROVIDER_B", "Telematics Provider B"),
		]:
			self.int_type.addItem(item[1], item[0])
		self.int_base_url = QLineEdit()
		self.int_client_id = QLineEdit()
		self.int_client_secret = QLineEdit()
		self.int_access_token = QLineEdit()
		self.int_refresh_token = QLineEdit()
		self.int_org_id = QLineEdit()
		self.int_metadata = QTextEdit()
		self.int_metadata.setFixedHeight(90)
		self.int_active = QComboBox()
		self.int_active.addItem("Yes", True)
		self.int_active.addItem("No", False)
		self.int_period = QComboBox()
		for period in ["today", "weekly", "monthly"]:
			self.int_period.addItem(period, period)
		self.int_since_hours = QLineEdit("6")
		for w in [
			self.int_type,
			self.int_base_url,
			self.int_client_id,
			self.int_client_secret,
			self.int_access_token,
			self.int_refresh_token,
			self.int_org_id,
			self.int_metadata,
			self.int_active,
			self.int_period,
			self.int_since_hours,
		]:
			self._style_input(w)

		form.addRow("Integration", self.int_type)
		form.addRow("Base URL", self.int_base_url)
		form.addRow("Client ID", self.int_client_id)
		form.addRow("Client Secret", self.int_client_secret)
		form.addRow("Access Token", self.int_access_token)
		form.addRow("Refresh Token", self.int_refresh_token)
		form.addRow("Org ID", self.int_org_id)
		form.addRow("Metadata JSON", self.int_metadata)
		form.addRow("Active", self.int_active)
		form.addRow("Accounting Period", self.int_period)
		form.addRow("Telematics Since Hours", self.int_since_hours)
		layout.addLayout(form)

		btn_row = QHBoxLayout()
		load_btn = QPushButton("Load Profile")
		save_btn = QPushButton("Save Profile")
		run_btn = QPushButton("Run Sync")
		log_btn = QPushButton("Refresh Logs")
		self._style_button(load_btn)
		self._style_button(save_btn, primary=True)
		self._style_button(run_btn, primary=True)
		self._style_button(log_btn)
		btn_row.addWidget(load_btn)
		btn_row.addWidget(save_btn)
		btn_row.addWidget(run_btn)
		btn_row.addWidget(log_btn)
		btn_row.addStretch(1)
		layout.addLayout(btn_row)

		self.int_logs = QTableWidget(0, 5)
		self.int_logs.setHorizontalHeaderLabels(["Time", "Integration", "Direction", "Status", "Summary"])
		self.int_logs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		self.int_logs.verticalHeader().setVisible(False)
		layout.addWidget(self.int_logs)
		self.int_status = QLabel("")
		layout.addWidget(self.int_status)

		def load_profile() -> None:
			try:
				target = self.int_type.currentData()
				payload = self.api_client.get_json("/api/integrations/profiles/")
				profiles = payload.get("profiles", [])
				match = None
				for profile in profiles:
					if profile.get("integration_type") == target:
						match = profile
						break
				if not match:
					self.int_status.setText("Profile not found, fill fields and save.")
					return
				self.int_base_url.setText(str(match.get("base_url", "")))
				self.int_client_id.setText(str(match.get("client_id", "")))
				self.int_org_id.setText(str(match.get("org_id", "")))
				self.int_metadata.setPlainText(json.dumps(match.get("metadata", {}), indent=2))
				self.int_active.setCurrentIndex(0 if match.get("is_active") else 1)
				self.int_status.setText("Profile loaded.")
			except Exception as exc:
				self.int_status.setText(f"Load failed: {exc}")

		def save_profile() -> None:
			try:
				metadata_raw = self.int_metadata.toPlainText().strip()
				metadata = json.loads(metadata_raw) if metadata_raw else {}
				payload = {
					"integration_type": self.int_type.currentData(),
					"base_url": self.int_base_url.text().strip(),
					"client_id": self.int_client_id.text().strip(),
					"org_id": self.int_org_id.text().strip(),
					"metadata": metadata,
					"is_active": bool(self.int_active.currentData()),
				}
				if self.int_client_secret.text().strip():
					payload["client_secret"] = self.int_client_secret.text().strip()
				if self.int_access_token.text().strip():
					payload["access_token"] = self.int_access_token.text().strip()
				if self.int_refresh_token.text().strip():
					payload["refresh_token"] = self.int_refresh_token.text().strip()
				self.api_client.post_json("/api/integrations/profiles/", payload)
				self.int_status.setText("Profile saved.")
			except Exception as exc:
				self.int_status.setText(f"Save failed: {exc}")

		def run_sync() -> None:
			try:
				integration_type = str(self.int_type.currentData())
				body = {"integration_type": integration_type}
				if integration_type.startswith("ACCOUNTING"):
					body["period"] = self.int_period.currentData()
				else:
					body["since_hours"] = int(self.int_since_hours.text().strip() or "6")
				result = self.api_client.post_json("/api/integrations/sync/run/", body)
				self.int_status.setText(f"Sync result: {result.get('status', 'OK')}")
				refresh_logs()
			except Exception as exc:
				self.int_status.setText(f"Sync failed: {exc}")

		def refresh_logs() -> None:
			try:
				target = self.int_type.currentData()
				payload = self.api_client.get_json(f"/api/integrations/sync/logs/?integration_type={target}")
				logs = payload.get("logs", [])
				self.int_logs.setRowCount(len(logs))
				for r, item in enumerate(logs):
					values = [
						str(item.get("created_at", "")),
						str(item.get("profile_type", "")),
						str(item.get("direction", "")),
						str(item.get("status", "")),
						str(item.get("summary", "")),
					]
					for c, value in enumerate(values):
						self.int_logs.setItem(r, c, QTableWidgetItem(value))
				self.int_status.setText(f"{len(logs)} logs loaded.")
			except Exception as exc:
				self.int_status.setText(f"Logs failed: {exc}")

		load_btn.clicked.connect(load_profile)
		save_btn.clicked.connect(save_profile)
		run_btn.clicked.connect(run_sync)
		log_btn.clicked.connect(refresh_logs)

	def _build_db_tab(self) -> None:
		layout = QVBoxLayout(self.db_tab)
		form = QFormLayout()
		self.db_provider = QComboBox()
		self.db_provider.addItem("PostgreSQL", "POSTGRES")
		self.db_provider.addItem("Neon", "NEON")
		self.db_host = QLineEdit()
		self.db_port = QLineEdit()
		self.db_name = QLineEdit()
		self.db_user = QLineEdit()
		self.db_pass = QLineEdit()
		self.db_ssl = QLineEdit()
		for w in [self.db_provider, self.db_host, self.db_port, self.db_name, self.db_user, self.db_pass, self.db_ssl]:
			self._style_input(w)
		form.addRow("Provider", self.db_provider)
		form.addRow("Host", self.db_host)
		form.addRow("Port", self.db_port)
		form.addRow("Database", self.db_name)
		form.addRow("User", self.db_user)
		form.addRow("Password", self.db_pass)
		form.addRow("SSL Mode", self.db_ssl)
		layout.addLayout(form)

		row = QHBoxLayout()
		load_btn = QPushButton("Load")
		save_btn = QPushButton("Save")
		test_btn = QPushButton("Test Connection")
		migrate_btn = QPushButton("Run Migration")
		self._style_button(load_btn)
		self._style_button(save_btn, primary=True)
		self._style_button(test_btn)
		self._style_button(migrate_btn)
		row.addWidget(load_btn)
		row.addWidget(save_btn)
		row.addWidget(test_btn)
		row.addWidget(migrate_btn)
		row.addStretch(1)
		layout.addLayout(row)
		self.db_status = QLabel("")
		layout.addWidget(self.db_status)
		layout.addStretch(1)

		def load() -> None:
			try:
				payload = self.api_client.get_json("/settings/api/db/profile/")
				data = payload.get("data", {})
				idx = self.db_provider.findData(data.get("provider", "POSTGRES"))
				if idx >= 0:
					self.db_provider.setCurrentIndex(idx)
				self.db_host.setText(str(data.get("host", "")))
				self.db_port.setText(str(data.get("port", "")))
				self.db_name.setText(str(data.get("database_name", "")))
				self.db_user.setText(str(data.get("username", "")))
				self.db_pass.setText(str(data.get("password", "")))
				self.db_ssl.setText(str(data.get("sslmode", "")))
				self.db_status.setText("DB profile loaded.")
			except Exception as exc:
				self.db_status.setText(f"Load failed: {exc}")

		def save() -> None:
			try:
				self.api_client.post_json(
					"/settings/api/db/profile/save/",
					{
						"provider": self.db_provider.currentData(),
						"host": self.db_host.text().strip(),
						"port": self.db_port.text().strip(),
						"database_name": self.db_name.text().strip(),
						"username": self.db_user.text().strip(),
						"password": self.db_pass.text().strip(),
						"sslmode": self.db_ssl.text().strip(),
					},
				)
				self.db_status.setText("DB profile saved.")
			except Exception as exc:
				self.db_status.setText(f"Save failed: {exc}")

		def test() -> None:
			try:
				result = self.api_client.post_json("/settings/api/db/test/", {})
				self.db_status.setText(str(result.get("message", "Done")))
			except Exception as exc:
				self.db_status.setText(f"Test failed: {exc}")

		def migrate() -> None:
			try:
				result = self.api_client.post_json("/settings/api/db/migrate/", {})
				self.db_status.setText(str(result.get("message", "Done")))
			except Exception as exc:
				self.db_status.setText(f"Migrate failed: {exc}")

		load_btn.clicked.connect(load)
		save_btn.clicked.connect(save)
		test_btn.clicked.connect(test)
		migrate_btn.clicked.connect(migrate)
