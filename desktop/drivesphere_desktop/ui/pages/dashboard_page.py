from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QFrame,
	QGridLayout,
	QHBoxLayout,
	QLabel,
	QPushButton,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


class DashboardPage(QWidget):
	def __init__(self) -> None:
		super().__init__()
		root = QVBoxLayout(self)
		root.setContentsMargins(0, 0, 0, 0)
		root.setSpacing(14)

		kpi_grid = QGridLayout()
		kpi_grid.setSpacing(12)
		self.kpi_bookings = self._build_kpi("Bookings")
		self.kpi_customers = self._build_kpi("Active Customers")
		self.kpi_fleet = self._build_kpi("Fleet Vehicles")
		self.kpi_revenue = self._build_kpi("Net Revenue")
		kpi_grid.addWidget(self.kpi_bookings[0], 0, 0)
		kpi_grid.addWidget(self.kpi_customers[0], 0, 1)
		kpi_grid.addWidget(self.kpi_fleet[0], 0, 2)
		kpi_grid.addWidget(self.kpi_revenue[0], 0, 3)
		root.addLayout(kpi_grid)

		row = QHBoxLayout()
		row.setSpacing(12)
		root.addLayout(row, 1)

		left = QFrame()
		left.setObjectName("AuthCard")
		left_layout = QVBoxLayout(left)
		left_layout.setContentsMargins(14, 14, 14, 14)
		left_layout.setSpacing(10)
		row.addWidget(left, 7)

		head = QHBoxLayout()
		title = QLabel("Overview")
		title.setObjectName("AuthLabel")
		head.addWidget(title)
		head.addStretch(1)
		self.btn_today = QPushButton("Today")
		self.btn_week = QPushButton("Weekly")
		self.btn_month = QPushButton("Monthly")
		for btn in (self.btn_today, self.btn_week, self.btn_month):
			btn.setObjectName("LangToggleButton")
			head.addWidget(btn)
		left_layout.addLayout(head)

		self.mini_grid = QGridLayout()
		self.mini_grid.setSpacing(10)
		self.mini_active = self._build_mini("Active Rentals")
		self.mini_upcoming = self._build_mini("Upcoming")
		self.mini_overdue = self._build_mini("Overdue")
		self.mini_maint = self._build_mini("Maintenance Open")
		self.mini_grid.addWidget(self.mini_active[0], 0, 0)
		self.mini_grid.addWidget(self.mini_upcoming[0], 0, 1)
		self.mini_grid.addWidget(self.mini_overdue[0], 1, 0)
		self.mini_grid.addWidget(self.mini_maint[0], 1, 1)
		left_layout.addLayout(self.mini_grid)

		right = QFrame()
		right.setObjectName("AuthCard")
		right_layout = QVBoxLayout(right)
		right_layout.setContentsMargins(14, 14, 14, 14)
		right_layout.setSpacing(10)
		row.addWidget(right, 5)

		right_title = QLabel("Recent Payments")
		right_title.setObjectName("AuthLabel")
		right_layout.addWidget(right_title)
		self.payments_list = QVBoxLayout()
		self.payments_list.setSpacing(8)
		right_layout.addLayout(self.payments_list)
		right_layout.addStretch(1)

		table_card = QFrame()
		table_card.setObjectName("AuthCard")
		table_layout = QVBoxLayout(table_card)
		table_layout.setContentsMargins(14, 14, 14, 14)
		table_layout.setSpacing(10)
		table_title = QLabel("Recent Reservations")
		table_title.setObjectName("AuthLabel")
		table_layout.addWidget(table_title)

		self.bookings_table = QTableWidget(0, 5)
		self.bookings_table.setHorizontalHeaderLabels(["Customer", "Vehicle", "Pickup", "Return", "Status"])
		self.bookings_table.horizontalHeader().setStretchLastSection(True)
		self.bookings_table.verticalHeader().setVisible(False)
		self.bookings_table.setAlternatingRowColors(True)
		self.bookings_table.setSelectionBehavior(QTableWidget.SelectRows)
		self.bookings_table.setEditTriggers(QTableWidget.NoEditTriggers)
		table_layout.addWidget(self.bookings_table)
		root.addWidget(table_card, 1)

	def _build_kpi(self, label: str) -> tuple[QFrame, QLabel]:
		card = QFrame()
		card.setObjectName("AuthCard")
		layout = QVBoxLayout(card)
		layout.setContentsMargins(14, 14, 14, 14)
		title = QLabel(label)
		title.setObjectName("AuthLabel")
		value = QLabel("-")
		value.setStyleSheet("font-size: 28px; font-weight: 800;")
		layout.addWidget(title)
		layout.addWidget(value)
		return card, value

	def _build_mini(self, label: str) -> tuple[QFrame, QLabel]:
		card = QFrame()
		card.setObjectName("AuthForm")
		layout = QVBoxLayout(card)
		layout.setContentsMargins(10, 10, 10, 10)
		title = QLabel(label)
		title.setStyleSheet("font-size: 12px;")
		value = QLabel("-")
		value.setStyleSheet("font-size: 18px; font-weight: 700;")
		layout.addWidget(title)
		layout.addWidget(value)
		return card, value

	def bind_period_handlers(self, on_today, on_week, on_month) -> None:
		self.btn_today.clicked.connect(on_today)
		self.btn_week.clicked.connect(on_week)
		self.btn_month.clicked.connect(on_month)

	def update_dashboard(self, data: dict) -> None:
		overview = data.get("overview", {})
		self.kpi_bookings[1].setText(str(overview.get("bookings_count", "-")))
		self.kpi_customers[1].setText(str(overview.get("active_customers", "-")))
		self.kpi_fleet[1].setText(str(overview.get("fleet_vehicles", "-")))
		self.kpi_revenue[1].setText(str(overview.get("revenue_net", "-")))

		self.mini_active[1].setText(str(overview.get("active_rentals", "-")))
		self.mini_upcoming[1].setText(str(overview.get("upcoming_bookings", "-")))
		self.mini_overdue[1].setText(str(overview.get("overdue_rentals", "-")))
		self.mini_maint[1].setText(str(overview.get("maintenance_open", "-")))

		bookings = data.get("bookings", [])[:6]
		self.bookings_table.setRowCount(len(bookings))
		for row, item in enumerate(bookings):
			customer = item.get("customer", {}).get("name", "-")
			vehicle = item.get("vehicle", {}).get("plate", "-")
			pickup = item.get("pickup_date", "-")
			ret = item.get("return_date", "-")
			status = item.get("status", "-")
			values = [customer, vehicle, pickup, ret, status]
			for col, value in enumerate(values):
				self.bookings_table.setItem(row, col, QTableWidgetItem(str(value)))

		while self.payments_list.count():
			item = self.payments_list.takeAt(0)
			widget = item.widget()
			if widget:
				widget.deleteLater()

		for payment in data.get("payments", [])[:5]:
			row_card = QFrame()
			row_card.setObjectName("AuthForm")
			row_layout = QHBoxLayout(row_card)
			row_layout.setContentsMargins(10, 8, 10, 8)
			left = QLabel(str(payment.get("customer_name", "-")))
			right = QLabel(f"{payment.get('currency', '')} {payment.get('amount', '0.000')}")
			right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
			row_layout.addWidget(left)
			row_layout.addWidget(right)
			self.payments_list.addWidget(row_card)
