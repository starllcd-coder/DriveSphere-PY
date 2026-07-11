from __future__ import annotations

from PySide6.QtWidgets import (
	QComboBox,
	QFormLayout,
	QHBoxLayout,
	QHeaderView,
	QLabel,
	QPushButton,
	QTabWidget,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)

from drivesphere_desktop.core.api_client import ApiClient


class ReportsPage(QWidget):
	def __init__(self, api_client: ApiClient) -> None:
		super().__init__()
		self.api_client = api_client
		self.is_rtl = False

		root = QVBoxLayout(self)
		root.setContentsMargins(0, 0, 0, 0)
		root.setSpacing(12)

		top = QHBoxLayout()
		self.period = QComboBox()
		self.period.addItem("Today", "today")
		self.period.addItem("Weekly", "weekly")
		self.period.addItem("Monthly", "monthly")
		self.period.setCurrentIndex(2)
		self.refresh_btn = QPushButton("Refresh")
		self.refresh_btn.setObjectName("DsBtnPrimary")
		top.addWidget(QLabel("Period"))
		top.addWidget(self.period)
		self.period.setObjectName("DsInput")
		top.addWidget(self.refresh_btn)
		top.addStretch(1)
		root.addLayout(top)

		self.tabs = QTabWidget()
		root.addWidget(self.tabs, 1)
		self.overview_tab = QWidget()
		self.financial_tab = QWidget()
		self.fleet_tab = QWidget()
		self.maintenance_tab = QWidget()
		self.customers_tab = QWidget()
		self.tabs.addTab(self.overview_tab, "Overview")
		self.tabs.addTab(self.financial_tab, "Financial")
		self.tabs.addTab(self.fleet_tab, "Fleet")
		self.tabs.addTab(self.maintenance_tab, "Maintenance")
		self.tabs.addTab(self.customers_tab, "Customers")

		self._build_overview()
		self._build_table_tab(self.financial_tab, "r_financial")
		self._build_table_tab(self.fleet_tab, "r_fleet")
		self._build_table_tab(self.maintenance_tab, "r_maintenance")
		self._build_table_tab(self.customers_tab, "r_customers")

		self.status = QLabel("")
		root.addWidget(self.status)
		self.refresh_btn.clicked.connect(self.load_data)

	def set_language(self, lang: str) -> None:
		self.is_rtl = lang == "ar"

	def _build_overview(self) -> None:
		layout = QVBoxLayout(self.overview_tab)
		form = QFormLayout()
		self.ov_new_customers = QLabel("-")
		self.ov_total_customers = QLabel("-")
		self.ov_revenue = QLabel("-")
		self.ov_trips = QLabel("-")
		self.ov_active_vehicles = QLabel("-")
		self.ov_completed_trips = QLabel("-")
		self.ov_cancelled = QLabel("-")
		self.ov_collection = QLabel("-")
		self.ov_pending = QLabel("-")
		self.ov_utilization = QLabel("-")
		form.addRow("New Customers", self.ov_new_customers)
		form.addRow("Total Customers", self.ov_total_customers)
		form.addRow("Revenue", self.ov_revenue)
		form.addRow("Trips", self.ov_trips)
		form.addRow("Active Vehicles", self.ov_active_vehicles)
		form.addRow("Completed Trips", self.ov_completed_trips)
		form.addRow("Cancelled Trips", self.ov_cancelled)
		form.addRow("Collection Rate", self.ov_collection)
		form.addRow("Pending Balance", self.ov_pending)
		form.addRow("Fleet Utilization", self.ov_utilization)
		layout.addLayout(form)
		layout.addStretch(1)

	def _build_table_tab(self, tab: QWidget, key: str) -> None:
		layout = QVBoxLayout(tab)
		table = QTableWidget(0, 2)
		table.setHorizontalHeaderLabels(["Metric", "Value"])
		table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		table.verticalHeader().setVisible(False)
		table.setObjectName(key)
		layout.addWidget(table)
		setattr(self, f"{key}_table", table)

	def _fill_simple_table(self, table: QTableWidget, payload: dict) -> None:
		rows: list[tuple[str, str]] = []
		for key, value in payload.items():
			if isinstance(value, (int, float, str, bool)) or value is None:
				rows.append((str(key), str(value)))
		table.setRowCount(len(rows))
		for r, (k, v) in enumerate(rows):
			table.setItem(r, 0, QTableWidgetItem(k))
			table.setItem(r, 1, QTableWidgetItem(v))

	def load_data(self) -> None:
		try:
			period = self.period.currentData() or "monthly"
			overview = self.api_client.get_json(f"/api/reports/overview/?period={period}").get("data", {})
			self.ov_new_customers.setText(str(overview.get("new_customers", 0)))
			self.ov_total_customers.setText(str(overview.get("total_customers", 0)))
			self.ov_revenue.setText(str(overview.get("revenue", 0)))
			self.ov_trips.setText(str(overview.get("trips", 0)))
			self.ov_active_vehicles.setText(str(overview.get("active_vehicles", 0)))
			self.ov_completed_trips.setText(str(overview.get("completed_trips", 0)))
			self.ov_cancelled.setText(str(overview.get("cancelled_trips", 0)))
			self.ov_collection.setText(f"{overview.get('collection_rate', 0)}%")
			self.ov_pending.setText(str(overview.get("pending_balance", 0)))
			self.ov_utilization.setText(f"{overview.get('fleet_utilization', 0)}%")

			financial = self.api_client.get_json(f"/api/reports/financial/?period={period}").get("data", {})
			fleet = self.api_client.get_json(f"/api/reports/fleet/?period={period}").get("data", {})
			maintenance = self.api_client.get_json(f"/api/reports/maintenance/?period={period}").get("data", {})
			customers = self.api_client.get_json(f"/api/reports/customers/?period={period}").get("data", {})
			self._fill_simple_table(self.r_financial_table, financial)
			self._fill_simple_table(self.r_fleet_table, fleet)
			self._fill_simple_table(self.r_maintenance_table, maintenance)
			self._fill_simple_table(self.r_customers_table, customers)
			self.status.setText("Reports refreshed.")
		except Exception as exc:
			self.status.setText(f"Load failed: {exc}")
