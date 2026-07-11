from drivesphere_desktop.core.api_client import ApiClient
from drivesphere_desktop.ui.pages.list_page import ActionSpec, ColumnSpec, FilterSpec, ListPage, OptionSpec
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout


class BookingsPage(ListPage):
	def __init__(self, api_client: ApiClient) -> None:
		super().__init__(
			api_client=api_client,
			endpoint="/api/bookings/",
			title_en="Bookings",
			title_ar="الحجوزات",
			filters=[
				FilterSpec("q", "Search Customer, Phone, Plate", "ابحث بالعميل أو الهاتف أو اللوحة"),
				FilterSpec(
					"status",
					"Status",
					"الحالة",
					[
						OptionSpec("", "All Status", "جميع الحالات"),
						OptionSpec("CONFIRMED", "Confirmed", "مؤكد"),
						OptionSpec("CHECKED_OUT", "Checked Out", "مسلم"),
						OptionSpec("RETURNED", "Returned", "مرتجع"),
						OptionSpec("UPCOMING", "Upcoming", "قادم"),
						OptionSpec("CANCELLED", "Cancelled", "ملغى"),
						OptionSpec("CLOSED", "Closed", "مغلق"),
					],
				),
			],
			columns=[
				ColumnSpec("ID", "الرقم", "id"),
				ColumnSpec("Customer", "العميل", "customer"),
				ColumnSpec("Vehicle", "المركبة", "vehicle"),
				ColumnSpec("Pickup", "الاستلام", "pickup_date"),
				ColumnSpec("Return", "الإرجاع", "return_date"),
				ColumnSpec("Status", "الحالة", "status"),
				ColumnSpec("Total", "الإجمالي", "total"),
			],
		)

		actions = QFrame()
		actions.setObjectName("ListActionsBar")
		layout = QHBoxLayout(actions)
		layout.setContentsMargins(12, 10, 12, 10)
		layout.setSpacing(8)

		self.add_btn = QPushButton("Add New Booking")
		self.add_btn.setObjectName("PrimaryButton")
		self.upcoming_btn = QPushButton("Upcoming Bookings")
		self.upcoming_btn.setObjectName("LangToggleButton")
		layout.addWidget(self.add_btn)
		layout.addWidget(self.upcoming_btn)
		layout.addStretch(1)

		self.layout().insertWidget(0, actions)
		self.add_btn.clicked.connect(lambda: self._set_quick_status("UPCOMING"))
		self.upcoming_btn.clicked.connect(lambda: self._set_quick_status("UPCOMING"))
		self.set_actions(
			[
				ActionSpec("edit", "Edit Booking", "تعديل الحجز", variant="ghost"),
				ActionSpec("delete", "Delete Booking", "حذف الحجز", variant="danger"),
			]
		)

	def set_language(self, lang: str) -> None:
		super().set_language(lang)
		is_ar = lang == "ar"
		self.add_btn.setText("إضافة حجز جديد" if is_ar else "Add New Booking")
		self.upcoming_btn.setText("الحجوزات القادمة" if is_ar else "Upcoming Bookings")

	def _set_quick_status(self, status: str) -> None:
		status_filter = self.filter_widgets.get("status")
		if status_filter is None:
			return
		index = status_filter.findData(status)
		if index >= 0:
			status_filter.setCurrentIndex(index)
			self.load_data()

	def action_edit(self) -> None:
		if not self.require_selection():
			return
		bid = self.selected_id()
		dlg = QDialog(self)
		dlg.setWindowTitle("Edit Booking" if not self.is_rtl else "تعديل الحجز")
		layout = QVBoxLayout(dlg)
		form = QFormLayout()

		pickup = QLineEdit(str(self.selected_row.get("pickup_date", "")))
		ret = QLineEdit(str(self.selected_row.get("return_date", "")))
		status = QComboBox()
		for code, label_en, label_ar in [
			("CONFIRMED", "Confirmed", "مؤكد"),
			("UPCOMING", "Upcoming", "قادم"),
			("CHECKED_OUT", "Checked Out", "مسلم"),
			("RETURNED", "Returned", "مرتجع"),
			("CLOSED", "Closed", "مغلق"),
			("CANCELLED", "Cancelled", "ملغى"),
		]:
			status.addItem(label_ar if self.is_rtl else label_en, code)
		index = status.findData(self.selected_row.get("status"))
		if index >= 0:
			status.setCurrentIndex(index)
		notes = QLineEdit("")

		form.addRow("Pickup Date (YYYY-MM-DD)" if not self.is_rtl else "تاريخ الاستلام", pickup)
		form.addRow("Return Date (YYYY-MM-DD)" if not self.is_rtl else "تاريخ الإرجاع", ret)
		form.addRow("Status" if not self.is_rtl else "الحالة", status)
		form.addRow("Notes" if not self.is_rtl else "ملاحظات", notes)
		layout.addLayout(form)
		buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
		buttons.accepted.connect(dlg.accept)

		initial = (pickup.text(), ret.text(), status.currentData(), notes.text())

		def reject_with_guard() -> None:
			current = (pickup.text(), ret.text(), status.currentData(), notes.text())
			if current != initial and not self.confirm_action(
				"Discard Changes",
				"Discard unsaved booking changes?",
				"تجاهل التغييرات",
				"هل تريد تجاهل تغييرات الحجز غير المحفوظة؟",
			):
				return
			dlg.reject()

		buttons.rejected.connect(reject_with_guard)
		layout.addWidget(buttons)
		if dlg.exec() != QDialog.Accepted:
			return

		try:
			self.api_client.post_json(
				f"/api/bookings/{bid}/update/",
				{
					"pickup_date": pickup.text().strip(),
					"return_date": ret.text().strip(),
					"status": status.currentData(),
					"notes": notes.text().strip(),
				},
			)
			self.notify("Booking updated", "تم تحديث الحجز")
			self.load_data()
		except Exception as exc:
			self.notify(f"Update failed: {exc}", f"فشل التحديث: {exc}")

	def action_delete(self) -> None:
		if not self.require_selection():
			return
		if not self.confirm_action(
			"Delete Booking",
			"Delete selected booking?",
			"حذف الحجز",
			"هل تريد حذف الحجز المحدد؟",
		):
			return
		bid = self.selected_id()
		try:
			self.api_client.post_json(f"/api/bookings/{bid}/delete/", {})
			self.notify("Booking deleted", "تم حذف الحجز")
			self.load_data()
		except Exception as exc:
			self.notify(f"Delete failed: {exc}", f"فشل الحذف: {exc}")
