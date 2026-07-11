from drivesphere_desktop.core.api_client import ApiClient
from drivesphere_desktop.ui.pages.list_page import ActionSpec, ColumnSpec, FilterSpec, ListPage, OptionSpec
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
	QComboBox,
	QDialog,
	QDialogButtonBox,
	QFormLayout,
	QGridLayout,
	QHBoxLayout,
	QLabel,
	QListWidget,
	QLineEdit,
	QPushButton,
	QTabWidget,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


class VehiclesPage(ListPage):
	def __init__(self, api_client: ApiClient) -> None:
		super().__init__(
			api_client=api_client,
			endpoint="/api/vehicles/",
			title_en="Vehicles",
			title_ar="المركبات",
			filters=[
				FilterSpec("plate", "Plate", "اللوحة"),
				FilterSpec("brand", "Brand", "الماركة"),
				FilterSpec("model", "Model", "الطراز"),
				FilterSpec(
					"status",
					"Status",
					"الحالة",
					[
						OptionSpec("", "Any Status", "كل الحالات"),
						OptionSpec("AVAILABLE", "Available", "متاحة"),
						OptionSpec("RESERVED", "Reserved", "محجوزة"),
						OptionSpec("RENTED", "Rented", "مؤجرة"),
						OptionSpec("MAINTENANCE", "Maintenance", "صيانة"),
						OptionSpec("INACTIVE", "Inactive", "غير نشطة"),
					],
				),
			],
			columns=[
				ColumnSpec("Plate", "رقم اللوحة", "plate_number"),
				ColumnSpec("Brand", "الماركة", "brand_name"),
				ColumnSpec("Model", "الطراز", "model_name"),
				ColumnSpec("Year", "السنة", "year"),
				ColumnSpec("Transmission", "ناقل الحركة", "transmission"),
				ColumnSpec("Fuel", "الوقود", "fuel_type"),
				ColumnSpec("Status", "الحالة", "status_label"),
				ColumnSpec("Daily Rate", "السعر اليومي", "daily_rate"),
			],
		)
		self.set_actions(
			[
				ActionSpec("docs", "Upload / View Docs", "رفع / عرض المستندات", variant="ghost"),
				ActionSpec("photos", "Photos", "الصور", variant="ghost"),
				ActionSpec("telematics", "Telematics", "التتبع", variant="primary"),
				ActionSpec("edit", "Edit Vehicle", "تعديل المركبة", variant="ghost"),
				ActionSpec("delete", "Delete Vehicle", "حذف المركبة", variant="danger"),
			]
		)

	def _format_idle(self, seconds: int | str) -> str:
		try:
			total = int(float(seconds or 0))
		except Exception:
			total = 0
		hours = total // 3600
		minutes = (total % 3600) // 60
		return f"{hours}h {minutes}m"

	def _format_duration(self, seconds: int | str) -> str:
		return self._format_idle(seconds)

	def action_delete(self) -> None:
		if not self.require_selection():
			return
		if not self.confirm_action(
			"Delete Vehicle",
			"Delete selected vehicle?",
			"حذف المركبة",
			"هل تريد حذف المركبة المحددة؟",
		):
			return
		vid = self.selected_id()
		try:
			self.api_client.post_json(f"/api/vehicles/{vid}/delete/", {})
			self.notify("Vehicle deleted", "تم حذف المركبة")
			self.load_data()
		except Exception as exc:
			self.notify(f"Delete failed: {exc}", f"فشل الحذف: {exc}")

	def action_docs(self) -> None:
		if not self.require_selection():
			return
		vid = self.selected_id()
		dlg = QDialog(self)
		dlg.setWindowTitle("Vehicle Documents" if not self.is_rtl else "مستندات المركبة")
		dlg.resize(520, 420)
		layout = QVBoxLayout(dlg)
		lst = QListWidget()
		layout.addWidget(lst)
		controls = QHBoxLayout()
		open_page_btn = QPushButton("Open Page" if not self.is_rtl else "فتح الصفحة")
		controls.addWidget(open_page_btn)
		controls.addStretch(1)
		layout.addLayout(controls)
		try:
			payload = self.api_client.get_json(f"/api/vehicles/{vid}/docs/")
			for doc in payload.get("results", []):
				lst.addItem(f"{doc.get('doc_type_label', '')} | {doc.get('expiry_date', '')}")
			if lst.count() == 0:
				lst.addItem("No documents" if not self.is_rtl else "لا توجد مستندات")
		except Exception as exc:
			lst.addItem(f"Failed: {exc}")
		buttons = QDialogButtonBox(QDialogButtonBox.Close)
		buttons.rejected.connect(dlg.reject)
		layout.addWidget(buttons)
		open_page_btn.clicked.connect(
			lambda: QDesktopServices.openUrl(QUrl(self.api_client.absolute_url(f"/vehicles/{vid}/documents/")))
		)
		dlg.exec()

	def action_photos(self) -> None:
		if not self.require_selection():
			return
		vid = self.selected_id()
		dlg = QDialog(self)
		dlg.setWindowTitle("Vehicle Photos" if not self.is_rtl else "صور المركبة")
		dlg.resize(520, 420)
		layout = QVBoxLayout(dlg)
		lst = QListWidget()
		layout.addWidget(lst)
		controls = QHBoxLayout()
		open_page_btn = QPushButton("Open Page" if not self.is_rtl else "فتح الصفحة")
		controls.addWidget(open_page_btn)
		controls.addStretch(1)
		layout.addLayout(controls)
		try:
			payload = self.api_client.get_json(f"/api/vehicles/{vid}/photos/")
			for photo in payload.get("results", []):
				lst.addItem(f"{photo.get('created_at', '')} | {photo.get('caption', '')}")
			if lst.count() == 0:
				lst.addItem("No photos" if not self.is_rtl else "لا توجد صور")
		except Exception as exc:
			lst.addItem(f"Failed: {exc}")
		buttons = QDialogButtonBox(QDialogButtonBox.Close)
		buttons.rejected.connect(dlg.reject)
		layout.addWidget(buttons)
		open_page_btn.clicked.connect(
			lambda: QDesktopServices.openUrl(QUrl(self.api_client.absolute_url(f"/vehicles/{vid}/photos/")))
		)
		dlg.exec()

	def action_edit(self) -> None:
		if not self.require_selection():
			return
		vid = self.selected_id()
		try:
			detail_payload = self.api_client.get_json(f"/api/vehicles/{vid}/")
			detail = detail_payload.get("vehicle", {})
			brands_payload = self.api_client.get_json("/api/vehicle-brands/")
			brands = brands_payload.get("results", [])
		except Exception as exc:
			self.notify(f"Load failed: {exc}", f"فشل التحميل: {exc}")
			return

		dlg = QDialog(self)
		dlg.setWindowTitle("Edit Vehicle" if not self.is_rtl else "تعديل المركبة")
		layout = QVBoxLayout(dlg)
		form = QFormLayout()

		plate = QLineEdit(str(detail.get("plate_number", "")))
		year = QLineEdit(str(detail.get("year", "")))
		color = QLineEdit(str(detail.get("color", "")))
		odo = QLineEdit(str(detail.get("odometer_km", "")))
		rate = QLineEdit(str(detail.get("daily_rate", "")))
		deposit = QLineEdit(str(detail.get("deposit", "")))

		brand = QComboBox()
		for b in brands:
			brand.addItem(str(b.get("name", "")), b.get("id"))
		brand_id = detail.get("brand_id")
		idx = brand.findData(brand_id)
		if idx >= 0:
			brand.setCurrentIndex(idx)

		model = QComboBox()
		status = QComboBox()
		for value in ["AVAILABLE", "RESERVED", "RENTED", "MAINTENANCE", "INACTIVE"]:
			status.addItem(value, value)
		idx = status.findData(detail.get("status"))
		if idx >= 0:
			status.setCurrentIndex(idx)

		transmission = QComboBox()
		for value in ["AUTOMATIC", "MANUAL"]:
			transmission.addItem(value, value)
		idx = transmission.findData(detail.get("transmission"))
		if idx >= 0:
			transmission.setCurrentIndex(idx)

		fuel = QComboBox()
		for value in ["PETROL", "DIESEL", "HYBRID", "ELECTRIC"]:
			fuel.addItem(value, value)
		idx = fuel.findData(detail.get("fuel_type") or detail.get("fuel"))
		if idx >= 0:
			fuel.setCurrentIndex(idx)

		def load_models() -> None:
			model.blockSignals(True)
			model.clear()
			try:
				payload = self.api_client.get_json(f"/api/vehicle-models/?brand_id={brand.currentData()}")
				for m in payload.get("results", []):
					model.addItem(str(m.get("name", "")), m.get("id"))
			except Exception:
				pass
			target = detail.get("model_id")
			mid = model.findData(target)
			if mid >= 0:
				model.setCurrentIndex(mid)
			model.blockSignals(False)

		brand.currentIndexChanged.connect(load_models)
		load_models()

		form.addRow("Plate" if not self.is_rtl else "اللوحة", plate)
		form.addRow("Brand" if not self.is_rtl else "الماركة", brand)
		form.addRow("Model" if not self.is_rtl else "الطراز", model)
		form.addRow("Year" if not self.is_rtl else "السنة", year)
		form.addRow("Transmission" if not self.is_rtl else "ناقل الحركة", transmission)
		form.addRow("Fuel" if not self.is_rtl else "الوقود", fuel)
		form.addRow("Status" if not self.is_rtl else "الحالة", status)
		form.addRow("Color" if not self.is_rtl else "اللون", color)
		form.addRow("Odometer" if not self.is_rtl else "عداد المسافة", odo)
		form.addRow("Daily Rate" if not self.is_rtl else "السعر اليومي", rate)
		form.addRow("Deposit" if not self.is_rtl else "التأمين", deposit)
		layout.addLayout(form)

		buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
		buttons.accepted.connect(dlg.accept)
		initial = (
			plate.text(),
			brand.currentData(),
			model.currentData(),
			year.text(),
			transmission.currentData(),
			fuel.currentData(),
			status.currentData(),
			color.text(),
			odo.text(),
			rate.text(),
			deposit.text(),
		)

		def reject_with_guard() -> None:
			current = (
				plate.text(),
				brand.currentData(),
				model.currentData(),
				year.text(),
				transmission.currentData(),
				fuel.currentData(),
				status.currentData(),
				color.text(),
				odo.text(),
				rate.text(),
				deposit.text(),
			)
			if current != initial and not self.confirm_action(
				"Discard Changes",
				"Discard unsaved vehicle changes?",
				"تجاهل التغييرات",
				"هل تريد تجاهل تغييرات المركبة غير المحفوظة؟",
			):
				return
			dlg.reject()

		buttons.rejected.connect(reject_with_guard)
		layout.addWidget(buttons)

		if dlg.exec() != QDialog.Accepted:
			return

		try:
			self.api_client.post_json(
				f"/api/vehicles/{vid}/update/",
				{
					"plate_number": plate.text().strip(),
					"brand_id": brand.currentData(),
					"model_id": model.currentData(),
					"year": year.text().strip(),
					"transmission": transmission.currentData(),
					"fuel_type": fuel.currentData(),
					"status": status.currentData(),
					"color": color.text().strip(),
					"odometer_km": odo.text().strip(),
					"daily_rate": rate.text().strip(),
					"deposit": deposit.text().strip(),
				},
			)
			self.notify("Vehicle updated", "تم تحديث المركبة")
			self.load_data()
		except Exception as exc:
			self.notify(f"Update failed: {exc}", f"فشل التحديث: {exc}")

	def action_telematics(self) -> None:
		if not self.require_selection():
			return
		vid = self.selected_id()
		dialog = QDialog(self)
		dialog.setWindowTitle("Telematics Details" if not self.is_rtl else "تفاصيل التتبع")
		dialog.resize(980, 640)
		root = QVBoxLayout(dialog)

		top_row = QHBoxLayout()
		days_box = QComboBox()
		for value, label in [("1", "1 Day"), ("7", "7 Days"), ("30", "30 Days")]:
			days_box.addItem(label if not self.is_rtl else f"{value} يوم", value)
		days_box.setCurrentIndex(1)
		refresh_btn = QPushButton("Refresh" if not self.is_rtl else "تحديث")
		refresh_btn.setObjectName("DsBtnPrimary")
		days_box.setObjectName("DsInput")
		top_row.addWidget(QLabel("Window" if not self.is_rtl else "النافذة"))
		top_row.addWidget(days_box)
		top_row.addStretch(1)
		top_row.addWidget(refresh_btn)
		root.addLayout(top_row)

		caption = QLabel("")
		caption.setObjectName("AuthLabel")
		root.addWidget(caption)

		tabs = QTabWidget()
		root.addWidget(tabs, 1)

		overview = QWidget()
		overview_layout = QVBoxLayout(overview)
		kpi_grid = QGridLayout()
		kpi_grid.setHorizontalSpacing(10)
		kpi_grid.setVerticalSpacing(10)
		overview_layout.addLayout(kpi_grid)

		kpis: dict[str, QLabel] = {}

		def add_kpi(name: str, row: int, col: int) -> None:
			card = QWidget()
			card_layout = QVBoxLayout(card)
			card_layout.setContentsMargins(10, 10, 10, 10)
			title = QLabel(name)
			value = QLabel("--")
			value.setStyleSheet("font-size: 20px; font-weight: 700;")
			card_layout.addWidget(title)
			card_layout.addWidget(value)
			kpi_grid.addWidget(card, row, col)
			kpis[name] = value

		add_kpi("Distance (km)", 0, 0)
		add_kpi("Avg Speed (km/h)", 0, 1)
		add_kpi("Idle Time", 0, 2)
		add_kpi("Avg Fuel (%)", 1, 0)
		add_kpi("Fuel Used (L)", 1, 1)
		add_kpi("Efficiency (km/L)", 1, 2)
		add_kpi("Pings", 2, 0)
		add_kpi("Battery (V)", 2, 1)

		latest_gps = QLabel("--")
		engine_state = QLabel("--")
		faults = QLabel("--")
		map_btn = QPushButton("Open Map" if not self.is_rtl else "فتح الخريطة")
		map_btn.setObjectName("LangToggleButton")
		map_btn.setEnabled(False)
		gps_url: dict[str, str] = {"value": ""}
		map_btn.clicked.connect(lambda: gps_url["value"] and QDesktopServices.openUrl(QUrl(gps_url["value"])))
		overview_layout.addWidget(QLabel("Latest GPS"))
		overview_layout.addWidget(latest_gps)
		overview_layout.addWidget(map_btn)
		overview_layout.addWidget(QLabel("Engine"))
		overview_layout.addWidget(engine_state)
		overview_layout.addWidget(QLabel("Fault Codes"))
		overview_layout.addWidget(faults)
		overview_layout.addStretch(1)
		tabs.addTab(overview, "Overview" if not self.is_rtl else "نظرة عامة")

		trips_tab = QWidget()
		trips_layout = QVBoxLayout(trips_tab)
		trips_table = QTableWidget(0, 6)
		trips_table.setHorizontalHeaderLabels(["Start", "End", "Distance", "Duration", "Max Speed", "Fuel Used"])
		trips_table.horizontalHeader().setStretchLastSection(True)
		trips_table.verticalHeader().setVisible(False)
		trips_table.setSelectionBehavior(QTableWidget.SelectRows)
		trips_table.setEditTriggers(QTableWidget.NoEditTriggers)
		trips_layout.addWidget(trips_table)
		tabs.addTab(trips_tab, "Trips" if not self.is_rtl else "الرحلات")

		events_tab = QWidget()
		events_layout = QVBoxLayout(events_tab)
		events_grid = QGridLayout()
		events_layout.addLayout(events_grid)
		event_values: dict[str, QLabel] = {}
		for idx, title in enumerate(["Overspeed", "Harsh Brakes", "Harsh Accel", "Low Battery"]):
			title_lbl = QLabel(title)
			value_lbl = QLabel("--")
			value_lbl.setStyleSheet("font-size: 22px; font-weight: 700;")
			events_grid.addWidget(title_lbl, idx, 0)
			events_grid.addWidget(value_lbl, idx, 1)
			event_values[title] = value_lbl
		fault_list = QLabel("")
		events_layout.addWidget(fault_list)
		events_layout.addStretch(1)
		tabs.addTab(events_tab, "Behavior & Alerts" if not self.is_rtl else "السلوك والتنبيهات")

		buttons = QDialogButtonBox(QDialogButtonBox.Close)
		buttons.rejected.connect(dialog.reject)
		root.addWidget(buttons)

		def load_data() -> None:
			try:
				days = int(days_box.currentData() or 7)
				metrics = self.api_client.get_json(f"/api/vehicles/{vid}/telematics/metrics/?days={days}")
				latest = self.api_client.get_json(f"/api/vehicles/{vid}/telematics/latest/")
				trips = self.api_client.get_json(f"/api/vehicles/{vid}/telematics/trips/?days={days}")
				events = self.api_client.get_json(f"/api/vehicles/{vid}/telematics/events/?days={days}")
				caption.setText(
					f"Vehicle: {metrics.get('plate_number', '-')}, Window: {metrics.get('window_days', days)} days"
				)
				kpis["Distance (km)"].setText(str(metrics.get("distance_km", 0)))
				kpis["Avg Speed (km/h)"].setText(str(metrics.get("avg_speed_kmh", 0)))
				kpis["Idle Time"].setText(self._format_idle(metrics.get("idle_seconds", 0)))
				kpis["Avg Fuel (%)"].setText(f"{metrics.get('avg_fuel_percent', 0)}%")
				kpis["Fuel Used (L)"].setText(str(metrics.get("fuel_used_liters", 0)))
				kpis["Efficiency (km/L)"].setText(str(metrics.get("efficiency_km_per_liter", 0)))
				kpis["Pings"].setText(str(metrics.get("pings_count", 0)))
				kpis["Battery (V)"].setText(str(metrics.get("avg_battery_voltage", 0)))

				latest_payload = latest.get("latest") or {}
				latest_gps.setText(f"{latest_payload.get('latitude', '-')}, {latest_payload.get('longitude', '-')}")
				engine_on = latest_payload.get("engine_on")
				engine_state.setText(
					f"{'ON' if engine_on else 'OFF' if engine_on is not None else 'Unknown'}"
					f" | {latest_payload.get('engine_status') or '-'}"
				)
				latest_fault_codes = latest_payload.get("fault_codes") or []
				faults.setText(", ".join([str(code) for code in latest_fault_codes]) if latest_fault_codes else "None")
				map_url = latest_payload.get("google_maps_url", "")
				gps_url["value"] = map_url
				map_btn.setEnabled(bool(map_url))

				trips_list = trips.get("trips") or []
				trips_table.setRowCount(len(trips_list))
				for row, trip in enumerate(trips_list):
					values = [
						str(trip.get("start_at", "")),
						str(trip.get("end_at", "")),
						f"{trip.get('distance_km', 0)} km",
						self._format_duration(trip.get("duration_seconds", 0)),
						f"{trip.get('max_speed_kmh', 0)} km/h",
						f"{trip.get('fuel_used_liters', 0)} L",
					]
					for col, val in enumerate(values):
						trips_table.setItem(row, col, QTableWidgetItem(val))

				event_values["Overspeed"].setText(str(events.get("overspeed_count", 0)))
				event_values["Harsh Brakes"].setText(str(events.get("harsh_brake_count", 0)))
				event_values["Harsh Accel"].setText(str(events.get("harsh_accel_count", 0)))
				event_values["Low Battery"].setText(str(events.get("low_battery_events", 0)))
				fault_codes = events.get("fault_codes") or []
				fault_list.setText(
					("Fault codes: " + ", ".join([str(code) for code in fault_codes]))
					if fault_codes
					else "No fault codes."
				)
			except Exception as exc:
				caption.setText(f"Load failed: {exc}")

		refresh_btn.clicked.connect(load_data)
		days_box.currentIndexChanged.connect(load_data)
		load_data()
		dialog.exec()
